# HabitFlow - Build Better Habits 🌱

<div align="center">

**A beautiful, mobile-first habit tracking web application built with Flask and deployed as an iOS app.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Mobile](#-mobile-features) • [Deployment](#-deployment)

</div>

---

## 📖 Overview

HabitFlow helps you build lasting habits through consistent daily tracking, visual progress monitoring, and science-backed strategies. Whether you're trying to exercise more, read daily, or develop any positive routine, HabitFlow makes it easy and enjoyable.

### Why HabitFlow?

- **🎯 Simple & Focused** - Track what matters without complexity
- **📱 Mobile-First** - Optimized for iOS with swipe gestures and thumb-friendly navigation
- **🌙 Dark Mode** - Easy on the eyes, day or night
- **📊 Visual Progress** - Charts and heatmaps show your journey
- **🔥 Streak Tracking** - Stay motivated with daily streaks
- **📚 Built-in Guide** - Science-backed habit-building strategies

---

## ✨ Features

### Core Functionality

- ✅ **Habit Management** - Create, edit, delete, and archive habits
- ✅ **Daily Tracking** - Mark habits complete with one tap or swipe
- ✅ **Streak Tracking** - Current streaks and all-time best records
- ✅ **Statistics Dashboard** - Visual charts and completion rates
- ✅ **Motivational Quotes** - Daily inspiration to keep you going
- ✅ **User Authentication** - Secure login with password hashing
- ✅ **Timezone Support** - Tracks completions in your local timezone

### Mobile Features 📱

#### Swipe Gestures
- **Swipe Right →** Complete a habit instantly
- **Swipe Left ←** Undo completion (if completed today)
- Progressive visual feedback with pulsing indicators
- Works perfectly on iOS Safari

#### Bottom Navigation
- Fixed thumb-friendly navigation bar
- 5 main actions: Home, Stats, Add Habit, Guide, About
- Elevated center "Add" button for quick access
- Active state indication
- Safe area support for notched iPhones

#### Dark Mode
- Toggle between light and dark themes
- Preference saved to your account
- Smooth transitions
- Purple gradient theme maintained

### Advanced Features

- **📈 30-Day Completion Chart** - See your progress over time
- **🗓️ GitHub-Style Heatmap** - Visual representation of your consistency
- **📝 Habit Motivation ("Why")** - Remember why you started
- **🔍 Search & Filter** - Find habits quickly
- **📦 Archive System** - Hide completed goals without losing data
- **♿ Accessible** - WCAG 2.1 AAA compliant (44px+ touch targets)

---

## 🎬 Demo

### Desktop View
Beautiful purple gradient theme with responsive cards and statistics.

### Mobile View
- Swipe gestures for quick completion
- Bottom navigation for thumb reach
- Dark mode support
- Tutorial overlay for first-time users

---

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/pav-vil/habit-tracker-app.git
   cd habit-tracker-app
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```
   Or simply run the app (auto-migration will handle it):
   ```bash
   python app.py
   ```

5. **Access the application**
   ```
   Open your browser to: http://localhost:5000
   ```

### Environment Variables (Optional)

Create a `.env` file for custom configuration:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/habits.db
FLASK_ENV=development
```

---

## 📱 Usage

### Getting Started

1. **Register an Account**
   - Click "Register" on the homepage
   - Enter your email and password
   - Set your timezone (for accurate daily tracking)

2. **Create Your First Habit**
   - Click "Add Habit" or the floating "+" button
   - Enter habit name (e.g., "Morning Exercise")
   - Add description and motivation (optional)
   - Click "Create Habit"

3. **Track Daily Progress**
   - **Desktop:** Click "Complete Today" button
   - **Mobile:** Swipe right on the habit card →
   - Watch your streak grow! 🔥

4. **View Your Progress**
   - Navigate to "Stats" to see charts
   - Check completion rates
   - View 30-day trends
   - Analyze your heatmap

### Mobile Usage (iOS)

#### Swipe Gestures Tutorial

When you first open the app on mobile, you'll see a tutorial explaining:

- **→ Swipe Right** - Completes the habit (green ✓ indicator)
- **← Swipe Left** - Undos completion if done today (red ↶ indicator)

**Visual Feedback:**
- Icons appear and pulse as you swipe
- Color gradients show swipe direction (green/red)
- Smooth bounce animation on completion

**Tips:**
- Swipe at least 80px to trigger action
- Quick swipes work best (< 500ms)
- Vertical scrolling still works normally
- You can always use buttons if you prefer

#### Bottom Navigation

On mobile (≤768px), the main navigation moves to the bottom:

- **🏠 Home** - Dashboard with all habits
- **📊 Stats** - Charts and analytics
- **+ Add** - Create new habit (elevated center button)
- **📖 Guide** - How to build lasting habits
- **ℹ️ About** - App information

**Features:**
- 48px minimum touch targets (thumb-friendly)
- Active state shows current page
- Works on notched iPhones (safe areas)
- Ripple effect on tap

#### Dark Mode

Toggle dark mode from the navbar (sun ☀️ / moon 🌙 icon):

- **Light Mode:** Purple gradients with white cards
- **Dark Mode:** Deep blue/purple with dark cards
- Preference saved to your account
- Works across all pages

---

## 🏗️ Project Structure

```
habit-tracker-app/
├── app.py                      # Main Flask application
├── models.py                   # Database models (User, Habit, Log)
├── forms.py                    # WTForms for validation
├── habits.py                   # Habits blueprint (CRUD routes)
├── stats.py                    # Statistics and analytics routes
├── auth.py                     # Authentication routes
├── auto_migrate.py             # Automatic database migrations
├── requirements.txt            # Python dependencies
├── instance/
│   └── habits.db              # SQLite database (auto-created)
├── templates/
│   ├── base.html              # Base template with navigation
│   ├── index.html             # Landing page
│   ├── dashboard.html         # Main habits dashboard
│   ├── stats.html             # Statistics with charts
│   ├── habit_guide.html       # How to build habits guide
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   └── ...
├── static/
│   ├── css/                   # Custom stylesheets (if any)
│   └── js/                    # JavaScript files (if any)
└── .claude/
    ├── CLAUDE.md              # AI assistant context
    └── agents/                # Agent configurations
```

---

## 🎨 Design System

### Color Theme: Purple Gradient

```css
--primary: #7c3aed;           /* Purple */
--primary-light: #a78bfa;     /* Light purple */
--primary-dark: #6d28d9;      /* Dark purple */
--background: #1a1a2e;        /* Dark background */
--text: #e5e7eb;              /* Light gray text */
--success: #10b981;           /* Green for success */
```

### Typography

- **Font Family:** 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Base Size:** 16px (prevents iOS zoom on input focus)
- **Headings:** 700 weight with purple accents

### Components

- **Cards:** 15px border-radius, subtle shadows
- **Buttons:** 44px minimum height, 8px border-radius
- **Inputs:** 44px height, 16px font size
- **Icons:** Emoji-based for universal compatibility

---

## 🛠️ Technology Stack

### Backend
- **Python 3.9+** - Modern Python features
- **Flask 3.0+** - Lightweight web framework
- **SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **WTForms** - Form validation
- **Werkzeug** - Password hashing (scrypt)

### Frontend
- **HTML5** - Semantic markup
- **Bootstrap 5.3** - Responsive framework
- **Vanilla JavaScript** - No dependencies
- **Chart.js 4.4.1** - Data visualization
- **CSS Variables** - Dynamic theming

### Database
- **SQLite** - Development (auto-migration)
- **PostgreSQL** - Production ready (Heroku compatible)

### Deployment
- **MobiLoud** - iOS app deployment
- **Heroku** - Web hosting (optional)
- **Render** - Alternative hosting

---

## 📱 Mobile Features

### iOS Safari Optimizations

HabitFlow is extensively optimized for iOS Safari:

#### Viewport & Layout
- ✅ `viewport-fit=cover` for safe area support
- ✅ `-webkit-fill-available` fixes address bar issues
- ✅ No zoom on input focus (16px minimum)
- ✅ Proper safe area insets for notched devices

#### Touch & Gestures
- ✅ `-webkit-tap-highlight-color: transparent`
- ✅ Touch event handling with `passive: false` for preventDefault
- ✅ Momentum scrolling (`-webkit-overflow-scrolling: touch`)
- ✅ No rubber band effect (`overscroll-behavior-y: none`)

#### Performance
- ✅ GPU acceleration (`transform: translateZ(0)`)
- ✅ Hardware-accelerated animations
- ✅ Optimized re-renders with `will-change`

#### Forms & Inputs
- ✅ Custom autofill styling (matches dark mode)
- ✅ `-webkit-appearance: none` for custom buttons
- ✅ Font smoothing (`-webkit-font-smoothing: antialiased`)

### Supported Devices

**Tested and optimized for:**
- iPhone SE (375px) - Minimum width
- iPhone 12/13/14 (390px) - Standard
- iPhone 14 Pro/15 Pro (Dynamic Island)
- iPhone X/11/12/13/14/15 (Notched models)
- iPad (768px+) - Tablet view

---

## 🚀 Deployment

### Deploy to Heroku

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku

   # Windows
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and create app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   heroku config:set FLASK_ENV=production
   ```

5. **Deploy**
   ```bash
   git push heroku main
   heroku run python init_db.py
   heroku open
   ```

### Deploy to Render

1. Create a `render.yaml` file (see example in repo)
2. Connect your GitHub repository to Render
3. Render will auto-deploy on push to main

### iOS App (MobiLoud)

1. Deploy web app to production URL
2. Sign up for MobiLoud account
3. Enter your web app URL
4. Configure iOS settings
5. Submit to App Store

**Important:** All mobile features work perfectly in web view:
- ✅ Swipe gestures
- ✅ Dark mode
- ✅ Bottom navigation
- ✅ Safe area support

---

## 🧪 Testing

### Manual Testing

```bash
# Run development server
python app.py

# Access at http://localhost:5000
```

**Test Checklist:**
- [ ] User registration and login
- [ ] Create, edit, delete habits
- [ ] Complete habits (button and swipe)
- [ ] Undo completion
- [ ] View statistics and charts
- [ ] Dark mode toggle
- [ ] Mobile responsive design
- [ ] Swipe tutorial on first visit

### Mobile Testing (Chrome DevTools)

1. Open DevTools (F12)
2. Toggle device toolbar
3. Select iPhone SE (375px) or iPhone 12
4. Test all touch interactions
5. Verify swipe gestures work
6. Check bottom navigation
7. Test dark mode

### Automated Testing

```bash
# Install pytest (if not already installed)
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=app tests/
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce
- Provide screenshots if UI-related
- Mention your browser/device

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use 4 spaces for indentation
- Add docstrings to functions
- Comment complex logic
- Test on mobile before submitting

---

## 📚 User Guide

### How to Build Lasting Habits

HabitFlow includes a comprehensive guide based on science-backed research:

**Access the guide:**
- Navigate to "📖 Guide" in the navigation menu
- Read strategies from James Clear, BJ Fogg, and more
- Follow the 30-day action plan
- Apply proven techniques like habit stacking

**Key Principles:**
1. **Start Small** - Begin with tiny habits
2. **Be Consistent** - Never miss twice
3. **Track Progress** - What gets measured gets managed
4. **Stack Habits** - Link new habits to existing ones
5. **Design Environment** - Make good habits obvious

---

## 🔒 Security

- **Password Hashing:** Werkzeug scrypt (255 characters)
- **CSRF Protection:** WTForms tokens on all forms
- **SQL Injection:** SQLAlchemy ORM prevents attacks
- **XSS Protection:** Jinja2 auto-escaping
- **Authorization:** User ownership checks on all queries
- **Session Security:** Flask-Login secure cookies

### Best Practices

- Never commit `.env` files
- Use strong `SECRET_KEY` in production
- Enable HTTPS in production
- Regular dependency updates
- Database backups

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **James Clear** - Atomic Habits methodology
- **BJ Fogg** - Tiny Habits research
- **Charles Duhigg** - The Power of Habit insights
- **Bootstrap Team** - Responsive framework
- **Chart.js** - Beautiful charts
- **Flask Community** - Excellent documentation

---

## 📞 Support

- **Documentation:** Read this README thoroughly
- **Issues:** [GitHub Issues](https://github.com/pav-vil/habit-tracker-app/issues)
- **Guide:** Built-in "How to Build Habits" guide in the app

---

## 🗺️ Roadmap

### Planned Features

- [ ] Social features (share progress with friends)
- [ ] Habit templates (pre-made habits to get started)
- [ ] Reminders and notifications
- [ ] Export data (CSV, JSON)
- [ ] Habit categories and tags
- [ ] Multi-language support
- [ ] Progressive Web App (PWA) support
- [ ] Weekly/monthly goals
- [ ] Habit notes and journal entries

### Recently Added ✨

- ✅ Swipe gestures for mobile completion
- ✅ Dark mode with user preference
- ✅ Bottom navigation for thumb reach
- ✅ iOS Safari optimizations
- ✅ Safe area support for notched devices
- ✅ Comprehensive habit guide
- ✅ Touch target optimization (44px+)
- ✅ Swipe tutorial for first-time users

---

<div align="center">

**Built with ❤️ by Paulo**

**Powered by Claude Code**

[⬆ Back to Top](#habitflow---build-better-habits-)

</div>
