# HabitFlow Profile & Payment Infrastructure - Implementation Progress

**Last Updated:** December 26, 2024
**Current Phase:** Phase 3 - Stripe Integration
**Overall Progress:** 20% (2 of 10 phases complete)

---

## Quick Summary

This document tracks the implementation of the complete profile management and multi-payment subscription system for HabitFlow. Use this to resume work from any computer.

### Business Model
- **Free Tier:** 3 habits maximum
- **Monthly:** $2.99/month (unlimited habits)
- **Annual:** $19.99/year (67% savings - **BEST VALUE**)
- **Lifetime:** $59.99 one-time (no recurring payments)

### Payment Methods
- **Stripe** (Credit/Debit cards) - Primary payment method
- **PayPal** - Alternative recurring payments
- **Coinbase Commerce** (Bitcoin) - Crypto option for lifetime tier

---

## Phase Completion Status

### ✅ Phase 1: Profile Page Foundation (COMPLETE)
**Status:** Completed December 26, 2024
**Commit:** `034cad4` - Add Profile Management & Payment Infrastructure (Phase 1 & 2)

**What Was Built:**
- ✅ `profile.py` - Profile blueprint with 7 routes
- ✅ `templates/profile/view.html` - Profile overview
- ✅ `templates/profile/edit.html` - Edit email/password
- ✅ `templates/profile/settings.html` - Timezone, dark mode, newsletter settings
- ✅ `templates/profile/subscription.html` - Subscription management (placeholder)
- ✅ `templates/profile/billing.html` - Payment history (placeholder)
- ✅ `templates/profile/delete_account.html` - Account deletion with 30-day grace
- ✅ `templates/profile/about.html` - About page (moved from habits section)
- ✅ `forms.py` - Added 4 new forms (EditEmailForm, EditPasswordForm, SettingsForm, DeleteAccountForm)
- ✅ `templates/base.html` - Added Profile link to desktop & mobile navigation
- ✅ Navigation updated to include Profile section

**Routes Available:**
- `GET /profile` - View profile overview
- `GET /profile/edit` - Edit email/password form
- `POST /profile/edit` - Update email/password
- `GET /profile/settings` - Settings page
- `POST /profile/settings` - Update settings
- `GET /profile/subscription` - Subscription management
- `GET /profile/billing` - Billing history
- `GET /profile/delete` - Delete account confirmation
- `POST /profile/delete` - Schedule account deletion
- `GET /profile/about` - About HabitFlow

**Testing Completed:**
- ✅ Email change validation (uniqueness check)
- ✅ Password strength validation
- ✅ Settings updates (timezone, dark mode, newsletter)
- ✅ Account soft deletion with 30-day grace period
- ✅ Mobile responsiveness on iPhone 13
- ✅ All forms working with CSRF protection

---

### ✅ Phase 2: Database Schema (COMPLETE)
**Status:** Completed December 26, 2024
**Commit:** `034cad4` - Add Profile Management & Payment Infrastructure (Phase 1 & 2)

**Database Changes:**

**Extended User Model (14 new fields):**
```python
# Subscription fields
subscription_tier = db.Column(db.String(20), default='free')
subscription_status = db.Column(db.String(20), default='active')
subscription_start_date = db.Column(db.DateTime)
subscription_end_date = db.Column(db.DateTime)
trial_end_date = db.Column(db.DateTime)

# Payment provider IDs
stripe_customer_id = db.Column(db.String(255), unique=True, index=True)
stripe_subscription_id = db.Column(db.String(255), index=True)
paypal_subscription_id = db.Column(db.String(255), index=True)
coinbase_charge_code = db.Column(db.String(255), index=True)

# Billing metadata
billing_email = db.Column(db.String(120))
last_payment_date = db.Column(db.DateTime)
payment_failures = db.Column(db.Integer, default=0)

# Account deletion
account_deleted = db.Column(db.Boolean, default=False, index=True)
deletion_scheduled_date = db.Column(db.DateTime)
```

**New Models Created:**

**Subscription Model:**
- Tracks subscription history and changes
- Fields: id, user_id, tier, status, payment_provider, provider_subscription_id, start_date, end_date, next_billing_date, amount_paid, currency
- Relationships: Links to User
- Indexes: user_id, status, payment_provider, provider_subscription_id

**Payment Model:**
- Tracks all payment transactions (successful, failed, pending, refunded)
- Fields: id, user_id, subscription_id, payment_provider, provider_transaction_id, amount, currency, status, payment_type, payment_date, notes
- Relationships: Links to User and Subscription
- Indexes: user_id, subscription_id, payment_provider, provider_transaction_id, status, payment_date

