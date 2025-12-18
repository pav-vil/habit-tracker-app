/**
 * Simple Mobile Chart Test
 */
const { chromium } = require('playwright');

async function test() {
    console.log('Starting test...');
    const browser = await chromium.launch({ headless: true });

    // Test iPhone SE
    const context = await browser.newContext({
        viewport: { width: 375, height: 667 }
    });

    const page = await context.newPage();

    try {
        // Go to login
        await page.goto('http://localhost:5000/auth/login');
        console.log('Loaded login page');

        // Login
        await page.fill('input[name="email"]', 'test@example.com');
        await page.fill('input[name="password"]', 'password123');
        await page.click('button[type="submit"]');

        await page.waitForTimeout(3000);
        console.log('Logged in');

        // Check for horizontal scroll
        const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
        const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

        console.log(`ScrollWidth: ${scrollWidth}px, ClientWidth: ${clientWidth}px`);

        if (scrollWidth > clientWidth) {
            console.log('ISSUE: Horizontal scrolling detected!');
        } else {
            console.log('PASS: No horizontal scrolling');
        }

        // Check chart container
        const chartHeight = await page.evaluate(() => {
            const container = document.querySelector('.chart-container');
            return container ? container.offsetHeight : 0;
        });

        console.log(`Chart container height: ${chartHeight}px`);

        if (chartHeight === 250) {
            console.log('PASS: Chart height correct for mobile (250px)');
        } else {
            console.log(`ISSUE: Chart height is ${chartHeight}px, expected 250px`);
        }

        // Take screenshot
        await page.screenshot({ path: 'C:\\Users\\PC\\habit-tracker-app\\test_screenshot.png', fullPage: true });
        console.log('Screenshot saved');

    } catch (error) {
        console.error('Error:', error.message);
    }

    await browser.close();
}

test();
