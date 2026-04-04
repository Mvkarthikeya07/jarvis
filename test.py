import speech_recognition as sr
import pyaudio
import time
import logging
logging.basicConfig(level=logging.DEBUG)

print("=== JARVIS VOICE TEST ===")
r = sr.Recognizer()
m = sr.Microphone()

print("1. Testing microphone...")
with m as source:
    r.adjust_for_ambient_noise(source)
    print("   OK - noise calibrated")

print("2. Say 'test one two' NOW...")
with m as source:
    audio = r.listen(source, timeout=5, phrase_time_limit=5)

print("3. Processing speech...")
try:
    text = r.recognize_google(audio)
    print(f"   SUCCESS! Heard: '{text}'")
except:
    print("   FAILED - no speech recognized")

print("4. Testing wake detector...")
# Your wake detector test
from wake_word.detector import WakeWordDetector
def callback(): print("WAKE!")
d = WakeWordDetector(callback)
d.start()
input("Speak loudly now! Press Enter to stop...")
d.stop()

print("=== TEST COMPLETE ===")