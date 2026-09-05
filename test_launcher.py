"""
Direct test of app_launcher — runs outside the web server.
Each successful test will ACTUALLY open the application on screen.
"""
import sys
sys.path.insert(0, '.')
from backend.tools.app_launcher import app_launcher

tests = [
    "Open Notepad",
    "open up calculator",
    "open kiro",
    "open up kiro fast",
    "Jarvis open discord",
    "launch vs code",
    "open chrome",
]

print("=" * 60)
print("  JARVIS APP LAUNCHER — DIRECT TEST")
print("  (Each PASS means the app actually opened on screen)")
print("=" * 60)

for query in tests:
    result = app_launcher.open_application(query)
    status = "[PASS]" if result["status"] == "success" else "[FAIL]"
    print(f"  {status} | '{query}' -> {result['message']}")

print("=" * 60)
