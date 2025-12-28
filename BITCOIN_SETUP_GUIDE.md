# Bitcoin/Cryptocurrency Payment Integration Setup Guide

**Last Updated:** December 28, 2025
**HabitFlow Payment Integration - Coinbase Commerce**

This guide will walk you through setting up Bitcoin and cryptocurrency payments using Coinbase Commerce for your HabitFlow **Lifetime Tier** ($59.99 one-time payment).

---

## Why Coinbase Commerce?

Coinbase Commerce is ideal for cryptocurrency payments because:
- Accepts Bitcoin, Ethereum, Litecoin, Bitcoin Cash, USDC, and Dogecoin
- **No transaction fees** - you receive 100% of the payment
- Simple integration with REST API
- Direct deposit to your crypto wallet
- Perfect for **one-time payments** (Lifetime tier)
- No KYC required to start accepting payments

**Note:** Coinbase Commerce is best for **one-time lifetime purchases** ($59.99). For recurring subscriptions, use Stripe or PayPal.

---

## Prerequisites

Before you begin, make sure you have:
- ✅ A Coinbase account (or willing to create one)
- ✅ Access to Coinbase Commerce dashboard
- ✅ A cryptocurrency wallet (or use Coinbase wallet)
- ✅ Your HabitFlow app deployed and accessible

---

## Step 1: Create Coinbase Commerce Account

### 1.1 Sign Up for Coinbase Commerce

1. Go to https://commerce.coinbase.com/
2. Click **"Get Started"**
3. You have two options:
   - **Option A:** Sign in with existing Coinbase account (recommended)
   - **Option B:** Create new Commerce-only account
4. Complete the signup process
5. Verify your email address

### 1.2 Business Information (Optional)

1. Log in to Coinbase Commerce
2. Go to **Settings** > **Business Information**
3. Fill in (optional but recommended):
   - Business name: `HabitFlow`
   - Business website: `https://your-app.onrender.com`
   - Business description: Habit tracking application
4. Click **"Save"**

**Note:** Unlike Stripe/PayPal, Coinbase Commerce doesn't require extensive business verification to start accepting payments.

---

## Step 2: Get Your API Key

### 2.1 Create API Key

