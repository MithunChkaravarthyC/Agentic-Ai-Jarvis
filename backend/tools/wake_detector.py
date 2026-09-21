"""
Acoustic Double-Clap and Voice Wake-Word Detector for J.A.R.V.I.S.
Enables waking up the system via:
1. Double clap (👏 👏) followed by "Wake up Jarvis"
2. Or speaking "Wake up Jarvis" directly
Once awakened, launches Chrome to the J.A.R.V.I.S. HUD.
"""

import time
import os
import sys
import threading
import subprocess
import webbrowser
from pathlib import Path

try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    np = None
    sd = None

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    sr = None


def launch_chrome(url: str):
    """Explicitly launch Google Chrome with the given URL, with fallbacks."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for cp in chrome_paths:
        if os.path.exists(cp):
            try:
                print(f">> [LAUNCHER] Opening Google Chrome: {cp} -> {url}")
                subprocess.Popen([cp, url])
                return True
            except Exception as e:
                print(f">> [LAUNCHER] Chrome launch attempt failed: {e}")

    # Fallback to system default
    try:
        webbrowser.open(url, new=2)
        return True
    except Exception:
        try:
            os.startfile(url)
            return True
        except Exception:
            return False


class AcousticWakeDetector:
    def __init__(self, port: int = 8000):
        self.port = port
        self.url = f"http://localhost:{port}"
        self.sample_rate = 16000
        self.chunk_size = 800  # 50ms per chunk at 16kHz
        self.running = False
        self.awakened = False

        # Clap detection state
        self.noise_floor = 200.0
        self.last_clap_time = 0.0
        self.clap_count = 0
        self.double_clap_time = 0.0
        self.waiting_for_voice = False

        # Voice recording buffer
        self.audio_buffer = []
        self.buffer_max_chunks = int(3.0 * (self.sample_rate / self.chunk_size))  # ~3 seconds of audio
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None

    def _audio_callback(self, indata, frames, time_info, status):
        """Streaming callback for real-time audio analysis."""
        if not self.running or self.awakened:
            return

        chunk = indata[:, 0]
        peak = float(np.max(np.abs(chunk)))
        rms = float(np.sqrt(np.mean(chunk.astype(float)**2)))

        # Update rolling background noise floor
        self.noise_floor = 0.96 * self.noise_floor + 0.04 * max(rms, 10.0)

        now = time.time()

        # Clap threshold: must be a sharp spike significantly above ambient noise
        clap_threshold = max(3500.0, self.noise_floor * 5.5)

        if peak > clap_threshold:
            time_since_last_clap = now - self.last_clap_time
            if 0.15 <= time_since_last_clap <= 1.2:
                # Double clap confirmed!
                self.clap_count = 2
                self.double_clap_time = now
                self.waiting_for_voice = True
                self.last_clap_time = 0.0
                print("\n>> [ACOUSTIC SENSOR] 👏 👏 DOUBLE CLAP DETECTED!", flush=True)
                print(">> [AUTHENTICATION] Listening for: \"Wake up Jarvis\"...\n", flush=True)
                self._play_chime()
            else:
                self.last_clap_time = now
                self.clap_count = 1

        # Reset clap count if too much time passed
        if self.clap_count == 1 and (now - self.last_clap_time) > 1.3:
            self.clap_count = 0

        # Append to audio buffer for voice recognition
        self.audio_buffer.append(chunk.copy())
        if len(self.audio_buffer) > self.buffer_max_chunks:
            self.audio_buffer.pop(0)

    def _play_chime(self):
        """Audio feedback confirmation."""
        try:
            import winsound
            winsound.Beep(1200, 120)
            winsound.Beep(1600, 150)
        except Exception:
            pass

    def _speak_wake_greeting(self):
        """Speak brief wake greeting through TTS engine if available."""
        try:
            from backend.agents.tts_agent import tts_agent
            tts_agent.speak("Good day, Sir. Systems energized. Launching interface now.")
        except Exception:
            pass

    def trigger_wake(self, reason: str = "Acoustic Wake Event"):
        """Awakens Jarvis and launches Chrome."""
        if self.awakened:
            return
        self.awakened = True
        self.running = False

        print("\n=======================================================", flush=True)
        print(f">> [WAKE CONFIRMED] Trigger: {reason}", flush=True)
        print(">> J.A.R.V.I.S. ACTIVATING... ENERGIZING ARC REACTOR!", flush=True)
        print("=======================================================\n", flush=True)

        self._play_chime()

        # Run TTS and browser launch
        threading.Thread(target=self._speak_wake_greeting, daemon=True).start()
        time.sleep(0.4)
        launch_chrome(self.url)

    def run_detector_loop(self):
        """Main listening loop."""
        if not AUDIO_AVAILABLE:
            print("[Warning] sounddevice or numpy not installed. Cannot listen for claps.", flush=True)
            return

        self.running = True
        print("\n=======================================================", flush=True)
        print(">> J.A.R.V.I.S. ACOUSTIC STANDBY SENSOR ONLINE", flush=True)
        print(">> [WAKE TRIGGER]: Clap twice (👏 👏) and say \"Wake up Jarvis\"", flush=True)
        print(f">> Target Interface: {self.url}", flush=True)
        print("=======================================================\n", flush=True)

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=self.chunk_size,
                callback=self._audio_callback
            ):
                last_voice_check = time.time()

                while self.running and not self.awakened:
                    time.sleep(0.3)
                    now = time.time()

                    # Periodic voice recognition check every ~1.5s if audio is present or double clap was heard
                    if (now - last_voice_check) >= 1.2 and len(self.audio_buffer) >= (self.buffer_max_chunks // 2):
                        last_voice_check = now
                        self._check_voice_wake()

                    # Timeout waiting for voice after double clap: after 8 seconds, if no voice, reset
                    if self.waiting_for_voice and (now - self.double_clap_time) > 8.0:
                        print(">> [ACOUSTIC SENSOR] Standby window expired. Clap twice again to initiate.", flush=True)
                        self.waiting_for_voice = False

        except Exception as e:
            print(f">> [Wake Detector Note]: {e}", flush=True)

    def _check_voice_wake(self):
        """Check the audio buffer for wake phrases like 'wake up jarvis' or 'jarvis'."""
        if not SR_AVAILABLE or not self.audio_buffer:
            return

        try:
            raw_audio = np.concatenate(self.audio_buffer).tobytes()
            audio_data = sr.AudioData(raw_audio, self.sample_rate, 2)
            text = self.recognizer.recognize_google(audio_data, language="en-US").lower()
            
            print(f">> [MIC HEARD]: \"{text}\"", flush=True)

            # Check if wake phrase matches
            wake_phrases = ["wake up jarvis", "wake up", "jarvis", "open jarvis", "hey jarvis", "start jarvis"]
            matched = any(phrase in text for phrase in wake_phrases)

            if matched:
                if self.waiting_for_voice:
                    self.trigger_wake("Double Clap (👏 👏) + Voice 'Wake up Jarvis'")
                else:
                    self.trigger_wake(f"Voice Command: \"{text}\"")
        except sr.UnknownValueError:
            # Silence or incomprehensible noise, normal
            pass
        except Exception:
            pass


def start_wake_word_listener(port: int = 8000) -> threading.Thread:
    """Launch the wake word and clap detector in a background thread."""
    detector = AcousticWakeDetector(port=port)
    t = threading.Thread(target=detector.run_detector_loop, daemon=True)
    t.start()
    return t
