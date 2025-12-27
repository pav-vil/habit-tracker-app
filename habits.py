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

    # Check if user is over habit limit (for free users after downgrade)
    over_limit = False
    habits_to_archive = 0
    if not current_user.is_premium_active():
        if total_habits > current_user.habit_limit:
            over_limit = True
            habits_to_archive = total_habits - current_user.habit_limit

    return render_template(
        'dashboard.html',
        habits=user_habits,
        stats=stats,
        pagination=pagination,
        over_limit=over_limit,
        habits_to_archive=habits_to_archive
    )


@habits_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_habit():
    """
    Create a new habit.
    GET: Show form
    POST: Process form and create habit
    """
    # Check if user can add more habits
    if not current_user.can_add_more_habits():
        flash(
            f'You have reached your habit limit ({current_user.habit_limit} habits). '
            f'Upgrade to premium for unlimited habits!',
            'warning'
        )
        return redirect(url_for('subscription.pricing'))

    form = HabitForm()

    if form.validate_on_submit():
        # Double-check limit before creating (race condition protection)
        if not current_user.can_add_more_habits():
            flash('Habit limit reached. Please upgrade to premium.', 'danger')
            return redirect(url_for('subscription.pricing'))

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