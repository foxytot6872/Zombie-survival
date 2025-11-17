"""Farm building."""
import pygame
import random
from world.building import Building, Cost, Production, TILE, BuildState

class Farm(Building):
    """Farm - produces food."""
    TYPE_ID = "farm"
    BASE_HP = 120
    BUILD_TIME = 4.0
    COST = Cost(wood=60, iron=0)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSIVE = Production(food_per_min=120.0)  # 10 food per 5 seconds = 120 per minute
    
    # Farm tile variants (loaded once at class level)
    farm_variants = None
    
    @classmethod
    def _load_farm_variants(cls):
        """Load farm tile variants from Farm.png (3 variants, 32x32 each)"""
        if cls.farm_variants is not None:
            return  # Already loaded
        
        try:
            farm_sheet = pygame.image.load('asset/Farm.png').convert_alpha()
            sheet_width, sheet_height = farm_sheet.get_size()
            
            # Extract 3 variants (TILE x TILE each, arranged horizontally)
            cls.farm_variants = []
            frame_width = TILE
            frame_height = TILE
            
            for i in range(3):
                if i * frame_width < sheet_width:
                    frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                    variant = farm_sheet.subsurface(frame_rect)
                    cls.farm_variants.append(variant)
                else:
                    # Create placeholder if variant missing
                    placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    placeholder.fill((100, 150, 100, 255))
                    cls.farm_variants.append(placeholder)
        except Exception as e:
            print(f"Warning: Could not load Farm.png: {e}, using placeholder")
            # Create placeholder variants
            cls.farm_variants = []
            for i in range(3):
                placeholder = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                placeholder.fill((100, 150, 100, 255))
                cls.farm_variants.append(placeholder)
    
    def __init__(self, grid_pos, tier=1, uid=None, world=None):
        # Load farm variants if not already loaded
        Farm._load_farm_variants()
        
        super().__init__(grid_pos, tier, uid, world)
        
        # Randomly select a farm variant
        if Farm.farm_variants and len(Farm.farm_variants) > 0:
            self.farm_variant = random.choice(Farm.farm_variants)
        else:
            self.farm_variant = None
        
        self.selected = False
    
    def draw(self, surface: pygame.Surface):
        """Draw farm with selected variant"""
        self.image.fill((0, 0, 0, 0))
        w, h = self.FOOTPRINT
        
        # Draw farm variant if available (always draw normally first)
        if self.farm_variant:
            self.image.blit(self.farm_variant, (0, 0))
        else:
            # Fallback: green rectangle
            color = (100, 150, 100) if self.state != BuildState.DESTROYED else (80, 30, 30)
            pygame.draw.rect(self.image, color, (0, 0, w*TILE, h*TILE))
        
        # Draw construction overlay if constructing (like gatling turret)
        if self.state == BuildState.CONSTRUCTING:
            overlay = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
            overlay.fill((100, 100, 100, 100))  # Semi-transparent grey overlay
            self.image.blit(overlay, (0, 0))
            
            # Build progress bar
            pct = self.progress / self.BUILD_TIME if self.BUILD_TIME > 0 else 1.0
            pygame.draw.rect(self.image, (200, 220, 80), (2, h*TILE-6, int((w*TILE-4)*pct), 4))
        
        # HP bar (if damaged)
        if self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            hp_pct = self.hp / self.max_hp
            hp_color = (0, 255, 0) if hp_pct > 0.5 else (255, 255, 0) if hp_pct > 0.25 else (255, 0, 0)
            pygame.draw.rect(self.image, hp_color, (2, 2, int((w*TILE-4)*hp_pct), 4))
        
        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)
        
        # Draw selection highlight
        if self.selected and self.state == BuildState.ACTIVE:
            pygame.draw.rect(surface, (255, 255, 0), self.rect, 2)

