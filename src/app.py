from flask import Flask, render_template, request, jsonify, session, url_for, flash, redirect
from adaptive_learning import AdaptiveLearningSystem
from question_generation import QuestionGenerator
from database import db  # Import our database class
import os
from datetime import datetime
import json
import asyncio
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import random

# Get the absolute path of the project root directory (one level up from src)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__,
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))
app.secret_key = os.urandom(24)

# Initialize systems
adaptive_system = AdaptiveLearningSystem()
question_generator = QuestionGenerator()

def async_route(f):
    """Decorator to handle async routes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    wrapper.__name__ = f.__name__
    return wrapper

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('login.html')
        
        try:
            # Attempt to sign in with Supabase
            result = db.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if result and result.user:
                # Check if email is verified
                if not result.user.email_confirmed_at:
                    flash('Please verify your email before logging in.', 'warning')
                    return render_template('login.html')
                
                session['user_id'] = result.user.id
                session['email'] = result.user.email
                
                # Create user progress record if it doesn't exist
                try:
                    db.create_user(result.user.id, email)
                except Exception as e:
                    app.logger.info(f"User record might already exist: {str(e)}")
                
                try:
                    db.update_user_login(result.user.id)
                except Exception as e:
                    app.logger.warning(f"Could not update login time: {str(e)}")
                
                flash('Successfully logged in!', 'success')
                return redirect(url_for('index'))
            else:
                app.logger.error("Login result was empty or invalid")
                flash('Invalid login credentials.', 'danger')
                return render_template('login.html')
            
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            
            if 'Email not confirmed' in str(e):
                flash('Please verify your email before logging in.', 'warning')
            elif 'Invalid login credentials' in str(e):
                flash('Invalid email or password.', 'danger')
            else:
                flash('Login failed. Please try again.', 'danger')
            
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Register user with Supabase
            result = db.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if result.user:
                flash('Registration successful! Please check your email to verify your account.', 'success')
                return redirect(url_for('login'))
            
        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    flash('Successfully logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Render the main page."""
    if 'user_id' not in session:
        return render_template('landing.html')

    try:
        # Reload topics data and clear user state
        adaptive_system.load_data()
        
        # Get user's progress from database
        progress_result = db.get_user_progress(session['user_id'])
        
        # Extract data from Supabase response
        progress_data = progress_result.data if hasattr(progress_result, 'data') else []
        
        # Get learning path
        learning_path = adaptive_system.generate_learning_path(session['user_id'])
        
        # Structure the subjects data
        subjects_data = {}
        
        # First, initialize all subjects from topics with default values
        for topic in adaptive_system.topics_data.get('topics', []):
            subjects_data[topic['title']] = {
                'difficulty_level': 'beginner',
                'score': 0,
                'mastered': False,
                'last_attempt': None,
                'history': [],
                'subtopics': []
            }
            # Add subtopics
            for subtopic in topic.get('subtopics', []):
                subjects_data[topic['title']]['subtopics'].append({
                    'title': subtopic['title'],
                    'score': 0,
                    'difficulty_level': 'beginner',
                    'mastered': False
                })
        
        # Then update with actual progress data
        for subject_progress in progress_data:
            if isinstance(subject_progress, dict):
                subject = subject_progress.get('subject')
                if subject and subject in subjects_data:
                    subjects_data[subject].update({
                        'difficulty_level': subject_progress.get('difficulty_level', 'beginner'),
                        'score': subject_progress.get('current_score', 0),
                        'mastered': subject_progress.get('mastered', False),
                        'last_attempt': subject_progress.get('last_attempt')
                    })
        
        # Add test history to each subject
        for subject in subjects_data:
            history_result = db.get_test_history(
                user_id=session['user_id'],
                subject=subject,
                limit=10
            )
            if hasattr(history_result, 'data'):
                history_data = history_result.data
                if history_data:
                    subjects_data[subject]['history'] = [
                        {
                            'attempt_number': idx + 1,
                            'score': round(item['score'] * 100, 1),
                            'date': item['test_date'],
                            'difficulty_level': item['difficulty_level']
                        }
                        for idx, item in enumerate(history_data)
                    ]
        
        return render_template('index.html',
                             learning_path=learning_path,
                             progress={'subjects': subjects_data},
                             user_id=session['user_id'],
                             topics_data=adaptive_system.topics_data)
                             
    except Exception as e:
        flash("An error occurred while loading your progress. Please try again.", "error")
        return render_template('error.html', error=str(e))

