"""
Mobile Responsiveness Test for Longest Streak Badge
Tests the badge component in isolation across different viewport sizes
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


def test_badge_responsiveness():
    """Test the longest streak badge on various screen sizes"""

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, slow_mo=500)

        # Create screenshots directory
        screenshots_dir = 'badge_test_screenshots'
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)

        # Get absolute path to test HTML
        test_html_path = os.path.abspath('test_badge_demo.html')
        test_url = f'file:///{test_html_path}'

        print("\n" + "="*70)
        print("MOBILE RESPONSIVENESS TEST - LONGEST STREAK BADGE")
        print("="*70)

        results = {
            'horizontal_scroll': [],
            'badge_stacking': [],
            'touch_targets': [],
            'visual_issues': []
        }

        for device_name, viewport in VIEWPORTS.items():
            print(f"\n[Testing {device_name} - {viewport['width']}x{viewport['height']}]")

            # Create context with specific viewport
            context = browser.new_context(
                viewport=viewport,
                device_scale_factor=2 if 'iPhone' in device_name else 1
            )
            page = context.new_page()

            # Navigate to test page
            page.goto(test_url)
            time.sleep(1)

            # Check for horizontal scrolling
            scroll_width = page.evaluate('document.documentElement.scrollWidth')
            client_width = page.evaluate('document.documentElement.clientWidth')
            has_horizontal_scroll = scroll_width > client_width

            if has_horizontal_scroll:
                print(f"  [FAIL] HORIZONTAL SCROLL DETECTED")
                print(f"         Content: {scroll_width}px, Viewport: {client_width}px")
                results['horizontal_scroll'].append(device_name)
            else:
                print(f"  [OK] No horizontal scrolling")

            # Check longest streak badges
            longest_streak_badges = page.query_selector_all('.longest-streak-badge')
            print(f"  [INFO] Found {len(longest_streak_badges)} longest streak badges")

            for idx, badge in enumerate(longest_streak_badges, 1):
                box = badge.bounding_box()
                if box:
                    width = box['width']
                    height = box['height']

                    # Check touch target size (44px minimum for iOS)
                    if height >= 44:
                        print(f"       [OK] Badge {idx}: {height:.0f}px height (iOS compliant)")
                    else:
                        print(f"       [WARN] Badge {idx}: {height:.0f}px height (< 44px)")
                        results['touch_targets'].append(f"{device_name} - Badge {idx}")

                    # Get computed styles
                    styles = page.evaluate('''(element) => {
                        const computed = window.getComputedStyle(element);
                        return {
                            display: computed.display,
                            marginLeft: computed.marginLeft,
                            marginTop: computed.marginTop,
                            width: computed.width,
                            border: computed.border,
                            background: computed.background
                        };
                    }''', badge)

                    # Check stacking on mobile
                    if viewport['width'] <= 575:
                        if styles['display'] == 'block':
                            print(f"       [OK] Badge {idx}: Stacks properly (display: block)")
                        else:
                            print(f"       [WARN] Badge {idx}: display: {styles['display']} (expected 'block')")
                            results['badge_stacking'].append(f"{device_name} - Badge {idx}")

                        if styles['marginLeft'] == '0px':
                            print(f"       [OK] Badge {idx}: No left margin on mobile")
                        else:
                            print(f"       [WARN] Badge {idx}: marginLeft: {styles['marginLeft']}")

                        if styles['marginTop'] != '0px':
                            print(f"       [OK] Badge {idx}: Has top margin: {styles['marginTop']}")
                    else:
                        if styles['display'] == 'inline-block':
                            print(f"       [OK] Badge {idx}: Inline on larger screens")
                        if styles['marginLeft'] != '0px':
                            print(f"       [OK] Badge {idx}: Has left margin: {styles['marginLeft']}")

                    # Check border
                    if '2px' in styles['border'] and ('255, 215, 0' in styles['border'] or 'ffd700' in styles['border'].lower()):
                        print(f"       [OK] Badge {idx}: Gold border present")
                    else:
                        print(f"       [INFO] Badge {idx}: Border: {styles['border'][:60]}")

            # Check trophy icons
            trophy_icons = page.query_selector_all('.trophy-icon')
            if trophy_icons:
                print(f"  [OK] Found {len(trophy_icons)} trophy icons")

            # Take screenshot
            screenshot_path = f'{screenshots_dir}/badge_{device_name.replace(" ", "_").replace("/", "-")}_{viewport["width"]}x{viewport["height"]}.png'
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  [SCREENSHOT] {screenshot_path}")

            context.close()
            print(f"  [DONE] {device_name}")

        browser.close()

        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        print("\n1. HORIZONTAL SCROLLING")
        if results['horizontal_scroll']:
            print(f"   [FAIL] Issues on: {', '.join(results['horizontal_scroll'])}")
        else:
            print("   [OK] No horizontal scrolling on any device")

        print("\n2. BADGE STACKING (Mobile)")
        if results['badge_stacking']:
            print(f"   [WARN] Issues on: {', '.join(results['badge_stacking'])}")
        else:
            print("   [OK] Badges stack properly on mobile devices")

        print("\n3. TOUCH TARGETS (44px minimum)")
        if results['touch_targets']:
            print(f"   [WARN] Small targets: {', '.join(results['touch_targets'])}")
        else:
            print("   [OK] All badges meet iOS minimum touch target size")

        print(f"\n4. SCREENSHOTS")
        print(f"   [OK] Saved to: {screenshots_dir}/")

        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)

        if not results['horizontal_scroll'] and not results['badge_stacking'] and not results['touch_targets']:
            print("[PASS] Longest streak badge is fully mobile-ready!")
            print("       - No horizontal scrolling")
            print("       - Proper stacking on mobile")
            print("       - iOS-compliant touch targets")
            print("       - Ready for iOS deployment via MobiLoud")
        else:
            if results['horizontal_scroll']:
                print("[ACTION] Fix horizontal scrolling issues")
            if results['badge_stacking']:
                print("[ACTION] Fix badge stacking on mobile")
            if results['touch_targets']:
                print("[ACTION] Increase padding to meet 44px minimum")

        print("="*70 + "\n")


if __name__ == '__main__':
    print("\nStarting Longest Streak Badge Mobile Test")
    print("Testing badge component in isolation\n")

    try:
        test_badge_responsiveness()
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
