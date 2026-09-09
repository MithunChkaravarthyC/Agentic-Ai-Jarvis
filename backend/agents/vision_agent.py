"""
vision_agent.py — Computer Vision & Multimodal Screen Perception Specialist for JARVIS.
Wraps screen_capture_tool + MiniCPM-V:latest via Ollama.
Guarantees single request/response cycle: capture -> compress -> infer -> unload/release VRAM.
Zero persistent VRAM overhead on RTX 4060 (8GB).
"""

import time
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from backend.config import MODEL_ROUTING
from backend.ollama_client import ollama_client
from backend.prompts import VISION_AGENT_SYSTEM_PROMPT, WEBCAM_AGENT_SYSTEM_PROMPT
from backend.tools.screen_capture_tool import screen_capture_tool
from backend.tools.webcam_capture_tool import webcam_capture_tool

logger = logging.getLogger("VisionAgent")

# CrewAI Tool compatibility
try:
    from crewai.tools import BaseTool
except ImportError:
    class BaseTool:
        name: str = ""
        description: str = ""
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class ScreenPerceptionTool(BaseTool):
    name: str = "screen_perception_tool"
    description: str = (
        "Captures a single on-demand screenshot of the user's screen (<=1280px compressed), "
        "inspects it with MiniCPM-V using a specialized prompt, returns an articulate answer, "
        "and immediately evicts the vision model from GPU VRAM."
    )

    def _run(self, question: str = "What is visible on my screen?", monitor: str = "primary") -> str:
        """CrewAI synchronous entrypoint with event loop detection and thread pool dispatch."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def _run_in_isolated_loop():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                res = new_loop.run_until_complete(vision_agent.perceive_screen(question=question, monitor=monitor))
                return res.get("answer", "")
            finally:
                new_loop.close()

        try:
            asyncio.get_running_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_in_isolated_loop)
                return future.result()
        except RuntimeError:
            return _run_in_isolated_loop()

    async def _arun(self, question: str = "What is visible on my screen?", monitor: str = "primary") -> str:
        """CrewAI asynchronous entrypoint (preferred path for async orchestrators)."""
        res = await vision_agent.perceive_screen(question=question, monitor=monitor)
        return res.get("answer", "")


class WebcamPerceptionTool(BaseTool):
    name: str = "webcam_perception_tool"
    description: str = (
        "Captures a single on-demand camera frame of the physical world, "
        "inspects physical objects, documents, or scenes with MiniCPM-V, "
        "returns an articulate answer, and immediately evicts the vision model from GPU VRAM."
    )

    def _run(self, question: str = "What is in front of the camera?", camera_index: int = 0) -> str:
        """CrewAI synchronous entrypoint with event loop detection and thread pool dispatch."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def _run_in_isolated_loop():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                res = new_loop.run_until_complete(vision_agent.perceive_webcam(question=question, camera_index=camera_index))
                return res.get("answer", "")
            finally:
                new_loop.close()

        try:
            asyncio.get_running_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_in_isolated_loop)
                return future.result()
        except RuntimeError:
            return _run_in_isolated_loop()

    async def _arun(self, question: str = "What is in front of the camera?", camera_index: int = 0) -> str:
        """CrewAI asynchronous entrypoint."""
        res = await vision_agent.perceive_webcam(question=question, camera_index=camera_index)
        return res.get("answer", "")


