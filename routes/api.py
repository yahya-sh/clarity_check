"""
routes/api.py — Centralized API endpoints.

Handles all API endpoints for both participants and instructors,
providing a clear boundary for API functionality and future
API versioning support.
"""
from flask import Blueprint, g, jsonify, request
from app import require_participant
from services.pin_service_extended import PinServiceExtended
from services.participant_service import ParticipantService
from utils.response_utils import ResponseUtils

routes = Blueprint('api', __name__)

# ── Public API Endpoints ─────────────────────────────────────────────────────

@routes.route('/validate-pin', methods=['POST'])
def validate_pin():
    """Validate a PIN code and return presentation information."""
    pin = request.json.get('pin', '').strip()
    
    # Use PinServiceExtended for validation
    response_data = PinServiceExtended.format_pin_validation_response(pin)
    
    if 'error' in response_data:
        status_code = 404 if response_data['error'] == 'Invalid PIN' else 400
        return jsonify(response_data), status_code
    
    return jsonify(response_data)

# ── Participant API Endpoints ───────────────────────────────────────────────

@routes.route('/check-session-status', methods=['POST'])
@require_participant
def check_session_status():
    """API endpoint to check if the participant's session is active."""
    try:
        success, error_message, session_data = ParticipantService.check_session_status(
            g.participant.presentation_instructor_username,
            g.participant.presentation_uuid,
            g.participant.session_uuid
        )
        
        if not success or session_data.get('status') != 'active':        
            return ResponseUtils.session_status_response(False, 'waiting')
        else:
            # Format the response using ResponseUtils
            return ResponseUtils.session_status_response(True, 'active')
            
    except Exception as e:
        return ResponseUtils.error_response(f"Failed to check session status: {str(e)}", 500)

# ── Instructor API Endpoints ─────────────────────────────────────────────────

@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions', methods=['POST'])
def api_get_objective_questions(presentation_id, objective_id):
    """
    API endpoint to get questions for an objective.
    
    This is the API version of the questions route that returns JSON
    without requiring instructor authentication (for future API use).
    """
    try:
        from services.presentation_service import PresentationService
        
        # For now, this requires instructor auth - could be expanded for public API
        username = request.args.get('username')  # For future API key auth
        if not username:
            return ResponseUtils.unauthorized_response("Authentication required")
        
        questions = PresentationService.get_objective_questions(
            presentation_id=presentation_id,
            username=username,
            objective_id=objective_id
        )
        
        return ResponseUtils.success_response({'questions': questions})
        
    except Exception as e:
        return ResponseUtils.error_response(f"Failed to load questions: {str(e)}", 500)

# ── Utility API Endpoints ─────────────────────────────────────────────────────

@routes.route('/health')
def health_check():
    """Simple health check endpoint for API monitoring."""
    return ResponseUtils.success_response({
        'status': 'healthy',
        'version': '1.0.0'
    })

@routes.route('/info')
def api_info():
    """API information and available endpoints."""
    return ResponseUtils.success_response({
        'name': 'Presentation System API',
        'version': '1.0.0',
        'endpoints': {
            'public': [
                'POST /api/validate-pin',
                'GET /api/health',
                'GET /api/info'
            ],
            'participant': [
                'POST /api/check-session-status'
            ],
            'instructor': [
                'POST /api/presentations/<id>/objectives/<obj_id>/questions'
            ]
        }
    })
