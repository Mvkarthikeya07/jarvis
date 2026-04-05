# 🤖 J.A.R.V.I.S — Autonomous AI Desktop Assistant with Real-Time Voice Control  

> *Just A Rather Very Intelligent System*  
> A fully autonomous AI assistant capable of controlling an entire computer system using natural voice commands.

📌 Overview

JARVIS is a production-grade, AI-powered desktop assistant designed for real-time voice interaction, intelligent decision-making, and deep system-level automation.

It integrates:

- Speech Recognition  
- Wake Word Detection  
- AI Reasoning (Claude)  
- OS-Level Automation  
- GUI Visualization  

into a modular, event-driven architecture capable of executing complex, multi-step tasks across the entire system.

⚡ Key Highlights

- 🧠 AI-driven multi-step execution  
- 🎙 Real-time voice control with wake word  
- 💻 Full OS-level automation  
- ⚔️ Weapon mode (developer environment setup)  
- 🎬 Favorites mode (instant entertainment launch)  
- 🎨 Interactive GUI with real-time feedback

📸 Live System Demonstration

The following screenshots demonstrate the real-time working of JARVIS, including voice interaction, AI processing, and system automation.

### 🎤 Listening Mode

<img width="1366" height="768" alt="Screenshot (18)" src="https://github.com/user-attachments/assets/51c80245-0ac8-4da9-8a17-906b3cdc8ade" />

- System actively listening for commands  
- Wake word detected  
- Ready for input  

### 🟢 Responding Mode

<img width="1366" height="768" alt="Screenshot (19)" src="https://github.com/user-attachments/assets/fb57df8b-6050-4762-a930-03c729c6ad76" />

- Command executed successfully  
- GUI + voice synchronized  
- Example: Opening documents
  
### 🟠 Processing Mode

<img width="1366" height="768" alt="Screenshot (20)" src="https://github.com/user-attachments/assets/4c152621-882d-46aa-a79a-cbc89bea0325" />

- AI analyzing the command  
- Multi-step execution in progress  

### 🌐 Real Automation 

<img width="1366" height="768" alt="Screenshot (22)" src="https://github.com/user-attachments/assets/77f416ed-de92-452f-aa94-07f322b2bbce" />

- Demonstrates browser automation  
- Executes actions like selecting videos  
- Example: “Play the second video”  

### ⚡ Execution Pipeline
Wake Word → Listening → Processing → Execution → Response

❓ Why JARVIS?

Modern computing still depends on manual input and fragmented workflows.
JARVIS demonstrates a shift toward intelligent, voice-driven systems capable of:

Executing real OS-level tasks
Automating workflows
Acting as a true digital assistant

👉 This project bridges the gap between:
Conversational AI ↔ System Control
```
🧠 Full System Architecture
                    ┌─────────────────────────────┐
                    │        User (Voice)         │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   Wake Word Detection       │
                    │   ("Hey Jarvis")            │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   Speech Recognition        │
                    │   (Voice → Text)            │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   Command Preprocessing     │
                    │   - Wake word removal       │
                    │   - Noise filtering         │
                    │   - Duplicate removal       │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   AI Decision Engine        │
                    │   (Claude LLM)              │
                    │                             │
                    │   - Intent detection        │
                    │   - Multi-step planning     │
                    │   - Action generation       │
                    └────────────┬────────────────┘
                                 │
                                 ▼
        ┌──────────────────────────────────────────────────────┐
        │              Device Controller Layer                 │
        │                                                      │
        │  ┌──────────────┐   ┌──────────────┐   ┌───────────┐ │
        │  │ App Control  │   │ File System  │   │ Web Control│ │
        │  │              │   │              │   │            │ │
        │  │ - Open apps  │   │ - Create     │   │ - Google   │ │
        │  │ - Close apps │   │ - Delete     │   │ - YouTube  │ │
        │  │ - Scan apps  │   │ - List files │   │ - URLs     │ │
        │  └──────────────┘   └──────────────┘   └───────────┘ │
        │                                                      │
        │  ┌──────────────┐   ┌──────────────┐   ┌───────────┐ │
        │  │ Keyboard     │   │ Mouse        │   │ Media     │ │
        │  │ Automation   │   │ Control      │   │ Control   │ │
        │  │              │   │              │   │           │ │
        │  │ - Type text  │   │ - Move       │   │ - Play    │ │
        │  │ - Shortcuts  │   │ - Click      │   │ - Pause   │ │
        │  │              │   │ - Scroll     │   │ - Volume  │ │
        │  └──────────────┘   └──────────────┘   └───────────┘ │
        │                                                      │
        │  ┌──────────────┐   ┌──────────────┐                │
        │  │ System Ctrl  │   │ Monitoring   │                │
        │  │              │   │              │                │
        │  │ - Shutdown   │   │ - CPU        │                │
        │  │ - Restart    │   │ - RAM        │                │
        │  │ - Lock       │   │ - Battery    │                │
        │  └──────────────┘   └──────────────┘                │
        └──────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   Response Generation       │
                    │   (Text Output)             │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   Text-to-Speech Engine     │
                    │   (Voice Output)            │
                    └────────────┬────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │   GUI Visualization         │
                    │   (Listening / Processing)  │
                    └─────────────────────────────┘
```

