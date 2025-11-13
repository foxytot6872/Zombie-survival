"""
Resource nodes for external harvesting.
"""
import pygame
import json
import random
import os
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass

@dataclass
class NodeConfig:
    """Node configuration from JSON"""
    resource: str  # "wood", "iron", "food"
    yield_total: int
    gather_per_tick: int
    tick_sec: float

class Node(pygame.sprite.Sprite):
    """Base class for resource nodes"""
    TYPE_ID: str = "node"
    RESOURCE: str = "wood"
    YIELD_TOTAL: int = 100
    GATHER_PER_TICK: int = 5
    TICK_SEC: float = 0.6
    RADIUS_PX: int = 20
    
    def __init__(self, pos: Tuple[float, float], config: Optional[NodeConfig] = None):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.remaining = config.yield_total if config else self.YIELD_TOTAL
        self.gather_per_tick = config.gather_per_tick if config else self.GATHER_PER_TICK
        self.tick_sec = config.tick_sec if config else self.TICK_SEC
        self.resource = config.resource if config else self.RESOURCE
        self.radius_px = self.RADIUS_PX
        
        # Rendering
        self.image = pygame.Surface((self.radius_px * 2, self.radius_px * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
        # Update image
        self._update_image()
    
    def _update_image(self):
        """Update node visual based on resource type and remaining"""
        self.image.fill((0, 0, 0, 0))
        
        # Color based on resource type
        if self.resource == "wood":
            color = (100, 150, 50)  # Green-brown for trees
        elif self.resource == "iron":
            color = (120, 120, 120)  # Grey for scrap
        else:
            color = (150, 100, 50)  # Brown for food
        
        # Draw circle
        pygame.draw.circle(self.image, color, (self.radius_px, self.radius_px), self.radius_px)
        pygame.draw.circle(self.image, (200, 200, 200), (self.radius_px, self.radius_px), self.radius_px, 2)
        
        # Draw depletion indicator (darker as it depletes)
        depletion_pct = self.remaining / (self.YIELD_TOTAL if hasattr(self, '_initial_yield') else self.remaining + 1)
        if depletion_pct < 1.0:
            dark_color = tuple(int(c * 0.5) for c in color)
            pygame.draw.circle(self.image, dark_color, (self.radius_px, self.radius_px), 
                             int(self.radius_px * depletion_pct))
    
    def gather_tick(self) -> int:
        """
        Perform one gather tick.
        Returns:
            Amount actually gathered (may be less if nearly depleted)
        """
        if self.is_depleted():
            return 0
        
        gathered = min(self.gather_per_tick, self.remaining)
        self.remaining -= gathered
        self._update_image()
        return gathered
    
    def is_depleted(self) -> bool:
        """Check if node is depleted"""
        return self.remaining <= 0
    
    def draw(self, surface: pygame.Surface):
        """Draw node on surface"""
        surface.blit(self.image, self.rect)
        
        # Draw resource amount label (optional, for debugging)
        # font = pygame.font.Font(None, 16)
        # text = font.render(str(self.remaining), True, (255, 255, 255))
        # text_rect = text.get_rect(center=(self.pos.x, self.pos.y - 20))
        # surface.blit(text, text_rect)

_TREE_TEXTURES: Optional[List[pygame.Surface]] = None
_TREE_TEXTURE_PATH = os.path.join('asset', 'Tree_node.png')
_TREE_TILE_SIZE = 32
_TREE_SCALE = 1.25


def _load_tree_textures() -> List[pygame.Surface]:
    """Load and slice the tree node sprite sheet into individual variants."""
    global _TREE_TEXTURES
    if _TREE_TEXTURES is not None:
        return _TREE_TEXTURES

    try:
        sheet = pygame.image.load(_TREE_TEXTURE_PATH).convert_alpha()
    except pygame.error:
        _TREE_TEXTURES = []
        return _TREE_TEXTURES

    width, height = sheet.get_size()
    tile_w = tile_h = _TREE_TILE_SIZE
    textures: List[pygame.Surface] = []

    for top in range(0, height, tile_h):
        for left in range(0, width, tile_w):
            if left + tile_w > width or top + tile_h > height:
                continue
            tile_surface = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
            tile_surface.blit(sheet, (0, 0), pygame.Rect(left, top, tile_w, tile_h))
            textures.append(tile_surface)

    _TREE_TEXTURES = textures
    return _TREE_TEXTURES


class TreePatch(Node):
    """Tree patch node - yields wood"""
    TYPE_ID = "tree_patch"
    RESOURCE = "wood"
    YIELD_TOTAL = 120
    GATHER_PER_TICK = 6
    TICK_SEC = 0.6
    RADIUS_PX = int(_TREE_TILE_SIZE * _TREE_SCALE / 2)
    
    def __init__(self, pos: Tuple[float, float], config: Optional[NodeConfig] = None):
        if config is None:
            # Load from config file
            config = self._load_config()
        self._tree_texture = self._pick_tree_texture()
        self._initial_yield = config.yield_total
        super().__init__(pos, config)
        # Ensure rect uses the full sprite dimensions
        self.rect = self.image.get_rect(center=self.pos)
    
    @classmethod
    def _load_config(cls) -> NodeConfig:
        """Load config from nodes.json"""
        try:
            with open('data/config/nodes.json', 'r') as f:
                data = json.load(f)
                node_data = data.get("tree_patch", {})
                return NodeConfig(
                    resource=node_data.get("resource", "wood"),
                    yield_total=node_data.get("yield_total", 120),
                    gather_per_tick=node_data.get("gather_per_tick", 6),
                    tick_sec=node_data.get("tick_sec", 0.6)
                )
        except:
            return NodeConfig("wood", 120, 6, 0.6)
    
    @staticmethod
    def _pick_tree_texture() -> Optional[pygame.Surface]:
        """Select a random tree texture variant."""
        textures = _load_tree_textures()
        if not textures:
            return None
        texture = random.choice(textures)
        if _TREE_SCALE != 1:
            width, height = texture.get_size()
            scaled_size = (int(width * _TREE_SCALE), int(height * _TREE_SCALE))
            return pygame.transform.smoothscale(texture, scaled_size)
        return texture

    def _update_image(self):
        """Update tree patch visual"""
        self.image.fill((0, 0, 0, 0))
        base_texture = self._tree_texture
        if base_texture:
            tex_rect = base_texture.get_rect()
            tex_rect.center = (self.radius_px, self.radius_px)
            self.image.blit(base_texture, tex_rect)
            # Darken sprite as resources deplete
            if hasattr(self, '_initial_yield') and self._initial_yield > 0:
                depletion_pct = max(0.0, min(1.0, self.remaining / self._initial_yield))
                if depletion_pct < 1.0:
                    shade = pygame.Surface(base_texture.get_size(), pygame.SRCALPHA)
                    darkness = int(160 * (1 - depletion_pct))
                    shade.fill((0, 0, 0, darkness))
                    self.image.blit(shade, tex_rect)
        else:
            # Fallback to simple circle if texture not available
            center = (self.radius_px, self.radius_px)
            pygame.draw.circle(self.image, (80, 120, 60), center, self.radius_px)
            pygame.draw.circle(self.image, (200, 200, 200), center, self.radius_px, 2)

class ScrapPile(Node):
    """Scrap pile node - yields iron"""
    TYPE_ID = "scrap_pile"
    RESOURCE = "iron"
    YIELD_TOTAL = 100
    GATHER_PER_TICK = 5
    TICK_SEC = 0.7
    
    def __init__(self, pos: Tuple[float, float], config: Optional[NodeConfig] = None):
        if config is None:
            config = self._load_config()
        super().__init__(pos, config)
        self._initial_yield = self.remaining
    
    @classmethod
    def _load_config(cls) -> NodeConfig:
        """Load config from nodes.json"""
        try:
            with open('data/config/nodes.json', 'r') as f:
                data = json.load(f)
                node_data = data.get("scrap_pile", {})
                return NodeConfig(
                    resource=node_data.get("resource", "iron"),
                    yield_total=node_data.get("yield_total", 100),
                    gather_per_tick=node_data.get("gather_per_tick", 5),
                    tick_sec=node_data.get("tick_sec", 0.7)
                )
        except:
            return NodeConfig("iron", 100, 5, 0.7)
    
    def _update_image(self):
        """Update scrap pile visual"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw scrap pile (grey metallic chunks)
        center = (self.radius_px, self.radius_px)
        depletion_pct = self.remaining / self._initial_yield if hasattr(self, '_initial_yield') else 1.0
        grey = (int(120 * depletion_pct), int(120 * depletion_pct), int(120 * depletion_pct))
        pygame.draw.circle(self.image, grey, center, self.radius_px)
        # Draw metallic highlights
        pygame.draw.circle(self.image, (180, 180, 180), 
                          (self.radius_px - 3, self.radius_px - 3), 4)
        pygame.draw.circle(self.image, (200, 200, 200), center, self.radius_px, 2)

def spawn_daily_nodes(world, cfg_nodes: Dict, upper_zone_rect: pygame.Rect, grid, min_dist_from_wall_px: int = 96):
    """
    Spawn daily resource nodes in the upper zone.
    Args:
        world: World object with nodes group
        cfg_nodes: Node configuration dict
        upper_zone_rect: Rect defining upper zone area
        grid: Grid object for collision checking
        min_dist_from_wall_px: Minimum distance from walls in pixels
    Returns:
        List of spawned nodes
    """
    nodes = []
    # Get existing nodes from group as a list
    existing_nodes = []
    if hasattr(world, 'nodes'):
        existing_nodes = list(world.nodes)
    
    # Get daily spawn config
    daily_spawn = cfg_nodes.get("daily_spawn", {"trees": 4, "scrap": 3, "min_dist_from_wall_px": 96})
    num_trees = daily_spawn.get("trees", 4)
    num_scrap = daily_spawn.get("scrap", 3)
    min_dist = daily_spawn.get("min_dist_from_wall_px", min_dist_from_wall_px)
    
    # Convert min_dist to grid tiles
    TILE = 32
    min_dist_tiles = int(min_dist / TILE)
    
    # Load node configs
    tree_config = None
    scrap_config = None
    try:
        tree_data = cfg_nodes.get("tree_patch", {})
        tree_config = NodeConfig(
            resource=tree_data.get("resource", "wood"),
            yield_total=tree_data.get("yield_total", 120),
            gather_per_tick=tree_data.get("gather_per_tick", 6),
            tick_sec=tree_data.get("tick_sec", 0.6)
        )
        scrap_data = cfg_nodes.get("scrap_pile", {})
        scrap_config = NodeConfig(
            resource=scrap_data.get("resource", "iron"),
            yield_total=scrap_data.get("yield_total", 100),
            gather_per_tick=scrap_data.get("gather_per_tick", 5),
            tick_sec=scrap_data.get("tick_sec", 0.7)
        )
    except:
        pass
    
    # Spawn trees
    for _ in range(num_trees):
        # Combine existing nodes and newly spawned nodes for collision check
        all_existing_nodes = existing_nodes + nodes
        node = _spawn_node_in_zone(TreePatch, upper_zone_rect, grid, min_dist_tiles, 
                                   tree_config, all_existing_nodes)
        if node:
            nodes.append(node)
    
    # Spawn scrap piles
    for _ in range(num_scrap):
        # Combine existing nodes and newly spawned nodes for collision check
        all_existing_nodes = existing_nodes + nodes
        node = _spawn_node_in_zone(ScrapPile, upper_zone_rect, grid, min_dist_tiles,
                                   scrap_config, all_existing_nodes)
        if node:
            nodes.append(node)
    
    return nodes

def _spawn_node_in_zone(node_class, zone_rect: pygame.Rect, grid, min_dist_tiles: int,
                        config: Optional[NodeConfig], existing_nodes: list,
                        max_attempts: int = 50) -> Optional[Node]:
    """
    Try to spawn a node in the zone without overlapping.
    Args:
        node_class: Node class to instantiate
        zone_rect: Zone rectangle
        grid: Grid for collision checking
        min_dist_tiles: Minimum distance from walls in tiles
        config: Node configuration
        existing_nodes: List of existing nodes to avoid
        max_attempts: Maximum spawn attempts
    Returns:
        Node instance or None if failed
    """
    TILE = 32
    node_radius_tiles = 1  # Nodes are roughly 1 tile radius
    
    for attempt in range(max_attempts):
        # Random position in upper zone
        x = random.randint(zone_rect.left + min_dist_tiles * TILE,
                          zone_rect.right - min_dist_tiles * TILE)
        y = random.randint(zone_rect.top + min_dist_tiles * TILE,
                          zone_rect.bottom - min_dist_tiles * TILE)
        
        pos = (x, y)
        grid_x = x // TILE
        grid_y = y // TILE
        
        # Check if position is safe (not blocked, not too close to walls)
        safe = True
        for check_x in range(grid_x - node_radius_tiles, grid_x + node_radius_tiles + 1):
            for check_y in range(grid_y - node_radius_tiles, grid_y + node_radius_tiles + 1):
                if grid.is_blocked(check_x, check_y):
                    safe = False
                    break
            if not safe:
                break
        
        if not safe:
            continue
        
        # Check distance from existing nodes (avoid overlapping)
        too_close = False
        min_node_dist = node_radius_tiles * 2 * TILE  # At least 2 tile radii apart
        for existing in existing_nodes:
            dist = (pygame.Vector2(pos) - existing.pos).length()
            if dist < min_node_dist:
                too_close = True
                break
        
        if too_close:
            continue
        
        # Spawn node
        node = node_class(pos, config)
        return node
    
    # Failed to find valid position
    return None

