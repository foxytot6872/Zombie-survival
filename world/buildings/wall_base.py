"""Base wall class with shared logic."""
from world.building import Building, Cost, BuildState, TILE
import pygame

class WallBase(Building):
    """Base class for walls - shared functionality."""
    FOOTPRINT = (1, 1)
    PASSABLE = False  # Walls block pathfinding

    def __init__(self, grid_pos, tier=1, uid=None):
        super().__init__(grid_pos, tier=tier, uid=uid)
        self.world = None
        self.sprite = None
        w, h = self.FOOTPRINT
        self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)

    def _get_fill_color(self):
        if hasattr(self, '_is_iron') and self._is_iron:
            return (120, 120, 140), (180, 180, 200)
        return (100, 80, 60), (150, 130, 100)

    def refresh_wall_variant(self, world=None):
        """Reset the wall sprite to the default solid piece."""
        if world is not None:
            self.world = world

        fill, border = self._get_fill_color()
        surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        surface.fill(fill)
        pygame.draw.rect(surface, border, (0, 0, TILE, TILE), 2)
        self.sprite = surface
        self.rect = self.sprite.get_rect(center=self.pos)

    def on_place(self, world):
        self.refresh_wall_variant(world)

    def on_complete(self, world=None):
        super().on_complete(world)
        self.refresh_wall_variant(world)

    def on_destroy(self):
        gx, gy = self.grid_x, self.grid_y
        world = getattr(self, 'world', None)
        super().on_destroy()
        if world:
            world.autotile_wall_and_neighbors(gx, gy)

    def on_upgrade(self):
        super().on_upgrade()
        self.refresh_wall_variant(self.world)

    def carry_over_hp(self, new_max_hp: int) -> int:
        if self.max_hp > 0:
            ratio = max(0.0, min(1.0, self.hp / self.max_hp))
        else:
            ratio = 1.0
        return int(ratio * new_max_hp)

    def draw(self, surface: pygame.Surface):
        w, h = self.FOOTPRINT
        if self.image is None or self.image.get_size() != (w * TILE, h * TILE):
            self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        if self.sprite is None:
            self.refresh_wall_variant(self.world)

        if self.state != BuildState.DESTROYED:
            if self.sprite:
                self.image.blit(self.sprite, (0, 0))
        else:
            pygame.draw.rect(self.image, (80, 30, 30), (0, 0, w * TILE, h * TILE))

        if self.state == BuildState.CONSTRUCTING:
            overlay = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.image.blit(overlay, (0, 0))
            pct = self.progress / self.BUILD_TIME if self.BUILD_TIME > 0 else 1.0
            bar_height = 4
            bar_y = h * TILE - bar_height - 2
            bar_width = w * TILE - 4
            pygame.draw.rect(self.image, (200, 220, 80), (2, bar_y, int(bar_width * pct), bar_height))

        if self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 1.0
            hp_color = (0, 255, 0) if hp_pct > 0.6 else (255, 255, 0) if hp_pct > 0.3 else (255, 0, 0)
            bar_height = 4
            bar_y = h * TILE - bar_height - 2
            bar_width = w * TILE - 4
            pygame.draw.rect(self.image, (0, 0, 0), (2, bar_y, bar_width, bar_height))
            hp_bar_width = int(bar_width * hp_pct)
            if hp_bar_width > 0:
                pygame.draw.rect(self.image, hp_color, (2, bar_y, hp_bar_width, bar_height))

        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)
