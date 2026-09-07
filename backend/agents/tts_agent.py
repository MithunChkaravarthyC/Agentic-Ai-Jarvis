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
    High-Performance Neural Text-to-Speech Engine.
    Uses Microsoft Edge-TTS (en-GB-RyanNeural) for human-like British J.A.R.V.I.S. eloquence
    with persistent disk caching for 0ms instant repeated playback.
    Includes automatic fallback to Kokoro / browser synthesis.
    """

    def __init__(self):
        self.voice = TTS_VOICE
        self.lang_code = TTS_LANG_CODE
        self.sample_rate = 24000
        self.has_edge_tts = False
        self.has_kokoro = False
        self.kokoro_pipeline = None
        self._check_engines()

    def _check_engines(self):
        """Detect installed TTS engines without blocking."""
        try:
            import edge_tts
            self.has_edge_tts = True
            logger.info(f"Edge-TTS engine online (Voice: '{self.voice}')")
        except ImportError:
            self.has_edge_tts = False

        # Check kokoro safely without hanging on Windows AppLocker
        try:
            import kokoro
            self.has_kokoro = True
        except Exception:
            self.has_kokoro = False

    def _ensure_kokoro(self):
        """Lazy-load Kokoro only if edge-tts is unavailable."""
        if self.kokoro_pipeline is not None or not self.has_kokoro:
            return
        try:
            from kokoro import KPipeline
            self.kokoro_pipeline = KPipeline(lang_code='b', repo_id='hexgrad/Kokoro-82M')
        except Exception as e:
            logger.warning(f"Kokoro initialization failed: {e}")
            self.has_kokoro = False

    def warmup(self):
        """Pre-warm TTS and pre-synthesize top common phrases for instant 0ms playback."""
        common_phrases = [
            "J.A.R.V.I.S. multi-agent protocol is online, Sir. All systems nominal.",
            "Certainly, Sir. Right away.",
            "Session context cleared, Sir.",
            "Authorization received. Transaction confirmed.",
            "Transaction cancelled, Sir.",
            "Atmospheric sensors updated, Sir."
        ]

        async def _warmup_async():
            for phrase in common_phrases:
                clean = self._clean_text(phrase)
                h = hashlib.md5(f"{self.voice}_{clean}".encode()).hexdigest()
                target_mp3 = CACHE_DIR / f"tts_{h}.mp3"
                if not target_mp3.exists():
                    await self._generate_edge_tts(clean, self.voice, str(target_mp3))

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_warmup_async())
            else:
                loop.run_until_complete(_warmup_async())
            logger.info("TTS phrase cache pre-warmed for instant sub-second playback.")
        except Exception as e:
            logger.warning(f"TTS warmup note: {e}")

    def _clean_text(self, text: str) -> str:
        """Strip HTML, markdown, roleplay actions, asterisks, URLs, and excess whitespace for natural speech."""
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
        # Normalize dotted J.A.R.V.I.S. to fluent word "Jarvis" so TTS speaks humanly
        text = re.sub(r'\bJ\.?A\.?R\.?V\.?I\.?S\.?\b', 'Jarvis', text, flags=re.IGNORECASE)
        # Unwrap markdown bold/italic markers while preserving the text inside: **word** -> word
        text = re.sub(r'\*\*+(.*?)\*\*+', r'\1', text)
        text = re.sub(r'__+(.*?)__+', r'\1', text)
        # Remove stage directions and roleplay actions in asterisks: e.g. *chuckles*, *sighs*, *smiles*, *nods*
        text = re.sub(r'(?<!\*)\*(?!\*)[a-zA-Z\s_\-]{1,35}\*(?!\*)', '', text)
        # Remove parenthetical stage directions: e.g. (chuckles), (laughs), (whispers), (clears throat)
        text = re.sub(r'\([a-zA-Z\s_\-]{2,40}\)', '', text)
        # Remove markdown headers, blockquotes, bullets
        text = re.sub(r'^[\s*#\-+>]+', '', text, flags=re.MULTILINE)
        # Strip all remaining rogue asterisks, tildes, hashes, backticks, brackets, pipes
        text = re.sub(r'[*_~#`^|\\<>{}\[\]]', '', text)
        # Remove emojis and non-speech symbols
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # For conversational speech, extract the core spoken thoughts (first 1-2 complete sentences)
        if len(text) > 280:
            truncated = text[:280]
            last_punct = max(truncated.rfind('. '), truncated.rfind('! '), truncated.rfind('? '))
            if last_punct > 80:
                text = truncated[:last_punct + 1]
            else:
                text = truncated.rsplit(' ', 1)[0] + '.'

        return text

    async def _generate_edge_tts(self, text: str, voice: str, filepath: str) -> bool:
        """Synthesize neural speech via Edge-TTS asynchronously."""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
            return Path(filepath).exists() and Path(filepath).stat().st_size > 500
        except Exception as e:
            logger.warning(f"Edge-TTS synthesis error: {e}")
            return False

    def _generate_kokoro(self, text: str, voice: str, filepath: str) -> bool:
        """Synchronous Kokoro generation fallback."""
        self._ensure_kokoro()
        if not self.kokoro_pipeline:
            return False
        try:
            import soundfile as sf
            import numpy as np
            import torch

            all_audio = []
            with torch.inference_mode():
                generator = self.kokoro_pipeline(text, voice='bf_emma', speed=1.1)
                for _, _, audio in generator:
                    if audio is not None:
                        all_audio.append(audio)

            if all_audio:
                combined = np.concatenate(all_audio)
                sf.write(filepath, combined, self.sample_rate)
                return True
        except Exception as e:
            logger.warning(f"Kokoro fallback error: {e}")
        return False

    async def synthesize(self, text: str, voice: str = None) -> dict:
        """
        Synthesize speech from text with sub-second latency and persistent disk caching.
        
        Args:
            text: Text to convert to speech.
            voice: Optional voice override.
            
        Returns:
            dict with 'status', 'audio_url', and 'cached' boolean.
        """
        clean_text = self._clean_text(text)
        if not clean_text or len(clean_text) < 2:
            return {"status": "skipped", "audio_url": None, "reason": "Text too short"}

        use_voice = voice or self.voice
        phrase_hash = hashlib.md5(f"{use_voice}_{clean_text}".encode()).hexdigest()

        # Check MP3 cache first (Edge-TTS)
        cached_mp3 = CACHE_DIR / f"tts_{phrase_hash}.mp3"
        cached_url_mp3 = f"/audio/cache/tts_{phrase_hash}.mp3"
        if cached_mp3.exists() and cached_mp3.stat().st_size > 500:
            return {"status": "success", "audio_url": cached_url_mp3, "cached": True}

        # Check WAV cache (Kokoro)
        cached_wav = CACHE_DIR / f"tts_{phrase_hash}.wav"
        cached_url_wav = f"/audio/cache/tts_{phrase_hash}.wav"
        if cached_wav.exists() and cached_wav.stat().st_size > 1000:
            return {"status": "success", "audio_url": cached_url_wav, "cached": True}

        # Priority 1: High-Speed Edge-TTS Neural Voice (Sub-second)
        if self.has_edge_tts:
            success = await self._generate_edge_tts(clean_text, use_voice, str(cached_mp3))
            if success:
                logger.info(f"Edge-TTS synthesized: tts_{phrase_hash}.mp3 ({len(clean_text)} chars)")
                return {"status": "success", "audio_url": cached_url_mp3, "cached": False}

        # Priority 2: Kokoro local fallback
        if self.has_kokoro:
            success = await asyncio.to_thread(self._generate_kokoro, clean_text, use_voice, str(cached_wav))
            if success:
                logger.info(f"Kokoro synthesized: tts_{phrase_hash}.wav ({len(clean_text)} chars)")
                return {"status": "success", "audio_url": cached_url_wav, "cached": False}

        logger.warning(f"No server-side TTS engine succeeded for: '{clean_text[:40]}...'")
        return {"status": "unavailable", "audio_url": None, "text_fallback": clean_text}

    def cleanup_old_audio(self, max_age_seconds: int = 3600):
        """Remove audio files older than max_age_seconds, preserving cache directory."""
        now = time.time()
        for f in AUDIO_DIR.glob("jarvis_tts_*.*"):
            try:
                if now - f.stat().st_mtime > max_age_seconds:
                    f.unlink()
            except Exception:
                pass

    def get_status(self) -> dict:
        """Return TTS engine status."""
        return {
            "available": self.has_edge_tts or self.has_kokoro,
            "engine": "Edge-TTS Neural" if self.has_edge_tts else ("Kokoro-82M" if self.has_kokoro else "Browser WebSpeech"),
            "voice": self.voice,
            "lang_code": self.lang_code,
            "sample_rate": self.sample_rate
        }

# Global singleton
tts_agent = TTSAgent()
