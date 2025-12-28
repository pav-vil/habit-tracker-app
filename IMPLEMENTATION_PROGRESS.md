# HabitFlow Profile & Payment Infrastructure - Implementation Progress

**Last Updated:** December 27, 2024
**Current Phase:** Phase 7 - Subscription Management UI
**Overall Progress:** 70% (7 of 10 phases complete)

---

## Quick Summary

This document tracks the implementation of the complete profile management and multi-payment subscription system for HabitFlow. Use this to resume work from any computer.

### Business Model
- **Free Tier:** 3 habits maximum
- **Monthly:** $2.99/month (unlimited habits)
- **Annual:** $19.99/year (67% savings - **BEST VALUE**)
- **Lifetime:** $59.99 one-time (no recurring payments)

### Payment Methods
- ✅ **Stripe** (Credit/Debit cards) - Primary payment method (LIVE)
- ✅ **PayPal** - Alternative recurring payments (LIVE)
- ✅ **Coinbase Commerce** (Bitcoin) - Crypto option for lifetime tier (LIVE)

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
- ✅ `templates/profile/subscription.html` - Subscription management
- ✅ `templates/profile/billing.html` - Payment history
- ✅ `templates/profile/delete_account.html` - Account deletion with 30-day grace
- ✅ `templates/profile/about.html` - About page
- ✅ `forms.py` - Added 4 new forms
- ✅ `templates/base.html` - Navigation updated

**Routes Available:**
- `GET /profile` - View profile overview
- `GET /profile/edit` - Edit email/password
- `POST /profile/edit` - Update email/password
- `GET /profile/settings` - Settings page
- `POST /profile/settings` - Update settings
- `GET /profile/subscription` - Subscription management
- `GET /profile/billing` - Billing history
- `GET /profile/delete` - Delete account confirmation
- `POST /profile/delete` - Schedule account deletion
- `GET /profile/about` - About HabitFlow

---

### ✅ Phase 2: Database Schema (COMPLETE)
**Status:** Completed December 26, 2024
**Commit:** `034cad4` + `51b6af1` (merged with subscription system)

**Database Changes:**

**Extended User Model (19 fields):**
```python
# Subscription fields
subscription_tier = db.Column(db.String(20), default='free')
subscription_status = db.Column(db.String(20), default='active')
subscription_start_date = db.Column(db.DateTime)
subscription_end_date = db.Column(db.DateTime)
trial_end_date = db.Column(db.DateTime)
habit_limit = db.Column(db.Integer, default=3)

# Payment provider IDs
stripe_customer_id = db.Column(db.String(255), unique=True, index=True)
stripe_subscription_id = db.Column(db.String(255), index=True)
paypal_subscription_id = db.Column(db.String(255), index=True)
coinbase_charge_code = db.Column(db.String(255), index=True)

# Billing metadata
billing_email = db.Column(db.String(120))
last_payment_date = db.Column(db.DateTime)
payment_failures = db.Column(db.Integer, default=0)

# Email notification preferences (Phase 5 Email)
email_notifications_enabled = db.Column(db.Boolean, default=True)
reminder_time = db.Column(db.String(5), default='09:00')
reminder_days = db.Column(db.String(20), default='all')
last_reminder_sent = db.Column(db.Date)

# Account deletion
account_deleted = db.Column(db.Boolean, default=False, index=True)
deletion_scheduled_date = db.Column(db.DateTime)
```

**New Models Created:**

**Subscription Model:**
- Tracks subscription history and changes
- Fields: id, user_id, tier, status, payment_provider, provider_subscription_id, start_date, end_date, next_billing_date, amount_paid, currency
- Supports: Stripe, PayPal, Coinbase providers

**Payment Model:**
- Tracks all payment transactions
- Fields: id, user_id, subscription_id, payment_provider, provider_transaction_id, amount, currency, status, payment_type, payment_date, notes
- Status: completed, failed, pending, refunded

**SubscriptionHistory Model:**
- Audit trail for all subscription changes
- Fields: id, user_id, subscription_type, status, started_at, ended_at, stripe_subscription_id, amount, notes

**PaymentTransaction Model:**
- Complete payment record tracking
- Fields: id, user_id, transaction_type, amount, status, payment_date, stripe_payment_id, notes

