"""
TiloPay Payment Handler for HabitFlow
Handles TiloPay payment processing for Costa Rica market
Supports: Credit/Debit cards, SINPE Móvil, recurring subscriptions

Official Documentation: https://app.tilopay.com/sdk/documentation.pdf
Contact: sac@tilopay.com for API access
"""

import requests
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from flask import current_app, url_for, flash, redirect
from models import db, User, Subscription, Payment, PaymentTransaction


class TiloPayHandler:
    """Handler for TiloPay API integration"""

    def __init__(self):
        """Initialize TiloPay handler with credentials from config"""
        self.mode = current_app.config.get('TILOPAY_MODE', 'test')

        if self.mode == 'test':
            self.api_key = current_app.config['TILOPAY_TEST_API_KEY']
            self.api_user = current_app.config['TILOPAY_TEST_API_USER']
            self.api_password = current_app.config['TILOPAY_TEST_API_PASSWORD']
            self.api_url = current_app.config['TILOPAY_API_URL_TEST']
        else:
            self.api_key = current_app.config['TILOPAY_API_KEY']
            self.api_user = current_app.config['TILOPAY_API_USER']
            self.api_password = current_app.config['TILOPAY_API_PASSWORD']
            self.api_url = current_app.config['TILOPAY_API_URL_PRODUCTION']

        self.webhook_secret = current_app.config.get('TILOPAY_WEBHOOK_SECRET')

    def _get_headers(self):
        """
        Generate authentication headers for TiloPay API requests.

        Returns:
            dict: HTTP headers with authentication
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-API-User': self.api_user,
            'X-API-Password': self.api_password
        }

    def create_payment(self, user, tier, currency='CRC'):
        """
        Create a TiloPay payment order.

        Args:
            user (User): The user making the purchase
            tier (str): Subscription tier - 'monthly', 'annual', or 'lifetime'
            currency (str): Currency code - 'CRC' or 'USD'

        Returns:
            dict: Payment order response with redirect URL

        Note: Complete implementation requires TiloPay SDK documentation
        Official docs: https://app.tilopay.com/sdk/documentation.pdf
        """
        try:
            # Get pricing
            pricing_data = current_app.config['PRICING'].get(currency, current_app.config['PRICING']['USD'])
            amount = pricing_data.get(tier)

            if not amount:
                raise ValueError(f'Pricing not configured for {tier} tier in {currency}')

            # Determine if this is a subscription or one-time payment
            is_subscription = tier in ['monthly', 'annual']

            # Build payment order data
            # NOTE: These fields are based on common payment gateway patterns
            # Verify exact field names and structure from official TiloPay SDK docs
            order_data = {
                'key': self.api_key,
                'user': self.api_user,
                'amount': str(amount),
                'currency': currency,
                'description': f'HabitFlow {tier.title()} Subscription',
                'reference': f'user_{user.id}_tier_{tier}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                'orderid': f'HF{user.id}{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',

                # Customer information
                'customer': {
                    'email': user.email,
                    'name': user.email.split('@')[0],
                },

                # Redirect URLs
                'redirect_success': current_app.config['APP_URL'] + url_for('payments.tilopay_success'),
                'redirect_error': current_app.config['APP_URL'] + url_for('payments.cancel'),
                'callback_url': current_app.config['APP_URL'] + url_for('webhooks.tilopay_webhook'),

                # Additional metadata
                'metadata': {
                    'user_id': user.id,
                    'tier': tier,
                    'is_subscription': is_subscription
                }
            }

            # Add subscription parameters if applicable
            if is_subscription:
                order_data['subscription'] = True
                order_data['subscription_frequency'] = 'monthly' if tier == 'monthly' else 'yearly'

            # Make API request to create payment order
            # NOTE: Endpoint path may differ - verify from official docs
            endpoint = f'{self.api_url}/orders/create'

            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=order_data,
                timeout=30
            )

            response.raise_for_status()
            payment_response = response.json()

            # Extract payment URL from response
            # NOTE: Response structure may differ - verify from official docs
            payment_url = payment_response.get('payment_url') or payment_response.get('redirect_url')

            if not payment_url:
                raise ValueError('Payment URL not found in TiloPay response')

            return {
                'success': True,
                'payment_url': payment_url,
                'order_id': payment_response.get('order_id'),
                'transaction_id': payment_response.get('transaction_id')
            }

        except requests.exceptions.RequestException as e:
            print(f"[TILOPAY ERROR] API request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            print(f"[TILOPAY ERROR] Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def verify_webhook_signature(self, payload, signature):
        """
        Verify TiloPay webhook signature.

        Args:
            payload (str or bytes): Webhook payload
            signature (str): Signature from webhook headers

        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            print("[TILOPAY WARNING] Webhook secret not configured")
            return False

        try:
            # Convert payload to bytes if it's a string
            if isinstance(payload, str):
                payload = payload.encode('utf-8')

            # Generate HMAC signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            print(f"[TILOPAY ERROR] Signature verification failed: {str(e)}")
            return False

    def process_payment_success(self, user, tier, transaction_data, currency='CRC'):
        """
        Process successful payment and activate subscription.

        Args:
            user (User): The user who made the payment
            tier (str): Subscription tier
            transaction_data (dict): Transaction data from TiloPay
            currency (str): Currency code

        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            # Get amount
            pricing_data = current_app.config['PRICING'].get(currency, current_app.config['PRICING']['USD'])
            amount = pricing_data.get(tier)

            # Update user subscription
            user.subscription_tier = tier
            user.subscription_status = 'active'
            user.subscription_start_date = datetime.utcnow()
            user.last_payment_date = datetime.utcnow()
            user.payment_failures = 0

            # Set subscription end date based on tier
            if tier == 'monthly':
                user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            elif tier == 'annual':
                user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
            elif tier == 'lifetime':
                user.subscription_end_date = None  # No end date

            # Create Subscription record
            subscription = Subscription(
                user_id=user.id,
                tier=tier,
                status='active',
                payment_provider='tilopay',
                provider_subscription_id=transaction_data.get('subscription_id') or transaction_data.get('order_id'),
                start_date=datetime.utcnow(),
                end_date=user.subscription_end_date,
                next_billing_date=user.subscription_end_date if tier in ['monthly', 'annual'] else None,
                amount_paid=amount,
                currency=currency
            )
            db.session.add(subscription)

            # Create Payment record
            payment = Payment(
                user_id=user.id,
                subscription_id=subscription.id,
                payment_provider='tilopay',
                provider_transaction_id=transaction_data.get('transaction_id') or transaction_data.get('order_id'),
                amount=amount,
                currency=currency,
                status='completed',
                payment_type='subscription' if tier in ['monthly', 'annual'] else 'lifetime',
                payment_date=datetime.utcnow(),
                notes=f'TiloPay {tier} subscription - {currency}'
            )
            db.session.add(payment)

            # Create PaymentTransaction record
            payment_transaction = PaymentTransaction(
                user_id=user.id,
                provider='tilopay',
                provider_transaction_id=transaction_data.get('transaction_id') or transaction_data.get('order_id'),
                amount=amount,
                currency=currency,
                status='completed',
                subscription_type=tier,
                transaction_date=datetime.utcnow(),
                payment_metadata=json.dumps(transaction_data)
            )
            db.session.add(payment_transaction)

            # Commit all changes
            db.session.commit()

            print(f"[TILOPAY] Successfully processed payment for user {user.id}, tier {tier}")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"[TILOPAY ERROR] Failed to process payment success: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def cancel_subscription(self, subscription_id):
        """
        Cancel a TiloPay subscription.

        Args:
            subscription_id (str): TiloPay subscription ID

        Returns:
            bool: True if cancellation successful, False otherwise

        Note: Complete implementation requires TiloPay SDK documentation
        """
        try:
            # Build cancellation request
            cancel_data = {
                'key': self.api_key,
                'user': self.api_user,
                'subscription_id': subscription_id
            }

            # Make API request to cancel subscription
            # NOTE: Endpoint path may differ - verify from official docs
            endpoint = f'{self.api_url}/subscriptions/{subscription_id}/cancel'

            response = requests.post(
                endpoint,
                headers=self._get_headers(),
                json=cancel_data,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            print(f"[TILOPAY] Subscription {subscription_id} cancelled successfully")
            return True

        except requests.exceptions.RequestException as e:
            print(f"[TILOPAY ERROR] Failed to cancel subscription: {str(e)}")
            return False
        except Exception as e:
            print(f"[TILOPAY ERROR] Unexpected error during cancellation: {str(e)}")
            return False


# Helper functions for Flask routes

def create_tilopay_payment(user, tier, currency='CRC'):
    """
    Create TiloPay payment and redirect to checkout.

    Args:
        user (User): The user making the purchase
        tier (str): Subscription tier
        currency (str): Currency code

    Returns:
        Flask redirect to TiloPay checkout or error page
    """
    try:
        handler = TiloPayHandler()
        result = handler.create_payment(user, tier, currency)

        if result.get('success'):
            # Redirect to TiloPay hosted checkout page
            return redirect(result['payment_url'], code=303)
        else:
            flash(f'TiloPay payment error: {result.get("error")}', 'danger')
            return redirect(url_for('subscription.pricing'))

    except Exception as e:
        flash('An error occurred with TiloPay. Please try again or contact support.', 'danger')
        print(f"[TILOPAY ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('subscription.pricing'))


def handle_tilopay_webhook(webhook_data, signature):
    """
    Process TiloPay webhook notification.

    Args:
        webhook_data (dict): Webhook payload
        signature (str): Webhook signature

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        handler = TiloPayHandler()

        # Verify webhook signature (if secret is configured)
        if handler.webhook_secret:
            if not handler.verify_webhook_signature(json.dumps(webhook_data), signature):
                print("[TILOPAY WEBHOOK] Invalid signature")
                return False, 'Invalid signature'

        # Extract event type and data
        event_type = webhook_data.get('event') or webhook_data.get('status')
        user_id = webhook_data.get('metadata', {}).get('user_id')
        tier = webhook_data.get('metadata', {}).get('tier')

        if not user_id or not tier:
            print("[TILOPAY WEBHOOK] Missing user_id or tier in metadata")
            return False, 'Missing required data'

        # Get user
        user = User.query.get(user_id)
        if not user:
            print(f"[TILOPAY WEBHOOK] User {user_id} not found")
            return False, 'User not found'

        # Process based on event type
        if event_type in ['completed', 'approved', 'success']:
            # Payment successful
            currency = webhook_data.get('currency', 'CRC')
            success = handler.process_payment_success(user, tier, webhook_data, currency)
            return success, 'Payment processed' if success else 'Processing failed'

        elif event_type in ['failed', 'rejected', 'error']:
            # Payment failed
            print(f"[TILOPAY WEBHOOK] Payment failed for user {user_id}")
            # TODO: Handle failed payment (send email, update user status, etc.)
            return True, 'Payment failure noted'

        elif event_type in ['cancelled', 'canceled']:
            # Payment cancelled by user
            print(f"[TILOPAY WEBHOOK] Payment cancelled by user {user_id}")
            return True, 'Cancellation noted'

        else:
            print(f"[TILOPAY WEBHOOK] Unknown event type: {event_type}")
            return True, f'Unknown event: {event_type}'

    except Exception as e:
        print(f"[TILOPAY WEBHOOK ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False, str(e)