## 🚀 Core Capabilities

### 🧠 AI Decision Engine
- Claude-powered reasoning  
- Context-aware interaction  
- Multi-step execution  
- Dynamic action mapping  
Example:

"Open Chrome and search for Python tutorials"
→ Opens Chrome → Searches automatically

🎙 Voice Interaction System
Wake word: “Hey Jarvis”
Continuous listening
Noise filtering
Duplicate speech handling
Real-time execution

💻 Full Device Control (Core Strength)

🖥 Application & Folder Control
Open ANY installed application
Auto-detect apps (Registry + Start Menu + Desktop)
Open system folders:
Desktop, Downloads, Documents
Open custom folders dynamically

❌ Process Management
Close apps
Close tabs
Close folders

💣 Close Everything Command
🌐 Web Automation
Google search
YouTube search
Open websites
WhatsApp Web
Social platform automation

⌨️ Keyboard Automation
Type text anywhere
Type in specific apps

Shortcuts:
Copy / Paste
New tab
Refresh
Select all

🖱 Mouse Automation
Move cursor (natural language positions)
Click actions
Scroll control

🎥 Intelligent Media Control

Play / Pause
Skip / rewind
Mute / Unmute
Fullscreen
Click specific videos

📁 File System Operations

Create files/folders
Delete files/folders
Open files
List directory contents

📞 Contact Integration
Call via WhatsApp
Send messages
Smart contact matching

🔊 Media & Volume Control
Volume up/down
Mute
Next/previous track

📸 Screenshot System
Capture screenshots
Auto-save

📊 System Monitoring
CPU
RAM
Disk
Battery
Processes

🖥 System Control
Shutdown
Restart
Sleep
Lock
Run terminal commands

⚔️ Advanced Features (UNIQUE)

⚔️ Weapon Mode
"Weapon up"
Opens ChatGPT, Claude, GitHub, VS Code
Displays time, date, weather

🎬 Favorites Mode
"Open my favourites"
Netflix
Amazon Prime
YouTube

💣 Global System Cleanup
"Close everything"
Closes all apps
Clears system workspace

⚡ Auto App Discovery
Scans system dynamically
Builds app index
Supports fuzzy matching

🤖 AI-Based Action Execution
Not rule-based
Uses LLM reasoning
Executes multi-step workflows

🎨 GUI System
Iron Man-style interface
Real-time states:
🔵 Listening
🟠 Processing
🟢 Responding

⚙️ Performance
Metric	Value
Response Time	~1 sec
Wake Latency	~300 ms
Architecture	Event-driven
Execution	Multi-threaded
```
📂 Project Structure
JARVIS /
│
├── brain/
│   ├── __init__.cpython-312.pyc
│   ├── core.cpython-312.pyc
│   ├── memory.cpython-312.pyc
│   │
│   ├── __init__.py
│   ├── core.py
│   └── memory.py
│
├── commands/
│   ├── __init__.py
│   ├── keyboard.py
│   ├── system.py
│   └── web.py
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── gui/
│   ├── __init__.py
│   ├── animations.py
│   └── main_window.py
│
├── voice/
│   ├── __init__.py
│   ├── listener.py
│   └── speaker.py
│
├── wake_word/
│   ├── __init__.cpython-312.pyc
│   └── detector.cpython-312.pyc
│   │
│   ├── __init__.py
│   └── detector.py
│
├── apps_cache.json
├── Contacts manager.py
├── debug_commands.py
├── Find mic.py
├── find_mic2.py
├── jarvis.log
├── main.py
├── requirements.txt
├── startup.bat
├── test_mic.py
└── test.py

The project follows a modular architecture separating AI logic, command execution, voice processing, GUI, and wake word detection into independent components.
```
```
🔧 Installation
git clone https://github.com/your-username/jarvis.git
cd jarvis
pip install -r requirements.txt
Configure Microphone
python Find mic.py
Run
python main.py
```
🎯 Example Commands
Hey Jarvis weapon up  
Hey Jarvis open chrome  
Hey Jarvis play first video  
Hey Jarvis close everything  
Hey Jarvis type hello in notepad  
Hey Jarvis call mom  
Hey Jarvis take screenshot  

🔬 Applications
Human-Computer Interaction (HCI)
AI Assistants
Desktop Automation
Intelligent Systems

🔮 Future Enhancements
Persistent memory
Task automation pipelines
Mobile integration
Smart home control

👨‍💻 Author

M V Karthikeya
B.Tech CSE (AI & ML)

📜 License

This project is licensed under the MIT License.

🏆 Final Statement

JARVIS is not just a voice assistant.
It is a fully autonomous AI system capable of controlling an entire computer through natural language.