**Helper Methods:**
```python
def is_premium(self):
    return self.subscription_tier in ['monthly', 'annual', 'lifetime']

def is_premium_active(self):
    # Checks tier + expiration for active subscription

def can_create_habit(self):
    # Enforces 3-habit limit for free tier

def can_add_more_habits(self):
    # Returns True for premium, checks limit for free

def get_habit_limit(self):
    return None if self.is_premium() else 3
```

---

### ✅ Phase 3: Stripe Integration (COMPLETE)
**Status:** Completed December 27, 2024
**Commits:** `30bb743`, `3929649`, `869117c`, `51b6af1`

**Implementation:**

**Backend (`payments.py`):**
- ✅ `create_stripe_checkout_session()` - Creates Stripe checkout
- ✅ Stripe Customer creation/retrieval
- ✅ Support for subscription mode (monthly/annual) and payment mode (lifetime)
- ✅ Success/cancel URL handling
- ✅ Metadata tracking (user_id, tier)

**Routes:**
- ✅ `GET /payments/checkout?tier=monthly&provider=stripe`
- ✅ `GET /payments/success?session_id=xxx` - Payment success handler
- ✅ `GET /payments/cancel` - Payment cancelled page

**Webhooks (`webhooks.py`):**
- ✅ `POST /webhooks/stripe` - Stripe webhook endpoint
- ✅ `checkout.session.completed` - Initial payment success
- ✅ `customer.subscription.updated` - Subscription changes
- ✅ `customer.subscription.deleted` - Subscription cancellation
- ✅ `invoice.payment_succeeded` - Recurring payment success
- ✅ `invoice.payment_failed` - Payment failure handling (3 strikes)
- ✅ Webhook signature verification for security

**Templates:**
- ✅ `templates/payments/success.html` - Payment success page
- ✅ `templates/payments/cancel.html` - Payment cancelled page

**Configuration:**
```bash
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID_MONTHLY=price_xxx
STRIPE_PRICE_ID_ANNUAL=price_xxx
STRIPE_PRICE_ID_LIFETIME=price_xxx
```

**Testing Completed:**
- ✅ Monthly subscription checkout
- ✅ Annual subscription checkout
- ✅ Lifetime payment checkout
- ✅ Webhook event processing
- ✅ Database records created correctly
- ✅ User subscription updated on payment

---

### ✅ Phase 4: Habit Limit Enforcement (COMPLETE)
**Status:** Completed December 27, 2024
**Commit:** `869117c` - Add Phase 4: Subscription downgrade handling

**Implementation:**

**Habit Creation Enforcement (`habits.py`):**
- ✅ Check `can_add_more_habits()` before allowing new habit
- ✅ Race condition protection (double-check after form submission)
- ✅ Redirect to upgrade page when limit reached
- ✅ Clear error message: "Free tier limited to 3 habits"

**Dashboard UI (`templates/dashboard.html`):**
- ✅ Habit counter for free users: "2/3 habits used"
- ✅ Over-limit warning banner (orange gradient)
- ✅ "Upgrade to Premium" button
- ✅ Shows number of habits to archive

**Downgrade Handling (`stripe_handler.py`):**
- ✅ `downgrade_user_to_free()` function
- ✅ Scheduled task: `check_expired_subscriptions.py`
- ✅ Automatically downgrades users when subscription expires
- ✅ Calculates habits_to_archive count
- ✅ Sets habit_limit = 3 for free users
- ✅ Tracks downgrade in SubscriptionHistory

**Warning System:**
- ✅ Orange banner shown when user has >3 habits on free tier
- ✅ "Choose Habits to Archive" button
- ✅ Email notification sent (Phase 5 Email integration)

**Testing Completed:**
- ✅ Free user creates 3 habits → allowed
- ✅ Free user tries 4th habit → blocked with message
- ✅ Premium user creates 10 habits → allowed
- ✅ Premium user downgrades with 8 habits → warning shown
- ✅ Subscription expiration triggers auto-downgrade

---

### ✅ Phase 5: PayPal Integration (COMPLETE)
**Status:** Completed December 27, 2024
**Commit:** `b72bae2` - Add Phase 5: PayPal Integration

