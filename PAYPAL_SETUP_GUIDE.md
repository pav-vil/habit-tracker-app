# PayPal Payment Integration Setup Guide

**Last Updated:** December 28, 2025
**HabitFlow Payment Integration - PayPal**

This guide will walk you through setting up PayPal as an alternative payment method for your HabitFlow subscription tiers (Monthly & Annual plans).

---

## Why PayPal?

PayPal provides an alternative payment option for users who:
- Don't have or don't want to use credit/debit cards
- Prefer PayPal's buyer protection
- Already have PayPal accounts
- Are in regions where PayPal is more popular

**Note:** PayPal is best for **recurring subscriptions** (Monthly & Annual). For one-time lifetime purchases, use Stripe or Coinbase Commerce.

---

## Prerequisites

Before you begin, make sure you have:
- ✅ A PayPal Business account (or willing to upgrade from Personal)
- ✅ Verified PayPal account (bank account linked)
- ✅ Access to PayPal Developer Dashboard
- ✅ Your HabitFlow app deployed and accessible

---

## Step 1: Create/Upgrade to PayPal Business Account

### 1.1 If You Don't Have a PayPal Account:
1. Go to https://www.paypal.com/us/business
2. Click **"Sign Up"**
3. Choose **"Business Account"**
4. Fill in your business information:
   - Business name: `HabitFlow` (or your business name)
   - Business type: Individual/Sole Proprietor or LLC
   - Business category: Software/Technology
   - Email and password
5. Complete verification (link bank account)

### 1.2 If You Have a Personal Account:
1. Log in to PayPal
2. Go to **Settings** > **Account Settings**
3. Click **"Upgrade to a Business Account"**
4. Follow the prompts to upgrade

---

## Step 2: Access PayPal Developer Dashboard

1. Go to https://developer.paypal.com/
2. Log in with your PayPal account
3. Click **"Dashboard"** in the top-right corner
4. You'll see two environments:
   - **Sandbox** (for testing)
   - **Live** (for production)

---

## Step 3: Create REST API App (Sandbox First)

### 3.1 Create Sandbox App (for testing)

1. In the Developer Dashboard, select **"Sandbox"**
2. Go to **"Apps & Credentials"**
3. Click **"Create App"**
4. Fill in:
   - **App Name:** `HabitFlow Sandbox`
   - **App Type:** Merchant
5. Click **"Create App"**
6. You'll see your credentials:
   - **Client ID** (starts with `A...`)
   - **Secret** (click "Show" to reveal)

**Save these credentials! You'll need them for testing.**

### 3.2 Configure Sandbox App

1. Under **"App Settings"**, scroll to **"Features"**
2. Enable:
   - ✅ **Accept payments**
   - ✅ **Subscriptions**
3. Click **"Save"**

---

## Step 4: Create Subscription Plans (Sandbox)

PayPal requires you to create subscription plans before users can subscribe.

### 4.1 Create Monthly Plan ($2.99/month)

1. In the PayPal Developer Dashboard, go to **"Subscriptions"** (in sandbox mode)
2. Click **"Create Plan"**
3. Fill in:
   - **Plan Name:** `HabitFlow Monthly`
   - **Plan ID:** (auto-generated, save this!)
   - **Billing cycle:**
     - Frequency: Monthly
     - Price: $2.99 USD
     - Total cycles: Unlimited (recurring)
   - **Setup fee:** $0.00
   - **Trial period:** None (or configure if you want)
4. Click **"Create Plan"**
5. **Copy the Plan ID** (starts with `P-...`) - you'll need this!

### 4.2 Create Annual Plan ($19.99/year)

1. Click **"Create Plan"** again
2. Fill in:
   - **Plan Name:** `HabitFlow Annual`
   - **Plan ID:** (auto-generated, save this!)
   - **Billing cycle:**
     - Frequency: Yearly
     - Price: $19.99 USD
     - Total cycles: Unlimited (recurring)
   - **Setup fee:** $0.00
   - **Trial period:** None
3. Click **"Create Plan"**
4. **Copy the Plan ID** (starts with `P-...`)

**Note:** PayPal doesn't support one-time "lifetime" subscriptions like Stripe does. Use Stripe or Coinbase for lifetime tier.

