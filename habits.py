"""
Habits Blueprint for HabitFlow
Handles all CRUD operations for habits: Create, Read, Update, Delete, Complete
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Habit
from forms import HabitForm
from datetime import date, timedelta
from models import Habit, CompletionLog

# Create habits blueprint
habits_bp = Blueprint('habits', __name__)


@habits_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Main dashboard showing all user's habits.
    Protected route - must be logged in to access.
    """
    # Get all habits for the current logged-in user
    user_habits = Habit.query.filter_by(user_id=current_user.id).order_by(Habit.created_at.desc()).all()
    
    # Calculate statistics
    total_habits = len(user_habits)
    active_streaks = sum(1 for habit in user_habits if habit.streak_count > 0)
    longest_streak = max([habit.streak_count for habit in user_habits], default=0)
    
    # Calculate completion rate (habits completed today)
    today = date.today()
    completed_today = sum(1 for habit in user_habits if habit.last_completed == today)
    completion_rate = int((completed_today / total_habits * 100)) if total_habits > 0 else 0
    
    stats = {
        'total_habits': total_habits,
        'active_streaks': active_streaks,
        'longest_streak': longest_streak,
        'completion_rate': completion_rate
    }
    
    return render_template('dashboard.html', habits=user_habits, stats=stats)


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
    
    habit = Habit.query.get_or_404(habit_id)
    
    # Security: ensure user owns this habit
    if habit.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('habits.dashboard'))
    
    today = date.today()
    
    # Check if already completed today
    if habit.last_completed == today:
        flash(f'"{habit.name}" already completed today!', 'info')
        return redirect(url_for('habits.dashboard'))
    
    # Update streak logic
    if habit.last_completed == today - timedelta(days=1):
        # Completed yesterday - streak continues
        habit.streak_count += 1
    else:
        # Streak broken or first completion - reset to 1
        habit.streak_count = 1
    
    # Update last completed date
    habit.last_completed = today
    
    # Log this completion for history tracking
    completion = CompletionLog(habit_id=habit.id, completed_at=today)
    db.session.add(completion)
    
    db.session.commit()
    
    flash(f'🎉 "{habit.name}" completed! Streak: {habit.streak_count} days', 'success')
    return redirect(url_for('habits.dashboard'))