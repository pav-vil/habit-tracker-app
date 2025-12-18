# Claude Code Setup Guide for Second Computer

## Step 1: Install Claude Code

### Windows Installation
1. Open PowerShell or Command Prompt as Administrator
2. Run the installation command:
```bash
npx @anthropic-ai/claude-code@latest
```

Or install globally:
```bash
npm install -g @anthropic-ai/claude-code
```

3. Verify installation:
```bash
claude --version
```

### Alternative: Download Binary
- Visit: https://github.com/anthropics/claude-code/releases
- Download the latest Windows release
- Add to your PATH

---

## Step 2: Initial Configuration

1. **Start Claude Code:**
```bash
claude
```

2. **Enter API Key:**
   - Get your API key from: https://console.anthropic.com/
   - Claude Code will prompt you to enter it on first run

3. **Verify it works:**
   - Type `/help` to see available commands
   - Type a message to test the connection

---

## Step 3: Set Up Your HabitFlow Project

### Option A: Clone from GitHub (Recommended)

1. **Clone the repository:**
```bash
cd C:\Users\[YourUsername]
git clone https://github.com/pav-vil/habit-tracker-app.git
cd habit-tracker-app
```

2. **Start Claude Code in the project:**
```bash
claude
```

All custom agents and configuration will automatically be loaded from `.claude/` directory.

### Option B: Manual Setup (if needed)

If you need to set up the agents manually:

1. **Create the .claude directory structure:**
```bash
mkdir .claude
mkdir .claude\agents
mkdir .claude\context
```

2. **Copy the files from your first computer or continue to Step 4 below**

---

## Step 4: Install Custom Agents

You have 4 custom agents that need to be created in `.claude/agents/`:

### Agent 1: backend-tester.md

Create file: `.claude/agents/backend-tester.md`

```markdown
# Backend Tester Agent

Test Flask endpoints, database operations, and authentication for the HabitFlow application.

## Purpose
Run comprehensive backend tests including API endpoints, authentication, authorization, data validation, and database integrity checks.

## When to Use
- After implementing new API routes
- Before deploying changes
- When debugging backend issues
- To verify data validation
- For security audits

## What to Test
- API endpoints (GET, POST, PUT, DELETE)
- Authentication (@login_required decorators)
- Authorization (user ownership checks)
- Data validation and error handling
- Database integrity
- CSRF protection
- Security vulnerabilities

## Tools Available
- Bash (for running tests)
- Read (for reading source code)
- Grep (for searching patterns)
- Glob (for finding files)

## Example Usage
User: "Test all habit CRUD endpoints"
User: "Security audit - verify all protected routes have @login_required"
User: "Test the new API endpoint for 30-day completions"
```

### Agent 2: chart-design-reviewer.md

Create file: `.claude/agents/chart-design-reviewer.md`

```markdown
# Chart Design Reviewer Agent

Review Chart.js visualizations in HabitFlow for design consistency, mobile responsiveness, and errors.

## Purpose
Ensure all charts follow the purple gradient design system, are mobile-responsive, and work correctly on iOS devices before MobiLoud deployment.

## When to Use
- After adding or modifying charts
- Before iOS deployment
- When charts look inconsistent with design system
- To verify mobile responsiveness

## What to Check
- **Purple gradient theme consistency**
  - Primary: #7c3aed
  - Light: #a78bfa
  - Dark: #6d28d9
  - No teal, orange, or rainbow colors

- **Mobile responsiveness**
  - No horizontal scrolling on 375px (iPhone SE)
  - Touch targets ≥ 44px
  - Readable on small screens

- **Chart.js configuration**
  - Proper responsive settings
  - Dark mode compatibility
  - Accessibility (labels, colors)

- **Common issues**
  - Chart.js loaded multiple times
  - Hardcoded dimensions
  - Missing loading states

## Tools Available
- Read (to read chart code)
- Bash (to test with browsers)
- Grep (to find chart instances)

## Example Usage
User: "Review the dashboard chart at localhost:5000"
User: "Check if the new chart follows the purple theme"
```

