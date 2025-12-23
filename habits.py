"""
Habits Blueprint for HabitFlow
Handles all CRUD operations for habits: Create, Read, Update, Delete, Complete
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Habit, CompletionLog
from forms import HabitForm
from datetime import date, timedelta

# Create habits blueprint
habits_bp = Blueprint('habits', __name__)


@habits_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Main dashboard showing all user's habits.
    Protected route - must be logged in to access.
    """
    # Get page number from query parameters (default to 1)
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of habits per page

    # Get paginated non-archived habits for the current logged-in user
    pagination = Habit.query.filter_by(
        user_id=current_user.id,
        archived=False
    ).order_by(Habit.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    user_habits = pagination.items

    # Calculate statistics (based on all habits, not just current page)
    all_habits = Habit.query.filter_by(user_id=current_user.id, archived=False).all()
    total_habits = len(all_habits)
    active_streaks = sum(1 for habit in all_habits if habit.streak_count > 0)
    longest_streak = max([habit.streak_count for habit in all_habits], default=0)

    # Calculate completion rate (habits completed today)
    today = current_user.get_user_date()
    completed_today = sum(1 for habit in all_habits if habit.last_completed == today)
    completion_rate = int((completed_today / total_habits * 100)) if total_habits > 0 else 0

    stats = {
        'total_habits': total_habits,
        'active_streaks': active_streaks,
        'longest_streak': longest_streak,
        'completion_rate': completion_rate
    }

    # Motivational quotes that rotate daily
    motivational_quotes = [
        {"quote": "Small daily improvements are the key to staggering long-term results.", "author": "Unknown"},
        {"quote": "Success is the sum of small efforts repeated day in and day out.", "author": "Robert Collier"},
        {"quote": "A journey of a thousand miles begins with a single step.", "author": "Lao Tzu"},
        {"quote": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
        {"quote": "You don't have to be great to start, but you have to start to be great.", "author": "Zig Ziglar"},
        {"quote": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
        {"quote": "Don't watch the clock; do what it does. Keep going.", "author": "Sam Levenson"},
        {"quote": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
        {"quote": "The best time to plant a tree was 20 years ago. The second best time is now.", "author": "Chinese Proverb"},
        {"quote": "Your future is created by what you do today, not tomorrow.", "author": "Unknown"},
        {"quote": "Excellence is not a destination; it is a continuous journey that never ends.", "author": "Brian Tracy"},
        {"quote": "Motivation is what gets you started. Habit is what keeps you going.", "author": "Jim Ryun"},
        {"quote": "We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "author": "Aristotle"},
        {"quote": "The difference between who you are and who you want to be is what you do.", "author": "Unknown"},
        {"quote": "Discipline is choosing between what you want now and what you want most.", "author": "Unknown"},
        {"quote": "The pain of discipline is far less than the pain of regret.", "author": "Unknown"},
        {"quote": "Success doesn't come from what you do occasionally, it comes from what you do consistently.", "author": "Unknown"},
        {"quote": "First we make our habits, then our habits make us.", "author": "Charles C. Noble"},
        {"quote": "You'll never change your life until you change something you do daily.", "author": "John C. Maxwell"},
        {"quote": "Consistency is the true foundation of trust. Either keep your promises or do not make them.", "author": "Roy T. Bennett"},
        {"quote": "The only impossible journey is the one you never begin.", "author": "Tony Robbins"},
        {"quote": "Don't count the days, make the days count.", "author": "Muhammad Ali"},
        {"quote": "Discipline equals freedom.", "author": "Jocko Willink"},
        {"quote": "The harder you work for something, the greater you'll feel when you achieve it.", "author": "Unknown"},
        {"quote": "Dream bigger. Do bigger.", "author": "Unknown"},
        {"quote": "Little by little, a little becomes a lot.", "author": "Tanzanian Proverb"},
        {"quote": "It's not about perfect. It's about effort.", "author": "Jillian Michaels"},
        {"quote": "Start where you are. Use what you have. Do what you can.", "author": "Arthur Ashe"},
        {"quote": "Your only limit is you.", "author": "Unknown"},
        {"quote": "One day or day one. You decide.", "author": "Unknown"},
    ]

    # Select quote based on day of year (ensures same quote all day)
    day_of_year = today.timetuple().tm_yday
    daily_quote = motivational_quotes[day_of_year % len(motivational_quotes)]

    return render_template('dashboard.html', habits=user_habits, stats=stats, pagination=pagination, daily_quote=daily_quote)


@habits_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_habit():
    """
    Create a new habit.
    GET: Show form
    POST: Process form and create habit
    """
    form = HabitForm()
    
    if form.validate_on_submit():
        # Create new habit
        new_habit = Habit(
            user_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            streak_count=0
        )
        
        # Save to database
        db.session.add(new_habit)
        db.session.commit()
        
        flash(f'Habit "{new_habit.name}" created successfully!', 'success')
        return redirect(url_for('habits.dashboard'))
    
    return render_template('habit_form.html', form=form, title='Add New Habit')


@habits_bp.route('/<int:habit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """
    Edit an existing habit.
    GET: Show form pre-filled with habit data
    POST: Update habit in database
    """
    # Get the habit (404 if not found)
    habit = Habit.query.get_or_404(habit_id)
    
    # Security check: Make sure this habit belongs to current user
    if habit.user_id != current_user.id:
        flash('You do not have permission to edit this habit.', 'danger')
        return redirect(url_for('habits.dashboard'))
    
    form = HabitForm()
    
    if form.validate_on_submit():
        # Update habit
        habit.name = form.name.data
        habit.description = form.description.data
        
        db.session.commit()
        
        flash(f'Habit "{habit.name}" updated successfully!', 'success')
        return redirect(url_for('habits.dashboard'))
    
    # Pre-fill form with current data (GET request)
    elif request.method == 'GET':
        form.name.data = habit.name
        form.description.data = habit.description
    
    return render_template('habit_form.html', form=form, title='Edit Habit', habit=habit)


@habits_bp.route('/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """
    Delete a habit.
    Only accepts POST requests (for security - prevents accidental deletion via GET)
    """
    habit = Habit.query.get_or_404(habit_id)
    
    # Security check: Make sure this habit belongs to current user
    if habit.user_id != current_user.id:
        flash('You do not have permission to delete this habit.', 'danger')
        return redirect(url_for('habits.dashboard'))
    
    habit_name = habit.name
    
    # Delete from database
    db.session.delete(habit)
    db.session.commit()
    
    flash(f'Habit "{habit_name}" deleted successfully.', 'info')
    return redirect(url_for('habits.dashboard'))


@habits_bp.route('/<int:habit_id>/complete', methods=['POST'])
@login_required
def complete_habit(habit_id):
    """Mark a habit as complete for today and log it."""
    from models import db, CompletionLog
    from flask import request

    # Debug: Print request data
    print(f"[DEBUG] Complete habit request received for habit_id: {habit_id}")
    print(f"[DEBUG] Request method: {request.method}")
    print(f"[DEBUG] Request form data: {request.form}")
    print(f"[DEBUG] Has CSRF token: {'csrf_token' in request.form}")

    habit = Habit.query.get_or_404(habit_id)

    # Security: ensure user owns this habit
    if habit.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('habits.dashboard'))

    today = current_user.get_user_date()

    # Use the model's complete() method to update streak and longest_streak
    if not habit.complete(today):
        flash(f'"{habit.name}" already completed today!', 'info')
        return redirect(url_for('habits.dashboard'))

    # Log this completion for history tracking
    completion = CompletionLog(habit_id=habit.id, completed_at=today)
    db.session.add(completion)

    db.session.commit()

    flash(f'🎉 "{habit.name}" completed! Streak: {habit.streak_count} days', 'success')
    return redirect(url_for('habits.dashboard'))


@habits_bp.route('/<int:habit_id>/undo', methods=['POST'])
@login_required
def undo_completion(habit_id):
    """Undo today's completion for a habit."""
    habit = Habit.query.get_or_404(habit_id)

    # Security: ensure user owns this habit
    if habit.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('habits.dashboard'))

    today = current_user.get_user_date()

    # Check if completed today
    if habit.last_completed != today:
        flash(f'"{habit.name}" was not completed today!', 'warning')
        return redirect(url_for('habits.dashboard'))

    # Find and delete today's completion log
    completion = CompletionLog.query.filter_by(
        habit_id=habit.id,
        completed_at=today
    ).first()

    if completion:
        db.session.delete(completion)

    # Recalculate streak - find previous completion
    previous_completion = CompletionLog.query.filter(
        CompletionLog.habit_id == habit.id,
        CompletionLog.completed_at < today
    ).order_by(CompletionLog.completed_at.desc()).first()

    if previous_completion:
        # Check if previous was yesterday
        yesterday = today - timedelta(days=1)
        if previous_completion.completed_at == yesterday:
            # Decrement streak
            habit.streak_count = max(0, habit.streak_count - 1)
        else:
            # Was not consecutive, reset to 0
            habit.streak_count = 0
        habit.last_completed = previous_completion.completed_at
    else:
        # No previous completions
        habit.streak_count = 0
        habit.last_completed = None

    db.session.commit()

    flash(f'Undid completion for "{habit.name}"', 'info')
    return redirect(url_for('habits.dashboard'))


@habits_bp.route('/<int:habit_id>/archive', methods=['POST'])
@login_required
def archive_habit(habit_id):
    """Archive a habit (soft delete)."""
    from flask import request

    # Debug: Print request data
    print(f"[DEBUG] Archive habit request received for habit_id: {habit_id}")
    print(f"[DEBUG] Request form data: {request.form}")
    print(f"[DEBUG] Has CSRF token: {'csrf_token' in request.form}")

    habit = Habit.query.get_or_404(habit_id)

    # Security: ensure user owns this habit
    if habit.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('habits.dashboard'))

    habit.archived = True
    db.session.commit()

    flash(f'"{habit.name}" has been archived.', 'info')
    return redirect(url_for('habits.dashboard'))


@habits_bp.route('/<int:habit_id>/unarchive', methods=['POST'])
@login_required
def unarchive_habit(habit_id):
    """Unarchive a habit (restore)."""
    habit = Habit.query.get_or_404(habit_id)

    # Security: ensure user owns this habit
    if habit.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('habits.archived'))

    habit.archived = False
    db.session.commit()

    flash(f'"{habit.name}" has been restored.', 'success')
    return redirect(url_for('habits.dashboard'))


@habits_bp.route('/archived')
@login_required
def archived():
    """View all archived habits."""
    # Get page number from query parameters (default to 1)
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of habits per page

    # Get paginated archived habits
    pagination = Habit.query.filter_by(
        user_id=current_user.id,
        archived=True
    ).order_by(Habit.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template('archived.html', habits=pagination.items, pagination=pagination)


@habits_bp.route('/newsletter-subscribe', methods=['POST'])
@login_required
def newsletter_subscribe():
    """Handle newsletter subscription preference."""
    from flask import jsonify

    try:
        data = request.get_json()
        subscribed = data.get('subscribed', False)

        # Update user's newsletter preference
        current_user.newsletter_subscribed = subscribed
        db.session.commit()

        return jsonify({'success': True, 'subscribed': subscribed})
    except Exception as e:
        print(f"[NEWSLETTER] Error updating subscription: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500