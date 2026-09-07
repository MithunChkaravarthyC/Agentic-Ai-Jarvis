import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from backend.config import MODEL_ROUTING
from backend.ollama_client import ollama_client
from backend.prompts import VISION_AGENT_SYSTEM_PROMPT

logger = logging.getLogger("VisionAgent")

class VisionAgent:
    def __init__(self):
        self.model = MODEL_ROUTING["vision"]

    def _encode_image(self, image_path: Path) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    async def analyze_screen(self, image_path: Path, question: str = "Analyze this web page and extract key information like items, totals, or errors.") -> str:
        """Inspect a screenshot using MiniCPM-V and answer questions."""
        if not image_path.exists():
            return "Screenshot file not found."

        try:
            image_b64 = self._encode_image(image_path)
            prompt = f"Examine this webpage screenshot carefully and answer: {question}"

            logger.info(f"VisionAgent inspecting {image_path.name} with {self.model}...")
            response = await ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=VISION_AGENT_SYSTEM_PROMPT,
                images=[image_b64],
                options={"temperature": 0.1, "num_predict": 256}
            )
            return response.strip()
        except Exception as e:
            logger.error(f"VisionAgent failed to inspect image: {e}")
            return f"Vision inspection failed: {str(e)}"

    async def verify_page_state(self, image_path: Path) -> Dict[str, Any]:
        """Detect what stage the browser is on (Home, Search, Cart, Payment, Confirmation)."""
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

vision_agent = VisionAgent()