@app.route('/start_topic/<topic>')
@async_route
async def start_topic(topic):
    """Start learning a specific topic."""
    if 'user_id' not in session:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        # Get subject from topic string
        subject = topic.split(' - ')[0]
        
        # Get user's current progress from database
        progress_result = db.get_user_progress(session['user_id'])
        current_difficulty = 'beginner'  # default
        
        # Find current difficulty level for the subject
        if hasattr(progress_result, 'data'):
            for item in progress_result.data:
                if isinstance(item, dict) and item.get('subject') == subject:
                    current_difficulty = item.get('difficulty_level', 'beginner')
                    break
        
        try:
            # Generate questions
            questions = await question_generator.generate_questions_for_topic(
                topic=topic,
                num_questions=10,
                difficulty_level=current_difficulty
            )
            
            if not questions:
                return render_template('topic.html',
                                    topic=topic,
                                    subject=subject,
                                    questions=None,
                                    error="No questions were generated. Please try again.",
                                    difficulty_level=current_difficulty)
            
            # Store questions in session for validation
            session['current_test'] = {
                'topic': topic,
                'questions': questions,
                'difficulty_level': current_difficulty,
                'start_time': datetime.now().isoformat()
            }
            
            return render_template('topic.html',
                                topic=topic,
                                subject=subject,
                                questions=questions,
                                difficulty_level=current_difficulty)
            
        except Exception as e:
            app.logger.error(f"Question generation failed: {str(e)}")
            error_message = "Question generation failed. Please try again later."
            
            if "Invalid JSON response" in str(e):
                error_message = "The question generation service returned an invalid response. Please try again."
            elif "No valid questions found" in str(e):
                error_message = "Could not generate valid questions. Please try again."
            elif "API call failed" in str(e):
                error_message = "Could not connect to the question generation service. Please try again later."
            
            return render_template('topic.html',
                                topic=topic,
                                subject=subject,
                                questions=None,
                                error=error_message,
                                difficulty_level=current_difficulty)
            
    except Exception as e:
        app.logger.error(f"Error in start_topic route: {str(e)}")
        return render_template('error.html', error="An unexpected error occurred. Please try again later.")

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Handle answer submission and update progress."""
    try:
        data = request.get_json()
        subject = data.get('subject')
        score = data.get('total_correct') / data.get('num_questions')
        time_taken = data.get('time_taken', 0)
        num_questions = data.get('num_questions', 0)
        total_correct = data.get('total_correct', 0)

        # Get current difficulty level
        progress_result = db.get_user_progress(session['user_id'])
        current_difficulty = 'beginner'
        
        # Extract data from Supabase response
        progress_data = progress_result.data if hasattr(progress_result, 'data') else []
        
        # Find current difficulty level for the subject
        for item in progress_data:
            if isinstance(item, dict) and item.get('subject') == subject:
                current_difficulty = item.get('difficulty_level', 'beginner')
                break

        # Store test result
        db.add_test_result(
            user_id=session['user_id'],
            subject=subject,
            score=score,
            difficulty_level=current_difficulty,
            time_taken=time_taken,
            num_questions=num_questions,
            correct_answers=total_correct
        )

        # Check if score meets advancement criteria
        if score >= 0.7:  # 70% or higher
            new_difficulty = {
                'beginner': 'intermediate',
                'intermediate': 'advanced',
                'advanced': 'advanced'
            }.get(current_difficulty, 'beginner')

            if new_difficulty != current_difficulty:
                # Update difficulty level without resetting score
                db.update_subject_progress(
                    user_id=session['user_id'],
                    subject=subject,
                    score=score,  # Keep the score that achieved advancement
                    difficulty_level=new_difficulty,
                    mastered=(new_difficulty == 'advanced')
                )
                
                return jsonify({
                    'score': score,
                    'difficulty_changed': True,
                    'new_difficulty': new_difficulty,
                    'message': f'Congratulations! You\'ve advanced to {new_difficulty} level! Get ready for more challenging questions.'
                })
        else:
            # Update progress without changing difficulty
            db.update_subject_progress(
                user_id=session['user_id'],
                subject=subject,
                score=score,
                difficulty_level=current_difficulty,
                mastered=False
            )

        return jsonify({
            'score': score,
            'difficulty_changed': False,
            'message': 'Score recorded successfully'
        })

    except Exception as e:
        app.logger.error(f"Error in submit_answer route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/progress')
def get_progress():
    """Get user's progress report."""
    if 'user_id' not in session:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        progress = adaptive_system.get_progress_report(session['user_id'])
        return jsonify(progress)
    except Exception as e:
        app.logger.error(f"Error in get_progress route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/mock_test')
@login_required
def mock_test():
    """Render the mock test page."""
    return render_template('mock_template.html')

@app.route('/api/get_mock_questions')
@login_required
@async_route
async def get_mock_questions():
    """Get questions for mock test from all subjects."""
    try:
        # Import mock_generator functionality
        from mock_generator import (
            get_aptitude_questions,
            get_math_questions,
            get_digital_logic_questions,
            get_computer_networks_questions,
            get_machine_learning_questions,
            get_software_engineering_questions,
            get_cloud_computing_questions,
            get_cybersecurity_questions
        )
        
        # Get questions from each subject sequentially
        all_questions = (
            await get_aptitude_questions() +
            await get_math_questions() +
            await get_digital_logic_questions() +
            await get_computer_networks_questions() +
            await get_machine_learning_questions() +
            await get_software_engineering_questions() +
            await get_cloud_computing_questions() +
            await get_cybersecurity_questions()
        )
        
        return jsonify(all_questions)
    except Exception as e:
        app.logger.error(f"Error getting mock questions: {str(e)}")
        return jsonify({'error': 'Failed to load questions'}), 500

@app.route('/api/submit_mock_answers', methods=['POST'])
@login_required
def submit_mock_answers():
    """Handle mock test answer submission."""
    try:
        data = request.get_json()
        answers = data.get('answers', [])
        
        # Get the questions that were asked
        questions = session.get('mock_questions', [])
        
        if not questions or len(answers) != len(questions):
            return jsonify({'error': 'Invalid submission'}), 400
        
        # Calculate score
        correct_count = 0
        results_by_subject = {}
        
        for idx, (question, user_answer) in enumerate(zip(questions, answers)):
            if user_answer == str(question['correct_answer']):  # Convert to string since form values are strings
                correct_count += 1
            
            # Track subject-wise performance
            subject = question['subject']
            if subject not in results_by_subject:
                results_by_subject[subject] = {'correct': 0, 'total': 0}
            results_by_subject[subject]['total'] += 1
            if user_answer == str(question['correct_answer']):
                results_by_subject[subject]['correct'] += 1
        
        # Calculate overall score
        total_questions = len(questions)
        score_percentage = (correct_count / total_questions) * 100
        
        # Store test result in database
        db.add_test_result(
            user_id=session['user_id'],
            subject='Mock Test',
            score=score_percentage / 100,  # Convert to decimal
            difficulty_level='mixed',
            time_taken=0,  # You could add a timer if needed
            num_questions=total_questions,
            correct_answers=correct_count
        )
        
        # Prepare response
        response = {
            'score': f"{correct_count}/{total_questions} ({score_percentage:.1f}%)",
            'subject_breakdown': {},
            'message': ''
        }
        
        # Add subject-wise breakdown
        for subject, results in results_by_subject.items():
            subject_percentage = (results['correct'] / results['total']) * 100
            response['subject_breakdown'][subject] = {
                'score': f"{results['correct']}/{results['total']} ({subject_percentage:.1f}%)"
            }
        
        # Add encouraging message based on score
        if score_percentage >= 70:
            response['message'] = "Excellent! You've demonstrated a strong understanding across multiple subjects."
        elif score_percentage >= 50:
            response['message'] = "Good effort! Keep practicing to improve your score further."
        else:
            response['message'] = "Keep practicing! Focus on the subjects where you scored lower."
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Error submitting mock answers: {str(e)}")
        return jsonify({'error': 'Failed to submit answers'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    # Ensure template and static directories exist
    os.makedirs(os.path.join(project_root, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'static'), exist_ok=True)
    
    # Run the app in debug mode
    app.run(debug=True) 