"""
Period Tracking Blueprint
Handles menstrual cycle tracking, predictions, symptoms, and statistics.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, PeriodCycle, PeriodDailyLog, PeriodSettings
from forms import PeriodCycleForm, PeriodDailyLogForm, PeriodSettingsForm
from datetime import datetime, date, timedelta
from sqlalchemy import func
import statistics

periods_bp = Blueprint('periods', __name__, url_prefix='/periods')


# ============================================================================
# HELPER FUNCTIONS - CYCLE PREDICTION & PHASE CALCULATION
# ============================================================================

def predict_next_cycles(user, num_predictions=3):
    """
    Predict next N menstrual cycles based on historical data.

    Args:
        user: User object
        num_predictions: Number of cycles to predict (default: 3)

    Returns:
        List of predicted cycles with confidence scores
    """
    # Get last 6 completed cycles (not predicted)
    completed_cycles = PeriodCycle.query.filter_by(
        user_id=user.id,
        is_predicted=False
    ).filter(
        PeriodCycle.end_date.isnot(None),
        PeriodCycle.cycle_length.isnot(None)
    ).order_by(PeriodCycle.start_date.desc()).limit(6).all()

    # Calculate average cycle length
    if len(completed_cycles) >= 3:
        cycle_lengths = [c.cycle_length for c in completed_cycles]
        avg_length = sum(cycle_lengths) / len(cycle_lengths)

        # Calculate standard deviation for confidence
        if len(cycle_lengths) > 1:
            std_dev = statistics.stdev(cycle_lengths)
            if std_dev < 3:
                confidence = "high"
            elif std_dev < 5:
                confidence = "medium"
            else:
                confidence = "low"
        else:
            confidence = "medium"
    else:
        # Fallback to user's setting if not enough data
        if user.period_settings:
            avg_length = user.period_settings.average_cycle_length
        else:
            avg_length = 28
        confidence = "low"

    # Find last period start
    last_cycle = PeriodCycle.query.filter_by(
        user_id=user.id,
        is_predicted=False
    ).order_by(PeriodCycle.start_date.desc()).first()

    if not last_cycle:
        return []  # No data to predict from

    # Generate predictions
    predictions = []
    period_duration = user.period_settings.average_period_duration if user.period_settings else 5

    for i in range(1, num_predictions + 1):
        predicted_start = last_cycle.start_date + timedelta(days=int(avg_length * i))
        predicted_end = predicted_start + timedelta(days=period_duration - 1)

        predictions.append({
            'start_date': predicted_start,
            'end_date': predicted_end,
            'confidence': confidence,
            'cycle_number': i
        })

    return predictions


def calculate_current_phase(user, current_date=None):
    """
    Calculate current hormonal phase based on cycle day.

    Phases:
    - Menstrual: Days 1-5 (period)
    - Follicular: Days 6-13
    - Ovulation: Days 14-16
    - Luteal: Days 17-28

    Args:
        user: User object
        current_date: Date to calculate for (default: today)

    Returns:
        Dict with phase info or None
    """
    if current_date is None:
        current_date = user.get_user_date() if hasattr(user, 'get_user_date') else date.today()

    # Find most recent cycle that started before or on current_date
    active_cycle = PeriodCycle.query.filter_by(
        user_id=user.id,
        is_predicted=False
    ).filter(
        PeriodCycle.start_date <= current_date
    ).order_by(PeriodCycle.start_date.desc()).first()

    if not active_cycle:
        return None

    # Calculate days since period start
    days_since_start = (current_date - active_cycle.start_date).days + 1

    # Get settings
    if user.period_settings:
        avg_cycle = user.period_settings.average_cycle_length
        period_duration = user.period_settings.average_period_duration
    else:
        avg_cycle = 28
        period_duration = 5

    # Determine phase
    if days_since_start <= period_duration:
        phase = "menstrual"
        phase_emoji = "🩸"
        phase_color = "#ec4899"
    elif days_since_start <= avg_cycle * 0.5:
        phase = "follicular"
        phase_emoji = "🌱"
        phase_color = "#10b981"
    elif days_since_start <= avg_cycle * 0.6:
        phase = "ovulation"
        phase_emoji = "🌸"
        phase_color = "#7c3aed"
    else:
        phase = "luteal"
        phase_emoji = "🌙"
        phase_color = "#f59e0b"

    # Calculate days until next period
    days_until_period = max(0, avg_cycle - days_since_start)

    return {
        'phase': phase,
        'phase_emoji': phase_emoji,
        'phase_color': phase_color,
        'cycle_day': days_since_start,
        'days_until_period': days_until_period,
        'average_cycle': avg_cycle
    }


# ============================================================================
# MAIN ROUTES
# ============================================================================

@periods_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Period tracking settings page"""
    # Get or create settings
    user_settings = PeriodSettings.query.filter_by(user_id=current_user.id).first()

    if not user_settings:
        user_settings = PeriodSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()

    form = PeriodSettingsForm()

    if form.validate_on_submit():
        user_settings.period_tracking_enabled = form.period_tracking_enabled.data
        user_settings.average_cycle_length = form.average_cycle_length.data
        user_settings.average_period_duration = form.average_period_duration.data
        user_settings.reminder_enabled = form.reminder_enabled.data
        user_settings.reminder_days_before = form.reminder_days_before.data or 2
        user_settings.show_on_dashboard = form.show_on_dashboard.data

        db.session.commit()
        flash('Period tracking settings updated successfully!', 'success')
        return redirect(url_for('periods.settings'))

    elif request.method == 'GET':
        # Pre-fill form
        form.period_tracking_enabled.data = user_settings.period_tracking_enabled
        form.average_cycle_length.data = user_settings.average_cycle_length
        form.average_period_duration.data = user_settings.average_period_duration
        form.reminder_enabled.data = user_settings.reminder_enabled
        form.reminder_days_before.data = user_settings.reminder_days_before
        form.show_on_dashboard.data = user_settings.show_on_dashboard

    return render_template('periods/settings.html', form=form, settings=user_settings)


