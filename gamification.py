"""
Gamification Blueprint for HabitFlow
Handles badges, achievements, and leaderboards.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Badge, UserBadge
from badge_service import (
    get_user_badges,
    get_unseen_badges,
    mark_badges_as_seen,
    check_and_award_badges
)
from leaderboard_service import (
    get_global_leaderboard,
    get_completions_leaderboard,
    get_badges_leaderboard,
    get_user_stats_summary,
    get_rank_emoji,
    get_percentile
)

gamification_bp = Blueprint('gamification', __name__)


# ==========================================
# BADGE ROUTES
# ==========================================

@gamification_bp.route('/badges')
@login_required
def badges():
    """
    Display user's earned and locked badges.
    """
    user_badges = get_user_badges(current_user, include_locked=True)
    unseen_badges = get_unseen_badges(current_user)

    # Mark badges as seen after displaying
    if unseen_badges:
        mark_badges_as_seen(current_user)

    # Calculate badge progress
    total_badges = Badge.query.filter_by(is_active=True).count()
    earned_count = len(user_badges['earned'])
    completion_percentage = int((earned_count / total_badges * 100)) if total_badges > 0 else 0

    # Group badges by category
    badges_by_category = {}
    for badge in user_badges['earned']:
        category = badge.badge.category
        if category not in badges_by_category:
            badges_by_category[category] = []
        badges_by_category[category].append(badge)

    locked_by_category = {}
    for badge in user_badges['locked']:
        category = badge.category
        if category not in locked_by_category:
            locked_by_category[category] = []
        locked_by_category[category].append(badge)

    return render_template(
        'gamification/badges.html',
        earned_badges=user_badges['earned'],
        locked_badges=user_badges['locked'],
        badges_by_category=badges_by_category,
        locked_by_category=locked_by_category,
        earned_count=earned_count,
        total_badges=total_badges,
        completion_percentage=completion_percentage,
        unseen_badges=unseen_badges
    )


@gamification_bp.route('/badges/check')
@login_required
def check_badges():
    """
    Manually trigger badge checking for current user.
    Useful for testing or forcing a check.
    """
    newly_awarded = check_and_award_badges(current_user)

    if newly_awarded:
        flash(f'Congratulations! You earned {len(newly_awarded)} new badge(s)!', 'success')
    else:
        flash('No new badges earned. Keep going!', 'info')

    return redirect(url_for('gamification.badges'))


# ==========================================
# LEADERBOARD ROUTES
# ==========================================

@gamification_bp.route('/leaderboard')
@login_required
def leaderboard():
    """
    Display global leaderboard with multiple tabs.
    """
    # Get leaderboard type from query param (default: global)
    lb_type = request.args.get('type', 'global')
    limit = 100

    if lb_type == 'completions':
        leaderboard_data = get_completions_leaderboard(limit=limit, days=30)
    elif lb_type == 'badges':
        leaderboard_data = get_badges_leaderboard(limit=limit)
    else:  # default to global (streaks)
        leaderboard_data = get_global_leaderboard(limit=limit, user=current_user)

    # Get current user stats
    user_stats = get_user_stats_summary(current_user)

    # Add rank emoji and percentile to leaders
    for leader in leaderboard_data['leaders']:
        leader['rank_emoji'] = get_rank_emoji(leader['rank'])
        leader['percentile'] = get_percentile(leader['rank'], leaderboard_data['total_users'])

    return render_template(
        'gamification/leaderboard.html',
        leaderboard=leaderboard_data,
        user_stats=user_stats,
        current_type=lb_type
    )


@gamification_bp.route('/api/leaderboard/<string:lb_type>')
@login_required
def api_leaderboard(lb_type):
    """
    API endpoint to get leaderboard data in JSON format.
    Useful for AJAX updates or mobile apps.
    """
    limit = request.args.get('limit', 100, type=int)

    if lb_type == 'completions':
        days = request.args.get('days', 30, type=int)
        leaderboard_data = get_completions_leaderboard(limit=limit, days=days)
    elif lb_type == 'badges':
        leaderboard_data = get_badges_leaderboard(limit=limit)
    elif lb_type == 'global':
        leaderboard_data = get_global_leaderboard(limit=limit, user=current_user)
    else:
        return jsonify({'error': 'Invalid leaderboard type'}), 400

    # Add rank emoji to each leader
    for leader in leaderboard_data['leaders']:
        leader['rank_emoji'] = get_rank_emoji(leader['rank'])

    return jsonify(leaderboard_data)


@gamification_bp.route('/api/user-stats')
@login_required
def api_user_stats():
    """
    API endpoint to get current user's stats summary.
    """
    user_stats = get_user_stats_summary(current_user)
    return jsonify(user_stats)


# ==========================================
# BADGE NOTIFICATION HELPERS
# ==========================================

def get_badge_notification_count(user):
    """
    Get count of unseen badge notifications for a user.
    Used for displaying badge count in navbar.

    Args:
        user (User): The user

    Returns:
        int: Number of unseen badges
    """
    return UserBadge.query.filter_by(
        user_id=user.id,
        notification_seen=False
    ).count()
