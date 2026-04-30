"""
routes/api.py — Centralized API endpoints.

Handles all API endpoints for both participants and instructors,
providing a clear boundary for API functionality and future
API versioning support.
"""
from flask import Blueprint, g, jsonify, request
from app import require_participant, require_instructor
from services.pin_service_extended import PinServiceExtended
from services.participant_service import ParticipantService
from services.live_session_service import LiveSessionService
from services.presentation_service import PresentationService
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
        
        # Convert choices to integers (they come as strings from form)
        try:
            answer_indices = [int(choice) for choice in choices]
        except (ValueError, TypeError):
            return ResponseUtils.error_response("Invalid choice values", 400)
        
        # Check if user has already answered this question
        has_answered = LiveSessionService.has_user_answered_question(
            username=g.participant.presentation_instructor_username,
            presentation_uuid=g.participant.presentation_uuid,
            session_uuid=g.participant.session_uuid,
            user_uuid=g.participant.uuid,
            question_uuid=question_uuid
        )
        
        if has_answered:
            return ResponseUtils.error_response("You already answered this question", 402)
        
        # Calculate response time using service method
        response_time = LiveSessionService.calculate_participant_response_time(
            username=g.participant.presentation_instructor_username,
            presentation_uuid=g.participant.presentation_uuid,
            session_uuid=g.participant.session_uuid
        )
        
        # Save the answer to the session JSON file
        success = LiveSessionService.set_user_answer(
            username=g.participant.presentation_instructor_username,
            presentation_uuid=g.participant.presentation_uuid,
            session_uuid=g.participant.session_uuid,
            user_uuid=g.participant.uuid,
            question_uuid=question_uuid,
            answer_indices=answer_indices,
            response_time=response_time
        )
        
        if not success:
            return ResponseUtils.error_response("Failed to save answer", 500)
        
        return ResponseUtils.success_response({
            'message': 'Answer submitted successfully',
            'choices': answer_indices,
            'question_uuid': question_uuid,
            'response_time': response_time
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

@routes.route('/presentations/<presentation_id>/live_session/<session_id>/responses-count', methods=['POST'])
@require_instructor
def get_live_responses_count(presentation_id, session_id):
    """API endpoint to get live count of answered participants for current question."""
    try:
        data = request.get_json()
        question_uuid = data.get('question_uuid')
        
        if not question_uuid:
            return ResponseUtils.error_response("Missing question_uuid", 400)
        
        # Get answered participants count
        answered_count, total_count = LiveSessionService.get_answered_participants_count(
            username=g.user.username,
            presentation_uuid=presentation_id,
            session_uuid=session_id,
            question_uuid=question_uuid
        )
        
        return ResponseUtils.success_response({
            'answered_count': answered_count,
            'participants_count': total_count,
            'all_answered': answered_count >= total_count and total_count > 0
        })
        
    except Exception as e:
        return ResponseUtils.error_response(f"Failed to get responses count: {str(e)}", 500)