**Helper Methods Added:**
```python
def is_premium(self):
    return self.subscription_tier in ['monthly', 'annual', 'lifetime']

def can_create_habit(self):
    if self.is_premium():
        return True
    active_count = Habit.query.filter_by(user_id=self.id, archived=False).count()
    return active_count < 3

def get_habit_limit(self):
    return None if self.is_premium() else 3
```

**Migrations:**
- ✅ `auto_migrate.py` updated with safe migrations
- ✅ All migrations tested on SQLite (development)
- ✅ Fixed SQLite UNIQUE constraint limitation
- ✅ Idempotent migrations (safe to run multiple times)

**Testing Completed:**
- ✅ Fresh database initialization
- ✅ Existing database migration (adds missing columns)
- ✅ Helper methods (is_premium, can_create_habit, get_habit_limit)
- ✅ No data loss during migration

---

### 🔄 Phase 3: Stripe Integration (IN PROGRESS)
**Status:** Starting now
**Estimated Time:** 2-3 days
**Priority:** High

**Goal:** Implement credit/debit card payments via Stripe (primary payment method)

**Tasks Remaining:**

1. **Setup Stripe Account:**
   - [ ] Create Stripe account (use test mode initially)
   - [ ] Create 3 products in Stripe dashboard:
     - Monthly subscription: $2.99/month
     - Annual subscription: $19.99/year
     - Lifetime purchase: $59.99 one-time
   - [ ] Get API keys from Stripe dashboard (test mode)
   - [ ] Get webhook secret for signature verification

2. **Backend Implementation:**
   - [ ] Add `stripe>=7.0.0` to `requirements.txt`
   - [ ] Create `payments.py` - Payment processing blueprint
   - [ ] Create `webhooks.py` - Webhook handlers
   - [ ] Update `config.py` - Add Stripe configuration
   - [ ] Update `.env.example` - Document required environment variables

3. **Key Functions to Implement in `payments.py`:**
   ```python
   def create_stripe_checkout_session(user, tier):
       # Create or retrieve Stripe customer
       # Create Checkout Session
       # Return session URL

   def handle_stripe_success(session_id):
       # Retrieve session from Stripe
       # Update user subscription
       # Create Subscription + Payment records
       # Flash success message

   def cancel_stripe_subscription(subscription_id):
       # Cancel at Stripe
       # Update user.subscription_status = 'cancelled'
   ```

4. **Webhook Handler in `webhooks.py`:**
   ```python
   @app.route('/webhooks/stripe', methods=['POST'])
   def stripe_webhook():
       # Verify signature
       # Handle events:
       #   - checkout.session.completed
       #   - customer.subscription.updated
       #   - customer.subscription.deleted
       #   - invoice.payment_failed
   ```

5. **Routes to Create:**
   - `GET /payments/checkout?tier=monthly&provider=stripe`
   - `GET /payments/success?session_id=xxx`
   - `GET /payments/cancel`
   - `POST /webhooks/stripe`

6. **Templates to Create:**
   - [ ] `templates/payments/checkout_stripe.html` - Checkout redirect page
   - [ ] `templates/payments/success.html` - Payment success page
   - [ ] `templates/payments/cancel.html` - Payment cancelled page
   - [ ] `templates/profile/pricing_modal.html` - Pricing table (modal or inline)
   - [ ] `static/js/payments.js` - Payment handling JavaScript

7. **Frontend Updates:**
   - [ ] Update `templates/profile/subscription.html` - Replace placeholder with Stripe checkout buttons
   - [ ] Update `templates/base.html` - Add "Upgrade" button to navbar for free users
   - [ ] Create pricing modal/page with 3 tier options

8. **Configuration (.env variables needed):**
   ```bash
   STRIPE_SECRET_KEY=sk_test_xxxx
   STRIPE_PUBLISHABLE_KEY=pk_test_xxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxx
   STRIPE_MONTHLY_PRICE_ID=price_xxxx
   STRIPE_ANNUAL_PRICE_ID=price_xxxx
   STRIPE_LIFETIME_PRICE_ID=price_xxxx
   ```

9. **Testing Checklist:**
   - [ ] Create monthly subscription (test mode)
   - [ ] Create annual subscription (test mode)
   - [ ] Create lifetime purchase (test mode)
   - [ ] Test webhooks using Stripe CLI: `stripe listen --forward-to localhost:5000/webhooks/stripe`
   - [ ] Test subscription cancellation
   - [ ] Test payment failure handling
   - [ ] Verify subscription status updates correctly
   - [ ] Verify Payment and Subscription records created

