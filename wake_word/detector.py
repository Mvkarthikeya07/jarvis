import pyaudio
import numpy as np
import threading
import time
import logging

logger = logging.getLogger(__name__)

# ✅ SET THIS to your working mic index (same as listener.py)
MIC_INDEX = None  # e.g. MIC_INDEX = 1

class WakeWordDetector:
    def __init__(self, callback):
        self.callback = callback
        self.is_running = False

        self.sample_rate = 16000
        self.chunk_size = 1024

        # Energy level that counts as "someone is speaking"
        # Raise this if it triggers on background noise
        # Lower this if it's not triggering when you speak
        self.energy_threshold = 0.015

        # How many consecutive loud chunks = a "wake word attempt"
        # At 50ms per chunk, 8 chunks = ~400ms of sustained speech
        self.trigger_count = 8

        self._consecutive = 0
        self._current_energy = 0.0
        self._stream = None
        self._audio = None

    def start(self):
        self.is_running = True
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        logger.info("Wake detector started")

    def stop(self):
        self.is_running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass

    def _run(self):
        try:
            self._audio = pyaudio.PyAudio()

            open_kwargs = dict(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            if MIC_INDEX is not None:
                open_kwargs["input_device_index"] = MIC_INDEX

            self._stream = self._audio.open(**open_kwargs)
            logger.info(f"🎤 Wake detector listening (energy threshold={self.energy_threshold})")

            cooldown = False
            cooldown_until = 0

            while self.is_running:
                try:
                    raw = self._stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(raw, dtype=np.float32)
                    energy = float(np.sqrt(np.mean(audio_data ** 2)))
                    self._current_energy = energy

                    # Skip during cooldown
                    if cooldown:
                        if time.time() > cooldown_until:
                            cooldown = False
                            self._consecutive = 0
                        continue

                    if energy > self.energy_threshold:
                        self._consecutive += 1
                        if self._consecutive >= self.trigger_count:
                            logger.info(f"🔥 Wake word triggered! (energy={energy:.4f})")
                            if self.callback:
                                self.callback()
                            cooldown = True
                            cooldown_until = time.time() + 2.5  # 2.5s cooldown
                            self._consecutive = 0
                    else:
                        # Decay counter so brief noise doesn't accumulate
                        self._consecutive = max(0, self._consecutive - 1)

                except IOError as e:
                    logger.warning(f"Audio read error: {e}")
                    time.sleep(0.05)

        except Exception as e:
            logger.error(f"Wake detector fatal error: {e}", exc_info=True)
        finally:
            self.stop()