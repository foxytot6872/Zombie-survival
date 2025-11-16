"""
Reusable 9-slice panel renderer using 32x32 tiles.
Assets expected in asset/hud:
  - Panel-center.png
  - Panel-border-top.png
  - Panel-border-bottom.png
  - Panel-border-left.png
  - Panel-border-right.png
  - Panel-corner-tl.png
  - Panel-corner-tr.png
  - Panel-corner-bl.png
  - Panel-corner-br.png
"""
import os
import pygame


class NineSlicePanel:
    """Draws a 9-slice panel of arbitrary size using 32x32 tile sprites."""

    TILE = 32

    def __init__(self, base_path: str = "asset/hud"):
        self.tiles = {}
        self._load_tiles(base_path)

    def _load_tiles(self, base_path: str):
        mapping = {
            "center": "Panel-center.png",
            "border_top": "Panel-border-top.png",
            "border_bottom": "Panel-border-bottom.png",
            "border_left": "Panel-border-left.png",
            "border_right": "Panel-border-right.png",
            "corner_tl": "Panel-corner-tl.png",
            "corner_tr": "Panel-corner-tr.png",
            "corner_bl": "Panel-corner-bl.png",
            "corner_br": "Panel-corner-br.png",
        }
        for key, filename in mapping.items():
            path = os.path.join(base_path, filename)
            if os.path.exists(path):
                try:
                    self.tiles[key] = pygame.image.load(path).convert_alpha()
                except Exception as e:
                    print(f"Warning: could not load {path}: {e}")

    def is_ready(self) -> bool:
        """Returns True if all required tiles are available."""
        required = [
            "center",
            "border_top",
            "border_bottom",
            "border_left",
            "border_right",
            "corner_tl",
            "corner_tr",
            "corner_bl",
            "corner_br",
        ]
        return all(k in self.tiles for k in required)

    def draw(self, surface: pygame.Surface, rect: pygame.Rect):
        """Draw the panel into the given rect."""
        if not self.is_ready():
            # Fallback simple box if tiles missing
            bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            bg.fill((40, 40, 40, 240))
            surface.blit(bg, rect)
            pygame.draw.rect(surface, (200, 200, 200), rect, 3)
            return

        t = self.TILE
        # Corners
        surface.blit(self.tiles["corner_tl"], (rect.x, rect.y))
        surface.blit(self.tiles["corner_tr"], (rect.right - t, rect.y))
        surface.blit(self.tiles["corner_bl"], (rect.x, rect.bottom - t))
        surface.blit(self.tiles["corner_br"], (rect.right - t, rect.bottom - t))

        # Top/Bottom borders
        x_start = rect.x + t
        x_end = rect.right - t
        y_top = rect.y
        y_bottom = rect.bottom - t
        x = x_start
        while x < x_end:
            surface.blit(self.tiles["border_top"], (x, y_top))
            surface.blit(self.tiles["border_bottom"], (x, y_bottom))
            x += t

        # Left/Right borders
        y_start = rect.y + t
        y_end = rect.bottom - t
        x_left = rect.x
        x_right = rect.right - t
        y = y_start
        while y < y_end:
            surface.blit(self.tiles["border_left"], (x_left, y))
            surface.blit(self.tiles["border_right"], (x_right, y))
            y += t

        # Center fill
        y = y_start
        while y < y_end:
            x = x_start
            while x < x_end:
                surface.blit(self.tiles["center"], (x, y))
                x += t
            y += t


