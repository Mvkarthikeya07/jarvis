"""
Run this ONCE to find your mic index.
Then set MIC_INDEX at the top of main.py
"""
import speech_recognition as sr
import pyaudio

print("\n=== MICROPHONE LIST ===")
names = sr.Microphone.list_microphone_names()
for i, name in enumerate(names):
    print(f"  Index {i}: {name}")

print("\n=== TESTING EACH MIC (say something when prompted) ===")
r = sr.Recognizer()
r.energy_threshold = 300
r.dynamic_energy_threshold = False

for i, name in enumerate(names):
    try:
        print(f"\n[{i}] {name}")
        with sr.Microphone(device_index=i) as src:
            r.adjust_for_ambient_noise(src, duration=0.5)
            print(f"     Say something now (3 sec)...")
            audio = r.listen(src, timeout=3, phrase_time_limit=3)
        text = r.recognize_google(audio)
        print(f"     🎉 HEARD: '{text}'")
        print(f"\n✅  USE THIS:  MIC_INDEX = {i}  (in main.py line 20)")
        break
    except Exception as e:
        print(f"     ❌ {type(e).__name__}")

print("\nDone!")