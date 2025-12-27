"""
Subscription Blueprint for HabitFlow
Handles pricing page, checkout, billing history, and subscription management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, PaymentTransaction, SubscriptionHistory
from stripe_handler import create_checkout_session, cancel_subscription
import stripe

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/pricing')
def pricing():
    """Display pricing page with subscription options."""
    plans = {
        'monthly': {
            'name': 'Monthly',
            'price': '$2.99',
            'period': 'per month',
            'features': [
                'Unlimited habits',
                'Advanced statistics',
                'Priority support',
                'Cancel anytime'
            ]
        },
        'annual': {
            'name': 'Annual',
            'price': '$19.99',
            'period': 'per year',
            'savings': 'Save 44%',
            'features': [
                'Unlimited habits',
                'Advanced statistics',
                'Priority support',
                'Best value - 2 months free!'
            ]
        },
        'lifetime': {
            'name': 'Lifetime',
            'price': '$59.99',
            'period': 'one-time',
            'badge': 'Best Deal',
            'features': [
                'Unlimited habits forever',
                'Advanced statistics',
                'Priority support',
                'All future features included',
                'One-time payment'
            ]
        }
    }

    return render_template('pricing.html', plans=plans)


@subscription_bp.route('/checkout/<plan_type>')
@login_required
def checkout(plan_type):
    """Create Stripe checkout session and redirect to Stripe."""
    if plan_type not in ['monthly', 'annual', 'lifetime']:
        flash('Invalid subscription plan selected.', 'danger')
        return redirect(url_for('subscription.pricing'))

    # Check if user is already premium
    if current_user.is_premium_active() and current_user.subscription_status != 'free':
        flash('You already have an active subscription. Please cancel first to change plans.', 'info')
        return redirect(url_for('subscription.manage'))

    # Create checkout session
    success_url = url_for('subscription.success', _external=True)
    cancel_url = url_for('subscription.pricing', _external=True)

    session = create_checkout_session(
        user=current_user,
        plan_type=plan_type,
        success_url=success_url,
        cancel_url=cancel_url
    )

    if not session:
        flash('Unable to create checkout session. Please try again later.', 'danger')
        return redirect(url_for('subscription.pricing'))

    # Redirect to Stripe Checkout
    return redirect(session.url, code=303)


@subscription_bp.route('/success')
@login_required
def success():
    """Payment success page."""
    return render_template('subscription_success.html')


@subscription_bp.route('/manage')
@login_required
def manage():
    """Subscription management page."""
    # Get user's subscription history
    subscription_history = SubscriptionHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(SubscriptionHistory.created_at.desc()).all()

    return render_template(
        'subscription_manage.html',
        history=subscription_history
    )


@subscription_bp.route('/billing-history')
@login_required
def billing_history():
    """Display billing history and invoices."""
    # Get paginated payment transactions
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = PaymentTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(PaymentTransaction.transaction_date.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template(
        'billing_history.html',
        transactions=pagination.items,
        pagination=pagination
    )


@subscription_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription_route():
    """Cancel user's subscription."""
    if not current_user.is_premium_active():
        flash('You do not have an active subscription to cancel.', 'warning')
        return redirect(url_for('subscription.manage'))

    if current_user.subscription_status == 'lifetime':
        flash('Lifetime subscriptions cannot be cancelled.', 'info')
        return redirect(url_for('subscription.manage'))

    # Cancel the Stripe subscription
    if cancel_subscription(current_user):
        flash(
            'Your subscription has been cancelled. You will retain access until the end of your billing period.',
            'success'
        )
    else:
        flash('Unable to cancel subscription. Please contact support.', 'danger')

    return redirect(url_for('subscription.manage'))
