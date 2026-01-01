"""
Badge Service for HabitFlow
Handles badge definitions, checking, and awarding logic.
Gamification system to improve user engagement and retention.
"""

from models import db, User, Badge, UserBadge, Habit, CompletionLog
from datetime import datetime, timedelta
from sqlalchemy import func


# ==========================================
# BADGE DEFINITIONS
# ==========================================

BADGE_DEFINITIONS = [
    # ========== STREAK BADGES ==========
    {
        'name': 'First Steps',
        'slug': 'first-steps',
        'description': 'Complete your first habit',
        'icon': '👣',
        'color': 'blue',
        'category': 'streak',
        'requirement_type': 'any_completion',
        'requirement_value': 1,
        'rarity': 'common',
        'display_order': 1
    },
    {
        'name': 'Week Warrior',
        'slug': 'week-warrior',
        'description': 'Maintain a 7-day streak on any habit',
        'icon': '🔥',
        'color': 'orange',
        'category': 'streak',
        'requirement_type': 'streak_days',
        'requirement_value': 7,
        'rarity': 'common',
        'display_order': 2
    },
    {
        'name': 'Two Week Triumph',
        'slug': 'two-week-triumph',
        'description': 'Maintain a 14-day streak on any habit',
        'icon': '💪',
        'color': 'red',
        'category': 'streak',
        'requirement_type': 'streak_days',
        'requirement_value': 14,
        'rarity': 'common',
        'display_order': 3
    },
    {
        'name': 'Month Master',
        'slug': 'month-master',
        'description': 'Maintain a 30-day streak on any habit',
        'icon': '🏆',
        'color': 'gold',
        'category': 'streak',
        'requirement_type': 'streak_days',
        'requirement_value': 30,
        'rarity': 'rare',
        'display_order': 4
    },
    {
        'name': 'Century Club',
        'slug': 'century-club',
        'description': 'Achieve a 100-day streak on any habit',
        'icon': '💯',
        'color': 'purple',
        'category': 'streak',
        'requirement_type': 'streak_days',
        'requirement_value': 100,
        'rarity': 'epic',
        'display_order': 5
    },
    {
        'name': 'Habit Hero',
        'slug': 'habit-hero',
        'description': 'Maintain a 365-day streak - one full year!',
        'icon': '🌟',
        'color': 'rainbow',
        'category': 'streak',
        'requirement_type': 'streak_days',
        'requirement_value': 365,
        'rarity': 'legendary',
        'display_order': 6
    },

    # ========== COMPLETION BADGES ==========
    {
        'name': 'Getting Started',
        'slug': 'getting-started',
        'description': 'Complete 10 total habit check-ins',
        'icon': '✅',
        'color': 'green',
        'category': 'completion',
        'requirement_type': 'total_completions',
        'requirement_value': 10,
        'rarity': 'common',
        'display_order': 10
    },
    {
        'name': 'Momentum Builder',
        'slug': 'momentum-builder',
        'description': 'Complete 50 total habit check-ins',
        'icon': '⚡',
        'color': 'yellow',
        'category': 'completion',
        'requirement_type': 'total_completions',
        'requirement_value': 50,
        'rarity': 'common',
        'display_order': 11
    },
    {
        'name': 'Commitment Champion',
        'slug': 'commitment-champion',
        'description': 'Complete 100 total habit check-ins',
        'icon': '🎯',
        'color': 'purple',
        'category': 'completion',
        'requirement_type': 'total_completions',
        'requirement_value': 100,
        'rarity': 'rare',
        'display_order': 12
    },
    {
        'name': 'Dedication Master',
        'slug': 'dedication-master',
        'description': 'Complete 500 total habit check-ins',
        'icon': '👑',
        'color': 'gold',
        'category': 'completion',
        'requirement_type': 'total_completions',
        'requirement_value': 500,
        'rarity': 'epic',
        'display_order': 13
    },
    {
        'name': 'Legendary Achiever',
        'slug': 'legendary-achiever',
        'description': 'Complete 1000 total habit check-ins',
        'icon': '🦸',
        'color': 'rainbow',
        'category': 'completion',
        'requirement_type': 'total_completions',
        'requirement_value': 1000,
        'rarity': 'legendary',
        'display_order': 14
    },

    # ========== PERFECT WEEK BADGES ==========
    {
        'name': 'Perfect Week',
        'slug': 'perfect-week',
        'description': 'Complete all habits every day for 7 days',
        'icon': '⭐',
        'color': 'blue',
        'category': 'completion',
        'requirement_type': 'perfect_week',
        'requirement_value': 7,
        'rarity': 'rare',
        'display_order': 20
    },
    {
        'name': 'Flawless Fortnight',
        'slug': 'flawless-fortnight',
        'description': 'Complete all habits every day for 14 days',
        'icon': '🌠',
        'color': 'purple',
        'category': 'completion',
        'requirement_type': 'perfect_week',
        'requirement_value': 14,
        'rarity': 'epic',
        'display_order': 21
    },

    # ========== HABIT COLLECTION BADGES ==========
    {
        'name': 'Habit Starter',
        'slug': 'habit-starter',
        'description': 'Create 3 habits',
        'icon': '🌱',
        'color': 'green',
        'category': 'habit_count',
        'requirement_type': 'habits_created',
        'requirement_value': 3,
        'rarity': 'common',
        'display_order': 30
    },
    {
        'name': 'Routine Builder',
        'slug': 'routine-builder',
        'description': 'Create 5 habits',
        'icon': '🏗️',
        'color': 'blue',
        'category': 'habit_count',
        'requirement_type': 'habits_created',
        'requirement_value': 5,
        'rarity': 'common',
        'display_order': 31
    },
    {
        'name': 'Lifestyle Architect',
        'slug': 'lifestyle-architect',
        'description': 'Create 10 habits',
        'icon': '🏛️',
        'color': 'purple',
        'category': 'habit_count',
        'requirement_type': 'habits_created',
        'requirement_value': 10,
        'rarity': 'rare',
        'display_order': 32
    },

    # ========== EARLY BIRD / NIGHT OWL ==========
    {
        'name': 'Early Bird',
        'slug': 'early-bird',
        'description': 'Complete 10 habits before 6 AM',
        'icon': '🌅',
        'color': 'orange',
        'category': 'special',
        'requirement_type': 'early_completions',
        'requirement_value': 10,
        'rarity': 'rare',
        'display_order': 40
    },
    {
        'name': 'Night Owl',
        'slug': 'night-owl',
        'description': 'Complete 10 habits after 10 PM',
        'icon': '🦉',
        'color': 'purple',
        'category': 'special',
        'requirement_type': 'late_completions',
        'requirement_value': 10,
        'rarity': 'rare',
        'display_order': 41
    },

    # ========== SOCIAL BADGES ==========
    {
        'name': 'Team Player',
        'slug': 'team-player',
        'description': 'Join your first challenge',
        'icon': '🤝',
        'color': 'blue',
        'category': 'challenge',
        'requirement_type': 'challenges_joined',
        'requirement_value': 1,
        'rarity': 'common',
        'display_order': 50
    },
    {
        'name': 'Challenge Creator',
        'slug': 'challenge-creator',
        'description': 'Create your first challenge',
        'icon': '🎪',
        'color': 'purple',
        'category': 'challenge',
        'requirement_type': 'challenges_created',
        'requirement_value': 1,
        'rarity': 'common',
        'display_order': 51
    },
    {
        'name': 'Community Leader',
        'slug': 'community-leader',
        'description': 'Create 3 challenges',
        'icon': '🎖️',
        'color': 'gold',
        'category': 'challenge',
        'requirement_type': 'challenges_created',
        'requirement_value': 3,
        'rarity': 'rare',
        'display_order': 52
    },
]


