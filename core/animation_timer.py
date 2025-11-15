"""
Lightweight animation timer utility for smooth interpolations.
Used for button animations, UI effects, and other simple tweening.
"""
import time
from typing import Callable, Optional


def ease_out_cubic(t: float) -> float:
    """Easing function: ease out cubic"""
    return 1 - (1 - t) ** 3


def ease_in_out_quad(t: float) -> float:
    """Easing function: ease in-out quadratic"""
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2


class AnimationTimer:
    """
    Lightweight timer for smooth animations.
    Uses simple interpolation with optional easing.
    """
    
    def __init__(self, duration: float, easing_func: Optional[Callable[[float], float]] = None):
        """
        Initialize animation timer.
        Args:
            duration: Animation duration in seconds
            easing_func: Optional easing function (default: linear)
        """
        self.duration = duration
        self.easing_func = easing_func or (lambda t: t)  # Linear by default
        self.start_time: Optional[float] = None
        self.is_active = False
    
    def start(self):
        """Start the animation"""
        self.start_time = time.time()
        self.is_active = True
    
    def stop(self):
        """Stop the animation"""
        self.is_active = False
        self.start_time = None
    
    def reset(self):
        """Reset the animation (same as stop)"""
        self.stop()
    
    def get_progress(self) -> float:
        """
        Get animation progress from 0.0 to 1.0.
        Returns 1.0 if animation is complete or not started.
        """
        if not self.is_active or self.start_time is None:
            return 1.0
        
        elapsed = time.time() - self.start_time
        t = min(elapsed / self.duration, 1.0)
        
        # Apply easing
        eased_t = self.easing_func(t)
        
        if t >= 1.0:
            self.is_active = False
        
        return eased_t
    
    def is_complete(self) -> bool:
        """Check if animation is complete"""
        if not self.is_active:
            return True
        return self.get_progress() >= 1.0
    
    def get_value(self, start: float, end: float) -> float:
        """
        Get interpolated value between start and end.
        Args:
            start: Start value
            end: End value
        Returns:
            Interpolated value
        """
        progress = self.get_progress()
        return start + (end - start) * progress


class PulseAnimation:
    """
    Specialized animation for pulsing effects (1.0 -> max -> 1.0).
    """
    
    def __init__(self, duration: float, max_scale: float = 1.15):
        """
        Initialize pulse animation.
        Args:
            duration: Full pulse duration (both directions)
            max_scale: Maximum scale value
        """
        self.duration = duration
        self.max_scale = max_scale
        self.start_time: Optional[float] = None
        self.is_active = False
    
    def start(self):
        """Start the pulse"""
        self.start_time = time.time()
        self.is_active = True
    
    def stop(self):
        """Stop the pulse"""
        self.is_active = False
        self.start_time = None
    
    def get_scale(self) -> float:
        """
        Get current scale value (1.0 -> max_scale -> 1.0).
        """
        if not self.is_active or self.start_time is None:
            return 1.0
        
        elapsed = time.time() - self.start_time
        t = elapsed / self.duration
        
        if t >= 1.0:
            self.is_active = False
            return 1.0
        
        # Pulse: 0 -> 1 -> 0
        if t < 0.5:
            # First half: 1.0 -> max_scale
            pulse_t = t * 2.0
            ease_t = ease_in_out_quad(pulse_t)
            return 1.0 + (self.max_scale - 1.0) * ease_t
        else:
            # Second half: max_scale -> 1.0
            pulse_t = (t - 0.5) * 2.0
            ease_t = ease_in_out_quad(pulse_t)
            return self.max_scale - (self.max_scale - 1.0) * ease_t

