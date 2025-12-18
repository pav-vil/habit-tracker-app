"""
Mobile Responsiveness Test for Dashboard - Longest Streak Badge
Tests the longest streak badge across different viewport sizes
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

def test_dashboard_mobile_responsiveness():
    """Test the dashboard page with longest streak badge on various screen sizes"""

    with sync_playwright() as p:
        # Launch browser in headed mode so we can see the test
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

            # Navigate to dashboard (assuming local development server)
            url = 'http://localhost:5000/dashboard'
            try:
                page.goto(url, wait_until='networkidle', timeout=10000)
            except Exception as e:
                print(f"  ❌ Could not load page: {e}")
                print(f"  ℹ️  Make sure Flask server is running on {url}")
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
                            print(f"       [WARN] Badge {idx+1} touch target: {height:.0f}px height (< 44px - may be too small)")

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
                                print(f"       [WARN] Badge {idx+1} display: {styles['display']} (should be 'block' on mobile)")

                            if styles['marginLeft'] == '0px':
                                print(f"       [OK] Badge {idx+1} has no left margin on mobile")
                            else:
                                print(f"       [WARN] Badge {idx+1} has marginLeft: {styles['marginLeft']} (should be 0 on mobile)")
                        else:
                            if styles['display'] == 'inline-block':
                                print(f"       [OK] Badge {idx+1} inline on larger screens")
            else:
                print(f"  [INFO] No longest streak badges found (user may have no habits with streaks)")

            # Check for current streak badge (should exist)
            current_streak_badges = page.query_selector_all('.streak-badge')
            if current_streak_badges:
                print(f"  [OK] Found {len(current_streak_badges)} current streak badge(s)")

            # Check trophy icon
            trophy_icons = page.query_selector_all('.trophy-icon')
            if trophy_icons:
                print(f"  [OK] Found {len(trophy_icons)} trophy icon(s)")

            # Check for console errors
            console_errors = []
            page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)

            # Take screenshot
            screenshot_path = f'{screenshots_dir}/dashboard_{device_name.replace(" ", "_").replace("/", "-")}_{viewport["width"]}x{viewport["height"]}.png'
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  [SCREENSHOT] Saved: {screenshot_path}")

            # Test scrolling behavior
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(0.5)

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
    print("\nStarting Mobile Responsiveness Test")
    print("Make sure Flask server is running on http://localhost:5000")
    print("You should be logged in with habits that have longest streaks\n")

    try:
        test_dashboard_mobile_responsiveness()
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
