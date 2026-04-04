import os
import subprocess
import platform
import logging

logger = logging.getLogger(__name__)

class SystemCommands:
    def __init__(self):
        self.system = platform.system().lower()
    
    def open_chrome(self):
        """Open Google Chrome"""
        try:
            if self.system == "windows":
                os.startfile("chrome.exe")
            else:
                subprocess.run(["google-chrome"])
        except:
            subprocess.run(["start", "chrome", "https://google.com"], shell=True)
    
    def open_notepad(self):
        """Open Notepad"""
        try:
            subprocess.run(["notepad.exe"])
        except:
            subprocess.run(["start", "notepad"], shell=True)
    
    def open_vscode(self):
        """Open VS Code"""
        try:
            subprocess.run(["code"])
        except:
            subprocess.run(["start", "code"], shell=True)
    
    def open_documents(self):
        """Open Documents folder"""
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        os.startfile(documents_path)
    
    def open_downloads(self):
        """Open Downloads folder"""
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        os.startfile(downloads_path)
    
    def shutdown(self):
        """Shutdown system"""
        subprocess.run(["shutdown", "/s", "/t", "10"])
    
    def restart(self):
        """Restart system"""
        subprocess.run(["shutdown", "/r", "/t", "10"])