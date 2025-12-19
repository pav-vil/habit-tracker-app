# HabitFlow - Render.com Deployment Guide

## Prerequisites
- GitHub account with your HabitFlow repository pushed
- Render.com account (free tier available)

---

## Step 1: Prepare Your Repository

Your repository already has all the necessary files:

✅ `config.py` - Production configuration with PostgreSQL support
✅ `requirements.txt` - All dependencies including gunicorn & psycopg2-binary
✅ `Procfile` - Web server command: `web: gunicorn app:app`
✅ `runtime.txt` - Python 3.12.0 specification
✅ `.env.example` - Environment variable template

**Commit and push to GitHub:**
```bash
git add .
git commit -m "Prepare for Render.com deployment"
git push origin main
```

---

## Step 2: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure database:
   - **Name:** `habitflow-db` (or your preference)
   - **Database:** `habitflow`
   - **User:** `habitflow_user`
   - **Region:** Choose closest to your users
   - **Plan:** Free (or paid for production)
4. Click **"Create Database"**
5. **IMPORTANT:** Copy the **Internal Database URL** (starts with `postgresql://`)
   - You'll use this in the next step

---

## Step 3: Create Web Service on Render

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure web service:

   **Basic Settings:**
   - **Name:** `habitflow-app` (or your preference)
   - **Region:** Same as database
   - **Branch:** `main`
   - **Root Directory:** (leave empty if app is in root)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app` (auto-detected from Procfile)
   - **Plan:** Free (or paid for production)

4. Click **"Advanced"** to add environment variables

---

## Step 4: Configure Environment Variables

Add these in the **Environment Variables** section:

### Required Variables:

| Key | Value | Notes |
|-----|-------|-------|
| `FLASK_ENV` | `production` | Enables ProductionConfig |
| `SECRET_KEY` | `<generate-random-key>` | See generation below |
| `DATABASE_URL` | `<postgres-internal-url>` | From Step 2 |

### Generate SECRET_KEY:
Run this locally:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste as `SECRET_KEY` value.

### Optional Variables:

| Key | Value | Notes |
|-----|-------|-------|
| `REDIS_URL` | `<redis-url>` | If using Redis for rate limiting |

---

## Step 5: Deploy!

1. Click **"Create Web Service"**
2. Render will:
   - Pull your code from GitHub
   - Install dependencies from `requirements.txt`
   - Run database migrations (via `auto_migrate.py`)
   - Start gunicorn server
3. Wait for deployment to complete (usually 2-5 minutes)
4. Your app will be available at: `https://habitflow-app.onrender.com`

---

## Step 6: Initialize Database (First Deploy Only)

Your app uses auto-migration (`auto_migrate.py`), so tables are created automatically on first run. However, if you need to manually initialize:

1. Go to your web service on Render
2. Click **"Shell"** tab
3. Run:
   ```bash
   python init_db.py
   ```

---

## Step 7: Verify Deployment

### Check Application Health:
1. Visit your app URL: `https://your-app-name.onrender.com`
2. Test registration: Create a new account
3. Test login: Log in with your account
4. Create a habit and mark it complete
5. View stats page to verify charts load

### Check Logs:
- Go to Render dashboard → Your web service → **Logs** tab
- Look for any errors or warnings
- Verify database connection messages

---

## Post-Deployment Configuration

### Custom Domain (Optional):
1. In Render dashboard → Your web service → **Settings**
2. Scroll to **Custom Domain**
3. Add your domain (e.g., `habitflow.com`)
4. Follow DNS configuration instructions

### Auto-Deploy on Git Push:
- Render automatically redeploys when you push to `main` branch
- Disable in **Settings** → **Auto-Deploy** if needed

### SSL Certificate:
- Render provides free SSL certificates automatically
- Your app will be available via HTTPS

---

## Environment-Specific Settings

### Development (Local):
```bash
FLASK_ENV=development
DATABASE_URL=sqlite:///habits.db
SECRET_KEY=dev-secret-key-change-in-production
```

### Production (Render):
```bash
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/db  # Auto-provided by Render
SECRET_KEY=<64-character-random-hex-string>
```

---

## Troubleshooting

### Issue: "Application Error" on deployment
**Solution:** Check logs in Render dashboard
- Common causes: Missing environment variables, database connection issues

### Issue: Database migrations fail
**Solution:**
1. SSH into Render shell
2. Run: `python init_db.py` manually
3. Restart web service

### Issue: Static files not loading
**Solution:**
- Check that `static/` folder is committed to Git
- Verify paths in templates use `url_for('static', filename='...')`

### Issue: Session cookies not persisting
**Solution:**
- Verify `SECRET_KEY` is set correctly
- Check that `FLASK_ENV=production` is set (enables secure cookies)

### Issue: Rate limiting not working
**Solution:**
- In-memory rate limiting resets on each deployment
- Use Redis for persistent rate limiting (add Redis service on Render)

---

## Database Backups (Important!)

### Automatic Backups (Paid Plans):
- Render provides automatic daily backups on paid PostgreSQL plans

### Manual Backup:
1. Go to Render dashboard → PostgreSQL database
2. Click **"Shell"** tab
3. Run:
   ```bash
   pg_dump -Fc $DATABASE_URL > backup.dump
   ```
4. Download backup file

### Restore from Backup:
```bash
pg_restore -d $DATABASE_URL backup.dump
```

---

## Monitoring & Maintenance

### View Logs:
```bash
# In Render dashboard → Web Service → Logs tab
# Or use Render CLI:
render logs -f
```

### Restart Service:
- Render dashboard → Web Service → **Manual Deploy** → **Clear build cache & deploy**

### Scale Service:
- Free tier: 1 instance, spins down after 15min inactivity
- Paid tier: Multiple instances, always-on, auto-scaling

---

## Cost Estimate (As of 2025)

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Web Service | ✅ (spins down after 15min) | $7/month (always-on) |
| PostgreSQL | ✅ 90 days, then expires | $7/month (persistent) |
| Redis | ❌ | $10/month |

**Note:** Free tier is great for testing, but production apps should use paid tier for:
- Always-on service (no cold starts)
- Persistent database (doesn't expire)
- More resources (CPU, RAM)

---

## Security Checklist

Before going live:

- [ ] `SECRET_KEY` is strong random value (64+ characters)
- [ ] `FLASK_ENV=production` is set
- [ ] Database credentials are secure (auto-managed by Render)
- [ ] `.env` file is in `.gitignore` (never committed)
- [ ] HTTPS is enabled (automatic on Render)
- [ ] CSRF protection is enabled (already configured in app)
- [ ] Rate limiting is active (already configured in app)
- [ ] Session cookies are secure (configured in ProductionConfig)

---

## Next Steps

1. **Test thoroughly** on Render free tier
2. **Set up monitoring** (Render provides basic metrics)
3. **Configure custom domain** if needed
4. **Upgrade to paid tier** when ready for production traffic
5. **Enable database backups** (paid plan feature)

---

## Support

- **Render Docs:** https://render.com/docs
- **Render Status:** https://status.render.com
- **Community Support:** https://community.render.com

---

**Your HabitFlow app is now production-ready! 🚀**
