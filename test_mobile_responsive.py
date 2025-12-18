"""
Mobile Compatibility Test for 30-Day Completion Chart
Tests dashboard chart responsiveness using Selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os

# Test viewports
VIEWPORTS = [
    {'name': 'iPhone SE', 'width': 375, 'height': 667},
    {'name': 'iPhone 11/12/13', 'width': 414, 'height': 896},
    {'name': 'iPad', 'width': 768, 'height': 1024},
    {'name': 'Desktop', 'width': 1920, 'height': 1080}
]

BASE_URL = 'http://localhost:5000'
TEST_EMAIL = 'test@example.com'
TEST_PASSWORD = 'password123'

def test_viewport(viewport):
    """Test a single viewport"""
    print(f"\n{'='*60}")
    print(f"Testing: {viewport['name']} ({viewport['width']}x{viewport['height']})")
    print('='*60)

    # Setup Chrome with mobile viewport
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(viewport['width'], viewport['height'])

    issues = []
    passed = []

    try:
        # Login
        driver.get(f'{BASE_URL}/auth/login')
        time.sleep(1)

        email_input = driver.find_element(By.NAME, 'email')
        password_input = driver.find_element(By.NAME, 'password')

        email_input.send_keys(TEST_EMAIL)
        password_input.send_keys(TEST_PASSWORD)

        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()

        # Wait for dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains('/habits/dashboard')
        )
        time.sleep(3)  # Wait for chart to render

        print('✓ Successfully logged in and navigated to dashboard')

        # TEST 1: Check for horizontal scrolling
        scroll_width = driver.execute_script('return document.documentElement.scrollWidth')
        client_width = driver.execute_script('return document.documentElement.clientWidth')

        if scroll_width > client_width:
            issue = f'Horizontal scroll detected: scrollWidth ({scroll_width}px) > clientWidth ({client_width}px)'
            print(f'✗ {issue}')
            issues.append(issue)
        else:
            print('✓ No horizontal scrolling')
            passed.append('No horizontal scrolling')

        # TEST 2: Check chart container visibility
        try:
            chart_container = driver.find_element(By.CSS_SELECTOR, '.chart-container')
            if chart_container.is_displayed():
                print('✓ Chart container is visible')
                passed.append('Chart container visible')
            else:
                issue = 'Chart container not visible'
                print(f'✗ {issue}')
                issues.append(issue)
        except Exception as e:
            issue = f'Chart container not found: {str(e)}'
            print(f'✗ {issue}')
            issues.append(issue)
            driver.quit()
            return {'viewport': viewport['name'], 'issues': issues, 'passed': passed}

        # TEST 3: Check chart height
        chart_height = driver.execute_script('''
            const container = document.querySelector('.chart-container');
            return container ? container.offsetHeight : 0;
        ''')

        expected_height = 250 if viewport['width'] <= 575 else 300

        if abs(chart_height - expected_height) <= 10:
            print(f'✓ Chart height correct: {chart_height}px (expected {expected_height}px)')
            passed.append(f'Chart height: {chart_height}px')
        else:
            issue = f'Chart height incorrect: {chart_height}px (expected {expected_height}px)'
            print(f'✗ {issue}')
            issues.append(issue)

        # TEST 4: Check canvas element
        canvas_count = driver.execute_script('''
            return document.querySelectorAll('#completionTrendChart').length;
        ''')

        if canvas_count > 0:
            print('✓ Chart canvas element exists')
            passed.append('Canvas element exists')
        else:
            issue = 'Chart canvas element missing'
            print(f'✗ {issue}')
            issues.append(issue)

        # TEST 5: Check chart card padding
        padding = driver.execute_script('''
            const card = document.querySelector('.chart-card');
            if (!card) return null;
            const style = window.getComputedStyle(card);
            return {
                left: parseInt(style.paddingLeft),
                right: parseInt(style.paddingRight),
                top: parseInt(style.paddingTop),
                bottom: parseInt(style.paddingBottom)
            };
        ''')

        if padding:
            expected_h_padding = 15 if viewport['width'] <= 575 else 25
            if padding['left'] == expected_h_padding and padding['right'] == expected_h_padding:
                print(f'✓ Chart card padding correct: {padding["left"]}px / {padding["right"]}px')
                passed.append(f'Padding: {padding["left"]}px/{padding["right"]}px')
            else:
                issue = f'Chart card padding: {padding["left"]}px/{padding["right"]}px (expected {expected_h_padding}px)'
                print(f'⚠ {issue}')
                issues.append(issue)

        # TEST 6: Check chart title visibility
        try:
            chart_title = driver.find_element(By.CSS_SELECTOR, '.chart-title')
            if chart_title.is_displayed():
                title_text = chart_title.text
                print(f'✓ Chart title visible: "{title_text}"')
                passed.append('Chart title visible')
            else:
                issue = 'Chart title not visible'
                print(f'✗ {issue}')
                issues.append(issue)
        except:
            issue = 'Chart title not found'
            print(f'✗ {issue}')
            issues.append(issue)

        # TEST 7: Take screenshot
        screenshots_dir = 'C:\\Users\\PC\\habit-tracker-app\\screenshots'
        os.makedirs(screenshots_dir, exist_ok=True)

        screenshot_path = os.path.join(
            screenshots_dir,
            f'dashboard_{viewport["name"].replace("/", "_")}_{viewport["width"]}x{viewport["height"]}.png'
        )

        driver.save_screenshot(screenshot_path)
        print(f'✓ Screenshot saved: {screenshot_path}')

        # TEST 8: Check console errors
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']

        if errors:
            issue = f'Console errors detected: {len(errors)} error(s)'
            print(f'✗ {issue}')
            issues.append(issue)
            for error in errors[:3]:  # Show first 3
                print(f'  - {error["message"][:100]}')
        else:
            print('✓ No console errors')
            passed.append('No console errors')

        # TEST 9: Check button tap targets (mobile only)
        if viewport['width'] <= 414:
            small_buttons = driver.execute_script('''
                const buttons = document.querySelectorAll('button, a.btn');
                let count = 0;
                buttons.forEach(btn => {
                    const rect = btn.getBoundingClientRect();
                    if (rect.width < 44 || rect.height < 44) {
                        count++;
                    }
                });
                return count;
            ''')

            if small_buttons > 0:
                issue = f'{small_buttons} button(s) smaller than 44x44px tap target'
                print(f'⚠ {issue}')
                issues.append(issue)
            else:
                print('✓ All buttons meet 44x44px minimum tap target')
                passed.append('Tap targets meet iOS standards')

    except Exception as e:
        issue = f'Test error: {str(e)}'
        print(f'✗ {issue}')
        issues.append(issue)

    finally:
        driver.quit()

    return {
        'viewport': viewport['name'],
        'dimensions': f"{viewport['width']}x{viewport['height']}",
        'issues': issues,
        'passed': passed
    }

def generate_report(results):
    """Generate final report"""
    print('\n\n')
    print('='*80)
    print('MOBILE COMPATIBILITY TEST REPORT - 30-DAY COMPLETION CHART')
    print('='*80)
    print(f'Date: {time.strftime("%Y-%m-%d")}')
    print(f'Time: {time.strftime("%H:%M:%S")}\n')

    total_issues = 0
    critical_issues = 0

    for result in results:
        print(f"\n{result['viewport']} ({result['dimensions']})")
        print('-'*60)

        if result['passed']:
            print('\nPassed Tests:')
            for p in result['passed']:
                print(f'  ✓ {p}')

        if result['issues']:
            print('\nIssues Found:')
            for issue in result['issues']:
                print(f'  ✗ {issue}')
                total_issues += 1
                if 'horizontal scroll' in issue.lower() or 'not visible' in issue.lower():
                    critical_issues += 1

    print('\n' + '='*80)
    print('SUMMARY')
    print('='*80)
    print(f'Total Viewports Tested: {len(results)}')
    print(f'Total Issues Found: {total_issues}')
    print(f'Critical Issues: {critical_issues}')

    if total_issues == 0:
        print('\n🎉 ALL TESTS PASSED - Chart is fully mobile responsive!')
        grade = 'A'
    elif critical_issues == 0:
        print('\n⚠ Minor issues found - Chart is functional but could be improved')
        grade = 'B'
    else:
        print('\n🚨 CRITICAL ISSUES FOUND - Chart needs fixes before deployment')
        grade = 'C'

    print(f'\nOverall Grade: {grade}')
    print('\n' + '='*80)

def main():
    """Run all tests"""
    results = []

    for viewport in VIEWPORTS:
        result = test_viewport(viewport)
        results.append(result)

    generate_report(results)

if __name__ == '__main__':
    main()