10. **Security Checklist:**
    - [ ] Webhook signature verification implemented
    - [ ] HTTPS enforced in production
    - [ ] API keys stored in environment variables only
    - [ ] Never log sensitive payment data
    - [ ] CSRF protection on all forms
    - [ ] Rate limiting on checkout endpoints

**Resources:**
- Stripe Documentation: https://stripe.com/docs/checkout/quickstart
- Stripe Webhooks: https://stripe.com/docs/webhooks
- Stripe Test Cards: https://stripe.com/docs/testing

---

### ⏳ Phase 4: Habit Limit Enforcement (NOT STARTED)
**Status:** Pending Phase 3 completion
**Estimated Time:** 1 day
**Priority:** High

**Goal:** Enforce 3-habit limit for free tier, allow unlimited for premium

**Tasks:**
- [ ] Modify `/habits/add` route to check `current_user.can_create_habit()`
- [ ] Show habit counter in dashboard for free users ("2/3 habits used")
- [ ] Redirect to upgrade page when limit reached
- [ ] Implement downgrade handling (when subscription expires with >3 habits)
- [ ] Show warning banner for users with >3 habits on free tier
- [ ] Send email reminder about habit limit
- [ ] Test: Free user creates 3 habits → allowed, 4th → blocked
- [ ] Test: Paid user creates 10 habits → allowed
- [ ] Test: Paid user downgrades with 8 habits → warning shown

---

### ⏳ Phase 5: PayPal Integration (NOT STARTED)
**Status:** Pending Phase 4 completion
**Estimated Time:** 2 days
**Priority:** Medium

**Goal:** Add PayPal as alternative payment option for recurring subscriptions

**Tasks:**
- [ ] Create PayPal Business account (sandbox mode)
- [ ] Create subscription plans (monthly, annual) in PayPal dashboard
- [ ] Get API credentials (Client ID, Client Secret)
- [ ] Add `paypalrestsdk>=1.13.1` to requirements.txt
- [ ] Extend `payments.py` with PayPal functions
- [ ] Extend `webhooks.py` with PayPal webhook handler
- [ ] Update config.py with PayPal configuration
- [ ] Update pricing modal with PayPal button
- [ ] Test subscription creation (sandbox)
- [ ] Test webhook delivery
- [ ] Test cancellation

**Environment Variables:**
```bash
PAYPAL_CLIENT_ID=xxxx
PAYPAL_CLIENT_SECRET=xxxx
PAYPAL_MODE=sandbox
PAYPAL_MONTHLY_PLAN_ID=P-xxxx
PAYPAL_ANNUAL_PLAN_ID=P-xxxx
```

---

### ⏳ Phase 6: Bitcoin Integration (NOT STARTED)
**Status:** Pending Phase 5 completion
**Estimated Time:** 2 days
**Priority:** Medium

**Goal:** Add crypto payment via Coinbase Commerce (lifetime tier only)

**Tasks:**
- [ ] Create Coinbase Commerce account
- [ ] Get API key and webhook secret
- [ ] Add `coinbase-commerce>=1.0.1` to requirements.txt
- [ ] Extend `payments.py` with Coinbase functions
- [ ] Extend `webhooks.py` with Coinbase webhook handler
- [ ] Create `templates/payments/checkout_crypto.html` - Bitcoin checkout page
- [ ] Update pricing modal with Bitcoin button
- [ ] Test charge creation (sandbox)
- [ ] Test charge:confirmed webhook
- [ ] Verify lifetime subscription created

**Environment Variables:**
```bash
COINBASE_COMMERCE_API_KEY=xxxx
COINBASE_COMMERCE_WEBHOOK_SECRET=xxxx
```

---

### ⏳ Phase 7: Subscription Management & Billing History (NOT STARTED)
**Status:** Pending Phase 6 completion
**Estimated Time:** 1 day
**Priority:** High

**Goal:** Complete subscription management UI and billing history

**Tasks:**
- [ ] Implement `/profile/subscription/cancel` - Cancel subscription
- [ ] Implement `/profile/subscription/resume` - Resume cancelled subscription
- [ ] Update `templates/profile/subscription.html` with real subscription data
- [ ] Implement billing history pagination (10 per page)
- [ ] Add date range filtering to billing history
- [ ] Create email templates for payment notifications
- [ ] Implement email sending:
  - Payment successful
  - Payment failed
  - Subscription cancelled
  - Downgrade warning (>3 habits)