---

## Step 5: Set Up Webhooks (Sandbox)

Webhooks notify your app when subscription events occur.

1. In Developer Dashboard, go to **"Webhooks"** (under sandbox)
2. Click **"Add Webhook"**
3. Fill in:
   - **Webhook URL:** `https://your-app.onrender.com/webhooks/paypal`
     (Replace with your actual Render URL)
   - **Event types:** Select these events:
     - ✅ `BILLING.SUBSCRIPTION.ACTIVATED`
     - ✅ `BILLING.SUBSCRIPTION.CANCELLED`
     - ✅ `BILLING.SUBSCRIPTION.SUSPENDED`
     - ✅ `BILLING.SUBSCRIPTION.UPDATED`
     - ✅ `PAYMENT.SALE.COMPLETED`
     - ✅ `PAYMENT.SALE.REFUNDED`
4. Click **"Save"**
5. **Copy the Webhook ID** - you'll need this for signature verification!

---

## Step 6: Test in Sandbox Mode

### 6.1 Update Your .env File (Development)

```bash
# PayPal Configuration (Sandbox)
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=<your_sandbox_client_id>
PAYPAL_CLIENT_SECRET=<your_sandbox_client_secret>
PAYPAL_WEBHOOK_ID=<your_sandbox_webhook_id>

# PayPal Plan IDs
PAYPAL_PLAN_ID_MONTHLY=P-xxxxxxxxxxxxx
PAYPAL_PLAN_ID_ANNUAL=P-xxxxxxxxxxxxx
```

### 6.2 Test Subscription Flow

1. Run your app locally: `python app.py`
2. Go to the pricing page
3. Select PayPal payment method
4. Use PayPal Sandbox test accounts:
   - **Buyer account:** Go to Developer Dashboard > Sandbox > Accounts
   - Use the email/password of a sandbox Personal account
5. Complete the subscription
6. Verify webhook is received (check your app logs)

**Sandbox Test Cards:**
- PayPal provides test accounts automatically
- No credit card needed for sandbox testing

---

## Step 7: Go Live with Production

Once testing is complete, switch to live mode.

### 7.1 Create Live REST API App

1. In Developer Dashboard, switch to **"Live"** mode
2. Go to **"Apps & Credentials"**
3. Click **"Create App"**
4. Fill in:
   - **App Name:** `HabitFlow Production`
   - **App Type:** Merchant
5. Click **"Create App"**
6. **Save your LIVE credentials:**
   - Client ID
   - Secret

### 7.2 Create Live Subscription Plans

1. Go to your **Live PayPal account** (not Developer Dashboard)
2. Navigate to **Products & Services** > **Subscriptions**
3. Create the same two plans:
   - Monthly: $2.99/month
   - Annual: $19.99/year
4. **Copy the Live Plan IDs**

### 7.3 Set Up Live Webhooks

1. Go to https://www.paypal.com/businessmanage/account/settings
2. Navigate to **Account Settings** > **Notifications** > **Webhooks**
3. Click **"Add Webhook"**
4. Fill in:
   - **Webhook URL:** `https://your-app.onrender.com/webhooks/paypal`
   - Select the same events as sandbox
5. **Copy the Live Webhook ID**

---

## Step 8: Configure Production Environment Variables

In Render.com dashboard, add these environment variables:

```bash
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=<your_live_client_id>
PAYPAL_CLIENT_SECRET=<your_live_client_secret>
PAYPAL_WEBHOOK_ID=<your_live_webhook_id>
PAYPAL_PLAN_ID_MONTHLY=P-xxxxxxxxxxxxx
PAYPAL_PLAN_ID_ANNUAL=P-xxxxxxxxxxxxx
```

**Important:** Make sure `PAYPAL_MODE=live` in production!

---

## Step 9: Test Live Payments

1. Make a real $2.99 payment (test with your own account)
2. Verify subscription is created in your database
3. Check that webhook is received
4. Verify user's subscription_tier is updated
5. Cancel the test subscription
6. Verify cancellation webhook works

**Refund the test payment** after verification.

---

## Webhook Events Reference

Your app handles these PayPal webhook events:

