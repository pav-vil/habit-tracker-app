/**
 * Mobile Compatibility Test for 30-Day Completion Chart
 * Tests dashboard chart responsiveness across multiple viewport sizes
 */

const { chromium } = require('playwright');
const fs = require('fs');

// Test viewports per iOS standards
const viewports = [
    { name: 'iPhone SE', width: 375, height: 667 },
    { name: 'iPhone 11/12/13', width: 414, height: 896 },
    { name: 'iPad', width: 768, height: 1024 },
    { name: 'Desktop', width: 1920, height: 1080 }
];

// Test credentials (change if needed)
const TEST_USER = {
    email: 'test@example.com',
    password: 'password123'
};

const BASE_URL = 'http://localhost:5000';

async function testMobileChart() {
    const browser = await chromium.launch({ headless: false });
    const results = [];

    for (const viewport of viewports) {
        console.log(`\n${'='.repeat(60)}`);
        console.log(`Testing: ${viewport.name} (${viewport.width}x${viewport.height})`);
        console.log('='.repeat(60));

        const context = await browser.newContext({
            viewport: { width: viewport.width, height: viewport.height },
            userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
        });

        const page = await context.newPage();
        const testResult = {
            viewport: viewport.name,
            dimensions: `${viewport.width}x${viewport.height}`,
            issues: [],
            passed: []
        };

        try {
            // Navigate to login
            await page.goto(`${BASE_URL}/auth/login`, { waitUntil: 'networkidle' });

            // Login
            await page.fill('input[name="email"]', TEST_USER.email);
            await page.fill('input[name="password"]', TEST_USER.password);
            await page.click('button[type="submit"]');

            // Wait for dashboard to load
            await page.waitForURL('**/habits/dashboard', { timeout: 5000 });
            await page.waitForTimeout(2000); // Wait for chart to render

            console.log('✓ Successfully logged in and navigated to dashboard');

            // TEST 1: Check for horizontal scrolling
            const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
            const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

            if (scrollWidth > clientWidth) {
                const issue = `Horizontal scroll detected: scrollWidth (${scrollWidth}px) > clientWidth (${clientWidth}px)`;
                console.log('✗', issue);
                testResult.issues.push(issue);
            } else {
                console.log('✓ No horizontal scrolling');
                testResult.passed.push('No horizontal scrolling');
            }

            // TEST 2: Check chart container exists and is visible
            const chartContainer = await page.locator('.chart-container').first();
            const isChartVisible = await chartContainer.isVisible();

            if (isChartVisible) {
                console.log('✓ Chart container is visible');
                testResult.passed.push('Chart container visible');
            } else {
                const issue = 'Chart container not visible';
                console.log('✗', issue);
                testResult.issues.push(issue);
            }

            // TEST 3: Check chart height on mobile
            const chartHeight = await chartContainer.evaluate(el => el.offsetHeight);
            const expectedHeight = viewport.width <= 575 ? 250 : 300;

            if (Math.abs(chartHeight - expectedHeight) <= 10) {
                console.log(`✓ Chart height correct: ${chartHeight}px (expected ${expectedHeight}px)`);
                testResult.passed.push(`Chart height: ${chartHeight}px`);
            } else {
                const issue = `Chart height incorrect: ${chartHeight}px (expected ${expectedHeight}px)`;
                console.log('✗', issue);
                testResult.issues.push(issue);
            }

            // TEST 4: Check canvas element exists
            const canvas = await page.locator('#completionTrendChart');
            const canvasExists = await canvas.count() > 0;

            if (canvasExists) {
                console.log('✓ Chart canvas element exists');
                testResult.passed.push('Canvas element exists');
            } else {
                const issue = 'Chart canvas element missing';
                console.log('✗', issue);
                testResult.issues.push(issue);
            }

            // TEST 5: Check chart card padding on mobile
            const chartCard = await page.locator('.chart-card').first();
            const padding = await chartCard.evaluate(el => {
                const style = window.getComputedStyle(el);
                return {
                    left: parseInt(style.paddingLeft),
                    right: parseInt(style.paddingRight),
                    top: parseInt(style.paddingTop),
                    bottom: parseInt(style.paddingBottom)
                };
            });

            const expectedPadding = viewport.width <= 575 ? { left: 15, right: 15 } : { left: 25, right: 25 };
            if (padding.left === expectedPadding.left && padding.right === expectedPadding.right) {
                console.log(`✓ Chart card padding correct: ${padding.left}px / ${padding.right}px`);
                testResult.passed.push(`Padding: ${padding.left}px/${padding.right}px`);
            } else {
                const issue = `Chart card padding incorrect: ${padding.left}px/${padding.right}px (expected ${expectedPadding.left}px/${expectedPadding.right}px)`;
                console.log('⚠', issue);
                testResult.issues.push(issue);
            }

            // TEST 6: Check for Chart.js errors in console
            const consoleErrors = [];
            page.on('console', msg => {
                if (msg.type() === 'error') {
                    consoleErrors.push(msg.text());
                }
            });

            await page.waitForTimeout(1000);

            if (consoleErrors.length > 0) {
                const issue = `Console errors detected: ${consoleErrors.join(', ')}`;
                console.log('✗', issue);
                testResult.issues.push(issue);
            } else {
                console.log('✓ No console errors');
                testResult.passed.push('No console errors');
            }

            // TEST 7: Check chart title visibility
            const chartTitle = await page.locator('.chart-title').first();
            const titleVisible = await chartTitle.isVisible();

            if (titleVisible) {
                const titleText = await chartTitle.textContent();
                console.log(`✓ Chart title visible: "${titleText}"`);
                testResult.passed.push('Chart title visible');
            } else {
                const issue = 'Chart title not visible';
                console.log('✗', issue);
                testResult.issues.push(issue);
            }

            // TEST 8: Take screenshot
            const screenshotPath = `C:\\Users\\PC\\habit-tracker-app\\screenshots\\dashboard_${viewport.name.replace(/\//g, '_')}_${viewport.width}x${viewport.height}.png`;

            // Create screenshots directory if it doesn't exist
            const dir = 'C:\\Users\\PC\\habit-tracker-app\\screenshots';
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }

            await page.screenshot({ path: screenshotPath, fullPage: true });
            console.log(`✓ Screenshot saved: ${screenshotPath}`);
            testResult.screenshot = screenshotPath;

            // TEST 9: Check tap target sizes (if on mobile viewport)
            if (viewport.width <= 414) {
                const buttons = await page.locator('button, a.btn').all();
                let smallButtons = 0;

                for (const button of buttons) {
                    const box = await button.boundingBox();
                    if (box && (box.width < 44 || box.height < 44)) {
                        smallButtons++;
                    }
                }

                if (smallButtons > 0) {
                    const issue = `${smallButtons} button(s) smaller than 44x44px tap target`;
                    console.log('⚠', issue);
                    testResult.issues.push(issue);
                } else {
                    console.log('✓ All buttons meet 44x44px minimum tap target');
                    testResult.passed.push('Tap targets meet iOS standards');
                }
            }

            // TEST 10: Test touch interaction (scroll to chart)
            await chartContainer.scrollIntoViewIfNeeded();
            await page.waitForTimeout(500);
            console.log('✓ Chart scrolls into view correctly');
            testResult.passed.push('Chart scrollable');

        } catch (error) {
            console.error('✗ Test failed:', error.message);
            testResult.issues.push(`Test error: ${error.message}`);
        } finally {
            await context.close();
        }

        results.push(testResult);
    }

    await browser.close();

    // Generate report
    generateReport(results);
}