1. In Coinbase Commerce dashboard, go to **Settings**
2. Click on **"API Keys"** tab
3. Click **"Create an API Key"**
4. You'll see your API key (starts with a long string)
5. **IMPORTANT:** Copy this key immediately - it won't be shown again!
6. Store it securely (you'll add it to environment variables)

**Security Warning:** Treat this API key like a password. Never commit it to git or share it publicly.

### 2.2 API Key Format

Your API key will look like this:
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

## Step 3: Set Up Webhook (for Payment Notifications)

Webhooks notify your app when a payment is received.

### 3.1 Create Webhook Endpoint

1. In Coinbase Commerce dashboard, go to **Settings**
2. Click **"Webhook subscriptions"**
3. Click **"Add an endpoint"**
4. Fill in:
   - **Endpoint URL:** `https://your-app.onrender.com/webhooks/coinbase`
     (Replace with your actual Render URL)
5. Click **"Save"**
6. You'll receive a **Webhook Shared Secret** - copy it!

**Webhook Secret Format:**
```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### 3.2 Webhook Events

Your app will receive these events:
- `charge:created` - Payment initiated
- `charge:confirmed` - Payment confirmed on blockchain
- `charge:failed` - Payment failed or expired
- `charge:pending` - Payment detected, waiting for confirmations

**Note:** Bitcoin transactions require blockchain confirmations (usually 1-6 confirmations depending on amount).

---

## Step 4: Configure Pricing

### 4.1 Lifetime Tier Pricing

HabitFlow Lifetime tier costs **$59.99 USD** (one-time payment).

Coinbase Commerce automatically converts this to cryptocurrency at the current exchange rate when the user checks out.

**Supported Cryptocurrencies:**
- Bitcoin (BTC)
- Ethereum (ETH)
- Litecoin (LTC)
- Bitcoin Cash (BCH)
- USD Coin (USDC)
- Dogecoin (DOGE)

Users can pay with any of these - you receive the equivalent of $59.99 USD.

### 4.2 No Plan Creation Needed

Unlike PayPal subscriptions, Coinbase Commerce doesn't require pre-creating payment plans. You simply create a "charge" for $59.99 when the user clicks "Pay with Bitcoin."

---

## Step 5: Test in Development Mode

### 5.1 Update Your .env File (Development)

```bash
# Coinbase Commerce Configuration
COINBASE_API_KEY=your_api_key_here
COINBASE_WEBHOOK_SECRET=your_webhook_secret_here

# Lifetime Tier Pricing
LIFETIME_TIER_PRICE=59.99
```

### 5.2 Test Payment Flow

1. Run your app locally: `python app.py`
2. Go to the pricing page
3. Click **"Pay with Bitcoin"** on Lifetime tier
4. You'll be redirected to Coinbase Commerce checkout
5. **Testing Options:**
   - **Option A:** Make a real small crypto payment ($0.01 test)
   - **Option B:** Use Coinbase Commerce test mode (if available)
6. Complete the payment
7. Verify webhook is received (check your app logs)
8. Verify user's subscription_tier is updated to "lifetime"

**Important:** Coinbase Commerce doesn't have a sandbox mode like Stripe. You can test with very small amounts (e.g., $0.01) or use the preview mode.

---

## Step 6: Set Up Crypto Wallet for Receiving Payments

### 6.1 Choose Withdrawal Method

You have two options for receiving your crypto payments:

**Option A: Coinbase Wallet (Easiest)**
1. In Coinbase Commerce, go to **Settings** > **Crypto Withdrawals**
2. Select **"Coinbase wallet"**
3. Link your Coinbase account
4. Payments automatically transfer to your Coinbase wallet
5. You can then convert to USD or hold as crypto

**Option B: External Wallet (Advanced)**
1. In Coinbase Commerce, go to **Settings** > **Crypto Withdrawals**
2. Select **"External wallet"**
3. Enter your wallet addresses for each cryptocurrency:
   - Bitcoin address (starts with `1`, `3`, or `bc1`)
   - Ethereum address (starts with `0x`)
   - Etc.
4. Verify wallet addresses carefully!
5. Payments will be sent directly to your wallets

**Recommendation:** Use Coinbase wallet initially for simplicity. You can always transfer to external wallets later.

---

## Step 7: Configure Production Environment

### 7.1 Add Environment Variables to Render

In your Render.com dashboard, add these environment variables:

```bash
COINBASE_API_KEY=<your_live_api_key>
COINBASE_WEBHOOK_SECRET=<your_webhook_secret>
LIFETIME_TIER_PRICE=59.99
```

### 7.2 Verify Webhook URL

1. Make sure your Render app is deployed and accessible
2. Webhook URL should be: `https://your-app.onrender.com/webhooks/coinbase`
3. Test the webhook by making a payment
4. Check Render logs to verify webhook delivery

---

## Step 8: Go Live and Test Real Payments

### 8.1 Make a Test Payment

1. Make a real $59.99 payment (you can refund yourself later)
2. Choose a cryptocurrency (Bitcoin recommended for testing)
3. Complete the payment using your own wallet
4. Wait for blockchain confirmations (1-6 confirmations)
5. Verify subscription is created in your database
6. Check that webhook is received
7. Verify user's subscription_tier is updated to "lifetime"

### 8.2 Verify User Experience

Test the complete flow:
1. User clicks "Pay with Bitcoin" on Lifetime tier
2. Redirected to Coinbase Commerce checkout
3. User selects cryptocurrency (BTC, ETH, etc.)
4. Payment instructions displayed with QR code
5. User sends payment from their wallet
6. Coinbase detects payment and shows "Pending"
7. After confirmations, payment shows "Completed"
8. User redirected back to HabitFlow
9. User sees "Lifetime Access" badge

---

## Step 9: Handle Edge Cases

### 9.1 Underpayment

If a user sends less than the required amount:
- Coinbase will mark the charge as "underpaid"
- Your webhook receives `charge:failed` event
- User does NOT get lifetime access
- You can manually refund or ask user to pay the difference

### 9.2 Overpayment

If a user sends more than required:
- Coinbase will mark the charge as "overpaid" but still successful
- User gets lifetime access
- Excess amount goes to your wallet (bonus!)

### 9.3 Payment Expiration

Coinbase charges expire after **1 hour** if not paid:
- User must create a new charge if expired
- Old charge is automatically marked as "failed"

### 9.4 Blockchain Confirmations

Different confirmation times by cryptocurrency:
- **Bitcoin:** ~10 minutes (1 confirmation), up to 60 min (6 confirmations)
- **Ethereum:** ~5 minutes (12 confirmations)
- **Litecoin:** ~2.5 minutes (6 confirmations)
- **USDC:** ~5 minutes (instant for small amounts)

**Important:** Don't grant access until charge is `confirmed` or `completed`.

---

## Webhook Events Reference

Your app handles these Coinbase Commerce webhook events:

| Event | Description | What Happens |
|-------|-------------|--------------|
| `charge:created` | User initiated payment | Create pending payment record |
| `charge:pending` | Payment detected on blockchain | Update payment status to "pending" |
| `charge:confirmed` | Payment confirmed (enough confirmations) | Activate lifetime subscription |
| `charge:failed` | Payment expired or failed | Mark payment as failed, notify user |
| `charge:delayed` | Payment needs more confirmations | Wait for more confirmations |

**Important:** Only grant access on `charge:confirmed`, NOT on `charge:pending`.

---

## Pricing Summary

| Plan | Price | Payment Method | Provider |
|------|-------|----------------|----------|
| Monthly | $2.99/month | Card / PayPal | Stripe / PayPal |
| Annual | $19.99/year | Card / PayPal | Stripe / PayPal |
| **Lifetime** | **$59.99** (one-time) | **Bitcoin/Crypto** | **Coinbase Commerce** |

**Coinbase Commerce Fees:** $0 (100% of payment goes to you!)

---

## Troubleshooting

### Webhook Not Receiving Events

1. Verify webhook URL is correct in Coinbase Commerce dashboard
2. Check webhook secret matches your .env file
3. Ensure your app is deployed and accessible via HTTPS
4. Check Render logs for webhook delivery
5. Test webhook using Coinbase Commerce "Send test" button

### Signature Verification Failed

1. Verify `COINBASE_WEBHOOK_SECRET` is correct
2. Make sure you're using the raw request body for verification
3. Check that webhook secret hasn't been regenerated
4. Verify your HMAC SHA256 implementation

### Payment Not Confirming

1. Check blockchain explorer to verify transaction
2. Wait for required confirmations (can take 10-60 minutes for Bitcoin)
3. Verify user sent correct amount
4. Check if payment expired (1-hour timeout)

### User Not Getting Lifetime Access

1. Verify webhook was received (check logs)
2. Confirm charge status is `confirmed` not just `pending`
3. Check database for payment record
4. Verify user's subscription_tier was updated
5. Look for errors in webhook handler

### Underpayment Issues

1. User sent less crypto than required
2. Price changed during checkout (crypto volatility)
3. User must create new charge with updated price
4. Consider adding 2-3% buffer for price fluctuations

---

## Security Best Practices

✅ **Do:**
- Use webhook signature verification (HMAC SHA256)
- Store API keys in environment variables, never in code
- Use HTTPS for webhook URLs
- Wait for `charge:confirmed` before granting access
- Log all webhook events for debugging
- Verify payment amounts match your pricing

❌ **Don't:**
- Commit Coinbase API keys to git
- Grant access on `charge:pending` (wait for confirmations)
- Skip webhook signature verification
- Trust client-side data without server verification
- Use HTTP for webhook URLs (must be HTTPS)

---

## Advanced: Handling Cryptocurrency Volatility

Bitcoin prices can fluctuate during checkout. To handle this:

### Option 1: Accept Price Fluctuations
- Coinbase locks the price for 1 hour during checkout
- User pays the BTC amount shown at checkout
- You receive the USD equivalent at that locked rate

### Option 2: Add Price Buffer
```python
# Add 2% buffer to account for volatility
LIFETIME_TIER_PRICE = 61.19  # $59.99 + 2%
```

### Option 3: Convert to Stablecoin
- In Coinbase Commerce settings, auto-convert payments to USDC
- USDC is pegged to $1 USD (no volatility)
- User can still pay with Bitcoin, but you receive USDC

**Recommendation:** Use Option 1 (default) unless you're worried about high volatility periods.

---

## Tax and Legal Considerations

### Tax Implications
- Cryptocurrency payments are taxable income
- Report at USD value when received
- Consult a tax professional for crypto tax reporting
- Keep records of all transactions

### Legal Compliance
- Cryptocurrency regulations vary by country
- Most countries treat it as property/asset
- No special licenses needed for accepting payments
- Consult local laws if operating internationally

**Disclaimer:** This is not tax or legal advice. Consult professionals for your specific situation.

---

## Support Resources

- **Coinbase Commerce Docs:** https://commerce.coinbase.com/docs/
- **API Reference:** https://commerce.coinbase.com/docs/api/
- **Webhooks Guide:** https://commerce.coinbase.com/docs/api/#webhooks
- **Coinbase Support:** https://help.coinbase.com/

---

## Quick Reference: Environment Variables

```bash
# Required for Coinbase Commerce Integration
COINBASE_API_KEY=<from_coinbase_commerce>
COINBASE_WEBHOOK_SECRET=<from_webhook_settings>
LIFETIME_TIER_PRICE=59.99
```

---

## Summary Checklist

**Initial Setup:**
- [ ] Create Coinbase Commerce account
- [ ] Get API key from Settings > API Keys
- [ ] Set up webhook endpoint
- [ ] Get webhook shared secret
- [ ] Configure .env with API credentials
- [ ] Choose withdrawal method (Coinbase wallet or external)

**Testing:**
- [ ] Test payment flow with small amount
- [ ] Verify webhook is received
- [ ] Confirm user gets lifetime access
- [ ] Check payment appears in Coinbase Commerce dashboard
- [ ] Verify blockchain confirmation process

**Production Deployment:**
- [ ] Add API credentials to Render environment variables
- [ ] Verify webhook URL is correct (HTTPS)
- [ ] Test live payment ($59.99)
- [ ] Verify subscription activation
- [ ] Test payment confirmation flow
- [ ] Monitor for any errors in logs

---

## Comparison: Why Bitcoin for Lifetime Tier?

| Feature | Stripe/PayPal | Coinbase Commerce |
|---------|---------------|-------------------|
| **Best For** | Recurring subscriptions | One-time payments |
| **Transaction Fee** | 2.9% + $0.30 (~$2.04 on $59.99) | **$0 (FREE!)** |
| **Your Revenue** | $57.95 | **$59.99** |
| **Payment Methods** | Credit/debit cards, PayPal | Bitcoin, Ethereum, 6+ cryptos |
| **Chargebacks** | Yes (risky) | **No (irreversible)** |
| **Settlement Time** | 2-7 days | Instant to wallet |
| **Recurring Billing** | ✅ Yes | ❌ No |

**Conclusion:** Use Coinbase Commerce for Lifetime tier to save on fees and eliminate chargebacks. Use Stripe/PayPal for Monthly/Annual subscriptions.

---

## Example User Flow

1. **User lands on pricing page**
   - Sees three tiers: Monthly ($2.99), Annual ($19.99), Lifetime ($59.99)
   - Clicks "Pay with Bitcoin" on Lifetime tier

2. **Redirected to Coinbase Commerce**
   - Charge created for $59.99 USD
   - User selects cryptocurrency (e.g., Bitcoin)
   - Shown Bitcoin amount (e.g., 0.0013 BTC at current rate)
   - QR code displayed for mobile payment

3. **User sends payment**
   - Scans QR code with crypto wallet
   - Sends exact Bitcoin amount shown
   - Coinbase detects payment immediately

4. **Payment confirmation**
   - Coinbase shows "Pending" while waiting for confirmations
   - After 1-6 confirmations (~10-60 min), status → "Completed"
   - User redirected back to HabitFlow

5. **Webhook notification**
   - Your app receives `charge:confirmed` webhook
   - Creates payment record in database
   - Updates user's subscription_tier to "lifetime"
   - Sends confirmation email

6. **User enjoys lifetime access**
   - User sees "Lifetime Access" badge
   - Can create unlimited habits
   - Access forever, no recurring payments

---

**You're all set!** Bitcoin/cryptocurrency payments via Coinbase Commerce are now integrated for your HabitFlow Lifetime tier. Users can choose between credit cards (Stripe), PayPal, or Bitcoin based on their preference. 🎉

For credit card and PayPal setup, see:
- `PAYPAL_SETUP_GUIDE.md` - PayPal subscriptions (Monthly/Annual)
- Stripe is already configured in your `PRODUCTION_DEPLOYMENT.md`