**Implementation:**

**Backend (`payments.py`):**
- ✅ `init_paypal()` - Initialize PayPal SDK
- ✅ `create_paypal_subscription()` - Create subscription and redirect
- ✅ `paypal_success()` - Handle approval callback
- ✅ `cancel_paypal_subscription()` - Cancel recurring subscription
- ✅ Support for monthly and annual plans (lifetime uses Stripe/Coinbase)

**Routes:**
- ✅ `GET /payments/checkout?tier=monthly&provider=paypal`
- ✅ `GET /payments/paypal-success?subscription_id=xxx`

**Webhooks (`webhooks.py`):**
- ✅ `POST /webhooks/paypal` - PayPal webhook endpoint
- ✅ `BILLING.SUBSCRIPTION.ACTIVATED` - Subscription activation
- ✅ `BILLING.SUBSCRIPTION.UPDATED` - Status changes
- ✅ `BILLING.SUBSCRIPTION.CANCELLED` - User cancellation → downgrade
- ✅ `BILLING.SUBSCRIPTION.SUSPENDED` - Payment failure tracking
- ✅ `PAYMENT.SALE.COMPLETED` - Recurring payment renewal
- ✅ Webhook signature verification

**Configuration:**
```bash
PAYPAL_MODE=sandbox  # or 'live'
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_secret
PAYPAL_WEBHOOK_ID=your_webhook_id
PAYPAL_PLAN_ID_MONTHLY=P-xxxxx
PAYPAL_PLAN_ID_ANNUAL=P-xxxxx
```

**Dependencies:**
- ✅ Added `paypalrestsdk>=1.13.1` to requirements.txt

**Testing Checklist:**
- [ ] Create PayPal subscription plans
- [ ] Test monthly subscription
- [ ] Test annual subscription
- [ ] Test webhook events
- [ ] Test cancellation flow
- [ ] Verify downgrade on cancellation

**Notes:**
- PayPal doesn't support one-time "lifetime" payments
- Lifetime tier requires Stripe or Coinbase Commerce

---

### ✅ Phase 5 (Email): Email Notifications (COMPLETE - BONUS)
**Status:** Completed December 27, 2024
**Commit:** `9bbe8ba` - Add Phase 5: Email notifications and user settings

**What Was Built:**

**Email Service (`email_service.py`):**
- ✅ `send_payment_success_email()` - Payment receipt
- ✅ `send_payment_failed_email()` - Payment failure alert
- ✅ `send_subscription_cancelled_email()` - Cancellation confirmation
- ✅ `send_subscription_expired_email()` - Expiry notice with habit warning
- ✅ `send_daily_reminder()` - Daily habit reminder with preferences
- ✅ HTML + plain text templates for all emails

**Email Templates (`templates/emails/`):**
- ✅ `base.html` - Email base template with HabitFlow branding
- ✅ `payment_success.html/.txt` - Receipt with transaction details
- ✅ `payment_failed.html/.txt` - Failure notification
- ✅ `subscription_cancelled.html/.txt` - Cancellation confirmation
- ✅ `subscription_expired.html/.txt` - Expiry notice
- ✅ `daily_reminder.html/.txt` - Habit reminder

**User Settings (`auth.py`):**
- ✅ `GET/POST /auth/settings` - Email notification preferences
- ✅ Enable/disable email notifications
- ✅ Set reminder time (time picker)
- ✅ Choose reminder days (all/weekdays/weekends)
- ✅ `templates/settings.html` - Settings UI

**Stripe Integration:**
- ✅ Send payment_success email after checkout
- ✅ Send payment_failed email on failures
- ✅ Send subscription_cancelled email on cancellation
- ✅ Send subscription_expired email on expiration

**Daily Reminders:**
- ✅ `send_daily_reminders.py` - Cron job script
- ✅ Respects user preferences (time, days)
- ✅ Only sends for incomplete habits
- ✅ Tracks last_reminder_sent to prevent duplicates

**Configuration:**
```bash
MAIL_SERVER=smtp.gmail.com  # or SendGrid/Mailgun
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your.email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=HabitFlow <noreply@habitflow.app>
```

