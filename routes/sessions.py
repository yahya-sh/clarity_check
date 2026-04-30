"""
routes/sessions.py — Session management routes.

Handles live session management, PIN management, QR code generation,
participant tracking, and session start functionality.
Extracted from instructor.py for better separation of concerns.
"""
from flask import Blueprint, render_template, flash, redirect, g, url_for, request, jsonify
from flask_wtf.csrf import CSRFError
from app import require_instructor
from repositories import runs_repo, presentations_repo
from repositories.base import ValidationError
from services import qr_service
from services.pin_service import get_or_renew_pin, refresh_pin as service_refresh_pin
from services.qr_service import generate_qr_code
from services.session_service import SessionService
from services.live_session_service import LiveSessionService
from utils.response_utils import ResponseUtils
from config.constants import FLASH_SUCCESS, FLASH_ERROR, SESSION_PENDING, SESSION_ACTIVE, SESSION_DONE
from models.presentation import Presentation
from routes._helpers import _load_presentation_or_abort

routes = Blueprint('sessions', __name__)


@routes.route('/presentations/<presentation_id>/run', methods=['GET'])
@require_instructor
def run_presentation(presentation_id):
    """
    Render the run/lobby page for a published presentation.

    This page displays the current PIN, QR code, and participant list.
    It also provides controls to start the session and manage participants.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id)
    if not isinstance(result, Presentation):
        return result
    presentation = result

    # Get or create a PIN for this presentation
    pin_code = get_or_renew_pin(username, presentation_id)

    # Generate QR code for the join URL
    join_url = url_for('participant.join_session', pin=pin_code, _external=True)
    qr_code_data_uri = generate_qr_code(join_url)

    # Get current participants from run data
    run_data = runs_repo.load_run_data(username, presentation_id)
    participants = run_data.get('participants', []) if run_data else []

    # Calculate objectives and questions count
    objectives_count = len(presentation.objectives) if presentation.objectives else 0
    questions_count = sum(len(obj.get('questions', [])) for obj in presentation.objectives) if presentation.objectives else 0

    return render_template(
        'instructor/run.html',
        presentation=presentation,
        pin_code=pin_code,
        qr_code=qr_code_data_uri,
        participants=participants,
        estimated_duration=presentation.calculate_estimated_duration(),
        join_url=join_url,
        objectives_count=objectives_count,
        questions_count=questions_count
    )

@routes.route('/presentations/<presentation_id>/refresh-pin', methods=['POST'])
@require_instructor
def refresh_pin(presentation_id):
    """
    Generate a new PIN for the active run, clearing the participant list.

    Returns JSON response with the new PIN and expiry time.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id, json_response=True)
    if not isinstance(result, Presentation):
        return result

    try:
        pin_data = service_refresh_pin(username, presentation_id)
        pin_code = pin_data['pin']
        join_url = url_for('participant.join_session', pin=pin_code, _external=True)
        return jsonify({
            'success': True,
            'pin_code': pin_code,
            'expires_at': pin_data['expires_at'],
            'qr_code': qr_service.generate_qr_code(join_url),
            'join_url': join_url
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to refresh PIN: {str(e)}'
        }), 500

