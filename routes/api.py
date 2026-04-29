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

@routes.route('/submit-answer', methods=['POST'])
@require_participant
def submit_answer():
    """API endpoint for participants to submit their answers."""
    try:
        data = request.get_json()
        choices = data.get('choices', [])
        question_uuid = data.get('question_uuid')
        
        if not choices or not question_uuid:
            return ResponseUtils.error_response("Missing required fields: choices and question_uuid", 400)
        
        # Here you would typically save the answer to a database or file
        # For now, we'll just return a success response
        # In a real implementation, you might want to:
        # 1. Validate the question belongs to the current session
        # 2. Save the participant's answer
        # 3. Update any scoring or tracking systems
        
        # Log the answer for debugging (remove in production)
        print(f"Answer submitted: participant={g.participant.session_uuid}, question={question_uuid}, choices={choices}")
        
        return ResponseUtils.success_response({
            'message': 'Answer submitted successfully',
            'choices': choices,
            'question_uuid': question_uuid
        })
        
    except Exception as e:
        return ResponseUtils.error_response(f"Failed to submit answer: {str(e)}", 500)

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
        
        if not success:
            return ResponseUtils.session_status_response(False, 'error', error_message)
        
        # Get timing information for active sessions
        timing_info = None
        current_question = None
        is_time_expired = False
        
        if session_data.get('status') == 'active':
            try:
                from services.live_session_service import LiveSessionService
                timing_info = LiveSessionService.get_session_timing(
                    g.participant.presentation_instructor_username,
                    g.participant.presentation_uuid,
                    g.participant.session_uuid
                )
                
                # Check if timing has expired
                is_time_expired = LiveSessionService.is_question_time_expired(
                    g.participant.presentation_instructor_username,
                    g.participant.presentation_uuid,
                    g.participant.session_uuid
                )
                
                # Get current question data if available
                if timing_info.get('current_question_uuid'):
                    current_question = LiveSessionService.get_current_question(
                        g.participant.presentation_instructor_username,
                        g.participant.presentation_uuid,
                        g.participant.session_uuid
                    )
                    
            except Exception:
                # If timing service fails, continue without timing info
                pass
        
        # Check if there's a new question (different from current)
        has_new_question = False
        if timing_info and timing_info.get('current_question_uuid'):
            # Compare with any stored previous question UUID if available
            # For now, we'll just check if there's a current question
            has_new_question = True
        
        # Build enhanced response
        response_data = {
            'success': True,
            'status': session_data.get('status', 'unknown'),
            'has_new_question': has_new_question,
            'is_time_expired': is_time_expired,
            'timing_info': timing_info,
            'current_question': current_question
        }
        
        return jsonify(response_data)
            
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
