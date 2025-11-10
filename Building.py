"""
Building system with construction phases and upgrades
"""
import pygame as pg
from config import GRID_SIZE, BUILDING_COSTS

class Building(pg.sprite.Sprite):
    # Construction phases
    FOUNDATION = 0
    SCAFFOLD = 1
    COMPLETE = 2
    
    def __init__(self, grid_x, grid_y, building_type, tier=1):
        pg.sprite.Sprite.__init__(self)
        
        self.building_type = building_type
        self.tier = tier
        self.grid_x = grid_x
        self.grid_y = grid_y
        
        # Convert grid to world position
        self.world_x = grid_x * GRID_SIZE + GRID_SIZE // 2
        self.world_y = grid_y * GRID_SIZE + GRID_SIZE // 2
        
        # Construction state
        self.construction_phase = self.FOUNDATION
        self.construction_progress = 0.0  # 0.0 to 1.0
        self.construction_speed = 0.01  # Progress per frame (adjust based on builders)
        
        # Building stats (scale with tier)
        base_hp = 100
        self.max_hp = int(base_hp * (1 + (tier - 1) * 0.5))  # +50% HP per tier
        self.hp = self.max_hp
        self.width = 1  # Grid cells
        self.height = 1
        
        # Create image based on type and phase
        self.update_image()
        
        self.rect = self.image.get_rect()
        self.rect.center = (self.world_x, self.world_y)
    
    def update_image(self):
        """Update building image based on type, tier, and construction phase"""
        size = GRID_SIZE
        
        if self.construction_phase == self.FOUNDATION:
            # Foundation phase - gray rectangle
            self.image = pg.Surface((size, size), pg.SRCALPHA)
            pg.draw.rect(self.image, (80, 80, 80), (0, 0, size, size))
            pg.draw.rect(self.image, (100, 100, 100), (2, 2, size-4, size-4))
        
        elif self.construction_phase == self.SCAFFOLD:
            # Scaffold phase - yellow/brown scaffolding
            self.image = pg.Surface((size, size), pg.SRCALPHA)
            pg.draw.rect(self.image, (139, 69, 19), (0, 0, size, size))
            # Draw scaffold lines
            for i in range(0, size, 4):
                pg.draw.line(self.image, (160, 82, 45), (i, 0), (i, size), 1)
                pg.draw.line(self.image, (160, 82, 45), (0, i), (size, i), 1)
        
        else:  # COMPLETE
            # Complete phase - actual building
            self.image = pg.Surface((size, size), pg.SRCALPHA)
            self._draw_complete_building()
    
    def _draw_complete_building(self):
        """Draw the completed building based on type"""
        size = GRID_SIZE
        colors = {
            "Wall": (120, 120, 120),
            "Gate": (100, 100, 100),
            "Turret_Mk1": (150, 150, 150),
            "Turret_Mk2": (180, 180, 180),
            "Turret_Mk3": (200, 200, 200),
            "Housing": (139, 69, 19),
            "Farm": (34, 139, 34),
            "Sawmill": (160, 82, 45),
            "Smelter": (105, 105, 105),
            "Hospital": (255, 255, 255),
            "Research_Lab": (70, 130, 180),
            "HQ": (139, 0, 0)
        }
        
        color = colors.get(self.building_type, (100, 100, 100))
        
        # Draw building base
        pg.draw.rect(self.image, color, (2, 2, size-4, size-4))
        pg.draw.rect(self.image, (color[0]*0.7, color[1]*0.7, color[2]*0.7), (2, 2, size-4, size-4), 2)
        
        # Add building-specific details
        if "Turret" in self.building_type:
            # Draw turret base circle (darker for higher tiers)
            base_color = (60 + self.tier * 20, 60 + self.tier * 20, 60 + self.tier * 20)
            pg.draw.circle(self.image, base_color, (size//2, size//2), size//3)
            # Draw tier indicator
            if self.tier > 1:
                tier_color = (255, 215, 0) if self.tier == 2 else (255, 140, 0)
                pg.draw.circle(self.image, tier_color, (size-8, 8), 4)
        elif self.building_type == "HQ":
            # Draw HQ flag
            pg.draw.rect(self.image, (255, 0, 0), (size-8, 2, 6, 8))
            # Draw tier indicator
            if self.tier > 1:
                tier_color = (255, 215, 0) if self.tier == 2 else (255, 140, 0)
                pg.draw.circle(self.image, tier_color, (size-12, size-8), 4)
        
        # Draw tier border for upgraded buildings
        if self.tier > 1:
            tier_color = (255, 215, 0) if self.tier == 2 else (255, 140, 0)
            pg.draw.rect(self.image, tier_color, (0, 0, size, size), 2)
    
    def update(self, builders_count=0):
        """Update construction progress"""
        if self.construction_phase < self.COMPLETE:
            # Increase construction speed with builders
            speed = self.construction_speed * (1 + builders_count * 0.5)
            self.construction_progress += speed
            
            if self.construction_progress >= 0.33 and self.construction_phase == self.FOUNDATION:
                self.construction_phase = self.SCAFFOLD
                self.update_image()
            elif self.construction_progress >= 1.0:
                self.construction_phase = self.COMPLETE
                self.construction_progress = 1.0
                self.update_image()
    
    def is_complete(self):
        """Check if building is complete"""
        return self.construction_phase == self.COMPLETE
    
    def take_damage(self, damage):
        """Take damage"""
        if self.is_complete():
            self.hp -= damage
            if self.hp < 0:
                self.hp = 0
            return self.hp <= 0
        return False
    
    def draw_construction_bar(self, screen):
        """Draw construction progress bar"""
        if self.construction_phase < self.COMPLETE:
            bar_width = GRID_SIZE
            bar_height = 4
            x = self.rect.left
            y = self.rect.top - 8
            
            # Background
            pg.draw.rect(screen, (50, 50, 50), (x, y, bar_width, bar_height))
            # Progress
            progress_width = int(bar_width * self.construction_progress)
            pg.draw.rect(screen, (0, 255, 0), (x, y, progress_width, bar_height))
            # Border
            pg.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 1)
    
    def draw_health_bar(self, screen):
        """Draw health bar"""
        if self.is_complete() and self.hp < self.max_hp:
            bar_width = GRID_SIZE
            bar_height = 4
            x = self.rect.left
            y = self.rect.bottom + 2
            
            # Background
            pg.draw.rect(screen, (100, 0, 0), (x, y, bar_width, bar_height))
            # Health
            health_width = int(bar_width * (self.hp / self.max_hp))
            pg.draw.rect(screen, (0, 200, 0), (x, y, health_width, bar_height))
            # Border
            pg.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 1)
    
    @staticmethod
    def get_cost(building_type, difficulty_multiplier=1.0):
        """Get building cost with difficulty multiplier"""
        costs = BUILDING_COSTS.get(building_type, {})
        return {k: int(v * difficulty_multiplier) for k, v in costs.items()}
    
    @staticmethod
    def get_upgrade_cost(building_type, current_tier, difficulty_multiplier=1.0):
        """Get upgrade cost for building"""
        if current_tier >= 3:  # Max tier
            return None
        
        base_cost = BUILDING_COSTS.get(building_type, {})
        # Upgrade cost is 1.5x base cost per tier
        upgrade_multiplier = 1.5 ** current_tier
        costs = {k: int(v * upgrade_multiplier * difficulty_multiplier) for k, v in base_cost.items()}
        return costs
    
    @staticmethod
    def get_refund(building_type, tier, difficulty_multiplier=1.0):
        """Get refund amount when demolishing (50% of total cost)"""
        base_cost = BUILDING_COSTS.get(building_type, {})
        # Calculate total cost including all upgrades
        total_cost = {}
        for t in range(1, tier + 1):
            upgrade_mult = 1.5 ** (t - 1) if t > 1 else 1.0
            for resource, amount in base_cost.items():
                total_cost[resource] = total_cost.get(resource, 0) + int(amount * upgrade_mult * difficulty_multiplier)
        
        # Refund 50%
        refund = {k: int(v * 0.5) for k, v in total_cost.items()}
        return refund

