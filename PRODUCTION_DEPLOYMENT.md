# HabitFlow - Production Deployment Guide

**Last Updated:** December 28, 2025
**Target Platform:** Render.com (Web Service + PostgreSQL)
**Status:** Ready for production deployment

---

## Pre-Deployment Checklist

### ✅ Code Readiness
- [x] All 10 implementation phases complete
- [x] Security hardening implemented (rate limiting, audit logging, CSRF protection)
- [x] GDPR compliance (data export, privacy policy, terms of service)
- [x] Payment integration (Stripe, PayPal, Coinbase Commerce)
- [x] Email notifications configured
- [x] Error handling and logging in place

### ✅ Documentation
- [x] README.md updated
- [x] .env.example with all required variables
- [x] Privacy policy and terms of service published
- [x] IMPLEMENTATION_PROGRESS.md tracking complete

---

## Step 1: Prepare Production Accounts

### 1.1 Stripe Account (Required)
1. Go to https://dashboard.stripe.com/register
2. Create a Stripe account (business account recommended)
3. Complete account verification
4. **Switch to LIVE mode** (toggle in top-right corner)
5. Navigate to **Developers > API Keys**
6. Copy your LIVE keys:
   - `STRIPE_SECRET_KEY` (starts with `sk_live_`)
   - `STRIPE_PUBLISHABLE_KEY` (starts with `pk_live_`)

**Create Products and Prices:**
1. Go to **Products** in Stripe Dashboard
2. Create three products:
   - **Monthly Plan**: $2.99/month recurring
   - **Annual Plan**: $19.99/year recurring
   - **Lifetime Access**: $59.99 one-time payment
3. Copy the Price IDs (start with `price_`)

**Set Up Webhooks:**
1. Go to **Developers > Webhooks**
2. Click **Add endpoint**
3. Endpoint URL: `https://your-app.onrender.com/webhooks/stripe`
4. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the **Signing secret** (`whsec_...`)

### 1.2 PayPal Account (Optional but Recommended)
1. Create business account at https://www.paypal.com/business
2. Go to https://developer.paypal.com/dashboard/applications/live
3. Create a REST API app
4. Copy credentials:
   - `PAYPAL_CLIENT_ID`
   - `PAYPAL_CLIENT_SECRET`
5. Set `PAYPAL_MODE=live`

**Create Subscription Plans:**
1. Go to PayPal Dashboard > Products & Services > Subscriptions
2. Create two subscription plans:
   - Monthly: $2.99/month
   - Annual: $19.99/year
3. Copy Plan IDs (`P-...`)

**Set Up Webhooks:**
1. Go to https://developer.paypal.com/dashboard/webhooks
2. Add webhook URL: `https://your-app.onrender.com/webhooks/paypal`
3. Select events:
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `PAYMENT.SALE.COMPLETED`
4. Copy Webhook ID

### 1.3 Coinbase Commerce (Optional - for Bitcoin)
1. Create account at https://commerce.coinbase.com/
2. Go to Settings > API Keys
3. Create API key and copy `COINBASE_COMMERCE_API_KEY`
4. Go to Settings > Webhook subscriptions
5. Add webhook: `https://your-app.onrender.com/webhooks/coinbase`
6. Copy Webhook Shared Secret

### 1.4 Email Service (Required)
**Option A: SendGrid (Recommended for production)**
1. Sign up at https://sendgrid.com/
2. Create API key with Mail Send permissions
3. Use these settings:
   ```
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=<your_sendgrid_api_key>
   ```

**Option B: Mailgun**
1. Sign up at https://www.mailgun.com/
2. Get SMTP credentials
3. Use settings from Mailgun dashboard

---

## Step 2: Deploy to Render.com

### 2.1 Create Render Account
1. Go to https://render.com/
2. Sign up with GitHub account
3. Grant access to your `habit-tracker-app` repository

### 2.2 Create PostgreSQL Database
1. Click **New +** > **PostgreSQL**
2. Name: `habitflow-db`
3. Database: `habitflow`
4. User: `habitflow_user` (auto-created)
5. Region: Select closest to your users
6. Plan: **Free** (for testing) or **Starter** (for production)
7. Click **Create Database**
8. **Copy the Internal Database URL** (starts with `postgresql://`)

