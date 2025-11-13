"""
Start screen/menu UI.
"""
import pygame
from typing import Optional, Callable

class StartScreen:
    """Start screen with background and title"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize start screen.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        
        self.is_visible = True
        
        # Load background image (try both possible filenames)
        self.background = None
        for bg_path in ['asset/gamestar.jpg', 'asset/Gamestart.jpg']:
            try:
                self.background = pygame.image.load(bg_path).convert()
                # Scale background to fit screen if needed
                bg_width, bg_height = self.background.get_size()
                if bg_width != screen_width or bg_height != screen_height:
                    self.background = pygame.transform.scale(self.background, (screen_width, screen_height))
                break
            except Exception:
                continue
        
        if self.background is None:
            print(f"Warning: Could not load gamestar.jpg or Gamestart.jpg, using placeholder")
            self.background = pygame.Surface((screen_width, screen_height))
            self.background.fill((20, 20, 40))  # Dark blue placeholder
        
        # Load title image
        try:
            self.title_image = pygame.image.load('asset/title.png').convert_alpha()
        except Exception as e:
            print(f"Warning: Could not load title.png: {e}, using placeholder")
            self.title_image = None
        
        # Load animated start button (256x128, 5 frames)
        self.button_frames = []
        self.button_frame_index = 0
        self.button_animation_timer = 0.0
        self.button_animation_speed = 0.15  # Time per frame in seconds
        try:
            button_sheet = pygame.image.load('asset/Startbtt.png').convert_alpha()
            sheet_width, sheet_height = button_sheet.get_size()
            # Extract 5 frames (assuming horizontal arrangement)
            frame_width = sheet_width // 5
            for i in range(5):
                frame_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_height)
                frame = button_sheet.subsurface(frame_rect)
                self.button_frames.append(frame)
        except Exception as e:
            print(f"Warning: Could not load Startbtt.png: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((100, 50), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 200))
            self.button_frames = [placeholder]
        
        self.on_start: Optional[Callable] = None
    
    def show(self):
        """Show start screen"""
        self.is_visible = True
    
    def hide(self):
        """Hide start screen"""
        self.is_visible = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle event.
        Returns:
            True if event was handled, False otherwise
        """
        if not self.is_visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                # Start game
                if self.on_start:
                    self.on_start()
                return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click anywhere to start
            if self.on_start:
                self.on_start()
            return True
        
        return False
    
    def update(self, dt: float):
        """Update animation"""
        if not self.is_visible:
            return
        
        # Update button animation
        if self.button_frames:
            self.button_animation_timer += dt
            if self.button_animation_timer >= self.button_animation_speed:
                self.button_animation_timer = 0.0
                self.button_frame_index = (self.button_frame_index + 1) % len(self.button_frames)
    
    def draw(self, surface: pygame.Surface):
        """Draw start screen"""
        if not self.is_visible:
            return
        
        # Draw background
        surface.blit(self.background, (0, 0))
        
        # Draw title in middle top
        if self.title_image:
            title_rect = self.title_image.get_rect()
            # Position at middle top (centered horizontally, near top)
            title_x = (self.screen_width - title_rect.width) // 2
            title_y = 100  # 100 pixels from top
            surface.blit(self.title_image, (title_x, title_y))
        
        # Draw animated button at middle bottom
        if self.button_frames:
            current_frame = self.button_frames[self.button_frame_index]
            frame_rect = current_frame.get_rect()
            # Position at middle bottom (centered horizontally, near bottom)
            button_x = (self.screen_width - frame_rect.width) // 2
            button_y = self.screen_height - 150  # 150 pixels from bottom
            surface.blit(current_frame, (button_x, button_y))

