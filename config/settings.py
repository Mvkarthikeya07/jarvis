import os
from pathlib import Path

class Settings:
    def __init__(self):
        self.config_dir = Path.home() / ".jarvis"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        
        self.load_settings()
    
    def load_settings(self):
        """Load user settings"""
        self.mic_device = None  # Auto-detect
        self.tts_voice = "default"
        self.wake_sensitivity = 0.6
        self.auto_start = True
    
    def save_settings(self):
        """Save settings to file"""
        settings = {
            "mic_device": self.mic_device,
            "tts_voice": self.tts_voice,
            "wake_sensitivity": self.wake_sensitivity,
            "auto_start": self.auto_start
        }