function generateReport(results) {
    console.log('\n\n');
    console.log('='.repeat(80));
    console.log('MOBILE COMPATIBILITY TEST REPORT - 30-DAY COMPLETION CHART');
    console.log('='.repeat(80));
    console.log(`Date: ${new Date().toLocaleDateString()}`);
    console.log(`Time: ${new Date().toLocaleTimeString()}\n`);

    let totalIssues = 0;
    let criticalIssues = 0;

    results.forEach(result => {
        console.log(`\n${result.viewport} (${result.dimensions})`);
        console.log('-'.repeat(60));

        if (result.passed.length > 0) {
            console.log('\nPassed Tests:');
            result.passed.forEach(pass => console.log(`  ✓ ${pass}`));
        }

        if (result.issues.length > 0) {
            console.log('\nIssues Found:');
            result.issues.forEach(issue => {
                console.log(`  ✗ ${issue}`);
                totalIssues++;
                if (issue.includes('horizontal scroll') || issue.includes('not visible')) {
                    criticalIssues++;
                }
            });
        }

        if (result.screenshot) {
            console.log(`\nScreenshot: ${result.screenshot}`);
        }
    });

    console.log('\n' + '='.repeat(80));
    console.log('SUMMARY');
    console.log('='.repeat(80));
    console.log(`Total Viewports Tested: ${results.length}`);
    console.log(`Total Issues Found: ${totalIssues}`);
    console.log(`Critical Issues: ${criticalIssues}`);

    if (totalIssues === 0) {
        console.log('\n🎉 ALL TESTS PASSED - Chart is fully mobile responsive!');
    } else if (criticalIssues === 0) {
        console.log('\n⚠ Minor issues found - Chart is functional but could be improved');
    } else {
        console.log('\n🚨 CRITICAL ISSUES FOUND - Chart needs fixes before deployment');
    }

    console.log('\n' + '='.repeat(80));
}

// Run the test
testMobileChart().catch(console.error);
