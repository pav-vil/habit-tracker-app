from playwright.sync_api import sync_playwright
import time

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # Desktop viewport (1920x1080)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print("Logging in...")
        # Go to login page
        page.goto('http://localhost:5000/login')
        time.sleep(1)

        # Fill in test credentials - try different selectors
        try:
            page.fill('input#email', 'test@habitflow.com')
        except:
            page.fill('input[type="email"]', 'test@habitflow.com')

        try:
            page.fill('input#password', 'password123')
        except:
            page.fill('input[type="password"]', 'password123')

        page.click('button[type="submit"]')
        time.sleep(3)

        print("Taking desktop screenshots...")

        # Stats page
        page.goto('http://localhost:5000/stats')
        time.sleep(5)  # Wait for charts to load
        page.screenshot(path='screenshot_stats_desktop.png', full_page=True)
        print("Stats desktop screenshot saved")

        # Dashboard page
        page.goto('http://localhost:5000/dashboard')
        time.sleep(2)
        page.screenshot(path='screenshot_dashboard_desktop.png', full_page=True)
        print("Dashboard desktop screenshot saved")

        context.close()

        # Mobile viewport (375x667 - iPhone SE)
        context = browser.new_context(viewport={'width': 375, 'height': 667})
        page = context.new_page()

        print("Logging in (mobile)...")
        # Go to login page
        page.goto('http://localhost:5000/login')
        time.sleep(1)

        # Fill in test credentials
        try:
            page.fill('input#email', 'test@habitflow.com')
        except:
            page.fill('input[type="email"]', 'test@habitflow.com')

        try:
            page.fill('input#password', 'password123')
        except:
            page.fill('input[type="password"]', 'password123')

        page.click('button[type="submit"]')
        time.sleep(3)

        print("Taking mobile screenshots...")

        # Stats page mobile
        page.goto('http://localhost:5000/stats')
        time.sleep(5)
        page.screenshot(path='screenshot_stats_mobile.png', full_page=True)
        print("Stats mobile screenshot saved")

        # Dashboard page mobile
        page.goto('http://localhost:5000/dashboard')
        time.sleep(2)
        page.screenshot(path='screenshot_dashboard_mobile.png', full_page=True)
        print("Dashboard mobile screenshot saved")

        browser.close()
        print("\nAll screenshots completed!")

if __name__ == '__main__':
    take_screenshots()
