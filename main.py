import pygame
import json
import constants as c
from world.buildings import BallisticTurret, GatlingTurret, PiercerTurret, HQ, Wall, Gate, Housing, Farm, Sawmill, Smelter, WallWood, WallIron
from world.enemies import BasicZombie, RunnerZombie, BruteZombie, SpitterZombie, SwarmlingZombie
from world.spawner import Spawner
from world.projectile import Projectile
from world.debug import DebugSystem
from button import Button
from world.map import Grid
from world.resources import Resources
from world.building import BuildState, Building
# Core systems
from core.wave_manager import WaveManager
from core.game_state import GameState, GameStateManager
from core.save_system import SaveSystem
from core.sound import SoundSystem
# UI components
from ui.game_over import GameOverScreen
from ui.pause_menu import PauseMenu
from ui.building_panel import BuildingPanel
from ui.hud import HUD
# Nodes and survivors
from world.nodes import TreePatch, ScrapPile, spawn_daily_nodes
from world.survivor import Worker, Guard

# pygame setup
pygame.init()

FPS = 60
TILE = 32  # 32x32 pixel tiles

screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
pygame.display.set_caption("Zombie Defense")
clock = pygame.time.Clock()
running = True

# Calculate grid dimensions
GRID_WIDTH = c.SCREEN_WIDTH // TILE
GRID_HEIGHT = c.SCREEN_HEIGHT // TILE


def load_image_or_placeholder(path, size, fill_color=(100, 100, 100, 255), label="image"):
    """Load an image from disk or return a colored placeholder surface."""
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        placeholder = pygame.Surface(size, pygame.SRCALPHA)
        placeholder.fill(fill_color)
        print(f"Warning: {label} missing at {path}, using placeholder")
        return placeholder


###################
# Load images
###################
# Turret images
turret_sheet_lv1 = load_image_or_placeholder(
    'asset/Turret_lv1.png',
    (32 * c.ANIMATION_STEPS, 32),
    (150, 150, 150, 255),
    "Ballistic turret sprite sheet Lv1"
)
turret_sheet_lv2 = load_image_or_placeholder(
    'asset/Turret_lv2.png',
    (32 * c.ANIMATION_STEPS, 32),
    (160, 150, 150, 255),
    "Ballistic turret sprite sheet Lv2"
)
turret_sprite_sheets = [turret_sheet_lv1, turret_sheet_lv2]
turret_base_lv1 = load_image_or_placeholder(
    'asset/Base_lv1.png',
    (32, 32),
    (100, 100, 100, 255),
    "Ballistic turret base Lv1"
)
turret_base_lv2 = load_image_or_placeholder(
    'asset/Base_lv2.png',
    (32, 32),
    (110, 110, 110, 255),
    "Ballistic turret base Lv2"
)
turret_base_lv3 = load_image_or_placeholder(
    'asset/Base_lv3.png',
    (32, 32),
    (120, 120, 120, 255),
    "Ballistic turret base Lv3"
)
turret_base_images = [turret_base_lv1, turret_base_lv2, turret_base_lv3]

# Gatling turret images (static image, not a sprite sheet)
try:
    gatling_base = pygame.image.load('asset/Gatling_Base_lv1.png').convert_alpha()
    gatling_image = pygame.image.load('asset/Gatling_lv1.png').convert_alpha()
except:
    # Create placeholder images if files don't exist
    gatling_base = pygame.Surface((32, 32))
    gatling_base.fill((120, 100, 80))
    gatling_image = pygame.Surface((32, 32), pygame.SRCALPHA)
    gatling_image.fill((180, 160, 140))
    print("Warning: Gatling turret assets not found, using placeholder")

# Grass tile images
try:
    grass_tile_sheet = pygame.image.load('asset/Grass_tile.png').convert_alpha()
    grass_tile_width, grass_tile_height = grass_tile_sheet.get_size()
    
    # Extract 3 variants if the image contains multiple tiles
    # If image is 96x32 (3 tiles), extract each 32x32 tile
    # If image is 32x32 (single tile), use it and create variations
    grass_tiles = []
    if grass_tile_width >= 96 and grass_tile_height == 32:
        # Image contains 3 horizontal tiles
        for i in range(3):
            tile = grass_tile_sheet.subsurface((i * 32, 0, 32, 32))
            grass_tiles.append(tile)
    elif grass_tile_width == 32 and grass_tile_height >= 96:
        # Image contains 3 vertical tiles
        for i in range(3):
            tile = grass_tile_sheet.subsurface((0, i * 32, 32, 32))
            grass_tiles.append(tile)
    elif grass_tile_width == 32 and grass_tile_height == 32:
        # Single tile - use it and create 2 variations by slightly modifying brightness
        base_tile = grass_tile_sheet
        grass_tiles.append(base_tile)
        
        # Create variation 1: slightly darker
        variation1 = base_tile.copy()
        dark_overlay = pygame.Surface((32, 32), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 15))  # Subtle dark overlay
        variation1.blit(dark_overlay, (0, 0))
        grass_tiles.append(variation1)
        
        # Create variation 2: slightly brighter/lighter
        variation2 = base_tile.copy()
        light_overlay = pygame.Surface((32, 32), pygame.SRCALPHA)
        light_overlay.fill((10, 15, 10, 10))  # Subtle light green overlay
        variation2.blit(light_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        grass_tiles.append(variation2)
    else:
        # Unknown format - extract first 32x32 tile and create variations
        tile = grass_tile_sheet.subsurface((0, 0, 32, 32))
        grass_tiles.append(tile)
        grass_tiles.append(tile)  # Use same for now
        grass_tiles.append(tile)  # Use same for now
except Exception as e:
    # Create placeholder grass tiles if file doesn't exist
    print(f"Warning: Grass_tile.png not found or error loading: {e}, using placeholder")
    grass_tiles = []
    for i in range(3):
        tile = pygame.Surface((32, 32))
        # Create 3 slightly different shades of green
        shade = 30 + (i * 5)
        tile.fill((shade, 50 + (i * 3), shade))
        grass_tiles.append(tile)

###################
# Game state
###################
# Load startup config to get upper_fraction for grid
try:
    import os
    startup_cfg_path = os.path.join("data", "config", "startup.json")
    with open(startup_cfg_path, "r") as f:
        startup_cfg = json.load(f)
        upper_fraction = startup_cfg.get("upper_fraction", 0.6667)
except:
    upper_fraction = 0.6667  # Default: 2/3 of screen is upper zone

# Create grid and resources
grid = Grid(GRID_WIDTH, GRID_HEIGHT, c.SCREEN_WIDTH, c.SCREEN_HEIGHT, upper_fraction)
resources = Resources(wood=500, iron=300, food=200)  # Starting resources

# Building groups
building_group = pygame.sprite.Group()
turret_group = pygame.sprite.Group()

# Enemy groups
enemy_group = pygame.sprite.Group()

# Projectile groups
projectile_group = pygame.sprite.Group()

build_mode = False  # True when player wants to build
selected_building_type = None  # Building class to build
selected_building = None  # Currently selected building
pending_construction = None  # Building being constructed (can cancel)

gather_mode = False  # True when player wants to assign workers to nodes

# Enemy factory for spawner
enemy_factory = {
    "walker": BasicZombie,
    "runner": RunnerZombie,
    "brute": BruteZombie,
    "spitter": SpitterZombie,
    "swarmling": SwarmlingZombie
}

# Enemy spawner (updated to support wave-based spawning)
zombie_spawner = Spawner(enemy_factory, spawn_interval=1.0)
spawn_horde_button_pressed = False

# Debug system
debug_system = DebugSystem()

# Load wave configuration
try:
    with open('data/config/waves.json', 'r') as f:
        waves_config = json.load(f)
except FileNotFoundError:
    # Default wave config if file doesn't exist
    waves_config = {
        "difficulty": {"easy": 0.85, "normal": 1.0, "hard": 1.5},
        "nights": [{"mix": {"walker": 12}}],
        "increment": {"per_night_mult": 1.12},
        "spawn": {"interval_sec": 1.0, "batch_size": 2},
        "day_duration": 30.0,
        "summary_duration": 5.0,
        "win_nights": 10
    }

# World object for building updates
class World:
    def __init__(self, resources, grid, screen_height=c.SCREEN_HEIGHT, enemy_group=None, projectile_group=None, building_group=None, sound_system=None, wave_manager=None, pathfinding=None, node_group=None, survivor_group=None):
        self.resources = resources
        self.grid = grid
        self.screen_height = screen_height
        self.enemy_group = enemy_group
        self.projectile_group = projectile_group
        self.building_group = building_group
        self.sound_system = sound_system
        self.wave_manager = wave_manager
        self.pathfinding = pathfinding
        self.nodes = node_group if node_group else pygame.sprite.Group()
        self.survivor_group = survivor_group if survivor_group else pygame.sprite.Group()
    
    def enemy_count(self):
        """Get current enemy count"""
        return len(self.enemy_group) if self.enemy_group else 0
    
    def deposit(self, resource: str, amount: int):
        """Deposit resources at HQ (stockpile)"""
        if resource == "wood":
            self.resources.wood += int(amount)
        elif resource == "iron":
            self.resources.iron += int(amount)
        elif resource == "food":
            self.resources.food += int(amount)
    
    def building_at(self, gx, gy):
        """Get building at grid position (gx, gy), or None if no building there."""
        if self.building_group is None:
            return None
        for building in self.building_group:
            if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                building.grid_x == gx and building.grid_y == gy):
                return building
        return None
    
    def is_wall_at(self, gx, gy):
        """Check if there's a wall at grid position (gx, gy)."""
        b = self.building_at(gx, gy)
        return bool(b) and getattr(b, "TYPE_ID", "").startswith("wall")
    
    def wall_tile_index_at(self, gx, gy):
        """Get the tile index of a wall at grid position (gx, gy), or None."""
        b = self.building_at(gx, gy)
        if not b or not hasattr(b, "tile_index"):
            return None
        return b.tile_index
    
    def refresh_wall_and_neighbors(self, gx, gy):
        """Refresh wall tile variants for the tile at (gx, gy) and its 4 neighbors."""
        for nx, ny in ((gx, gy), (gx+1, gy), (gx-1, gy), (gx, gy+1), (gx, gy-1)):
            b = self.building_at(nx, ny)
            if b and hasattr(b, "refresh_wall_variant"):
                b.refresh_wall_variant(self)
    
    def autotile_wall_and_neighbors(self, gx, gy):
        """Alias for refresh_wall_and_neighbors (backwards compatibility)."""
        self.refresh_wall_and_neighbors(gx, gy)

