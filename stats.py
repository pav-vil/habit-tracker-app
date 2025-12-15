# stats.py - Statistics blueprint for HabitFlow
# Provides data visualization for habit tracking progress

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import Habit
from datetime import datetime, timedelta
from sqlalchemy import func

# Create blueprint for stats routes
stats_bp = Blueprint('stats', __name__, url_prefix='/stats')


@stats_bp.route('/')
@login_required
def stats_dashboard():
    """Main statistics page with charts and insights."""
    
    # Get all habits for current user
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    
    # Calculate overview stats
    total_habits = len(habits)
    active_streaks = sum(1 for h in habits if h.streak_count > 0)
    longest_streak = max((h.streak_count for h in habits), default=0)
    
    # Get completion data for the last 30 days
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    
    # Build streak history data for line chart
    streak_data = []
    for habit in habits:
        streak_data.append({
            'name': habit.name,
            'streak': habit.streak_count,
            'last_completed': habit.last_completed.isoformat() if habit.last_completed else None
        })
    
    return render_template('stats.html',
                       habits=habits,
                       total_habits=total_habits,
                       active_streaks=active_streaks,
                       longest_streak=longest_streak,
                       streak_data=streak_data,
                       now=datetime.now())

@stats_bp.route('/api/chart-data')
@login_required
def chart_data():
    """API endpoint returning JSON data for charts."""
    from models import CompletionLog
    
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    
    # Prepare data for streak bar chart
    habit_names = [h.name for h in habits]
    streak_counts = [h.streak_count for h in habits]
    
    # Day of week analysis from completion logs
    day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    completions_by_day = [0, 0, 0, 0, 0, 0, 0]
    
    # Get all completion logs for user's habits
    habit_ids = [h.id for h in habits]
    if habit_ids:
        logs = CompletionLog.query.filter(CompletionLog.habit_id.in_(habit_ids)).all()
        for log in logs:
            day_index = log.completed_at.weekday()  # 0=Monday, 6=Sunday
            completions_by_day[day_index] += 1
    
    # Last 14 days trend data for line chart
    today = datetime.now().date()
    trend_labels = []
    trend_data = []
    
    for i in range(13, -1, -1):  # 14 days, oldest first
        day = today - timedelta(days=i)
        trend_labels.append(day.strftime('%b %d'))
        
        # Count completions on this day
        if habit_ids:
            count = CompletionLog.query.filter(
                CompletionLog.habit_id.in_(habit_ids),
                CompletionLog.completed_at == day
            ).count()
        else:
            count = 0
        trend_data.append(count)
    
    return jsonify({
        'habitNames': habit_names,
        'streakCounts': streak_counts,
        'dayLabels': day_labels,
        'completionsByDay': completions_by_day,
        'trendLabels': trend_labels,
        'trendData': trend_data,
        'totalHabits': len(habits)
    })

