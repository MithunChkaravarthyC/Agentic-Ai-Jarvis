import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.agents.jarvis_orchestrator import jarvis_orchestrator

async def test_all_scenarios():
    print("=" * 60)
    print("   TESTING JARVIS GREETINGS, CONVERSATION & AGENTS")
    print("=" * 60)

    # 1. Test Pure Greeting "hi Jarvis"
    print("\n>> 1. Testing 'hi Jarvis'...")
    res1 = await jarvis_orchestrator.handle_user_input("hi Jarvis")
    print(f"Type: {res1.get('type')}")
    print(f"Reply: {res1.get('reply')}")
    print(f"Audio URL: {res1.get('audio_url')}")
    assert res1.get('type') == 'greeting', f"Expected 'greeting', got {res1.get('type')}"
    assert res1.get('reply').strip() not in ["Sir.", "Sir"], f"Reply must NOT be just 'Sir.', got {res1.get('reply')}"
    assert len(res1.get('reply')) > 15, "Reply too short"
    print("[PASS] Greeting test passed!")

    # 2. Test Identity "who are you"
    print("\n>> 2. Testing 'who are you'...")
    res2 = await jarvis_orchestrator.handle_user_input("who are you")
    print(f"Type: {res2.get('type')}")
    print(f"Reply: {res2.get('reply')[:120]}...")
    assert res2.get('type') == 'greeting'
    assert "Jarvis" in res2.get('reply') or "jarvis" in res2.get('reply').lower()
    print("[PASS] Identity check passed!")

    # 3. Test Repeated Greeting "hi jarvis" (ensure no repetition bias trap)
    print("\n>> 3. Testing repeated greeting 'hi jarvis'...")
    res3 = await jarvis_orchestrator.handle_user_input("hi jarvis")
    print(f"Type: {res3.get('type')}")
    print(f"Reply: {res3.get('reply')}")
    assert res3.get('reply').strip() not in ["Sir.", "Sir"]
    assert len(res3.get('reply')) > 15
    print("[PASS] Repetition trap prevented!")

    # 4. Test Time Query
    print("\n>> 4. Testing 'what time is it?'...")
    res4 = await jarvis_orchestrator.handle_user_input("what time is it?")
    print(f"Type: {res4.get('type')}")
    print(f"Reply: {res4.get('reply')}")
    assert res4.get('type') == 'time_report'
    print("[PASS] Time query passed!")

    # 5. Test Weather Query
    print("\n>> 5. Testing 'what is the weather in London?'...")
    res5 = await jarvis_orchestrator.handle_user_input("what is the weather in London?")
    print(f"Type: {res5.get('type')}")
    print(f"Reply: {res5.get('reply')}")
    assert res5.get('type') == 'weather_report'
    print("[PASS] Weather query passed!")

    # 6. Test App Launching
    print("\n>> 6. Testing 'open notepad'...")
    res6 = await jarvis_orchestrator.handle_user_input("open notepad")
    print(f"Type: {res6.get('type')}")
    print(f"Reply: {res6.get('reply')}")
    assert res6.get('type') == 'app_launched'
    print("[PASS] App launcher passed!")

    print("\n" + "=" * 60)
    print("   ALL TESTS PASSED 100% SUCCESSFUL!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_all_scenarios())