- [ ] Test all email notifications
- [ ] Test subscription cancellation flow
- [ ] Test subscription resumption

---

### ⏳ Phase 8: Security Hardening (NOT STARTED)
**Status:** Pending Phase 7 completion
**Estimated Time:** 1 day
**Priority:** High

**Goal:** Ensure production-ready security

**Security Checklist:**
- [ ] Webhook signature verification (all 3 providers)
- [ ] Rate limiting on checkout/payment endpoints (10 req/hour per user)
- [ ] HTTPS enforced in production (`SESSION_COOKIE_SECURE = True`)
- [ ] Redirect HTTP → HTTPS
- [ ] API keys in environment variables only
- [ ] Never log payment details
- [ ] Encrypt database backups
- [ ] Graceful error handling for payment failures
- [ ] User-friendly error messages
- [ ] CSRF protection on all forms
- [ ] User ownership checks on all routes
- [ ] Password confirmation for sensitive actions

**GDPR Compliance:**
- [ ] Implement data export (JSON download)
- [ ] Implement hard delete after 30-day grace period
- [ ] Create privacy policy page
- [ ] Create terms of service page
- [ ] Add consent checkboxes for data processing

---

### ⏳ Phase 9: Mobile Testing & UI Polish (NOT STARTED)
**Status:** Pending Phase 8 completion
**Estimated Time:** 1 day
**Priority:** High

**Goal:** Ensure flawless mobile experience (iPhone SE 375px minimum)

**Testing Checklist:**

**Profile Pages (Mobile):**
- [ ] /profile - Responsive, no horizontal scroll
- [ ] /profile/edit - Forms usable on mobile
- [ ] /profile/settings - Touch targets 44px+
- [ ] /profile/subscription - Readable text
- [ ] /profile/billing - Table scrolls horizontally if needed
- [ ] /profile/about - All sections readable

**Payment Flow (Mobile):**
- [ ] Pricing modal - No horizontal scroll
- [ ] Stripe checkout - Redirects work on mobile
- [ ] PayPal checkout - Redirects work on mobile
- [ ] Coinbase checkout - QR code scannable
- [ ] Success page - Readable on mobile
- [ ] Cancel page - Readable on mobile

**Dashboard:**
- [ ] Habit counter visible for free users
- [ ] Upgrade button prominent
- [ ] No layout breaks at 375px

**Dark Mode:**
- [ ] All profile pages readable in dark mode
- [ ] Payment pages support dark mode
- [ ] Purple gradient theme consistent

**Touch Targets:**
- [ ] All buttons minimum 44px height
- [ ] Links have adequate tap area
- [ ] Form inputs easy to tap

---

### ⏳ Phase 10: Production Deployment (NOT STARTED)
**Status:** Pending Phase 9 completion
**Estimated Time:** 1 day
**Priority:** High

**Goal:** Launch payment system to production

**Environment Setup:**
- [ ] Add production Stripe keys to Render/Heroku
- [ ] Add production PayPal credentials
- [ ] Add production Coinbase Commerce key
- [ ] Set `FLASK_ENV=production`
- [ ] Verify `SESSION_COOKIE_SECURE=True`

**Webhook Configuration:**
- [ ] Register Stripe webhook: `https://habitflow.com/webhooks/stripe`
- [ ] Register PayPal webhook: `https://habitflow.com/webhooks/paypal`
- [ ] Register Coinbase webhook: `https://habitflow.com/webhooks/coinbase`
- [ ] Verify webhook signatures work in production

**Database Migration:**
- [ ] Backup production database
- [ ] Run migrations: `flask db upgrade`
- [ ] Verify no data loss
- [ ] Test on production

**Production Testing:**
- [ ] Create test subscription (Stripe live mode)
- [ ] Verify webhook delivery
- [ ] Test cancellation flow
- [ ] Monitor logs for errors

**Monitoring:**
- [ ] Set up alerts for payment failures
- [ ] Monitor webhook delivery (Stripe/PayPal/Coinbase dashboards)
- [ ] Track subscription metrics (MRR, churn)

**Documentation:**
- [ ] Update README with payment setup instructions
- [ ] Document webhook URLs
- [ ] Create admin guide for managing subscriptions

---

## Recent Fixes & Updates

### December 26, 2024

