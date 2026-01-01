"""
Leaderboard Service for HabitFlow
Handles global and category-specific leaderboards with rankings.
"""

from models import db, User, Habit, CompletionLog, UserBadge
from sqlalchemy import func, desc, case
from datetime import datetime, timedelta


# ==========================================
# LEADERBOARD QUERIES
# ==========================================

def get_global_leaderboard(limit=100, user=None):
    """
    Get global leaderboard based on longest streaks.

    Args:
        limit (int): Maximum number of users to return
        user (User, optional): Current user for highlighting their position

    Returns:
        dict: {
            'leaders': list of user data with rankings,
            'user_rank': current user's rank (if provided),
            'total_users': total number of users with streaks
        }
    """
    # Subquery to get each user's best streak
    user_best_streaks = db.session.query(
        Habit.user_id,
        func.max(func.greatest(Habit.current_streak, Habit.longest_streak)).label('best_streak'),
        func.count(Habit.id).label('habit_count'),
        func.sum(
            case(
                (Habit.current_streak > 0, 1),
                else_=0
            )
        ).label('active_streaks')
    ).filter(
        Habit.archived == False
    ).group_by(Habit.user_id).subquery()

    # Join with User and get badge counts
    leaderboard_query = db.session.query(
        User.id,
        User.email,
        user_best_streaks.c.best_streak,
        user_best_streaks.c.habit_count,
        user_best_streaks.c.active_streaks,
        func.count(UserBadge.id).label('badge_count')
    ).join(
        user_best_streaks,
        User.id == user_best_streaks.c.user_id
    ).outerjoin(
        UserBadge,
        User.id == UserBadge.user_id
    ).filter(
        User.account_deleted == False,
        user_best_streaks.c.best_streak > 0  # Only users with streaks
    ).group_by(
        User.id,
        User.email,
        user_best_streaks.c.best_streak,
        user_best_streaks.c.habit_count,
        user_best_streaks.c.active_streaks
    ).order_by(
        desc(user_best_streaks.c.best_streak),
        desc(user_best_streaks.c.active_streaks),
        desc(user_best_streaks.c.habit_count)
    )

    # Get total count
    total_users = leaderboard_query.count()

    # Get top N
    top_users = leaderboard_query.limit(limit).all()

    # Format results
    leaders = []
    user_rank = None

    for rank, row in enumerate(top_users, 1):
        user_data = {
            'rank': rank,
            'user_id': row[0],
            'email': row[1],
            'username': row[1].split('@')[0],  # Use email prefix as username
            'best_streak': row[2],
            'habit_count': row[3],
            'active_streaks': row[4],
            'badge_count': row[5],
            'is_current_user': user and row[0] == user.id
        }
        leaders.append(user_data)

        if user and row[0] == user.id:
            user_rank = rank

    # If user not in top N, find their rank
    if user and not user_rank:
        user_rank = get_user_rank(user)

    return {
        'leaders': leaders,
        'user_rank': user_rank,
        'total_users': total_users,
        'leaderboard_type': 'global'
    }


