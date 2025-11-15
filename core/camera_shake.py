"""
Lightweight camera shake manager for screen shake effects.
Applies shake only to game world, not UI layer.
"""
import random
import time


class CameraShakeManager:
    """
    Manages camera shake effects with simple offset-based shaking.
    """
    
    def __init__(self):
        """Initialize camera shake manager"""
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.start_time = None
        self.offset_x = 0.0
        self.offset_y = 0.0
    
    def shake(self, intensity: float, duration: float = 0.1):
        """
        Trigger a camera shake.
        Args:
            intensity: Shake intensity in pixels (2-4 recommended)
            duration: Shake duration in seconds (default 0.1s)
        """
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.start_time = time.time()
    
    def update(self, dt: float):
        """
        Update shake effect.
        Args:
            dt: Delta time in seconds
        """
        if self.start_time is None:
            self.offset_x = 0.0
            self.offset_y = 0.0
            return
        
        elapsed = time.time() - self.start_time
        
        if elapsed >= self.shake_duration:
            # Shake complete
            self.offset_x = 0.0
            self.offset_y = 0.0
            self.start_time = None
            self.shake_intensity = 0.0
        else:
            # Calculate shake decay (linear decay)
            decay = 1.0 - (elapsed / self.shake_duration)
            current_intensity = self.shake_intensity * decay
            
            # Generate random offset
            self.offset_x = random.uniform(-current_intensity, current_intensity)
            self.offset_y = random.uniform(-current_intensity, current_intensity)
    
    def get_offset(self) -> tuple:
        """
        Get current shake offset.
        Returns:
            Tuple of (offset_x, offset_y) in pixels
        """
        return (int(self.offset_x), int(self.offset_y))
    
    def reset(self):
        """Reset shake immediately"""
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.start_time = None
        self.shake_intensity = 0.0

