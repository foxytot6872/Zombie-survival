"""Base wall class with shared logic."""
from world.building import Building, Cost, BuildState, TILE
import pygame

# Module-level variables to store wall tiles (set from main.py)
# Level 1: default (wood walls)
wall_tiles_dict = {}
# Level 2: upgraded/iron walls
wall_tiles_lv2_dict = {}

def set_wall_tiles(tiles_lv1, tiles_lv2=None):
    """
    Set wall tile dictionaries from main.py.
    tiles_lv1: dict of sprites for level 1 walls
    tiles_lv2: optional dict of sprites for level 2 walls (used by iron walls)
    """
    global wall_tiles_dict, wall_tiles_lv2_dict
    wall_tiles_dict = tiles_lv1 or {}
    if tiles_lv2 is not None:
        wall_tiles_lv2_dict = tiles_lv2 or {}

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

    def has_wall(self, dx, dy):
        """Check if there's a wall at offset (dx, dy) from this wall's position."""
        if not self.world:
            return False
        gx = self.grid_x + dx
        gy = self.grid_y + dy
        return self.world.is_wall_at(gx, gy)

    def get_wall_neighbor(self, dx, dy):
        """Get the wall building object at offset (dx, dy), or None if not a wall."""
        if not self.world:
            return None
        gx = self.grid_x + dx
        gy = self.grid_y + dy
        building = self.world.building_at(gx, gy)
        if building and hasattr(building, 'TYPE_ID') and building.TYPE_ID.startswith("wall"):
            return building
        return None

    def is_tile_type(self, tile_key):
        """Check if this wall's current sprite matches a specific tile type."""
        if not self.sprite or not wall_tiles_dict:
            return False
        target_tile = wall_tiles_dict.get(tile_key)
        if not target_tile:
            return False
        # Compare sprite surfaces by checking if they're the same object or have same size/contents
        # For simplicity, we compare by checking if sprite is the same surface object
        return self.sprite is target_tile

    def update_sprite(self):
        """Update wall sprite based on neighboring walls (auto-tiling)."""
        if not self.world:
            return
        
        # Check neighbors (N, S, E, W)
        N = self.has_wall(0, -1)
        S = self.has_wall(0, 1)
        E = self.has_wall(1, 0)
        W = self.has_wall(-1, 0)
        
        # Choose correct tile set based on wall type (wood vs iron / level 2)
        # Default: level 1 tiles; iron/level-2 walls use lv2 tiles if provided
        if hasattr(self, "_is_iron") and self._is_iron and wall_tiles_lv2_dict:
            wall_tiles = wall_tiles_lv2_dict
        else:
            wall_tiles = wall_tiles_dict if wall_tiles_dict else {}
        
        # Determine sprite based on neighbors
        if not wall_tiles:
            # Fallback to old method if tiles not loaded
            self.refresh_wall_variant_fallback()
            return
        
        sprite = None
        
        # 1 — 4-way
        if N and S and W and E:
            sprite = wall_tiles.get("4way")
        
        # 2 — T-junctions
        if sprite is None:
            # T-up: has up, left, right, but no down
            if N and W and E and not S:
                sprite = wall_tiles.get("t_down")
            # T-down: has down, left, right, but no up
            elif S and W and E and not N:
                sprite = wall_tiles.get("t_up")
            # T-right: has up, down, right, but no left
            elif N and S and E and not W:
                sprite = wall_tiles.get("t_left")
            # T-left: has up, down, left, but no right
            elif N and S and W and not E:
                sprite = wall_tiles.get("t_right")
        
        # 3 — Corners (MUST COME BEFORE VERTICAL RULE)
        if sprite is None:
            # Corner bottom-left
            if S and W and not N and not E:
                sprite = wall_tiles.get("corner_tr")
            # Corner bottom-right
            elif S and E and not N and not W:
                sprite = wall_tiles.get("corner_tl")
            # Corner top-left
            elif N and W and not S and not E:
                sprite = wall_tiles.get("corner_br")
            # Corner top-right
            elif N and E and not S and not W:
                sprite = wall_tiles.get("corner_bl")
        
        # 4 — NEW VERTICAL RULE (after corners)
        if sprite is None and (N or S):
            if E:
                sprite = wall_tiles.get("vertical_r")
            elif W:
                sprite = wall_tiles.get("vertical_l")
            else:
                sprite = wall_tiles.get("vertical_l")
        
        # 5 — HORIZONTAL
        if sprite is None and (W or E):
            sprite = wall_tiles.get("horizontal")
        
        # Fallback if nothing matched
        if sprite is None:
            sprite = wall_tiles.get("horizontal")
        
        # Set sprite (fallback to old method if sprite not found)
        if sprite:
            self.sprite = sprite
            self.rect = self.sprite.get_rect(center=self.pos) if self.sprite else None
        else:
            self.refresh_wall_variant_fallback()

    def refresh_wall_variant_fallback(self):
        """Fallback method using old colored rectangle approach."""
        fill, border = self._get_fill_color()
        surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        surface.fill(fill)
        pygame.draw.rect(surface, border, (0, 0, TILE, TILE), 2)
        self.sprite = surface
        self.rect = self.sprite.get_rect(center=self.pos) if self.sprite else None

    def refresh_wall_variant(self, world=None):
        """Refresh wall variant - calls update_sprite for auto-tiling."""
        if world is not None:
            self.world = world
        self.update_sprite()

    def on_place(self, world):
        self.refresh_wall_variant(world)
        # Update all neighbors (this wall already updated by refresh_wall_variant)
        if world:
            gx, gy = self.grid_x, self.grid_y
            for nx, ny in ((gx+1, gy), (gx-1, gy), (gx, gy+1), (gx, gy-1)):
                neighbor = world.building_at(nx, ny)
                if neighbor and hasattr(neighbor, "update_sprite"):
                    neighbor.update_sprite()

    def on_complete(self, world=None):
        super().on_complete(world)
        self.refresh_wall_variant(world)
        # Update all neighbors (this wall already updated by refresh_wall_variant)
        if world:
            gx, gy = self.grid_x, self.grid_y
            for nx, ny in ((gx+1, gy), (gx-1, gy), (gx, gy+1), (gx, gy-1)):
                neighbor = world.building_at(nx, ny)
                if neighbor and hasattr(neighbor, "update_sprite"):
                    neighbor.update_sprite()

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
