from playwright.sync_api import sync_playwright
import time

def take_screenshots():
    with sync_playwright() as p:
        # Launch browser in headful mode for debugging
        browser = p.chromium.launch(headless=True)

        # Desktop
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Capture console messages
        console_messages = []
        page.on('console', lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on('pageerror', lambda exc: console_messages.append(f"[ERROR] {exc}"))

        # Just go directly to stats page (will redirect to login if needed)
        print("Going to stats page...")
        page.goto('http://localhost:5000/stats')
        time.sleep(5)

        # Take screenshot of whatever we see
        page.screenshot(path='screenshot_current_desktop.png', full_page=True)
        print("Desktop screenshot saved")

        # Try dashboard
        page.goto('http://localhost:5000/dashboard')
        time.sleep(3)
        page.screenshot(path='screenshot_current2_desktop.png', full_page=True)

        # Mobile
        page = browser.new_page(viewport={'width': 375, 'height': 667})
        page.on('console', lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))

        page.goto('http://localhost:5000/stats')
        time.sleep(5)
        page.screenshot(path='screenshot_current_mobile.png', full_page=True)
        print("Mobile screenshot saved")

        # Save console output
        with open('console_log.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(console_messages) if console_messages else 'No console messages')

        print("Console log saved")
        print(f"Captured {len(console_messages)} console messages")

        browser.close()

if __name__ == '__main__':
    take_screenshots()