@routes.route('/presentations/<presentation_id>/pin-status', methods=['GET'])
@require_instructor
def pin_status(presentation_id):
    """Return the current PIN and its expiry time as JSON."""
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id, json_response=True)
    if not isinstance(result, Presentation):
        return result

    try:
        pin_code = get_or_renew_pin(username, presentation_id)
        # Load run data to get expires_at
        run_data = runs_repo.load_run_data(username, presentation_id)
        expires_at = run_data.get('expires_at') if run_data else None
        return jsonify({
            'pin_code': pin_code,
            'expires_at': expires_at
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes.route('/presentations/<presentation_id>/participants', methods=['GET'])
@require_instructor
def get_participants(presentation_id):
    """Return the current participant list for the active run as JSON."""
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id, json_response=True)
    if not isinstance(result, Presentation):
        return result

    try:
        run_data = runs_repo.load_run_data(username, presentation_id)
        participants = run_data.get('participants', []) if run_data else []
        return jsonify({'participants': participants})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes.route('/presentations/<presentation_id>/start-session', methods=['POST'])
@require_instructor
def start_session(presentation_id):
    """
    Start a live session from the current run.

    Creates a new session and marks it as active. Returns JSON response
    with session details or error information.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id, json_response=True)
    if not isinstance(result, Presentation):
        return result

    try:
        # Use the standalone service function to move run data to session stage
        session_data = SessionService.move_run_to_session(username, presentation_id)
        session_uuid = session_data.get('session_uuid')
        
        if not session_uuid:
            flash('Failed to create session: No session UUID generated', FLASH_ERROR)
            return redirect(url_for('sessions.run_presentation', presentation_id=presentation_id))
        
        # Initialize session with objectives, questions, and sequencing
        try:
            SessionService.init_session(username, presentation_id, session_uuid)
        except Exception as e:
            flash(f'Failed to initialize session: {str(e)}', FLASH_ERROR)
            return redirect(url_for('sessions.run_presentation', presentation_id=presentation_id))
        
        # Redirect to the live session page
        return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_uuid))
    except Exception as e:
        flash(f'Failed to start session: {str(e)}', FLASH_ERROR)
        return redirect(url_for('sessions.run_presentation', presentation_id=presentation_id))

@routes.route('/presentations/<presentation_id>/live_session/<session_id>')
@require_instructor
def live_session(presentation_id, session_id):
    """
    Render the live session page for an instructor.
    
    Displays the active session with controls for managing participants,
    questions, and session flow.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id)
    if not isinstance(result, Presentation):
        return result
    presentation = result

    try:
        # Load session data
        session_data = SessionService.get_session(username, presentation_id, session_id)
        session_status = session_data.get('status')
        
        # Calculate progress values (needed for both template types)
        current_question_uuid = session_data.get('current_question_uuid')
        current_question_index = 0
        total_questions = 0
        progress_percentage = 0
        
        if session_data.get('shuffled_question_uuids'):
            total_questions = len(session_data['shuffled_question_uuids'])
            if current_question_uuid and current_question_uuid in session_data['shuffled_question_uuids']:
                current_question_index = session_data['shuffled_question_uuids'].index(current_question_uuid) + 1
        
        progress_percentage = (current_question_index / total_questions * 100) if total_questions > 0 else 0
        
        # Render template based on session status
        if session_status == SESSION_PENDING:
            # Load data for results template
            current_question = None
            participants_map = {}
            
            if current_question_uuid:
                # Get current question data
                questions = session_data.get('questions', {})
                if current_question_uuid in questions:
                    current_question = questions[current_question_uuid]
                
                # Create participants map
                for participant in session_data.get('participants', []):
                    participants_map[participant['uuid']] = participant
            
            # Get answer statistics
            answers_statistics = session_data.get('answers_statistics', {})
            
            # Calculate enhanced statistics for results display
            enhanced_stats = {}
            if current_question_uuid:
                try:
                    enhanced_stats_result = LiveSessionService.calculate_enhanced_statistics(
                        username, presentation_id, session_id, current_question_uuid
                    )
                    if enhanced_stats_result.get('success'):
                        enhanced_stats = enhanced_stats_result
                except Exception:
                    # If enhanced stats fail, continue with basic stats
                    pass
            
            return render_template(
                'instructor/session_instructor_question_result.html',
                presentation=presentation,
                session_data=session_data,
                session_id=session_id,
                current_question=current_question,
                current_question_index=current_question_index,
                total_questions=total_questions,
                progress_percentage=progress_percentage,
                answer_statistics=answers_statistics,
                participants_map=participants_map,
                enhanced_stats=enhanced_stats
            )
        
        # Check if session is active
        elif session_status != SESSION_ACTIVE:
            flash('Session not found or not active', FLASH_ERROR)
            return redirect(url_for('sessions.run_presentation', presentation_id=presentation_id))

        # Calculate initial timing and progress values for active session
        timing_info = None
        initial_time_remaining = 0
        is_time_expired = False
        
        try:
            # Get timing information
            timing_info = LiveSessionService.get_session_timing(username, presentation_id, session_id)
            initial_time_remaining = timing_info.get('time_remaining', 0) or 0
            is_time_expired = LiveSessionService.is_question_time_expired(username, presentation_id, session_id)
            
        except Exception:
            # If timing service fails, continue with default values
            pass

        return render_template(
            'instructor/session_instructor_question.html',
            presentation=presentation,
            session_data=session_data,
            session_id=session_id,
            timing_info=timing_info,
            current_question_index=current_question_index,
            total_questions=total_questions,
            progress_percentage=progress_percentage,
            initial_time_remaining=initial_time_remaining,
            is_time_expired=is_time_expired
        )
    except Exception as e:
        flash(f'Failed to load session: {str(e)}', FLASH_ERROR)
        return redirect(url_for('sessions.run_presentation', presentation_id=presentation_id))