def get_completions_leaderboard(limit=100, days=30):
    """
    Get leaderboard based on total completions in the last X days.

    Args:
        limit (int): Maximum number of users to return
        days (int): Number of days to look back

    Returns:
        dict: Leaderboard data with completion counts
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Query completions in time range
    leaderboard_query = db.session.query(
        User.id,
        User.email,
        func.count(CompletionLog.id).label('completion_count'),
        func.count(func.distinct(CompletionLog.habit_id)).label('unique_habits'),
        func.count(UserBadge.id).label('badge_count')
    ).join(
        Habit,
        User.id == Habit.user_id
    ).join(
        CompletionLog,
        Habit.id == CompletionLog.habit_id
    ).outerjoin(
        UserBadge,
        User.id == UserBadge.user_id
    ).filter(
        User.account_deleted == False,
        CompletionLog.completed_at >= cutoff_date
    ).group_by(
        User.id,
        User.email
    ).order_by(
        desc('completion_count')
    )

    total_users = leaderboard_query.count()
    top_users = leaderboard_query.limit(limit).all()

    leaders = []
    for rank, row in enumerate(top_users, 1):
        user_data = {
            'rank': rank,
            'user_id': row[0],
            'email': row[1],
            'username': row[1].split('@')[0],
            'completion_count': row[2],
            'unique_habits': row[3],
            'badge_count': row[4]
        }
        leaders.append(user_data)

    return {
        'leaders': leaders,
        'total_users': total_users,
        'leaderboard_type': 'completions',
        'time_range': f'{days} days'
    }


def get_badges_leaderboard(limit=100):
    """
    Get leaderboard based on number of badges earned.

    Args:
        limit (int): Maximum number of users to return

    Returns:
        dict: Leaderboard data with badge counts
    """
    leaderboard_query = db.session.query(
        User.id,
        User.email,
        func.count(UserBadge.id).label('badge_count'),
        func.max(func.greatest(Habit.current_streak, Habit.longest_streak)).label('best_streak')
    ).outerjoin(
        UserBadge,
        User.id == UserBadge.user_id
    ).outerjoin(
        Habit,
        User.id == Habit.user_id
    ).filter(
        User.account_deleted == False
    ).group_by(
        User.id,
        User.email
    ).having(
        func.count(UserBadge.id) > 0
    ).order_by(
        desc('badge_count'),
        desc('best_streak')
    )

    total_users = leaderboard_query.count()
    top_users = leaderboard_query.limit(limit).all()

    leaders = []
    for rank, row in enumerate(top_users, 1):
        user_data = {
            'rank': rank,
            'user_id': row[0],
            'email': row[1],
            'username': row[1].split('@')[0],
            'badge_count': row[2],
            'best_streak': row[3] or 0
        }
        leaders.append(user_data)

    return {
        'leaders': leaders,
        'total_users': total_users,
        'leaderboard_type': 'badges'
    }


def get_user_rank(user):
    """
    Get a specific user's rank in the global leaderboard.

    Args:
        user (User): The user to find rank for

    Returns:
        int: User's rank (1-indexed), or None if not ranked
    """
    # Get user's best streak
    user_best_streak = db.session.query(
        func.max(func.greatest(Habit.current_streak, Habit.longest_streak))
    ).filter(
        Habit.user_id == user.id,
        Habit.archived == False
    ).scalar()

    if not user_best_streak or user_best_streak == 0:
        return None

    # Count how many users have a better streak
    better_users = db.session.query(
        Habit.user_id
    ).filter(
        Habit.archived == False
    ).group_by(
        Habit.user_id
    ).having(
        func.max(func.greatest(Habit.current_streak, Habit.longest_streak)) > user_best_streak
    ).count()

    return better_users + 1


def get_user_stats_summary(user):
    """
    Get comprehensive stats summary for a user.

    Args:
        user (User): The user

    Returns:
        dict: Stats summary including rank, streaks, completions, badges
    """
    # Best streak
    best_streak = db.session.query(
        func.max(func.greatest(Habit.current_streak, Habit.longest_streak))
    ).filter(
        Habit.user_id == user.id,
        Habit.archived == False
    ).scalar() or 0

    # Active streaks count
    active_streaks = db.session.query(
        func.count(Habit.id)
    ).filter(
        Habit.user_id == user.id,
        Habit.archived == False,
        Habit.current_streak > 0
    ).scalar() or 0

    # Total completions
    total_completions = CompletionLog.query.join(Habit).filter(
        Habit.user_id == user.id
    ).count()

    # Completions this month
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_completions = CompletionLog.query.join(Habit).filter(
        Habit.user_id == user.id,
        CompletionLog.completed_at >= first_of_month
    ).count()

    # Badge count
    badge_count = UserBadge.query.filter_by(user_id=user.id).count()

    # Global rank
    global_rank = get_user_rank(user)

    # Habit count
    habit_count = Habit.query.filter_by(
        user_id=user.id,
        archived=False
    ).count()

    return {
        'best_streak': best_streak,
        'active_streaks': active_streaks,
        'total_completions': total_completions,
        'monthly_completions': monthly_completions,
        'badge_count': badge_count,
        'global_rank': global_rank,
        'habit_count': habit_count
    }


# ==========================================
# LEADERBOARD UTILITIES
# ==========================================

def get_rank_emoji(rank):
    """
    Get emoji for a given rank.

    Args:
        rank (int): The rank

    Returns:
        str: Emoji for the rank
    """
    if rank == 1:
        return '🥇'
    elif rank == 2:
        return '🥈'
    elif rank == 3:
        return '🥉'
    elif rank <= 10:
        return '🏅'
    else:
        return '⭐'


def get_percentile(rank, total):
    """
    Calculate percentile for a rank.

    Args:
        rank (int): User's rank
        total (int): Total number of users

    Returns:
        int: Percentile (0-100)
    """
    if total == 0:
        return 0
    return int(((total - rank + 1) / total) * 100)
