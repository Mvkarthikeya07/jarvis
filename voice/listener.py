import speech_recognition as sr
import threading
import time
import logging

logger = logging.getLogger(__name__)

# ✅ SET THIS to your working mic index (run find_mic.py to find it)
MIC_INDEX = None  # e.g. MIC_INDEX = 1

class VoiceListener:
    def __init__(self, brain, callback):
        self.brain = brain
        self.callback = callback
        self.listening_active = False
        self._thread = None
        logger.info("VoiceListener ready")

    def start(self):
        self._thread = threading.Thread(target=self._listen_forever, daemon=True)
        self._thread.start()

    def set_listening_active(self, active):
        self.listening_active = active
        logger.info(f"Listening: {'ACTIVE' if active else 'IDLE'}")

    def _listen_forever(self):
        logger.info("Listener loop started")

        while True:
            try:
                if not self.listening_active:
                    time.sleep(0.2)
                    continue

                logger.info("LISTENING for command...")

                r = sr.Recognizer()
                r.energy_threshold = 300
                r.dynamic_energy_threshold = False

                mic_kwargs = {"device_index": MIC_INDEX} if MIC_INDEX is not None else {}

                with sr.Microphone(**mic_kwargs) as source:
                    r.adjust_for_ambient_noise(source, duration=0.3)
                    try:
                        audio = r.listen(source, timeout=5, phrase_time_limit=8)
                    except sr.WaitTimeoutError:
                        logger.info("No speech heard, going back to idle")
                        self.listening_active = False
                        continue

                try:
                    text = r.recognize_google(audio)
                    logger.info(f"HEARD: '{text}'")
                    self.listening_active = False  # one command at a time
                    self.brain.process_command(text.lower())
                    if self.callback:
                        self.callback(text)
                except sr.UnknownValueError:
                    logger.info("Could not understand audio")
                    self.listening_active = False
                except sr.RequestError as e:
                    logger.error(f"Google API error: {e}")
                    self.listening_active = False

            except Exception as e:
                logger.error(f"Listener error: {e}", exc_info=True)
                self.listening_active = False
                time.sleep(1)

    def stop(self):
        self.listening_active = False