@routes.route('/presentations/<presentation_id>/live_session/<session_id>/end_session', methods=['POST'])
@require_instructor
def end_session(presentation_id, session_id):
    """
    End the current live session.
    
    Updates session status to completed and redirects to presentation view page.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id, json_response=True)
    if not isinstance(result, Presentation):
        return result

    try:
        # End the session
        SessionService.end_session(username, presentation_id, session_id)
        
        # Redirect to presentation view page
        return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))
    except Exception as e:
        flash(f'Failed to end session: {str(e)}', FLASH_ERROR)
        return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))

@routes.route('/presentations/<presentation_id>/live_session/<session_id>/show_results', methods=['POST'])
@require_instructor
def show_question_results(presentation_id, session_id):
    """
    Calculate and display answer statistics for the current question.
    
    Processes the current question's answers, calculates statistics,
    stores them in the session data, and redirects to the results page.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id)
    if not isinstance(result, Presentation):
        return result
    presentation = result

    try:
        # Load session data
        session_data = SessionService.get_session(username, presentation_id, session_id)
        
        # Check if session is active
        if not SessionService.is_session_active(username, presentation_id, session_id):
            flash('Session not found or not active', FLASH_ERROR)
            return redirect(url_for('sessions.run_presentation', presentation_id=presentation_id))
        
        # Get current question UUID
        current_question_uuid = session_data.get('current_question_uuid')
        if not current_question_uuid:
            flash('No active question to show results for', FLASH_ERROR)
            return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))
        
        # Calculate statistics using service method
        try:
            result = LiveSessionService.calculate_statistics(
                username, presentation_id, session_id, current_question_uuid
            )
            
            if not result['success']:
                flash(f"Failed to calculate statistics: {result.get('error', 'Unknown error')}", FLASH_ERROR)
                return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))
            
            # Extract data from service result
            statistics = result['statistics']
            participants_map = result['participants_map']
            current_question = result['current_question']
            
            # Update session status to pending
            status_updated = LiveSessionService.update_session_status(
                username, presentation_id, session_id, SESSION_PENDING
            )
            
            if not status_updated:
                flash('Warning: Failed to update session status', FLASH_ERROR)
                
        except Exception as e:
            flash(f'Failed to calculate answer statistics: {str(e)}', FLASH_ERROR)
            return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))
        
        # Redirect to live_session endpoint which will check status and render appropriate template
        return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))
        
    except Exception as e:
        flash(f'Failed to show results: {str(e)}', FLASH_ERROR)
        return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))