### 2.3 Create Web Service
1. Click **New +** > **Web Service**
2. Connect your GitHub repository: `habit-tracker-app`
3. Configuration:
   - **Name:** `habitflow` (or your preferred name)
   - **Region:** Same as database
   - **Branch:** `main`
   - **Root Directory:** Leave blank
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free or Starter ($7/month)

### 2.4 Add Environment Variables
Click **Environment** tab and add these variables:

**Flask Configuration:**
```bash
FLASK_ENV=production
SECRET_KEY=<generate-with-python-secrets-token-hex-32>
APP_URL=https://your-app-name.onrender.com
```

**Database:**
```bash
DATABASE_URL=<paste-internal-database-url-from-step-2.2>
```

**Stripe (LIVE keys):**
```bash
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_ID_MONTHLY=price_xxxxx
STRIPE_PRICE_ID_ANNUAL=price_xxxxx
STRIPE_PRICE_ID_LIFETIME=price_xxxxx
```

**PayPal (if using):**
```bash
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=xxxxx
PAYPAL_CLIENT_SECRET=xxxxx
PAYPAL_WEBHOOK_ID=xxxxx
PAYPAL_PLAN_ID_MONTHLY=P-xxxxx
PAYPAL_PLAN_ID_ANNUAL=P-xxxxx
```

**Coinbase Commerce (if using):**
```bash
COINBASE_COMMERCE_API_KEY=xxxxx
COINBASE_COMMERCE_WEBHOOK_SECRET=xxxxx
COINBASE_LIFETIME_PRICE=59.99
```

**Email (SendGrid example):**
```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=apikey
MAIL_PASSWORD=<sendgrid_api_key>
MAIL_DEFAULT_SENDER=HabitFlow <noreply@habitflow.app>
MAIL_MAX_EMAILS=100
```

### 2.5 Deploy
1. Click **Create Web Service**
2. Wait for build and deployment (5-10 minutes)
3. Your app will be available at: `https://your-app-name.onrender.com`

---

## Step 3: Post-Deployment Configuration

### 3.1 Update Webhook URLs
Go back to each payment provider and update webhook URLs with your production URL:

- **Stripe:** `https://your-app-name.onrender.com/webhooks/stripe`
- **PayPal:** `https://your-app-name.onrender.com/webhooks/paypal`
- **Coinbase:** `https://your-app-name.onrender.com/webhooks/coinbase`

### 3.2 Test Webhooks
1. In Stripe Dashboard > Webhooks, click **Send test webhook**
2. Verify the webhook is received successfully
3. Check Render logs for webhook processing

### 3.3 Test Payment Flows
**Stripe Test:**
1. Visit your pricing page
2. Use Stripe test card: `4242 4242 4242 4242`, any future expiry, any CVV
3. Complete checkout
4. Verify subscription is created in database
5. Check email notification is sent

**PayPal Test:**
1. Use PayPal sandbox account
2. Complete checkout
3. Verify subscription in database

### 3.4 Set Up Cron Jobs
**Daily Cleanup Script:**
Add this to Render cron jobs (if available) or use an external cron service like cron-job.org:
```bash
0 2 * * * curl -X POST https://your-app-name.onrender.com/admin/cleanup
```

Or run manually via shell access:
```bash
python cleanup.py
```

---

## Step 4: Custom Domain (Optional)

### 4.1 Purchase Domain
- Namecheap, Google Domains, or any domain registrar
- Recommended: `habitflow.app` or similar

### 4.2 Configure DNS
1. In Render dashboard, go to your web service
2. Click **Settings** > **Custom Domains**
3. Add your domain (e.g., `habitflow.app`)
4. Add CNAME record to your DNS:
   ```
   CNAME: www -> your-app-name.onrender.com
   CNAME: @ -> your-app-name.onrender.com (if supported)
   ```
5. Wait for DNS propagation (5-60 minutes)
6. Render will automatically provision SSL certificate

### 4.3 Update Environment Variables
Update `APP_URL` in Render environment variables:
```bash
APP_URL=https://habitflow.app
```

---

## Step 5: Monitoring & Maintenance

### 5.1 Set Up Monitoring
**Render Built-in Monitoring:**
- View metrics in Render dashboard
- Set up alerts for downtime

**External Monitoring (Optional):**
- UptimeRobot: https://uptimerobot.com/
- Pingdom: https://www.pingdom.com/

