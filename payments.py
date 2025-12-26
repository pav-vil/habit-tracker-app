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

    Returns:
        Redirect to payment provider checkout or error page
    """
    tier = request.args.get('tier')
    provider = request.args.get('provider', 'stripe')

    # Validate tier parameter
    valid_tiers = ['monthly', 'annual', 'lifetime']
    if tier not in valid_tiers:
        flash('Invalid subscription tier selected.', 'danger')
        return redirect(url_for('profile.subscription'))

    # Check if user already has this tier or higher
    if current_user.subscription_tier == tier:
        flash(f'You already have the {tier} subscription!', 'info')
        return redirect(url_for('profile.subscription'))

    # Route to appropriate payment provider
    if provider == 'stripe':
        return create_stripe_checkout_session(current_user, tier)
    elif provider == 'paypal':
        flash('PayPal integration coming in Phase 5!', 'info')
        return redirect(url_for('profile.subscription'))
    elif provider == 'coinbase':
        flash('Bitcoin integration coming in Phase 6!', 'info')
        return redirect(url_for('profile.subscription'))
    else:
        flash('Invalid payment provider selected.', 'danger')
        return redirect(url_for('profile.subscription'))


def create_stripe_checkout_session(user, tier):
    """
    Create a Stripe Checkout Session for the specified tier.

    Args:
        user (User): The user object making the purchase
        tier (str): Subscription tier - 'monthly', 'annual', or 'lifetime'

    Returns:
        Redirect to Stripe Checkout or error page
    """
    try:
        # Initialize Stripe with secret key
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

        # Get the appropriate price ID from configuration
        price_mapping = {
            'monthly': current_app.config['STRIPE_MONTHLY_PRICE_ID'],
            'annual': current_app.config['STRIPE_ANNUAL_PRICE_ID'],
            'lifetime': current_app.config['STRIPE_LIFETIME_PRICE_ID']
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

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            mode=checkout_mode,
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            success_url=current_app.config['APP_URL'] + url_for('payments.success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=current_app.config['APP_URL'] + url_for('payments.cancel'),
            metadata={
                'user_id': user.id,
                'tier': tier
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
# TODO: Implement PayPal integration in Phase 5


# ==========================================
# COINBASE COMMERCE (Phase 6)
# ==========================================
# TODO: Implement Coinbase Commerce integration in Phase 6
