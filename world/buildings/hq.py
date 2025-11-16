"""HQ (Headquarters) building."""
from world.building import Building, Cost, BuildState, TILE
import pygame

class HQ(Building):
    """Headquarters - main base building."""
    TYPE_ID = "hq"
    BASE_HP = 2000
    BUILD_TIME = 0.0  # Spawns active (no construction time)
    COST = Cost()  # No cost for initial HQ
    FOOTPRINT = (2, 2)
    TIER_MAX = 1  # No upgrades for now
    
    # Class-level image (set from main.py after loading)
    building_image = None
    
    def __init__(self, grid_pos, tier=1, uid=None, building_image=None, world=None):
        super().__init__(grid_pos, tier, uid, world)
        # Use provided image or class-level image
        self.building_image = building_image if building_image is not None else HQ.building_image
        # HQ spawns immediately active
        self.state = BuildState.ACTIVE
        self.hp = self.max_hp
        self.progress = 0.0
    
    def update(self, dt, world=None):
        """Update HQ - optional tiny regen during day"""
        super().update(dt, world)
        
        # Optional: slow auto-repair during DAY (configurable)
        # Check if it's day time (from wave manager or world)
        is_day = False
        if world:
            # Check wave manager state if available
            if hasattr(world, 'wave_manager'):
                is_day = world.wave_manager.state == "DAY"
            elif hasattr(world, 'is_day'):
                is_day = world.is_day
        
        # Small regen during day (configurable, default ~30 HP/min)
        if is_day and self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            regen_rate = 0.5  # HP per second (~30 HP/min)
            self.hp = min(self.max_hp, self.hp + regen_rate * dt)
    
    def draw(self, surface: pygame.Surface):
        """Draw HQ with custom image"""
        w, h = self.FOOTPRINT
        footprint_width = w * TILE
        footprint_height = h * TILE
        
        # Determine image dimensions - use actual image size to avoid cropping
        if self.building_image:
            img_width, img_height = self.building_image.get_size()
            # Use the larger of footprint or image size to ensure no cropping
            display_width = max(footprint_width, img_width)
            display_height = max(footprint_height, img_height)
        else:
            display_width = footprint_width
            display_height = footprint_height
        
        # Add space below for HP bar
        hp_bar_height = 8
        hp_bar_spacing = 4
        total_height = display_height + hp_bar_height + hp_bar_spacing
        
        # Update image size if needed
        if self.image.get_size() != (display_width, total_height):
            self.image = pygame.Surface((display_width, total_height), pygame.SRCALPHA)
        
        # Clear image
        self.image.fill((0, 0, 0, 0))
        
        # Draw building image if available
        if self.building_image:
            # Draw image at its natural size (or scale to fit footprint if smaller)
            img_width, img_height = self.building_image.get_size()
            if img_width <= display_width and img_height <= display_height:
                # Image fits, draw it as-is (centered if smaller than footprint)
                img_x = (display_width - img_width) // 2
                img_y = (display_height - img_height) // 2
                self.image.blit(self.building_image, (img_x, img_y))
            else:
                # Image is larger, scale it down to fit while maintaining aspect ratio
                scale_w = display_width / img_width
                scale_h = display_height / img_height
                scale = min(scale_w, scale_h)  # Use smaller scale to fit both dimensions
                scaled_width = int(img_width * scale)
                scaled_height = int(img_height * scale)
                scaled_image = pygame.transform.smoothscale(self.building_image, (scaled_width, scaled_height))
                img_x = (display_width - scaled_width) // 2
                img_y = (display_height - scaled_height) // 2
                self.image.blit(scaled_image, (img_x, img_y))
        else:
            # Fallback to default drawing
            if self.state == BuildState.DESTROYED:
                color = (80, 30, 30)  # Dark red when destroyed
            else:
                color = (50, 100, 150)  # Blue-grey for HQ
            
            # Draw main building
            pygame.draw.rect(self.image, color, (0, 0, footprint_width, footprint_height))
            # Draw border
            pygame.draw.rect(self.image, (100, 150, 200), (0, 0, footprint_width, footprint_height), 3)
            # Draw cross symbol in center to indicate HQ
            center_x, center_y = footprint_width // 2, footprint_height // 2
            cross_size = 10
            pygame.draw.line(self.image, (200, 200, 255), 
                            (center_x - cross_size, center_y), 
                            (center_x + cross_size, center_y), 3)
            pygame.draw.line(self.image, (200, 200, 255), 
                            (center_x, center_y - cross_size), 
                            (center_x, center_y + cross_size), 3)
        
        # HP bar (always show for HQ since it's important) - draw below the image
        if self.state == BuildState.ACTIVE:
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 1.0
            hp_color = (0, 255, 0) if hp_pct > 0.6 else (255, 255, 0) if hp_pct > 0.3 else (255, 0, 0)
            bar_height = hp_bar_height
            bar_y = display_height + hp_bar_spacing  # Position below the image
            bar_width = display_width - 4
            bar_x = 2
            # Background bar
            pygame.draw.rect(self.image, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # HP bar (always draw, even at full HP)
            hp_bar_width = int(bar_width * hp_pct)
            if hp_bar_width > 0:
                pygame.draw.rect(self.image, hp_color, (bar_x, bar_y, hp_bar_width, bar_height))
        
        # Update rect position (center on building position, accounting for extra height)
        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)
    
    def on_destroy(self):
        """Called when HQ is destroyed"""
        # Nothing special - game_state handles GAME OVER
        pass