| Event | Description | What Happens |
|-------|-------------|--------------|
| `BILLING.SUBSCRIPTION.ACTIVATED` | User subscribes | Creates subscription, activates premium |
| `BILLING.SUBSCRIPTION.CANCELLED` | User cancels | Marks subscription as cancelled |
| `BILLING.SUBSCRIPTION.SUSPENDED` | Payment failed | Suspends subscription |
| `BILLING.SUBSCRIPTION.UPDATED` | Plan changed | Updates subscription details |
| `PAYMENT.SALE.COMPLETED` | Recurring payment succeeded | Extends subscription |
| `PAYMENT.SALE.REFUNDED` | Payment refunded | Processes refund, may cancel subscription |

---

## Pricing Summary

| Plan | Price | PayPal Plan ID Variable |
|------|-------|-------------------------|
| Monthly | $2.99/month | `PAYPAL_PLAN_ID_MONTHLY` |
| Annual | $19.99/year | `PAYPAL_PLAN_ID_ANNUAL` |
| Lifetime | N/A | Use Stripe or Coinbase |

**Note:** PayPal charges 2.9% + $0.30 per transaction.

---

## Troubleshooting

### Webhook Not Receiving Events
1. Verify webhook URL is correct in PayPal dashboard
2. Check webhook ID matches your .env file
3. Ensure your app is deployed and accessible
4. Check Render logs for webhook delivery

### Signature Verification Failed
1. Verify `PAYPAL_WEBHOOK_ID` is correct
2. Make sure webhook ID matches live or sandbox mode
3. Check that webhook secret is not exposed

### Subscription Not Activating
1. Verify plan IDs are correct
2. Check that plans are active in PayPal dashboard
3. Verify user completed the checkout flow
4. Check app logs for errors

### Can't Find Subscription Plans
1. Make sure you're in the correct mode (sandbox vs live)
2. Plans must be created in the PayPal web dashboard, not Developer Dashboard
3. For live plans, use the main PayPal account settings

---

## Security Best Practices

✅ **Do:**
- Use webhook signature verification (already implemented)
- Store credentials in environment variables, never in code
- Use HTTPS for webhook URLs
- Test thoroughly in sandbox before going live
- Monitor webhook delivery and failures

❌ **Don't:**
- Commit PayPal credentials to git
- Use sandbox credentials in production
- Skip webhook signature verification
- Trust client-side data without server verification

---

## Support Resources

- **PayPal Developer Docs:** https://developer.paypal.com/docs/
- **Subscription Plans:** https://developer.paypal.com/docs/subscriptions/
- **Webhooks:** https://developer.paypal.com/docs/api-basics/notifications/webhooks/
- **PayPal Support:** https://www.paypal.com/us/smarthelp/contact-us

---

## Quick Reference: Environment Variables

```bash
# Required for PayPal Integration
PAYPAL_MODE=sandbox  # or 'live' for production
PAYPAL_CLIENT_ID=<from_paypal_app>
PAYPAL_CLIENT_SECRET=<from_paypal_app>
PAYPAL_WEBHOOK_ID=<from_paypal_webhooks>
PAYPAL_PLAN_ID_MONTHLY=P-xxxxxxxxxxxxx
PAYPAL_PLAN_ID_ANNUAL=P-xxxxxxxxxxxxx
```

---

## Summary Checklist

**Sandbox Testing:**
- [ ] Create PayPal Business account
- [ ] Create sandbox REST API app
- [ ] Get sandbox credentials (Client ID, Secret)
- [ ] Create sandbox subscription plans (Monthly, Annual)
- [ ] Set up sandbox webhooks
- [ ] Configure .env with sandbox credentials
- [ ] Test subscription flow
- [ ] Verify webhooks are received

**Production Deployment:**
- [ ] Create live REST API app
- [ ] Get live credentials
- [ ] Create live subscription plans
- [ ] Set up live webhooks
- [ ] Configure Render environment variables
- [ ] Test live payment
- [ ] Verify subscription activation
- [ ] Test cancellation flow

---

**You're all set!** PayPal is now integrated as an alternative payment method for your HabitFlow subscriptions. Users can choose between Stripe (cards) and PayPal based on their preference. 🎉

For Bitcoin/cryptocurrency payments, see `BITCOIN_SETUP_GUIDE.md`.