@periods_bp.route('/')
@login_required
def dashboard():
    """Main period tracker dashboard"""
    # Check if period tracking is enabled
    user_settings = PeriodSettings.query.filter_by(user_id=current_user.id).first()

    if not user_settings or not user_settings.period_tracking_enabled:
        flash('Please enable period tracking in settings first.', 'warning')
        return redirect(url_for('periods.settings'))

    # Get current phase info
    phase_info = calculate_current_phase(current_user)

    # Get all cycles (past and predicted)
    all_cycles = PeriodCycle.query.filter_by(
        user_id=current_user.id
    ).order_by(PeriodCycle.start_date.desc()).all()

    # Separate past and predicted cycles
    past_cycles = [c for c in all_cycles if not c.is_predicted]
    predicted_cycles = [c for c in all_cycles if c.is_predicted]

    # Generate new predictions if needed
    if len(predicted_cycles) < 3:
        # Delete old predictions
        PeriodCycle.query.filter_by(
            user_id=current_user.id,
            is_predicted=True
        ).delete()
        db.session.commit()

        # Generate new predictions
        predictions = predict_next_cycles(current_user, 3)
        for pred in predictions:
            new_pred = PeriodCycle(
                user_id=current_user.id,
                start_date=pred['start_date'],
                end_date=pred['end_date'],
                is_predicted=True
            )
            db.session.add(new_pred)
        db.session.commit()

        # Re-fetch predicted cycles
        predicted_cycles = PeriodCycle.query.filter_by(
            user_id=current_user.id,
            is_predicted=True
        ).order_by(PeriodCycle.start_date.asc()).all()

    # Get recent daily logs
    recent_logs = PeriodDailyLog.query.filter_by(
        user_id=current_user.id
    ).order_by(PeriodDailyLog.log_date.desc()).limit(7).all()

    return render_template('periods/dashboard.html',
                         phase_info=phase_info,
                         past_cycles=past_cycles[:6],  # Last 6 cycles
                         predicted_cycles=predicted_cycles,
                         recent_logs=recent_logs,
                         settings=user_settings)