# ==========================================
# BADGE INITIALIZATION
# ==========================================

def initialize_badges():
    """
    Initialize badge definitions in database.
    Safe to run multiple times - will not create duplicates.
    """
    print("[BADGES] Initializing badge definitions...")
    created_count = 0
    updated_count = 0

    for badge_data in BADGE_DEFINITIONS:
        existing_badge = Badge.query.filter_by(slug=badge_data['slug']).first()

        if existing_badge:
            # Update existing badge
            existing_badge.name = badge_data['name']
            existing_badge.description = badge_data['description']
            existing_badge.icon = badge_data['icon']
            existing_badge.color = badge_data['color']
            existing_badge.category = badge_data['category']
            existing_badge.requirement_type = badge_data['requirement_type']
            existing_badge.requirement_value = badge_data['requirement_value']
            existing_badge.rarity = badge_data['rarity']
            existing_badge.display_order = badge_data['display_order']
            updated_count += 1
        else:
            # Create new badge
            new_badge = Badge(
                name=badge_data['name'],
                slug=badge_data['slug'],
                description=badge_data['description'],
                icon=badge_data['icon'],
                color=badge_data['color'],
                category=badge_data['category'],
                requirement_type=badge_data['requirement_type'],
                requirement_value=badge_data['requirement_value'],
                rarity=badge_data['rarity'],
                display_order=badge_data['display_order']
            )
            db.session.add(new_badge)
            created_count += 1

    db.session.commit()
    print(f"[BADGES] OK Initialized {created_count} new badges, updated {updated_count} existing badges")
    return created_count + updated_count


