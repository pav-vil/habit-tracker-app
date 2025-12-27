"""
Webhook handlers for payment providers
Currently supports: Stripe
"""
from flask import Blueprint, request, jsonify, current_app
import stripe
from stripe_handler import (
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_payment_failed
)

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.
    Must be registered in Stripe Dashboard.
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        print("[WEBHOOK] Error: STRIPE_WEBHOOK_SECRET not configured")
        return jsonify({'error': 'Webhook not configured'}), 500

    try:
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
