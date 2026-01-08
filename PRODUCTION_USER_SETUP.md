# Production User Setup Guide

## Create habitprueba@aol.co Account in Production

Follow these steps to create the user account in your production environment on Render.

---

## Method 1: Using Render Console (Recommended)

### Step 1: Access Render Dashboard
1. Go to https://dashboard.render.com/
2. Log in to your account
3. Find your **habit-tracker-app** web service
4. Click on it to open the service details

### Step 2: Open Shell Console
1. In the left sidebar, click **"Shell"** or **"Console"**
2. Wait for the terminal to connect (you'll see a command prompt)

### Step 3: Run the User Creation Script
Copy and paste this command into the Render console:

```bash
python create_production_user.py
```

### Step 4: Verify Success
You should see output like:

```
Creating user account: habitprueba@aol.co
✓ User created successfully

==================================================
PRODUCTION ACCOUNT READY
==================================================
Email:        habitprueba@aol.co
Password:     Prueba123
Verified:     ✓ YES
Tier:         free
Habit Limit:  3
==================================================
```

### Step 5: Test Login
1. Go to your production URL (e.g., `https://habitflow.onrender.com`)
2. Click **Login**
3. Enter credentials:
   - Email: `habitprueba@aol.co`
   - Password: `Prueba123`

---

## Method 2: Using Local Connection to Production DB

If you have the production DATABASE_URL, you can create the user locally:

### Step 1: Set Environment Variable
```bash
# Get DATABASE_URL from Render dashboard (Environment tab)
export DATABASE_URL="postgresql://user:password@hostname/database"
```

### Step 2: Run Script Locally
```bash
cd habit-tracker-app
python create_production_user.py
```

---

## Method 3: Direct PostgreSQL Command

If you prefer SQL, connect to the production database and run:

```sql
-- Connect to your PostgreSQL database first
-- Then run these commands:

INSERT INTO "user" (
    email,
    password_hash,
    timezone,
    subscription_tier,
    subscription_status,
    habit_limit,
    created_at
) VALUES (
    'habitprueba@aol.co',
    'scrypt:32768:8:1$...',  -- Use password_hash from local test
    'America/Costa_Rica',
    'free',
    'active',
    3,
    NOW()
);
```

**Note:** You'll need to generate the password_hash first by running Python locally:

```python
from werkzeug.security import generate_password_hash
print(generate_password_hash('Prueba123'))
```

---

## Account Credentials

Once created, the account will have these credentials:

| Field | Value |
|-------|-------|
| **Email** | habitprueba@aol.co |
| **Password** | Prueba123 |
| **Subscription** | Free (3 habits max) |
| **Timezone** | America/Costa_Rica |

---

## Troubleshooting

### Error: "User already exists"
- The script will automatically reset the password
- No action needed - just use the new password: `Prueba123`

### Error: "Connection refused" or "Database error"
- Check that DATABASE_URL is correctly set in Render environment variables
- Verify the PostgreSQL add-on is running
- Check Render logs for detailed error messages

### Can't access Render console
- Ensure you're logged in to the correct Render account
- Check that the web service is running (not suspended)
- Try refreshing the browser or using incognito mode

### Script not found
- Make sure you've deployed the latest code with `git push`
- Render auto-deploys from GitHub when you push
- Wait for the deployment to complete (check "Events" tab)

---

## Security Notes

⚠️ **Important:**
- This password (`Prueba123`) is a **temporary test password**
- User should change it after first login via Profile > Edit
- Never share production credentials publicly
- Consider using a password manager for production accounts

---

## Next Steps After Account Creation

1. ✅ Login to production with new credentials
2. ✅ Verify all features work (create habits, track completions)
3. ✅ Change password via Profile > Edit (recommended)
4. ✅ Configure timezone if needed
5. ✅ Test email notifications (if configured)

---

**Need Help?**
- Check Render logs: Dashboard > Logs tab
- Review app logs for errors
- Verify DATABASE_URL is correctly set
- Contact support if persistent issues occur
