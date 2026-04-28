from flask import Blueprint, g, render_template, request, flash, redirect, url_for, jsonify, session
from repositories.presentations import load_presentation, save_presentation, get_presentation_by_pin
from repositories.runs import get_unexpired_run_by_pin, join_participant, save_run_data, load_run_data, get_all_run_paths_across_users
from forms.join import JoinForm
from datetime import datetime
import json
import os
from app import require_participant

from repositories.sessions import load_session
routes = Blueprint('main', __name__)

@routes.route('/')
def index():
    return render_template('index.html')


@routes.route('/api/validate-pin', methods=['POST'])
def validate_pin():
    pin = request.json.get('pin', '').strip()
    
    if not pin:
        return jsonify({'error': 'PIN is required'}), 400
    
    presentation = get_presentation_by_pin(pin)
    if not presentation:
        return jsonify({'error': 'Invalid PIN'}), 404
    
    # Return presentation info for valid PIN
    return jsonify({
        'title': presentation.title or '',
        'description': presentation.description or '',
        'valid': True
    })


@routes.route('/join')
def join_session():
    pin = request.args.get('pin', '').strip()
    presentation = None
    if pin:
        presentation = get_presentation_by_pin(pin)
        if not presentation:
            flash('Presentation not found with this PIN.', 'error')
            return redirect(url_for('main.index'))
    
    form = JoinForm(pin=pin)
    return render_template('join.html', form=form, presentation=presentation, pin=pin)


@routes.route('/join', methods=['POST'])
def handle_join():
    form = JoinForm(request.form)
    
    if not form.validate():
        flash('Please correct the errors below.', 'error')
        return render_template('join.html', form=form, presentation=None)
    
    pin = str(form.pin.data)
    nickname = form.nickname.data.strip()

    run = get_unexpired_run_by_pin(pin)
    print('run: ', run)
    if not run:
        flash('Presentation not found with this PIN.', 'error')
        return redirect(url_for('main.join_session'))
    
    participant = join_participant(run, nickname)

    # Store participant data in session (similar to instructor login)
    session['participant_uuid'] = participant.uuid
    session['participant_session_uuid'] = participant.session_uuid
    session['participant_nickname'] = nickname
    session['presentation_uuid'] = run['presentation_uuid']
    session['presentation_instructor_username'] = run['username']
    session.permanent = True
    
    # Redirect to the joined session
    return redirect(url_for('main.participant_session', session_uuid=participant.session_uuid))

@require_participant
@routes.route('/api/check-session-status', methods=['POST'])
def check_session_status():
    """API endpoint to check if session is created and started"""
    try:
        session_data = load_session(
            g.participant.presentation_instructor_username, 
            g.participant.presentation_uuid, 
            g.participant.session_uuid
        )
        
        if session_data and session_data.get('status') == 'active':
            return jsonify({'success': True, 'status': 'active'})
        else:
            return jsonify({'success': False, 'status': 'waiting'})
    except Exception as e:
        return jsonify({'success': False, 'status': 'error', 'message': str(e)}), 500


@require_participant
@routes.route('/session/<session_uuid>')
def participant_session(session_uuid):
    """Display the joined session page for a participant"""
    session_data = load_session(g.participant.presentation_instructor_username, g.participant.presentation_uuid, g.participant.session_uuid)
    return render_template('session.html', session_data=session_data)
    
    