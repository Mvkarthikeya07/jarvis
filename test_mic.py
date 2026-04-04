import speech_recognition as sr
import pyaudio

# --- CHANGE THIS to your mic index from the list above ---
MIC_INDEX = 1  

print("🎤 Testing Microphone...")
r = sr.Recognizer()
r.energy_threshold = 300        # lower = more sensitive
r.dynamic_energy_threshold = False  # stop it auto-adjusting too high
m = sr.Microphone(device_index=MIC_INDEX)

with m as source:
    print("Calibrating for 2s...")
    r.adjust_for_ambient_noise(source, duration=2)
    print(f"Energy threshold set to: {r.energy_threshold}")
    print("Say something NOW (you have 10 seconds)...")
    audio = r.listen(source, timeout=10, phrase_time_limit=5)

print("Processing...")
try:
    text = r.recognize_google(audio)
    print(f"🎉 Heard: {text}")
except Exception as e:
    print(f"❌ Error: {e}")