import keyboard
import time
import logging

logger = logging.getLogger(__name__)

class KeyboardCommands:
    def type_text(self, text):
        """Type text using keyboard automation"""
        try:
            time.sleep(0.3)  # Small delay to ensure focus
            keyboard.write(text, delay=0.05)  # delay between keystrokes for reliability
            logger.info(f"Typed: {text}")
            return True
        except Exception as e:
            logger.error(f"Typing error: {e}")
            return False