"""
Stripe payment handler for HabitFlow
Handles checkout sessions, subscription management, and webhook events
"""
import stripe
import os
from datetime import datetime, timedelta
from flask import current_app, url_for
from models import db, User, SubscriptionHistory, PaymentTransaction
from email_service import (
    send_payment_success_email,
    send_payment_failed_email,
    send_subscription_cancelled_email,
    send_subscription_expired_email
)


def init_stripe():
    """Initialize Stripe with API key."""
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')


def create_checkout_session(user, plan_type, success_url, cancel_url):
    """
    Create a Stripe Checkout session for subscription purchase.

    Args:
        user: User model instance
        plan_type: 'monthly', 'annual', or 'lifetime'
        success_url: URL to redirect on successful payment
        cancel_url: URL to redirect on cancelled payment

    Returns:
        Checkout session object or None if error
    """
    init_stripe()

    # Map plan types to Stripe Price IDs
    price_ids = {
        'monthly': current_app.config.get('STRIPE_PRICE_ID_MONTHLY'),
        'annual': current_app.config.get('STRIPE_PRICE_ID_ANNUAL'),
        'lifetime': current_app.config.get('STRIPE_PRICE_ID_LIFETIME'),
    }

    price_id = price_ids.get(plan_type)
    if not price_id:
        print(f"[STRIPE] Error: No price ID configured for plan: {plan_type}")
        return None

    try:
        # Create or get Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={'user_id': user.id}
            )
            user.stripe_customer_id = customer.id
            db.session.commit()

        # Determine mode based on plan type
        mode = 'payment' if plan_type == 'lifetime' else 'subscription'

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            mode=mode,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': user.id,
                'plan_type': plan_type
            }
        )

        print(f"[STRIPE] Checkout session created: {session.id} for user {user.id}")
        return session

    except stripe.error.StripeError as e:
        print(f"[STRIPE] Error creating checkout session: {e}")
        return None


def handle_checkout_completed(session):
    """
    Handle successful checkout completion.
    Activates subscription and records payment.

    Args:
        session: Stripe checkout session object
    """
    user_id = int(session.metadata.get('user_id'))
    plan_type = session.metadata.get('plan_type')

    user = db.session.get(User, user_id)
    if not user:
        print(f"[STRIPE] Error: User {user_id} not found")
        return

    # Calculate subscription end date
    if plan_type == 'lifetime':
        subscription_end_date = None
        stripe_subscription_id = None
    elif plan_type == 'monthly':
        subscription_end_date = datetime.utcnow() + timedelta(days=30)
        stripe_subscription_id = session.subscription
    elif plan_type == 'annual':
        subscription_end_date = datetime.utcnow() + timedelta(days=365)
        stripe_subscription_id = session.subscription
    else:
        print(f"[STRIPE] Error: Unknown plan type {plan_type}")
        return

    # Update user subscription
    old_status = user.subscription_status
    user.subscription_status = plan_type
    user.subscription_end_date = subscription_end_date
    user.habit_limit = 999999  # Effectively unlimited

    # Create subscription history record
    subscription_history = SubscriptionHistory(
        user_id=user.id,
        subscription_type=plan_type,
        status='active',
        started_at=datetime.utcnow(),
        stripe_subscription_id=stripe_subscription_id,
        amount=session.amount_total / 100,  # Convert from cents
        currency=session.currency.upper(),
        notes=f'Upgraded from {old_status} to {plan_type}'
    )
    db.session.add(subscription_history)
    db.session.flush()  # Get the ID

    # Create payment transaction record
    payment_transaction = PaymentTransaction(
        user_id=user.id,
        provider='stripe',
        provider_transaction_id=session.payment_intent,
        stripe_invoice_id=session.invoice if hasattr(session, 'invoice') else None,
        amount=session.amount_total / 100,
        currency=session.currency.upper(),
        status='completed',
        subscription_type=plan_type,
        subscription_history_id=subscription_history.id,
        transaction_date=datetime.utcnow(),
        payment_metadata={
            'checkout_session_id': session.id,
            'customer_id': session.customer
        }
    )
    db.session.add(payment_transaction)

    db.session.commit()

    print(f"[STRIPE] ✓ Subscription activated for user {user.id}: {plan_type}")

    # Send payment success email
    send_payment_success_email(
        user=user,
        amount=session.amount_total / 100,
        subscription_type=plan_type
    )


def handle_subscription_updated(subscription):
    """
    Handle subscription update events (renewals, changes).

    Args:
        subscription: Stripe subscription object
    """
    customer_id = subscription.customer
    user = User.query.filter_by(stripe_customer_id=customer_id).first()

    if not user:
        print(f"[STRIPE] Error: No user found for customer {customer_id}")
        return

    # Update subscription end date based on current period end
    user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)

    # Check if subscription is active or cancelled
    if subscription.status == 'active':
        # Determine plan type from subscription items
        plan_type = 'monthly'  # Default
        # You would need to check subscription.items to determine if annual

        user.subscription_status = plan_type
        user.habit_limit = 999999
    elif subscription.status in ['canceled', 'unpaid']:
        # Don't immediately downgrade - wait until end date
        print(f"[STRIPE] Subscription {subscription.id} status: {subscription.status}")

    db.session.commit()
    print(f"[STRIPE] ✓ Subscription updated for user {user.id}")


