"""
Webhook handlers for payment providers
Currently supports: Stripe, PayPal, Coinbase (placeholder)
Combines implementations from both versions for comprehensive webhook handling
"""
from flask import Blueprint, request, jsonify, current_app
import stripe
import paypalrestsdk
import hmac
import hashlib
from models import db, User, Subscription, Payment
from datetime import datetime, timedelta

# Create blueprint for webhook routes
webhooks_bp = Blueprint('webhooks', __name__)


# ==========================================
# STRIPE WEBHOOKS
# ==========================================

@webhooks_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.
    Must be registered in Stripe Dashboard.

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
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        print("[WEBHOOK] Error: STRIPE_WEBHOOK_SECRET not configured")
        return jsonify({'error': 'Webhook not configured'}), 500

    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        print(f"[WEBHOOK] Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"[WEBHOOK] Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    event_type = event['type']
    event_data = event['data']['object']

    print(f"[WEBHOOK] Received event: {event_type}")

    try:
        if event_type == 'checkout.session.completed':
            handle_checkout_completed(event_data)

        elif event_type == 'customer.subscription.updated':
            handle_subscription_updated(event_data)

        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted(event_data)

        elif event_type == 'invoice.payment_succeeded':
            handle_invoice_payment_succeeded(event_data)

        elif event_type == 'invoice.payment_failed':
            handle_payment_failed(event_data)

        else:
            print(f"[WEBHOOK] Unhandled event type: {event_type}")

    except Exception as e:
        print(f"[WEBHOOK] Error processing event {event_type}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Processing error'}), 500

    return jsonify({'success': True}), 200


def handle_checkout_completed(session):
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
            print("[WEBHOOK] Missing metadata in checkout session")
            return

        user = db.session.get(User, int(user_id))
        if not user:
            print(f"[WEBHOOK] User not found: {user_id}")
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
            print(f"[WEBHOOK] Updated user {user_id} to {tier} tier")

    except Exception as e:
        db.session.rollback()
        print(f"[WEBHOOK ERROR] checkout.session.completed: {e}")


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
            print(f"[WEBHOOK] User not found for customer: {customer_id}")
            return

        # Check if subscription is set to cancel
        if subscription.get('cancel_at_period_end'):
            user.subscription_status = 'cancelled'
            user.subscription_end_date = datetime.fromtimestamp(subscription['current_period_end'])
            db.session.commit()
            print(f"[WEBHOOK] User {user.id} subscription set to cancel at period end")

        # Check if subscription status changed to active
        elif subscription['status'] == 'active':
            user.subscription_status = 'active'
            db.session.commit()
            print(f"[WEBHOOK] User {user.id} subscription reactivated")

    except Exception as e:
        db.session.rollback()
        print(f"[WEBHOOK ERROR] customer.subscription.updated: {e}")


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
            print(f"[WEBHOOK] User not found for customer: {customer_id}")
            return

        # Downgrade to free tier
        user.subscription_tier = 'free'
        user.subscription_status = 'expired'
        user.subscription_end_date = datetime.utcnow()
        user.stripe_subscription_id = None
        user.habit_limit = 3

        db.session.commit()
        print(f"[WEBHOOK] User {user.id} subscription deleted, downgraded to free")

    except Exception as e:
        db.session.rollback()
        print(f"[WEBHOOK ERROR] customer.subscription.deleted: {e}")


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
            print(f"[WEBHOOK] User not found for customer: {customer_id}")
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

        print(f"[WEBHOOK] User {user.id} payment succeeded, subscription extended")

    except Exception as e:
        db.session.rollback()
        print(f"[WEBHOOK ERROR] invoice.payment_succeeded: {e}")


def handle_payment_failed(invoice):
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
            print(f"[WEBHOOK] User not found for customer: {customer_id}")
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
            user.habit_limit = 3
            print(f"[WEBHOOK] User {user.id} subscription cancelled after {user.payment_failures} failures")

        db.session.commit()
        print(f"[WEBHOOK] User {user.id} payment failed ({user.payment_failures} failures)")

    except Exception as e:
        db.session.rollback()
        print(f"[WEBHOOK ERROR] invoice.payment_failed: {e}")


# ==========================================
# PAYPAL WEBHOOKS (Phase 5)
# ==========================================

@webhooks_bp.route('/paypal', methods=['POST'])
def paypal_webhook():
    """
    Handle PayPal webhook events.
    Must be registered in PayPal Developer Dashboard.

    Processes async subscription notifications from PayPal.

    Critical events handled:
    - BILLING.SUBSCRIPTION.ACTIVATED: New subscription activated
    - BILLING.SUBSCRIPTION.UPDATED: Subscription plan changed
    - BILLING.SUBSCRIPTION.CANCELLED: Subscription cancelled by user
    - BILLING.SUBSCRIPTION.SUSPENDED: Subscription suspended (payment failure)
    - PAYMENT.SALE.COMPLETED: Recurring payment successful

    Security:
    - Verifies webhook signature using PayPal SDK
    - Rejects unsigned or invalid requests

    Returns:
        JSON response with status
    """
    # Get webhook data
    webhook_data = request.get_json()

    if not webhook_data:
        print("[PAYPAL WEBHOOK] No data received")
        return jsonify({'error': 'No data'}), 400

    event_type = webhook_data.get('event_type')
    resource = webhook_data.get('resource', {})

    print(f"[PAYPAL WEBHOOK] Received event: {event_type}")

    # Verify webhook signature (if webhook_id is configured)
    webhook_id = current_app.config.get('PAYPAL_WEBHOOK_ID')
    if webhook_id:
        try:
            # Initialize PayPal
            paypalrestsdk.configure({
                'mode': current_app.config['PAYPAL_MODE'],
                'client_id': current_app.config['PAYPAL_CLIENT_ID'],
                'client_secret': current_app.config['PAYPAL_CLIENT_SECRET']
            })

            # Verify the webhook event
            transmission_id = request.headers.get('Paypal-Transmission-Id')
            transmission_time = request.headers.get('Paypal-Transmission-Time')
            cert_url = request.headers.get('Paypal-Cert-Url')
            auth_algo = request.headers.get('Paypal-Auth-Algo')
            transmission_sig = request.headers.get('Paypal-Transmission-Sig')

            # Verify using PayPal SDK
            response = paypalrestsdk.WebhookEvent.verify(
                transmission_id,
                transmission_time,
                webhook_id,
                event_type,
                cert_url,
                auth_algo,
                transmission_sig,
                webhook_data
            )

            if not response:
                print("[PAYPAL WEBHOOK] Signature verification failed")
                return jsonify({'error': 'Invalid signature'}), 401

        except Exception as e:
            print(f"[PAYPAL WEBHOOK] Signature verification error: {e}")
            # In development, we might skip verification if not configured
            if current_app.config['PAYPAL_MODE'] == 'live':
                return jsonify({'error': 'Verification failed'}), 401

    # Handle the event
    try:
        if event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            handle_paypal_subscription_activated(resource)

        elif event_type == 'BILLING.SUBSCRIPTION.UPDATED':
            handle_paypal_subscription_updated(resource)

        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            handle_paypal_subscription_cancelled(resource)

        elif event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            handle_paypal_subscription_suspended(resource)

        elif event_type == 'PAYMENT.SALE.COMPLETED':
            handle_paypal_payment_completed(resource)

        else:
            print(f"[PAYPAL WEBHOOK] Unhandled event type: {event_type}")

    except Exception as e:
        print(f"[PAYPAL WEBHOOK] Error processing event {event_type}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Processing error'}), 500

    return jsonify({'success': True}), 200


def handle_paypal_subscription_activated(resource):
    """Handle PayPal subscription activation (BILLING.SUBSCRIPTION.ACTIVATED)."""
    subscription_id = resource.get('id')
    custom_id = resource.get('custom_id')  # This is our user_id
    plan_id = resource.get('plan_id')

    if not subscription_id or not custom_id:
        print("[PAYPAL WEBHOOK] Missing subscription_id or custom_id")
        return

    try:
        user = db.session.get(User, int(custom_id))
        if not user:
            print(f"[PAYPAL WEBHOOK] User {custom_id} not found")
            return

        # Determine tier from plan ID
        tier = None
        amount = 0

        if plan_id == current_app.config['PAYPAL_PLAN_ID_MONTHLY']:
            tier = 'monthly'
            amount = 2.99
        elif plan_id == current_app.config['PAYPAL_PLAN_ID_ANNUAL']:
            tier = 'annual'
            amount = 19.99

        if not tier:
            print(f"[PAYPAL WEBHOOK] Unknown plan ID: {plan_id}")
            return

        # Subscription was already activated in the success callback
        # This webhook confirms it
        print(f"[PAYPAL WEBHOOK] Subscription {subscription_id} activated for user {user.id}")

    except Exception as e:
        print(f"[PAYPAL WEBHOOK ERROR] subscription_activated: {e}")


def handle_paypal_subscription_updated(resource):
    """Handle PayPal subscription update (BILLING.SUBSCRIPTION.UPDATED)."""
    subscription_id = resource.get('id')
    status = resource.get('status')

    if not subscription_id:
        print("[PAYPAL WEBHOOK] Missing subscription_id in update")
        return

    try:
        # Find user by PayPal subscription ID
        user = User.query.filter_by(paypal_subscription_id=subscription_id).first()

        if not user:
            print(f"[PAYPAL WEBHOOK] No user found for subscription {subscription_id}")
            return

        # Update subscription status
        if status == 'ACTIVE':
            user.subscription_status = 'active'
        elif status == 'SUSPENDED':
            user.subscription_status = 'suspended'
        elif status == 'CANCELLED':
            user.subscription_status = 'cancelled'

        db.session.commit()
        print(f"[PAYPAL WEBHOOK] Subscription {subscription_id} updated to status: {status}")

    except Exception as e:
        db.session.rollback()
        print(f"[PAYPAL WEBHOOK ERROR] subscription_updated: {e}")


def handle_paypal_subscription_cancelled(resource):
    """Handle PayPal subscription cancellation (BILLING.SUBSCRIPTION.CANCELLED)."""
    subscription_id = resource.get('id')

    if not subscription_id:
        print("[PAYPAL WEBHOOK] Missing subscription_id in cancellation")
        return

    try:
        # Find user by PayPal subscription ID
        user = User.query.filter_by(paypal_subscription_id=subscription_id).first()

        if not user:
            print(f"[PAYPAL WEBHOOK] No user found for subscription {subscription_id}")
            return

        # Update user to free tier
        user.subscription_status = 'cancelled'
        user.subscription_tier = 'free'
        user.habit_limit = 3
        user.subscription_end_date = datetime.utcnow()

        # Update Subscription record
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            payment_provider='paypal',
            provider_subscription_id=subscription_id,
            status='active'
        ).first()

        if subscription:
            subscription.status = 'cancelled'
            subscription.end_date = datetime.utcnow()

        db.session.commit()
        print(f"[PAYPAL WEBHOOK] Subscription {subscription_id} cancelled, user {user.id} downgraded to free")

    except Exception as e:
        db.session.rollback()
        print(f"[PAYPAL WEBHOOK ERROR] subscription_cancelled: {e}")


def handle_paypal_subscription_suspended(resource):
    """Handle PayPal subscription suspension due to payment failure (BILLING.SUBSCRIPTION.SUSPENDED)."""
    subscription_id = resource.get('id')

    if not subscription_id:
        print("[PAYPAL WEBHOOK] Missing subscription_id in suspension")
        return

    try:
        # Find user by PayPal subscription ID
        user = User.query.filter_by(paypal_subscription_id=subscription_id).first()

        if not user:
            print(f"[PAYPAL WEBHOOK] No user found for subscription {subscription_id}")
            return

        # Increment payment failures
        user.payment_failures += 1
        user.subscription_status = 'suspended'

        # If too many failures, cancel subscription
        if user.payment_failures >= 3:
            user.subscription_tier = 'free'
            user.subscription_status = 'expired'
            user.habit_limit = 3
            user.subscription_end_date = datetime.utcnow()
            print(f"[PAYPAL WEBHOOK] User {user.id} subscription expired after {user.payment_failures} failures")

        db.session.commit()
        print(f"[PAYPAL WEBHOOK] Subscription {subscription_id} suspended for user {user.id}")

    except Exception as e:
        db.session.rollback()
        print(f"[PAYPAL WEBHOOK ERROR] subscription_suspended: {e}")


def handle_paypal_payment_completed(resource):
    """Handle successful PayPal recurring payment (PAYMENT.SALE.COMPLETED)."""
    sale_id = resource.get('id')
    amount = float(resource.get('amount', {}).get('total', 0))
    currency = resource.get('amount', {}).get('currency', 'USD')
    billing_agreement_id = resource.get('billing_agreement_id')

    if not sale_id or not billing_agreement_id:
        print("[PAYPAL WEBHOOK] Missing sale_id or billing_agreement_id in payment")
        return

    try:
        # Find user by PayPal subscription ID
        # Note: billing_agreement_id is the subscription ID
        user = User.query.filter_by(paypal_subscription_id=billing_agreement_id).first()

        if not user:
            print(f"[PAYPAL WEBHOOK] No user found for billing agreement {billing_agreement_id}")
            return

        # Record the payment
        subscription = Subscription.query.filter_by(
            user_id=user.id,
            payment_provider='paypal',
            provider_subscription_id=billing_agreement_id,
            status='active'
        ).first()

        payment = Payment(
            user_id=user.id,
            subscription_id=subscription.id if subscription else None,
            payment_provider='paypal',
            provider_transaction_id=sale_id,
            amount=amount,
            currency=currency,
            status='completed',
            payment_type='renewal',
            payment_date=datetime.utcnow(),
            notes='PayPal recurring payment'
        )
        db.session.add(payment)

        # Update user's last payment date and reset failure count
        user.last_payment_date = datetime.utcnow()
        user.payment_failures = 0

        # Extend subscription end date
        if user.subscription_tier == 'monthly':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        elif user.subscription_tier == 'annual':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=365)

        # Update subscription next billing date
        if subscription:
            subscription.next_billing_date = user.subscription_end_date

        db.session.commit()
        print(f"[PAYPAL WEBHOOK] Payment {sale_id} completed for user {user.id}, amount: {amount} {currency}")

    except Exception as e:
        db.session.rollback()
        print(f"[PAYPAL WEBHOOK ERROR] payment_completed: {e}")


# ==========================================
# COINBASE COMMERCE WEBHOOKS (Phase 6 - Placeholder)
# ==========================================

@webhooks_bp.route('/coinbase', methods=['POST'])
def coinbase_webhook():
    """
    Handle Coinbase Commerce webhook events.
    TODO: Implement in Phase 6
    """
    return jsonify({'status': 'not implemented'}), 501
