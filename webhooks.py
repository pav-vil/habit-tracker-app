# webhooks.py - Webhook Handlers for HabitFlow
# Handles asynchronous payment events from Stripe, PayPal, and Coinbase Commerce

from flask import Blueprint, request, jsonify, current_app
from models import db, User, Subscription, Payment
from datetime import datetime, timedelta
import stripe

# Create blueprint for webhook routes
webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')


# ==========================================
# STRIPE WEBHOOKS (Phase 3)
# ==========================================

@webhooks_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.
    Processes async payment notifications from Stripe.

    Critical events handled:
    - checkout.session.completed: New subscription/payment successful
    - customer.subscription.updated: Subscription changed
    - customer.subscription.deleted: Subscription cancelled
    - invoice.payment_succeeded: Recurring payment successful
    - invoice.payment_failed: Payment failure

    Security:
    - Verifies webhook signature to ensure request is from Stripe
    - Rejects unsigned or invalid requests

    Returns:
        JSON response with status
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    # Verify webhook signature
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        webhook_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

        # Construct event from payload and signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

    except ValueError as e:
        # Invalid payload
        print(f"[STRIPE WEBHOOK] Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"[STRIPE WEBHOOK] Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event based on type
    event_type = event['type']
    data_object = event['data']['object']

    print(f"[STRIPE WEBHOOK] Received event: {event_type}")

    # Event: Checkout session completed (new subscription or one-time payment)
    if event_type == 'checkout.session.completed':
        handle_checkout_session_completed(data_object)

    # Event: Subscription updated (tier change, status change)
    elif event_type == 'customer.subscription.updated':
        handle_subscription_updated(data_object)

    # Event: Subscription deleted (cancellation confirmed)
    elif event_type == 'customer.subscription.deleted':
        handle_subscription_deleted(data_object)

    # Event: Invoice payment succeeded (recurring payment successful)
    elif event_type == 'invoice.payment_succeeded':
        handle_invoice_payment_succeeded(data_object)

    # Event: Invoice payment failed (payment failure)
    elif event_type == 'invoice.payment_failed':
        handle_invoice_payment_failed(data_object)

    # Other events (log but don't process)
    else:
        print(f"[STRIPE WEBHOOK] Unhandled event type: {event_type}")

    return jsonify({'status': 'success'}), 200


def handle_checkout_session_completed(session):
    """
    Handle checkout.session.completed event.
    Called when a user completes initial checkout.

    This is primarily a backup to the success page handler.
    The success page handles most updates, but webhook ensures
    completion even if user closes browser before redirect.

    Args:
        session (dict): Stripe checkout session object
    """
    try:
        user_id = session['metadata'].get('user_id')
        tier = session['metadata'].get('tier')

        if not user_id or not tier:
            print("[STRIPE WEBHOOK] Missing metadata in checkout session")
            return

        user = db.session.get(User, int(user_id))
        if not user:
            print(f"[STRIPE WEBHOOK] User not found: {user_id}")
            return

        # Only update if not already updated (idempotency check)
        if user.subscription_tier != tier:
            user.subscription_tier = tier
            user.subscription_status = 'active'
            user.subscription_start_date = datetime.utcnow()

            # Set end date
            if tier == 'monthly':
                user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            elif tier == 'annual':
                user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
            elif tier == 'lifetime':
                user.subscription_end_date = None

            if session.get('subscription'):
                user.stripe_subscription_id = session['subscription']

            user.last_payment_date = datetime.utcnow()

            db.session.commit()
            print(f"[STRIPE WEBHOOK] Updated user {user_id} to {tier} tier")

    except Exception as e:
        db.session.rollback()
        print(f"[STRIPE WEBHOOK ERROR] checkout.session.completed: {e}")


def handle_subscription_updated(subscription):
    """
    Handle customer.subscription.updated event.
    Called when subscription status changes (e.g., cancel_at_period_end set).

    Args:
        subscription (dict): Stripe subscription object
    """
    try:
        customer_id = subscription['customer']

        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"[STRIPE WEBHOOK] User not found for customer: {customer_id}")
            return

        # Check if subscription is set to cancel
        if subscription.get('cancel_at_period_end'):
            user.subscription_status = 'cancelled'
            user.subscription_end_date = datetime.fromtimestamp(subscription['current_period_end'])
            db.session.commit()
            print(f"[STRIPE WEBHOOK] User {user.id} subscription set to cancel at period end")

        # Check if subscription status changed to active
        elif subscription['status'] == 'active':
            user.subscription_status = 'active'
            db.session.commit()
            print(f"[STRIPE WEBHOOK] User {user.id} subscription reactivated")

    except Exception as e:
        db.session.rollback()
        print(f"[STRIPE WEBHOOK ERROR] customer.subscription.updated: {e}")