# ==========================================
# BADGE CHECKING LOGIC
# ==========================================

def check_and_award_badges(user):
    """
    Check all badge requirements for a user and award new badges.
    Call this after significant actions (habit completion, habit creation, etc.)

    Args:
        user (User): The user to check badges for

    Returns:
        list: List of newly awarded UserBadge objects
    """
    newly_awarded = []

    # Get all badges the user hasn't earned yet
    earned_badge_ids = [ub.badge_id for ub in user.earned_badges.all()]
    available_badges = Badge.query.filter(
        Badge.is_active == True,
        ~Badge.id.in_(earned_badge_ids) if earned_badge_ids else True
    ).all()

    for badge in available_badges:
        if check_badge_requirement(user, badge):
            # Award the badge!
            user_badge = UserBadge(
                user_id=user.id,
                badge_id=badge.id,
                earned_at=datetime.utcnow(),
                notification_seen=False
            )
            db.session.add(user_badge)
            newly_awarded.append(user_badge)
            print(f"[BADGES] 🎉 Awarded '{badge.name}' to user {user.id}")

    if newly_awarded:
        db.session.commit()

    return newly_awarded


def check_badge_requirement(user, badge):
    """
    Check if a user meets the requirement for a specific badge.

    Args:
        user (User): The user to check
        badge (Badge): The badge to check requirements for

    Returns:
        bool: True if user meets the requirement, False otherwise
    """
    requirement_type = badge.requirement_type
    requirement_value = badge.requirement_value

    # ========== ANY COMPLETION ==========
    if requirement_type == 'any_completion':
        completion_count = CompletionLog.query.join(Habit).filter(
            Habit.user_id == user.id
        ).count()
        return completion_count >= requirement_value

    # ========== STREAK DAYS ==========
    elif requirement_type == 'streak_days':
        # Check if any habit has a streak >= requirement
        max_current_streak = db.session.query(func.max(Habit.current_streak)).filter(
            Habit.user_id == user.id,
            Habit.archived == False
        ).scalar() or 0

        max_longest_streak = db.session.query(func.max(Habit.longest_streak)).filter(
            Habit.user_id == user.id
        ).scalar() or 0

        return max(max_current_streak, max_longest_streak) >= requirement_value

    # ========== TOTAL COMPLETIONS ==========
    elif requirement_type == 'total_completions':
        total_completions = CompletionLog.query.join(Habit).filter(
            Habit.user_id == user.id
        ).count()
        return total_completions >= requirement_value

    # ========== PERFECT WEEK ==========
    elif requirement_type == 'perfect_week':
        # Check if user has completed ALL habits every day for X days
        days_to_check = requirement_value
        user_date = user.get_user_date()

        # Get all active habits
        active_habits = Habit.query.filter_by(
            user_id=user.id,
            archived=False
        ).all()

        if not active_habits:
            return False

        # Check each day going backwards
        for day_offset in range(days_to_check):
            check_date = user_date - timedelta(days=day_offset)

            # Count completions on this date
            completions_on_date = CompletionLog.query.filter(
                CompletionLog.habit_id.in_([h.id for h in active_habits]),
                CompletionLog.completed_date == check_date
            ).count()

            # If any day didn't have ALL habits completed, fail
            if completions_on_date < len(active_habits):
                return False

        return True

    # ========== HABITS CREATED ==========
    elif requirement_type == 'habits_created':
        total_habits = Habit.query.filter_by(user_id=user.id).count()
        return total_habits >= requirement_value

    # ========== EARLY COMPLETIONS ==========
    elif requirement_type == 'early_completions':
        # Count completions before 6 AM
        early_completions = CompletionLog.query.join(Habit).filter(
            Habit.user_id == user.id,
            func.extract('hour', CompletionLog.completed_at) < 6
        ).count()
        return early_completions >= requirement_value

    # ========== LATE COMPLETIONS ==========
    elif requirement_type == 'late_completions':
        # Count completions after 10 PM
        late_completions = CompletionLog.query.join(Habit).filter(
            Habit.user_id == user.id,
            func.extract('hour', CompletionLog.completed_at) >= 22
        ).count()
        return late_completions >= requirement_value

    # ========== CHALLENGES JOINED ==========
    elif requirement_type == 'challenges_joined':
        from models import ChallengeParticipant
        challenges_joined = ChallengeParticipant.query.filter_by(
            user_id=user.id,
            status='active'
        ).count()
        return challenges_joined >= requirement_value

    # ========== CHALLENGES CREATED ==========
    elif requirement_type == 'challenges_created':
        from models import Challenge
        challenges_created = Challenge.query.filter_by(
            creator_id=user.id
        ).filter(Challenge.deleted_at.is_(None)).count()
        return challenges_created >= requirement_value

    # Unknown requirement type
    return False


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_user_badges(user, include_locked=False):
    """
    Get all badges for a user, optionally including locked badges.

    Args:
        user (User): The user to get badges for
        include_locked (bool): If True, include badges the user hasn't earned

    Returns:
        dict: {'earned': [UserBadge], 'locked': [Badge]} if include_locked=True
              {'earned': [UserBadge]} if include_locked=False
    """
    earned_badges = user.earned_badges.join(Badge).order_by(Badge.display_order).all()

    if include_locked:
        earned_badge_ids = [ub.badge_id for ub in earned_badges]
        locked_badges = Badge.query.filter(
            Badge.is_active == True,
            ~Badge.id.in_(earned_badge_ids) if earned_badge_ids else True
        ).order_by(Badge.display_order).all()

        return {
            'earned': earned_badges,
            'locked': locked_badges
        }

    return {'earned': earned_badges}


def get_unseen_badges(user):
    """
    Get badges the user has earned but hasn't seen the notification for.

    Args:
        user (User): The user to check

    Returns:
        list: List of UserBadge objects with notification_seen=False
    """
    return UserBadge.query.filter_by(
        user_id=user.id,
        notification_seen=False
    ).join(Badge).order_by(UserBadge.earned_at.desc()).all()


def mark_badges_as_seen(user):
    """
    Mark all unseen badges as seen for a user.

    Args:
        user (User): The user
    """
    UserBadge.query.filter_by(
        user_id=user.id,
        notification_seen=False
    ).update({'notification_seen': True})
    db.session.commit()
