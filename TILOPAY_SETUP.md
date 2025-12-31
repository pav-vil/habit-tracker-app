# TiloPay Integration Setup Guide

## Overview

TiloPay is a Costa Rican payment gateway that supports:
- **Credit/Debit Cards**: Visa, Mastercard, American Express
- **Local Payments**: SINPE Móvil (Costa Rica), cash payments at physical locations
- **Recurring Subscriptions**: Monthly and annual billing
- **Multi-currency**: CRC and USD support

## Why TiloPay for Costa Rica?

- **Local Payment Methods**: SINPE Móvil handles 40% of Costa Rica's retail transactions
- **Bank Settlement**: Direct integration with Costa Rican banks
- **Higher Conversion**: Familiar payment methods reduce cart abandonment
- **Better UX**: Optimized for Central American market

## Prerequisites

1. **TiloPay Account**: Register at [https://start.tilopay.com](https://start.tilopay.com)
2. **Business Verification**: TiloPay requires business registration and bank approval
3. **Official Documentation**: Download the SDK guide at [https://app.tilopay.com/sdk/documentation.pdf](https://app.tilopay.com/sdk/documentation.pdf)

## Setup Steps

### 1. Get TiloPay API Credentials

1. Log into your TiloPay portal at [https://admin.tilopay.com](https://admin.tilopay.com)
2. Navigate to **Settings** → **API Credentials**
3. Generate or copy:
   - **API Key** (Integration Key)
   - **API User** (Username)
   - **API Password** (Password)
4. Generate a **Webhook Secret** for secure webhook verification

### 2. Configure Environment Variables

Add these to your `.env` file:

```bash
# TiloPay Configuration
TILOPAY_MODE=test  # Use 'test' for development, 'production' for live
TILOPAY_API_KEY=your-api-key-here
TILOPAY_API_USER=your-api-username-here
TILOPAY_API_PASSWORD=your-api-password-here
TILOPAY_WEBHOOK_SECRET=your-webhook-secret-here
```

**For Testing** (Test credentials are already configured in config.py):
- Test Key: `6609-5850-8330-8034-3464`
- Test User: `lSrT45`
- Test Password: `Zlb8H9`

### 3. Verify API Endpoints

The integration uses these assumed API endpoints (verify from official SDK docs):
- **Create Payment**: `POST {API_URL}/orders/create`
- **Cancel Subscription**: `POST {API_URL}/subscriptions/{id}/cancel`

**IMPORTANT**: Check the official TiloPay SDK documentation (https://app.tilopay.com/sdk/documentation.pdf) for the exact:
- API endpoint paths
- Request/response field names
- Authentication header format
- Error codes and handling

### 4. Update tilopay_handler.py

Once you have the official documentation:

1. Review the `create_payment()` function in `tilopay_handler.py`
2. Update the request payload structure to match TiloPay's specification
3. Verify endpoint URLs
4. Adjust response field mappings
5. Test with TiloPay's test environment

Key areas marked with `NOTE:` comments need verification:
```python
# NOTE: These fields are based on common payment gateway patterns
# Verify exact field names and structure from official TiloPay SDK docs
```

### 5. Configure Webhooks in TiloPay Portal

1. Log into TiloPay portal
2. Navigate to **Settings** → **Webhooks**
3. Add webhook URL: `https://your-domain.com/webhooks/tilopay`
4. Enable events:
   - Payment completed/approved/success
   - Payment failed/rejected/error
   - Payment cancelled
   - Subscription renewed
   - Subscription cancelled
5. Save the webhook secret to your environment variables

### 6. Test Integration

#### Test Mode:
1. Set `TILOPAY_MODE=test` in `.env`
2. Visit pricing page: `http://localhost:5000/pricing`
3. Select CRC currency
4. Click "Subscribe with TiloPay"
5. Use TiloPay test cards (get from TiloPay docs)

#### Verify:
- Payment creation redirects to TiloPay checkout
- Successful payment redirects back with correct parameters
- Webhook processes payment and activates subscription
- Database records created (Subscription, Payment, PaymentTransaction)

### 7. Go Live

1. Complete business verification with TiloPay
2. Get production API credentials
3. Update environment variables:
   ```bash
   TILOPAY_MODE=production
   TILOPAY_API_KEY=production-key
   TILOPAY_API_USER=production-user
   TILOPAY_API_PASSWORD=production-password
   ```
4. Update webhook URL to production domain
5. Test thoroughly with real Costa Rican payment methods

## API Implementation Notes

### Payment Flow

```
User clicks "Subscribe with TiloPay"
    ↓
App calls create_payment() in tilopay_handler.py
    ↓
Makes POST request to TiloPay API /orders/create
    ↓
Redirects user to TiloPay hosted checkout
    ↓
User completes payment
    ↓
TiloPay redirects to /payments/tilopay-success
    ↓
TiloPay sends webhook to /webhooks/tilopay
    ↓
Webhook handler activates subscription
    ↓
User sees success message
```

### Webhook Security

Webhooks are secured with HMAC-SHA256 signature verification:

```python
expected_signature = hmac.new(
    webhook_secret.encode('utf-8'),
    payload,
    hashlib.sha256
).hexdigest()
```

Verify the signature header name with TiloPay docs (assumed: `X-TiloPay-Signature` or `X-Signature`).

### Currency Handling

- **CRC (Costa Rica Colones)**: No decimal places, format as ₡1,500
- **USD**: 2 decimal places, format as $2.99
- Pricing configured in `config.py`:
  ```python
  'CRC': {
      'monthly': 1500,    # ₡1,500
      'annual': 10000,    # ₡10,000
      'lifetime': 30000   # ₡30,000
  }
  ```

## Troubleshooting

### Common Issues

**Issue**: Payment creation fails with authentication error
- **Solution**: Verify API credentials are correct
- Check that `TILOPAY_MODE` matches credentials (test vs production)

**Issue**: Webhook not receiving notifications
- **Solution**: Verify webhook URL is publicly accessible
- Check webhook secret matches TiloPay portal configuration
- Review TiloPay logs in their dashboard

**Issue**: Subscription not activating after payment
- **Solution**: Check webhook handler logs (`[TILOPAY WEBHOOK]` entries)
- Verify signature verification is passing
- Ensure user_id and tier are in webhook metadata

**Issue**: Currency mismatch errors
- **Solution**: Verify currency parameter is passed correctly
- Check pricing configuration in config.py

### Logs

Enable detailed logging by checking console output:
```python
print(f"[TILOPAY] ...")  # General logs
print(f"[TILOPAY ERROR] ...")  # Error logs
print(f"[TILOPAY WEBHOOK] ...")  # Webhook logs
```

## Files Modified

- `config.py` - TiloPay configuration and credentials
- `tilopay_handler.py` - NEW: TiloPay API integration
- `payments.py` - Added TiloPay checkout and success routes
- `webhooks.py` - Added TiloPay webhook handler
- `templates/pricing.html` - Added TiloPay payment options for CRC
- `requirements.txt` - Added requests library

## Next Steps

1. **Contact TiloPay Support**: Email sac@tilopay.com
   - Request API documentation access
   - Ask about test environment details
   - Clarify webhook event types

2. **Complete API Integration**:
   - Review official SDK documentation
   - Update endpoint URLs and field mappings
   - Test all payment scenarios

3. **Add SINPE Móvil Support**:
   - Verify TiloPay's SINPE Móvil integration method
   - Update UI to highlight SINPE as local payment option
   - Test with Costa Rican users

4. **Monitor Performance**:
   - Track conversion rates (TiloPay vs Stripe)
   - Monitor payment success rates
   - Collect user feedback on payment experience

## Support

- **TiloPay Support**: sac@tilopay.com
- **Documentation**: https://app.tilopay.com/sdk/documentation.pdf
- **Portal**: https://admin.tilopay.com

## References

- [TiloPay Official Site](https://start.tilopay.com/en/)
- [TiloPay WooCommerce Integration](https://woocommerce.com/document/tilopay-gateway/)
- [Costa Rica Payment Methods Guide](https://tecnosoluciones.com/what-are-the-online-payment-methods-in-costa-rica-for-virtual-stores-and-e-commerce/?lang=en)
