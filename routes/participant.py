"""
routes/participant.py — Participant session routes.

Handles participant session management, including joining sessions
and live session viewing. Extracted from main.py for better
separation of concerns.
"""
from flask import Blueprint, render_template, flash, redirect, url_for, request, session, g
from forms.join import JoinForm
from app import require_participant
from services.pin_service_extended import PinServiceExtended
from services.participant_service import ParticipantService
from services.live_session_service import LiveSessionService
from utils.form_utils import FormUtils
from config.constants import FLASH_ERROR, SESSION_DONE

routes = Blueprint('participant', __name__)

@routes.route('/join')
def join_session():
    """Render the join session page."""
    pin = request.args.get('pin', '').strip()
    presentation = None
    
    if pin:
        # Use PinServiceExtended to validate PIN and get presentation
        is_valid, error_message, presentation_obj = PinServiceExtended.validate_pin(pin)
        
        if not is_valid:
            flash(error_message or 'Session not found with this PIN.', FLASH_ERROR)
            return redirect(url_for('public.index'))
        
        presentation = presentation_obj
    
    form = JoinForm(pin=pin)
    return render_template('join.html', form=form, presentation=presentation, pin=pin)

@routes.route('/join', methods=['POST'])
def handle_join():
    """Handle participant session join."""
    form = JoinForm(request.form)
    
    if not form.validate():
        FormUtils.flash_form_validation_errors(form)
        return render_template('join.html', form=form, presentation=None)
    
    pin, nickname = FormUtils.prepare_join_session_data(form)
    
    # Use ParticipantService to handle the join process
    success, error_message, participant, run_data = ParticipantService.join_session_run(pin, nickname)
    if not success:
        flash(error_message or ParticipantService.get_join_failure_flash_message(), FLASH_ERROR)
        return redirect(url_for('participant.join_session'))
    
    # Prepare and store session data
    session_data = ParticipantService.prepare_participant_session_data(participant, run_data)
    session.update(session_data)
    
    # Redirect to the joined session
    redirect_url = ParticipantService.get_join_success_redirect_url(participant.session_uuid)
    return redirect(redirect_url)

@routes.route('/session/<session_uuid>')
@require_participant
def participant_session(session_uuid):
    """Render the live session page for an authenticated participant."""
    success, error_message, session_data = ParticipantService.get_session_for_participant(
        g.participant.presentation_instructor_username,
        g.participant.presentation_uuid,
        g.participant.session_uuid
    )
    # Redirect to the session result page if session is done
    if session_data.get('status') == SESSION_DONE:
        return redirect(url_for('participant.session_result', session_uuid=session_uuid))
    
    if not success or session_uuid != g.participant.session_uuid:
        flash(error_message or "Session not found", FLASH_ERROR)
        return redirect(url_for('participant.join_session'))
    
    # Get timing information for active sessions
    timing_info = None
    current_question = None
    is_time_expired = False
    current_objective = None
    
    try:
        # Get timing information for active sessions
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
            
            # Extract objective information from session data
            if current_question and current_question.get('parent_objective_id'):
                objectives = session_data.get('objectives', {})
                current_objective = objectives.get(current_question['parent_objective_id'])
            
    except Exception:
        # If timing service fails, continue
        pass
    
    # Calculate question progress using service function
    current_question_index, total_questions = LiveSessionService.get_current_question_index(
        g.participant.presentation_instructor_username,
        g.participant.presentation_uuid,
        g.participant.session_uuid
    )
    # Convert to 1-based index for display
    current_question_index_display = current_question_index + 1 if total_questions > 0 else 0
    
    # Check if user has already answered the current question
    has_answered = False
    if current_question and current_question.get('question_id'):
        has_answered = LiveSessionService.has_user_answered_question(
            username=g.participant.presentation_instructor_username,
            presentation_uuid=g.participant.presentation_uuid,
            session_uuid=g.participant.session_uuid,
            user_uuid=g.participant.uuid,
            question_uuid=current_question['question_id']
        )
    return render_template('session.html', 
                         session_data=session_data,
                         timing_info=timing_info,
                         current_question=current_question,
                         current_objective=current_objective,
                         is_time_expired=is_time_expired,
                         current_question_index=current_question_index_display,
                         total_questions=total_questions,
                         has_answered=has_answered)

@routes.route('/session/<session_uuid>/result')
@require_participant
def session_result(session_uuid):
    """Render the session result page with leaderboard for participants."""
    # Validate that the session_uuid matches the participant's session
    if session_uuid != g.participant.session_uuid:
        flash("Session not found", FLASH_ERROR)
        return redirect(url_for('participant.join_session'))
    
    # Get session data
    success, error_message, session_data = ParticipantService.get_session_for_participant(
        g.participant.presentation_instructor_username,
        g.participant.presentation_uuid,
        g.participant.session_uuid
    )
    
    if not success:
        flash(error_message or "Session not found", FLASH_ERROR)
        return redirect(url_for('participant.join_session'))
    
    # Verify session is completed
    if session_data.get('status') != SESSION_DONE:
        flash("Session results are not available yet", FLASH_ERROR)
        return redirect(url_for('participant.participant_session', session_uuid=session_uuid))
    
    # Get users_points from session data
    users_points = session_data.get('users_points', {})
    participants = session_data.get('participants', [])
    
    # Create leaderboard by merging participant info with points
    leaderboard = []
    for participant in participants:
        participant_uuid = participant.get('uuid')
        nickname = participant.get('nickname', 'Anonymous')
        points = users_points.get(participant_uuid, 0)
        
        leaderboard.append({
            'uuid': participant_uuid,
            'nickname': nickname,
            'points': points
        })
    
    # Sort by points (highest first)
    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    
    return render_template('session_participant_result.html',
                         session_data=session_data,
                         leaderboard=leaderboard)
