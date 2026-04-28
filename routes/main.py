from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from repositories.presentations import load_presentation, save_presentation, get_presentation_by_pin
from repositories.runs import save_run_data, load_run_data
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

    presentation = get_presentation_by_pin(pin)
    if not presentation:
        flash('Presentation not found with this PIN.', 'error')
        return redirect(url_for('main.join_session'))
    
    return render_template('joined.html', presentation=presentation, nickname=nickname)