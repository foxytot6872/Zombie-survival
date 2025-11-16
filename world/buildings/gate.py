"""Gate building."""
from world.building import Building, Cost, BuildState, TILE
import pygame
import os

class Gate(Building):
    """Gate - passable defensive structure (enemies can path through)."""
    TYPE_ID = "gate"
    BASE_HP = 300
    BUILD_TIME = 2.0
    COST = Cost(wood=30, iron=10)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSABLE = True  # Gates are passable for pathfinding
    
    def __init__(self, grid_pos, tier=1, uid=None):
        super().__init__(grid_pos, tier, uid)
        # Gates can be passable but still block placement
        self.passable = True
        # Lazy-load sprite assets once per class
        if not hasattr(Gate, "_sprites"):
            Gate._sprites = self._load_sprites()
    
    def draw(self, surface: pygame.Surface):
        """Draw gate with distinctive appearance"""
        w, h = self.FOOTPRINT
        # Update image size if needed
        if self.image.get_size() != (w * TILE, h * TILE):
            self.image = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        
        # Clear image
        self.image.fill((0, 0, 0, 0))

        drawn = False
        # Prefer using sprite assets if available
        sprites = getattr(Gate, "_sprites", {})
        level_key = "lv2" if self.tier >= 2 else "lv1"
        level_sprites = sprites.get(level_key, {})
        if level_sprites:
            # Determine neighbor walls to pick orientation
            has_up = hasattr(self, "world") and self.world and self.world.is_wall_at(self.grid_x, self.grid_y - 1)
            has_down = hasattr(self, "world") and self.world and self.world.is_wall_at(self.grid_x, self.grid_y + 1)
            has_left = hasattr(self, "world") and self.world and self.world.is_wall_at(self.grid_x - 1, self.grid_y)
            has_right = hasattr(self, "world") and self.world and self.world.is_wall_at(self.grid_x + 1, self.grid_y)

            img_to_blit = None
            # Horizontal gate if walls on left & right (typical base entrance)
            if has_left and has_right:
                img_to_blit = level_sprites.get("horizontal")
            # Vertical corridor case: pick a vertical variant
            elif has_up or has_down:
                if has_left and not has_right:
                    img_to_blit = level_sprites.get("vertical_r") or level_sprites.get("vertical_l")
                elif has_right and not has_left:
                    img_to_blit = level_sprites.get("vertical_l") or level_sprites.get("vertical_r")
                else:
                    # Default to left variant if ambiguous
                    img_to_blit = level_sprites.get("vertical_l") or level_sprites.get("vertical_r")
            else:
                # No obvious neighbors; default to horizontal
                img_to_blit = level_sprites.get("horizontal")

            if img_to_blit:
                # Scale if needed
                if img_to_blit.get_size() != (w * TILE, h * TILE):
                    img_to_blit = pygame.transform.scale(img_to_blit, (w * TILE, h * TILE))
                self.image.blit(img_to_blit, (0, 0))
                drawn = True

        if not drawn:
            # Fallback: simple vector drawing
            if self.state == BuildState.DESTROYED:
                color = (80, 30, 30)  # Dark red when destroyed
            else:
                color = (120, 100, 80)  # Brown/beige for gate
            pygame.draw.rect(self.image, color, (0, 0, w * TILE, h * TILE))
            pygame.draw.rect(self.image, (150, 130, 100), (0, 0, w * TILE, h * TILE), 2)
            center_x = w * TILE // 2
            pygame.draw.line(self.image, (100, 80, 60), (center_x, 4), (center_x, h * TILE - 4), 2)
        
        # HP bar if damaged
        if self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 1.0
            hp_color = (0, 255, 0) if hp_pct > 0.6 else (255, 255, 0) if hp_pct > 0.3 else (255, 0, 0)
            bar_height = 4
            bar_y = h * TILE - bar_height - 2
            bar_width = w * TILE - 4
            # Background bar
            pygame.draw.rect(self.image, (0, 0, 0), (2, bar_y, bar_width, bar_height))
            # HP bar
            hp_bar_width = int(bar_width * hp_pct)
            if hp_bar_width > 0:
                pygame.draw.rect(self.image, hp_color, (2, bar_y, hp_bar_width, bar_height))
        
        # Update rect position
        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)

    def _load_sprites(self):
        """Load gate sprites for lv1/lv2. Returns dict like {'lv1': {...}, 'lv2': {...}}"""
        def load_path(path: str):
            # try exact path, then try to fix common typos (e.g., missing dot before png)
            if os.path.exists(path):
                try:
                    return pygame.image.load(path).convert_alpha()
                except Exception:
                    pass
            # attempt to fix missing dot before extension
            if path.endswith("lv1png"):
                alt = path.replace("lv1png", "lv1.png")
                if os.path.exists(alt):
                    try:
                        return pygame.image.load(alt).convert_alpha()
                    except Exception:
                        pass
            if path.endswith("lv2png"):
                alt = path.replace("lv2png", "lv2.png")
                if os.path.exists(alt):
                    try:
                        return pygame.image.load(alt).convert_alpha()
                    except Exception:
                        pass
            return None

        base = "asset/Wall"
        defs = {
            "lv1": {
                "horizontal": "Gate-horizontal_lv1.png",
                "vertical_l": "Gate-Vertical-l_lv1png",
                "vertical_r": "Gate-Vertical-r_lv1png",
            },
            "lv2": {
                "horizontal": "Gate-horizontal_lv2.png",
                "vertical_l": "Gate-Vertical-l_lv2png",
                "vertical_r": "Gate-Vertical-r_lv2.png" if os.path.exists(os.path.join(base, "Gate-Vertical-r_lv2.png")) else "Gate-Vertical-r_lv2png",
            },
        }
        out = {}
        for lvl, mapping in defs.items():
            out[lvl] = {}
            for key, rel in mapping.items():
                img = load_path(os.path.join(base, rel))
                if img:
                    out[lvl][key] = img
        return out

