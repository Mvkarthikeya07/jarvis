"""
Quick test — shows exactly what Jarvis hears and what it tries to do
"""
import speech_recognition as sr
import webbrowser, os, subprocess, datetime, urllib.parse

MIC_INDEX = 1

r = sr.Recognizer()
r.energy_threshold = 300
r.dynamic_energy_threshold = False

print("=== JARVIS COMMAND TEST ===")
print("Speak a command when you see LISTEN...\n")

while True:
    print("Say a command (or say 'quit' to stop):")
    try:
        with sr.Microphone(device_index=MIC_INDEX) as src:
            r.adjust_for_ambient_noise(src, duration=0.3)
            print(">>> LISTEN...")
            audio = r.listen(src, timeout=6, phrase_time_limit=6)
        text = r.recognize_google(audio).lower()
        print(f"\n✅ Heard: '{text}'")

        # Show which branch it hits
        if any(w in text for w in ["hello","hi","hey","good morning","good evening"]):
            print("→ BRANCH: Greeting")
        elif "time" in text:
            print(f"→ BRANCH: Time → {datetime.datetime.now().strftime('%I:%M %p')}")
        elif "date" in text or "today" in text:
            print(f"→ BRANCH: Date")
        elif "open" in text:
            print(f"→ BRANCH: Open → checking what...")
            for app in ["chrome","notepad","calculator","vscode","vs code","documents","downloads","explorer","spotify","discord","whatsapp","youtube","settings","task manager"]:
                if app in text:
                    print(f"   ✅ Matched app: '{app}'")
                    break
            else:
                print(f"   ❌ No app matched in: '{text}'")
                print(f"   Try saying: 'open chrome' or 'open notepad'")
        elif "search" in text or "google" in text:
            query = text.replace("search","").replace("google","").strip()
            print(f"→ BRANCH: Search → query='{query}'")
        elif "youtube" in text:
            print(f"→ BRANCH: YouTube")
        elif "weather" in text:
            print(f"→ BRANCH: Weather")
        elif "joke" in text:
            print(f"→ BRANCH: Joke")
        elif "shutdown" in text or "restart" in text:
            print(f"→ BRANCH: System control")
        else:
            print(f"→ BRANCH: ❌ NO MATCH — fell to fallback")
            print(f"   Raw text was: '{text}'")
            print(f"   Tip: speak clearly, say 'open chrome' not just 'chrome'")

        print()
        if "quit" in text or "exit" in text:
            break

    except sr.WaitTimeoutError:
        print("❌ Timeout — didn't hear anything\n")
    except sr.UnknownValueError:
        print("❌ Heard sound but couldn't understand\n")
    except KeyboardInterrupt:
        break

print("Done!")