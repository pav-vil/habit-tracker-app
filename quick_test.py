"""
Quick test to verify HabitFlow routes are working
Tests the complete habit and leaderboard functionality
"""
import requests
import sys

BASE_URL = 'http://127.0.0.1:5000'

def test_routes():
    """Test basic routes without authentication"""

    print("=" * 70)
    print("TESTING HABITFLOW ROUTES")
    print("=" * 70)

    # Create a session to maintain cookies
    session = requests.Session()

    # Test 1: Homepage
    print("\n[1] Testing homepage (GET /)...")
    try:
        response = session.get(f"{BASE_URL}/")
        print(f"    Status: {response.status_code}")
        print(f"    Response length: {len(response.text)}")
        if response.status_code == 200:
            print("    [PASS] Homepage loads")
        else:
            print("    [FAIL] Homepage failed")
    except Exception as e:
        print(f"    [ERROR] {e}")

    # Test 2: Leaderboard (should redirect to login)
    print("\n[2] Testing leaderboard (GET /gamification/leaderboard)...")
    try:
        response = session.get(f"{BASE_URL}/gamification/leaderboard", allow_redirects=False)
        print(f"    Status: {response.status_code}")
        if response.status_code in [302, 401]:
            print("    [PASS] Leaderboard requires login (redirected)")
        elif response.status_code == 200:
            print("    [WARNING] Leaderboard accessible without login")
        else:
            print(f"    [FAIL] Unexpected status code")
    except Exception as e:
        print(f"    [ERROR] {e}")

    # Test 3: Badges (should redirect to login)
    print("\n[3] Testing badges (GET /gamification/badges)...")
    try:
        response = session.get(f"{BASE_URL}/gamification/badges", allow_redirects=False)
        print(f"    Status: {response.status_code}")
        if response.status_code in [302, 401]:
            print("    [PASS] Badges requires login (redirected)")
        elif response.status_code == 200:
            print("    [WARNING] Badges accessible without login")
        else:
            print(f"    [FAIL] Unexpected status code")
    except Exception as e:
        print(f"    [ERROR] {e}")

    # Test 4: Complete habit (should redirect to login or fail)
    print("\n[4] Testing complete habit (POST /habits/1/complete)...")
    try:
        response = session.post(f"{BASE_URL}/habits/1/complete", allow_redirects=False)
        print(f"    Status: {response.status_code}")
        if response.status_code in [302, 401, 405]:
            print("    [PASS] Complete habit requires auth or habit doesn't exist")
        else:
            print(f"    [FAIL] Unexpected status code")
    except Exception as e:
        print(f"    [ERROR] {e}")

    # Test 5: Dashboard (should redirect to login)
    print("\n[5] Testing dashboard (GET /habits/dashboard)...")
    try:
        response = session.get(f"{BASE_URL}/habits/dashboard", allow_redirects=False)
        print(f"    Status: {response.status_code}")
        if response.status_code in [302, 401]:
            print("    [PASS] Dashboard requires login (redirected)")
        elif response.status_code == 200:
            print("    [WARNING] Dashboard accessible without login")
        else:
            print(f"    [FAIL] Unexpected status code")
    except Exception as e:
        print(f"    [ERROR] {e}")

    print("\n" + "=" * 70)
    print("ROUTE TESTING COMPLETE")
    print("=" * 70)
    print("\nNOTE: All protected routes should redirect to login (302)")
    print("      This confirms the routes exist and are properly protected")
    print("\nNext steps: Login and test authenticated routes")

if __name__ == '__main__':
    try:
        test_routes()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
