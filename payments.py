# payments.py - Payment Processing Blueprint for HabitFlow
# Handles Stripe, PayPal, and Coinbase Commerce payment flows

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, User, Subscription, Payment
from datetime import datetime, timedelta
import stripe

# Create blueprint for payment routes
payments_bp = Blueprint('payments', __name__, url_prefix='/payments')


# ==========================================
# STRIPE PAYMENT PROCESSING (Phase 3)
# ==========================================

@payments_bp.route('/checkout')
@login_required
def checkout():
    """
    Initiate payment checkout flow.
    Redirects to appropriate payment provider based on 'provider' parameter.

    Query Parameters:
        tier (str): Subscription tier - 'monthly', 'annual', or 'lifetime'
        provider (str): Payment provider - 'stripe', 'paypal', or 'coinbase'
        currency (str): Currency code - 'USD' or 'CRC' (default: 'USD')

    Returns:
        Redirect to payment provider checkout or error page
    """
    tier = request.args.get('tier')
    provider = request.args.get('provider', 'stripe')
    currency = request.args.get('currency', 'USD').upper()

    # Validate tier parameter
    valid_tiers = ['monthly', 'annual', 'lifetime']
    if tier not in valid_tiers:
        flash('Invalid subscription tier selected.', 'danger')
        return redirect(url_for('profile.subscription'))

    # Validate currency
    if currency not in current_app.config['SUPPORTED_CURRENCIES']:
        currency = 'USD'

    # Check if user already has this tier or higher
    if current_user.subscription_tier == tier:
        flash(f'You already have the {tier} subscription!', 'info')
        return redirect(url_for('profile.subscription'))

    # Route to appropriate payment provider
    if provider == 'stripe':
        return create_stripe_checkout_session(current_user, tier, currency)
    elif provider == 'paypal':
        return create_paypal_subscription(current_user, tier, currency)
    elif provider == 'coinbase':
        return create_coinbase_charge(current_user, tier)  # Coinbase always uses USD
    else:
        flash('Invalid payment provider selected.', 'danger')
        return redirect(url_for('profile.subscription'))


def create_stripe_checkout_session(user, tier, currency='USD'):
    """
    Create a Stripe Checkout Session for the specified tier.

    Args:
        user (User): The user object making the purchase
        tier (str): Subscription tier - 'monthly', 'annual', or 'lifetime'
        currency (str): Currency code - 'USD' or 'CRC'

    Returns:
        Redirect to Stripe Checkout or error page
    """
    try:
        # Initialize Stripe with secret key
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Validate currency
        if currency not in current_app.config['SUPPORTED_CURRENCIES']:
            currency = 'USD'

        # Get pricing for the selected currency
        pricing_data = current_app.config['PRICING'][currency]
        amount = pricing_data.get(tier)

        if not amount:
            flash(f'Pricing not configured for {tier} tier in {currency}.', 'danger')
            return redirect(url_for('profile.subscription'))

        # Get the appropriate price ID from configuration
        price_mapping = {
            'monthly': current_app.config['STRIPE_PRICE_ID_MONTHLY'],
            'annual': current_app.config['STRIPE_PRICE_ID_ANNUAL'],
            'lifetime': current_app.config['STRIPE_PRICE_ID_LIFETIME']
        }

        price_id = price_mapping.get(tier)

        if not price_id:
            flash(f'Stripe Price ID not configured for {tier} tier. Please contact support.', 'danger')
            return redirect(url_for('profile.subscription'))

        # Create or retrieve Stripe customer
        if not user.stripe_customer_id:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    'user_id': user.id,
                    'subscription_tier': tier
                }
            )

            # Save customer ID to database
            user.stripe_customer_id = customer.id
            db.session.commit()
        else:
            # Use existing customer ID
            customer_id = user.stripe_customer_id

        # Determine checkout mode based on tier
        # Lifetime = one-time payment, Monthly/Annual = subscription
        if tier == 'lifetime':
            checkout_mode = 'payment'  # One-time payment
        else:
            checkout_mode = 'subscription'  # Recurring subscription

        # Convert amount to cents for Stripe (Stripe uses smallest currency unit)
        # For USD: multiply by 100 (dollars to cents)
        # For CRC: CRC doesn't use decimal places, so no conversion needed
        if currency == 'CRC':
            stripe_amount = int(amount)  # CRC colones (no decimals)
        else:
            stripe_amount = int(amount * 100)  # USD cents

        # Prepare recurring interval for subscriptions
        recurring_interval = None
        if tier == 'monthly':
            recurring_interval = 'month'
        elif tier == 'annual':
            recurring_interval = 'year'

        # Build line items with dynamic pricing
        line_item = {
            'price_data': {
                'currency': currency.lower(),
                'product_data': {
                    'name': f'HabitFlow {tier.title()} Subscription',
                    'description': f'Unlimited habits with {tier} billing'
                },
                'unit_amount': stripe_amount
            },
            'quantity': 1
        }

        # Add recurring interval for subscriptions
        if recurring_interval:
            line_item['price_data']['recurring'] = {
                'interval': recurring_interval
            }

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            mode=checkout_mode,
            line_items=[line_item],
            success_url=current_app.config['APP_URL'] + url_for('payments.success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=current_app.config['APP_URL'] + url_for('payments.cancel'),
            metadata={
                'user_id': user.id,
                'tier': tier,
                'currency': currency
            }
        )

        # Redirect to Stripe Checkout
        return redirect(checkout_session.url, code=303)

    except stripe.error.StripeError as e:
        # Handle Stripe-specific errors
        flash(f'Payment error: {str(e)}', 'danger')
        print(f"[STRIPE ERROR] {str(e)}")
        return redirect(url_for('profile.subscription'))
    except Exception as e:
        # Handle general errors
        flash('An unexpected error occurred. Please try again or contact support.', 'danger')
        print(f"[PAYMENT ERROR] {str(e)}")
        return redirect(url_for('profile.subscription'))


