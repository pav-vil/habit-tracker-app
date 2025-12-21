"""
Test Render deployment - Registration and Login functionality
Tests the deployed app on Render to verify it's working correctly
"""

from playwright.sync_api import sync_playwright, expect
import time

# IMPORTANT: Update this URL to your actual Render deployment URL
RENDER_URL = "https://your-app-name.onrender.com"  # Replace with your actual URL

def test_registration_and_login():
    """Test user registration and login on Render deployment"""

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        try:
            # Generate unique test user
            timestamp = int(time.time())
            test_email = f"testuser{timestamp}@example.com"
            test_password = "TestPassword123"

            print(f"\n{'='*60}")
            print(f"Testing Render Deployment: {RENDER_URL}")
            print(f"Test Email: {test_email}")
            print(f"{'='*60}\n")

            # Step 1: Navigate to registration page
            print("[1/6] Navigating to registration page...")
            page.goto(f"{RENDER_URL}/auth/register", wait_until="networkidle")
            page.wait_for_timeout(1000)

            # Check for Internal Server Error
            if "Internal Server Error" in page.content():
                print("❌ ERROR: Internal Server Error detected on registration page!")
                print("Check Render logs for details.")
                return False

            print("✓ Registration page loaded successfully")

            # Step 2: Fill registration form
            print("[2/6] Filling registration form...")
            page.fill('input[name="email"]', test_email)
            page.fill('input[name="password"]', test_password)
            page.fill('input[name="confirm_password"]', test_password)
            page.select_option('select[name="timezone"]', 'America/New_York')
            print("✓ Form filled successfully")

            # Step 3: Submit registration
            print("[3/6] Submitting registration...")
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)

            # Check for errors after submission
            if "Internal Server Error" in page.content():
                print("❌ ERROR: Internal Server Error during registration!")
                print("This indicates a server-side issue.")
                print("\nPossible causes:")
                print("- SECRET_KEY not properly set in Render environment variables")
                print("- DATABASE_URL not properly set")
                print("- Database connection issue")
                print("\nCheck Render logs for detailed error information.")
                return False

            # Check if redirected to login page
            if "/auth/login" in page.url:
                print("✓ Registration successful! Redirected to login page")
            else:
                print(f"⚠ Warning: Expected redirect to login, but at: {page.url}")
                # Check for success message
                if "Account created successfully" in page.content():
                    print("✓ Success message found, proceeding to login...")
                    page.goto(f"{RENDER_URL}/auth/login")
                else:
                    print("❌ Registration may have failed - no success message found")
                    return False

            # Step 4: Fill login form
            print("[4/6] Filling login form...")
            page.fill('input[name="email"]', test_email)
            page.fill('input[name="password"]', test_password)
            print("✓ Login form filled")

            # Step 5: Submit login
            print("[5/6] Submitting login...")
            page.click('button[type="submit"]')
            page.wait_for_timeout(2000)

            # Check for errors after login
            if "Internal Server Error" in page.content():
                print("❌ ERROR: Internal Server Error during login!")
                print("Check Render logs for details.")
                return False

            # Step 6: Verify login success
            print("[6/6] Verifying login success...")
            current_url = page.url

            if current_url == RENDER_URL or current_url == f"{RENDER_URL}/":
                print("✓ Login successful! Redirected to home page")

                # Check for welcome message or logout link
                if "logout" in page.content().lower():
                    print("✓ User session created - logout link visible")
                    print("\n" + "="*60)
                    print("✅ ALL TESTS PASSED!")
                    print("="*60 + "\n")
                    return True
                else:
                    print("⚠ Warning: Login succeeded but no logout link found")
                    return True
            else:
                print(f"❌ Login failed - unexpected redirect to: {current_url}")

                # Check for error message
                if "Invalid email or password" in page.content():
                    print("Error: Invalid credentials (but we just registered!)")
                    print("This suggests a database or session issue")

                return False

        except Exception as e:
            print(f"\n❌ TEST FAILED WITH EXCEPTION!")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\nClosing browser...")
            page.wait_for_timeout(2000)
            browser.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Render Deployment Test - Registration & Login")
    print("="*60 + "\n")

    # Check if URL is set
    if "your-app-name" in RENDER_URL:
        print("⚠️  WARNING: Please update RENDER_URL in this script!")
        print("Edit the RENDER_URL variable at the top of this file.")
        print("Example: RENDER_URL = 'https://habitflow.onrender.com'")
        exit(1)

    success = test_registration_and_login()

    if success:
        print("\n🎉 Deployment is working correctly!")
    else:
        print("\n💔 Deployment has issues - check Render logs")

    exit(0 if success else 1)
