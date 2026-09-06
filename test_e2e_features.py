import asyncio
import sys
from pathlib import Path

# Add workspace root
sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.agents.jarvis_orchestrator import jarvis_orchestrator
from backend.tools.time_tool import time_tool
from backend.tools.weather_tool import weather_tool
from backend.agents.code_agent import code_agent

async def test_features():
    print("=" * 65)
    print("   TESTING REAL TIME, LIVE CLIMATE & LUSION 3D ENGINE")
    print("=" * 65)

    # 1. Test Time Query (Local)
    print("\n>> 1. Testing Local Time Query...")
    res_time = await jarvis_orchestrator.handle_user_input("What time is it right now?")
    assert res_time["type"] == "time_report", f"Expected time_report, got {res_time['type']}"
    assert "time_data" in res_time, "time_data missing from response"
    print("Reply:", res_time["reply"])
    print("Time 12H:", res_time["time_data"]["time_12h"])
    print("Date:", res_time["time_data"]["date"])
    print("Day:", res_time["time_data"]["day"])
    print("[PASS] Local Real Time works!")

    # 2. Test Time Query (Target City - Tokyo)
    print("\n>> 2. Testing Target City Time (Tokyo)...")
    res_tokyo = await jarvis_orchestrator.handle_user_input("What is the time in Tokyo?")
    assert res_tokyo["type"] == "time_report"
    assert res_tokyo["time_data"]["city"] == "Tokyo"
    print("Reply:", res_tokyo["reply"])
    print("[PASS] World Time works!")

    # 3. Test Live Climate / Weather (Local)
    print("\n>> 3. Testing Local Live Climate Query...")
    res_weather = await jarvis_orchestrator.handle_user_input("What is the original climate outside?")
    assert res_weather["type"] == "weather_report"
    assert "weather_data" in res_weather
    w = res_weather["weather_data"]
    print("City:", w["city"])
    print("Temperature:", f"{w['temperature_c']}°C / {w['temperature_f']}°F")
    print("Condition:", w["condition"])
    print("Humidity:", f"{w['humidity']}%")
    print("Wind:", f"{w['wind_speed_kmh']} km/h {w['wind_direction']}")
    print("Reply:", res_weather["reply"])
    print("[PASS] Live Local Climate works!")

    # 4. Test Live Climate / Weather (Target City - London)
    print("\n>> 4. Testing Target City Live Weather (London)...")
    res_london = await jarvis_orchestrator.handle_user_input("What is the weather in London?")
    assert res_london["type"] == "weather_report"
    w_lon = res_london["weather_data"]
    print("London Temp:", f"{w_lon['temperature_c']}°C, {w_lon['condition']}")
    print("Reply:", res_london["reply"])
    print("[PASS] Target City Live Weather works!")

    # 5. Test Lusion-Grade 3D Website Generation
    print("\n>> 5. Testing Lusion 3D Website Generator...")
    res_lusion = await jarvis_orchestrator.handle_user_input("Build a 3D website like lusion website in a smooth way")
    assert res_lusion["type"] == "web_app_ready"
    proj = res_lusion["project"]
    print("Project Name:", proj["project_name"])
    print("Preview URL:", proj["preview_url"])
    print("Generated Files:", proj["files"])

    # Verify generated 3D files contain Three.js and lerp
    proj_dir = Path(proj["directory"])
    index_content = (proj_dir / "index.html").read_text(encoding="utf-8")
    app_js_content = (proj_dir / "app.js").read_text(encoding="utf-8")
    
    assert "three.min.js" in index_content, "Three.js CDN missing from index.html"
    assert "0.05" in app_js_content, "Lerp damping factor missing from app.js"
    assert "MeshPhysicalMaterial" in app_js_content, "MeshPhysicalMaterial missing from app.js"
    assert "initParticleSwarm" in app_js_content, "Particle swarm missing from app.js"
    assert "initAudioSynthesizer" in app_js_content, "Audio synthesizer missing from app.js"
    print("[PASS] Lusion 3D Web Application successfully architected and verified!")

    print("\n" + "=" * 65)
    print("   ALL REAL-TIME, CLIMATE & LUSION 3D TESTS PASSED 100%!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_features())
