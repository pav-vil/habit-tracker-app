"""
Admin Blueprint for HabitFlow
Provides user management and premium access control for administrators.
"""

from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from models import db, User, SubscriptionHistory, AuditLog, log_security_event

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """
    Decorator that requires the current user to be an admin.
    Must be used after @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            log_security_event(
                user_id=current_user.id,
                event_type='admin_access_denied',
                description=f'User attempted to access admin area: {request.path}',
                success=False
            )
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """
    Admin user management page.
    Lists all users with search and filter capabilities.
    """
    # Get query parameters
    search = request.args.get('search', '').strip()
    tier_filter = request.args.get('tier', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Build query
    query = User.query.filter_by(account_deleted=False)

    # Apply search filter
    if search:
        query = query.filter(User.email.ilike(f'%{search}%'))

    # Apply tier filter
    if tier_filter:
        query = query.filter_by(subscription_tier=tier_filter)

    # Order by creation date (newest first)
    query = query.order_by(User.created_at.desc())

    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items

    # Log admin access
    log_security_event(
        user_id=current_user.id,
        event_type='admin_users_view',
        description=f'Admin viewed users list (page {page}, search: "{search}", tier: "{tier_filter}")',
        success=True
    )

    return render_template(
        'admin/users.html',
        users=users,
        pagination=pagination,
        search=search,
        tier_filter=tier_filter
    )


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """
    View detailed information about a specific user.
    """
    user = User.query.get_or_404(user_id)

    # Get user's subscription history
    subscription_history = SubscriptionHistory.query.filter_by(
        user_id=user_id
    ).order_by(SubscriptionHistory.created_at.desc()).limit(10).all()

    # Get recent audit logs for this user
    audit_logs = AuditLog.query.filter_by(
        user_id=user_id
    ).order_by(AuditLog.created_at.desc()).limit(20).all()

    log_security_event(
        user_id=current_user.id,
        event_type='admin_user_detail_view',
        description=f'Admin viewed details for user {user.email} (ID: {user_id})',
        success=True
    )

    return render_template(
        'admin/user_detail.html',
        user=user,
        subscription_history=subscription_history,
        audit_logs=audit_logs
    )


@admin_bp.route('/users/<int:user_id>/grant-premium', methods=['POST'])
@login_required
@admin_required
def grant_premium(user_id):
    """
    Grant lifetime premium access to a user.
    """
    user = User.query.get_or_404(user_id)

    # Get the tier from form (default to lifetime)
    tier = request.form.get('tier', 'lifetime')
    if tier not in ['monthly', 'annual', 'lifetime']:
        tier = 'lifetime'

    # Store previous state for logging
    previous_tier = user.subscription_tier
    previous_status = user.subscription_status

    try:
        # Update user subscription
        user.subscription_tier = tier
        user.subscription_status = 'active'
        user.subscription_start_date = datetime.utcnow()
        user.habit_limit = 999  # Effectively unlimited

        # For lifetime, no end date needed
        if tier == 'lifetime':
            user.subscription_end_date = None
        else:
            # For monthly/annual, set appropriate end date
            from datetime import timedelta
            if tier == 'monthly':
                user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            else:  # annual
                user.subscription_end_date = datetime.utcnow() + timedelta(days=365)

        # Create subscription history record
        subscription_record = SubscriptionHistory(
            user_id=user.id,
            subscription_type=tier,
            status='active',
            amount=0,  # Admin granted - free
            currency='USD',
            notes=f'Premium access granted by admin (ID: {current_user.id}, Email: {current_user.email})'
        )
        db.session.add(subscription_record)

        db.session.commit()

        # Log the action
        log_security_event(
            user_id=current_user.id,
            event_type='admin_grant_premium',
            description=f'Admin granted {tier} premium to user {user.email} (ID: {user_id}). Previous: {previous_tier}/{previous_status}',
            success=True,
            metadata={
                'target_user_id': user_id,
                'target_email': user.email,
                'new_tier': tier,
                'previous_tier': previous_tier,
                'previous_status': previous_status
            }
        )

        flash(f'Successfully granted {tier} premium to {user.email}', 'success')

    except Exception as e:
        db.session.rollback()
        log_security_event(
            user_id=current_user.id,
            event_type='admin_grant_premium',
            description=f'Failed to grant premium to user {user.email}: {str(e)}',
            success=False,
            error_message=str(e)
        )
        flash(f'Error granting premium: {str(e)}', 'danger')

    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/revoke-premium', methods=['POST'])
@login_required
@admin_required
def revoke_premium(user_id):
    """
    Revoke premium access from a user (downgrade to free).
    """
    user = User.query.get_or_404(user_id)

    # Store previous state for logging
    previous_tier = user.subscription_tier
    previous_status = user.subscription_status

    try:
        # Downgrade to free tier
        user.subscription_tier = 'free'
        user.subscription_status = 'cancelled'
        user.subscription_end_date = datetime.utcnow()
        user.habit_limit = 3  # Free tier limit

        # Create subscription history record
        subscription_record = SubscriptionHistory(
            user_id=user.id,
            subscription_type='free',
            status='cancelled',
            amount=0,
            currency='USD',
            notes=f'Premium access revoked by admin (ID: {current_user.id}, Email: {current_user.email})'
        )
        db.session.add(subscription_record)

        db.session.commit()

        # Log the action
        log_security_event(
            user_id=current_user.id,
            event_type='admin_revoke_premium',
            description=f'Admin revoked premium from user {user.email} (ID: {user_id}). Previous: {previous_tier}/{previous_status}',
            success=True,
            metadata={
                'target_user_id': user_id,
                'target_email': user.email,
                'previous_tier': previous_tier,
                'previous_status': previous_status
            }
        )

        flash(f'Successfully revoked premium from {user.email}', 'success')

    except Exception as e:
        db.session.rollback()
        log_security_event(
            user_id=current_user.id,
            event_type='admin_revoke_premium',
            description=f'Failed to revoke premium from user {user.email}: {str(e)}',
            success=False,
            error_message=str(e)
        )
        flash(f'Error revoking premium: {str(e)}', 'danger')

    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """
    Toggle admin status for a user.
    Cannot remove admin from yourself.
    """
    user = User.query.get_or_404(user_id)

    # Prevent removing admin from yourself
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'warning')
        return redirect(url_for('admin.user_detail', user_id=user_id))

    try:
        previous_status = user.is_admin
        user.is_admin = not user.is_admin
        db.session.commit()

        action = 'granted' if user.is_admin else 'revoked'

        log_security_event(
            user_id=current_user.id,
            event_type='admin_toggle_admin',
            description=f'Admin {action} admin privileges for user {user.email} (ID: {user_id})',
            success=True,
            metadata={
                'target_user_id': user_id,
                'target_email': user.email,
                'new_status': user.is_admin,
                'previous_status': previous_status
            }
        )

        flash(f'Successfully {action} admin privileges for {user.email}', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating admin status: {str(e)}', 'danger')

    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/api/users/search')
@login_required
@admin_required
def api_search_users():
    """
    API endpoint for searching users (for autocomplete).
    Returns JSON with matching users.
    """
    search = request.args.get('q', '').strip()

    if len(search) < 2:
        return jsonify([])

    users = User.query.filter(
        User.email.ilike(f'%{search}%'),
        User.account_deleted == False
    ).limit(10).all()

    return jsonify([{
        'id': u.id,
        'email': u.email,
        'tier': u.subscription_tier,
        'is_admin': u.is_admin
    } for u in users])
