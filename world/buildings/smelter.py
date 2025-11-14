"""Smelter building with dynamic sprite upgrades."""
from __future__ import annotations

import os
import pygame

from world.building import Building, Cost, Production

SPRITE_CACHE = {}


def load_smelter_sprite(path: str) -> pygame.Surface:
    """Load sprite surface with caching and placeholder fallback."""
    if path in SPRITE_CACHE:
        return SPRITE_CACHE[path]

    if os.path.exists(path):
        try:
            SPRITE_CACHE[path] = pygame.image.load(path).convert_alpha()
            return SPRITE_CACHE[path]
        except Exception:
            pass

    # Placeholder if missing
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    surface.fill((90, 70, 70))
    pygame.draw.rect(surface, (30, 20, 20), surface.get_rect(), 2)
    SPRITE_CACHE[path] = surface
    return surface


def prepare_frames(surface: pygame.Surface) -> list[pygame.Surface] | pygame.Surface:
    """
    Split horizontal sprite sheet into frames if width indicates multiple frames.
    Otherwise return the surface itself.
    """
    height = surface.get_height()
    width = surface.get_width()

    if height == 0:
        return surface

    if width > height and width % height == 0:
        frames = []
        frame_width = height  # assume square frames laid horizontally
        for x in range(0, width, frame_width):
            frame = surface.subsurface((x, 0, frame_width, height)).copy()
            frames.append(frame)
        return frames

    return surface


class Smelter(Building):
    """Smelter - produces iron and visually upgrades via research."""

    TYPE_ID = "smelter"
    BASE_HP = 140
    BUILD_TIME = 4.5
    COST = Cost(wood=40, iron=40)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSIVE = Production(iron_per_min=120.0)  # 10 iron per 5 seconds = 120 per minute

    LEVEL_SPRITES = {
        1: ("asset/smelter/Bricks_01.png", "asset/smelter/Bricks_01-Sheet.png"),
        2: ("asset/smelter/Bricks_02.png", "asset/smelter/Bricks_02-Sheet.png"),
        3: ("asset/smelter/Bricks_03.png", "asset/smelter/Bricks_03-Sheet.png"),
    }

    def __init__(self, grid_pos, tier=1, uid=None):
        super().__init__(grid_pos, tier=tier, uid=uid)
        self.level_sprites = self._load_level_sprites()
        self.update_sprite()

    def _load_level_sprites(self):
        sprites = {}
        for level, paths in self.LEVEL_SPRITES.items():
            surface = None
            for path in paths:
                surface = load_smelter_sprite(path)
                if surface is not None:
                    break
            sprites[level] = prepare_frames(surface)
        return sprites