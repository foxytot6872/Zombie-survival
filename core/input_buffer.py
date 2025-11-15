"""
Input buffer system for responsive input handling.
Provides a small time window to register inputs that might have been missed.
"""
import time
from collections import deque
from typing import Optional, Tuple, Dict


class InputBuffer:
    """
    Lightweight input buffer that stores recent inputs for a short time window.
    Allows catching inputs that might be missed during frame timing.
    """
    
    def __init__(self, buffer_duration: float = 0.125):
        """
        Initialize input buffer.
        Args:
            buffer_duration: How long to keep inputs in buffer (seconds), default 125ms
        """
        self.buffer_duration = buffer_duration
        self.buffer: Dict[str, deque] = {
            'left_click': deque(),
            'right_click': deque(),
            'key_r': deque(),
            'key_g': deque(),
        }
    
    def add_input(self, input_type: str, data: Optional[dict] = None):
        """
        Add an input to the buffer.
        Args:
            input_type: Type of input ('left_click', 'right_click', 'key_r', 'key_g')
            data: Optional data associated with the input (e.g., mouse position)
        """
        if input_type in self.buffer:
            current_time = time.time()
            self.buffer[input_type].append((current_time, data or {}))
    
    def consume_input(self, input_type: str) -> Optional[dict]:
        """
        Check and consume an input from the buffer if it exists and is recent enough.
        Args:
            input_type: Type of input to check
        Returns:
            Input data if found and valid, None otherwise
        """
        if input_type not in self.buffer:
            return None
        
        current_time = time.time()
        buffer_queue = self.buffer[input_type]
        
        # Remove expired inputs
        while buffer_queue:
            timestamp, data = buffer_queue[0]
            if current_time - timestamp <= self.buffer_duration:
                # Found valid input - remove and return it
                buffer_queue.popleft()
                return data
            else:
                # Input expired - remove it
                buffer_queue.popleft()
        
        return None
    
    def has_input(self, input_type: str) -> bool:
        """
        Check if there's a valid input in the buffer without consuming it.
        Args:
            input_type: Type of input to check
        Returns:
            True if valid input exists, False otherwise
        """
        if input_type not in self.buffer:
            return False
        
        current_time = time.time()
        buffer_queue = self.buffer[input_type]
        
        # Remove expired inputs
        while buffer_queue:
            timestamp, _ = buffer_queue[0]
            if current_time - timestamp <= self.buffer_duration:
                # Found valid input
                return True
            else:
                # Input expired - remove it
                buffer_queue.popleft()
        
        return False
    
    def clear(self, input_type: Optional[str] = None):
        """
        Clear the buffer for a specific input type or all inputs.
        Args:
            input_type: Type to clear, or None to clear all
        """
        if input_type:
            if input_type in self.buffer:
                self.buffer[input_type].clear()
        else:
            for key in self.buffer:
                self.buffer[key].clear()