class VisionAgent:
    """Autonomous Computer Vision Agent with zero persistent VRAM residency."""

    def __init__(self):
        self.model = MODEL_ROUTING["vision"]
        self.tool = ScreenPerceptionTool()
        self.webcam_tool = WebcamPerceptionTool()

    def _encode_image(self, image_path: Path) -> str:
        """Read image bytes and return base64 encoded string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    async def perceive_screen(
        self,
        question: str = "What is on my screen right now?",
        monitor: Union[str, int] = "primary"
    ) -> Dict[str, Any]:
        """
        Phase 1 Screen Perception:
        1. Capture monitor (downscaled to <=1280px, JPEG 80)
        2. Encode base64
        3. Call MiniCPM-V via Ollama
        4. Immediately evict model from VRAM (keep_alive: 0)
        5. Log performance telemetry (capture time, inference latency, VRAM freed)
        6. Return structured findings
        """
        overall_start = time.perf_counter()

        # Step 1: On-demand screen capture
        capture_meta = screen_capture_tool.capture(monitor=monitor)
        if capture_meta.get("status") != "success":
            return {
                "status": "error",
                "answer": f"I was unable to capture your screen: {capture_meta.get('message', 'Unknown error')}",
                "screenshot_url": None
            }

        image_path = Path(capture_meta["image_path"])
        capture_time_ms = capture_meta["latency_ms"]

        # Step 2: Base64 encoding
        encode_start = time.perf_counter()
        image_b64 = self._encode_image(image_path)
        encode_time_ms = round((time.perf_counter() - encode_start) * 1000.0, 1)

        # Step 3: Single-shot MiniCPM-V inference
        clean_question = question.strip() if question else "Analyze the screen and explain what is visible."
        prompt = f"User Request: {clean_question}\nInspect this screen capture and provide a concise, factual, articulate response."

        logger.info(f"[VisionAgent] Calling {self.model} for screen perception...")
        infer_start = time.perf_counter()

        response = await ollama_client.generate(
            model=self.model,
            prompt=prompt,
            system=VISION_AGENT_SYSTEM_PROMPT,
            images=[image_b64],
            options={"temperature": 0.2, "num_predict": 300},
            keep_alive="0s"  # Evict immediately upon completion
        )

        infer_time_ms = round((time.perf_counter() - infer_start) * 1000.0, 1)

        # Step 4: Proactive VRAM release enforcement
        vram_start = time.perf_counter()
        await ollama_client.unload_model(self.model)
        vram_release_ms = round((time.perf_counter() - vram_start) * 1000.0, 1)

        total_time_ms = round((time.perf_counter() - overall_start) * 1000.0, 1)

        answer = response.strip() if response else "I inspected your screen, Sir, but could not detect distinct details."

        logger.info(
            f"[VisionAgent Performance] Capture: {capture_time_ms}ms | Encode: {encode_time_ms}ms | "
            f"Infer: {infer_time_ms}ms | VRAM Eviction: {vram_release_ms}ms | Total: {total_time_ms}ms | "
            f"Image Size: {capture_meta['file_size_kb']} KB ({capture_meta['resolution'][0]}x{capture_meta['resolution'][1]})"
        )

        return {
            "status": "success",
            "answer": answer,
            "image_path": str(image_path),
            "screenshot_url": capture_meta["url"],
            "telemetry": {
                "capture_time_ms": capture_time_ms,
                "infer_time_ms": infer_time_ms,
                "vram_release_ms": vram_release_ms,
                "total_time_ms": total_time_ms,
                "resolution": capture_meta["resolution"],
                "file_size_kb": capture_meta["file_size_kb"]
            }
        }

    async def analyze_screen(
        self,
        image_path: Path,
        question: str = "Analyze this web page and extract key information like items, totals, or errors."
    ) -> str:
        """Inspect an existing screenshot file with automatic VRAM release."""
        if not image_path.exists():
            return "Screenshot file not found."

        try:
            image_b64 = self._encode_image(image_path)
            prompt = f"Examine this webpage screenshot carefully and answer: {question}"

            logger.info(f"[VisionAgent] Inspecting {image_path.name} with {self.model}...")
            response = await ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=VISION_AGENT_SYSTEM_PROMPT,
                images=[image_b64],
                options={"temperature": 0.1, "num_predict": 256},
                keep_alive="0s"
            )
            # Ensure model evicted
            await ollama_client.unload_model(self.model)
            return response.strip()
        except Exception as e:
            logger.error(f"VisionAgent failed to inspect image: {e}")
            return f"Vision inspection note: {str(e)}"

    async def verify_page_state(self, image_path: Path) -> Dict[str, Any]:
        """Detect stage on screen for gate verification."""
        prompt = """Look at this screenshot and identify the current page state.
