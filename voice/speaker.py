import pyttsx3
import threading
import queue
import logging

logger = logging.getLogger(__name__)

class Speaker:
    """
    Thread-safe TTS speaker.
    """

    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        logger.info("Speaker ready")

    def speak(self, text: str):
        if text:
            logger.info(f"SAY → {text}")
            self._queue.put(text)

    def _worker(self):
        try:
            engine = pyttsx3.init('sapi5')  # 🔥 FORCE WINDOWS DRIVER

            engine.setProperty('rate', 170)
            engine.setProperty('volume', 1.0)

            voices = engine.getProperty('voices')

            # 🔥 safer voice selection
            if voices:
                engine.setProperty('voice', voices[0].id)

            logger.info("✅ TTS engine initialised")

            while True:
                text = self._queue.get()

                if text is None:
                    break

                try:
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()  # 🔥 IMPORTANT FIX
                except Exception as e:
                    logger.error(f"TTS error: {e}")

        except Exception as e:
            logger.error(f"TTS init failed: {e}", exc_info=True)

    def stop(self):
        self._queue.put(None)