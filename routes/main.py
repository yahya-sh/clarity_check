from flask import Blueprint, render_template, request, flash, redirect, url_for
from repositories.presentations import load_presentation, save_presentation
from repositories.runs import save_run_data, load_run_data
from datetime import datetime
import json
import os
routes = Blueprint('main', __name__)

@routes.route('/')
def index():
    return render_template('index.html')


@routes.route('/join')
def join_session():
    pin = request.args.get('pin', '').strip()
    
    if not pin:
        flash('Invalid join link.', 'error')
        return redirect(url_for('main.index'))
    
    # Find run data with this PIN
    
    run_data = None
    presentation = None
    instructors_dir = "data/instructors"
    
    if os.path.exists(instructors_dir):
        for username in os.listdir(instructors_dir):
            runs_dir = os.path.join(instructors_dir, username, "runs")
            if os.path.exists(runs_dir):
                for filename in os.listdir(runs_dir):
                    if filename.endswith('_pin.json'):
                        try:
                            filepath = os.path.join(runs_dir, filename)
                            with open(filepath) as f:
                                data = json.load(f)
                                
                            # Check if this run has the matching PIN and it's not expired
                            if data.get('pin_code') == pin:
                                pin_expires_at = data.get('expires_at')
                                if pin_expires_at:
                                    try:
                                        expires_at = datetime.fromisoformat(pin_expires_at)
                                        if expires_at > datetime.now():
                                            # Found valid run
                                            run_data = data
                                            # Load the associated presentation
                                            presentation_uuid = data.get('presentation_uuid')
                                            if presentation_uuid:
                                                presentation = load_presentation(username, presentation_uuid)
                                            break
                                    except ValueError:
                                        continue
                        except (json.JSONDecodeError, KeyError):
                            continue
                    
                    if run_data:
                        break
                if run_data:
                    break
    
    if not run_data or not presentation:
        flash('Invalid or expired PIN.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('join.html', presentation=presentation, pin=pin)


@routes.route('/join', methods=['POST'])
def handle_join():
    pin = request.form.get('pin', '').strip()
    nickname = request.form.get('nickname', '').strip()
    
    if not pin or not nickname:
        flash('Please provide both PIN and nickname.', 'error')
        return redirect(url_for('main.join_session', pin=pin))
    
    # Find and update run data
    import os
    import json
    
    run_data = None
    run_path = None
    presentation = None
    instructors_dir = "data/instructors"
    
    if os.path.exists(instructors_dir):
        for username in os.listdir(instructors_dir):
            runs_dir = os.path.join(instructors_dir, username, "runs")
            if os.path.exists(runs_dir):
                for filename in os.listdir(runs_dir):
                    if filename.endswith('_pin.json'):
                        try:
                            filepath = os.path.join(runs_dir, filename)
                            with open(filepath) as f:
                                data = json.load(f)
                                
                            if data.get('pin_code') == pin:
                                pin_expires_at = data.get('expires_at')
                                if pin_expires_at:
                                    try:
                                        expires_at = datetime.fromisoformat(pin_expires_at)
                                        if expires_at > datetime.now():
                                            run_path = filepath
                                            run_data = data
                                            
                                            # Check if nickname already exists
                                            existing_nicknames = [p.get('nickname', '') for p in run_data.get('participants', [])]
                                            if nickname in existing_nicknames:
                                                flash('This nickname is already taken. Please choose another.', 'error')
                                                return redirect(url_for('main.join_session', pin=pin))
                                            
                                            # Add new participant
                                            run_data['participants'].append({
                                                'nickname': nickname,
                                                'joined_at': datetime.now().isoformat()
                                            })
                                            
                                            # Save updated run data
                                            with open(filepath, 'w') as f:
                                                json.dump(run_data, f, indent=2)
                                            
                                            # Load associated presentation
                                            presentation_uuid = run_data.get('presentation_uuid')
                                            if presentation_uuid:
                                                presentation = load_presentation(username, presentation_uuid)
                                            
                                            flash(f'Successfully joined as {nickname}!', 'success')
                                            return render_template('joined.html', presentation=presentation, nickname=nickname)
                                            
                                    except ValueError:
                                        continue
                        except (json.JSONDecodeError, KeyError):
                            continue
                    
                    if run_path:
                        break
                if run_path:
                    break
    
    flash('Invalid or expired PIN.', 'error')
    return redirect(url_for('main.index'))