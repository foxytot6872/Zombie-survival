"""Smelter building with dynamic sprite upgrades."""
from __future__ import annotations

import os
import pygame
from typing import List, Union

from world.building import Building, Cost, Production

SPRITE_CACHE = {}


def load_smelter_sprite(path: str) -> pygame.Surface:
    """Load sprite surface with caching and placeholder fallback."""
    if path in SPRITE_CACHE:
        return SPRITE_CACHE[path]

    if os.path.exists(path):
        try:
            loaded = pygame.image.load(path).convert_alpha()
            SPRITE_CACHE[path] = loaded
            print(f"Loaded smelter sprite: {path} ({loaded.get_width()}x{loaded.get_height()})")
            return loaded
        except Exception as e:
            print(f"Warning: Failed to load smelter sprite {path}: {e}")

    # Placeholder if missing
    print(f"Warning: Smelter sprite not found at {path}, using placeholder")
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    surface.fill((90, 70, 70))
    pygame.draw.rect(surface, (30, 20, 20), surface.get_rect(), 2)
    SPRITE_CACHE[path] = surface
    return surface


def prepare_frames(surface: pygame.Surface, frame_width: int = 96) -> Union[List[pygame.Surface], pygame.Surface]:
    """
    Split horizontal sprite sheet into frames.
    For smelter: 96x96 per frame, 4 frames = 384x96 sprite sheet.
    """
    height = surface.get_height()
    width = surface.get_width()

    if height == 0 or width == 0:
        return surface

    # Check if width is divisible by frame_width (indicates multiple frames)
    if width >= frame_width and width % frame_width == 0:
        frames = []
        num_frames = width // frame_width
        for x in range(0, width, frame_width):
            frame = surface.subsurface((x, 0, frame_width, height)).copy()
            frames.append(frame)
        print(f"Split sprite sheet into {num_frames} frames ({frame_width}x{height} each)")
        return frames

    # Single frame
    return surface


class Smelter(Building):
    """Smelter - produces iron and visually upgrades via research."""

    TYPE_ID = "smelter"
    BASE_HP = 140
    BUILD_TIME = 4.5
    COST = Cost(wood=40, iron=40)
    FOOTPRINT = (2, 2)  # width 2, height 2 tiles
    TIER_MAX = 3
    PASSIVE = Production(iron_per_min=120.0)  # 10 iron per 5 seconds = 120 per minute

    LEVEL_SPRITES = {
        1: ("asset/smelter/Bricks_01-Sheet.png",),
        2: ("asset/smelter/Bricks_02-Sheet.png",),
        3: ("asset/smelter/Bricks_03-Sheet.png",),
    }

    def __init__(self, grid_pos, tier=1, uid=None):
        super().__init__(grid_pos, tier=tier, uid=uid)
        # Sync level with tier for sprite selection
        self.level = self.tier
        self.level_sprites = self._load_level_sprites()
        
        # Animation state
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.2  # seconds per frame (adjust for animation speed)
        
        # Sprite scale factor (make sprites bigger)
        self.sprite_scale = 1  # Scale up by 2x
        
        self.update_sprite()
    
    def on_upgrade(self):
        """Update sprite when tier upgrades."""
        super().on_upgrade()
        # Sync level with tier when upgraded
        self.level = self.tier

    def _load_level_sprites(self):
        sprites = {}
        # Frame sizes per tier: tier 1 = 64x64, tier 2-3 = 96x96
        frame_sizes = {
            1: 64,  # 64x64 per frame, 4 frames = 256x64
            2: 96,  # 96x96 per frame, 4 frames = 384x96
            3: 96,  # 96x96 per frame, 4 frames = 384x96
        }
        
        for level, paths in self.LEVEL_SPRITES.items():
            surface = None
            for path in paths:
                surface = load_smelter_sprite(path)
                if surface is not None:
                    break
            if surface is None:
                # Create placeholder if all paths failed
                frame_width = frame_sizes.get(level, 96)
                placeholder_width = frame_width * 4  # 4 frames
                placeholder_height = frame_width
                surface = pygame.Surface((placeholder_width, placeholder_height), pygame.SRCALPHA)
                surface.fill((90, 70, 70))
                pygame.draw.rect(surface, (30, 20, 20), surface.get_rect(), 2)
            # Split into 4 frames with appropriate frame width for this tier
            frame_width = frame_sizes.get(level, 96)
            sprites[level] = prepare_frames(surface, frame_width=frame_width)
        return sprites
    
    def update(self, dt: float, world=None):
        """Update animation timer."""
        super().update(dt, world)
        
        # Update animation
        if hasattr(self, 'level_sprites') and self.level_sprites:
            sprite_data = self.level_sprites.get(self.level)
            if sprite_data is None:
                max_level = max(self.level_sprites.keys())
                sprite_data = self.level_sprites.get(max_level)
            
            if isinstance(sprite_data, list) and len(sprite_data) > 0:
                self.animation_timer += dt
                if self.animation_timer >= self.animation_delay:
                    self.animation_timer = 0.0
                    self.frame_index = (self.frame_index + 1) % len(sprite_data)
    
    def draw(self, surface: pygame.Surface):
        """Draw smelter with animated sprite from level_sprites."""
        from world.building import BuildState
        
        # Get current frame from level_sprites
        sprite = None
        if hasattr(self, 'level_sprites') and self.level_sprites:
            sprite_data = self.level_sprites.get(self.level)
            if sprite_data is None:
                # Fall back to highest available level
                max_level = max(self.level_sprites.keys())
                sprite_data = self.level_sprites.get(max_level)
            
            if sprite_data:
                if isinstance(sprite_data, list):
                    # Use current frame index for animation
                    if sprite_data:
                        self.frame_index = self.frame_index % len(sprite_data)
                        sprite = sprite_data[self.frame_index]
                else:
                    sprite = sprite_data
        
        # Draw sprite centered on footprint using self.rect.center
        if sprite:
            sprite_w, sprite_h = sprite.get_size()
            sprite_w = int(sprite_w * self.sprite_scale)
            sprite_h = int(sprite_h * self.sprite_scale)
            scaled_sprite = pygame.transform.scale(sprite, (sprite_w, sprite_h))
            
            # Center sprite using rect.center
            draw_x = self.rect.centerx - sprite_w // 2
            draw_y = self.rect.centery - sprite_h // 2
            surface.blit(scaled_sprite, (draw_x, draw_y))
        
        # Draw construction overlay if constructing
        if self.state == BuildState.CONSTRUCTING:
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay.fill((100, 100, 100, 100))  # Semi-transparent grey overlay
            surface.blit(overlay, self.rect.topleft)
            
            # Build progress bar (at bottom of footprint)
            pct = self.progress / self.BUILD_TIME if self.BUILD_TIME > 0 else 1.0
            bar_height = 4
            bar_y = self.rect.bottom - bar_height - 2
            bar_width = self.rect.width - 4
            bar_x = self.rect.left + 2
            pygame.draw.rect(surface, (200, 220, 80), (bar_x, bar_y, int(bar_width * pct), bar_height))
        
        # HP bar (if damaged)
        if self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 1.0
            hp_color = (0, 255, 0) if hp_pct > 0.6 else (255, 255, 0) if hp_pct > 0.3 else (255, 0, 0)
            bar_height = 4
            bar_y = self.rect.top + 2
            bar_width = self.rect.width - 4
            bar_x = self.rect.left + 2
            pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            hp_bar_width = int(bar_width * hp_pct)
            if hp_bar_width > 0:
                pygame.draw.rect(surface, hp_color, (bar_x, bar_y, hp_bar_width, bar_height))