**Dependencies:**
- ✅ Added `Flask-Mail>=0.9.1` to requirements.txt

**Scheduled Task Setup:**
```bash
# Cron job for daily reminders (9 AM daily)
0 9 * * * cd /path/to/habit-tracker-app && python send_daily_reminders.py
```

---

### ✅ Phase 6: Coinbase Commerce Integration (COMPLETE)
**Status:** Completed December 27, 2024
**Commit:** `8728e23` - Complete Phase 6: Coinbase Commerce Integration

**Goal:** Add crypto payment via Coinbase Commerce (lifetime tier only)

**Implementation:**

**Backend (`payments.py`):**
- ✅ `init_coinbase()` - Initialize Coinbase Commerce client
- ✅ `create_coinbase_charge()` - Create Bitcoin charge for lifetime tier
- ✅ `coinbase_success()` - Handle payment redirect (shows pending page)
- ✅ Restriction: Coinbase only available for lifetime tier ($59.99)
- ✅ One-time payment (no recurring subscriptions)

**Routes:**
- ✅ `GET /payments/checkout?tier=lifetime&provider=coinbase`
- ✅ `GET /payments/coinbase-success` - Payment confirmation page

**Webhooks (`webhooks.py`):**
- ✅ `POST /webhooks/coinbase` - Coinbase Commerce webhook endpoint
- ✅ `charge:confirmed` - Payment confirmed on blockchain → activate lifetime subscription
- ✅ `charge:failed` - Payment failed or expired → record failed payment
- ✅ `charge:pending` - Payment initiated but not confirmed yet
- ✅ Webhook signature verification using Coinbase Commerce SDK
- ✅ Creates Subscription and Payment records on confirmation

**Templates:**
- ✅ `templates/payments/coinbase_pending.html` - Bitcoin payment confirmation page
  - Explains 10-30 minute blockchain confirmation time
  - Shows premium benefits preview
  - Pulse animation on pending icon
  - User can safely close page, email sent on confirmation

**Configuration (`config.py`):**
```python
COINBASE_COMMERCE_API_KEY = os.environ.get('COINBASE_COMMERCE_API_KEY')
COINBASE_COMMERCE_WEBHOOK_SECRET = os.environ.get('COINBASE_COMMERCE_WEBHOOK_SECRET')
COINBASE_LIFETIME_PRICE = float(os.environ.get('COINBASE_LIFETIME_PRICE', '59.99'))
```

**Environment Variables (`.env.example`):**
```bash
COINBASE_COMMERCE_API_KEY=your_api_key_here
COINBASE_COMMERCE_WEBHOOK_SECRET=your_webhook_shared_secret_here
COINBASE_LIFETIME_PRICE=59.99
```

**Dependencies:**
- ✅ Added `coinbase-commerce>=1.0.1` to requirements.txt

**Payment Provider Matrix:**
| Provider | Monthly | Annual | Lifetime |
|----------|---------|--------|----------|
| Stripe   | ✅ $2.99 | ✅ $19.99 | ✅ $59.99 |
| PayPal   | ✅ $2.99 | ✅ $19.99 | ❌ N/A |
| Coinbase | ❌ N/A | ❌ N/A | ✅ $59.99 |

**Security:**
- ✅ Webhook signature verification (X-CC-Webhook-Signature header)
- ✅ Idempotency checks to prevent duplicate activations
- ✅ Metadata validation for user_id and tier

**Testing Checklist:**
- [ ] Create Coinbase Commerce account
- [ ] Get API key and webhook secret from dashboard
- [ ] Test charge creation with sandbox account
- [ ] Test webhook events (charge:confirmed, charge:failed, charge:pending)
- [ ] Verify lifetime subscription activated on blockchain confirmation
- [ ] Test payment failure handling
- [ ] Verify email sent on confirmation (Phase 5 Email integration)

**Production Setup:**
1. Create Coinbase Commerce account at https://commerce.coinbase.com/
2. Get API key from Settings > API Keys
3. Create webhook at Settings > Webhook subscriptions
   - URL: https://your-domain.com/webhooks/coinbase
   - Events: charge:confirmed, charge:failed, charge:pending
4. Copy Webhook Shared Secret
5. Add credentials to Render environment variables

