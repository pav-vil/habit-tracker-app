"""
Manual Payment Blueprint
Handles SINPE Móvil and manual payment requests for Costa Rica users.
Includes admin panel for approving/rejecting payment requests.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, PaymentRequest, User, SubscriptionHistory, PaymentTransaction
from datetime import datetime, timedelta
from functools import wraps

manual_payment_bp = Blueprint('manual_payment', __name__, url_prefix='/payment')


# ============================================================================
# ADMIN REQUIRED DECORATOR
# ============================================================================

def admin_required(f):
    """Decorator to require admin privileges for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('habits.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# PRICING CONFIGURATION
# ============================================================================

PRICING = {
    'monthly': {
        'crc': 1500,
        'usd': 2.99,
        'habit_limit': 999,  # Unlimited
        'duration_days': 30
    },
    'annual': {
        'crc': 10000,
        'usd': 19.99,
        'habit_limit': 999,
        'duration_days': 365
    },
    'lifetime': {
        'crc': 30000,
        'usd': 59.99,
        'habit_limit': 999,
        'duration_days': None  # Forever
    }
}


# ============================================================================
# USER-FACING ROUTES
# ============================================================================

@manual_payment_bp.route('/plans')
@login_required
def view_plans():
    """Show available subscription plans with SINPE Móvil payment option."""
    return render_template('manual_payment/plans.html', pricing=PRICING)


@manual_payment_bp.route('/request/<tier>', methods=['GET', 'POST'])
@login_required
def create_request(tier):
    """Create a new payment request for a subscription tier."""

    if tier not in PRICING:
        flash('Invalid subscription plan.', 'danger')
        return redirect(url_for('manual_payment.view_plans'))

    # Check if user already has a pending request
    pending_request = PaymentRequest.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).first()

    if pending_request:
        flash('You already have a pending payment request. Please wait for approval.', 'warning')
        return redirect(url_for('manual_payment.my_requests'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method', 'sinpe_movil')
        phone_number = request.form.get('phone_number', '').strip()
        transaction_reference = request.form.get('transaction_reference', '').strip()
        payment_proof_notes = request.form.get('payment_proof_notes', '').strip()

        # Validation
        if payment_method == 'sinpe_movil' and not phone_number:
            flash('Please provide your SINPE Móvil phone number.', 'danger')
            return render_template('manual_payment/request.html',
                                 tier=tier,
                                 pricing=PRICING[tier])

        if not transaction_reference:
            flash('Please provide a transaction reference or confirmation number.', 'danger')
            return render_template('manual_payment/request.html',
                                 tier=tier,
                                 pricing=PRICING[tier])

        # Create payment request
        new_request = PaymentRequest(
            user_id=current_user.id,
            subscription_tier=tier,
            amount=PRICING[tier]['crc'],
            currency='CRC',
            payment_method=payment_method,
            phone_number=phone_number,
            transaction_reference=transaction_reference,
            payment_proof_notes=payment_proof_notes,
            status='pending'
        )

        db.session.add(new_request)
        db.session.commit()

        flash('Payment request submitted successfully! We will review it within 24 hours.', 'success')
        return redirect(url_for('manual_payment.my_requests'))

    # GET request - show form
    return render_template('manual_payment/request.html',
                         tier=tier,
                         pricing=PRICING[tier])


@manual_payment_bp.route('/my-requests')
@login_required
def my_requests():
    """Show user's payment requests history."""
    requests = PaymentRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(PaymentRequest.created_at.desc()).all()

    return render_template('manual_payment/my_requests.html', requests=requests)


@manual_payment_bp.route('/cancel-request/<int:request_id>', methods=['POST'])
@login_required
def cancel_request(request_id):
    """Cancel a pending payment request."""
    payment_request = PaymentRequest.query.filter_by(
        id=request_id,
        user_id=current_user.id,
        status='pending'
    ).first_or_404()

    payment_request.status = 'cancelled'
    payment_request.updated_at = datetime.utcnow()
    db.session.commit()

    flash('Payment request cancelled.', 'info')
    return redirect(url_for('manual_payment.my_requests'))


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@manual_payment_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard showing all payment requests."""

    # Get filter from query params
    status_filter = request.args.get('status', 'pending')

    query = PaymentRequest.query

    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)

    # Get payment requests with user info
    payment_requests = query.order_by(PaymentRequest.created_at.desc()).all()

    # Get statistics
    stats = {
        'pending': PaymentRequest.query.filter_by(status='pending').count(),
        'approved': PaymentRequest.query.filter_by(status='approved').count(),
        'rejected': PaymentRequest.query.filter_by(status='rejected').count(),
        'total': PaymentRequest.query.count()
    }

    return render_template('manual_payment/admin_dashboard.html',
                         payment_requests=payment_requests,
                         stats=stats,
                         current_filter=status_filter)


@manual_payment_bp.route('/admin/approve/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def approve_request(request_id):
    """Approve a payment request and activate subscription."""

    payment_request = PaymentRequest.query.get_or_404(request_id)

    if payment_request.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('manual_payment.admin_dashboard'))

    admin_notes = request.form.get('admin_notes', '').strip()

    try:
        # Update payment request
        payment_request.status = 'approved'
        payment_request.reviewed_by = current_user.id
        payment_request.reviewed_at = datetime.utcnow()
        payment_request.admin_notes = admin_notes

        # Get user
        user = User.query.get(payment_request.user_id)

        # Activate subscription
        tier = payment_request.subscription_tier
        user.subscription_tier = tier
        user.subscription_status = 'active'
        user.subscription_start_date = datetime.utcnow()
        user.last_payment_date = datetime.utcnow()

        # Set end date for monthly/annual
        if tier == 'monthly':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            user.habit_limit = 999
        elif tier == 'annual':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
            user.habit_limit = 999
        elif tier == 'lifetime':
            user.subscription_end_date = None  # Never expires
            user.habit_limit = 999

        # Create subscription history record
        sub_history = SubscriptionHistory(
            user_id=user.id,
            subscription_type=tier,
            status='active',
            started_at=datetime.utcnow(),
            amount=payment_request.amount,
            currency=payment_request.currency,
            notes=f'Manual payment via {payment_request.payment_method}. Reference: {payment_request.transaction_reference}'
        )
        db.session.add(sub_history)

        # Create payment transaction record
        payment_tx = PaymentTransaction(
            user_id=user.id,
            provider='manual_' + payment_request.payment_method,
            provider_transaction_id=f'MANUAL-{payment_request.id}-{int(datetime.utcnow().timestamp())}',
            amount=payment_request.amount,
            currency=payment_request.currency,
            status='completed',
            subscription_type=tier,
            transaction_date=datetime.utcnow(),
            payment_metadata={
                'payment_method': payment_request.payment_method,
                'phone_number': payment_request.phone_number,
                'transaction_reference': payment_request.transaction_reference,
                'approved_by_admin': current_user.email
            }
        )
        db.session.add(payment_tx)

        db.session.commit()

        flash(f'Payment approved! User {user.email} now has {tier} subscription.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error approving payment: {str(e)}', 'danger')

    return redirect(url_for('manual_payment.admin_dashboard'))


@manual_payment_bp.route('/admin/reject/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_request(request_id):
    """Reject a payment request."""

    payment_request = PaymentRequest.query.get_or_404(request_id)

    if payment_request.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('manual_payment.admin_dashboard'))

    admin_notes = request.form.get('admin_notes', '').strip()

    if not admin_notes:
        flash('Please provide a reason for rejection.', 'danger')
        return redirect(url_for('manual_payment.admin_dashboard'))

    # Update payment request
    payment_request.status = 'rejected'
    payment_request.reviewed_by = current_user.id
    payment_request.reviewed_at = datetime.utcnow()
    payment_request.admin_notes = admin_notes
    payment_request.updated_at = datetime.utcnow()

    db.session.commit()

    user = User.query.get(payment_request.user_id)
    flash(f'Payment request from {user.email} has been rejected.', 'info')

    return redirect(url_for('manual_payment.admin_dashboard'))


@manual_payment_bp.route('/admin/make-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    """Grant admin privileges to a user (super admin only)."""

    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash(f'{user.email} is already an admin.', 'info')
    else:
        user.is_admin = True
        db.session.commit()
        flash(f'{user.email} is now an admin.', 'success')

    return redirect(url_for('manual_payment.admin_dashboard'))
