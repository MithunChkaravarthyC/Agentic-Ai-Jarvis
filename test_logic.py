"""
Comprehensive Intent & Routing Verification Test
Ensures words like 'weather' NEVER trigger food booking, and each intent routes accurately.
"""
import sys, re
sys.path.insert(0, '.')

from backend.agents.jarvis_orchestrator import JarvisOrchestrator
from backend.tools.app_launcher import _clean

orch = JarvisOrchestrator()

test_cases = [
    # Time queries
    ("what time is it", "time_query"),
    ("what is the time right now", "time_query"),
    ("tell me the time please", "time_query"),
    ("what is the time in Tokyo", "time_query"),
    ("what is today's date", "time_query"),
    ("what day is it today", "time_query"),

    # Weather queries (Previously bugged due to 'eat' in 'weather')
    ("what is the weather today", "weather_query"),
    ("how is the weather in Coimbatore", "weather_query"),
    ("is it raining outside", "weather_query"),
    ("what is the temperature in Bangalore", "weather_query"),
    ("original climate in London", "weather_query"),
    
    # App launcher
    ("Open Notepad", "open_app"),
    ("open up calculator", "open_app"),
    ("open up kiro fast", "open_app"),
    ("launch vs code", "open_app"),
    
    # Food ordering
    ("Swiggy Biryani", "order_swiggy"),
    ("order pizza please", "order_swiggy"),
    ("order some burger for dinner", "order_swiggy"),
    
    # Flights
    ("Book Flight from Chennai to Delhi", "book_flight"),
    ("fly to Mumbai next week", "book_flight"),
    
    # Web building (including Lusion 3D websites)
    ("build me a cake shop website", "build_web_app"),
    ("create an interactive 3D portfolio app", "build_web_app"),
    ("build a 3d website like lusion website in a smooth way", "build_web_app"),
    ("generate a 3d designed website like lusion", "build_web_app"),
    
    # Research
    ("research quantum computing for me", "research_topic"),
    ("explain how neural networks work", "research_topic"),
]

print("=" * 65)
print("   JARVIS MULTI-AGENT INTENT ROUTING VERIFICATION")
print("=" * 65)

all_passed = True
for query, expected in test_cases:
    classified = orch._classify_intent(query)
    is_correct = classified == expected
    status = "[PASS]" if is_correct else "[FAIL]"
    if not is_correct:
        all_passed = False
    print(f"  {status} '{query}' -> '{classified}' (expected: '{expected}')")

print("=" * 65)
print("ALL ROUTING TESTS PASSED!" if all_passed else "SOME TESTS FAILED!")
print("=" * 65)