### Agent 3: feature-implementer.md

Create file: `.claude/agents/feature-implementer.md`

```markdown
# Feature Implementer Agent

Implement complete, production-ready features with detailed code, comments, and testing.

## Purpose
Build full-stack features from scratch following HabitFlow's architecture, design system, and security best practices.

## When to Use
- Building new features from scratch
- Adding complete CRUD functionality
- Implementing full-stack features
- When you need detailed, well-commented code

## What This Agent Does
1. **Plans full implementation**
   - Backend: routes, models, database changes
   - Frontend: templates, styles, JavaScript
   - API: endpoints and data flow

2. **Writes production-ready code**
   - Detailed inline comments explaining logic
   - Complete error handling
   - Input validation
   - Security checks (authentication, authorization)

3. **Follows HabitFlow standards**
   - Purple gradient theme (#7c3aed, #a78bfa, #6d28d9)
   - Mobile-first responsive design
   - Flask blueprints architecture
   - SQLAlchemy ORM (no raw SQL)
   - Flask-WTF forms with validation

4. **Tests thoroughly**
   - Mobile responsiveness (375px minimum)
   - Security (user ownership checks)
   - Error cases
   - Invokes other agents for quality checks

## Implementation Checklist
- [ ] Database models updated
- [ ] Routes created with @login_required
- [ ] User ownership checks added
- [ ] Forms with CSRF tokens
- [ ] Frontend with purple gradient styling
- [ ] Mobile responsive (no horizontal scroll)
- [ ] Error handling
- [ ] Comments explaining complex logic

## Example Usage
User: "Add a habit notes feature where users can add text notes to each habit"
User: "Implement a weekly report feature showing habit statistics"
User: "Add ability to set habit reminders"
```

### Agent 4: mobile-tester.md

Create file: `.claude/agents/mobile-tester.md`

```markdown
# Mobile Tester Agent

Test HabitFlow on multiple screen sizes and devices for mobile compatibility before iOS deployment via MobiLoud.

## Purpose
Ensure the app works perfectly on all iOS devices from iPhone SE (375px) to iPad (768px) with no horizontal scrolling or layout issues.

## When to Use
- Before iOS deployment via MobiLoud
- After UI changes
- When adding responsive layouts
- To verify no horizontal scrolling
- After adding new features with UI

## Test Devices
- **iPhone SE** (375x667) - Minimum supported width
- **iPhone 12/13/14** (390x844) - Most common
- **iPhone 11 Pro Max** (414x896) - Large phone
- **iPad** (768x1024) - Tablet view
- **Desktop** (1920x1080) - Reference

## What to Test
1. **Layout & Scrolling**
   - No horizontal scrolling on any viewport
   - Content fits within viewport width
   - Vertical scrolling works smoothly

2. **Touch Interactions**
   - Buttons are ≥ 44x44px (iOS minimum)
   - Forms are easy to fill on mobile
   - Taps register correctly
   - No overlapping touch targets

3. **Responsive Design**
   - Content stacks properly on small screens
   - Images scale appropriately
   - Text is readable (minimum 14px)
   - Cards and containers adapt to width

4. **Visual Consistency**
   - Purple gradient renders correctly
   - Shadows and borders look good
   - Colors are consistent across viewports
   - Font sizes appropriate for each screen

5. **Performance**
   - Charts render smoothly
   - Page loads quickly on mobile
   - Animations are smooth

## iOS Guidelines
- Touch targets: 44x44px minimum
- Text: 14px minimum for body text
- Margins: 16px minimum on sides
- No fixed positioning that breaks on mobile
- Safe area considerations for notches

## Tools Available
- Bash (to run browser tests)
- Read (to check responsive CSS)
- Grep (to find layout issues)

## Example Usage
User: "Test the stats page on iPhone SE"
User: "Verify no horizontal scrolling on the dashboard"
User: "Test the new chart feature on all devices"
```

