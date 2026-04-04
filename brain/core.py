import re
import datetime
import logging
from commands.system import SystemCommands
from commands.web import WebCommands
from commands.keyboard import KeyboardCommands
from voice.speaker import Speaker
from brain.memory import Memory

logger = logging.getLogger(__name__)

class JarvisBrain:
    def __init__(self):
        self.speaker = Speaker()
        self.memory = Memory()
        self.system = SystemCommands()
        self.web = WebCommands()
        self.keyboard = KeyboardCommands()
    
    def process_command(self, command):
        """Main command processor"""
        command = command.strip().lower()
        self.memory.add_conversation(command)
        
        # Greetings
        if any(greeting in command for greeting in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
            response = self._handle_greeting()
        
        # Time queries
        elif any(word in command for word in ['time', 'clock']):
            response = self._get_time()
        
        # Who are you / identity
        elif any(word in command for word in ['who are you', 'your name', 'who made you']):
            response = "I am Jarvis, your personal desktop assistant. How can I help you today?"
        
        # System commands
        elif 'open' in command:
            response = self._handle_open(command)
        
        # Search
        elif 'search' in command or 'google' in command:
            query = command.replace('search', '').replace('google', '').strip()
            response = self.web.google_search(query)
        
        # WhatsApp
        elif 'whatsapp' in command:
            response = self._handle_whatsapp(command)
        
        # Type text
        elif 'type' in command:
            response = self._handle_type(command)
        
        # System control
        elif any(word in command for word in ['shutdown', 'restart', 'sleep']):
            response = self._handle_system_control(command)
        
        # Weather (mock - extend with API later)
        elif 'weather' in command:
            response = "The weather is looking great today! For accurate forecasts, integrate a weather API."
        
        else:
            response = "I'm not sure how to help with that yet. Try asking me to open apps, search, or tell you the time."
        
        self.speaker.speak(response)
        return response
    
    def _handle_greeting(self):
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning! How can I assist you today?"
        elif 12 <= hour < 17:
            return "Good afternoon! What can I do for you?"
        else:
            return "Good evening! How may I help you?"
    
    def _get_time(self):
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}"
    
    def _handle_open(self, command):
        if 'chrome' in command or 'browser' in command:
            self.system.open_chrome()
            return "Opening Google Chrome"
        elif 'notepad' in command:
            self.system.open_notepad()
            return "Opening Notepad"
        elif 'code' in command or 'vscode' in command:
            self.system.open_vscode()
            return "Opening Visual Studio Code"
        elif 'documents' in command:
            self.system.open_documents()
            return "Opening Documents folder"
        elif 'downloads' in command:
            self.system.open_downloads()
            return "Opening Downloads folder"
        else:
            return "I can open Chrome, Notepad, VS Code, Documents, or Downloads."
    
    def _handle_whatsapp(self, command):
        # Extract contact/message (simplified)
        self.web.open_whatsapp()
        return "Opening WhatsApp Web. Please send your message manually."
    
    def _handle_type(self, command):
        text = re.search(r'type (.+)', command)
        if text:
            self.keyboard.type_text(text.group(1))
            return f"Typing: {text.group(1)}"
        return "Please specify what to type."
    
    def _handle_system_control(self, command):
        if 'shutdown' in command:
            self.system.shutdown()
            return "Shutting down the computer in 10 seconds."
        elif 'restart' in command:
            self.system.restart()
            return "Restarting the computer."
        return "System command not recognized."