@payments_bp.route('/success')
@login_required
def success():
    """
    Payment success page.
    Displays after successful Stripe checkout.
    Retrieves session from Stripe and updates user subscription.

    Query Parameters:
        session_id (str): Stripe Checkout Session ID

    Returns:
        Rendered success template
    """
    session_id = request.args.get('session_id')

    if not session_id:
        flash('Invalid payment session.', 'danger')
        return redirect(url_for('profile.subscription'))

    try:
        # Initialize Stripe
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Retrieve the checkout session from Stripe
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        # Verify the session belongs to the current user
        if str(checkout_session.metadata.get('user_id')) != str(current_user.id):
            flash('Invalid payment session.', 'danger')
            return redirect(url_for('profile.subscription'))

        # Extract subscription details
        tier = checkout_session.metadata.get('tier')
        payment_status = checkout_session.payment_status

        # Only process if payment was successful
        if payment_status == 'paid':
            # Update user subscription
            current_user.subscription_tier = tier
            current_user.subscription_status = 'active'
            current_user.subscription_start_date = datetime.utcnow()

            # Set subscription end date based on tier
            if tier == 'monthly':
                current_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            elif tier == 'annual':
                current_user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
            elif tier == 'lifetime':
                current_user.subscription_end_date = None  # No end date for lifetime

            # Save Stripe subscription ID (if applicable)
            if checkout_session.subscription:
                current_user.stripe_subscription_id = checkout_session.subscription

            current_user.last_payment_date = datetime.utcnow()
            current_user.payment_failures = 0  # Reset failure count

            # Create Subscription record
            subscription = Subscription(
                user_id=current_user.id,
                tier=tier,
                status='active',
                payment_provider='stripe',
                provider_subscription_id=checkout_session.subscription if checkout_session.subscription else checkout_session.id,
                start_date=datetime.utcnow(),
                end_date=current_user.subscription_end_date,
                next_billing_date=current_user.subscription_end_date if tier in ['monthly', 'annual'] else None,
                amount_paid=checkout_session.amount_total / 100.0,  # Convert from cents
                currency=checkout_session.currency.upper()
            )
            db.session.add(subscription)

            # Create Payment record
            payment = Payment(
                user_id=current_user.id,
                subscription_id=subscription.id,
                payment_provider='stripe',
                provider_transaction_id=checkout_session.payment_intent if checkout_session.payment_intent else checkout_session.id,
                amount=checkout_session.amount_total / 100.0,  # Convert from cents
                currency=checkout_session.currency.upper(),
                status='completed',
                payment_type='subscription' if tier in ['monthly', 'annual'] else 'lifetime',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)

            # Commit all changes
            db.session.commit()

            flash(f'Payment successful! You now have the {tier} subscription with unlimited habits!', 'success')

            return render_template('payments/success.html',
                                   tier=tier,
                                   amount=checkout_session.amount_total / 100.0,
                                   currency=checkout_session.currency.upper())
        else:
            flash('Payment not completed. Please try again.', 'warning')
            return redirect(url_for('profile.subscription'))

    except stripe.error.StripeError as e:
        flash(f'Error verifying payment: {str(e)}', 'danger')
        print(f"[STRIPE ERROR] {str(e)}")
        return redirect(url_for('profile.subscription'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing your payment. Please contact support.', 'danger')
        print(f"[PAYMENT SUCCESS ERROR] {str(e)}")
        return redirect(url_for('profile.subscription'))


@payments_bp.route('/cancel')
def cancel():
    """
    Payment cancelled page.
    Displays when user cancels checkout.

    Returns:
        Rendered cancel template
    """
    return render_template('payments/cancel.html')


def cancel_stripe_subscription(subscription_id):
    """
    Cancel a Stripe subscription.
    Called when user cancels their recurring subscription.

    Args:
        subscription_id (str): Stripe subscription ID

    Returns:
        bool: True if cancellation successful, False otherwise
    """
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Cancel the subscription at period end (don't cut off immediately)
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )

        return True

    except stripe.error.StripeError as e:
        print(f"[STRIPE CANCEL ERROR] {str(e)}")
        return False
    except Exception as e:
        print(f"[CANCEL ERROR] {str(e)}")
        return False


# ==========================================
# PAYPAL PAYMENT PROCESSING (Phase 5)
# ==========================================

import paypalrestsdk


def init_paypal():
    """Initialize PayPal SDK with credentials from config."""
    paypalrestsdk.configure({
        'mode': current_app.config['PAYPAL_MODE'],  # 'sandbox' or 'live'
        'client_id': current_app.config['PAYPAL_CLIENT_ID'],
        'client_secret': current_app.config['PAYPAL_CLIENT_SECRET']
    })


def create_paypal_subscription(user, tier, currency='USD'):
    """
    Create a PayPal subscription for the specified tier.

    Args:
        user (User): The user object making the purchase
        tier (str): Subscription tier - 'monthly' or 'annual'
        currency (str): Currency code - 'USD' or 'CRC'

    Returns:
        Redirect to PayPal approval URL or error page
    """
    try:
        # Initialize PayPal
        init_paypal()

        # Validate currency
        if currency not in current_app.config['SUPPORTED_CURRENCIES']:
            currency = 'USD'

        # Get pricing for the selected currency
        pricing_data = current_app.config['PRICING'][currency]
        amount = pricing_data.get(tier)

        if not amount:
            flash(f'Pricing not configured for {tier} tier in {currency}.', 'danger')
            return redirect(url_for('profile.subscription'))

        # Get the appropriate plan ID from configuration
        # Note: You'll need to create separate PayPal plans for each currency
        plan_mapping = {
            'monthly': current_app.config['PAYPAL_PLAN_ID_MONTHLY'],
            'annual': current_app.config['PAYPAL_PLAN_ID_ANNUAL']
        }

        plan_id = plan_mapping.get(tier)

        if not plan_id:
            flash(f'PayPal Plan ID not configured for {tier} tier. Please contact support.', 'danger')
            return redirect(url_for('profile.subscription'))

        # PayPal doesn't support lifetime subscriptions - redirect to Stripe
        if tier == 'lifetime':
            flash('Please use Stripe or Coinbase for lifetime purchases.', 'info')
            return redirect(url_for('profile.subscription'))

        # Create PayPal subscription
        subscription = paypalrestsdk.Subscription({
            'plan_id': plan_id,
            'subscriber': {
                'name': {
                    'given_name': user.email.split('@')[0],  # Use email prefix as first name
                    'surname': 'User'
                },
                'email_address': user.email
            },
            'application_context': {
                'brand_name': 'HabitFlow',
                'locale': 'en-US',
                'shipping_preference': 'NO_SHIPPING',
                'user_action': 'SUBSCRIBE_NOW',
                'return_url': current_app.config['APP_URL'] + url_for('payments.paypal_success'),
                'cancel_url': current_app.config['APP_URL'] + url_for('payments.cancel')
            },
            'custom_id': str(user.id)  # Track user ID for webhook processing
        })

        if subscription.create():
            # Get approval URL
            for link in subscription.links:
                if link.rel == 'approve':
                    approval_url = link.href
                    # Store subscription ID temporarily for verification
                    # (In production, consider using a more secure method)
                    return redirect(approval_url, code=303)

            flash('Error creating PayPal subscription. Please try again.', 'danger')
            return redirect(url_for('profile.subscription'))

        else:
            error_msg = subscription.error.get('message', 'Unknown error') if hasattr(subscription, 'error') else 'Unknown error'
            flash(f'PayPal error: {error_msg}', 'danger')
            print(f"[PAYPAL ERROR] {subscription.error}")
            return redirect(url_for('profile.subscription'))

    except Exception as e:
        flash('An unexpected error occurred with PayPal. Please try again or contact support.', 'danger')
        print(f"[PAYPAL ERROR] {str(e)}")
        return redirect(url_for('profile.subscription'))


@payments_bp.route('/paypal-success')
@login_required
def paypal_success():
    """
    PayPal subscription approval callback.
    User is redirected here after approving PayPal subscription.

    Query Parameters:
        subscription_id (str): PayPal Subscription ID
        ba_token (str): Billing agreement token

    Returns:
        Redirect to success page or profile
    """
    subscription_id = request.args.get('subscription_id')
    ba_token = request.args.get('ba_token')

    if not subscription_id:
        flash('Invalid PayPal subscription.', 'danger')
        return redirect(url_for('profile.subscription'))

    try:
        # Initialize PayPal
        init_paypal()

        # Retrieve subscription details from PayPal
        paypal_subscription = paypalrestsdk.Subscription.find(subscription_id)

        if not paypal_subscription:
            flash('Could not verify PayPal subscription.', 'danger')
            return redirect(url_for('profile.subscription'))

        # Verify this subscription belongs to current user
        if paypal_subscription.custom_id != str(current_user.id):
            flash('Invalid PayPal subscription.', 'danger')
            return redirect(url_for('profile.subscription'))

        # Determine tier from plan ID
        plan_id = paypal_subscription.plan_id
        tier = None
        amount = 0

        if plan_id == current_app.config['PAYPAL_PLAN_ID_MONTHLY']:
            tier = 'monthly'
            amount = 2.99
        elif plan_id == current_app.config['PAYPAL_PLAN_ID_ANNUAL']:
            tier = 'annual'
            amount = 19.99

        if not tier:
            flash('Unknown PayPal plan.', 'danger')
            return redirect(url_for('profile.subscription'))

        # Update user subscription
        current_user.subscription_tier = tier
        current_user.subscription_status = 'active'
        current_user.subscription_start_date = datetime.utcnow()
        current_user.paypal_subscription_id = subscription_id

        # Set subscription end date
        if tier == 'monthly':
            current_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        elif tier == 'annual':
            current_user.subscription_end_date = datetime.utcnow() + timedelta(days=365)

        current_user.last_payment_date = datetime.utcnow()
        current_user.payment_failures = 0

        # Create Subscription record
        subscription_record = Subscription(
            user_id=current_user.id,
            tier=tier,
            status='active',
            payment_provider='paypal',
            provider_subscription_id=subscription_id,
            start_date=datetime.utcnow(),
            end_date=current_user.subscription_end_date,
            next_billing_date=current_user.subscription_end_date,
            amount_paid=amount,
            currency='USD'
        )
        db.session.add(subscription_record)

        # Create Payment record
        payment_record = Payment(
            user_id=current_user.id,
            subscription_id=subscription_record.id,
            payment_provider='paypal',
            provider_transaction_id=subscription_id,  # Use subscription ID as transaction ID
            amount=amount,
            currency='USD',
            status='completed',
            payment_type='subscription',
            payment_date=datetime.utcnow(),
            notes=f'PayPal {tier} subscription activated'
        )
        db.session.add(payment_record)

        db.session.commit()

        flash(f'Payment successful! You now have the {tier} subscription with unlimited habits!', 'success')

        return render_template('payments/success.html',
                               tier=tier,
                               amount=amount,
                               currency='USD',
                               provider='PayPal')

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing your PayPal subscription. Please contact support.', 'danger')
        print(f"[PAYPAL SUCCESS ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('profile.subscription'))


def cancel_paypal_subscription(subscription_id):
    """
    Cancel a PayPal subscription.
    Called when user cancels their recurring subscription.

    Args:
        subscription_id (str): PayPal subscription ID

    Returns:
        bool: True if cancellation successful, False otherwise
    """
    try:
        init_paypal()

        # Find the subscription
        subscription = paypalrestsdk.Subscription.find(subscription_id)

        if not subscription:
            print(f"[PAYPAL] Subscription {subscription_id} not found")
            return False

        # Cancel the subscription
        if subscription.cancel({'reason': 'User requested cancellation'}):
            print(f"[PAYPAL] Subscription {subscription_id} cancelled successfully")
            return True
        else:
            print(f"[PAYPAL] Failed to cancel subscription: {subscription.error}")
            return False

    except Exception as e:
        print(f"[PAYPAL CANCEL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ==========================================
# COINBASE COMMERCE (Phase 6)
# ==========================================

from coinbase_commerce.client import Client
from coinbase_commerce.error import SignatureVerificationError, WebhookInvalidPayload


def init_coinbase():
    """Initialize Coinbase Commerce client with API key from config."""
    Client.api_key = current_app.config['COINBASE_COMMERCE_API_KEY']


def create_coinbase_charge(user, tier):
    """
    Create a Coinbase Commerce charge for Bitcoin/crypto payment.
    Only supports lifetime tier (one-time payment).

    Args:
        user (User): The user object making the purchase
        tier (str): Subscription tier - must be 'lifetime'

    Returns:
        Redirect to Coinbase Commerce hosted checkout or error page
    """
    try:
        # Coinbase Commerce only supports one-time payments (perfect for lifetime tier)
        if tier != 'lifetime':
            flash('Bitcoin payments are only available for lifetime tier. Please use Stripe or PayPal for subscriptions.', 'info')
            return redirect(url_for('profile.subscription'))

        # Initialize Coinbase Commerce
        init_coinbase()

        # Get price from configuration
        price = current_app.config['COINBASE_LIFETIME_PRICE']

        # Create charge
        charge = Client().charge.create(
            name='HabitFlow Lifetime Access',
            description='Unlimited habits forever - one-time payment',
            pricing_type='fixed_price',
            local_price={
                'amount': str(price),
                'currency': 'USD'
            },
            metadata={
                'user_id': user.id,
                'user_email': user.email,
                'tier': 'lifetime'
            },
            redirect_url=current_app.config['APP_URL'] + url_for('payments.coinbase_success'),
            cancel_url=current_app.config['APP_URL'] + url_for('payments.cancel')
        )

        # Store charge code temporarily for verification
        # In production, consider storing this in a session or temporary database table
        # For now, we'll rely on webhook verification

        # Redirect to Coinbase Commerce hosted checkout page
        return redirect(charge.hosted_url, code=303)

    except Exception as e:
        flash('An unexpected error occurred with Coinbase Commerce. Please try again or contact support.', 'danger')
        print(f"[COINBASE ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('profile.subscription'))


@payments_bp.route('/coinbase-success')
@login_required
def coinbase_success():
    """
    Coinbase Commerce payment redirect page.
    User is redirected here after completing crypto payment.

    Note: Actual subscription activation happens via webhook (webhooks.py)
    This page just shows a pending confirmation message.

    Returns:
        Rendered success template with pending status
    """
    # The webhook will handle the actual subscription activation
    # This page just confirms the user completed the checkout flow

    flash('Bitcoin payment submitted! Your lifetime subscription will be activated once the payment is confirmed on the blockchain (usually 10-30 minutes).', 'info')

    return render_template('payments/coinbase_pending.html',
                           tier='lifetime',
                           amount=current_app.config['COINBASE_LIFETIME_PRICE'],
                           currency='USD')
