"""
Building panel UI for upgrade and repair.
"""
import pygame
from typing import Optional, Callable
from world.building import Building, BuildState

class BuildingPanel:
    """Building panel UI for upgrade and repair"""
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, upgrade_panel_frames=None, upgrade_panel_darken_frames=None, panel_background_frames=None, upgrade_button_frames=None, demolish_button_frames=None, health_bar_frames=None, current_level_frames=None, next_level_frames=None):
        """
        Initialize building panel.
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            upgrade_panel_frames: List of 3 frames for upgrade progress panel
            upgrade_panel_darken_frames: List of 3 darkened frames for upgrade progress panel
            panel_background_frames: List of 3 frames (497x742 each) for building detail panel background
            upgrade_button_frames: List of 4 frames (277x84 each) for upgrade button with hover/press animation
            demolish_button_frames: List of 4 frames (91x68 each) for demolish button with pulsing animation
            health_bar_frames: List of 11 frames (280x27 each) for health bar display (0% to 100% in 10% increments)
            current_level_frames: List of 3 frames (70x80 each) for current tier/level display (1, 2, 3)
            next_level_frames: List of 3 frames (70x80 each) for next tier/level display (1, 2, 3)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Scale fonts up (1.2x - slightly bigger than original)
        self.font_large = pygame.font.Font(None, int(48 * 1.2))  # ~58
        self.font_medium = pygame.font.Font(None, int(32 * 1.2))  # ~38
        self.font_small = pygame.font.Font(None, int(24 * 1.2))  # ~29
        
        self.is_visible = False
        self.selected_building: Optional[Building] = None
        
        # Set panel size based on upgrade panel frames or background frames if available
        self.panel_background_frames = panel_background_frames if panel_background_frames else []
        self.upgrade_panel_frames = upgrade_panel_frames if upgrade_panel_frames else []
        
        if self.upgrade_panel_frames and len(self.upgrade_panel_frames) > 0:
            # Use upgrade panel frame size (375x475)
            bg_width, bg_height = self.upgrade_panel_frames[0].get_size()
            self.panel_rect = pygame.Rect(0, 0, bg_width, bg_height)
        elif self.panel_background_frames and len(self.panel_background_frames) > 0:
            bg_width, bg_height = self.panel_background_frames[0].get_size()
            self.panel_rect = pygame.Rect(0, 0, bg_width, bg_height)
        else:
            # Fallback size (scaled up)
            self.panel_rect = pygame.Rect(0, 0, int(300 * 1.2), int(400 * 1.2))
        


        #Placement for the panel
        self.panel_rect.bottomright = (screen_width - 10, screen_height - 140)
        
        # Scale factor for internal elements (1.2x - slightly bigger than original)
        self.scale = 1.2
        self.button_rects = {}  # Store button rects for click detection
        
        self.upgrade_panel_darken_frames = upgrade_panel_darken_frames if upgrade_panel_darken_frames else []
        self.upgrade_panel_rect = None  # Will be set when drawing
        
        self.upgrade_button_frames = upgrade_button_frames if upgrade_button_frames else []
        self.upgrade_button_rect = None  # Will be set when drawing
        self.upgrade_button_pressed = False  # Track if button is being pressed
        self.upgrade_button_animation_timer = 0.0  # Timer for animation
        self.upgrade_button_animation_speed = 0.1  # Time per frame (seconds)
        self.upgrade_button_animation_direction = 1  # 1 = forward, -1 = reverse
        self.upgrade_button_was_hovering = False  # Track previous hover state
        self.upgrade_button_animation_playing = False  # Track if animation is currently playing
        
        self.demolish_button_frames = demolish_button_frames if demolish_button_frames else []
        self.demolish_button_rect = None  # Will be set when drawing
        self.demolish_button_animation_timer = 0.0  # Timer for pulsing animation
        self.demolish_button_animation_speed = 0.15  # Time per frame (seconds) for pulsing
        
        self.health_bar_frames = health_bar_frames if health_bar_frames else []
        self.current_level_frames = current_level_frames if current_level_frames else []
        self.next_level_frames = next_level_frames if next_level_frames else []
        
        self.on_upgrade: Optional[Callable] = None
        self.on_repair: Optional[Callable] = None
        self.on_sell: Optional[Callable] = None
    
    def show(self, building: Building):
        """Show building panel"""
        self.is_visible = True
        self.selected_building = building
    
    def hide(self):
        """Hide building panel"""
        self.is_visible = False
        self.selected_building = None
    
    def handle_event(self, event: pygame.event.Event, mouse_pos) -> Optional[str]:
        """
        Handle event.
        Args:
            event: Pygame event
            mouse_pos: Mouse position tuple
        Returns:
            Button name if clicked, None otherwise
        """
        if not self.is_visible or not self.selected_building:
            return None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicking outside panel - close it
            if not self.panel_rect.collidepoint(mouse_pos):
                self.hide()
                return "close"
            
            # Check upgrade button click (if upgrade button is drawn)
            if self.upgrade_button_rect and self.upgrade_button_rect.collidepoint(mouse_pos):
                self.upgrade_button_pressed = True
                # Check if building can be upgraded
                from world.buildings.wall_wood import WallWood
                can_upgrade_to_iron = isinstance(self.selected_building, WallWood) and self.selected_building.state == BuildState.ACTIVE
                can_upgrade_tier = self.selected_building.tier < self.selected_building.TIER_MAX and self.selected_building.state == BuildState.ACTIVE
                if can_upgrade_to_iron:
                    return "upgrade_to_iron"
                elif can_upgrade_tier:
                    return "upgrade"
            
            # Check demolish button click
            if self.demolish_button_rect and self.demolish_button_rect.collidepoint(mouse_pos):
                return "demolish"
            
            # Check other button clicks
            if hasattr(self, 'button_rects'):
                for button_name, button_rect in self.button_rects.items():
                    if button_rect.collidepoint(mouse_pos):
                        return button_name
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Reset button press state
            self.upgrade_button_pressed = False
        
        return None
    
    def draw(self, surface: pygame.Surface, resources, mouse_pos=None, show_ui_rectangles: bool = False, dt: float = 0.016):
        """Draw building panel"""
        if not self.is_visible or not self.selected_building:
            return
        
        building = self.selected_building
        
        # DEBUG: Draw overlay rectangle for building panel (497x742, bottom-right)
        if show_ui_rectangles:
            panel_overlay = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
            panel_overlay.fill((255, 0, 128, 80))  # Pink overlay
            surface.blit(panel_overlay, self.panel_rect)
        
        # Draw panel background using upgrade panel frames - select frame based on upgrade progress
        # Initialize upgrade_progress if not set (backwards compatibility)
        if not hasattr(building, 'upgrade_progress'):
            building.upgrade_progress = 0
        
        # Use upgrade panel frames as the panel background
        if self.upgrade_panel_frames and len(self.upgrade_panel_frames) > 0:
            # Select frame based on upgrade progress and tier
            # Frame 0-2: upgrade progress states (0, 1, 2)
            # Frame 3: max upgraded state (when tier == 3 or TIER_MAX)
            if building.tier >= building.TIER_MAX:
                # Building is at max tier - use last frame (frame 3)
                frame_index = len(self.upgrade_panel_frames) - 1
            else:
                # Use upgrade progress (0, 1, 2)
                frame_index = min(building.upgrade_progress, len(self.upgrade_panel_frames) - 2)
            
            # Ensure frame index is within bounds
            frame_index = min(frame_index, len(self.upgrade_panel_frames) - 1)
            current_background = self.upgrade_panel_frames[frame_index]
            
            # Draw at natural size (375x475) at the panel position
            surface.blit(current_background, self.panel_rect)
        elif self.panel_background_frames and len(self.panel_background_frames) > 0:
            # Fallback to panel_background_frames if upgrade_panel_frames not available
            frame_index = min(building.upgrade_progress, len(self.panel_background_frames) - 1)
            current_background = self.panel_background_frames[frame_index]
            surface.blit(current_background, self.panel_rect)
        else:
            # Fallback: simple background if frames not loaded
            panel_bg = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
            panel_bg.fill((50, 50, 50, 230))
            surface.blit(panel_bg, self.panel_rect)
            # Draw panel border
            pygame.draw.rect(surface, (200, 200, 200), self.panel_rect, 3)
        
        # Draw building info (scaled up)
        y_offset = self.panel_rect.y + int(20 * self.scale)
        line_height = int(30 * self.scale)
        
        # Building name (use larger font)
        building_name = building.TYPE_ID.replace('_', ' ').title()
        name_surface = self.font_large.render(building_name, True, (255, 255, 255))
        surface.blit(name_surface, (self.panel_rect.x + int(10 * self.scale), y_offset))
        y_offset += line_height + int(10 * self.scale)
        
        # HP text
        hp_text = f"HP: {building.hp} / {building.max_hp}"
        hp_surface = self.font_medium.render(hp_text, True, (255, 255, 255))
        surface.blit(hp_surface, (self.panel_rect.x + int(10 * self.scale), y_offset))
        y_offset += line_height
        
        # Draw HP bar using health bar frames at position (48, 115) relative to panel
        if self.health_bar_frames and len(self.health_bar_frames) > 0:
            hp_percent = building.hp / building.max_hp if building.max_hp > 0 else 0
            # Calculate frame index: 0% = frame 0, 10% = frame 1, ..., 100% = frame 10
            # Clamp hp_percent to 0-1 range and convert to frame index (0-10)
            frame_index = int(hp_percent * 10)
            frame_index = max(0, min(len(self.health_bar_frames) - 1, frame_index))
            
            # Position at (48, 115) relative to panel
            health_bar_x = self.panel_rect.x + 48
            health_bar_y = self.panel_rect.y + 115
            
            # Get the health bar frame
            health_bar_frame = self.health_bar_frames[frame_index]
            
            # Draw the health bar
            surface.blit(health_bar_frame, (health_bar_x, health_bar_y))
        else:
            # Fallback: draw HP bar (scaled) if frames not loaded
            hp_bar_rect = pygame.Rect(self.panel_rect.x + int(10 * self.scale), y_offset, 
                                      self.panel_rect.width - int(20 * self.scale), int(20 * self.scale))
            hp_percent = building.hp / building.max_hp if building.max_hp > 0 else 0
            hp_color = (0, 255, 0) if hp_percent > 0.5 else (255, 255, 0) if hp_percent > 0.25 else (255, 0, 0)
            pygame.draw.rect(surface, (0, 0, 0), hp_bar_rect)
            pygame.draw.rect(surface, hp_color, (hp_bar_rect.x, hp_bar_rect.y, int(hp_bar_rect.width * hp_percent), hp_bar_rect.height))
        
        y_offset += line_height + int(10 * self.scale)
        
        # Tier - draw current level number
        if self.current_level_frames and len(self.current_level_frames) > 0:
            # Get tier (1, 2, or 3) - convert to frame index (0, 1, or 2)
            tier = building.tier
            level_frame_index = tier - 1  # tier 1 = frame 0, tier 2 = frame 1, tier 3 = frame 2
            level_frame_index = max(0, min(len(self.current_level_frames) - 1, level_frame_index))
            
            # Check if we're on the last upgrade panel frame (max upgraded)
            is_max_upgraded = building.tier >= building.TIER_MAX
            
            if is_max_upgraded:
                # Use position (170, 195) for max upgraded state
                # Adjust for wider numbers (2 and 3) - move them left
                base_x = 168
                if level_frame_index == 1:  # Number 2
                    x_offset = -5  # Move left by 5 pixels
                elif level_frame_index == 2:  # Number 3
                    x_offset = -14  # Move left by 14 pixels
                else:  # Number 1
                    x_offset = 0
                
                level_x = self.panel_rect.x + base_x + x_offset
                level_y = self.panel_rect.y + 195
            else:
                # Base position - frame 1 (number 1) is at x=52, y=170
                base_x = 52
                # Adjust for wider numbers (2 and 3) - move them left
                if level_frame_index == 1:  # Number 2
                    x_offset = -5  # Move left by 5 pixels
                elif level_frame_index == 2:  # Number 3
                    x_offset = -14  # Move left by 14 pixels
                else:  # Number 1
                    x_offset = 0
                
                level_x = self.panel_rect.x + base_x + x_offset
                level_y = self.panel_rect.y + 170
            
            # Get the level frame
            level_frame = self.current_level_frames[level_frame_index]
            
            # Draw the current level number
            surface.blit(level_frame, (level_x, level_y))
            
            # Draw next level number at x=285, same y as current level
            if self.next_level_frames and len(self.next_level_frames) > 0 and building.tier < building.TIER_MAX:
                # Get next tier (current tier + 1)
                next_tier = building.tier + 1
                next_level_frame_index = next_tier - 1  # tier 2 = frame 1, tier 3 = frame 2
                next_level_frame_index = max(0, min(len(self.next_level_frames) - 1, next_level_frame_index))
                
                # Base position - frame 1 (number 1) is at x=285
                next_base_x = 285
                # Adjust for wider numbers (2 and 3) - move them left (same offsets as current level)
                if next_level_frame_index == 1:  # Number 2
                    next_x_offset = -5  # Move left by 5 pixels
                elif next_level_frame_index == 2:  # Number 3
                    next_x_offset = -14  # Move left by 14 pixels
                else:  # Number 1
                    next_x_offset = 0
                
                next_level_x = self.panel_rect.x + next_base_x + next_x_offset
                next_level_y = level_y  # Same y as current level
                
                # Get the next level frame
                next_level_frame = self.next_level_frames[next_level_frame_index]
                
                # Draw the next level number
                surface.blit(next_level_frame, (next_level_x, next_level_y))
        else:
            # Fallback: draw tier text if frames not loaded
            tier_text = f"Tier: {building.tier} / {building.TIER_MAX}"
            tier_surface = self.font_medium.render(tier_text, True, (255, 255, 255))
            surface.blit(tier_surface, (self.panel_rect.x + int(10 * self.scale), y_offset))
        
        # Buttons (store rects for click detection)
        self.button_rects = {}
        
        # Upgrade clickable area - coordinates (42, 404) to (450, 541) relative to panel background
        # Check if this is a wood wall that can be upgraded to iron
        from world.buildings.wall_wood import WallWood
        can_upgrade_to_iron = isinstance(building, WallWood) and building.state == BuildState.ACTIVE
        can_upgrade_tier = building.tier < building.TIER_MAX and building.state == BuildState.ACTIVE
        
        # Initialize upgrade_progress if not set (backwards compatibility)
        if not hasattr(building, 'upgrade_progress'):
            building.upgrade_progress = 0
        
        # Set up upgrade clickable area if building can be upgraded
        if can_upgrade_to_iron or can_upgrade_tier:
            # Clickable area coordinates relative to panel background: (42, 404) to (450, 541)
            # Scale these coordinates by the panel scale factor
            clickable_left = int(42 * self.scale)
            clickable_top = int(404 * self.scale)
            clickable_width = int((450 - 42) * self.scale)  # 408 * scale
            clickable_height = int((541 - 404) * self.scale)  # 137 * scale
            
            # Calculate clickable area position on screen (relative to panel position)
            clickable_x = self.panel_rect.x + clickable_left
            clickable_y = self.panel_rect.y + clickable_top
            
            # Store clickable area rect for click detection
            self.upgrade_panel_rect = pygame.Rect(clickable_x, clickable_y, clickable_width, clickable_height)
            
            # DEBUG: Draw overlay rectangle for upgrade clickable area (408x137)
            if show_ui_rectangles:
                upgrade_overlay = pygame.Surface((clickable_width, clickable_height), pygame.SRCALPHA)
                upgrade_overlay.fill((0, 255, 128, 100))  # Light green overlay for upgrade area
                surface.blit(upgrade_overlay, self.upgrade_panel_rect)
            
            # Register upgrade button
            if can_upgrade_to_iron:
                self.button_rects["upgrade_to_iron"] = self.upgrade_panel_rect
            else:
                self.button_rects["upgrade"] = self.upgrade_panel_rect
        
        # Draw upgrade button at position (74, 330) relative to panel
        if self.upgrade_button_frames and len(self.upgrade_button_frames) > 0:
            button_x = self.panel_rect.x + 74
            button_y = self.panel_rect.y + 330
            
            # Get button dimensions from first frame
            button_width, button_height = self.upgrade_button_frames[0].get_size()
            
            # Create or update button rect for click detection
            self.upgrade_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # Check if mouse is hovering over upgrade button
            is_hovering = mouse_pos and self.upgrade_button_rect.collidepoint(mouse_pos)
            frame_count = len(self.upgrade_button_frames)
            max_time = self.upgrade_button_animation_speed * (frame_count - 1)  # Time to reach last frame
            
            # Detect hover state changes
            if is_hovering and not self.upgrade_button_was_hovering:
                # Mouse just entered - start forward animation
                self.upgrade_button_animation_direction = 1
                self.upgrade_button_animation_playing = True
                self.upgrade_button_animation_timer = 0.0
            elif not is_hovering and self.upgrade_button_was_hovering:
                # Mouse just left - start reverse animation
                self.upgrade_button_animation_direction = -1
                self.upgrade_button_animation_playing = True
                # Start from current position (or last frame if we were at the end)
                if self.upgrade_button_animation_timer >= max_time:
                    self.upgrade_button_animation_timer = max_time
            
            # Update animation timer if playing
            if self.upgrade_button_animation_playing:
                self.upgrade_button_animation_timer += dt * self.upgrade_button_animation_direction
                
                # Check if forward animation finished
                if self.upgrade_button_animation_direction == 1 and self.upgrade_button_animation_timer >= max_time:
                    self.upgrade_button_animation_timer = max_time
                    self.upgrade_button_animation_playing = False
                    # Stay on last frame if still hovering
                    if is_hovering:
                        frame_index = frame_count - 1
                    else:
                        frame_index = int(self.upgrade_button_animation_timer / self.upgrade_button_animation_speed)
                # Check if reverse animation finished
                elif self.upgrade_button_animation_direction == -1 and self.upgrade_button_animation_timer <= 0.0:
                    self.upgrade_button_animation_timer = 0.0
                    self.upgrade_button_animation_playing = False
                    frame_index = 0
                else:
                    # Animation still playing
                    frame_index = int(self.upgrade_button_animation_timer / self.upgrade_button_animation_speed)
                    frame_index = max(0, min(frame_count - 1, frame_index))  # Clamp to valid range
            else:
                # Animation not playing - determine frame based on current state
                if is_hovering:
                    # Stay on last frame if hovering and animation finished
                    frame_index = frame_count - 1
                else:
                    # Stay on first frame if not hovering
                    frame_index = 0
            
            # Update previous hover state
            self.upgrade_button_was_hovering = is_hovering
            
            # Get the button frame
            button_frame = self.upgrade_button_frames[frame_index]
            
            # Draw the upgrade button
            surface.blit(button_frame, (button_x, button_y))
        
        # Draw demolish button at position (301, 0) relative to panel
        if self.demolish_button_frames and len(self.demolish_button_frames) > 0:
            demolish_button_x = self.panel_rect.x + 301
            demolish_button_y = self.panel_rect.y - 7
            
            # Get button dimensions from first frame
            demolish_button_width, demolish_button_height = self.demolish_button_frames[0].get_size()
            
            # Create or update button rect for click detection
            self.demolish_button_rect = pygame.Rect(demolish_button_x, demolish_button_y, demolish_button_width, demolish_button_height)
            
            # Check if mouse is hovering over demolish button
            is_hovering_demolish = mouse_pos and self.demolish_button_rect.collidepoint(mouse_pos)
            
            # Rubber band pulsing animation when hovering
            if is_hovering_demolish:
                # Update animation timer
                self.demolish_button_animation_timer += dt
                
                # Create rubber band effect: go forward then backward repeatedly
                # Use triangle wave for smooth forward-backward pulsing motion
                demolish_frame_count = len(self.demolish_button_frames)
                max_time = self.demolish_button_animation_speed * (demolish_frame_count - 1)
                cycle_time = max_time * 2  # Full cycle: forward + backward
                
                # Create triangle wave: 0 -> max_time -> 0 -> max_time...
                cycle_position = self.demolish_button_animation_timer % cycle_time
                if cycle_position <= max_time:
                    # Forward: 0 to max_time
                    normalized_time = cycle_position
                else:
                    # Backward: max_time to 0
                    normalized_time = max_time - (cycle_position - max_time)
                
                # Calculate frame index based on normalized time
                demolish_frame_index = int(normalized_time / self.demolish_button_animation_speed)
                demolish_frame_index = max(0, min(demolish_frame_count - 1, demolish_frame_index))
            else:
                # Reset to first frame when not hovering
                self.demolish_button_animation_timer = 0.0
                demolish_frame_index = 0
            
            # Get the demolish button frame
            demolish_button_frame = self.demolish_button_frames[demolish_frame_index]
            
            # Draw the demolish button
            surface.blit(demolish_button_frame, (demolish_button_x, demolish_button_y))
    
    def _get_upgrade_cost(self, building: Building):
        """Get upgrade cost for building (per progress step, not per tier)"""
        from world.building import Cost
        base_cost = building.COST
        # Cost increases with tier, but is per progress step (1/3 of tier upgrade cost)
        upgrade_mult = 1.25  # 25% increase per tier
        tier_cost_mult = upgrade_mult * building.tier
        # Divide by 3 since it takes 3 upgrades to reach next tier
        return Cost(
            wood=int(base_cost.wood * tier_cost_mult / 3),
            iron=int(base_cost.iron * tier_cost_mult / 3),
            food=int(base_cost.food * tier_cost_mult / 3)
        )
    
    def _get_repair_cost(self, building: Building):
        """Get repair cost for building"""
        from world.building import Cost
        hp_needed = building.max_hp - building.hp
        # 1 wood per 5 HP
        wood_cost = max(1, hp_needed // 5)
        return Cost(wood=wood_cost, iron=0, food=0)
    
    def _get_wall_upgrade_cost(self):
        """Get upgrade cost for wood wall → iron wall"""
        from world.building import Cost
        return Cost(wood=10, iron=40, food=0)