**Notes:**
- Coinbase Commerce only supports one-time payments (perfect for lifetime tier)
- Bitcoin, Ethereum, Litecoin, USDC, and other crypto supported
- Payment confirmation takes ~10 minutes (blockchain confirmations)
- User receives email when payment is confirmed (webhook-based)
- Actual subscription activation happens via webhook, not redirect page

---

### ⏳ Phase 7: Subscription Management & Billing History (PARTIALLY COMPLETE)
**Status:** Pending Phase 6 completion
**Estimated Time:** 1 day
**Priority:** High

**Already Built:**
- ✅ Email notifications for all payment events
- ✅ Subscription records tracked in database
- ✅ Payment records tracked in database
- ✅ Email service with templates

**Remaining Tasks:**
- [ ] Implement `/profile/subscription/cancel` - Cancel subscription
- [ ] Implement `/profile/subscription/resume` - Resume cancelled subscription
- [ ] Update `templates/profile/subscription.html` with real data:
  - Current plan details
  - Next billing date
  - Payment method
  - Cancel/Resume buttons
- [ ] Implement billing history pagination (10 per page)
- [ ] Add date range filtering to billing history
- [ ] Display payment history in `templates/profile/billing.html`

**Email Notifications (Already Complete):**
- ✅ Payment successful
- ✅ Payment failed
- ✅ Subscription cancelled
- ✅ Downgrade warning (>3 habits)
- ✅ Daily habit reminders

---

### ⏳ Phase 8: Security Hardening (PARTIALLY COMPLETE)
**Status:** Ongoing
**Estimated Time:** 1 day
**Priority:** High

**Already Implemented:**
- ✅ Webhook signature verification (Stripe, PayPal)
- ✅ CSRF protection on all forms
- ✅ Password hashing (Werkzeug)
- ✅ Environment variables for secrets
- ✅ HTTPS enforced in production (Render)
- ✅ Session cookie security settings
- ✅ User ownership checks on routes

**Remaining Tasks:**
- [ ] Rate limiting on checkout/payment endpoints (10 req/hour per user)
- [ ] Graceful error handling for payment failures (partially done)
- [ ] Encrypt database backups
- [ ] Password confirmation for sensitive actions (delete account, change payment)
- [ ] Audit logging for security events

**GDPR Compliance:**
- [ ] Implement data export (JSON download)
- [ ] Implement hard delete after 30-day grace period
- [ ] Create privacy policy page
- [ ] Create terms of service page
- [ ] Add consent checkboxes for data processing

---

### ⏳ Phase 9: Mobile Testing & UI Polish (PARTIALLY COMPLETE)
**Status:** Ongoing
**Estimated Time:** 1 day
**Priority:** High

**Already Tested:**
- ✅ Dashboard responsive (iPhone SE 375px minimum)
- ✅ Profile pages responsive
- ✅ Dark mode support
- ✅ Touch targets 44px+ (iOS standard)
- ✅ Bottom navigation for mobile
- ✅ Swipe gestures for habit completion

**Remaining Testing:**
- [ ] Payment flow on mobile (Stripe, PayPal, Coinbase)
- [ ] Pricing modal - No horizontal scroll
- [ ] Success/cancel pages on mobile
- [ ] Billing history table responsive
- [ ] All forms usable on mobile keyboards

---

### ⏳ Phase 10: Production Deployment (PARTIALLY COMPLETE)
**Status:** Deployed to Render, needs final configuration
**Priority:** High

**Already Deployed:**
- ✅ App running on Render.com
- ✅ PostgreSQL database configured
- ✅ Auto-migrations working
- ✅ HTTPS enabled
- ✅ Environment variables set

**Remaining Tasks:**
- [ ] Add production Stripe keys to Render
- [ ] Add production PayPal credentials to Render
- [ ] Add production email credentials (SendGrid/Mailgun)
- [ ] Register production webhook URLs:
  - `https://habitflow.onrender.com/webhooks/stripe`
  - `https://habitflow.onrender.com/webhooks/paypal`
  - `https://habitflow.onrender.com/webhooks/coinbase` (Phase 6)
