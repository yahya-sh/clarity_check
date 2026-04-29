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
from utils.form_utils import FormUtils
from config.constants import FLASH_ERROR

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
            flash(error_message or 'Presentation not found with this PIN.', FLASH_ERROR)
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
    
    if not success:
        flash(error_message or "Session not found", FLASH_ERROR)
        return redirect(url_for('participant.join_session'))
    
    return render_template('session.html', session_data=session_data)
