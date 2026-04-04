import tkinter as tk
from tkinter import Canvas
import math
import time
import logging

logger = logging.getLogger(__name__)

class OrbAnimation:
    def __init__(self, parent, size=220):
        # FIXED: Use 'black' - works everywhere
        self.canvas = Canvas(parent, width=size, height=size, 
                           bg='black', highlightthickness=0)
        self.size = size
        self.center_x = size // 2
        self.center_y = size // 2
        self.radius = size // 2 - 25
        self.animation_type = "idle"
        
        self.canvas.pack(pady=20)
        self.create_orb()
        logger.info("OrbAnimation created successfully")
    
    def create_orb(self):
        """Create the glowing orb"""
        self.canvas.delete("all")
        
        # Outer glow
        self.canvas.create_oval(
            self.center_x - self.radius - 30, self.center_y - self.radius - 30,
            self.center_x + self.radius + 30, self.center_y + self.radius + 30,
            fill="#001133", outline="", tags="glow1"
        )
        # Middle glow
        self.canvas.create_oval(
            self.center_x - self.radius - 15, self.center_y - self.radius - 15,
            self.center_x + self.radius + 15, self.center_y + self.radius + 15,
            fill="#004499", outline="", tags="glow2"
        )
        # Main orb
        self.canvas.create_oval(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            fill="#00D4FF", outline="#00A8FF", width=5, tags="orb"
        )
    
    def start_listening_animation(self):
        """Siri-style listening waves"""
        logger.info("Starting listening animation")
        self.animation_type = "listening"
        self.canvas.delete("waveform")
        self._animate_listening()
    
    def start_processing_animation(self):
        """Processing rings"""
        self.animation_type = "processing"
        self.canvas.delete("rings")
        self._animate_processing()
    
    def stop_animation(self):
        """Stop all animations"""
        self.canvas.delete("waveform", "rings")
        self.animation_type = "idle"
    
    def _animate_listening(self):
        """Green waveform animation"""
        def animate():
            if self.animation_type != "listening":
                return
            self.canvas.delete("waveform")
            t = time.time() * 8
            
            # 20 pulsing waves around orb
            for i in range(20):
                angle = (t + i * 0.3) % (2 * math.pi)
                wave_height = 25 + 15 * abs(math.sin(t * 4 + i))
                x1 = self.center_x + math.cos(angle) * (self.radius + 15)
                y1 = self.center_y + math.sin(angle) * (self.radius + 15)
                x2 = self.center_x + math.cos(angle) * (self.radius + 15 + wave_height)
                y2 = self.center_y + math.sin(angle) * (self.radius + 15 + wave_height)
                
                self.canvas.create_line(x1, y1, x2, y2, 
                    fill="#00FF88", width=5, capstyle=tk.ROUND, tags="waveform")
            
            self.canvas.after(50, animate)
        animate()
    
    def _animate_processing(self):
        """Orange expanding rings"""
        def animate():
            if self.animation_type != "processing":
                return
            self.canvas.delete("rings")
            t = time.time() * 3
            
            # 8 expanding rings
            for i in range(8):
                ring_radius = self.radius + 25 + i * 20 + (math.sin(t + i * 0.8) * 15)
                alpha = 1.0 - i * 0.12
                self.canvas.create_oval(
                    self.center_x - ring_radius, self.center_y - ring_radius,
                    self.center_x + ring_radius, self.center_y + ring_radius,
                    outline="#FF6B35", width=6, tags="rings"
                )
            
            self.canvas.after(60, animate)
        animate()