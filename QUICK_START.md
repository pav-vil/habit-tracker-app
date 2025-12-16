# HabitFlow - Quick Start Guide

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/pav-vil/habit-tracker-app.git
cd habit-tracker-app
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables (Optional for Development)
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values (or use defaults for development)
```

### 5. Run Database Migration
```bash
# If you have an existing database
python migrate_add_archived.py

# If new installation, skip this step - DB will be created automatically
```

### 6. Run the Application
```bash
python app.py
```

Visit: http://localhost:5000

### 7. Create Your First Account
1. Click "Register"
2. Enter email and password (min 8 chars, 1 uppercase, 1 number)
3. Select your timezone
4. Start tracking habits!

---

## Production Deployment

### Option 1: Heroku (Recommended for Beginners)

```bash
# 1. Install Heroku CLI (if not installed)
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login to Heroku
heroku login

# 3. Create app
heroku create your-app-name

# 4. Add PostgreSQL database
heroku addons:create heroku-postgresql:mini

# 5. Set secret key
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 6. Deploy
git push heroku main

# 7. Run migration
heroku run python migrate_add_archived.py

# 8. Open your app
heroku open
```

**Cost:** Free tier available

### Option 2: Railway (Modern & Fast)

```bash
# 1. Go to https://railway.app
# 2. Click "Start a New Project"
# 3. Choose "Deploy from GitHub repo"
# 4. Select your repository
# 5. Add PostgreSQL database from Railway
# 6. Set environment variables:
#    - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")
#    - FLASK_ENV=production
# 7. Railway auto-deploys on push to main
```

**Cost:** $5/month free credit

### Option 3: Render

```bash
# 1. Go to https://render.com
# 2. Click "New +" → "Web Service"
# 3. Connect your GitHub repository
# 4. Configure:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: gunicorn app:app
# 5. Add PostgreSQL database
# 6. Set environment variables (same as Railway)
# 7. Deploy!
```

**Cost:** Free tier available

---

## Testing Checklist

After deployment, test these features:

### User Management
- [ ] Register new account
- [ ] Login
- [ ] Logout
- [ ] Password validation works

### Habit Management
- [ ] Create new habit
- [ ] View habits on dashboard
- [ ] Edit habit
- [ ] Complete habit (streak increases)
- [ ] Undo completion (streak decreases)
- [ ] Archive habit
- [ ] View archived habits
- [ ] Restore archived habit
- [ ] Delete habit permanently

### UI/UX
- [ ] Statistics show correctly
- [ ] Pagination works (if 10+ habits)
- [ ] Confirmation dialogs appear
- [ ] Mobile responsive
- [ ] Timezone handling works

### Security
- [ ] Rate limiting works (try 6 failed logins)
- [ ] CSRF protection works
- [ ] Cannot access other users' habits

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Database migration issues
```bash
# Delete database and start fresh
rm habits.db
python app.py
```

### Port already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

### Heroku "Application Error"
```bash
# Check logs
heroku logs --tail

# Common fixes:
heroku config:set SECRET_KEY=your-secret-key
heroku restart
```

---

## Key Features

✅ **User Authentication:** Secure login/registration with password hashing
✅ **Habit Tracking:** Create and track daily habits
✅ **Streak Counting:** Automatic streak calculation with timezone support
✅ **Undo Function:** Accidentally marked complete? Undo it!
✅ **Habit Archiving:** Hide habits without losing data
✅ **Statistics Dashboard:** Track your progress at a glance
✅ **Pagination:** Handles large numbers of habits efficiently
✅ **Security:** CSRF protection, rate limiting, input validation
✅ **Mobile Friendly:** Responsive design works on all devices

---

## Need Help?

- **Documentation:** See `DEPLOYMENT.md` for detailed deployment guide
- **Issues:** Report bugs on GitHub Issues
- **Code:** Check `PROJECT_STATUS.md` for development roadmap

---

**Happy Habit Tracking! 🎯**
