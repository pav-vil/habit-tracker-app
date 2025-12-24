# Changelog

All notable changes to HabitFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned Features
- Social features (share progress with friends)
- Habit templates (pre-made habits to get started)
- Reminders and notifications
- Export data (CSV, JSON)
- Habit categories and tags
- Multi-language support
- Progressive Web App (PWA) support
- Weekly/monthly goals
- Habit notes and journal entries

---

## [1.4.0] - 2024-12-24

### Added
- **Inline Help Text**: Added contextual help throughout the app
  - Dashboard swipe gesture tips banner (mobile only)
  - Habit form best practices guide with examples
  - Statistics page explanatory tooltips and descriptions
- **Comprehensive CHANGELOG**: Created version history documentation

### Improved
- Enhanced user onboarding with helpful tips on complex features
- Better explanations for statistics (Active Streaks, Heatmap, etc.)
- Clearer guidance on habit creation best practices

---

## [1.3.0] - 2024-12-17

### Added
- **Touch Target Optimization**: All interactive elements now meet WCAG 2.1 AAA standards
  - Minimum 44px height for all buttons and inputs
  - Improved tap targets for mobile devices
  - Better accessibility for touch interactions
- **Comprehensive README**: 584-line documentation covering:
  - Installation guide (Windows, macOS, Linux)
  - Mobile features documentation
  - Swipe gesture tutorial
  - iOS Safari optimizations list
  - Deployment guides (Heroku, Render, MobiLoud)
  - Testing instructions and best practices
  - Security guidelines

### Fixed
- **iOS Safari Rendering Issues**: Complete mobile optimization overhaul
  - Fixed viewport height issues with `-webkit-fill-available`
  - Fixed tap highlight color and autofill styling
  - Fixed backdrop filter support for iOS
  - Added safe area support for notched iPhones (X, 11, 12, 13, 14, 15)
  - Fixed bottom navigation safe area padding
  - Enhanced touch event handling for iOS
  - Prevented zoom on input focus (16px minimum font size)
  - Fixed rubber band scrolling effect
  - Added GPU acceleration for smooth animations

### Improved
- Enhanced swipe gesture detection with better visual feedback
  - Progressive opacity scaling (20px threshold for visual feedback)
  - Reduced swipe threshold to 80px (from 100px)
  - Added pulsing animations on swipe indicators
  - Improved color gradients (green for complete, red for undo)
  - Better touch vs scroll conflict resolution

---

## [1.2.0] - 2024-12-16

### Added
- **Habit Building Guide**: Comprehensive guide page based on science-backed research
  - 7 proven strategies (Start Small, Habit Stacking, Environment Design, etc.)
  - 30-day action plan for building lasting habits
  - Common pitfalls to avoid
  - Recommended resources (Atomic Habits, Tiny Habits, The Power of Habit)
  - Integration with main navigation
  - Accessible to non-logged-in users

### Improved
- Navigation menu updated with "📖 Guide" link
- Added educational content to support user success

---

## [1.1.0] - 2024-12-15

### Added
- **Dark Mode**: Full theme switching with user preference persistence
  - Toggle switch in navigation bar (sun/moon icons)
  - CSS variables for dynamic theming
  - Preference saved to user database
  - Smooth transitions between themes
  - Purple gradient maintained in both modes
  - Chart.js theme adaptation

- **Swipe Gestures**: Touch-friendly habit completion for mobile
  - Swipe right (→) to complete habit instantly
  - Swipe left (←) to undo completion (if completed today)
  - Progressive visual feedback with pulsing indicators
  - Color gradients showing swipe direction (green/red)
  - Smooth bounce animation on completion
  - Tutorial overlay for first-time mobile users
  - LocalStorage persistence for tutorial state

- **Bottom Navigation**: Mobile-optimized thumb-friendly navigation
  - Fixed bottom bar for screens ≤768px
  - 5 main actions: Home, Stats, Add, Guide, About
  - Elevated center "Add" button (56px height)
  - Active state indication with purple highlight
  - Safe area support for notched devices
  - Ripple effect on tap
  - Minimum 48px touch targets

### Improved
- Mobile UX significantly enhanced with gesture controls
- Better accessibility on mobile devices
- Improved one-handed usability with bottom navigation

