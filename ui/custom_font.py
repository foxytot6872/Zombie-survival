"""
Custom font renderer using sprite sheet frames for letters.
Numbers are rendered using Arial font.
"""
import pygame
from typing import Dict, Optional, Tuple


class CustomFont:
    """Custom font renderer that uses sprite sheet frames for letters and Arial for numbers."""
    
    def __init__(self, letter_frames: Dict[str, pygame.Surface], number_font: pygame.font.Font):
        """
        Initialize custom font.
        
        Args:
            letter_frames: Dictionary mapping letter (A-Z) to pygame.Surface
            number_font: pygame.font.Font for rendering numbers (0-9)
        """
        self.letter_frames = letter_frames
        self.number_font = number_font
        # Store letter dimensions (assuming all letters are same size)
        if letter_frames:
            first_letter = next(iter(letter_frames.values()))
            self.letter_width = first_letter.get_width()
            self.letter_height = first_letter.get_height()
        else:
            self.letter_width = 17
            self.letter_height = 22
    
    def render(self, text: str, antialias: bool = True, color: Tuple[int, int, int] = (255, 255, 255), 
               spacing: int = 0) -> pygame.Surface:
        """
        Render text using custom letter frames for A-Z and number font for 0-9.
        
        Args:
            text: Text to render (only A-Z, a-z, 0-9, space and common punctuation)
            color: Color tuple (only affects numbers, letters use their original colors)
            spacing: Additional spacing between characters (default 0)
        
        Returns:
            pygame.Surface with rendered text
        """
        if not text:
            return pygame.Surface((0, 0), pygame.SRCALPHA)
        
        # Calculate total width and height
        total_width = 0
        max_height = self.letter_height
        
        # First pass: calculate dimensions
        for char in text:
            if char == ' ':
                total_width += self.letter_width // 2  # Space is half letter width
            elif char.isalpha():
                # Convert to uppercase for lookup
                letter_key = char.upper()
                if letter_key in self.letter_frames:
                    total_width += self.letter_width
                else:
                    # Fallback: use number font size
                    fallback_surface = self.number_font.render(char, True, color)
                    total_width += fallback_surface.get_width()
                    max_height = max(max_height, fallback_surface.get_height())
            elif char.isdigit() or char in '.,!?:;-':
                # Use number font
                fallback_surface = self.number_font.render(char, True, color)
                total_width += fallback_surface.get_width()
                max_height = max(max_height, fallback_surface.get_height())
            else:
                # Other characters use number font
                fallback_surface = self.number_font.render(char, True, color)
                total_width += fallback_surface.get_width()
                max_height = max(max_height, fallback_surface.get_height())
            
            if spacing > 0 and char != text[-1]:  # Don't add spacing after last char
                total_width += spacing
        
        # Create output surface
        output = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        
        # Second pass: render characters
        x_offset = 0
        for char in text:
            if char == ' ':
                # Space - just advance position
                x_offset += self.letter_width // 2
            elif char.isalpha():
                # Use letter frames
                letter_key = char.upper()
                if letter_key in self.letter_frames:
                    letter_frame = self.letter_frames[letter_key]
                    # Center vertically
                    y_offset = (max_height - self.letter_height) // 2
                    output.blit(letter_frame, (x_offset, y_offset))
                    x_offset += self.letter_width
                else:
                    # Fallback to number font
                    fallback_surface = self.number_font.render(char, True, color)
                    y_offset = (max_height - fallback_surface.get_height()) // 2
                    output.blit(fallback_surface, (x_offset, y_offset))
                    x_offset += fallback_surface.get_width()
            elif char.isdigit() or char in '.,!?:;-':
                # Use number font
                number_surface = self.number_font.render(char, True, color)
                y_offset = (max_height - number_surface.get_height()) // 2
                output.blit(number_surface, (x_offset, y_offset))
                x_offset += number_surface.get_width()
            else:
                # Other characters use number font
                fallback_surface = self.number_font.render(char, True, color)
                y_offset = (max_height - fallback_surface.get_height()) // 2
                output.blit(fallback_surface, (x_offset, y_offset))
                x_offset += fallback_surface.get_width()
            
            if spacing > 0 and char != text[-1]:  # Don't add spacing after last char
                x_offset += spacing
        
        return output
    
    def size(self, text: str, spacing: int = 0) -> Tuple[int, int]:
        """
        Get the size of rendered text without actually rendering it.
        
        Args:
            text: Text to measure
            spacing: Additional spacing between characters
        
        Returns:
            Tuple of (width, height)
        """
        if not text:
            return (0, self.letter_height)
        
        total_width = 0
        max_height = self.letter_height
        
        for char in text:
            if char == ' ':
                total_width += self.letter_width // 2
            elif char.isalpha():
                letter_key = char.upper()
                if letter_key in self.letter_frames:
                    total_width += self.letter_width
                else:
                    # Fallback: estimate based on number font
                    fallback_width, fallback_height = self.number_font.size(char)
                    total_width += fallback_width
                    max_height = max(max_height, fallback_height)
            elif char.isdigit() or char in '.,!?:;-':
                number_width, number_height = self.number_font.size(char)
                total_width += number_width
                max_height = max(max_height, number_height)
            else:
                fallback_width, fallback_height = self.number_font.size(char)
                total_width += fallback_width
                max_height = max(max_height, fallback_height)
            
            if spacing > 0 and char != text[-1]:
                total_width += spacing
        
        return (total_width, max_height)
    
    def get_rect(self, text: str) -> pygame.Rect:
        """
        Get a Rect with the size of rendered text (for compatibility with pygame.font.Font).
        
        Args:
            text: Text to measure
        
        Returns:
            pygame.Rect with width and height set to text size, position at (0, 0)
        """
        width, height = self.size(text)
        return pygame.Rect(0, 0, width, height)
    
    def get_linesize(self) -> int:
        """
        Get the recommended line spacing height (for compatibility with pygame.font.Font).
        
        Returns:
            Recommended line height in pixels
        """
        # Return the letter height, which is the base line height
        # Add a small amount for spacing (typically 20% more)
        return int(self.letter_height * 1.2)


