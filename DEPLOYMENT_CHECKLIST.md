# HabitFlow - Render.com Deployment Checklist

## ✅ Production Config Files Ready

All files have been created/updated for Render.com deployment:

### 1. **config.py** ✅
- `DevelopmentConfig` class for local development
- `ProductionConfig` class for Render deployment
- Automatic `postgres://` to `postgresql://` conversion for SQLAlchemy
- Environment variable support: `SECRET_KEY`, `DATABASE_URL`, `FLASK_ENV`
- Secure session settings for production (HTTPS-only cookies)

### 2. **requirements.txt** ✅
Contains all dependencies:
- Flask 3.1.0
- SQLAlchemy 2.0.23
- gunicorn 21.2.0 (production server)
- psycopg2-binary 2.9.9 (PostgreSQL driver)
- python-dotenv 1.0.0 (environment variables)
- Flask-Login, Flask-WTF, Flask-Limiter (security)

### 3. **Procfile** ✅
```
web: gunicorn app:app
```
Tells Render how to start your production server.

### 4. **runtime.txt** ✅
```
python-3.12.0
```
Specifies Python version for Render.

### 5. **.env.example** ✅
Updated with Render-specific deployment notes:
- `FLASK_ENV` - Set to `production` on Render
- `SECRET_KEY` - Generate random 64-char hex string
- `DATABASE_URL` - Auto-populated by Render PostgreSQL
- `REDIS_URL` - Optional, for production rate limiting

### 6. **app.py** ✅ (Updated)
**Changes made:**
- Now loads config from `config.py` based on `FLASK_ENV`
- Uses environment variables instead of hardcoded values
- Rate limiter uses config value for storage URI

**Before:**
```python
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
```

**After:**
```python
from config import config
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])
```

### 7. **RENDER_DEPLOYMENT_GUIDE.md** ✅ (New)
Complete step-by-step guide covering:
- Creating PostgreSQL database on Render
- Setting up web service
- Configuring environment variables
- Database initialization
- Troubleshooting common issues
- Security checklist
- Cost estimates

---

## 🚀 Quick Deployment Steps

### 1. Generate SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output - you'll need it for Render.

### 2. Push to GitHub
```bash
git add .
git commit -m "Configure for Render.com deployment"
git push origin main
```

### 3. Create PostgreSQL Database on Render
1. Go to https://dashboard.render.com/
2. **New +** → **PostgreSQL**
3. Name: `habitflow-db`
4. Create database
5. **Copy Internal Database URL**

### 4. Create Web Service on Render
1. **New +** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - Name: `habitflow-app`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### 5. Add Environment Variables
In Render web service settings:

| Variable | Value |
|----------|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | `<your-generated-key>` |
| `DATABASE_URL` | `<postgres-internal-url>` |

### 6. Deploy!
Click **"Create Web Service"** - Render will build and deploy automatically.

Your app will be live at: `https://your-app-name.onrender.com`

---

## 🔍 Testing Your Deployment

Once deployed, test these features:

- [ ] Visit homepage - Should load without errors
- [ ] Register new account - Creates user in PostgreSQL
- [ ] Login - Session persists across page loads
- [ ] Create habit - Saves to database
- [ ] Mark habit complete - Updates completion status
- [ ] View dashboard - 30-day chart renders correctly
- [ ] View stats page - All 4 charts load properly
- [ ] Archive habit - Soft delete works
- [ ] Logout - Session cleared properly

---

## ⚙️ Environment Variables Reference

### Local Development (.env file):
```bash
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///habits.db
```

### Production (Render Environment Variables):
```bash
FLASK_ENV=production
SECRET_KEY=<64-char-random-hex>
DATABASE_URL=postgresql://user:pass@host:5432/db  # Auto-provided
```

---

## 🛡️ Security Checklist

Before going live:

- [ ] `FLASK_ENV=production` set on Render
- [ ] Strong random `SECRET_KEY` (64+ characters)
- [ ] `.env` file NOT committed to Git (in `.gitignore`)
- [ ] HTTPS enabled (automatic on Render)
- [ ] CSRF protection active (already configured)
- [ ] Rate limiting enabled (already configured)
- [ ] Session cookies secure (configured in ProductionConfig)
- [ ] Database credentials secure (managed by Render)

---

## 📊 What Happens in Production?

### DevelopmentConfig (Local):
- `DEBUG = True` - Shows detailed error pages
- `SQLite` database - File-based, single user
- `SESSION_COOKIE_SECURE = False` - Works over HTTP
- Session lifetime: 24 hours

### ProductionConfig (Render):
- `DEBUG = False` - Generic error pages (security)
- `PostgreSQL` database - Robust, multi-user
- `SESSION_COOKIE_SECURE = True` - HTTPS only
- Session lifetime: 1 hour
- Automatic `postgres://` → `postgresql://` conversion

---

## 🔧 Troubleshooting

### "Application Error" after deployment:
1. Check Render logs: Dashboard → Logs tab
2. Verify all environment variables are set
3. Ensure `FLASK_ENV=production`

### Database connection fails:
1. Verify `DATABASE_URL` is set correctly
2. Check PostgreSQL service is running
3. Confirm internal database URL is used (not external)

### Charts not loading:
1. Check browser console for JavaScript errors
2. Verify Chart.js CDN is accessible
3. Test API endpoint: `/api/chart-data`

### Session not persisting:
1. Verify `SECRET_KEY` is set
2. Check `FLASK_ENV=production` enables secure cookies
3. Ensure you're accessing via HTTPS

---

## 📚 Additional Resources

- **Full Deployment Guide:** `RENDER_DEPLOYMENT_GUIDE.md`
- **Environment Variables:** `.env.example`
- **Configuration Classes:** `config.py`
- **Render Documentation:** https://render.com/docs/deploy-flask

---

## 💡 Pro Tips

1. **Use Render's free tier** for testing before upgrading
2. **Monitor logs** during first deployment to catch issues early
3. **Test locally with PostgreSQL** before deploying (optional but recommended)
4. **Enable auto-deploy** to automatically redeploy on Git push
5. **Set up custom domain** for professional appearance

---

**Ready to deploy? Follow the steps above and your HabitFlow app will be live in minutes! 🎉**

For detailed instructions, see: `RENDER_DEPLOYMENT_GUIDE.md`
