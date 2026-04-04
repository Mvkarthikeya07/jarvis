import customtkinter as ctk
import tkinter as tk
import threading
import time
import logging
from gui.animations import OrbAnimation

logger = logging.getLogger(__name__)

class JarvisGUI:
    def __init__(self, brain, on_close_callback=None):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.brain = brain
        self.on_close = on_close_callback
        self.window = None
        self.orb = None
        self.status_label = None
        self.is_listening = False
        
        self.setup_window()
        logger.info("🎨 JarvisGUI created")
    
    def setup_window(self):
        """Create main transparent window"""
        self.window = ctk.CTk()
        self.window.title("Jarvis")
        self.window.geometry("400x450")
        self.window.configure(fg_color="black")
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.95)
        
        # Center and make always on top
        self.window.eval('tk::PlaceWindow . center')
        self.window.overrideredirect(True)  # Frameless
        
        # Main frame
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent", corner_radius=20)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Animated orb
        self.orb = OrbAnimation(main_frame, size=220)
        self.orb.pack(pady=30)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Hey Jarvis",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#00D4FF"
        )
        self.status_label.pack(pady=10)
        
        # Debug label (shows last command)
        self.debug_label = ctk.CTkLabel(
            main_frame,
            text="Ready",
            font=ctk.CTkFont(size=14),
            text_color="#888"
        )
        self.debug_label.pack(pady=5)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="✕",
            width=35, height=35,
            fg_color="#ff4444",
            hover_color="#cc3333",
            command=self.hide,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=20
        )
        close_btn.place(relx=0.95, rely=0.05, anchor="center")
        
        # Initially hidden
        self.hide()
    
    def start(self):
        """Start GUI event loop"""
        logger.info("🎬 Starting GUI mainloop...")
        self.window.mainloop()
    
    def show(self):
        """Show window with entrance animation"""
        logger.info("📱 Showing Jarvis GUI")
        self.window.deiconify()
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.window.after(100, lambda: self.window.attributes("-topmost", False))
    
    def hide(self):
        """Hide window smoothly"""
        logger.info("🙈 Hiding Jarvis GUI")
        self.window.withdraw()
        self.orb.stop_animation()
        self.status_label.configure(text="Hey Jarvis")
        self.debug_label.configure(text="Ready")
    
    def show_listening(self):
        """Show listening state"""
        logger.info("🎤 GUI: Listening mode")
        self.show()
        self.is_listening = True
        self.status_label.configure(text="🎤 Listening...")
        self.debug_label.configure(text="Speak your command!")
        self.orb.start_listening_animation()
    
    def show_processing(self, command=""):
        """Show processing state"""
        logger.info(f"⚙️ GUI: Processing '{command}'")
        self.status_label.configure(text="🤖 Processing...")
        self.debug_label.configure(text=f"Command: {command}")
        self.orb.start_processing_animation()
        
        # Auto-hide after 4 seconds
        self.window.after(4000, self.hide)
    
    def show_error(self, message):
        """Show error state"""
        self.status_label.configure(text="❌ Error")
        self.debug_label.configure(text=message)
        self.orb.start_error_animation()
        self.window.after(3000, self.hide)
    
    def close(self):
        """Close application"""
        logger.info("🔚 Closing Jarvis")
        if self.on_close:
            self.on_close()
    
    def stop(self):
        """Stop GUI"""
        if self.window:
            self.window.quit()
            self.window.destroy()