@routes.route('/presentations/<presentation_id>/live_session/<session_id>/next_question', methods=['POST'])
@require_instructor
def next_question(presentation_id, session_id):
    """
    Move to the next question in the session.
    
    Advances the session to the next question and redirects back to the live session page.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id)
    if not isinstance(result, Presentation):
        return result

    try:
        # Move to next question using the live session service
        LiveSessionService.move_to_next_question(
            username, presentation_id, session_id
        )
        
        # Update session status to active
        status_updated = LiveSessionService.update_session_status(
            username, presentation_id, session_id, SESSION_ACTIVE
        )
        
        if not status_updated:
            flash('Warning: Failed to update session status to active', FLASH_ERROR)
        
        # Redirect back to the live session page
        return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))
        
    except ValidationError as e:
        # Check if this is the "no more questions" error
        if "No more questions available" in str(e):
            # Change session status to done
            try:
                SessionService.set_status(username, presentation_id, session_id, SESSION_DONE)
                SessionService.calculate_participants_points(username, presentation_id, session_id)
                flash('Session completed! All questions have been answered.', FLASH_SUCCESS)
                # Redirect to the result page
                return redirect(url_for('sessions.session_result', presentation_id=presentation_id, session_id=session_id))
            except Exception as status_error:
                flash(f'Session completed but failed to update status: {str(status_error)}', FLASH_WARNING)
                return redirect(url_for('sessions.session_result', presentation_id=presentation_id, session_id=session_id))
        else:
            # Handle other ValidationError cases
            flash(f'Validation error: {str(e)}', FLASH_ERROR)
            return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))
        
    except Exception as e:
        flash(f'Failed to move to next question: {str(e)}', FLASH_ERROR)
        return redirect(url_for('sessions.live_session', presentation_id=presentation_id, session_id=session_id))

@routes.route('/presentations/<presentation_id>/live_session/<session_id>/timing', methods=['GET'])
@require_instructor
def get_session_timing(presentation_id, session_id):
    """
    Return current session timing as JSON for JavaScript synchronization.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id, json_response=True)
    if not isinstance(result, Presentation):
        return result

    try:
        timing_info = LiveSessionService.get_session_timing(username, presentation_id, session_id)
        return jsonify(timing_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes.route('/presentations/<presentation_id>/sessions/<session_id>/result')
@require_instructor
def session_result(presentation_id, session_id):
    """
    Display the final results for a completed session.
    
    Shows comprehensive session statistics, participant performance,
    and overall results for the completed session.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id)
    if not isinstance(result, Presentation):
        return result
    presentation = result

    try:
        # Load session data
        session_data = SessionService.get_session(username, presentation_id, session_id)
        
        # Get session statistics
        session_stats = SessionService.get_session_statistics(username, presentation_id, session_id)
        
        # Calculate comprehensive results
        participants = session_data.get('participants', [])
        questions = session_data.get('questions', {})
        objectives = session_data.get('objectives', {})
        
        # Calculate participant performance using service function
        participant_results = SessionService.calculate_participant_performance(username, presentation_id, session_id)
        
        # Calculate question statistics
        question_stats = []
        users_answers = session_data.get('users_answers', {})
        
        for question_uuid, question in questions.items():
            # Get all answers for this question
            total_answers = 0
            correct_answers = 0
            correct_indices = set(question.get('correct_indices', []))
            
            for participant_uuid, participant_answers in users_answers.items():
                if question_uuid in participant_answers:
                    total_answers += 1
                    user_answer = participant_answers[question_uuid]
                    
                    # Handle both single answer (int) and multiple answers (list)
                    if isinstance(user_answer, list):
                        # Multiple choice: check if all selected indices are correct
                        user_answer_set = set(user_answer)
                        if user_answer_set == correct_indices:
                            correct_answers += 1
                    else:
                        # Single choice: check if answer matches correct index
                        if user_answer in correct_indices:
                            correct_answers += 1
            
            correct_percentage = (correct_answers / total_answers * 100) if total_answers > 0 else 0
            
            question_stats.append({
                'uuid': question_uuid,
                'question_text': question.get('text', 'Unknown Question'),
                'total_answers': total_answers,
                'correct_answers': correct_answers,
                'correct_percentage': round(correct_percentage, 1)
            })
        
        # Calculate objective performance using service function
        objective_stats = SessionService.calculate_objectives_performance(username, presentation_id, session_id, question_stats)
        
        # Calculate overall session statistics
        total_participants = len(participants)
        total_questions = len(questions)
        avg_score = sum(p['score_percentage'] for p in participant_results) / total_participants if total_participants > 0 else 0
        
        return render_template(
            'instructor/session_instructor_result.html',
            presentation=presentation,
            session_data=session_data,
            session_stats=session_stats,
            participant_results=participant_results,
            question_stats=question_stats,
            objective_stats=objective_stats,
            total_participants=total_participants,
            total_questions=total_questions,
            avg_score=round(avg_score, 1),
            session_id=session_id
        )
        
    except Exception as e:
        flash(f'Failed to load session results: {str(e)}', FLASH_ERROR)
        return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))
