"""
Simple verification: Check if chart elements exist in dashboard.html template
"""

# Read the dashboard template
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("[TEST] Verifying chart elements in dashboard.html template...\n")

# Check for key elements
checks = {
    'Chart card container': '.chart-card' in content,
    'Chart title': 'chart-title' in content,
    'Chart canvas element': 'id="completionTrendChart"' in content,
    'Loading spinner': 'id="chartLoading"' in content,
    'API fetch call': '/api/30-day-completions' in content,
    'Chart.js initialization': 'new Chart(ctx' in content,
    'Purple gradient color': '#7c3aed' in content,
    'Longest streak badge class': 'longest-streak-badge' in content,
    'Trophy icon': 'trophy' in content.lower(),
}

all_passed = True
for check_name, result in checks.items():
    status = "[OK]" if result else "[FAIL]"
    print(f"{status} {check_name}: {'Found' if result else 'NOT FOUND'}")
    if not result:
        all_passed = False

print("\n" + "="*60)
if all_passed:
    print("[SUCCESS] All chart elements found in template!")
    print("The chart HTML is correctly added to the template.")
else:
    print("[WARNING] Some elements missing from template")

# Check base.html for Chart.js
print("\n[TEST] Checking Chart.js in base.html...")
with open('templates/base.html', 'r', encoding='utf-8') as f:
    base_content = f.read()

if 'chart.js' in base_content.lower():
    print("[OK] Chart.js library is loaded")
else:
    print("[FAIL] Chart.js library NOT found in base.html")

print("\n" + "="*60)
print("\nNext step: Make sure Flask app is running and visit:")
print("http://localhost:5000/habits/dashboard")
print("\nThe chart should appear between the stats cards and 'Add New Habit' button.")