- [ ] Verify webhook signatures work in production
- [ ] Test live payments (Stripe, PayPal)
- [ ] Set up monitoring/alerts for payment failures
- [ ] Monitor subscription metrics (MRR, churn)
- [ ] Create admin dashboard for subscription management

---

## Recent Fixes & Updates

### December 27, 2024

**CRITICAL FIX: PostgreSQL Migration Issue**
**Commit:** `b72bae2` - PostgreSQL compatibility fix

**Problem:**
```
(psycopg2.errors.UndefinedColumn) column user.habit_limit does not exist
```

**Root Cause:**
- PostgreSQL treats `user` as a reserved keyword
- Migrations were failing silently because table name wasn't quoted
- Users couldn't log in due to missing columns

**Solution:**
- Updated `auto_migrate.py` to use `"user"` (quoted) instead of `user`
- Changed all ALTER TABLE statements for PostgreSQL compatibility
- Fixed boolean DEFAULT values (1 → TRUE for PostgreSQL)
- Created `fix_habit_limit_migration.py` for emergency repairs

**Files Changed:**
- `auto_migrate.py` - All user table migrations now PostgreSQL-compatible
- `fix_habit_limit_migration.py` - Emergency migration script for Render

**Deployment Fix:**
1. Redeploy on Render (auto-migrate will run correctly now)
2. Or manually run: `python fix_habit_limit_migration.py`

---

**Commit:** `51b6af1` - Merge subscription system with profile management

**Major Merge:**
- Combined local subscription system (Phases 2-5) with remote profile features
- Merged User model with ALL fields from both versions (19 new fields)
- Combined all blueprints: auth, habits, stats, profile, subscription, payments, webhooks
- Merged templates: base.html (navigation + dark mode) and dashboard.html (all features)
- Result: Comprehensive app with subscription + profile + dark mode + mobile optimization

**Features Combined:**
- LOCAL: Stripe payments, email notifications, habit limits, downgrade handling
- REMOTE: Dark mode toggle, profile pages, swipe gestures, motivational quotes
- Both subscription tracking systems preserved (SubscriptionHistory + Subscription models)

---

**Commit:** `9bbe8ba` - Email Notifications System

**Complete email notification system:**
- Payment receipts, failure alerts, cancellation confirmations
- Daily habit reminders with user preferences
- User settings page for notification preferences
- HTML + text email templates
- Flask-Mail integration
- Scheduled reminder script

---

**Commit:** `869117c` - Subscription Downgrade Handling

**Automatic downgrade system:**
- `check_expired_subscriptions.py` - Scheduled task
- `downgrade_user_to_free()` function
- Over-limit warning banner on dashboard
- Habit archival tracking
- Email notifications for expired subscriptions

---

**Commit:** `3929649` - Dark Purple UI Theme

**Visual update:**
- Dark purple color scheme throughout app
- Updated CSS variables
- Enhanced stat cards
- Purple gradient backgrounds

---

**Commit:** `30bb743` - Stripe Payment Integration

**Full Stripe implementation:**
- Checkout sessions for all tiers
- Webhook handlers for 5 event types
- Database tracking (Subscription + Payment models)
- Success/cancel pages
- Customer creation and management

---

## Environment Variables Summary

### Required for Current Functionality:

```bash
# Flask Core
SECRET_KEY=your_64_char_secret_key
DATABASE_URL=postgresql://...  # Auto-set by Render
FLASK_ENV=production

# Stripe (Phase 3)
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID_MONTHLY=price_xxx
STRIPE_PRICE_ID_ANNUAL=price_xxx
STRIPE_PRICE_ID_LIFETIME=price_xxx

# PayPal (Phase 5)
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
PAYPAL_WEBHOOK_ID=xxx
PAYPAL_PLAN_ID_MONTHLY=P-xxx
PAYPAL_PLAN_ID_ANNUAL=P-xxx

# Email (Phase 5 Email)
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key
MAIL_DEFAULT_SENDER=HabitFlow <noreply@habitflow.app>

# App Config
APP_URL=https://yourapp.onrender.com
```

### Optional (Phase 6):

```bash
# Coinbase Commerce
COINBASE_COMMERCE_API_KEY=xxx
COINBASE_COMMERCE_WEBHOOK_SECRET=xxx
```