**Commit:** `aad0560` - Move About page to Profile section
- ✅ Moved about route from habits.py to profile.py
- ✅ Relocated templates/about.html to templates/profile/about.html
- ✅ Updated navigation links from habits.about to profile.about
- ✅ About page now accessible at /profile/about

**Commit:** `9d51247` - Fix Unicode character errors
- ✅ Removed Unicode checkmark characters (✓) causing Windows encoding errors
- ✅ Fixed print statements in app.py and auto_migrate.py
- ✅ App now starts successfully without charmap codec errors

**Comparison Charts Feature:**
- ✅ Added "This Week vs Last Week" comparison chart to stats page
- ✅ Shows grouped bar chart with purple gradients
- ✅ Displays percentage change with color-coded badges

**Hamburger Menu Fix:**
- ✅ Fixed hamburger menu not working on iPhone 13
- ✅ Hidden hamburger button on mobile (uses bottom nav instead)

---

## Environment Variables Needed

### Current (Already Set)
```bash
SECRET_KEY=xxx
DATABASE_URL=sqlite:///habits.db  # or postgresql://...
FLASK_ENV=development
```

### Phase 3 - Stripe (NEED TO ADD)
```bash
STRIPE_SECRET_KEY=sk_test_xxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
STRIPE_MONTHLY_PRICE_ID=price_xxxx
STRIPE_ANNUAL_PRICE_ID=price_xxxx
STRIPE_LIFETIME_PRICE_ID=price_xxxx
```

### Phase 5 - PayPal (NEED TO ADD)
```bash
PAYPAL_CLIENT_ID=xxxx
PAYPAL_CLIENT_SECRET=xxxx
PAYPAL_MODE=sandbox
PAYPAL_MONTHLY_PLAN_ID=P-xxxx
PAYPAL_ANNUAL_PLAN_ID=P-xxxx
```

### Phase 6 - Coinbase Commerce (NEED TO ADD)
```bash
COINBASE_COMMERCE_API_KEY=xxxx
COINBASE_COMMERCE_WEBHOOK_SECRET=xxxx
```

### Production Only
```bash
APP_URL=https://habitflow.com
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
```

---

## File Structure

### Current Files (Phase 1 & 2)
```
habit-tracker-app/
├── app.py                          # Main Flask app (profile blueprint registered)
├── profile.py                      # Profile blueprint (7 routes)
├── models.py                       # User, Habit, Subscription, Payment models
├── forms.py                        # Profile forms added
├── auto_migrate.py                 # Database migrations
├── config.py                       # Configuration (needs Stripe config)
├── requirements.txt                # Dependencies (needs stripe added)
├── .env.example                    # Environment variables template
├── templates/
│   ├── base.html                   # Navigation updated
│   ├── profile/
│   │   ├── view.html              # Profile overview
│   │   ├── edit.html              # Edit email/password
│   │   ├── settings.html          # Settings page
│   │   ├── subscription.html      # Subscription management (placeholder)
│   │   ├── billing.html           # Billing history (placeholder)
│   │   ├── delete_account.html    # Account deletion
│   │   └── about.html             # About page
│   └── stats.html                  # Comparison charts added
└── IMPLEMENTATION_PROGRESS.md      # This file
```

### Files to Create (Phase 3)
```
├── payments.py                     # Payment processing blueprint
├── webhooks.py                     # Webhook handlers
├── static/
│   └── js/
│       └── payments.js            # Payment frontend logic
└── templates/
    └── payments/
        ├── checkout_stripe.html   # Stripe checkout redirect
        ├── success.html           # Payment success
        └── cancel.html            # Payment cancelled
```

---

## Next Steps (Resume Here)

1. **Start Phase 3: Stripe Integration**
   - Create Stripe test account at https://dashboard.stripe.com/register
   - Get test API keys
   - Create 3 products (Monthly, Annual, Lifetime)
   - Add Stripe SDK to requirements.txt
   - Create payments.py blueprint
   - Create webhooks.py handler

2. **Read This Document First**
   - Review Phase 3 tasks above
   - Set up Stripe account before coding
   - Follow security checklist

3. **Testing Strategy**
   - Use Stripe test mode for all development
   - Use Stripe CLI for webhook testing
   - Switch to live mode only in Phase 10

---

## Questions or Blockers?

If you encounter issues:
1. Check this document first
2. Review the original plan in `.claude/plans/composed-sparking-snowflake.md`
3. Verify all Phase 1 & 2 features are working before proceeding

---

**Document Owner:** Paulo
**Project:** HabitFlow
**Purpose:** Track implementation progress across multiple computers
**Last Modified:** December 26, 2024
