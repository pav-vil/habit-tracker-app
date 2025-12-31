"""
Subscription Blueprint for HabitFlow
Handles pricing page, checkout, billing history, and subscription management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, PaymentTransaction, SubscriptionHistory, Payment, Subscription
from payments import create_paypal_subscription, cancel_paypal_subscription

subscription_bp = Blueprint('subscription', __name__)


@subscription_bp.route('/pricing')
def pricing():
    """Display pricing page with subscription options."""
    # Get currency from query parameter or session, default to USD
    currency = request.args.get('currency', current_app.config.get('DEFAULT_CURRENCY', 'USD')).upper()

    # Validate currency
    if currency not in current_app.config['SUPPORTED_CURRENCIES']:
        currency = 'USD'

    # Get pricing for selected currency
    pricing_data = current_app.config['PRICING'][currency]
    currency_symbol = current_app.config['CURRENCY_SYMBOLS'][currency]

    # Format prices based on currency
    if currency == 'CRC':
        # CRC uses no decimals and comma separator
        monthly_price = f'{currency_symbol}{pricing_data["monthly"]:,.0f}'
        annual_price = f'{currency_symbol}{pricing_data["annual"]:,.0f}'
        lifetime_price = f'{currency_symbol}{pricing_data["lifetime"]:,.0f}'
    else:
        # USD uses 2 decimals
        monthly_price = f'{currency_symbol}{pricing_data["monthly"]:.2f}'
        annual_price = f'{currency_symbol}{pricing_data["annual"]:.2f}'
        lifetime_price = f'{currency_symbol}{pricing_data["lifetime"]:.2f}'

    plans = {
        'monthly': {
            'name': 'Monthly',
            'price': monthly_price,
            'price_numeric': pricing_data['monthly'],
            'currency': currency,
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
            'price': annual_price,
            'price_numeric': pricing_data['annual'],
            'currency': currency,
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
            'price': lifetime_price,
            'price_numeric': pricing_data['lifetime'],
            'currency': currency,
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

    return render_template(
        'pricing.html',
        plans=plans,
        current_currency=currency,
        supported_currencies=current_app.config['SUPPORTED_CURRENCIES']
    )


@subscription_bp.route('/checkout/<plan_type>')
@login_required
def checkout(plan_type):
    """Create payment subscription and redirect to payment provider."""
    if plan_type not in ['monthly', 'annual', 'lifetime']:
        flash('Invalid subscription plan selected.', 'danger')
        return redirect(url_for('subscription.pricing'))

    # Check if user is already premium
    if current_user.is_premium_active() and current_user.subscription_status != 'free':
        flash('You already have an active subscription. Please cancel first to change plans.', 'info')
        return redirect(url_for('subscription.manage'))

    # Get currency from query parameter, default to USD
    currency = request.args.get('currency', 'USD').upper()

    # Validate currency
    if currency not in current_app.config['SUPPORTED_CURRENCIES']:
        currency = 'USD'

    # For lifetime tier: Show message to contact support or use crypto
    # (Coinbase Commerce will be configured later)
    if plan_type == 'lifetime':
        flash('Lifetime tier is currently available via Bitcoin/Crypto payments only. Coinbase Commerce setup coming soon! For now, please use monthly or annual plans.', 'info')
        return redirect(url_for('subscription.pricing'))

    # Create PayPal subscription (monthly or annual only) with currency support
    return create_paypal_subscription(current_user, plan_type, currency)


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
    """Cancel user's PayPal subscription."""
    if not current_user.is_premium_active():
        flash('You do not have an active subscription to cancel.', 'warning')
        return redirect(url_for('subscription.manage'))

    if current_user.subscription_tier == 'lifetime':
        flash('Lifetime subscriptions cannot be cancelled.', 'info')
        return redirect(url_for('subscription.manage'))

    # Cancel the PayPal subscription
    if current_user.paypal_subscription_id:
        if cancel_paypal_subscription(current_user.paypal_subscription_id):
            # Update user status
            current_user.subscription_status = 'cancelled'
            db.session.commit()

            flash(
                'Your subscription has been cancelled. You will retain access until the end of your billing period.',
                'success'
            )
        else:
            flash('Unable to cancel subscription. Please contact support.', 'danger')
    else:
        flash('No active PayPal subscription found. Please contact support.', 'danger')

    return redirect(url_for('subscription.manage'))
