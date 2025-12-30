"""
Challenges Blueprint for HabitFlow
Handles community challenges where users compete or collaborate on habit goals.
Premium users can create challenges, free users can join via invites.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import (
    db, Challenge, ChallengeParticipant, ChallengeInvite, HabitChallengeLink,
    ChallengeActivity, Habit, User, log_security_event
)
from forms import ChallengeForm, InviteForm, LinkHabitForm
from datetime import datetime, timedelta
from functools import wraps

# Create challenges blueprint
challenges_bp = Blueprint('challenges', __name__)


# ============================================================================
# DECORATORS
# ============================================================================

def require_premium(f):
    """
    Decorator to require premium subscription.
    Redirects free users to pricing page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_premium_active():
            flash('This feature requires a premium subscription. Upgrade to unlock unlimited habits and challenge creation!', 'warning')
            return redirect(url_for('profile.subscription'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# CHALLENGE BROWSING & LISTING
# ============================================================================

@challenges_bp.route('/my-challenges')
@login_required
def my_challenges():
    """
    Dashboard showing user's challenges - both created and joined.
    Separates into two tabs: challenges created by user vs challenges joined.
    """
    # Get challenges created by user (only active, not soft-deleted)
    created_challenges = Challenge.query.filter_by(
        creator_id=current_user.id,
        deleted_at=None
    ).order_by(Challenge.created_at.desc()).all()

    # Get challenges user has joined (via ChallengeParticipant)
    joined_participations = ChallengeParticipant.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()

    # Extract challenges from participations (exclude ones user created)
    joined_challenges = [
        p.challenge for p in joined_participations
        if p.challenge.creator_id != current_user.id and p.challenge.deleted_at is None
    ]

    # Get participant records for both types
    created_participants = {}
    joined_participants = {}

    for challenge in created_challenges:
        created_participants[challenge.id] = ChallengeParticipant.query.filter_by(
            challenge_id=challenge.id,
            user_id=current_user.id
        ).first()

    for challenge in joined_challenges:
        joined_participants[challenge.id] = ChallengeParticipant.query.filter_by(
            challenge_id=challenge.id,
            user_id=current_user.id
        ).first()

    return render_template(
        'challenges/my_challenges.html',
        created_challenges=created_challenges,
        joined_challenges=joined_challenges,
        created_participants=created_participants,
        joined_participants=joined_participants
    )


@challenges_bp.route('/<int:challenge_id>')
@login_required
def detail(challenge_id):
    """
    Challenge detail page with leaderboard/stats and activity feed.
    Shows competitive leaderboard or collaborative group progress based on challenge type.
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Check if challenge is soft-deleted
    if challenge.deleted_at:
        flash('This challenge has been deleted.', 'error')
        return redirect(url_for('challenges.my_challenges'))

    # Check if user is a participant
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status='active'
    ).first()

    if not participation and challenge.creator_id != current_user.id:
        flash('You are not a participant in this challenge.', 'error')
        return redirect(url_for('challenges.my_challenges'))

    # Get all active participants with their stats
    participants = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        status='active'
    ).order_by(ChallengeParticipant.current_streak.desc()).all()

    # Get user's linked habits for this challenge
    user_linked_habits = []
    if participation:
        habit_links = HabitChallengeLink.query.filter_by(
            challenge_id=challenge_id,
            participant_id=participation.id,
            is_active=True
        ).all()
        user_linked_habits = [link.habit for link in habit_links]

    # Get recent activity feed
    recent_activities = ChallengeActivity.query.filter_by(
        challenge_id=challenge_id
    ).order_by(ChallengeActivity.created_at.desc()).limit(20).all()

    # Calculate collaborative stats if needed
    collaborative_stats = None
    if challenge.challenge_type == 'collaborative':
        total_streak = sum(p.current_streak for p in participants)
        total_completions = sum(p.total_completions for p in participants)
        avg_streak = total_streak / len(participants) if participants else 0

        # Calculate participation rate (active today)
        today = current_user.get_user_date()
        active_today = sum(1 for p in participants if p.last_activity == today)
        participation_rate = (active_today / len(participants) * 100) if participants else 0

        collaborative_stats = {
            'total_streak': total_streak,
            'average_streak': round(avg_streak, 1),
            'total_completions': total_completions,
            'participation_rate': round(participation_rate, 1),
            'active_today': active_today,
            'total_participants': len(participants)
        }

    return render_template(
        'challenges/detail.html',
        challenge=challenge,
        participation=participation,
        participants=participants,
        user_linked_habits=user_linked_habits,
        recent_activities=recent_activities,
        collaborative_stats=collaborative_stats
    )


# ============================================================================
# CHALLENGE MANAGEMENT (PREMIUM ONLY)
# ============================================================================

@challenges_bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_premium
def create():
    """
    Create a new challenge (premium users only).
    Creates challenge, adds creator as first participant, logs activity.
    """
    form = ChallengeForm()

    if form.validate_on_submit():
        # Create the challenge
        challenge = Challenge(
            creator_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            icon=form.icon.data,
            challenge_type=form.challenge_type.data,
            goal_type=form.goal_type.data,
            goal_target=form.goal_target.data if form.goal_target.data else None,
            max_participants=form.max_participants.data if form.max_participants.data else None,
            status='active',
            visibility='invite_only'
        )

        db.session.add(challenge)
        db.session.flush()  # Flush to get challenge.id

        # Add creator as first participant with 'creator' role
        creator_participant = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=current_user.id,
            role='creator',
            status='active'
        )
        db.session.add(creator_participant)

        # Log activity
        activity = ChallengeActivity(
            challenge_id=challenge.id,
            user_id=current_user.id,
            activity_type='challenge_created',
            description=f'{current_user.email} created the challenge "{challenge.name}"'
        )
        db.session.add(activity)

        db.session.commit()

        # Log security event
        log_security_event(
            user_id=current_user.id,
            event_type='challenge_created',
            description=f'Created challenge: {challenge.name}'
        )

        flash(f'Challenge "{challenge.name}" created successfully! Invite friends to join.', 'success')
        return redirect(url_for('challenges.detail', challenge_id=challenge.id))

    return render_template('challenges/create.html', form=form)


@challenges_bp.route('/<int:challenge_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(challenge_id):
    """
    Edit an existing challenge (creator only).
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Check ownership
    if challenge.creator_id != current_user.id:
        flash('Only the challenge creator can edit this challenge.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Check if soft-deleted
    if challenge.deleted_at:
        flash('Cannot edit a deleted challenge.', 'error')
        return redirect(url_for('challenges.my_challenges'))

    form = ChallengeForm(obj=challenge)

    if form.validate_on_submit():
        challenge.name = form.name.data
        challenge.description = form.description.data
        challenge.icon = form.icon.data
        challenge.challenge_type = form.challenge_type.data
        challenge.goal_type = form.goal_type.data
        challenge.goal_target = form.goal_target.data if form.goal_target.data else None
        challenge.max_participants = form.max_participants.data if form.max_participants.data else None
        challenge.updated_at = datetime.utcnow()

        # Log activity
        activity = ChallengeActivity(
            challenge_id=challenge.id,
            user_id=current_user.id,
            activity_type='challenge_updated',
            description=f'{current_user.email} updated the challenge settings'
        )
        db.session.add(activity)

        db.session.commit()

        flash('Challenge updated successfully!', 'success')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    return render_template('challenges/edit.html', form=form, challenge=challenge)


@challenges_bp.route('/<int:challenge_id>/delete', methods=['POST'])
@login_required
def delete(challenge_id):
    """
    Soft delete a challenge (creator only).
    Sets deleted_at timestamp instead of actually deleting.
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Check ownership
    if challenge.creator_id != current_user.id:
        flash('Only the challenge creator can delete this challenge.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Soft delete
    challenge.deleted_at = datetime.utcnow()
    challenge.status = 'archived'

    # Log activity
    activity = ChallengeActivity(
        challenge_id=challenge.id,
        user_id=current_user.id,
        activity_type='challenge_deleted',
        description=f'{current_user.email} deleted the challenge'
    )
    db.session.add(activity)

    db.session.commit()

    log_security_event(
        user_id=current_user.id,
        event_type='challenge_deleted',
        description=f'Deleted challenge: {challenge.name}'
    )

    flash('Challenge deleted successfully.', 'success')
    return redirect(url_for('challenges.my_challenges'))


# ============================================================================
# INVITATIONS
# ============================================================================

@challenges_bp.route('/<int:challenge_id>/invite', methods=['GET', 'POST'])
@login_required
def invite(challenge_id):
    """
    Send email invite to join challenge.
    Available to all participants if allow_invites is True.
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Check if challenge allows invites
    if not challenge.allow_invites:
        flash('Invitations are currently disabled for this challenge.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Check if user is a participant
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status='active'
    ).first()

    if not participation:
        flash('You must be a participant to send invites.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    form = InviteForm()

    if form.validate_on_submit():
        # Check if invite already exists for this email
        existing_invite = ChallengeInvite.query.filter_by(
            challenge_id=challenge_id,
            invitee_email=form.email.data,
            status='pending'
        ).first()

        if existing_invite and not existing_invite.is_expired():
            flash('An invite has already been sent to this email.', 'warning')
            return redirect(url_for('challenges.detail', challenge_id=challenge_id))

        # Create invite with 30-day expiration
        invite = ChallengeInvite(
            challenge_id=challenge_id,
            inviter_id=current_user.id,
            invitee_email=form.email.data,
            personal_message=form.message.data,
            token=ChallengeInvite.generate_token(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        db.session.add(invite)
        db.session.commit()

        # TODO: Send email via email service
        # send_challenge_invite_email(invite)

        # Log activity
        activity = ChallengeActivity(
            challenge_id=challenge.id,
            user_id=current_user.id,
            activity_type='invite_sent',
            description=f'{current_user.email} invited {form.email.data}'
        )
        db.session.add(activity)
        db.session.commit()

        flash(f'Invitation sent to {form.email.data}!', 'success')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    return render_template('challenges/invite.html', form=form, challenge=challenge)


@challenges_bp.route('/<int:challenge_id>/shareable-link')
@login_required
def shareable_link(challenge_id):
    """
    Generate a shareable invite link (90-day expiration).
    Available to all participants if allow_invites is True.
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Check if challenge allows invites
    if not challenge.allow_invites:
        flash('Invitations are currently disabled for this challenge.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Check if user is a participant
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status='active'
    ).first()

    if not participation:
        flash('You must be a participant to create shareable links.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Check if unexpired shareable link already exists
    existing_link = ChallengeInvite.query.filter_by(
        challenge_id=challenge_id,
        invitee_email=None,  # Shareable links have no specific email
        status='pending'
    ).filter(
        ChallengeInvite.expires_at > datetime.utcnow()
    ).first()

    if existing_link:
        invite_url = url_for('challenges.accept_invite', token=existing_link.token, _external=True)
        return render_template('challenges/shareable_link.html', challenge=challenge, invite_url=invite_url, invite=existing_link)

    # Create new shareable link with 90-day expiration
    invite = ChallengeInvite(
        challenge_id=challenge_id,
        inviter_id=current_user.id,
        invitee_email=None,  # No specific email for shareable links
        token=ChallengeInvite.generate_token(),
        expires_at=datetime.utcnow() + timedelta(days=90)
    )

    db.session.add(invite)
    db.session.commit()

    invite_url = url_for('challenges.accept_invite', token=invite.token, _external=True)

    flash('Shareable link created! Copy and share with friends.', 'success')
    return render_template('challenges/shareable_link.html', challenge=challenge, invite_url=invite_url, invite=invite)


@challenges_bp.route('/invite/<token>')
def accept_invite(token):
    """
    Accept invite and join challenge (public route, requires login).
    Redirects to login if not authenticated, then returns here.
    """
    invite = ChallengeInvite.query.filter_by(token=token).first_or_404()

    # Check if invite expired
    if invite.is_expired():
        invite.status = 'expired'
        db.session.commit()
        flash('This invite link has expired.', 'error')
        return redirect(url_for('habits.dashboard'))

    # Check if already accepted
    if invite.status == 'accepted':
        flash('This invite has already been used.', 'info')
        return redirect(url_for('challenges.detail', challenge_id=invite.challenge_id))

    challenge = invite.challenge

    # Check if challenge is deleted
    if challenge.deleted_at:
        flash('This challenge has been deleted.', 'error')
        return redirect(url_for('habits.dashboard'))

    # Require login
    if not current_user.is_authenticated:
        flash('Please log in or create an account to join this challenge.', 'info')
        return redirect(url_for('auth.login', next=request.url))

    # Check if user is already a participant
    existing_participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge.id,
        user_id=current_user.id
    ).first()

    if existing_participation and existing_participation.status == 'active':
        flash('You are already a member of this challenge!', 'info')
        return redirect(url_for('challenges.detail', challenge_id=challenge.id))

    # Check max participants limit
    if challenge.max_participants:
        current_participant_count = ChallengeParticipant.query.filter_by(
            challenge_id=challenge.id,
            status='active'
        ).count()

        if current_participant_count >= challenge.max_participants:
            flash('This challenge has reached its maximum number of participants.', 'error')
            return redirect(url_for('habits.dashboard'))

    # Reactivate if user previously left
    if existing_participation and existing_participation.status == 'left':
        existing_participation.status = 'active'
        existing_participation.left_at = None
        participant = existing_participation
    else:
        # Create new participation
        participant = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=current_user.id,
            role='member',
            status='active'
        )
        db.session.add(participant)

    # Mark invite as accepted
    invite.status = 'accepted'
    invite.accepted_at = datetime.utcnow()
    invite.accepted_by_user_id = current_user.id

    # Log activity
    activity = ChallengeActivity(
        challenge_id=challenge.id,
        user_id=current_user.id,
        activity_type='user_joined',
        description=f'{current_user.email} joined the challenge'
    )
    db.session.add(activity)

    db.session.commit()

    # TODO: Send email to creator
    # send_challenge_joined_email(challenge, current_user)

    flash(f'Welcome to "{challenge.name}"! Link your habits to start tracking progress.', 'success')
    return redirect(url_for('challenges.link_habit', challenge_id=challenge.id))


# ============================================================================
# HABIT LINKING
# ============================================================================

@challenges_bp.route('/<int:challenge_id>/link-habit', methods=['GET', 'POST'])
@login_required
def link_habit(challenge_id):
    """
    Link existing habit or create new habit for this challenge.
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Get user's participation
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status='active'
    ).first()

    if not participation:
        flash('You must join the challenge first.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    form = LinkHabitForm()

    # Populate habit choices with user's habits (excluding already linked ones)
    already_linked_habit_ids = [
        link.habit_id for link in HabitChallengeLink.query.filter_by(
            challenge_id=challenge_id,
            participant_id=participation.id,
            is_active=True
        ).all()
    ]

    available_habits = Habit.query.filter_by(
        user_id=current_user.id,
        archived=False
    ).filter(
        ~Habit.id.in_(already_linked_habit_ids)
    ).all()

    form.habit_id.choices = [(0, '-- Create New Habit --')] + [(h.id, h.name) for h in available_habits]

    if form.validate_on_submit():
        # Check if creating new habit or linking existing
        if form.habit_id.data == 0:
            # Create new habit
            if not form.new_habit_name.data:
                flash('Please provide a name for the new habit.', 'error')
                return render_template('challenges/link_habit.html', form=form, challenge=challenge)

            # Check habit limit for free users
            if not current_user.can_add_more_habits():
                flash('You have reached your habit limit. Upgrade to premium for unlimited habits!', 'warning')
                return redirect(url_for('profile.subscription'))

            new_habit = Habit(
                user_id=current_user.id,
                name=form.new_habit_name.data,
                description=f'Tracking for challenge: {challenge.name}'
            )
            db.session.add(new_habit)
            db.session.flush()
            habit_to_link = new_habit
        else:
            # Link existing habit
            habit_to_link = Habit.query.get(form.habit_id.data)

            # Verify ownership
            if habit_to_link.user_id != current_user.id:
                flash('Invalid habit selected.', 'error')
                return redirect(url_for('challenges.link_habit', challenge_id=challenge_id))

        # Create the link
        link = HabitChallengeLink(
            habit_id=habit_to_link.id,
            challenge_id=challenge_id,
            participant_id=participation.id,
            is_active=True
        )
        db.session.add(link)

        # Update participant progress
        participation.update_progress()

        # Log activity
        activity = ChallengeActivity(
            challenge_id=challenge.id,
            user_id=current_user.id,
            activity_type='habit_linked',
            description=f'{current_user.email} linked habit "{habit_to_link.name}"'
        )
        db.session.add(activity)

        db.session.commit()

        flash(f'Habit "{habit_to_link.name}" linked to challenge!', 'success')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    return render_template('challenges/link_habit.html', form=form, challenge=challenge)


@challenges_bp.route('/<int:challenge_id>/unlink-habit/<int:habit_id>', methods=['POST'])
@login_required
def unlink_habit(challenge_id, habit_id):
    """
    Unlink a habit from the challenge.
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Get user's participation
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status='active'
    ).first()

    if not participation:
        flash('You are not a participant in this challenge.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Find the link
    link = HabitChallengeLink.query.filter_by(
        habit_id=habit_id,
        challenge_id=challenge_id,
        participant_id=participation.id,
        is_active=True
    ).first()

    if not link:
        flash('Habit is not linked to this challenge.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Unlink (soft delete)
    link.is_active = False
    link.unlinked_at = datetime.utcnow()

    # Update participant progress
    participation.update_progress()

    db.session.commit()

    flash('Habit unlinked from challenge.', 'success')
    return redirect(url_for('challenges.detail', challenge_id=challenge_id))


# ============================================================================
# PARTICIPATION
# ============================================================================

@challenges_bp.route('/<int:challenge_id>/leave', methods=['POST'])
@login_required
def leave(challenge_id):
    """
    Leave a challenge (cannot leave if you're the creator).
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Get user's participation
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status='active'
    ).first()

    if not participation:
        flash('You are not a participant in this challenge.', 'error')
        return redirect(url_for('challenges.my_challenges'))

    # Cannot leave if creator
    if participation.role == 'creator':
        flash('Challenge creators cannot leave their own challenges. Delete the challenge instead.', 'error')
        return redirect(url_for('challenges.detail', challenge_id=challenge_id))

    # Mark as left
    participation.status = 'left'
    participation.left_at = datetime.utcnow()

    # Unlink all habits
    for link in participation.habit_links.filter_by(is_active=True).all():
        link.is_active = False
        link.unlinked_at = datetime.utcnow()

    # Log activity
    activity = ChallengeActivity(
        challenge_id=challenge.id,
        user_id=current_user.id,
        activity_type='user_left',
        description=f'{current_user.email} left the challenge'
    )
    db.session.add(activity)

    db.session.commit()

    flash('You have left the challenge.', 'success')
    return redirect(url_for('challenges.my_challenges'))


# ============================================================================
# PROGRESS UPDATES
# ============================================================================

@challenges_bp.route('/update-progress', methods=['POST'])
@login_required
def update_progress():
    """
    Update challenge progress after habit completion.
    Called as webhook/background job when habits are completed.
    """
    data = request.get_json()
    habit_id = data.get('habit_id')

    if not habit_id:
        return jsonify({'error': 'Missing habit_id'}), 400

    # Find all challenge links for this habit
    links = HabitChallengeLink.query.filter_by(
        habit_id=habit_id,
        is_active=True
    ).all()

    for link in links:
        # Update participant progress
        link.participant.update_progress()

    db.session.commit()

    return jsonify({'success': True, 'updated_challenges': len(links)})


# ============================================================================
# API ENDPOINTS
# ============================================================================

@challenges_bp.route('/<int:challenge_id>/leaderboard-data')
@login_required
def leaderboard_data(challenge_id):
    """
    JSON API endpoint for real-time leaderboard updates.
    Returns participant rankings and stats.
    """
    challenge = Challenge.query.get_or_404(challenge_id)

    # Check if user is a participant
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id,
        status='active'
    ).first()

    if not participation and challenge.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Get all active participants sorted by current_streak
    participants = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        status='active'
    ).order_by(ChallengeParticipant.current_streak.desc()).all()

    # Build leaderboard data
    leaderboard = []
    for idx, p in enumerate(participants, start=1):
        leaderboard.append({
            'rank': idx,
            'user_id': p.user_id,
            'user_email': p.user.email,
            'current_streak': p.current_streak,
            'longest_streak': p.longest_streak,
            'total_completions': p.total_completions,
            'last_activity': p.last_activity.isoformat() if p.last_activity else None
        })

    return jsonify({
        'challenge_id': challenge_id,
        'challenge_type': challenge.challenge_type,
        'leaderboard': leaderboard
    })
