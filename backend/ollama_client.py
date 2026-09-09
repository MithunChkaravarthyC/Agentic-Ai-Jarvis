import httpx
import json
import re
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from backend.config import OLLAMA_BASE_URL, MODEL_ROUTING

logger = logging.getLogger("JarvisOllama")

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")

    async def check_health(self) -> Dict[str, Any]:
        """Check if Ollama server is reachable and list available models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m["name"] for m in res.json().get("models", [])]
                    return {"status": "online", "models": models}
                return {"status": "error", "error": f"Status code {res.status_code}"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        images: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream completion tokens from Ollama."""
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if images:
            payload["images"] = images
        if options:
            payload["options"] = options

        timeout = httpx.Timeout(120.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status_code != 200:
                        yield f"[Error: Ollama returned status {response.status_code}]"
                        return
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    yield chunk["response"]
                                if chunk.get("done", False):
                                    break
                            except Exception:
                                continue
        except Exception as e:
            logger.error(f"Error streaming from model {model}: {e}")
            yield f"[Ollama Error: {str(e)}]"

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        images: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[Any] = None
    ) -> str:
        """Fetch non-streaming generation from Ollama with automatic fallback."""
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if images:
            payload["images"] = images
        if options:
            payload["options"] = options
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive

        timeout = httpx.Timeout(60.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "")
                else:
                    logger.warning(f"Model {model} returned status {res.status_code}")
        except Exception as e:
            logger.error(f"Failed to generate with {model}: {e}")

    async def unload_model(self, model: str):
        """Immediately evict model from GPU VRAM by setting keep_alive to 0."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": model, "prompt": "", "keep_alive": 0}
                )
                logger.info(f"Model '{model}' evicted from GPU VRAM (status {res.status_code}).")
                return True
        except Exception as e:
            logger.debug(f"Note unloading model {model}: {e}")
            return False

        # Fallback to lighter model if primary model had an issue
        fallback_model = MODEL_ROUTING.get("coder_fallback", "llama3.2:latest")
        if model != fallback_model:
            logger.info(f"Attempting fallback to {fallback_model}...")
            payload["model"] = fallback_model
            # Text models do not accept image arrays
            payload.pop("images", None)
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    res = await client.post(f"{self.base_url}/api/generate", json=payload)
                    if res.status_code == 200:
                        return res.json().get("response", "")
            except Exception as e2:
                logger.error(f"Fallback model also failed: {e2}")

        return ""

    @staticmethod
    def extract_deepseek_reasoning(text: str) -> Dict[str, str]:
        """Extract <think>...</think> chain of thought and clean response for DeepSeek-R1."""
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if think_match:
            thought = think_match.group(1).strip()
            clean_content = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return {"thought": thought, "content": clean_content}
        return {"thought": "", "content": text.strip()}

# Global singleton
ollama_client = OllamaClient()