def handle_subscription_deleted(subscription):
    """
    Handle subscription cancellation/deletion.

    Args:
        subscription: Stripe subscription object
    """
    customer_id = subscription.customer
    user = User.query.filter_by(stripe_customer_id=customer_id).first()

    if not user:
        print(f"[STRIPE] Error: No user found for customer {customer_id}")
        return

    # Record cancellation in history
    subscription_history = SubscriptionHistory(
        user_id=user.id,
        subscription_type=user.subscription_status,
        status='cancelled',
        started_at=datetime.utcnow(),
        stripe_subscription_id=subscription.id,
        notes='Subscription cancelled'
    )
    db.session.add(subscription_history)

    # Downgrade user to free tier
    user.subscription_status = 'free'
    user.subscription_end_date = None
    user.habit_limit = 3

    db.session.commit()
    print(f"[STRIPE] ✓ Subscription cancelled for user {user.id}")


def handle_payment_failed(invoice):
    """
    Handle failed payment attempts.

    Args:
        invoice: Stripe invoice object
    """
    customer_id = invoice.customer
    user = User.query.filter_by(stripe_customer_id=customer_id).first()

    if not user:
        print(f"[STRIPE] Error: No user found for customer {customer_id}")
        return

    # Record failed payment
    payment_transaction = PaymentTransaction(
        user_id=user.id,
        provider='stripe',
        provider_transaction_id=invoice.payment_intent if invoice.payment_intent else f"failed_{invoice.id}",
        stripe_invoice_id=invoice.id,
        amount=invoice.amount_due / 100,
        currency=invoice.currency.upper(),
        status='failed',
        subscription_type=user.subscription_status,
        transaction_date=datetime.utcnow(),
        payment_metadata={
            'failure_reason': 'Payment failed',
            'invoice_id': invoice.id
        }
    )
    db.session.add(payment_transaction)
    db.session.commit()

    print(f"[STRIPE] WARNING: Payment failed for user {user.id}")

    # Send payment failed email
    send_payment_failed_email(
        user=user,
        amount=invoice.amount_due / 100
    )


def cancel_subscription(user):
    """
    Cancel a user's active Stripe subscription.

    Args:
        user: User model instance

    Returns:
        True if successful, False otherwise
    """
    init_stripe()

    if not user.stripe_customer_id:
        return False

    try:
        # Get active subscriptions for customer
        subscriptions = stripe.Subscription.list(
            customer=user.stripe_customer_id,
            status='active'
        )

        for subscription in subscriptions.data:
            # Cancel at period end (don't immediately cut off access)
            stripe.Subscription.modify(
                subscription.id,
                cancel_at_period_end=True
            )
            print(f"[STRIPE] Subscription {subscription.id} set to cancel at period end")

        # Send cancellation confirmation email
        send_subscription_cancelled_email(
            user=user,
            end_date=user.subscription_end_date
        )

        return True

    except stripe.error.StripeError as e:
        print(f"[STRIPE] Error cancelling subscription: {e}")
        return False


def downgrade_user_to_free(user, reason="subscription_expired"):
    """
    Downgrade a user from premium to free tier.
    Handles users who have more than 3 habits.

    Args:
        user: User model instance
        reason: Reason for downgrade (subscription_expired, cancelled, payment_failed)

    Returns:
        dict with downgrade info
    """
    from models import Habit

    old_status = user.subscription_status
    active_habit_count = Habit.query.filter_by(
        user_id=user.id,
        archived=False
    ).count()

    # Record in subscription history
    subscription_history = SubscriptionHistory(
        user_id=user.id,
        subscription_type=old_status,
        status='downgraded',
        started_at=datetime.utcnow(),
        notes=f'Downgraded to free tier: {reason}'
    )
    db.session.add(subscription_history)

    # Downgrade user
    user.subscription_status = 'free'
    user.subscription_end_date = None
    user.habit_limit = 3

    db.session.commit()

    print(f"[DOWNGRADE] User {user.id} downgraded from {old_status} to free")
    print(f"[DOWNGRADE] User has {active_habit_count} active habits (limit: 3)")

    return {
        'old_status': old_status,
        'active_habits': active_habit_count,
        'over_limit': active_habit_count > 3,
        'habits_to_archive': max(0, active_habit_count - 3)
    }


def check_expired_subscriptions():
    """
    Check for expired subscriptions and downgrade users.
    This should be run as a scheduled task (e.g., daily cron job).

    Returns:
        Number of users downgraded
    """
    downgraded_count = 0

    # Find users with expired subscriptions
    expired_users = User.query.filter(
        User.subscription_status.in_(['monthly', 'annual']),
        User.subscription_end_date <= datetime.utcnow()
    ).all()

    for user in expired_users:
        downgrade_info = downgrade_user_to_free(user, reason="subscription_expired")
        downgraded_count += 1

        if downgrade_info['over_limit']:
            print(f"[DOWNGRADE] User {user.id} needs to archive {downgrade_info['habits_to_archive']} habits")

        # Send subscription expired email
        send_subscription_expired_email(
            user=user,
            habits_to_archive=downgrade_info['habits_to_archive']
        )

    print(f"[DOWNGRADE] Processed {downgraded_count} expired subscriptions")
    return downgraded_count
