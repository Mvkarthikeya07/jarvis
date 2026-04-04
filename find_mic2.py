"""
Mic finder - gives you 3 seconds to prepare before each recording
"""
import speech_recognition as sr
import time

names = sr.Microphone.list_microphone_names()
input_mics = [(i, n) for i, n in enumerate(names) if any(
    w in n.lower() for w in ["microphone", "input", "capture", "headset", "mic"]
)]

print("\n=== TESTING INPUT MICS ONLY ===")
print("When you see 'SPEAK NOW' — say your name clearly and loudly\n")

r = sr.Recognizer()
r.energy_threshold = 200
r.dynamic_energy_threshold = False

for i, name in input_mics:
    try:
        print(f"[{i}] {name}")
        with sr.Microphone(device_index=i) as src:
            print("     Calibrating...")
            r.adjust_for_ambient_noise(src, duration=1)
            print(f"     Energy level: {r.energy_threshold:.0f}")
            print("     >>> SPEAK NOW (5 seconds) <<<")
            audio = r.listen(src, timeout=5, phrase_time_limit=4)
        text = r.recognize_google(audio)
        print(f"\n✅  SUCCESS! Heard: '{text}'")
        print(f"✅  SET THIS IN main.py:  MIC_INDEX = {i}\n")
    except sr.WaitTimeoutError:
        print("     ❌ Timeout — mic didn't pick up sound (wrong device or too quiet)")
    except sr.UnknownValueError:
        print("     ❌ Heard sound but couldn't understand — try speaking louder")
    except Exception as e:
        print(f"     ❌ {type(e).__name__}: {e}")
    print()

print("Done!")