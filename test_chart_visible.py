"""
Quick Playwright test to verify 30-day chart is visible on dashboard
"""
from playwright.sync_api import sync_playwright
import time

def test_chart_visible():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("[TEST] Testing chart visibility on dashboard...")

        try:
            # Navigate to app
            page.goto('http://localhost:5000')
            print("[OK] App loaded")

            # Login
            page.goto('http://localhost:5000/auth/login')
            page.fill('input[name="email"]', 'test@example.com')
            page.fill('input[name="password"]', 'password123')
            page.click('button[type="submit"]')
            time.sleep(1)
            print("[OK] Logged in")

            # Go to dashboard
            page.goto('http://localhost:5000/habits/dashboard')
            time.sleep(2)
            print("[OK] Dashboard loaded")

            # Check if chart container exists
            chart_card = page.locator('.chart-card')
            if chart_card.count() > 0:
                print("[OK] Chart card found!")
            else:
                print("[FAIL] Chart card NOT found")

            # Check if chart title exists
            chart_title = page.locator('.chart-title')
            if chart_title.count() > 0:
                title_text = chart_title.text_content()
                print(f"[OK] Chart title found: '{title_text}'")
            else:
                print("[FAIL] Chart title NOT found")

            # Check if canvas exists
            canvas = page.locator('#completionTrendChart')
            if canvas.count() > 0:
                print("[OK] Chart canvas found!")

                # Check if canvas is visible
                if canvas.is_visible():
                    print("[OK] Chart canvas is VISIBLE!")
                else:
                    print("[FAIL] Chart canvas exists but is HIDDEN")
            else:
                print("[FAIL] Chart canvas NOT found")

            # Check if loading spinner is gone
            loading = page.locator('#chartLoading')
            if loading.count() > 0:
                if loading.is_visible():
                    print("[WARNING] Loading spinner still visible (chart may be loading)")
                else:
                    print("[OK] Loading spinner hidden (chart loaded)")

            # Check for longest streak badges
            longest_badges = page.locator('.longest-streak-badge')
            count = longest_badges.count()
            print(f"[OK] Found {count} longest streak badges")

            # Take screenshot
            page.screenshot(path='test_chart_verification.png')
            print("[OK] Screenshot saved: test_chart_verification.png")

            # Wait a bit to see the result
            time.sleep(3)

            print("\n[SUCCESS] Test complete! Check the browser and screenshot.")

        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            page.screenshot(path='test_error.png')

        finally:
            browser.close()

if __name__ == '__main__':
    test_chart_visible()