### 5.2 Log Monitoring
- View logs in Render dashboard
- Look for errors, failed payments, webhook issues

### 5.3 Database Backups
- Render automatically backs up PostgreSQL databases
- For additional safety, set up manual backups:
  ```bash
  pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
  ```

### 5.4 Security Checks
- [ ] HTTPS enabled (Render auto-configures)
- [ ] Webhook signatures verified
- [ ] Rate limiting active
- [ ] Audit logs being written
- [ ] No secrets in code or logs

---

## Step 6: Production Testing

### 6.1 Functional Testing
- [ ] User registration works
- [ ] Login/logout works
- [ ] Create habits (free tier limit = 3)
- [ ] Upgrade to paid plan
- [ ] Complete checkout (Stripe/PayPal)
- [ ] Verify subscription activation
- [ ] Cancel subscription
- [ ] Resume subscription
- [ ] Export data (GDPR)
- [ ] Delete account (30-day grace period)

### 6.2 Email Testing
- [ ] Payment confirmation emails sent
- [ ] Subscription cancelled emails sent
- [ ] Daily reminder emails sent (if enabled)
- [ ] Welcome email sent on registration

### 6.3 Mobile Testing
- [ ] Test on iPhone (Safari)
- [ ] Test on Android (Chrome)
- [ ] No horizontal scrolling
- [ ] All buttons work
- [ ] Payment flow completes

---

## Step 7: Go Live Checklist

### Pre-Launch
- [ ] All environment variables configured
- [ ] Webhooks registered and tested
- [ ] Payment flows tested end-to-end
- [ ] Email notifications tested
- [ ] Privacy policy and terms accessible
- [ ] Custom domain configured (if using)
- [ ] SSL certificate active
- [ ] Database backups configured
- [ ] Monitoring set up

### Launch Day
- [ ] Announce on social media
- [ ] Submit to Product Hunt (optional)
- [ ] Monitor logs for errors
- [ ] Watch payment processing
- [ ] Respond to user feedback

### Post-Launch (First 48 Hours)
- [ ] Monitor error rates
- [ ] Check payment success rate
- [ ] Verify webhook delivery
- [ ] Watch for spam/abuse
- [ ] Respond to support emails

---

## Troubleshooting

### Payment Not Processing
1. Check webhook delivery in Stripe/PayPal dashboard
2. Verify webhook URL is correct
3. Check Render logs for errors
4. Ensure webhook signature verification is passing

### Email Not Sending
1. Verify MAIL_* environment variables
2. Check SendGrid/Mailgun dashboard for delivery status
3. Look for authentication errors in logs
4. Verify sender email is verified

### Database Connection Issues
1. Check DATABASE_URL is correct
2. Verify database is running in Render dashboard
3. Check connection limits (upgrade plan if needed)

### 500 Internal Server Error
1. Check Render logs for Python errors
2. Verify all environment variables are set
3. Ensure migrations ran successfully
4. Check SECRET_KEY is set

---

## Cost Estimate

**Monthly Costs (Production):**
- Render Web Service: $7/month (Starter plan)
- Render PostgreSQL: $7/month (Starter plan)
- SendGrid Email: $0-15/month (free up to 100 emails/day)
- **Total: $14-30/month**

**Payment Processing Fees:**
- Stripe: 2.9% + $0.30 per transaction
- PayPal: 2.9% + $0.30 per transaction
- Coinbase Commerce: 1% per transaction

---

## Support & Maintenance

**Regular Maintenance:**
- Weekly: Review error logs
- Monthly: Check subscription metrics (MRR, churn)
- Quarterly: Security audit
- Annually: Dependencies update

**Backup Strategy:**
- Database: Automated by Render (daily)
- Code: GitHub repository
- Environment variables: Document in secure location (1Password, etc.)

---

## Success Metrics

Track these KPIs in your admin dashboard:
- **MRR (Monthly Recurring Revenue):** Target growth
- **Churn Rate:** Target < 5% monthly
- **Conversion Rate:** Free to Paid conversion
- **Payment Success Rate:** Target > 98%
- **Email Delivery Rate:** Target > 99%

---

## Conclusion

Your HabitFlow app is now production-ready! 🚀

For support or questions:
- **GitHub Issues:** https://github.com/your-username/habit-tracker-app/issues
- **Email:** support@habitflow.app

Good luck with your launch! 🎉