Reply with a short JSON or summary containing:
- current_stage (e.g., Search Results, Cart Summary, Payment Screen, Confirmation)
- total_amount_detected (if any)
- items_or_flights_listed (summary)
"""
        analysis = await self.analyze_screen(image_path, prompt)
        return {
            "analysis": analysis,
            "image_path": str(image_path)
        }

    async def perceive_webcam(
        self,
        question: str = "What am I holding or what is in front of the camera?",
        camera_index: int = 0
    ) -> Dict[str, Any]:
        """
        Phase 3 Webcam Physical Perception:
        1. Capture single camera frame (downscaled to <=1280px, JPEG 80)
        2. Encode base64
        3. Call MiniCPM-V via Ollama using WEBCAM_AGENT_SYSTEM_PROMPT
        4. Immediately evict model from VRAM (keep_alive: 0)
        5. Return structured findings & performance telemetry
        """
        overall_start = time.perf_counter()

        # Step 1: On-demand webcam capture
        capture_meta = webcam_capture_tool.capture(camera_index=camera_index)
        if capture_meta.get("status") == "fallback" or capture_meta.get("source_mode") == "fallback_renderer":
            return {
                "status": "error",
                "answer": "I attempted to access your optical camera, Sir, but the video device is currently unavailable or busy. Please ensure no other application is using your webcam and try again.",
                "screenshot_url": capture_meta.get("url"),
                "telemetry": capture_meta
            }

        image_path = Path(capture_meta["image_path"])
        capture_time_ms = capture_meta["latency_ms"]

        # Step 2: Base64 encoding
        encode_start = time.perf_counter()
        image_b64 = self._encode_image(image_path)
        encode_time_ms = round((time.perf_counter() - encode_start) * 1000.0, 1)

        # Step 3: Single-shot MiniCPM-V physical inference
        clean_question = question.strip() if question else "Inspect the camera view and identify what you see or what is being held."
        prompt = f"User Request: {clean_question}\nAnalyze this camera photo and describe the physical object, document, or scene with precision."

        logger.info(f"[VisionAgent] Calling {self.model} for webcam perception...")
        infer_start = time.perf_counter()

        response = await ollama_client.generate(
            model=self.model,
            prompt=prompt,
            system=WEBCAM_AGENT_SYSTEM_PROMPT,
            images=[image_b64],
            options={"temperature": 0.2, "num_predict": 300},
            keep_alive="0s"
        )
        infer_time_ms = round((time.perf_counter() - infer_start) * 1000.0, 1)

        # Step 4: Proactive VRAM release enforcement
        vram_start = time.perf_counter()
        await ollama_client.unload_model(self.model)
        vram_release_ms = round((time.perf_counter() - vram_start) * 1000.0, 1)

        total_time_ms = round((time.perf_counter() - overall_start) * 1000.0, 1)
        answer = response.strip() if response else "I inspected your camera view, Sir, but could not discern distinct objects."

        logger.info(
            f"[VisionAgent Physical Performance] Capture: {capture_time_ms}ms | Encode: {encode_time_ms}ms | "
            f"Infer: {infer_time_ms}ms | VRAM Eviction: {vram_release_ms}ms | Total: {total_time_ms}ms | "
            f"Image Size: {capture_meta['file_size_kb']} KB ({capture_meta['resolution'][0]}x{capture_meta['resolution'][1]})"
        )

        return {
            "status": "success",
            "answer": answer,
            "image_path": str(image_path),
            "screenshot_url": capture_meta["url"],
            "telemetry": {
                "capture_time_ms": capture_time_ms,
                "infer_time_ms": infer_time_ms,
                "vram_release_ms": vram_release_ms,
                "total_time_ms": total_time_ms,
                "resolution": capture_meta["resolution"],
                "file_size_kb": capture_meta["file_size_kb"],
                "source_mode": capture_meta.get("source_mode", "dedicated_capture")
            }
        }


# Global singleton instance
vision_agent = VisionAgent()