# Initialize core systems first
game_state_manager = GameStateManager()
save_system = SaveSystem()
sound_system = SoundSystem()

# Initialize pathfinding (will be updated with building_group after buildings are created)
from world.pathfinding import Pathfinding
pathfinding = Pathfinding(grid, building_group)

# Node and survivor groups
node_group = pygame.sprite.Group()
survivor_group = pygame.sprite.Group()

# Initialize world (wave_manager will be added after initialization)
world = World(resources, grid, enemy_group=enemy_group, projectile_group=projectile_group, building_group=building_group, sound_system=sound_system, pathfinding=pathfinding, node_group=node_group, survivor_group=survivor_group)

# Initialize wave manager
wave_manager = WaveManager(world, waves_config, difficulty="normal")
# Update world with wave_manager reference
world.wave_manager = wave_manager

# Initialize UI components
hud = HUD(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
game_over_screen = GameOverScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
pause_menu = PauseMenu(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
building_panel = BuildingPanel(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)

# Set UI callbacks
def load_startup_cfg():
    """Load startup configuration from JSON"""
    import os
    try:
        path = os.path.join("data", "config", "startup.json")
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: startup.json not found, using defaults")
        return {
            "upper_fraction": 0.6667,
            "north_wall": {
                "y_offset_tiles": 1,
                "length_tiles": 20,
                "gate_width_tiles": 2,
                "organic_shape": True,
                "curve_depth_tiles": 2,
                "variation_tiles": 1
            },
            "hq": {
                "behind_wall_offset_tiles": 8,
                "center_x_offset_tiles": 0
            },
            "turret_pads": {
                "behind_wall_offset_tiles": 3,
                "x_offsets_from_gate": [-6, 6],
                "additional_turrets": []
            }
        }
    except Exception as e:
        print(f"Error loading startup.json: {e}, using defaults")
        return {
            "upper_fraction": 0.6667,
            "north_wall": {
                "y_offset_tiles": 1,
                "length_tiles": 20,
                "gate_width_tiles": 2,
                "organic_shape": True,
                "curve_depth_tiles": 2,
                "variation_tiles": 1
            },
            "hq": {
                "behind_wall_offset_tiles": 8,
                "center_x_offset_tiles": 0
            },
            "turret_pads": {
                "behind_wall_offset_tiles": 3,
                "x_offsets_from_gate": [-6, 6],
                "additional_turrets": []
            }
        }

def create_organic_wall_shape(cfg_wall, start_cx, wall_row, W_TILES, H_TILES):
    """
    Create an organic wall shape (curved arc with variations).
    Returns list of (gx, gy) positions for wall segments.
    """
    import math
    import random
    wall_len = int(cfg_wall.get("length_tiles", 20))
    gate_w = int(cfg_wall.get("gate_width_tiles", 2))
    organic = cfg_wall.get("organic_shape", True)
    curve_depth = int(cfg_wall.get("curve_depth_tiles", 2))
    variation = int(cfg_wall.get("variation_tiles", 1))
    
    wall_positions = []
    
    if not organic:
        # Straight line (fallback)
        left_x = start_cx - wall_len // 2
        gate_left = start_cx - gate_w // 2
        gate_right = gate_left + gate_w - 1
        right_x = left_x + wall_len - 1
        
        # Left wall
        for gx in range(left_x, gate_left):
            wall_positions.append((gx, wall_row))
        # Right wall
        for gx in range(gate_right + 1, right_x + 1):
            wall_positions.append((gx, wall_row))
        
        gate_positions = [(gx, wall_row) for gx in range(gate_left, gate_right + 1)]
        return wall_positions, gate_positions
    
    # Organic curved shape: Create an arc that curves south (toward base)
    # Use a combination of parabola + sine wave for more organic feel
    left_x = start_cx - wall_len // 2
    right_x = left_x + wall_len - 1
    
    # Calculate gate positions (gate stays at base row, but we'll curve it slightly)
    gate_left = start_cx - gate_w // 2
    gate_right = gate_left + gate_w - 1
    gate_positions = []  # Initialize gate positions list
    
    # Create curved wall positions
    # Combine parabola + sine wave for more organic, wavy appearance
    center_offset = wall_len / 2.0
    if center_offset == 0:
        center_offset = 1
    
    # Helper function to calculate Y position for a given X
    def calculate_wall_y(gx, gate_flatness=1.0):
        x_offset = (gx - start_cx) / center_offset
        # Parabolic curve (curves south/positive Y) - main arc
        parabolic_offset = curve_depth * (x_offset * x_offset) * gate_flatness
        # Sine wave for wavy/organic variation (reduced for gate)
        sine_offset = (variation * 0.5 * gate_flatness) * math.sin(x_offset * math.pi * 2)  # Full wave across wall
        # Random variation for irregularity (reduced for gate)
        random.seed(gx * 7 + 13)  # Deterministic variation
        random_offset = random.randint(-variation, variation) * 0.5 * gate_flatness
        # Combine all offsets
        total_offset = parabolic_offset + sine_offset + random_offset
        gy = int(wall_row + total_offset)
        # Clamp to valid grid bounds
        return max(0, min(H_TILES - 1, gy))
    
    # Left side of gate
    for gx in range(left_x, gate_left):
        gy = calculate_wall_y(gx, gate_flatness=1.0)
        wall_positions.append((gx, gy))
    
    # Gate positions (follows curve but less pronounced - 50% flatness for smoother gate)
    for gx in range(gate_left, gate_right + 1):
        # Gate follows the curve but with reduced variation for smoother appearance
        gy = calculate_wall_y(gx, gate_flatness=0.5)
        gate_positions.append((gx, gy))
    
    # Right side of gate
    for gx in range(gate_right + 1, right_x + 1):
        gy = calculate_wall_y(gx, gate_flatness=1.0)
        wall_positions.append((gx, gy))
    
    return wall_positions, gate_positions

def spawn_starting_layout():
    """Spawn starting layout: HQ behind wall, organic north wall, gate, and turrets"""
    global building_group, grid, turret_group, world
    
    cfg = load_startup_cfg()
    TILE = grid.TILE
    W_TILES = grid.width
    H_TILES = grid.height
    
    # Update grid's upper_fraction if specified in config
    if "upper_fraction" in cfg:
        grid.upper_fraction = cfg["upper_fraction"]
    
    # --- Compute split row (tile index) ---
    split_y_px = grid.get_split_y_px()
    split_row = grid.px_to_tile(split_y_px)
    
    # --- North wall line (near split) ---
    wall_cfg = cfg.get("north_wall", {})
    y_off = int(wall_cfg.get("y_offset_tiles", 1))
    wall_row = max(0, min(H_TILES - 1, split_row - 1 - y_off))  # 1 tile above split by default
    
    start_cx = W_TILES // 2
    
    # Create organic wall shape
    wall_positions, gate_positions = create_organic_wall_shape(
        wall_cfg, start_cx, wall_row, W_TILES, H_TILES
    )
    
    # Import building classes
    from world.buildings.wall_wood import WallWood
    from world.buildings.gate import Gate
    
    # Place walls (organic shape)
    walls_placed = []
    for gx, gy in wall_positions:
        # Ensure position is valid
        if 0 <= gx < W_TILES and 0 <= gy < H_TILES:
            w = WallWood((gx, gy), tier=1)
            w.state = BuildState.ACTIVE  # Start completed
            w.hp = w.max_hp
            w.progress = w.BUILD_TIME
            w.world = world  # Set world reference
            building_group.add(w)
            grid.set_footprint_blocked((gx, gy), WallWood.FOOTPRINT, True)
            walls_placed.append((gx, gy))
    
    # After all walls are placed, refresh all wall variants so they see their neighbors
    for gx, gy in walls_placed:
        world.autotile_wall_and_neighbors(gx, gy)
    
    # Place gate
    for gx, gy in gate_positions:
        if 0 <= gx < W_TILES and 0 <= gy < H_TILES:
            g = Gate((gx, gy), tier=1)
            g.state = BuildState.ACTIVE  # Start completed
            g.hp = g.max_hp
            g.progress = g.BUILD_TIME
            building_group.add(g)
            grid.set_footprint_blocked((gx, gy), Gate.FOOTPRINT, True)
    
    # Find the southernmost wall position (for HQ placement behind wall)
    if wall_positions:
        max_wall_y = max(gy for _, gy in wall_positions)
        if gate_positions:
            max_wall_y = max(max_wall_y, max(gy for _, gy in gate_positions))
    else:
        max_wall_y = wall_row
    
    print(f"North wall placed (organic shape) with {len(wall_positions)} segments")
    print(f"Gate placed at {len(gate_positions)} tiles, max wall Y: {max_wall_y}")
    
    # --- HQ placement (behind wall) ---
    hq_cfg = cfg.get("hq", {})
    behind_offset = int(hq_cfg.get("behind_wall_offset_tiles", 8))
    center_x_offset = int(hq_cfg.get("center_x_offset_tiles", 0))
    
    hq_w, hq_h = HQ.FOOTPRINT
    hq_gx = start_cx + center_x_offset - hq_w // 2
    hq_gy = max_wall_y + behind_offset
    
    # Ensure HQ fits on screen
    hq_gy = min(H_TILES - hq_h, hq_gy)
    hq_gx = max(0, min(W_TILES - hq_w, hq_gx))
    
    hq = HQ((hq_gx, hq_gy), tier=1)
    building_group.add(hq)
    grid.set_footprint_blocked((hq_gx, hq_gy), HQ.FOOTPRINT, True)
    
    # Store HQ reference in world
    if 'world' in globals():
        world.hq = hq
    
    print(f"HQ spawned at grid position ({hq_gx}, {hq_gy}) - behind wall")
    
    # --- Turret pads (behind wall, symmetric) ---
    turret_cfg = cfg.get("turret_pads", {})
    pad_off_y = int(turret_cfg.get("behind_wall_offset_tiles", 3))
    pad_row = min(H_TILES - 1, max_wall_y + pad_off_y)
    
    # Use existing turret images (loaded at startup)
    global turret_sprite_sheets, turret_base_images
    
    # Main turrets near gate
    for dx in turret_cfg.get("x_offsets_from_gate", [-6, 6]):
        gx = start_cx + int(dx)
        if 0 <= gx < W_TILES and 0 <= pad_row < H_TILES:
            t = BallisticTurret((gx, pad_row), turret_sprite_sheets, turret_base_images, tier=1)
            t.state = BuildState.ACTIVE
            t.hp = t.max_hp
            t.progress = t.BUILD_TIME
            building_group.add(t)
            turret_group.add(t)
            grid.set_footprint_blocked((gx, pad_row), BallisticTurret.FOOTPRINT, True)
            print(f"Turret placed at ({gx}, {pad_row})")
    
    # Additional turrets (if configured)
    for turret_def in turret_cfg.get("additional_turrets", []):
        t_x = start_cx + int(turret_def.get("x_offset", 0))
        t_y = pad_row + int(turret_def.get("y_offset", 0))
        if 0 <= t_x < W_TILES and 0 <= t_y < H_TILES:
            t = BallisticTurret((t_x, t_y), turret_sprite_sheets, turret_base_images, tier=1)
            t.state = BuildState.ACTIVE
            t.hp = t.max_hp
            t.progress = t.BUILD_TIME
            building_group.add(t)
            turret_group.add(t)
            grid.set_footprint_blocked((t_x, t_y), BallisticTurret.FOOTPRINT, True)
            print(f"Additional turret placed at ({t_x}, {t_y})")
    
    print(f"Starting layout spawned: HQ at ({hq_gx}, {hq_gy}), organic wall with gate, turrets behind wall")
    
    # Update pathfinding building group reference (after all buildings are placed)
    if 'pathfinding' in globals():
        pathfinding.building_group = building_group
    if 'world' in globals() and hasattr(world, 'pathfinding'):
        world.pathfinding.building_group = building_group

def spawn_hq_at_center():
    """Legacy function - now uses spawn_starting_layout()"""
    spawn_starting_layout()

def spawn_initial_workers():
    """Spawn initial workers near HQ"""
    global survivor_group, building_group
    # Find HQ position
    hq_pos = None
    for building in building_group:
        if isinstance(building, HQ):
            hq_pos = building.pos
            break
    
    if not hq_pos:
        return
    
    # Spawn 3 workers near HQ
    for i in range(3):
        offset_x = (i - 1) * 40  # Spread them out
        worker_pos = (hq_pos.x + offset_x, hq_pos.y + 40)
        worker = Worker(worker_pos)
        survivor_group.add(worker)
    
    print(f"Spawned {3} workers near HQ")

def spawn_daily_resource_nodes():
    """Spawn daily resource nodes in upper zone"""
    global node_group, world, grid
    
    # Load nodes config
    try:
        with open('data/config/nodes.json', 'r') as f:
            nodes_config = json.load(f)
    except:
        print("Warning: Could not load nodes.json, using defaults")
        nodes_config = {
            "tree_patch": {"resource": "wood", "yield_total": 120, "gather_per_tick": 6, "tick_sec": 0.6},
            "scrap_pile": {"resource": "iron", "yield_total": 100, "gather_per_tick": 5, "tick_sec": 0.7},
            "daily_spawn": {"trees": 4, "scrap": 3, "min_dist_from_wall_px": 96}
        }
    
    # Define upper zone (top 1/3 of screen)
    upper_zone_rect = pygame.Rect(0, 0, c.SCREEN_WIDTH, c.SCREEN_HEIGHT // 3)
    
    # Spawn nodes
    new_nodes = spawn_daily_nodes(world, nodes_config, upper_zone_rect, grid)
    for node in new_nodes:
        node_group.add(node)
    
    print(f"Spawned {len(new_nodes)} resource nodes in upper zone")

def restart_game():
    """Restart game"""
    global building_group, turret_group, enemy_group, projectile_group, resources, wave_manager, game_state_manager, node_group, survivor_group
    # Reset game state
    building_group.empty()
    turret_group.empty()
    enemy_group.empty()
    projectile_group.empty()
    node_group.empty()
    survivor_group.empty()
    grid.clear()
    resources.wood = 500
    resources.iron = 300
    resources.food = 200
    wave_manager.reset()
    game_state_manager.reset()
    game_over_screen.hide()
    pause_menu.hide()
    building_panel.hide()
    # Spawn starting layout (HQ, walls, gate, turrets)
    spawn_starting_layout()
    # Spawn initial workers
    spawn_initial_workers()
    # Spawn daily nodes
    spawn_daily_resource_nodes()
    print("Game restarted")

def load_game():
    """Load game"""
    global building_group, turret_group, enemy_group, projectile_group, resources, wave_manager, game_state_manager
    save_data = save_system.load_world()
    if save_data:
        # Restore resources
        resources.wood = save_data["resources"]["wood"]
        resources.iron = save_data["resources"]["iron"]
        resources.food = save_data["resources"]["food"]
        
        # Restore wave manager
        wave_manager.night = save_data["wave_manager"]["night"]
        wave_manager.day = save_data["wave_manager"]["day"]
        wave_manager.state = save_data["wave_manager"]["state"]
        wave_manager.enemies_killed = save_data["wave_manager"]["enemies_killed"]
        wave_manager.enemies_spawned = save_data["wave_manager"]["enemies_spawned"]
        wave_manager.timer = save_data["wave_manager"].get("timer", 0.0)
        
        # Restore buildings (simplified - would need proper deserialization)
        # building_group.empty()
        # turret_group.empty()
        # for building_data in save_data["buildings"]:
        #     # Recreate buildings from data
        #     pass
        
        # Restore game state
        game_state_manager.set_state(GameState(save_data["game_state"]))
        
        print("Game loaded!")
    else:
        print("No save file found!")

def save_game():
    """Save game"""
    save_system.save_world(world, wave_manager, game_state_manager, resources)
    print("Game saved!")

def quit_game():
    """Quit game"""
    global running
    running = False

game_over_screen.on_restart = restart_game
game_over_screen.on_quit = quit_game
def resume_game():
    """Resume game"""
    game_state_manager.resume()
    pause_menu.hide()

pause_menu.on_resume = resume_game
pause_menu.on_save = save_game
pause_menu.on_load = load_game
pause_menu.on_quit = quit_game

# Building panel callbacks (will be set up in game loop)
def upgrade_building(building):
    """Upgrade building"""
    if building and building.tier < building.TIER_MAX:
        from world.building import Cost
        upgrade_mult = 1.25
        base_cost = building.COST
        upgrade_cost = Cost(
            wood=int(base_cost.wood * upgrade_mult * building.tier),
            iron=int(base_cost.iron * upgrade_mult * building.tier),
            food=int(base_cost.food * upgrade_mult * building.tier)
        )
        if (resources.wood >= upgrade_cost.wood and
            resources.iron >= upgrade_cost.iron and
            resources.food >= upgrade_cost.food):
            resources.wood -= upgrade_cost.wood
            resources.iron -= upgrade_cost.iron
            resources.food -= upgrade_cost.food
            building.upgrade()
            # If it's a wall, refresh neighbors after upgrade
            if hasattr(building, 'on_upgrade') and callable(building.on_upgrade):
                # on_upgrade will call autotile_wall_and_neighbors if world is set
                if hasattr(building, 'world') and building.world:
                    building.on_upgrade()
                elif isinstance(building, (WallWood, WallIron)) and world:
                    building.world = world
                    building.on_upgrade()
            sound_system.play("upgrade")
            print(f"Upgraded {building.TYPE_ID} to tier {building.tier}")

def repair_building(building):
    """Repair building"""
    if building and building.hp < building.max_hp:
        hp_needed = building.max_hp - building.hp
        wood_cost = max(1, hp_needed // 5)
        if resources.wood >= wood_cost:
            resources.wood -= wood_cost
            building.repair(hp_needed)
            sound_system.play("repair")
            print(f"Repaired {building.TYPE_ID}")

def sell_building(building):
    """Sell building"""
    if building:
        # Prevent selling HQ (main base)
        if isinstance(building, HQ):
            print("Cannot sell HQ - it's the main base!")
            return
        building.refund_cost(resources, ratio=0.6)
        grid.set_footprint_blocked((building.grid_x, building.grid_y), building.FOOTPRINT, False)
        building_group.remove(building)
        if building in turret_group:
            turret_group.remove(building)
        building_panel.hide()
        sound_system.play("button_click")
        print(f"Sold {building.TYPE_ID}")

###################
# Debug functions
###################
def debug_add_resources():
    """Add +100 to all resources"""
    resources.wood += 100
    resources.iron += 100
    resources.food += 100
    print("Debug: Added +100 to all resources")

def debug_instant_build():
    """Complete all buildings under construction"""
    for building in building_group:
        if building.state == BuildState.CONSTRUCTING:
            building.progress = building.BUILD_TIME
            building.state = BuildState.ACTIVE
            building.hp = building.max_hp
            building.on_complete(world)
            # Mark tiles as blocked
            grid.set_footprint_blocked((building.grid_x, building.grid_y), building.FOOTPRINT, True)
    print("Debug: Completed all buildings")

def debug_spawn_zombie_at_mouse(mouse_pos):
    """Spawn a zombie at mouse position"""
    zombie = BasicZombie(mouse_pos)
    enemy_group.add(zombie)
    print(f"Debug: Spawned zombie at {mouse_pos}")

def debug_clear_enemies():
    """Clear all enemies"""
    count = len(enemy_group)
    enemy_group.empty()
    print(f"Debug: Cleared {count} enemies")

def debug_clear_buildings():
    """Clear all buildings"""
    count = len(building_group)
    # Unblock tiles
    for building in building_group:
        grid.set_footprint_blocked((building.grid_x, building.grid_y), building.FOOTPRINT, False)
    building_group.empty()
    turret_group.empty()
    print(f"Debug: Cleared {count} buildings")

def debug_toggle_spawner():
    """Toggle spawner on/off"""
    zombie_spawner.set_active(not zombie_spawner.active)
    status = "ON" if zombie_spawner.active else "OFF"
    print(f"Debug: Spawner {status}")

def debug_kill_all_enemies():
    """Kill all enemies"""
    count = 0
    for enemy in enemy_group:
        enemy.take_damage(enemy.hp)
        count += 1
    print(f"Debug: Killed {count} enemies")

def debug_complete_all_buildings():
    """Complete all buildings instantly"""
    count = 0
    for building in building_group:
        if building.state == BuildState.CONSTRUCTING:
            building.progress = building.BUILD_TIME
            building.state = BuildState.ACTIVE
            building.hp = building.max_hp
            building.on_complete(world)
            grid.set_footprint_blocked((building.grid_x, building.grid_y), building.FOOTPRINT, True)
            count += 1
    print(f"Debug: Completed {count} buildings")

# Register debug actions
debug_system.register_action(pygame.K_F1, "Add +100 Resources", debug_add_resources)
debug_system.register_action(pygame.K_F2, "Instant Build", debug_instant_build)
debug_system.register_action(pygame.K_F3, "Spawn Zombie @ Mouse", lambda: None)  # Handled separately
debug_system.register_action(pygame.K_F4, "Clear All Enemies", debug_clear_enemies)
debug_system.register_action(pygame.K_F5, "Clear All Buildings", debug_clear_buildings)
debug_system.register_action(pygame.K_F6, "Toggle Spawner", debug_toggle_spawner)
debug_system.register_action(pygame.K_F7, "Kill All Enemies", debug_kill_all_enemies)
debug_system.register_action(pygame.K_F8, "Complete All Buildings", debug_complete_all_buildings)
# F9: Skip to night, F10: Skip to summary, F11: Cycle difficulty (handled in event loop)

###################
# Helper functions for buttons
###################
def create_button_image(text, color=(100, 150, 100), width=100, height=40):
    """Create a button image with text"""
    button_img = pygame.Surface((width, height))
    button_img.fill(color)
    font = pygame.font.Font(None, 20)
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(width//2, height//2))
    button_img.blit(text_surface, text_rect)
    return button_img

###################
# Create buttons for all buildings
###################
button_y_start = 10
button_spacing = 45
buttons = {}

# Building types with their button labels and colors
# Note: HQ is not buildable - it spawns automatically at game start
building_types = [
    (BallisticTurret, "Ballistic", (150, 100, 100), turret_sprite_sheets, turret_base_images),
    (GatlingTurret, "Gatling", (200, 150, 100), gatling_image, gatling_base),
    (PiercerTurret, "Piercer", (150, 100, 150), turret_sheet_lv1, turret_base_lv1),
    (Wall, "Wall", (120, 120, 120)),
    (Gate, "Gate", (100, 100, 100)),
    (Housing, "Housing", (150, 120, 100)),
    (Farm, "Farm", (100, 150, 100)),
    (Sawmill, "Sawmill", (139, 90, 43)),
    (Smelter, "Smelter", (150, 150, 150)),
]

for i, (building_class, label, color, *args) in enumerate(building_types):
    button_img = create_button_image(label, color)
    button = Button(10, button_y_start + i * button_spacing, button_img)
    buttons[building_class] = {
        'button': button,
        'label': label,
        'color': color,
        'args': args
    }

###################
# Helper functions
###################
def pixel_to_grid(pos):
    """Convert pixel position to grid coordinates."""
    x, y = pos
    grid_x = x // TILE
    grid_y = y // TILE
    return (grid_x, grid_y)

def grid_to_pixel(grid_pos):
    """Convert grid coordinates to pixel position (center of tile)."""
    gx, gy = grid_pos
    px = (gx + 0.5) * TILE
    py = (gy + 0.5) * TILE
    return (px, py)

def can_place_building(building_class, grid_pos, grid, building_group=None):
    """Check if a building can be placed at the given grid position."""
    return building_class.can_place(grid, grid_pos, building_group)

def draw_preview(screen, grid_pos, can_place, footprint=(1, 1)):
    """Draw building preview at grid position."""
    w, h = footprint
    gx, gy = grid_pos
    
    # Calculate pixel position for top-left corner
    px = gx * TILE
    py = gy * TILE
    
    # Choose color based on whether placement is valid
    if can_place:
        color = (0, 255, 0, 100)  # Green with transparency
        outline_color = (0, 255, 0)
    else:
        color = (255, 0, 0, 100)  # Red with transparency
        outline_color = (255, 0, 0)
    
    # Create a semi-transparent surface
    preview_surface = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
    preview_surface.fill(color)
    
    # Draw the preview
    screen.blit(preview_surface, (px, py))
    pygame.draw.rect(screen, outline_color, (px, py, w * TILE, h * TILE), 2)

def deselect_building():
    """Deselect currently selected building and hide panel."""
    global selected_building
    
    # Deselect all buildings
    for building in building_group:
        if hasattr(building, 'selected'):
            building.selected = False
    
    # Hide building panel
    building_panel.hide()
    
    # Clear selected building
    selected_building = None

def select_building(mouse_pos, building_group):
    """Select a building at mouse position."""
    global selected_building
    
    # Deselect all buildings first
    for building in building_group:
        if hasattr(building, 'selected'):
            building.selected = False
    selected_building = None
    
    # Check if mouse is over any building
    for building in building_group:
        if building.rect.collidepoint(mouse_pos):
            if hasattr(building, 'selected'):
                building.selected = True
            selected_building = building
            return True
    
    return False

def draw_resources(screen, resources, font):
    """Draw resource display."""
    y_offset = 10
    x_offset = 400
    line_height = 25
    
    texts = [
        f"Wood: {int(resources.wood)}",
        f"Iron: {int(resources.iron)}",
        f"Food: {int(resources.food)}"
    ]
    
    for i, text in enumerate(texts):
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (x_offset, y_offset + i * line_height))
    
    # Draw enemy count
    enemy_text = font.render(f"Zombies: {len(enemy_group)}", True, (255, 0, 0))
    screen.blit(enemy_text, (x_offset, y_offset + len(texts) * line_height))

def create_building(building_class, grid_pos, *args):
    """Create a building instance based on the building class."""
    # Check if it's a turret (needs sprite sheet and base image)
    if building_class is BallisticTurret:
        if len(args) >= 2:
            sprite_sheets, base_images = args[0], args[1]
            building = building_class(grid_pos, sprite_sheets, base_images, tier=1)
            turret_group.add(building)
            return building
    elif building_class in (GatlingTurret, PiercerTurret):
        if len(args) >= 2:
            sprite_sheet, base_image = args[0], args[1]
            building = building_class(grid_pos, sprite_sheet, base_image, tier=1)
            turret_group.add(building)
            return building
    else:
        # Other buildings just need grid position
        building = building_class(grid_pos, tier=1)
        return building
    
    return None

###################
# Initialize game - spawn starting layout
###################
spawn_starting_layout()
# Spawn initial workers (after HQ is created)
spawn_initial_workers()
# Spawn daily nodes
spawn_daily_resource_nodes()

###################
# Main game loop
###################
font = pygame.font.Font(None, 24)
fps_counter = 0
fps_timer = 0.0
current_fps = 60.0

while running:
    dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
    
    # Calculate FPS
    fps_timer += dt
    fps_counter += 1
    if fps_timer >= 1.0:
        current_fps = fps_counter / fps_timer
        fps_counter = 0
        fps_timer = 0.0
    
    # Fill screen with background
    # Draw grass tile map background
    # Calculate how many tiles we need to cover the screen
    tiles_x = (c.SCREEN_WIDTH + TILE - 1) // TILE  # Ceiling division to ensure full coverage
    tiles_y = (c.SCREEN_HEIGHT + TILE - 1) // TILE  # Ceiling division to ensure full coverage
    
    # Draw grass tiles across the entire screen with variation
    for y in range(tiles_y):
        for x in range(tiles_x):
            # Use a simple pattern to select which grass variant to use
            # This creates a somewhat random but consistent pattern across the map
            # Using modulo to cycle through variants
            variant_index = (x * 7 + y * 11) % len(grass_tiles)
            tile_x = x * TILE
            tile_y = y * TILE
            screen.blit(grass_tiles[variant_index], (tile_x, tile_y))
    
    # Draw day/night divider line (subtle)
    split_y_px = grid.get_split_y_px()
    pygame.draw.line(screen, (40, 50, 40), (0, split_y_px), (c.SCREEN_WIDTH, split_y_px), 2)
    # Draw semi-transparent overlay to distinguish zones
    overlay = pygame.Surface((c.SCREEN_WIDTH, split_y_px), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 20))  # Very subtle darkening for upper zone (night/danger zone)
    screen.blit(overlay, (0, 0))
    
    # Draw gate icon/banner on gate columns (if gate exists)
    try:
        # Find gate buildings using isinstance (Gate is already imported)
        gate_buildings = [b for b in building_group if isinstance(b, Gate)]
        if gate_buildings:
            # Get gate center position (use first gate)
            gate_building = gate_buildings[0]
            gate_center_x_px = gate_building.pos.x
            gate_pixel_y = split_y_px - 25  # Above the divider line
            # Draw simple "GATE" text banner
            gate_font = pygame.font.Font(None, 20)
            gate_text = gate_font.render("GATE", True, (200, 200, 100))
            gate_text_rect = gate_text.get_rect(center=(gate_center_x_px, gate_pixel_y))
            # Draw background for text
            banner_bg = pygame.Surface((64, 20), pygame.SRCALPHA)
            banner_bg.fill((0, 0, 0, 100))
            screen.blit(banner_bg, (gate_text_rect.x - 10, gate_text_rect.y - 2))
            screen.blit(gate_text, gate_text_rect)
    except Exception:
        # Silently fail if gate banner drawing fails (non-critical)
        pass
    
    # Get mouse position
    mouse_pos = pygame.mouse.get_pos()
    
    ###################
    # Handle button clicks
    ###################
    for building_class, button_data in buttons.items():
        if button_data['button'].draw(screen):
            if selected_building_type == building_class:
                # Deselect if clicking the same button
                selected_building_type = None
                build_mode = False
            else:
                # Select this building type
                selected_building_type = building_class
                build_mode = True
                # Deselect any selected building when entering build mode
                deselect_building()
    
    # Highlight selected button
    if selected_building_type:
        if selected_building_type in buttons:
            button = buttons[selected_building_type]['button']
            # Draw highlight
            pygame.draw.rect(screen, (255, 255, 0), button.rect, 3)
    
    ###################
    # Update buildings
    ###################
    # Track which buildings are now active (for tile blocking)
    newly_active = []
    buildings_to_remove = []
    for building in building_group:
        old_state = building.state
        building.update(dt, world)
        # Check if construction just completed
        if old_state == BuildState.CONSTRUCTING and building.state == BuildState.ACTIVE:
            newly_active.append(building)
            sound_system.play("build_placed")
            # If it's a wall, refresh neighbors when construction completes
            if hasattr(building, 'on_place') and callable(building.on_place):
                building.on_place(world)
        # Check if building was destroyed OR if HQ HP <= 0 (lose condition)
        if building.state == BuildState.DESTROYED:
            buildings_to_remove.append(building)
            sound_system.play("building_destroyed")
        
        # Check if HQ HP <= 0 (lose condition) - check HP directly, not just state
        if isinstance(building, HQ) and building.hp <= 0:
            if not game_over_screen.is_visible:  # Only trigger once
                game_state_manager.game_over()
                game_over_screen.show(GameState.GAME_OVER, {
                    "nights": wave_manager.night - 1,
                    "enemies_killed": wave_manager.enemies_killed,
                    "buildings_built": len([b for b in building_group if not isinstance(b, HQ)])
                })
                sound_system.play("game_over")
                # Mark HQ as destroyed
                building.state = BuildState.DESTROYED
                building.hp = 0
                if building not in buildings_to_remove:
                    buildings_to_remove.append(building)
    
    # Mark tiles as blocked for newly active buildings
    for building in newly_active:
        grid.set_footprint_blocked((building.grid_x, building.grid_y), building.FOOTPRINT, True)
        # Clear pending construction if this was it
        if pending_construction == building:
            pending_construction = None
    
    # Remove destroyed buildings
    for building in buildings_to_remove:
        # Store position before removing (for wall autotiling)
        gx, gy = building.grid_x, building.grid_y
        # Check if it's a wall (for autotiling neighbors)
        is_wall = hasattr(building, 'TYPE_ID') and building.TYPE_ID.startswith('wall')
        
        # Unblock grid tiles
        grid.set_footprint_blocked((gx, gy), building.FOOTPRINT, False)
        # Remove from groups
        building_group.remove(building)
        if building in turret_group:
            turret_group.remove(building)
        # Clear pending construction if this was it
        if pending_construction == building:
            pending_construction = None
        # Hide building panel if destroyed building was selected
        if building_panel.selected_building == building:
            building_panel.hide()
        
        # Refresh wall neighbors after removal (on_destroy should handle this, but ensure it happens)
        if is_wall:
            world.autotile_wall_and_neighbors(gx, gy)
    
    ###################
    # Update wave manager
    ###################
    # Only update if playing (not paused or game over)
    if game_state_manager.is_playing() and not game_over_screen.is_visible:
        wave_state = wave_manager.update(dt, zombie_spawner, world)
        
        # Check win condition
        if wave_state == "WIN" or wave_manager.is_won():
            game_state_manager.win()
            game_over_screen.show(GameState.WIN, {
                "nights": wave_manager.night - 1,
                "enemies_killed": wave_manager.enemies_killed,
                "buildings_built": len(building_group)
            })
            sound_system.play("game_over")
        
        # Track previous state to detect transitions
        if not hasattr(wave_manager, '_prev_state'):
            wave_manager._prev_state = wave_manager.state
        
        # Check for state transitions
        if wave_manager._prev_state != wave_manager.state:
            # State changed
            if wave_manager.state == WaveManager.STATE_DAY:
                # Just started day - spawn daily nodes
                spawn_daily_resource_nodes()
            elif wave_manager.state == WaveManager.STATE_NIGHT:
                # Just started night
                recipe = wave_manager.get_wave_recipe()
                spawn_config = waves_config["spawn"]
                zombie_spawner.begin(recipe, spawn_config)
                hud.show_event(f"Night {wave_manager.night} Begins!", 3.0)
                sound_system.play("wave_start")
                wave_manager.enemies_spawned = 0
            elif wave_manager.state == WaveManager.STATE_SUMMARY:
                # Just started summary - autosave
                save_system.save_world(world, wave_manager, game_state_manager, resources)
                hud.show_event(f"Night {wave_manager.night - 1} Cleared!", 3.0)
                sound_system.play("wave_clear")
        
        wave_manager._prev_state = wave_manager.state
    
    ###################
    # Update enemies
    ###################
    # Update spawner (only during night)
    if wave_manager.state == WaveManager.STATE_NIGHT:
        zombie_spawner.update(dt, enemy_group)
        # Update enemies spawned count
        wave_manager.enemies_spawned = zombie_spawner.spawn_count
    
    # Update world's enemy group and projectile group references (for turrets and enemies)
    world.enemy_group = enemy_group
    world.projectile_group = projectile_group
    
    # Update enemies first (movement and targeting)
    enemies_to_remove = []
    for enemy in enemy_group:
        was_alive = enemy.alive
        enemy.update(dt, world)
        # Track enemy kills (only count once when enemy dies)
        if was_alive and not enemy.alive and enemy.hp <= 0:
            wave_manager.enemies_killed += 1
            sound_system.play("enemy_death")
        # Mark enemies that reached bottom or died for removal
        if enemy.reached_bottom or not enemy.alive:
            enemies_to_remove.append(enemy)
    
    # Build spatial grid for separation AFTER enemies have moved
    # Cell size: 64 pixels (2x2 tiles)
    CELL_SIZE = 64
    spatial_buckets = {}
    for enemy in enemy_group:
        if enemy.alive:
            ix = int(enemy.pos.x // CELL_SIZE)
            iy = int(enemy.pos.y // CELL_SIZE)
            key = (ix, iy)
            if key not in spatial_buckets:
                spatial_buckets[key] = []
            spatial_buckets[key].append(enemy)
    
    # Apply separation to all alive enemies
    for enemy in enemy_group:
        if enemy.alive:
            # Get neighbors from spatial grid
            ix = int(enemy.pos.x // CELL_SIZE)
            iy = int(enemy.pos.y // CELL_SIZE)
            neighbors = []
            # Check current cell and 8 surrounding cells
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    key = (ix + dx, iy + dy)
                    if key in spatial_buckets:
                        for other in spatial_buckets[key]:
                            if other is not enemy and other.alive:
                                dist = (enemy.pos - other.pos).length()
                                if dist <= enemy.SEPARATION_RANGE:
                                    neighbors.append(other)
            
            # Apply separation
            if neighbors:
                enemy.apply_separation(dt, neighbors)
    
    # Remove dead/reached-bottom enemies
    for enemy in enemies_to_remove:
        enemy_group.remove(enemy)
    
    ###################
    # Update nodes
    ###################
    # Nodes don't need updates (they're just data containers)
    # Remove depleted nodes
    depleted_nodes = []
    for node in node_group:
        if node.is_depleted():
            depleted_nodes.append(node)
    for node in depleted_nodes:
        node_group.remove(node)
    
    ###################
    # Update survivors
    ###################
    # Build spatial grid for survivor separation
    CELL_SIZE = 64
    survivor_spatial_buckets = {}
    for survivor in survivor_group:
        if survivor.alive:
            ix = int(survivor.pos.x // CELL_SIZE)
            iy = int(survivor.pos.y // CELL_SIZE)
            key = (ix, iy)
            if key not in survivor_spatial_buckets:
                survivor_spatial_buckets[key] = []
            survivor_spatial_buckets[key].append(survivor)
    
    # Update survivors
    survivors_to_remove = []
    for survivor in survivor_group:
        if not survivor.alive:
            survivors_to_remove.append(survivor)
            continue
        
        # Update survivor
        survivor.update(dt, world)
        
        # Apply separation to workers
        if survivor.role == "worker" and survivor.alive:
            # Get neighbors from spatial grid
            ix = int(survivor.pos.x // CELL_SIZE)
            iy = int(survivor.pos.y // CELL_SIZE)
            neighbors = []
            # Check current cell and 8 surrounding cells
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    key = (ix + dx, iy + dy)
                    if key in survivor_spatial_buckets:
                        for other in survivor_spatial_buckets[key]:
                            if other is not survivor and other.alive:
                                dist = (survivor.pos - other.pos).length()
                                if dist <= survivor.SEPARATION_RANGE:
                                    neighbors.append(other)
            
            # Apply separation
            if neighbors:
                survivor.apply_separation(dt, neighbors)
    
    # Remove dead survivors
    for survivor in survivors_to_remove:
        survivor_group.remove(survivor)
    
    ###################
    # Update projectiles
    ###################
    projectiles_to_remove = []
    for projectile in projectile_group:
        # Update projectile (check collisions with enemies and buildings)
        # Projectiles automatically check correct target type (enemy or building)
        projectile.update(dt, enemy_group, building_group)
        if not projectile.active:
            projectiles_to_remove.append(projectile)
    
    # Remove inactive projectiles
    for projectile in projectiles_to_remove:
        projectile_group.remove(projectile)
    
    # Draw turrets separately (they have custom rendering)
    for turret in turret_group:
        turret.draw(screen)
    
    # Draw other buildings
    for building in building_group:
        if building not in turret_group:
            building.draw(screen)
    
    ###################
    # Draw nodes
    ###################
    for node in node_group:
        node.draw(screen)
    
    ###################
    # Draw survivors
    ###################
    for survivor in survivor_group:
        if survivor.alive:
            survivor.draw(screen)
    
    ###################
    # Draw projectiles
    ###################
    for projectile in projectile_group:
        projectile.draw(screen)
    
    ###################
    # Draw enemies
    ###################
    for enemy in enemy_group:
        enemy.draw(screen)
    
    ###################
    # Draw HUD
    ###################
    # Find HQ for HP display
    hq = None
    hq_hp = 0
    hq_max_hp = 2000
    for building in building_group:
        if isinstance(building, HQ):
            hq = building
            hq_hp = building.hp
            hq_max_hp = building.max_hp
            break
    
    hud.update(dt, wave_manager.day, wave_manager.night, wave_manager.state, {
        "enemies_spawned": zombie_spawner.spawn_count,
        "total_to_spawn": zombie_spawner.total_to_spawn,
        "enemies_killed": wave_manager.enemies_killed
    }, hq_hp, hq_max_hp)
    
    # Show "Starting Defenses" hint on Day 1 (once)
    if wave_manager.day == 1 and wave_manager.state == "DAY" and not hasattr(hud, '_starting_hint_shown'):
        hud.show_starting_defenses_hint()
        hud._starting_hint_shown = True
    
    hud.draw(screen)
    
    ###################
    # Draw building panel
    ###################
    if building_panel.is_visible:
        building_panel.draw(screen, resources)
    
    ###################
    # Draw pause menu
    ###################
    if game_state_manager.is_paused():
        pause_menu.draw(screen)
    
    ###################
    # Draw game over screen
    ###################
    if game_over_screen.is_visible:
        game_over_screen.draw(screen)
    
    ###################
    # Draw preview when in build mode
    ###################
    if build_mode and selected_building_type:
        grid_pos = pixel_to_grid(mouse_pos)
        can_place = can_place_building(selected_building_type, grid_pos, grid)
        
        # Check if we have enough resources
        cost = selected_building_type.get_cost()
        if resources.wood < cost.wood or resources.iron < cost.iron or resources.food < cost.food:
            can_place = False
        
        draw_preview(screen, grid_pos, can_place, selected_building_type.FOOTPRINT)
    
    ###################
    # Draw gather mode indicator
    ###################
    if gather_mode:
        # Draw text indicator
        gather_text = font.render("GATHER MODE - Click on nodes to assign workers (G to cancel)", True, (255, 255, 0))
        text_rect = gather_text.get_rect(center=(c.SCREEN_WIDTH // 2, 100))
        screen.blit(gather_text, text_rect)
    
    ###################
    # Draw resources
    ###################
    draw_resources(screen, resources, font)
    
    ################### 
    # Update debug info
    ###################
    if debug_system.is_active():
        debug_system.update_info("Buildings", len(building_group))
        debug_system.update_info("Enemies", len(enemy_group))
        debug_system.update_info("Turrets", len(turret_group))
        debug_system.update_info("Spawner", "ON" if zombie_spawner.active else "OFF")
        debug_system.update_info("Wave State", wave_manager.state)  
        debug_system.update_info("Day", wave_manager.day)
        grid_pos_debug = pixel_to_grid(mouse_pos)
        debug_system.update_info("Grid Pos", f"({grid_pos_debug[0]}, {grid_pos_debug[1]})")
    
    ###################
    # Draw debug overlay
    ###################
    debug_system.draw(screen, mouse_pos, current_fps)
    
    ###################
    # Handle events
    ###################
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Skip input if game over or paused
            if game_over_screen.is_visible:
                if game_over_screen.handle_event(event):
                    continue
                continue
            
            if game_state_manager.is_paused():
                if pause_menu.handle_event(event):
                    continue
                continue
            
            # Debug mode: F3 + Click to spawn zombie at mouse
            if debug_system.is_active():
                keys = pygame.key.get_pressed()
                if keys[pygame.K_F3]:
                    debug_spawn_zombie_at_mouse(mouse_pos)
                    continue
            
            # Handle building panel clicks (upgrade/repair/sell)
            if building_panel.is_visible:
                button_clicked = building_panel.handle_event(event, mouse_pos)
                if button_clicked == "close":
                    # Clicked outside panel - deselect building and hide panel
                    deselect_building()
                elif button_clicked == "upgrade":
                    building = building_panel.selected_building
                    if building:
                        upgrade_building(building)
                elif button_clicked == "repair":
                    building = building_panel.selected_building
                    if building:
                        repair_building(building)
                elif button_clicked == "sell":
                    building = building_panel.selected_building
                    if building:
                        sell_building(building)
                        # Building is sold, so deselect it
                        deselect_building()
                continue
            
            # Check if in gather mode
            if gather_mode:
                # Check if clicked on a node
                clicked_node = False
                for node in node_group:
                    if node.rect.collidepoint(mouse_pos):
                        clicked_node = True
                        # Find nearest idle worker
                        nearest_worker = None
                        nearest_distance = float('inf')
                        for survivor in survivor_group:
                            if survivor.role == "worker" and survivor.alive:
                                from world.survivor import SurvivorState
                                # Check if worker is idle or has no assigned node
                                if survivor.state == SurvivorState.IDLE or (
                                    hasattr(survivor, 'assigned_node') and survivor.assigned_node is None
                                ):
                                    distance = (survivor.pos - node.pos).length()
                                    if distance < nearest_distance:
                                        nearest_distance = distance
                                        nearest_worker = survivor
                        
                        if nearest_worker:
                            # Assign worker to node
                            nearest_worker.assign_gather(node)
                            sound_system.play("button_click")
                            print(f"Assigned worker to {node.TYPE_ID} at ({int(node.pos.x)}, {int(node.pos.y)})")
                        else:
                            print("No idle workers available")
                        break
                
                if clicked_node:
                    continue
                
                # Clicked on empty space in gather mode - do nothing (keep gather mode active)
                continue
            
            # Check if clicking on any button (handled above)
            clicked_button = False
            for building_class, button_data in buttons.items():
                if button_data['button'].rect.collidepoint(mouse_pos):
                    clicked_button = True
                    gather_mode = False  # Disable gather mode when entering build mode
                    break
            
            if clicked_button:
                continue
            
            if build_mode and selected_building_type:
                grid_pos = pixel_to_grid(mouse_pos)
                can_place = can_place_building(selected_building_type, grid_pos, grid, building_group)
                
                # Debug mode: Instant build (no cost, instant completion, no placement checks)
                if debug_system.is_active():
                    # Override all checks in debug mode
                    building_class_name = selected_building_type.__name__ if selected_building_type else "building"
                    building = create_building(selected_building_type, grid_pos, *buttons[selected_building_type]['args'])
                    if building:
                        building_group.add(building)
                        building.state = BuildState.ACTIVE
                        building.hp = building.max_hp
                        building.progress = building.BUILD_TIME
                        # Set world reference for walls
                        if hasattr(building, 'world'):
                            building.world = world
                        building.on_complete(world)
                        # If it's a wall, refresh neighbors after placement
                        if hasattr(building, 'on_place') and callable(building.on_place):
                            building.on_place(world)
                        # Force unblock then block (in case of overlap)
                        grid.set_footprint_blocked(grid_pos, selected_building_type.FOOTPRINT, False)
                        grid.set_footprint_blocked(grid_pos, selected_building_type.FOOTPRINT, True)
                        build_mode = False
                        print(f"Debug: Instant built {building_class_name} at {grid_pos}")
                        selected_building_type = None
                        sound_system.play("build_placed")
                elif can_place:
                    # Try to pay cost
                    if selected_building_type.pay_cost(resources):
                        # Create building
                        button_data = buttons[selected_building_type]
                        building = create_building(selected_building_type, grid_pos, *button_data['args'])
                        
                        if building:
                            building_group.add(building)
                            # Set world reference for walls
                            if hasattr(building, 'world'):
                                building.world = world
                            building.start_construction()
                            # Mark tiles as blocked
                            grid.set_footprint_blocked(grid_pos, selected_building_type.FOOTPRINT, True)
                            build_mode = False  # Exit build mode after placing
                            selected_building_type = None
                            pending_construction = building
                            sound_system.play("build_placed")
            else:
                # Try to select a building
                building_clicked = select_building(mouse_pos, building_group)
                if building_clicked:
                    # Building selected - show building panel
                    if selected_building:
                        building_panel.show(selected_building)
                        sound_system.play("button_click")
                else:
                    # No building clicked - deselect building and hide panel
                    deselect_building()
        
        # Handle right-click to dismiss panel and deselect building
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right mouse button
            # Skip if game over or paused
            if game_over_screen.is_visible or game_state_manager.is_paused():
                continue
            
            # Deselect building and hide panel on right-click
            deselect_building()
        
        # Handle keyboard input
        if event.type == pygame.KEYDOWN:
            # F12: Toggle debug mode (works even when paused/over - always accessible)
            if event.key == pygame.K_F12:
                debug_system.toggle()
                print(f"Debug mode: {'ON' if debug_system.is_active() else 'OFF'}")
                continue
            
            # Handle game over screen
            if game_over_screen.is_visible:
                if game_over_screen.handle_event(event):
                    continue
                continue
            
            # Handle pause menu
            if game_state_manager.is_paused():
                if pause_menu.handle_event(event):
                    continue
                # ESC to resume from pause menu
                if event.key == pygame.K_ESCAPE:
                    game_state_manager.resume()
                    pause_menu.hide()
                continue
            
            # Toggle gather mode (G key) - only when not paused
            if event.key == pygame.K_g:
                gather_mode = not gather_mode
                build_mode = False  # Disable build mode when entering gather mode
                selected_building_type = None
                if gather_mode:
                    print("Gather mode enabled - Click on nodes to assign workers")
                else:
                    print("Gather mode disabled")
                continue
            
            # ESC key handling (priority order)
            if event.key == pygame.K_ESCAPE:
                if gather_mode:
                    gather_mode = False
                    print("Gather mode disabled")
                    continue
                elif building_panel.is_visible:
                    deselect_building()
                    continue
                elif build_mode:
                    build_mode = False  # Exit build mode
                    selected_building_type = None
                    deselect_building()
                    continue
                elif pending_construction and pending_construction.state == BuildState.CONSTRUCTING:
                    # Cancel construction and refund 60%
                    pending_construction.refund_cost(resources, ratio=0.6)
                    grid.set_footprint_blocked((pending_construction.grid_x, pending_construction.grid_y), pending_construction.FOOTPRINT, False)
                    building_group.remove(pending_construction)
                    if pending_construction in turret_group:
                        turret_group.remove(pending_construction)
                    pending_construction = None
                    build_mode = False
                    selected_building_type = None
                    print("Construction cancelled - 60% refund")
                    continue
                else:
                    # Toggle pause
                    if game_state_manager.is_paused():
                        game_state_manager.resume()
                        pause_menu.hide()
                    else:
                        game_state_manager.pause()
                    continue
            
            # Handle debug actions (only when debug mode is active and not paused/over)
            if debug_system.is_active() and not game_over_screen.is_visible and not game_state_manager.is_paused():
                if event.key == pygame.K_F3:
                    # F3: Spawn zombie at current mouse position
                    debug_spawn_zombie_at_mouse(mouse_pos)
                    continue
                elif debug_system.handle_key(event.key):
                    # Debug action handled by debug system (F1, F2, F4-F8)
                    continue
                elif event.key == pygame.K_F9:
                    # F9: Skip to night
                    wave_manager.start_night()
                    recipe = wave_manager.get_wave_recipe()
                    spawn_config = waves_config["spawn"]
                    zombie_spawner.begin(recipe, spawn_config)
                    hud.show_event(f"Debug: Skipped to Night {wave_manager.night}", 3.0)
                    print(f"Debug: Skipped to night {wave_manager.night}")
                    continue
                elif event.key == pygame.K_F10:
                    # F10: Skip to summary
                    wave_manager.start_summary()
                    zombie_spawner.done = True
                    zombie_spawner.active = False
                    hud.show_event("Debug: Skipped to Summary", 3.0)
                    print("Debug: Skipped to summary")
                    continue
                elif event.key == pygame.K_F11:
                    # F11: Cycle difficulty
                    difficulties = ["easy", "normal", "hard"]
                    current_idx = difficulties.index(wave_manager.difficulty) if wave_manager.difficulty in difficulties else 1
                    next_idx = (current_idx + 1) % len(difficulties)
                    wave_manager.difficulty = difficulties[next_idx]
                    hud.show_event(f"Debug: Difficulty: {wave_manager.difficulty}", 3.0)
                    print(f"Debug: Difficulty changed to {wave_manager.difficulty}")
                    continue
            
            # Handle spacebar for testing (only when not paused/over)
            if event.key == pygame.K_SPACE and not game_over_screen.is_visible and not game_state_manager.is_paused():
                # Spawn a horde of zombies (for testing)
                zombie_spawner.spawn_horde(enemy_group, count=10, spread=200, enemy_class=BasicZombie)
                continue
    
    # Update display
    pygame.display.flip()

pygame.quit()
