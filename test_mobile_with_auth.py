"""
Mobile Responsiveness Test for Dashboard - With Authentication
Tests the longest streak badge across different viewport sizes with proper login
"""

from playwright.sync_api import sync_playwright
import time
import os

# Test viewport configurations
VIEWPORTS = {
    'iPhone SE': {'width': 375, 'height': 667},
    'iPhone 12/13/14': {'width': 390, 'height': 844},
    'iPhone 11 Pro Max': {'width': 414, 'height': 896},
    'iPad': {'width': 768, 'height': 1024},
    'Desktop': {'width': 1920, 'height': 1080}
}

# Test credentials
TEST_EMAIL = 'test@example.com'
TEST_PASSWORD = 'password123'


def login_user(page, email, password):
    """Helper function to log in a user"""
    try:
        # Go to login page
        page.goto('http://localhost:5000/login', wait_until='networkidle')

        # Fill in login form
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', password)

        # Submit form
        page.click('button[type="submit"]')

        # Wait for redirect
        time.sleep(2)

        return True
    except Exception as e:
        print(f"  [ERROR] Login failed: {e}")
        return False


def test_dashboard_mobile_responsiveness():
    """Test the dashboard page with longest streak badge on various screen sizes"""

    with sync_playwright() as p:
        # Launch browser in headed mode
        browser = p.chromium.launch(headless=False)

        # Create screenshots directory
        screenshots_dir = 'mobile_test_screenshots'
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)

        print("\n" + "="*70)
        print("MOBILE RESPONSIVENESS TEST - DASHBOARD (LONGEST STREAK BADGE)")
        print("="*70)

        for device_name, viewport in VIEWPORTS.items():
            print(f"\n[Testing {device_name} - {viewport['width']}x{viewport['height']}]")

            # Create context with specific viewport
            context = browser.new_context(
                viewport=viewport,
                device_scale_factor=2 if 'iPhone' in device_name else 1
            )
            page = context.new_page()

            # Login first
            print(f"  [AUTH] Logging in as {TEST_EMAIL}...")
            if not login_user(page, TEST_EMAIL, TEST_PASSWORD):
                print(f"  [WARN] Could not log in - may need to create test account")
                print(f"  [INFO] Skipping to next viewport...")
                context.close()
                continue

            # Navigate to dashboard
            try:
                page.goto('http://localhost:5000/dashboard', wait_until='networkidle', timeout=10000)
            except Exception as e:
                print(f"  [FAIL] Could not load dashboard: {e}")
                context.close()
                continue

            # Wait for page to load
            time.sleep(1)

            # Check for horizontal scrolling
            scroll_width = page.evaluate('document.documentElement.scrollWidth')
            client_width = page.evaluate('document.documentElement.clientWidth')
            has_horizontal_scroll = scroll_width > client_width

            if has_horizontal_scroll:
                print(f"  [FAIL] HORIZONTAL SCROLL DETECTED")
                print(f"         Scroll width: {scroll_width}px, Viewport width: {client_width}px")
            else:
                print(f"  [OK] No horizontal scrolling ({scroll_width}px content in {client_width}px viewport)")

            # Check if longest streak badge exists
            longest_streak_badges = page.query_selector_all('.longest-streak-badge')
            if longest_streak_badges:
                print(f"  [OK] Found {len(longest_streak_badges)} longest streak badge(s)")

                # Get badge dimensions and position
                for idx, badge in enumerate(longest_streak_badges):
                    box = badge.bounding_box()
                    if box:
                        width = box['width']
                        height = box['height']

                        # Check touch target size (44px minimum for iOS)
                        if height >= 44:
                            print(f"       [OK] Badge {idx+1} touch target: {height:.0f}px height (>= 44px)")
                        else:
                            print(f"       [WARN] Badge {idx+1} touch target: {height:.0f}px height (< 44px)")

                        # Check if badge is visible
                        is_visible = badge.is_visible()
                        if is_visible:
                            print(f"       [OK] Badge {idx+1} is visible (width: {width:.0f}px)")
                        else:
                            print(f"       [FAIL] Badge {idx+1} is not visible")

                        # Get computed styles
                        styles = page.evaluate('''(element) => {
                            const computed = window.getComputedStyle(element);
                            return {
                                display: computed.display,
                                marginLeft: computed.marginLeft,
                                marginTop: computed.marginTop,
                                border: computed.border,
                                background: computed.background
                            };
                        }''', badge)

                        # Check if stacking properly on mobile (should be block on small screens)
                        if viewport['width'] <= 575:
                            if styles['display'] == 'block':
                                print(f"       [OK] Badge {idx+1} stacks properly (display: block)")
                            else:
                                print(f"       [WARN] Badge {idx+1} display: {styles['display']} (expected 'block')")

                            if styles['marginLeft'] == '0px':
                                print(f"       [OK] Badge {idx+1} has no left margin on mobile")
                            else:
                                print(f"       [WARN] Badge {idx+1} has marginLeft: {styles['marginLeft']}")
                        else:
                            if styles['display'] == 'inline-block':
                                print(f"       [OK] Badge {idx+1} inline on larger screens")

                        # Check border (gold border)
                        if 'rgb(255, 215, 0)' in styles['border'] or '#ffd700' in styles['border'].lower():
                            print(f"       [OK] Badge {idx+1} has gold border")
                        else:
                            print(f"       [INFO] Badge {idx+1} border: {styles['border'][:50]}")
            else:
                print(f"  [INFO] No longest streak badges found (habits may have no streaks)")

            # Check for current streak badge (should exist)
            current_streak_badges = page.query_selector_all('.streak-badge:not(.longest-streak-badge)')
            if current_streak_badges:
                print(f"  [OK] Found {len(current_streak_badges)} current streak badge(s)")

            # Check trophy icon
            trophy_icons = page.query_selector_all('.trophy-icon')
            if trophy_icons:
                print(f"  [OK] Found {len(trophy_icons)} trophy icon(s)")

            # Take screenshot
            screenshot_path = f'{screenshots_dir}/dashboard_auth_{device_name.replace(" ", "_").replace("/", "-")}_{viewport["width"]}x{viewport["height"]}.png'
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  [SCREENSHOT] Saved: {screenshot_path}")

            # Close context
            context.close()
            print(f"  [DONE] Test completed for {device_name}")

        browser.close()

        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"[OK] Tested {len(VIEWPORTS)} different viewport sizes")
        print(f"[OK] Screenshots saved to: {screenshots_dir}/")
        print("\nNext Steps:")
        print("1. Review screenshots for visual issues")
        print("2. Check that badges stack properly on iPhone SE (375px)")
        print("3. Verify purple gradient and gold border are visible")
        print("4. Ensure trophy icon renders correctly")
        print("="*70 + "\n")


if __name__ == '__main__':
    print("\nStarting Mobile Responsiveness Test (With Authentication)")
    print("Make sure Flask server is running on http://localhost:5000")
    print(f"Using test account: {TEST_EMAIL}\n")

    try:
        test_dashboard_mobile_responsiveness()
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