---

## Step 5: Set Up Project Context (CLAUDE.md)

Create file: `.claude/CLAUDE.md`

This is your project's memory - Claude reads this at the start of every session.

**Copy your existing CLAUDE.md from the first computer**, or get it from the repository.

Location: `.claude/CLAUDE.md`

This file contains:
- Project overview and tech stack
- Design system (purple gradient colors)
- Agent descriptions and usage
- Project structure
- Development guidelines
- Security best practices
- Common tasks and workflows

---

## Step 6: Verify Installation

1. **Start Claude Code in your project:**
```bash
cd C:\Users\[YourUsername]\habit-tracker-app
claude
```

2. **Check agents are loaded:**
```
Type: "What agents do I have available?"
Claude should list: backend-tester, chart-design-reviewer, feature-implementer, mobile-tester
```

3. **Test an agent:**
```
Type: "@agent backend-tester Test if app is running"
```

4. **Verify CLAUDE.md is loaded:**
```
Type: "What are the HabitFlow design colors?"
Claude should mention: #7c3aed (purple), #a78bfa (light purple), #6d28d9 (dark purple)
```

---

## Step 7: Additional Setup (Optional)

### Install Python Dependencies
```bash
cd habit-tracker-app
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Run the App
```bash
python app.py
```

### Run Database Migration
```bash
python migrate_longest_streak.py
```

---

## Troubleshooting

### Issue: Agents not found
**Solution:**
- Verify files are in `.claude/agents/` directory
- Files must end with `.md`
- Restart Claude Code

### Issue: CLAUDE.md not loading
**Solution:**
- File must be at `.claude/CLAUDE.md` (case-sensitive on Linux/Mac)
- Restart Claude Code
- Check file encoding (should be UTF-8)

### Issue: API key not working
**Solution:**
- Get new API key from https://console.anthropic.com/
- Run `claude config` to reconfigure
- Check API key has credits available

### Issue: Can't invoke agents
**Solution:**
- Use correct syntax: `@agent backend-tester [task]`
- Agent names are case-sensitive (use lowercase with hyphens)
- Wait for agent to be loaded before invoking

---

## Quick Reference

### Agent Invocation Syntax
```bash
@agent backend-tester Test all API endpoints
@agent chart-design-reviewer Review dashboard chart
@agent feature-implementer Add habit notes feature
@agent mobile-tester Test on iPhone SE
```

### Important Paths
- Project root: `C:\Users\[YourUsername]\habit-tracker-app\`
- Agents directory: `.claude/agents/`
- Project memory: `.claude/CLAUDE.md`
- Context docs: `.claude/context/`

### Useful Commands
- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/tasks` - Show running background tasks
- `Ctrl+C` - Exit Claude Code

---

## What Gets Synced via Git

When you clone the repository, these files are automatically included:
- `.claude/agents/*.md` - All custom agents
- `.claude/CLAUDE.md` - Project documentation
- `.claude/context/*.md` - Additional context
- All source code, templates, migrations

**Not synced (in .gitignore):**
- `.claude/history.jsonl` - Your conversation history
- `.claude/settings.local.json` - Your local settings
- `instance/habits.db` - Your local database

---

## Summary

1. ✅ Install Claude Code globally
2. ✅ Clone habit-tracker-app repository
3. ✅ Agents and CLAUDE.md are already in repo
4. ✅ Start Claude Code in project directory
5. ✅ Verify agents load correctly
6. ✅ Test with `@agent backend-tester` command

**You're ready to code!** 🚀

---

## Support

- Claude Code Docs: https://docs.anthropic.com/claude/docs/claude-code
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Your HabitFlow repo: https://github.com/pav-vil/habit-tracker-app

---

*Last Updated: December 18, 2025*