def load_custom_font(font_sheet_path: str, letter_width: int = 17, letter_height: int = 22,
                     number_font_size: int = 22) -> Optional[CustomFont]:
    """
    Load custom font from sprite sheet.
    
    Args:
        font_sheet_path: Path to the font sheet PNG file
        letter_width: Width of each letter frame
        letter_height: Height of each letter frame
        number_font_size: Size for Arial number font
    
    Returns:
        CustomFont object or None if loading fails
    """
    try:
        # Load font sheet
        font_sheet = pygame.image.load(font_sheet_path).convert_alpha()
        sheet_width = font_sheet.get_width()
        sheet_height = font_sheet.get_height()
        
        # Extract 26 frames (A-Z)
        letter_frames = {}
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for i, letter in enumerate(letters):
            try:
                frame_x = i * letter_width
                frame_rect = pygame.Rect(frame_x, 0, letter_width, letter_height)
                
                # Check bounds
                if frame_rect.right <= sheet_width and frame_rect.bottom <= sheet_height:
                    frame = font_sheet.subsurface(frame_rect)
                    letter_frames[letter] = frame.copy()
                else:
                    print(f"Warning: Letter {letter} frame out of bounds in {font_sheet_path}")
                    # Create placeholder
                    placeholder = pygame.Surface((letter_width, letter_height), pygame.SRCALPHA)
                    placeholder.fill((255, 0, 255, 255))  # Magenta placeholder
                    letter_frames[letter] = placeholder
            except (ValueError, pygame.error) as e:
                print(f"Warning: Failed to extract letter {letter} from {font_sheet_path}: {e}")
                # Create placeholder
                placeholder = pygame.Surface((letter_width, letter_height), pygame.SRCALPHA)
                placeholder.fill((255, 0, 255, 255))  # Magenta placeholder
                letter_frames[letter] = placeholder
        
        # Load Arial font for numbers
        try:
            number_font = pygame.font.SysFont("arial", number_font_size)
        except:
            # Fallback to default font
            number_font = pygame.font.Font(None, number_font_size)
        
        return CustomFont(letter_frames, number_font)
        
    except Exception as e:
        print(f"Error loading custom font from {font_sheet_path}: {e}")
        return None


def load_number_font(number_sheet_path: str, number_width: int = 17, number_height: int = 22) -> Optional[list]:
    """
    Load number font frames from sprite sheet.
    
    Args:
        number_sheet_path: Path to the number sheet PNG file
        number_width: Width of each number frame
        number_height: Height of each number frame
    
    Returns:
        List of 10 pygame.Surface frames (0-9) or None if loading fails
    """
    try:
        # Load number sheet
        number_sheet = pygame.image.load(number_sheet_path).convert_alpha()
        sheet_width = number_sheet.get_width()
        sheet_height = number_sheet.get_height()
        
        # Extract 10 frames (0-9)
        number_frames = []
        
        for i in range(10):  # 0-9
            try:
                frame_x = i * number_width
                frame_rect = pygame.Rect(frame_x, 0, number_width, number_height)
                
                # Check bounds
                if frame_rect.right <= sheet_width and frame_rect.bottom <= sheet_height:
                    frame = number_sheet.subsurface(frame_rect)
                    number_frames.append(frame.copy())
                else:
                    print(f"Warning: Number {i} frame out of bounds in {number_sheet_path}")
                    # Create placeholder
                    placeholder = pygame.Surface((number_width, number_height), pygame.SRCALPHA)
                    placeholder.fill((255, 0, 255, 255))  # Magenta placeholder
                    number_frames.append(placeholder)
            except (ValueError, pygame.error) as e:
                print(f"Warning: Failed to extract number {i} from {number_sheet_path}: {e}")
                # Create placeholder
                placeholder = pygame.Surface((number_width, number_height), pygame.SRCALPHA)
                placeholder.fill((255, 0, 255, 255))  # Magenta placeholder
                number_frames.append(placeholder)
        
        # Ensure we have exactly 10 frames
        while len(number_frames) < 10:
            if number_frames:
                number_frames.append(number_frames[0])
            else:
                placeholder = pygame.Surface((number_width, number_height), pygame.SRCALPHA)
                placeholder.fill((255, 0, 255, 255))  # Magenta placeholder
                number_frames.append(placeholder)
        
        return number_frames
        
    except Exception as e:
        print(f"Error loading number font from {number_sheet_path}: {e}")
        return None