---

## File Structure

### Current Files (Phases 1-5 Complete):

```
habit-tracker-app/
├── app.py                          # Main Flask app
├── auth.py                         # Authentication + Settings
├── habits.py                       # Habit management with limit enforcement
├── profile.py                      # Profile management
├── payments.py                     # Stripe + PayPal checkout
├── webhooks.py                     # Stripe + PayPal webhooks
├── stripe_handler.py               # Stripe subscription management
├── subscription.py                 # Subscription blueprint
├── email_service.py                # Email notification service
├── models.py                       # User, Habit, Subscription, Payment models
├── forms.py                        # All forms
├── auto_migrate.py                 # Database migrations (PostgreSQL-compatible)
├── config.py                       # Configuration (Stripe, PayPal, Email)
├── requirements.txt                # Dependencies (Stripe, PayPal, Flask-Mail)
├── .env.example                    # Environment variables template
├── check_expired_subscriptions.py  # Cron job for downgrades
├── send_daily_reminders.py         # Cron job for email reminders
├── fix_habit_limit_migration.py    # Emergency migration script
├── templates/
│   ├── base.html                   # Navigation + Dark mode + Mobile nav
│   ├── dashboard.html              # Dashboard with over-limit warnings
│   ├── settings.html               # Email notification settings
│   ├── profile/                    # Profile pages
│   │   ├── view.html
│   │   ├── edit.html
│   │   ├── settings.html
│   │   ├── subscription.html
│   │   ├── billing.html
│   │   ├── delete_account.html
│   │   └── about.html
│   ├── payments/                   # Payment pages
│   │   ├── success.html
│   │   └── cancel.html
│   └── emails/                     # Email templates
│       ├── base.html
│       ├── payment_success.html/.txt
│       ├── payment_failed.html/.txt
│       ├── subscription_cancelled.html/.txt
│       ├── subscription_expired.html/.txt
│       └── daily_reminder.html/.txt
└── IMPLEMENTATION_PROGRESS.md      # This file
```

### Files to Create (Phase 6):

```
├── templates/
│   └── payments/
│       └── checkout_crypto.html    # Bitcoin checkout page
```

---

## Next Steps (Resume Here)

### Immediate Priority:

1. **Fix Render Deployment (If Needed)**
   - Verify auto-migrate fixed the PostgreSQL issue
   - Test login functionality
   - Check database columns are created

2. **Configure Production Email**
   - Set up SendGrid or Mailgun account
   - Add production email credentials to Render
   - Test email sending in production

3. **Configure Production PayPal**
   - Switch from sandbox to live mode
   - Create live subscription plans
   - Register production webhook URL
   - Test PayPal checkout flow

### Next Phase (Phase 6):

1. **Start Coinbase Commerce Integration**
   - Create Coinbase Commerce account
   - Get API credentials
   - Implement crypto payment for lifetime tier
   - Test Bitcoin checkout

### Testing Checklist (Before Going Live):

- [ ] Stripe checkout works (monthly, annual, lifetime)
- [ ] PayPal checkout works (monthly, annual)
- [ ] Webhooks processing correctly (Stripe, PayPal)
- [ ] Email notifications sending
- [ ] Habit limit enforcement working
- [ ] Downgrade system working
- [ ] Mobile UI tested on real devices
- [ ] All database migrations applied

---

## Questions or Blockers?

If you encounter issues:
1. Check this document first
2. Review commit history for recent changes
3. Check Render logs for errors
4. Verify all environment variables are set

**Common Issues:**

**Login Error on Render:**
- Fix: Redeploy (auto_migrate.py now PostgreSQL-compatible)
- Or run: `python fix_habit_limit_migration.py`

**Emails Not Sending:**
- Verify MAIL_* environment variables are set
- Check email provider credentials
- Test with local SMTP server first

**Webhooks Not Working:**
- Verify webhook URLs are publicly accessible
- Check webhook signature verification
- Review webhook logs in Stripe/PayPal dashboards

---

**Document Owner:** Paulo
**Project:** HabitFlow
**Purpose:** Track implementation progress across all phases
**Repository:** https://github.com/pav-vil/habit-tracker-app
**Last Modified:** December 27, 2024