def handle_subscription_deleted(subscription):
    """
    Handle customer.subscription.deleted event.
    Called when subscription is permanently cancelled.

    Args:
        subscription (dict): Stripe subscription object
    """
    try:
        customer_id = subscription['customer']

        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"[STRIPE WEBHOOK] User not found for customer: {customer_id}")
            return

        # Downgrade to free tier
        user.subscription_tier = 'free'
        user.subscription_status = 'expired'
        user.subscription_end_date = datetime.utcnow()
        user.stripe_subscription_id = None

        db.session.commit()
        print(f"[STRIPE WEBHOOK] User {user.id} subscription deleted, downgraded to free")

    except Exception as e:
        db.session.rollback()
        print(f"[STRIPE WEBHOOK ERROR] customer.subscription.deleted: {e}")


def handle_invoice_payment_succeeded(invoice):
    """
    Handle invoice.payment_succeeded event.
    Called when recurring payment is successful (monthly/annual renewal).

    Creates a Payment record for each successful renewal.

    Args:
        invoice (dict): Stripe invoice object
    """
    try:
        customer_id = invoice['customer']

        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"[STRIPE WEBHOOK] User not found for customer: {customer_id}")
            return

        # Update last payment date
        user.last_payment_date = datetime.utcnow()
        user.payment_failures = 0  # Reset failure count

        # Extend subscription end date
        if user.subscription_tier == 'monthly':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        elif user.subscription_tier == 'annual':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=365)

        # Create Payment record
        payment = Payment(
            user_id=user.id,
            subscription_id=None,  # Could link to Subscription if needed
            payment_provider='stripe',
            provider_transaction_id=invoice['payment_intent'] if invoice.get('payment_intent') else invoice['id'],
            amount=invoice['amount_paid'] / 100.0,  # Convert from cents
            currency=invoice['currency'].upper(),
            status='completed',
            payment_type='renewal',
            payment_date=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()

        print(f"[STRIPE WEBHOOK] User {user.id} payment succeeded, subscription extended")

    except Exception as e:
        db.session.rollback()
        print(f"[STRIPE WEBHOOK ERROR] invoice.payment_succeeded: {e}")


def handle_invoice_payment_failed(invoice):
    """
    Handle invoice.payment_failed event.
    Called when recurring payment fails.

    Increments failure count and updates subscription status.
    After 3 failures, subscription is cancelled.

    Args:
        invoice (dict): Stripe invoice object
    """
    try:
        customer_id = invoice['customer']

        # Find user by Stripe customer ID
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            print(f"[STRIPE WEBHOOK] User not found for customer: {customer_id}")
            return

        # Increment payment failure count
        user.payment_failures += 1

        # Create Payment record for failed payment
        payment = Payment(
            user_id=user.id,
            subscription_id=None,
            payment_provider='stripe',
            provider_transaction_id=invoice['id'],
            amount=invoice['amount_due'] / 100.0,  # Convert from cents
            currency=invoice['currency'].upper(),
            status='failed',
            payment_type='renewal',
            payment_date=datetime.utcnow(),
            notes=f"Payment attempt {user.payment_failures} failed"
        )
        db.session.add(payment)

        # If 3+ failures, cancel subscription
        if user.payment_failures >= 3:
            user.subscription_status = 'expired'
            user.subscription_tier = 'free'
            user.subscription_end_date = datetime.utcnow()
            print(f"[STRIPE WEBHOOK] User {user.id} subscription cancelled after {user.payment_failures} failures")

        db.session.commit()
        print(f"[STRIPE WEBHOOK] User {user.id} payment failed ({user.payment_failures} failures)")

    except Exception as e:
        db.session.rollback()
        print(f"[STRIPE WEBHOOK ERROR] invoice.payment_failed: {e}")


# ==========================================
# PAYPAL WEBHOOKS (Phase 5)
# ==========================================

@webhooks_bp.route('/paypal', methods=['POST'])
def paypal_webhook():
    """
    Handle PayPal webhook events.
    TODO: Implement in Phase 5
    """
    return jsonify({'status': 'not implemented'}), 501


# ==========================================
# COINBASE COMMERCE WEBHOOKS (Phase 6)
# ==========================================

@webhooks_bp.route('/coinbase', methods=['POST'])
def coinbase_webhook():
    """
    Handle Coinbase Commerce webhook events.
    TODO: Implement in Phase 6
    """
    return jsonify({'status': 'not implemented'}), 501
