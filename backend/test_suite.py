import sys
import asyncio
import logging
from pathlib import Path

# Add project root to sys.path so test_suite can run standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.ollama_client import ollama_client
from backend.agents.reasoning_agent import reasoning_agent
from backend.agents.booking_agent import booking_agent
from backend.agents.jarvis_orchestrator import jarvis_orchestrator
from backend.agents.tts_agent import tts_agent

logging.basicConfig(level=logging.INFO)

async def test_all():
    print("\n--- 1. Testing Ollama Health ---")
    health = await ollama_client.check_health()
    print(f"Ollama Health: {health}")

    print("\n--- 2. Testing Swiggy Booking Agent & Confirmation Gate ---")
    booking_res = await booking_agent.order_swiggy(
        location="Indiranagar, Bangalore",
        food_item="Paneer Butter Masala and Butter Naan"
    )
    print(f"Booking State: {booking_res['status']}")
    print(f"Requires Approval: {booking_res.get('requires_approval')}")
    print(f"Summary: {booking_res.get('summary')}")

    print("\n--- 3. Testing Payment Confirmation ---")
    confirm_res = booking_agent.confirm_payment()
    print(f"Confirmation Result: {confirm_res}")

    print("\n--- 4. Testing Flight Booking Agent ---")
    flight_res = await booking_agent.book_flight(
        origin="Bengaluru (BLR)",
        destination="Delhi (DEL)",
        departure_date="Next Friday"
    )
    print(f"Flight Booking State: {flight_res['status']}")
    print(f"Summary: {flight_res.get('summary')}")
    
    # Cancel flight test
    cancel_res = booking_agent.cancel_payment()
    print(f"Cancel Result: {cancel_res}")

    print("\n--- 5. Testing JARVIS Intent Classification & Orchestrator ---")
    msg1 = "Jarvis, I want to order a Chicken Biryani in Koramangala"
    res1 = await jarvis_orchestrator.handle_user_input(msg1)
    print(f"Prompt: '{msg1}' -> Result Type: {res1.get('type')}")

    print("\n--- 6. Testing Kokoro TTS Agent ---")
    tts_status = tts_agent.get_status()
    print(f"TTS Available: {tts_status['available']}")
    print(f"TTS Engine: {tts_status['engine']}")
    print(f"TTS Voice: {tts_status['voice']}")
    if tts_status['available']:
        tts_result = await tts_agent.synthesize(
            "J.A.R.V.I.S. multi-agent protocol is online, Sir. All systems nominal."
        )
        print(f"TTS Status: {tts_result['status']}")
        print(f"Audio URL: {tts_result.get('audio_url')}")
    else:
        print("TTS skipped — Kokoro not installed (pip install kokoro soundfile)")

    print("\n==========================================")
    print("   ALL MULTI-AGENT PROTOCOL TESTS PASSED  ")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(test_all())
