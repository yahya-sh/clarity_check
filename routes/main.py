from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from repositories.presentations import load_presentation, save_presentation, get_presentation_by_pin
from repositories.runs import get_unexpired_run_by_pin, join_participant, save_run_data, load_run_data, get_all_run_paths_across_users
from forms.join import JoinForm
from datetime import datetime
import json
import os
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
    if not run:
        flash('Presentation not found with this PIN.', 'error')
        return redirect(url_for('main.join_session'))
    
    participant = join_participant(run, nickname)
    
    # Redirect to the joined session
    return redirect(url_for('main.joined_session', session_uuid=participant.uuid))


@routes.route('/joined/<session_uuid>')
def joined_session(session_uuid):
    """Display the joined session page for a participant"""
    # Find the participant by their UUID
    all_run_paths = get_all_run_paths_across_users()
    participant_data = None
    run_data = None
    presentation = None
    
    for run_path in all_run_paths:
        try:
            with open(run_path, 'r') as f:
                current_run_data = json.load(f)
            
            # Look for participant in this run
            for participant in current_run_data.get('participants', []):
                if participant.get('uuid') == session_uuid:
                    participant_data = participant
                    run_data = current_run_data
                    break
            
            if participant_data:
                break
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    if not participant_data or not run_data:
        flash('Session not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Get presentation information
    presentation_uuid = run_data.get('presentation_uuid')
    presentation = None
    if presentation_uuid:
        # Find the username from the run path to load the presentation
        for run_path in all_run_paths:
            try:
                with open(run_path, 'r') as f:
                    current_run_data = json.load(f)
                
                if current_run_data.get('session_uuid') == run_data['session_uuid']:
                    # Extract username from path: data/instructors/{username}/runs/...
                    path_parts = run_path.split(os.sep)
                    if len(path_parts) >= 4 and path_parts[1] == 'instructors':
                        username = path_parts[2]
                        presentation = load_presentation(username, presentation_uuid)
                    break
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return render_template('joined.html', 
                         presentation=presentation, 
                         nickname=participant_data['nickname'],
                         session_uuid=session_uuid)
    