@periods_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_cycle():
    """Add a new period cycle"""
    form = PeriodCycleForm()

    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data

        # Validate dates
        if end_date and end_date < start_date:
            flash('End date cannot be before start date.', 'danger')
            return render_template('periods/add_cycle.html', form=form)

        # Check for overlapping cycles
        existing = PeriodCycle.query.filter_by(
            user_id=current_user.id,
            is_predicted=False
        ).filter(
            PeriodCycle.start_date <= start_date,
            PeriodCycle.end_date >= start_date
        ).first()

        if existing:
            flash('This date overlaps with an existing period cycle.', 'danger')
            return render_template('periods/add_cycle.html', form=form)

        # Create new cycle
        new_cycle = PeriodCycle(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            is_predicted=False
        )

        # Calculate cycle length if this isn't the first cycle
        prev_cycle = PeriodCycle.query.filter_by(
            user_id=current_user.id,
            is_predicted=False
        ).filter(
            PeriodCycle.start_date < start_date
        ).order_by(PeriodCycle.start_date.desc()).first()

        if prev_cycle:
            prev_cycle.cycle_length = (start_date - prev_cycle.start_date).days

        db.session.add(new_cycle)
        db.session.commit()

        flash('Period cycle added successfully!', 'success')
        return redirect(url_for('periods.dashboard'))

    return render_template('periods/add_cycle.html', form=form)


@periods_bp.route('/edit/<int:cycle_id>', methods=['GET', 'POST'])
@login_required
def edit_cycle(cycle_id):
    """Edit an existing period cycle"""
    cycle = PeriodCycle.query.filter_by(
        id=cycle_id,
        user_id=current_user.id,
        is_predicted=False
    ).first_or_404()

    form = PeriodCycleForm()

    if form.validate_on_submit():
        cycle.start_date = form.start_date.data
        cycle.end_date = form.end_date.data

        # Recalculate cycle length
        next_cycle = PeriodCycle.query.filter_by(
            user_id=current_user.id,
            is_predicted=False
        ).filter(
            PeriodCycle.start_date > cycle.start_date
        ).order_by(PeriodCycle.start_date.asc()).first()

        if next_cycle:
            cycle.cycle_length = (next_cycle.start_date - cycle.start_date).days

        db.session.commit()
        flash('Period cycle updated successfully!', 'success')
        return redirect(url_for('periods.dashboard'))

    elif request.method == 'GET':
        form.start_date.data = cycle.start_date
        form.end_date.data = cycle.end_date

    return render_template('periods/edit_cycle.html', form=form, cycle=cycle)


@periods_bp.route('/delete/<int:cycle_id>', methods=['POST'])
@login_required
def delete_cycle(cycle_id):
    """Delete a period cycle"""
    cycle = PeriodCycle.query.filter_by(
        id=cycle_id,
        user_id=current_user.id,
        is_predicted=False
    ).first_or_404()

    db.session.delete(cycle)
    db.session.commit()

    flash('Period cycle deleted successfully!', 'success')
    return redirect(url_for('periods.dashboard'))


@periods_bp.route('/api/current-phase')
@login_required
def api_current_phase():
    """API endpoint: Get current cycle phase information"""
    phase_info = calculate_current_phase(current_user)

    if not phase_info:
        return jsonify({
            'success': False,
            'message': 'No cycle data available'
        })

    return jsonify({
        'success': True,
        'phase': phase_info['phase'],
        'phase_emoji': phase_info['phase_emoji'],
        'phase_color': phase_info['phase_color'],
        'cycle_day': phase_info['cycle_day'],
        'days_until_period': phase_info['days_until_period'],
        'average_cycle': phase_info['average_cycle']
    })