### Technical
- Added `dark_mode` field to User model
- Created `/habits/dark-mode-toggle` API endpoint
- Auto-migration system updated for database schema changes
- Touch event handling with passive/non-passive listeners
- CSS variables for theme switching

---

## [1.0.0] - 2024-12-01

### Initial Release

#### Core Features
- **User Authentication**: Secure registration, login, and logout
  - Password hashing with werkzeug.security (scrypt)
  - Flask-Login session management
  - CSRF protection on all forms
  - Timezone support for accurate daily tracking

- **Habit Management**: Full CRUD operations
  - Create habits with name, description, and motivation ("why")
  - Edit existing habits
  - Delete habits
  - Archive system (soft delete)
  - View archived habits

- **Daily Tracking**: Mark habits complete with streak tracking
  - One-tap completion
  - Undo completion for today
  - Current streak counter
  - Longest streak record (all-time best)
  - Last completed date tracking

- **Statistics Dashboard**: Visual progress tracking
  - Overview cards (Total Habits, Active Streaks, Longest Streak)
  - 14-day completion trend line chart
  - Current streaks bar chart by habit
  - Best days for habits chart (by day of week)
  - Activity heatmap (GitHub-style, 12 weeks)
  - Detailed habits table with status

- **Data Visualization**: Chart.js integration
  - Purple gradient color scheme (brand consistency)
  - Responsive charts for all screen sizes
  - Loading skeletons for async data
  - Interactive tooltips with custom styling
  - Export to PDF and PNG image

- **Motivational Features**:
  - Daily rotating motivational quotes (30 quotes)
  - Habit motivation field ("why") for personal accountability
  - Streak celebration messages
  - Progress visualization

#### Design System
- **Purple Gradient Theme**: Consistent brand colors
  - Primary: #7c3aed
  - Light: #a78bfa
  - Dark: #6d28d9
  - Background: #1a1a2e
  - Success: #10b981

- **Responsive Design**: Mobile-first approach
  - Bootstrap 5.3 framework
  - Breakpoints: 375px, 768px, 1024px
  - No horizontal scrolling on mobile
  - Optimized for iPhone SE (375px minimum)

- **Accessibility**: WCAG compliance
  - Semantic HTML5 markup
  - ARIA labels on interactive elements
  - Keyboard navigation support
  - Screen reader friendly

#### Technical Stack
- **Backend**: Python 3.9+, Flask 3.0+, SQLAlchemy, Flask-Login, WTForms
- **Frontend**: HTML5, Bootstrap 5.3, Vanilla JavaScript, Chart.js 4.4.1
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Security**: Password hashing, CSRF tokens, SQL injection prevention, XSS protection

#### Database Models
- **User**: Authentication, preferences, timezone
- **Habit**: Name, description, motivation, streaks, timestamps
- **CompletionLog**: Daily completion history for analytics

#### Routes & Blueprints
- **Auth**: `/register`, `/login`, `/logout`
- **Habits**: `/dashboard`, `/habits/add`, `/habits/<id>/edit`, `/habits/<id>/delete`, `/habits/<id>/complete`, `/habits/<id>/undo`, `/habits/<id>/archive`
- **Stats**: `/stats`, `/stats/api/chart-data`
- **Pages**: `/`, `/about`

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|-------------|
| 1.4.0 | 2024-12-24 | Inline help text, tooltips, changelog |
| 1.3.0 | 2024-12-17 | Touch optimization, iOS Safari fixes, comprehensive README |
| 1.2.0 | 2024-12-16 | Habit building guide with science-backed strategies |
| 1.1.0 | 2024-12-15 | Dark mode, swipe gestures, bottom navigation |
| 1.0.0 | 2024-12-01 | Initial release with core functionality |

---

## Migration Notes

### Upgrading to 1.4.0
- No database changes required
- Inline help is automatically displayed to all users

### Upgrading to 1.3.0
- No database changes required
- iOS Safari users will see improved rendering automatically

### Upgrading to 1.2.0
- No database changes required
- New guide page accessible at `/guide`

### Upgrading to 1.1.0
- Database migration required: `dark_mode` field added to `user` table
- Auto-migration runs on app startup (no manual action needed)
- Users will default to light mode (dark_mode=False)

---

## Contributors

- **Paulo** - Lead Developer
- **Claude Code** - AI Development Assistant

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*For detailed installation, usage, and deployment instructions, see [README.md](README.md)*
