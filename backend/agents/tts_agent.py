import os
import re
import time
import logging
import asyncio
import hashlib
from pathlib import Path

from backend.config import AUDIO_DIR, TTS_VOICE, TTS_LANG_CODE

logger = logging.getLogger("TTSAgent")
CACHE_DIR = AUDIO_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class TTSAgent:
    """
    Text-to-Speech agent powered by Kokoro-82M.
    Generates natural, high-quality speech audio files locally on CPU with persistent disk caching.
    """

    def __init__(self):
        self.pipeline = None
        self.voice = TTS_VOICE
        self.lang_code = TTS_LANG_CODE
        self.sample_rate = 24000
        self.available = False
        self._initialized = False

    def _ensure_pipeline(self):
        """Initialize the Kokoro TTS pipeline. Gracefully degrades if not installed."""
        if self._initialized:
            return
        self._initialized = True
        try:
            import torch
            # Set optimal PyTorch CPU inference threads
            if hasattr(torch, "set_num_threads"):
                cpu_cnt = os.cpu_count() or 4
                torch.set_num_threads(min(8, cpu_cnt))

            from kokoro import KPipeline
            self.pipeline = KPipeline(lang_code=self.lang_code, repo_id='hexgrad/Kokoro-82M')
            self.available = True
            logger.info(f"Kokoro-82M TTS initialized — voice='{self.voice}', lang='{self.lang_code}'")
        except ImportError:
            logger.warning(
                "Kokoro TTS not installed. Install with: pip install kokoro soundfile. "
                "Also requires espeak-ng system package."
            )
        except Exception as e:
            logger.warning(f"Kokoro TTS initialization failed: {e}")

    def warmup(self):
        """Warm up Kokoro pipeline during server boot and pre-synthesize top common phrases."""
        self._ensure_pipeline()
        if self.available and self.pipeline:
            try:
                import torch
                with torch.inference_mode():
                    list(self.pipeline("Online, Sir.", voice=self.voice, speed=1.1))

                # Pre-synthesize top common phrases into permanent disk cache for 0ms instant playback
                common_phrases = [
                    "J.A.R.V.I.S. multi-agent protocol is online, Sir. All systems nominal.",
                    "Certainly, Sir. Right away.",
                    "Session context cleared, Sir.",
                    "Authorization received. Transaction confirmed.",
                    "Transaction cancelled, Sir.",
                    "Atmospheric sensors updated, Sir."
                ]
                for phrase in common_phrases:
                    clean = self._clean_text(phrase)
                    h = hashlib.md5(f"{self.voice}_{clean}".encode()).hexdigest()
                    target = CACHE_DIR / f"tts_{h}.wav"
                    if not target.exists():
                        self._generate_audio(clean, self.voice, str(target))

                logger.info("Kokoro-82M TTS pre-warmed with permanent phrase cache for instant playback.")
            except Exception as e:
                logger.warning(f"Kokoro warmup encountered: {e}")

    def _clean_text(self, text: str) -> str:
        """Strip HTML, markdown, roleplay actions, asterisks, URLs, and excessive whitespace for natural speech."""
        if not text:
            return ""
        # Remove code blocks entirely
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove inline code backticks
        text = re.sub(r'`[^`]*`', '', text)
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', text)
        # Remove markdown links [text](url) -> text
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # 1. First unwrap markdown bold/italic markers while preserving the text inside: **word** -> word
        text = re.sub(r'\*\*+(.*?)\*\*+', r'\1', text)
        text = re.sub(r'__+(.*?)__+', r'\1', text)
        # 2. Remove stage directions and roleplay actions in asterisks: e.g. *chuckles*, *sighs*, *smiles*, *nods*
        text = re.sub(r'(?<!\*)\*(?!\*)[a-zA-Z\s_\-]{1,35}\*(?!\*)', '', text)
        # 3. Remove parenthetical stage directions: e.g. (chuckles), (laughs), (whispers), (clears throat)
        text = re.sub(r'\([a-zA-Z\s_\-]{2,40}\)', '', text)
        # Remove markdown headers, blockquotes, bullets
        text = re.sub(r'^[\s*#\-+>]+', '', text, flags=re.MULTILINE)
        # Strip all remaining rogue asterisks, tildes, hashes, backticks, brackets, pipes
        text = re.sub(r'[*_~#`^|\\<>{}\[\]]', '', text)
        # Remove emojis and non-speech symbols
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # For instant speech response, extract the core spoken thought (first 1-2 complete sentences)
        if len(text) > 240:
            truncated = text[:240]
            last_punct = max(truncated.rfind('. '), truncated.rfind('! '), truncated.rfind('? '))
            if last_punct > 80:
                text = truncated[:last_punct + 1]
            else:
                text = truncated.rsplit(' ', 1)[0] + '.'

        return text

    async def synthesize(self, text: str, voice: str = None) -> dict:
        """
        Synthesize speech from text using Kokoro-82M with sub-second latency and persistent disk caching.
        
        Args:
            text: The text to convert to speech.
            voice: Optional voice override (e.g., 'bf_emma', 'bm_daniel', 'af_heart').
            
        Returns:
            dict with 'audio_url' (str) and 'status' (str).
        """
        self._ensure_pipeline()
        if not self.available or not self.pipeline:
            return {"status": "unavailable", "audio_url": None}

        clean_text = self._clean_text(text)
        if not clean_text or len(clean_text) < 3:
            return {"status": "skipped", "audio_url": None, "reason": "Text too short"}

        use_voice = voice or self.voice
        phrase_hash = hashlib.md5(f"{use_voice}_{clean_text}".encode()).hexdigest()
        cached_file = CACHE_DIR / f"tts_{phrase_hash}.wav"
        cached_url = f"/audio/cache/tts_{phrase_hash}.wav"

        # Ultra-fast path: return persistent cached audio in 0.001 seconds
        if cached_file.exists() and cached_file.stat().st_size > 1000:
            return {"status": "success", "audio_url": cached_url, "cached": True}

        try:
            # Run synthesis in a thread pool to avoid blocking the async event loop
            audio_data = await asyncio.to_thread(
                self._generate_audio, clean_text, use_voice, str(cached_file)
            )
            
            if audio_data and cached_file.exists():
                logger.info(f"Kokoro TTS generated: tts_{phrase_hash}.wav ({len(clean_text)} chars)")
                return {"status": "success", "audio_url": cached_url}
            else:
                return {"status": "error", "audio_url": None, "reason": "No audio generated"}

        except Exception as e:
            logger.error(f"Kokoro TTS synthesis failed: {e}")
            return {"status": "error", "audio_url": None, "reason": str(e)}

    def _generate_audio(self, text: str, voice: str, filepath: str) -> bool:
        """Synchronous audio generation using torch.inference_mode()."""
        import soundfile as sf
        import numpy as np
        import torch

        all_audio = []
        with torch.inference_mode():
            generator = self.pipeline(text, voice=voice, speed=1.1)
            for i, (gs, ps, audio) in enumerate(generator):
                if audio is not None:
                    all_audio.append(audio)

        if all_audio:
            combined = np.concatenate(all_audio)
            sf.write(filepath, combined, self.sample_rate)
            return True
        return False

    def cleanup_old_audio(self, max_age_seconds: int = 300):
        """Remove audio files older than max_age_seconds to save disk space, preserving recent cache."""
        now = time.time()
        for f in AUDIO_DIR.glob("jarvis_tts_*.wav"):
            try:
                if now - f.stat().st_mtime > max_age_seconds:
                    f.unlink()
            except Exception:
                pass

    def get_status(self) -> dict:
        """Return TTS agent status info without blocking the event loop."""
        if not self._initialized:
            import importlib.util
            self.available = importlib.util.find_spec("kokoro") is not None

        return {
            "available": self.available,
            "engine": "Kokoro-82M",
            "voice": self.voice,
            "lang_code": self.lang_code,
            "sample_rate": self.sample_rate
        }


# Singleton instance
tts_agent = TTSAgent()
