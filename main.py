import pygame
import json
from typing import Dict
import constants as c
from world.buildings import BallisticTurret, GatlingTurret, PiercerTurret, HQ, Wall, Gate, Farm, Sawmill, Smelter, WallWood, WallIron
from world.enemies import BasicZombie, RunnerZombie, BruteZombie, SpitterZombie, SwarmlingZombie, Skeleton, ArcherSkeleton, WarriorSkeleton
from world.spawner import Spawner
from world.projectile import Projectile, ArrowProjectile, GatlingBullet, ZombieBullet
from world.buildings.piercer_turret import PiercingProjectile
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
from core.day_events import DayEventManager
# UI components
from ui.game_over import GameOverScreen
from ui.pause_menu import PauseMenu
from ui.building_panel import BuildingPanel
from ui.hud import HUD
from ui.research_button import ResearchButton
from ui.start_screen import StartScreen
<<<<<<< Updated upstream
from ui.difficulty_screen import SelectDifficultyScreen
=======
>>>>>>> Stashed changes
from research_tree import open_research_tree
from world.research import ResearchManager
from difficulty_config import Difficulty, DIFFICULTY_CONFIG
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
frame_width = 32 * c.ANIMATION_STEPS
turret_sheet_lv1 = load_image_or_placeholder(
    'asset/Turret_lv1.png',
    (frame_width, 32),
    (150, 150, 150, 255),
    "Ballistic turret sprite sheet Lv1"
)
turret_sheet_lv2 = load_image_or_placeholder(
    'asset/Turret_lv2.png',
    (frame_width, 32),
    (160, 150, 150, 255),
    "Ballistic turret sprite sheet Lv2"
)
turret_sheet_lv3 = load_image_or_placeholder(
    'asset/Turret_lv3.png',
    (frame_width, 32),
    (170, 150, 150, 255),
    "Ballistic turret sprite sheet Lv3"
)
turret_sprite_sheets = [turret_sheet_lv1, turret_sheet_lv2, turret_sheet_lv3]
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

# Railgun (Piercer) turret base images
railgun_base_lv1 = load_image_or_placeholder(
    'asset/Railgunbase_lv1.png',
    (32, 32),
    (120, 100, 100, 255),
    "Railgun turret base Lv1"
)
railgun_base_lv2 = load_image_or_placeholder(
    'asset/Railgunbase_lv2.png',
    (32, 32),
    (130, 110, 110, 255),
    "Railgun turret base Lv2"
)
railgun_base_lv3 = load_image_or_placeholder(
    'asset/Railgunbase_lv3.png',
    (32, 32),
    (140, 120, 120, 255),
    "Railgun turret base Lv3"
)
railgun_base_images = [railgun_base_lv1, railgun_base_lv2, railgun_base_lv3]

# Railgun (Piercer) turret sprite sheets (8 frames, 64x64 each)
railgun_frame_size = 64
railgun_sheet_width = railgun_frame_size * c.ANIMATION_STEPS  # 8 frames * 64 = 512
railgun_sheet_lv1 = load_image_or_placeholder(
    'asset/Railgunturret_lv1.png',
    (railgun_sheet_width, railgun_frame_size),
    (150, 100, 100, 255),
    "Railgun turret sprite sheet Lv1"
)
railgun_sheet_lv2 = load_image_or_placeholder(
    'asset/Railgunturret_lv2.png',
    (railgun_sheet_width, railgun_frame_size),
    (150, 100, 100, 255),
    "Railgun turret sprite sheet Lv2"
)
railgun_sheet_lv3 = load_image_or_placeholder(
    'asset/Railgunturret_lv3.png',
    (railgun_sheet_width, railgun_frame_size),
    (150, 100, 100, 255),
    "Railgun turret sprite sheet Lv3"
)
# Use lv1 for tier 1, lv2 for tier 2, and lv1 for tier 3 until lv3 is added
railgun_sprite_sheets = [railgun_sheet_lv1, railgun_sheet_lv2, railgun_sheet_lv3]

# Gatling turret images - try new tiwtir textures first, fallback to old
# Load all three tiers for Gatling turret
gatling_base_lv1 = load_image_or_placeholder(
    'asset/Tiwtir_gun_base_lv1.png',
    (64, 64),
    (120, 100, 80, 255),
    "Gatling turret base Lv1"
)
gatling_base_lv2 = load_image_or_placeholder(
    'asset/Tiwtir_gun_base_lv2.png',
    (64, 64),
    (120, 100, 80, 255),
    "Gatling turret base Lv2"
)
# Lv3 base is a sprite sheet with 4 frames (64x64 each) - 256x64 total
gatling_base_lv3 = load_image_or_placeholder(
    'asset/Tiwtir_gun_base_lv3.png',
    (256, 64),  # 4 frames * 64 = 256 pixels wide, 64 pixels tall
    (120, 100, 80, 255),
    "Gatling turret base Lv3 (sprite sheet)"
)
gatling_base_images = [gatling_base_lv1, gatling_base_lv2, gatling_base_lv3]

# Gatling turret sprite sheets (9 frames, 96x96 each)
gatling_frame_size = 96
gatling_sheet_width = gatling_frame_size * 9  # 9 frames * 96 = 864
gatling_sheet_lv1 = load_image_or_placeholder(
    'asset/Tiwtir_gun_turret_lv1.png',
    (gatling_sheet_width, gatling_frame_size),
    (180, 160, 140, 255),
    "Gatling turret sprite sheet Lv1"
)
gatling_sheet_lv2 = load_image_or_placeholder(
    'asset/Tiwtir_gun_turret_lv2.png',
    (gatling_sheet_width, gatling_frame_size),
    (180, 160, 140, 255),
    "Gatling turret sprite sheet Lv2"
)
gatling_sheet_lv3 = load_image_or_placeholder(
    'asset/Tiwtir_gun_turret_lv3.png',
    (gatling_sheet_width, gatling_frame_size),
    (180, 160, 140, 255),
    "Gatling turret sprite sheet Lv3"
)
gatling_sprite_sheets = [gatling_sheet_lv1, gatling_sheet_lv2, gatling_sheet_lv3]

# Backward compatibility - use lv1 for old code paths
gatling_image = None
gatling_turret_sheet = gatling_sheet_lv1  # Default to lv1
gatling_base = gatling_base_lv1  # Default to lv1

# Zombie sprite sheets (32 frames, 48x48 each)
zombie_sprite_sheet = load_image_or_placeholder(
    'asset/Zombie_Normal_Sheet.png',
    (48 * 32, 48),  # 32 frames * 48 pixels = 1536 pixels wide, 48 pixels tall
    (100, 150, 100, 255),
    "Zombie Normal sprite sheet"
)

runner_sprite_sheet = load_image_or_placeholder(
    'asset/Zombie_Runner_Sheet.png',
    (48 * 32, 48),  # 32 frames * 48 pixels = 1536 pixels wide, 48 pixels tall
    (200, 150, 50, 255),
    "Zombie Runner sprite sheet"
)

brute_sprite_sheet = load_image_or_placeholder(
    'asset/Zombie_Brute_Sheet.png',
    (48 * 32, 48),  # 32 frames * 48 pixels = 1536 pixels wide, 48 pixels tall
    (100, 30, 30, 255),
    "Zombie Brute sprite sheet"
)

# Swarmling zombie sprite sheet (32 frames, 48x48 each)
# Note: Individual frames will be scaled to 0.8 in the SwarmlingZombie class
swarmling_sprite_sheet = load_image_or_placeholder(
    'asset/Zombie_Swarmling-Sheet.png',
    (48 * 32, 48),  # 32 frames * 48 pixels = 1536 pixels wide, 48 pixels tall
    (120, 100, 80, 255),
    "Zombie Swarmling sprite sheet"
)

# Spitter zombie sprite sheet (31 frames, 64x64 each)
spitter_sprite_sheet = load_image_or_placeholder(
    'asset/Pumpkinhead/Pumpkinhead-Sheet.png',
    (64 * 31, 64),  # 31 frames * 64 pixels = 1984 pixels wide, 64 pixels tall
    (100, 50, 150, 255),
    "Spitter zombie sprite sheet"
)

# Set sprite sheets for zombie classes
BasicZombie.sprite_sheet = zombie_sprite_sheet
RunnerZombie.sprite_sheet = runner_sprite_sheet
BruteZombie.sprite_sheet = brute_sprite_sheet
SwarmlingZombie.sprite_sheet = swarmling_sprite_sheet
SpitterZombie.sprite_sheet = spitter_sprite_sheet

# Skeleton sprite sheet (40 frames, 48x48 each)
skeleton_sprite_sheet = load_image_or_placeholder(
    'asset/NormalSkeleton_Sheet.png',
    (48 * 40, 48),  # 40 frames * 48 pixels = 1920 pixels wide, 48 pixels tall
    (200, 200, 200, 255),
    "Skeleton sprite sheet"
)

# Set sprite sheet for Skeleton class
Skeleton.sprite_sheet = skeleton_sprite_sheet

# Archer Skeleton sprite sheet (34 frames, 48x48 each)
archer_skeleton_sprite_sheet = load_image_or_placeholder(
    'asset/ArcherSkeleton_Sheet.png',
    (48 * 34, 48),  # 34 frames * 48 pixels = 1632 pixels wide, 48 pixels tall
    (200, 200, 200, 255),
    "Archer Skeleton sprite sheet"
)

# Set sprite sheet for ArcherSkeleton class
ArcherSkeleton.sprite_sheet = archer_skeleton_sprite_sheet

# Arrow Projectile sprite sheet (4 frames, 16x16 each)
arrow_projectile_sheet = load_image_or_placeholder(
    'asset/ArrowProjectile.png',
    (16 * 4, 16),  # 4 frames * 16 pixels = 64 pixels wide, 16 pixels tall
    (255, 255, 0, 255),
    "Arrow Projectile sprite sheet"
)

# Set sprite sheet for ArrowProjectile class
ArrowProjectile.sprite_sheet = arrow_projectile_sheet

# Ballistic Bullet sprite sheet (4 frames, 16x16 each)
ballistic_bullet_sheet = load_image_or_placeholder(
    'asset\Balisticbullet-Sheet.png',
    (16 * 4, 16),  # 4 frames * 16 pixels = 64 pixels wide, 16 pixels tall
    (255, 200, 0, 255),
    "Ballistic Bullet sprite sheet"
)

# Set sprite sheet for Projectile class (base projectile used by ballistic turrets)
Projectile.sprite_sheet = ballistic_bullet_sheet

# Gatling (Tiwtir) Bullet sprite sheet (4 frames, 16x16 each)
gatling_bullet_sheet = load_image_or_placeholder(
    'asset\Tiwtirbullet-Sheet.png',
    (16 * 4, 16),  # 4 frames * 16 pixels = 64 pixels wide, 16 pixels tall
    (255, 150, 0, 255),
    "Gatling Bullet sprite sheet"
)

# Railgun Bullet sprite sheet (4 frames, 16x16 each)
railgun_bullet_sheet = load_image_or_placeholder(
    'asset\Railgunbullet-Sheet.png',
    (16 * 4, 16),  # 4 frames * 16 pixels = 64 pixels wide, 16 pixels tall
    (200, 100, 255, 255),
    "Railgun Bullet sprite sheet"
)

# Zombie Bullet sprite sheet (4 frames, 16x16 each)
zombie_bullet_sheet = load_image_or_placeholder(
    'asset\Zombiebullet-Sheet.png',
    (16 * 4, 16),  # 4 frames * 16 pixels = 64 pixels wide, 16 pixels tall
    (150, 50, 50, 255),
    "Zombie Bullet sprite sheet"
)

# Set sprite sheets for projectile classes
GatlingBullet.sprite_sheet = gatling_bullet_sheet
PiercingProjectile.sprite_sheet = railgun_bullet_sheet
ZombieBullet.sprite_sheet = zombie_bullet_sheet

# Warrior Skeleton sprite sheet (46 frames, 48x48 each)
warrior_skeleton_sprite_sheet = load_image_or_placeholder(
    'asset/WarriorSkeleton_Sheet.png',
    (48 * 46, 48),  # 46 frames * 48 pixels = 2208 pixels wide, 48 pixels tall
    (200, 200, 200, 255),
    "Warrior Skeleton sprite sheet"
)

# Set sprite sheet for WarriorSkeleton class
WarriorSkeleton.sprite_sheet = warrior_skeleton_sprite_sheet

# Day counter sprite sheet (6 frames, 256x128 each)
daycounter_sheet = load_image_or_placeholder(
    'asset/hud/Daycounter-Sheet.png',
    (256 * 6, 128),  # 6 frames * 256 pixels = 1536 pixels wide, 128 pixels tall
    (100, 100, 100, 255),
    "Day counter sprite sheet"
)
# Extract 6 frames from the sheet
daycounter_frames = []
if daycounter_sheet:
    frame_width = 256
    frame_height = 128
    for i in range(6):
        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        if frame_rect.right <= daycounter_sheet.get_width():
            frame = daycounter_sheet.subsurface(frame_rect)
            daycounter_frames.append(frame)
        else:
            # If frame doesn't exist, use first frame as fallback
            if daycounter_frames:
                daycounter_frames.append(daycounter_frames[0])
            else:
                # Create placeholder if no frames available
                placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                placeholder.fill((100, 100, 100, 255))
                daycounter_frames.append(placeholder)
else:
    # Create placeholder frames if sheet not loaded
    for i in range(6):
        placeholder = pygame.Surface((256, 128), pygame.SRCALPHA)
        placeholder.fill((100, 100, 100, 255))
        daycounter_frames.append(placeholder)

# HQ building image
hq_image = load_image_or_placeholder(
    'asset/base.png',
    (64, 64),  # 2x2 tile building
    (50, 100, 150, 255),
    "HQ building image"
)

# Set image for HQ class
HQ.building_image = hq_image

# Upgrade panel image - extract 3 frames (384x386 each) - for upgrade progress indicator
upgrade_panel_sheet = load_image_or_placeholder(
    'asset/upgrade_1-2_panel.png',
    (384 * 3, 386),  # 3 frames * 384 pixels = 1152 pixels wide, 386 pixels tall
    (100, 100, 100, 255),
    "Upgrade panel sprite sheet"
)
# Extract 3 frames from the sheet
upgrade_panel_frames = []
if upgrade_panel_sheet:
    frame_width = 384
    frame_height = 386
    for i in range(3):
        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        frame = upgrade_panel_sheet.subsurface(frame_rect)
        upgrade_panel_frames.append(frame)

# Upgrade panel darkened image - extract 3 frames (384x386 each)
upgrade_panel_darken_sheet = load_image_or_placeholder(
    'asset/upgrade_1-2_panel_darken.png',
    (384 * 3, 386),  # 3 frames * 384 pixels = 1152 pixels wide, 386 pixels tall
    (100, 100, 100, 255),
    "Upgrade panel darkened sprite sheet"
)
# Extract 3 frames from the darkened sheet
upgrade_panel_darken_frames = []
if upgrade_panel_darken_sheet:
    frame_width = 384
    frame_height = 386
    for i in range(3):
        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        frame = upgrade_panel_darken_sheet.subsurface(frame_rect)
        upgrade_panel_darken_frames.append(frame)

# New upgrade panel sheet for building detail panel background - extract 3 frames (497x742 each)
# Scale factor for making panel bigger (1.2x - slightly bigger than original)
PANEL_SCALE = 1.2
building_panel_sheet = load_image_or_placeholder(
    'asset/upgrade_panel_Sheet.png',
    (497 * 3, 742),  # 3 frames * 497 pixels = 1491 pixels wide, 742 pixels tall
    (50, 50, 50, 255),
    "Building detail panel background sheet"
)
# Extract 3 frames from the sheet and scale them up
building_panel_frames = []
if building_panel_sheet:
    frame_width = 497
    frame_height = 742
    scaled_width = int(frame_width * PANEL_SCALE)
    scaled_height = int(frame_height * PANEL_SCALE)
    for i in range(3):
        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        if frame_rect.right <= building_panel_sheet.get_width():
            frame = building_panel_sheet.subsurface(frame_rect)
            # Scale the frame up
            scaled_frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
            building_panel_frames.append(scaled_frame)
        else:
            # If frame doesn't exist, use first frame as fallback
            if building_panel_frames:
                building_panel_frames.append(building_panel_frames[0])
            else:
                # Create placeholder if no frames available
                placeholder = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                placeholder.fill((50, 50, 50, 255))
                building_panel_frames.append(placeholder)
else:
    # Create placeholder frames if sheet not loaded
    scaled_width = int(497 * PANEL_SCALE)
    scaled_height = int(742 * PANEL_SCALE)
    for i in range(3):
        placeholder = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        placeholder.fill((50, 50, 50, 255))
        building_panel_frames.append(placeholder)

# Grass tile images (day and night variants)
def load_grass_variants(sheet_path, default_color=(50, 100, 50)):
    """Load grass tile variants from a sheet. Returns list of 3 variants."""
    try:
        import os
        if not os.path.exists(sheet_path):
            print(f"Warning: {sheet_path} does not exist, using placeholder")
            placeholder = pygame.Surface((32, 32))
            placeholder.fill(default_color)
            return [placeholder, placeholder, placeholder]
        
        grass_sheet = pygame.image.load(sheet_path).convert_alpha()
        sheet_width, sheet_height = grass_sheet.get_size()
        print(f"Loaded {sheet_path}: {sheet_width}x{sheet_height}")
        
        variants = []
        if sheet_width >= 96 and sheet_height == 32:
            # Image contains 3 horizontal tiles (96x32 = 3*32x32)
            print(f"  Detected horizontal layout: extracting 3 tiles")
            for i in range(3):
                variant = grass_sheet.subsurface((i * 32, 0, 32, 32))
                variants.append(variant)
        elif sheet_width == 32 and sheet_height >= 96:
            # Image contains 3 vertical tiles (32x96 = 3*32x32)
            print(f"  Detected vertical layout: extracting 3 tiles")
            for i in range(3):
                variant = grass_sheet.subsurface((0, i * 32, 32, 32))
                variants.append(variant)
        elif sheet_width == 32 and sheet_height == 32:
            # Single tile - use it for all 3 variants
            print(f"  Detected single tile: using for all 3 variants")
            variants = [grass_sheet, grass_sheet, grass_sheet]
        else:
            # Try to extract tiles based on actual dimensions
            print(f"  Unknown format {sheet_width}x{sheet_height}, attempting extraction")
            # Try horizontal first
            if sheet_width >= 32 and sheet_height >= 32:
                num_horizontal = sheet_width // 32
                if num_horizontal >= 3:
                    for i in range(3):
                        if i * 32 < sheet_width:
                            variant = grass_sheet.subsurface((i * 32, 0, 32, 32))
                            variants.append(variant)
                # Try vertical if horizontal didn't work
                elif sheet_height >= 96:
                    for i in range(3):
                        if i * 32 < sheet_height:
                            variant = grass_sheet.subsurface((0, i * 32, 32, 32))
                            variants.append(variant)
                # Last resort: extract first 32x32 tile and use for all
                if not variants:
                    tile = grass_sheet.subsurface((0, 0, min(32, sheet_width), min(32, sheet_height)))
                    # Scale to 32x32 if needed
                    if tile.get_size() != (32, 32):
                        tile = pygame.transform.scale(tile, (32, 32))
                    variants = [tile, tile, tile]
        
        # Ensure we have exactly 3 variants
        while len(variants) < 3:
            if variants:
                variants.append(variants[0])
            else:
                placeholder = pygame.Surface((32, 32))
                placeholder.fill(default_color)
                variants.append(placeholder)
        
        print(f"  Successfully loaded {len(variants)} variants")
        return variants[:3]  # Return exactly 3
    except Exception as e:
        # Create placeholder grass tiles if file doesn't exist
        import traceback
        print(f"Warning: {sheet_path} error loading: {e}")
        print(traceback.format_exc())
        placeholder = pygame.Surface((32, 32))
        placeholder.fill(default_color)
        return [placeholder, placeholder, placeholder]

# Load day grass tiles
grass_tiles_day = load_grass_variants('asset/Grass_tile.png', (50, 100, 50))

# Load night grass tiles
grass_tiles_night = load_grass_variants('asset/Grassnight_tile.png', (30, 50, 30))

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
resources = Resources(wood=0, iron=0, food=0, coins=0)
current_difficulty = Difficulty.EASY

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
    "swarmling": SwarmlingZombie,
    "skeleton": Skeleton,
    "archer_skeleton": ArcherSkeleton,
    "warrior_skeleton": WarriorSkeleton
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
        
        # Day event modifiers (initialized to neutral values)
        self.modifiers = {
            "resource_prod_mult": 1.0,
            "coin_drop_mult": 1.0,
            "build_cost_mult": 1.0,
            "turret_fire_rate_mult": 1.0,
            "building_damage_taken_mult": 1.0,
            "zombie_spawn_mult": 1.0,
            "zombie_speed_mult": 1.0,
            "zombie_hp_mult": 1.0,
            "turret_range_mult": 1.0,
            "node_spawn_bonus": False,
            "lightning_storm": False,
        }
        
        # Day event manager (will be set after initialization)
        self.day_events = None
        self.hud = None
        self.nodes = node_group if node_group else pygame.sprite.Group()
        self.survivor_group = survivor_group if survivor_group else pygame.sprite.Group()
<<<<<<< Updated upstream
        self.production_multipliers = {"sawmill": 1.0, "smelter": 1.0}
        self.current_difficulty = Difficulty.EASY
        self.sawmill_level = 0
=======
>>>>>>> Stashed changes
        self.buildings_by_type: Dict[str, list] = {}
    
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

    # ----- Building registry helpers -----
    def register_building(self, building):
        type_id = getattr(building, "TYPE_ID", building.__class__.__name__.lower())
        type_id = type_id.lower()
        self.buildings_by_type.setdefault(type_id, []).append(building)

    def unregister_building(self, building):
        type_id = getattr(building, "TYPE_ID", building.__class__.__name__.lower()).lower()
        if type_id in self.buildings_by_type:
            try:
                self.buildings_by_type[type_id].remove(building)
                if not self.buildings_by_type[type_id]:
                    del self.buildings_by_type[type_id]
            except ValueError:
                pass

    def upgrade_buildings(self, type_id: str, new_level: int):
        type_id = type_id.lower()
        for building in self.buildings_by_type.get(type_id, []):
            building.upgrade_level(new_level)

# Initialize core systems first
game_state_manager = GameStateManager()
# Start in menu state
game_state_manager.set_state(GameState.MENU)
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

# Initialize research system (needed before building buttons)
research_manager = ResearchManager(world)
world.research = research_manager

# Initialize wave manager
wave_manager = WaveManager(world, waves_config, difficulty="normal")
# Update world with wave_manager reference
world.wave_manager = wave_manager

# Initialize UI components
hud = HUD(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, daycounter_frames)
# Set HUD reference in world for day events
world.hud = hud

# Initialize day event manager
day_event_manager = DayEventManager(world)
world.day_events = day_event_manager
game_over_screen = GameOverScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
pause_menu = PauseMenu(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
start_screen = StartScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
difficulty_screen = SelectDifficultyScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
building_panel = BuildingPanel(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, upgrade_panel_frames, upgrade_panel_darken_frames, building_panel_frames)


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
    """Spawn starting layout: HQ in center, walls surrounding it, gate, and turrets outside"""
    global building_group, grid, turret_group, world
    
    TILE = grid.TILE
    W_TILES = grid.width
    H_TILES = grid.height
    
    # Center of screen
    center_x = W_TILES // 2
    center_y = H_TILES // 2
    
    # Import building classes
    from world.buildings.wall_wood import WallWood
    from world.buildings.gate import Gate
    
    # --- Wall compound dimensions (15x8 rectangle) ---
    compound_width = 15  # 15 tiles wide
    compound_height = 8  # 8 tiles high
    
    # Center the compound on screen
    compound_left = center_x - compound_width // 2
    compound_right = compound_left + compound_width - 1
    compound_top = center_y - compound_height // 2
    compound_bottom = compound_top + compound_height - 1
    
    # Ensure compound fits on screen (adjust if needed, but keep symmetric)
    if compound_left < 2:
        offset = 2 - compound_left
        compound_left += offset
        compound_right += offset
    if compound_right >= W_TILES - 2:
        offset = (W_TILES - 2) - compound_right
        compound_left += offset
        compound_right += offset
    if compound_top < 2:
        offset = 2 - compound_top
        compound_top += offset
        compound_bottom += offset
    if compound_bottom >= H_TILES - 2:
        offset = (H_TILES - 2) - compound_bottom
        compound_top += offset
        compound_bottom += offset
    
    # --- HQ placement (centered in compound) ---
    # Place HQ in the center of the compound
    hq_w, hq_h = HQ.FOOTPRINT
    hq_gx = compound_left + (compound_width - hq_w) // 2
    hq_gy = compound_top + (compound_height - hq_h) // 2
    
    hq = HQ((hq_gx, hq_gy), tier=1)
    building_group.add(hq)
    world.register_building(hq)
    grid.set_footprint_blocked((hq_gx, hq_gy), HQ.FOOTPRINT, True)
    
    # Store HQ reference in world
    if 'world' in globals():
        world.hq = hq
    
    print(f"HQ spawned at grid position ({hq_gx}, {hq_gy}) - center")
    print(f"Compound: left={compound_left}, right={compound_right}, top={compound_top}, bottom={compound_bottom}")
    
    # --- Place walls surrounding HQ ---
    walls_placed = []
    
    # Top wall
    for gx in range(compound_left, compound_right + 1):
        if 0 <= gx < W_TILES and 0 <= compound_top < H_TILES:
            w = WallWood((gx, compound_top), tier=1)
            w.state = BuildState.ACTIVE
            w.hp = w.max_hp
            w.progress = w.BUILD_TIME
            w.world = world
            building_group.add(w)
            world.register_building(w)
            grid.set_footprint_blocked((gx, compound_top), WallWood.FOOTPRINT, True)
            walls_placed.append((gx, compound_top))
    
    # Bottom wall
    for gx in range(compound_left, compound_right + 1):
        if 0 <= gx < W_TILES and 0 <= compound_bottom < H_TILES:
            w = WallWood((gx, compound_bottom), tier=1)
            w.state = BuildState.ACTIVE
            w.hp = w.max_hp
            w.progress = w.BUILD_TIME
            w.world = world
            building_group.add(w)
            world.register_building(w)
            grid.set_footprint_blocked((gx, compound_bottom), WallWood.FOOTPRINT, True)
            walls_placed.append((gx, compound_bottom))
    
    # Left wall (excluding corners already placed)
    for gy in range(compound_top + 1, compound_bottom):
        if 0 <= compound_left < W_TILES and 0 <= gy < H_TILES:
            w = WallWood((compound_left, gy), tier=1)
            w.state = BuildState.ACTIVE
            w.hp = w.max_hp
            w.progress = w.BUILD_TIME
            w.world = world
            building_group.add(w)
            world.register_building(w)
            grid.set_footprint_blocked((compound_left, gy), WallWood.FOOTPRINT, True)
            walls_placed.append((compound_left, gy))
    
    # Right wall (excluding corners already placed)
    for gy in range(compound_top + 1, compound_bottom):
        if 0 <= compound_right < W_TILES and 0 <= gy < H_TILES:
            w = WallWood((compound_right, gy), tier=1)
            w.state = BuildState.ACTIVE
            w.hp = w.max_hp
            w.progress = w.BUILD_TIME
            w.world = world
            building_group.add(w)
            world.register_building(w)
            grid.set_footprint_blocked((compound_right, gy), WallWood.FOOTPRINT, True)
            walls_placed.append((compound_right, gy))
    
    # After all walls are placed, refresh all wall variants so they see their neighbors
    for gx, gy in walls_placed:
        world.autotile_wall_and_neighbors(gx, gy)
    
    print(f"Walls placed: {len(walls_placed)} segments forming compound")
    
    # --- Place gate (bottom side, center) ---
    gate_gx = center_x
    gate_gy = compound_bottom
    if 0 <= gate_gx < W_TILES and 0 <= gate_gy < H_TILES:
        # Remove wall at gate position if it exists
        for gx, gy in walls_placed[:]:
            if gx == gate_gx and gy == gate_gy:
                # Find and remove the wall building
                for building in building_group:
                    if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                        building.grid_x == gate_gx and building.grid_y == gate_gy and
                        isinstance(building, WallWood)):
                        world.unregister_building(building)
                        building_group.remove(building)
                        grid.set_footprint_blocked((gate_gx, gate_gy), WallWood.FOOTPRINT, False)
                        walls_placed.remove((gate_gx, gate_gy))
                        break
        
        g = Gate((gate_gx, gate_gy), tier=1)
        g.state = BuildState.ACTIVE
        g.hp = g.max_hp
        g.progress = g.BUILD_TIME
        building_group.add(g)
        world.register_building(g)
        grid.set_footprint_blocked((gate_gx, gate_gy), Gate.FOOTPRINT, True)
        print(f"Gate placed at ({gate_gx}, {gate_gy})")
    
    # --- Place turrets outside walls ---
    global turret_sprite_sheets, turret_base_images
    
    # Turret positions outside the compound (one tile away from walls)
    turret_offset = 2  # tiles outside the wall
    
    # Top turrets
    for dx in [-3, 0, 3]:
        turret_gx = center_x + dx
        turret_gy = compound_top - turret_offset
        if 0 <= turret_gx < W_TILES and 0 <= turret_gy < H_TILES:
            t = BallisticTurret((turret_gx, turret_gy), turret_sprite_sheets, turret_base_images, tier=1)
            t.state = BuildState.ACTIVE
            t.hp = t.max_hp
            t.progress = t.BUILD_TIME
            building_group.add(t)
            world.register_building(t)
            turret_group.add(t)
            grid.set_footprint_blocked((turret_gx, turret_gy), BallisticTurret.FOOTPRINT, True)
            print(f"Turret placed at ({turret_gx}, {turret_gy}) - top")
    
    # Bottom turrets (avoid gate area)
    for dx in [-4, 4]:
        turret_gx = center_x + dx
        turret_gy = compound_bottom + turret_offset
        if 0 <= turret_gx < W_TILES and 0 <= turret_gy < H_TILES:
            t = BallisticTurret((turret_gx, turret_gy), turret_sprite_sheets, turret_base_images, tier=1)
            t.state = BuildState.ACTIVE
            t.hp = t.max_hp
            t.progress = t.BUILD_TIME
            building_group.add(t)
            world.register_building(t)
            turret_group.add(t)
            grid.set_footprint_blocked((turret_gx, turret_gy), BallisticTurret.FOOTPRINT, True)
            print(f"Turret placed at ({turret_gx}, {turret_gy}) - bottom")
    
    # Side turrets
    turret_gx = compound_left - turret_offset
    turret_gy = center_y
    if 0 <= turret_gx < W_TILES and 0 <= turret_gy < H_TILES:
        t = BallisticTurret((turret_gx, turret_gy), turret_sprite_sheets, turret_base_images, tier=1)
        t.state = BuildState.ACTIVE
        t.hp = t.max_hp
        t.progress = t.BUILD_TIME
        building_group.add(t)
        world.register_building(t)
        turret_group.add(t)
        grid.set_footprint_blocked((turret_gx, turret_gy), BallisticTurret.FOOTPRINT, True)
        print(f"Turret placed at ({turret_gx}, {turret_gy}) - left")
    
    turret_gx = compound_right + turret_offset
    turret_gy = center_y
    if 0 <= turret_gx < W_TILES and 0 <= turret_gy < H_TILES:
        t = BallisticTurret((turret_gx, turret_gy), turret_sprite_sheets, turret_base_images, tier=1)
        t.state = BuildState.ACTIVE
        t.hp = t.max_hp
        t.progress = t.BUILD_TIME
        building_group.add(t)
        world.register_building(t)
        turret_group.add(t)
        grid.set_footprint_blocked((turret_gx, turret_gy), BallisticTurret.FOOTPRINT, True)
        print(f"Turret placed at ({turret_gx}, {turret_gy}) - right")
    
    print(f"Starting layout spawned: HQ at center ({hq_gx}, {hq_gy}), walls surrounding, gate at bottom, turrets outside")
    
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
        worker = Worker(worker_pos, world=world)
        survivor_group.add(worker)
    
    print(f"Spawned {3} workers near HQ")

def spawn_daily_resource_nodes():
    """Spawn daily resource nodes in clusters around the starting structure"""
    global node_group, world, grid, building_group
    
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
    
    # Find HQ and calculate actual compound bounds from walls
    hq_pos = None
    compound_bounds = None
    TILE = 32
    
    # Find walls to determine compound bounds
    wall_positions = []
    for building in building_group:
        if isinstance(building, HQ):
            hq_pos = (building.grid_x, building.grid_y)
        # Check for walls (WallWood, WallIron, or Wall)
        from world.buildings.wall_wood import WallWood
        from world.buildings.wall_iron import WallIron
        if isinstance(building, (WallWood, WallIron, Wall)):
            if hasattr(building, 'grid_x') and hasattr(building, 'grid_y'):
                wall_positions.append((building.grid_x, building.grid_y))
    
    if not hq_pos:
        # Fallback to upper zone if HQ not found
        upper_zone_rect = pygame.Rect(0, 0, c.SCREEN_WIDTH, c.SCREEN_HEIGHT // 3)
        new_nodes = spawn_daily_nodes(world, nodes_config, upper_zone_rect, grid)
        for node in new_nodes:
            node_group.add(node)
        print(f"Spawned {len(new_nodes)} resource nodes in upper zone (fallback)")
        return
    
    # Calculate compound bounds from walls (in grid coordinates)
    if wall_positions:
        min_wall_x = min(gx for gx, gy in wall_positions)
        max_wall_x = max(gx for gx, gy in wall_positions)
        min_wall_y = min(gy for gx, gy in wall_positions)
        max_wall_y = max(gy for gx, gy in wall_positions)
        
        # Add padding to get outside the walls
        compound_bounds = {
            'left': min_wall_x - 1,
            'right': max_wall_x + 1,
            'top': min_wall_y - 1,
            'bottom': max_wall_y + 1
        }
    else:
        # Fallback: estimate from HQ
        for building in building_group:
            if isinstance(building, HQ):
                compound_bounds = {
                    'left': building.grid_x - 8,
                    'right': building.grid_x + building.FOOTPRINT[0] + 8,
                    'top': building.grid_y - 8,
                    'bottom': building.grid_y + building.FOOTPRINT[1] + 8
                }
                break
    
    # Get daily spawn config
    daily_spawn = nodes_config.get("daily_spawn", {"trees": 4, "scrap": 3, "min_dist_from_wall_px": 96})
    num_trees = daily_spawn.get("trees", 4)
    num_scrap = daily_spawn.get("scrap", 3)
    
    # Apply node spawn bonus from day events
    if hasattr(world, 'modifiers') and world.modifiers.get("node_spawn_bonus", False):
        num_trees += 2  # Bonus trees
        num_scrap += 2  # Bonus scrap
    
    # Load node configs
    tree_config = None
    scrap_config = None
    try:
        tree_data = nodes_config.get("tree_patch", {})
        from world.nodes import NodeConfig
        tree_config = NodeConfig(
            resource=tree_data.get("resource", "wood"),
            yield_total=tree_data.get("yield_total", 120),
            gather_per_tick=tree_data.get("gather_per_tick", 6),
            tick_sec=tree_data.get("tick_sec", 0.6)
        )
        scrap_data = nodes_config.get("scrap_pile", {})
        scrap_config = NodeConfig(
            resource=scrap_data.get("resource", "iron"),
            yield_total=scrap_data.get("yield_total", 100),
            gather_per_tick=scrap_data.get("gather_per_tick", 5),
            tick_sec=scrap_data.get("tick_sec", 0.7)
        )
    except:
        pass
    
    new_nodes = []
    
    # Define cluster areas around the compound (4 quadrants + corners)
    # Each cluster will have nodes of the same type
    # Convert grid positions to pixel positions for cluster centers
    cluster_distance = 10  # tiles from compound edge
    cluster_areas = [
        # Top-left cluster (trees) - in pixels
        {'center_px': ((compound_bounds['left'] - cluster_distance) * TILE, 
                       (compound_bounds['top'] - cluster_distance) * TILE), 
         'radius_px': 80, 'type': 'tree'},
        # Top-right cluster (scrap)
        {'center_px': ((compound_bounds['right'] + cluster_distance) * TILE, 
                       (compound_bounds['top'] - cluster_distance) * TILE), 
         'radius_px': 80, 'type': 'scrap'},
        # Bottom-left cluster (scrap)
        {'center_px': ((compound_bounds['left'] - cluster_distance) * TILE, 
                       (compound_bounds['bottom'] + cluster_distance) * TILE), 
         'radius_px': 80, 'type': 'scrap'},
        # Bottom-right cluster (trees)
        {'center_px': ((compound_bounds['right'] + cluster_distance) * TILE, 
                       (compound_bounds['bottom'] + cluster_distance) * TILE), 
         'radius_px': 80, 'type': 'tree'},
    ]
    
    # Spawn nodes in clusters
    import random
    from world.nodes import TreePatch, ScrapPile
    
    trees_spawned = 0
    scrap_spawned = 0
    
    for cluster in cluster_areas:
        cluster_x_px, cluster_y_px = cluster['center_px']
        radius_px = cluster['radius_px']
        cluster_type = cluster['type']
        
        # Determine how many nodes to spawn in this cluster
        if cluster_type == 'tree' and trees_spawned < num_trees:
            nodes_in_cluster = min(2, num_trees - trees_spawned)  # 2 nodes per tree cluster
        elif cluster_type == 'scrap' and scrap_spawned < num_scrap:
            nodes_in_cluster = min(2, num_scrap - scrap_spawned)  # 2 nodes per scrap cluster
        else:
            continue
        
        for _ in range(nodes_in_cluster):
            # Try to find a valid position in the cluster (in pixels)
            for attempt in range(30):
                offset_x_px = random.randint(-radius_px, radius_px)
                offset_y_px = random.randint(-radius_px, radius_px)
                node_x_px = cluster_x_px + offset_x_px
                node_y_px = cluster_y_px + offset_y_px
                
                # Convert to grid for collision checking
                node_gx = int(node_x_px // TILE)
                node_gy = int(node_y_px // TILE)
                
                # Ensure position is valid and not too close to compound
                if (0 <= node_gx < grid.width and 0 <= node_gy < grid.height and
                    not grid.is_blocked(node_gx, node_gy) and
                    (node_gx < compound_bounds['left'] - 2 or node_gx > compound_bounds['right'] + 2 or
                     node_gy < compound_bounds['top'] - 2 or node_gy > compound_bounds['bottom'] + 2)):
                    
                    # Check distance from existing nodes (using pixel positions)
                    too_close = False
                    node_pos = pygame.Vector2(node_x_px, node_y_px)
                    min_node_dist = 96  # 3 tiles in pixels
                    for existing_node in list(node_group) + new_nodes:
                        if hasattr(existing_node, 'pos'):
                            dist = (node_pos - existing_node.pos).length()
                            if dist < min_node_dist:
                                too_close = True
                                break
                    
                    if not too_close:
                        # Spawn the node using pixel position
                        # Note: TreePatch automatically picks a random texture variant on creation
                        if cluster_type == 'tree' and tree_config:
                            node = TreePatch((node_x_px, node_y_px), tree_config)
                            new_nodes.append(node)
                            trees_spawned += 1
                            break
                        elif cluster_type == 'scrap' and scrap_config:
                            node = ScrapPile((node_x_px, node_y_px), scrap_config)
                            new_nodes.append(node)
                            scrap_spawned += 1
                            break
    
    # Add remaining nodes randomly around the compound if we didn't spawn enough
    if trees_spawned < num_trees:
        remaining = num_trees - trees_spawned
        for _ in range(remaining * 20):  # Try multiple times
            if trees_spawned >= num_trees:
                break
            # Random position around compound (in pixels)
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                node_x_px = random.randint((compound_bounds['left'] - 10) * TILE, 
                                           (compound_bounds['right'] + 10) * TILE)
                node_y_px = (compound_bounds['top'] - random.randint(5, 15)) * TILE
            elif side == 'bottom':
                node_x_px = random.randint((compound_bounds['left'] - 10) * TILE, 
                                           (compound_bounds['right'] + 10) * TILE)
                node_y_px = (compound_bounds['bottom'] + random.randint(5, 15)) * TILE
            elif side == 'left':
                node_x_px = (compound_bounds['left'] - random.randint(5, 15)) * TILE
                node_y_px = random.randint((compound_bounds['top'] - 10) * TILE, 
                                           (compound_bounds['bottom'] + 10) * TILE)
            else:  # right
                node_x_px = (compound_bounds['right'] + random.randint(5, 15)) * TILE
                node_y_px = random.randint((compound_bounds['top'] - 10) * TILE, 
                                           (compound_bounds['bottom'] + 10) * TILE)
            
            node_gx = int(node_x_px // TILE)
            node_gy = int(node_y_px // TILE)
            
            if (0 <= node_gx < grid.width and 0 <= node_gy < grid.height and
                not grid.is_blocked(node_gx, node_gy)):
                # Check distance from existing nodes (using pixel positions)
                too_close = False
                node_pos = pygame.Vector2(node_x_px, node_y_px)
                min_node_dist = 96  # 3 tiles in pixels
                for existing_node in list(node_group) + new_nodes:
                    if hasattr(existing_node, 'pos'):
                        dist = (node_pos - existing_node.pos).length()
                        if dist < min_node_dist:
                            too_close = True
                            break
                if not too_close and tree_config:
                    # TreePatch automatically uses random texture variant
                    node = TreePatch((node_x_px, node_y_px), tree_config)
                    new_nodes.append(node)
                    trees_spawned += 1
    
    if scrap_spawned < num_scrap:
        remaining = num_scrap - scrap_spawned
        for _ in range(remaining * 20):
            if scrap_spawned >= num_scrap:
                break
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                node_x_px = random.randint((compound_bounds['left'] - 10) * TILE, 
                                           (compound_bounds['right'] + 10) * TILE)
                node_y_px = (compound_bounds['top'] - random.randint(5, 15)) * TILE
            elif side == 'bottom':
                node_x_px = random.randint((compound_bounds['left'] - 10) * TILE, 
                                           (compound_bounds['right'] + 10) * TILE)
                node_y_px = (compound_bounds['bottom'] + random.randint(5, 15)) * TILE
            elif side == 'left':
                node_x_px = (compound_bounds['left'] - random.randint(5, 15)) * TILE
                node_y_px = random.randint((compound_bounds['top'] - 10) * TILE, 
                                           (compound_bounds['bottom'] + 10) * TILE)
            else:
                node_x_px = (compound_bounds['right'] + random.randint(5, 15)) * TILE
                node_y_px = random.randint((compound_bounds['top'] - 10) * TILE, 
                                           (compound_bounds['bottom'] + 10) * TILE)
            
            node_gx = int(node_x_px // TILE)
            node_gy = int(node_y_px // TILE)
            
            if (0 <= node_gx < grid.width and 0 <= node_gy < grid.height and
                not grid.is_blocked(node_gx, node_gy)):
                # Check distance from existing nodes (using pixel positions)
                too_close = False
                node_pos = pygame.Vector2(node_x_px, node_y_px)
                min_node_dist = 96  # 3 tiles in pixels
                for existing_node in list(node_group) + new_nodes:
                    if hasattr(existing_node, 'pos'):
                        dist = (node_pos - existing_node.pos).length()
                        if dist < min_node_dist:
                            too_close = True
                            break
                if not too_close and scrap_config:
                    node = ScrapPile((node_x_px, node_y_px), scrap_config)
                    new_nodes.append(node)
                    scrap_spawned += 1
    
    # Add all nodes to the group
    for node in new_nodes:
        node_group.add(node)
    
    print(f"Spawned {len(new_nodes)} resource nodes in clusters around compound ({trees_spawned} trees, {scrap_spawned} scrap)")

def apply_difficulty_settings(difficulty: Difficulty, *, reset_resources: bool = True):
    """Apply the selected difficulty to resources, economy, and research scaling."""
    settings = DIFFICULTY_CONFIG[difficulty]
    if reset_resources:
        resources.wood = settings.starting_resources.get("wood", resources.wood)
        resources.iron = settings.starting_resources.get("iron", resources.iron)
        resources.food = settings.starting_resources.get("food", resources.food)
        resources.coins = 0
    world.production_multipliers["sawmill"] = settings.sawmill_yield_multiplier
    world.production_multipliers["smelter"] = settings.smelter_yield_multiplier
    world.current_difficulty = difficulty
    if hasattr(wave_manager, "difficulty"):
        wave_manager.difficulty = difficulty.name.lower()
    research_manager.apply_difficulty_scaling(settings.research_total_target)


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
    apply_difficulty_settings(current_difficulty, reset_resources=True)
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


pause_menu.on_restart = restart_game
pause_menu.on_quit = quit_game
pause_menu.on_resume = resume_game  # For ESC key in pause menu


def open_difficulty_selection():
    """Transition from start screen to difficulty selection."""
    start_screen.hide()
    difficulty_screen.show()
    game_state_manager.set_state(GameState.SELECT_DIFFICULTY)


def handle_difficulty_selected(selection: Difficulty):
    """Apply difficulty and start gameplay."""
    global current_difficulty
    current_difficulty = selection
    apply_difficulty_settings(selection, reset_resources=True)
    difficulty_screen.hide()
    game_state_manager.set_state(GameState.PLAYING)


def handle_difficulty_cancel():
    """Return to start screen from difficulty selection."""
    difficulty_screen.hide()
    start_screen.show()
    game_state_manager.set_state(GameState.MENU)


start_screen.on_start = open_difficulty_selection
difficulty_screen.on_select = handle_difficulty_selected
difficulty_screen.on_cancel = handle_difficulty_cancel

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
            building.upgrade(world)
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
        building.refund_cost(resources, ratio=0.6, world=world)
        grid.set_footprint_blocked((building.grid_x, building.grid_y), building.FOOTPRINT, False)
        world.unregister_building(building)
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
    """Spawn all types of enemies at mouse position (with small offset for visibility)"""
    import random
    enemy_types = [BasicZombie, RunnerZombie, BruteZombie, SpitterZombie, SwarmlingZombie, Skeleton, ArcherSkeleton, WarriorSkeleton]
    
    # Spawn all enemy types with small random offsets so they don't overlap
    for i, enemy_class in enumerate(enemy_types):
        # Add small random offset (0-40 pixels) so enemies are visible separately
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-20, 20)
        spawn_pos = pygame.Vector2(mouse_pos[0] + offset_x, mouse_pos[1] + offset_y)
        
        enemy = enemy_class(spawn_pos)
        enemy_group.add(enemy)
    
    print(f"Debug: Spawned all enemy types (8 total) near {mouse_pos}")

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

def debug_add_coins():
    """Add +100 coins"""
    resources.add_coins(100)
    print("Debug: Added +100 coins")

def debug_unlock_all_research():
    """Unlock all research items"""
    if world.research:
        for key in world.research.research_defs.keys():
            if not world.research.is_research_purchased(key):
                world.research.unlock(key)
        rebuild_building_buttons()
        print("Debug: Unlocked all research")

def debug_roll_day_event():
    """Force roll a new day event"""
    if world.day_events:
        world.day_events.roll_new_day_event(wave_manager.day)
        print("Debug: Rolled new day event")

def debug_clear_day_event():
    """Clear current day event and reset modifiers"""
    if world.day_events:
        world.day_events.clear_event()
        print("Debug: Cleared day event, modifiers reset")

def debug_toggle_footprints():
    """Toggle showing building footprints"""
    debug_system.show_footprints = not debug_system.show_footprints
    status = "ON" if debug_system.show_footprints else "OFF"
    print(f"Debug: Show footprints {status}")

# Register debug actions
debug_system.register_action(pygame.K_F1, "Add +100 Resources", debug_add_resources)
debug_system.register_action(pygame.K_F2, "Instant Build", debug_instant_build)
debug_system.register_action(pygame.K_F3, "Spawn Zombie @ Mouse", lambda: None)  # Handled separately
debug_system.register_action(pygame.K_F4, "Clear All Enemies", debug_clear_enemies)
debug_system.register_action(pygame.K_F5, "Clear All Buildings", debug_clear_buildings)
debug_system.register_action(pygame.K_F6, "Toggle Spawner", debug_toggle_spawner)
debug_system.register_action(pygame.K_F7, "Kill All Enemies", debug_kill_all_enemies)
debug_system.register_action(pygame.K_F8, "Complete All Buildings", debug_complete_all_buildings)
# Additional debug actions (using number keys)
debug_system.register_action(pygame.K_1, "Add +100 Coins", debug_add_coins)
debug_system.register_action(pygame.K_2, "Unlock All Research", debug_unlock_all_research)
debug_system.register_action(pygame.K_3, "Roll Day Event", debug_roll_day_event)
debug_system.register_action(pygame.K_f, "Toggle Footprints", debug_toggle_footprints)
# F9-F11: Wave skipping (handled in event loop)
# F12: Toggle debug mode (handled in event loop)

###################
# Helper functions for buttons
###################
def create_button_image(text, color=(100, 150, 100), width=100, height=40):
    """Create a button image with text"""
    button_img = pygame.Surface((width, height))
    button_img.fill(color)
    # Use larger font for bigger buttons
    font = pygame.font.Font(None, int(20 * 1.5))  # Scale font with button size
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(width//2, height//2))
    button_img.blit(text_surface, text_rect)
    return button_img

###################
# Create buttons for all buildings
###################
# Building buttons will be horizontal at bottom left
button_x_start = 10
button_width = 150  # Increased from 100
button_height = 60  # Increased from 40
button_spacing = 160  # Width (150) + spacing (10)
buttons = {}

# Building types with their button labels and colors
# Note: HQ is not buildable - it spawns automatically at game start
building_types = [
    (BallisticTurret, "Ballistic", (150, 100, 100), turret_sprite_sheets, turret_base_images),
    (GatlingTurret, "Gatling", (200, 150, 100), gatling_sprite_sheets, gatling_base_images),
    (PiercerTurret, "Piercer", (150, 100, 150), railgun_sprite_sheets, railgun_base_images),
    (Wall, "Wall", (120, 120, 120)),
    (Gate, "Gate", (100, 100, 100)),
    (Farm, "Farm", (100, 150, 100)),
    (Sawmill, "Sawmill", (139, 90, 43)),
    (Smelter, "Smelter", (150, 150, 150)),
]

# Mapping of building classes to research unlock keys
# Note: These are the unlock keys (what gets added to unlocked set when research is purchased)
building_to_research = {
    Sawmill: "sawmill",
    Smelter: "smelter",
    PiercerTurret: "railgun",  # Research "railgun" unlocks "railgun"
}

# Store all building types for potential unlocking later
all_building_types = building_types.copy()

def rebuild_building_buttons():
    """Rebuild building buttons based on current research unlocks."""
    global buttons, button_index
    buttons = {}
    button_index = 0
    
    for building_class, label, color, *args in all_building_types:
        # Check if building requires research unlock
        research_key = building_to_research.get(building_class)
        if research_key and not research_manager.is_unlocked(research_key):
            continue  # Skip this building if not unlocked
        
        button_img = create_button_image(label, color, button_width, button_height)
        # Position buttons horizontally at bottom left
        button_x = button_x_start + button_index * button_spacing
        button_y = c.SCREEN_HEIGHT - button_height - 10  # 10px from bottom
        button = Button(button_x, button_y, button_img)
        buttons[building_class] = {
            'button': button,
            'label': label,
            'color': color,
            'args': args
        }
        button_index += 1

# Initial button creation
rebuild_building_buttons()

def launch_research_tree():
    """Open the research tree UI and rebuild buttons afterwards."""
    open_research_tree(screen, world, research_manager, game_state_manager)
    rebuild_building_buttons()

research_button = ResearchButton(10, 10, 120, 40, launch_research_tree)

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
    """Draw resource display (including coins) at bottom, spanning horizontally."""
    padding = 10
    item_spacing = 30  # Space between items horizontally (increased from 20)
    # Use larger font for resources
    resource_font = pygame.font.Font(None, 36)  # Increased from 24
    
    # Handle NaN values by converting to 0
    import math
    wood_val = resources.wood if not math.isnan(resources.wood) else 0
    iron_val = resources.iron if not math.isnan(resources.iron) else 0
    food_val = resources.food if not math.isnan(resources.food) else 0
    coins_val = resources.coins if not math.isnan(resources.coins) else 0
    
    # Also fix the resources if they're NaN
    if math.isnan(resources.wood):
        resources.wood = 0
    if math.isnan(resources.iron):
        resources.iron = 0
    if math.isnan(resources.food):
        resources.food = 0
    if math.isnan(resources.coins):
        resources.coins = 0
    
    texts = [
        f"Wood: {int(wood_val)}",
        f"Iron: {int(iron_val)}",
        f"Food: {int(food_val)}",
        f"Coins: {int(coins_val)}",
        f"Zombies: {len(enemy_group)}"
    ]
    
    # Calculate total width needed
    text_surfaces = []
    total_width = 0
    for text in texts:
        # Use gold color for coins, red for zombies, white for others
        if "Coins" in text:
            color = (255, 215, 0)
        elif "Zombies" in text:
            color = (255, 0, 0)
        else:
            color = (255, 255, 255)
        text_surface = resource_font.render(text, True, color)
        text_surfaces.append((text_surface, color))
        total_width += text_surface.get_width() + item_spacing
    
    # Remove last spacing
    total_width -= item_spacing
    
    # Position at bottom-right, spanning horizontally
    start_x = c.SCREEN_WIDTH - total_width - padding  # Right-aligned with padding
    start_y = c.SCREEN_HEIGHT - 45  # 45px from bottom (increased from 30)
    
    # DEBUG: Draw overlay rectangle for resource display area (horizontal span)
    resource_overlay = pygame.Surface((total_width + 20, 45), pygame.SRCALPHA)
    resource_overlay.fill((0, 255, 255, 80))  # Cyan overlay
    screen.blit(resource_overlay, (start_x - 10, start_y - 5))
    
    # Draw all resources horizontally
    current_x = start_x
    for text_surface, color in text_surfaces:
        screen.blit(text_surface, (current_x, start_y))
        current_x += text_surface.get_width() + item_spacing

def create_building(building_class, grid_pos, *args):
    """Create a building instance based on the building class."""
    # Check if it's a turret (needs sprite sheet and base image)
    if building_class is BallisticTurret:
        if len(args) >= 2:
            sprite_sheets, base_images = args[0], args[1]
            building = building_class(grid_pos, sprite_sheets, base_images, tier=1)
            building.world = world
            world.register_building(building)
            turret_group.add(building)
            return building
    elif building_class is PiercerTurret:
        if len(args) >= 2:
            sprite_sheets, base_images = args[0], args[1]
            building = building_class(grid_pos, sprite_sheets, base_images, tier=1)
            building.world = world
            world.register_building(building)
            turret_group.add(building)
            return building
    elif building_class is GatlingTurret:
        if len(args) >= 2:
            sprite_sheets, base_images = args[0], args[1]
            building = building_class(grid_pos, sprite_sheets, base_images, tier=1)
            building.world = world
            world.register_building(building)
            turret_group.add(building)
            return building
    else:
        # Other buildings just need grid position
        building = building_class(grid_pos, tier=1)
        building.world = world
        world.register_building(building)
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
    
    # Apply research modifiers (combine with day event modifiers)
    # Use caching to avoid recalculating every frame - only recalculates when research changes
    # IMPORTANT: world.modifiers should only contain day event modifiers.
    # We apply research modifiers on top and store the result in world.modifiers
    # for components to read. Day events will reset world.modifiers when they change.
    if hasattr(world, 'research') and world.research:
        # Get effective modifiers (cached, only recalculates when research changes or day events change)
        effective_modifiers = research_manager.apply_research_modifiers()
        # Update world.modifiers with effective modifiers
        # Day events will reset world.modifiers to only day event modifiers when they change,
        # and mark research modifiers as dirty, so this is safe
        world.modifiers.update(effective_modifiers)
    
    # Calculate FPS
    fps_timer += dt
    fps_counter += 1
    if fps_timer >= 1.0:
        current_fps = fps_counter / fps_timer
        fps_counter = 0
        fps_timer = 0.0
    
    # Handle start screen (menu state)
    if game_state_manager.get_state() == GameState.MENU:
        # Update start screen animation
        start_screen.update(dt)
        
        # Draw start screen
        start_screen.draw(screen)
        
        # Handle events for start screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                start_screen.handle_event(event)
        
        pygame.display.flip()
        continue
    
    if game_state_manager.get_state() == GameState.SELECT_DIFFICULTY:
        difficulty_screen.update(dt)
        difficulty_screen.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                difficulty_screen.handle_event(event)
        pygame.display.flip()
        continue
    
    # Fill screen with background
    # Draw grass tile map background
    # Calculate how many tiles we need to cover the screen
    tiles_x = (c.SCREEN_WIDTH + TILE - 1) // TILE  # Ceiling division to ensure full coverage
    tiles_y = (c.SCREEN_HEIGHT + TILE - 1) // TILE  # Ceiling division to ensure full coverage
    
    # Draw grass tiles across the entire screen with variation
    # Select day or night tiles based on wave manager state
    is_night = wave_manager.state == WaveManager.STATE_NIGHT
    current_grass_tiles = grass_tiles_night if is_night else grass_tiles_day
    
    for y in range(tiles_y):
        for x in range(tiles_x):
            # Use a simple pattern to select which grass variant to use
            # This creates a somewhat random but consistent pattern across the map
            # Using modulo to cycle through variants
            # The same variant_index is used for both day and night to maintain consistency
            variant_index = (x * 7 + y * 11) % len(current_grass_tiles)
            tile_x = x * TILE
            tile_y = y * TILE
            screen.blit(current_grass_tiles[variant_index], (tile_x, tile_y))
    
    # Day/night divider line removed
    # Overlay removed - using original texture without tinting
    
    # Draw gate icon/banner on gate columns (if gate exists)
    try:
        # Find gate buildings using isinstance (Gate is already imported)
        gate_buildings = [b for b in building_group if isinstance(b, Gate)]
        if gate_buildings:
            # Get gate center position (use first gate)
            gate_building = gate_buildings[0]
            gate_center_x_px = gate_building.pos.x
            gate_pixel_y = gate_building.pos.y - 25  # Above the gate
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
    
    # DEBUG: Draw overlay rectangles for build menu buttons (bottom-left)
    if buttons:
        # Calculate total width of button row
        num_buttons = len(buttons)
        total_button_width = num_buttons * button_spacing
        button_row_y = c.SCREEN_HEIGHT - button_height - 10
        button_overlay = pygame.Surface((total_button_width, button_height), pygame.SRCALPHA)
        button_overlay.fill((255, 128, 0, 80))  # Orange overlay
        screen.blit(button_overlay, (button_x_start, button_row_y))
    
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
        
        world.unregister_building(building)
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
            # Roll day event on first day
            if wave_manager.state == WaveManager.STATE_DAY and world.day_events:
                world.day_events.roll_new_day_event(wave_manager.day)
        
        # Check for state transitions
        if wave_manager._prev_state != wave_manager.state:
            # State changed
            if wave_manager.state == WaveManager.STATE_DAY:
                # Just started day - roll random day event
                if world.day_events:
                    world.day_events.roll_new_day_event(wave_manager.day)
                # Spawn daily nodes
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
        zombie_spawner.update(dt, enemy_group, world)
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
        
        # Check if enemy should be removed
        should_remove = False
        if enemy.reached_bottom:
            should_remove = True
        elif not enemy.alive:
            # For enemies with sprite animations, wait for death animation to complete
            if isinstance(enemy, (BasicZombie, RunnerZombie, BruteZombie, Skeleton, ArcherSkeleton, WarriorSkeleton)):
                if hasattr(enemy, 'death_animation_complete') and enemy.death_animation_complete:
                    should_remove = True
            else:
                # For other enemy types, remove immediately when dead
                should_remove = True
        
        if should_remove:
            enemies_to_remove.append(enemy)
    
    # Drop coins when enemies are removed (ensures coins are always dropped)
    for enemy in enemies_to_remove:
        # Initialize coins_dropped if not present (for backwards compatibility)
        if not hasattr(enemy, 'coins_dropped'):
            enemy.coins_dropped = False
        
        if not enemy.coins_dropped and enemy.hp <= 0:  # Only drop coins if killed (not if reached bottom)
            # Drop coins based on enemy difficulty/type
            base_reward = 2
            if hasattr(enemy, 'TYPE_ID'):
                # Different enemy types give different rewards
                type_rewards = {
                    "walker": 2,
                    "runner": 3,
                    "brute": 5,
                    "spitter": 4,
                    "swarmling": 1,
                    "skeleton": 3,
                    "archer_skeleton": 4,
                    "warrior_skeleton": 5
                }
                coin_reward = type_rewards.get(enemy.TYPE_ID, base_reward)
            else:
                coin_reward = base_reward
            
            # Apply coin drop modifier from day events
            coin_mult = world.modifiers.get("coin_drop_mult", 1.0) if hasattr(world, 'modifiers') else 1.0
            coin_reward = int(coin_reward * coin_mult)
            resources.add_coins(coin_reward)
            enemy.coins_dropped = True
    
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
        # Update projectile (check collisions with enemies, buildings, and survivors)
        # Projectiles automatically check correct target type (enemy, building, or survivor)
        # ArrowProjectile supports survivor_group parameter, others ignore it
        if isinstance(projectile, ArrowProjectile):
            projectile.update(dt, enemy_group, building_group, survivor_group)
        else:
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
    # Draw building footprints (debug mode)
    ###################
    if debug_system.is_active() and debug_system.show_footprints:
        for building in building_group:
            # Get footprint dimensions
            footprint = getattr(building, 'FOOTPRINT', (1, 1))
            w, h = footprint
            gx, gy = building.grid_x, building.grid_y
            
            # Calculate pixel position for top-left corner
            px = gx * TILE
            py = gy * TILE
            
            # Draw semi-transparent footprint overlay
            footprint_surface = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
            footprint_surface.fill((255, 255, 0, 80))  # Yellow with transparency
            screen.blit(footprint_surface, (px, py))
            
            # Draw footprint outline
            pygame.draw.rect(screen, (255, 255, 0), (px, py, w * TILE, h * TILE), 2)
            
            # Draw grid lines within footprint
            for dx in range(1, w):
                line_x = px + dx * TILE
                pygame.draw.line(screen, (200, 200, 0), (line_x, py), (line_x, py + h * TILE), 1)
            for dy in range(1, h):
                line_y = py + dy * TILE
                pygame.draw.line(screen, (200, 200, 0), (px, line_y), (px + w * TILE, line_y), 1)
    
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
    # Apply night blue tint overlay
    ###################
    if is_night:
        night_overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        night_overlay.fill((30, 40, 80, 80))  # Darkish blue tint with transparency
        screen.blit(night_overlay, (0, 0))
    
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
        building_panel.draw(screen, resources, mouse_pos)
    
    ###################
    # Draw research button
    ###################
    # DEBUG: Draw overlay rectangle for research button (top-left, 10px padding)
    if hasattr(research_button, 'rect'):
        research_overlay = pygame.Surface((research_button.rect.width, research_button.rect.height), pygame.SRCALPHA)
        research_overlay.fill((128, 0, 255, 80))  # Purple overlay
        screen.blit(research_overlay, research_button.rect)
    research_button.draw(screen)
    
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
    # Draw start screen (should not be visible during gameplay, but just in case)
    ###################
    if start_screen.is_visible:
        start_screen.draw(screen)
    if difficulty_screen.is_visible:
        difficulty_screen.draw(screen)
    
    ###################
    # Draw preview when in build mode
    ###################
    if build_mode and selected_building_type:
        grid_pos = pixel_to_grid(mouse_pos)
        can_place = can_place_building(selected_building_type, grid_pos, grid)
        
        # Check if we have enough resources (with day event modifiers)
        cost = selected_building_type.get_cost()
        # Apply build cost modifier from day events
        if hasattr(world, 'modifiers'):
            cost_mult = world.modifiers.get("build_cost_mult", 1.0)
            effective_wood = int(cost.wood * cost_mult)
            effective_iron = int(cost.iron * cost_mult)
            effective_food = int(cost.food * cost_mult)
        else:
            effective_wood = cost.wood
            effective_iron = cost.iron
            effective_food = cost.food
        
        if resources.wood < effective_wood or resources.iron < effective_iron or resources.food < effective_food:
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
        debug_system.update_info("Night", wave_manager.night)
        debug_system.update_info("Coins", resources.coins)
        grid_pos_debug = pixel_to_grid(mouse_pos)
        debug_system.update_info("Grid Pos", f"({grid_pos_debug[0]}, {grid_pos_debug[1]})")
        
        # Research info
        if world.research:
            unlocked_count = len(world.research.unlocked)
            purchased_count = len(world.research.purchased)
            debug_system.update_info("Research Unlocked", f"{unlocked_count} items")
            debug_system.update_info("Research Purchased", f"{purchased_count} items")
        
        # Day event info
        if world.day_events and world.day_events.current_event:
            event_name = world.day_events.current_event.get("name", "None")
            debug_system.update_info("Day Event", event_name)
        else:
            debug_system.update_info("Day Event", "None")
        
        # Modifiers info
        if hasattr(world, 'modifiers'):
            mods = []
            if world.modifiers.get("resource_prod_mult", 1.0) != 1.0:
                mods.append(f"Prod: {world.modifiers['resource_prod_mult']:.2f}x")
            if world.modifiers.get("coin_drop_mult", 1.0) != 1.0:
                mods.append(f"Coins: {world.modifiers['coin_drop_mult']:.2f}x")
            if world.modifiers.get("build_cost_mult", 1.0) != 1.0:
                mods.append(f"Cost: {world.modifiers['build_cost_mult']:.2f}x")
            if world.modifiers.get("turret_fire_rate_mult", 1.0) != 1.0:
                mods.append(f"Fire: {world.modifiers['turret_fire_rate_mult']:.2f}x")
            if world.modifiers.get("building_damage_taken_mult", 1.0) != 1.0:
                mods.append(f"Dmg: {world.modifiers['building_damage_taken_mult']:.2f}x")
            if world.modifiers.get("zombie_spawn_mult", 1.0) != 1.0:
                mods.append(f"Spawn: {world.modifiers['zombie_spawn_mult']:.2f}x")
            if world.modifiers.get("zombie_speed_mult", 1.0) != 1.0:
                mods.append(f"ZSpeed: {world.modifiers['zombie_speed_mult']:.2f}x")
            if world.modifiers.get("zombie_hp_mult", 1.0) != 1.0:
                mods.append(f"ZHP: {world.modifiers['zombie_hp_mult']:.2f}x")
            if world.modifiers.get("turret_range_mult", 1.0) != 1.0:
                mods.append(f"Range: {world.modifiers['turret_range_mult']:.2f}x")
            if world.modifiers.get("node_spawn_bonus", False):
                mods.append("NodeBonus")
            if world.modifiers.get("lightning_storm", False):
                mods.append("Lightning")
            if mods:
                debug_system.update_info("Modifiers", ", ".join(mods))
    
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
            continue
        
        if game_state_manager.get_state() == GameState.SELECT_DIFFICULTY:
            if difficulty_screen.handle_event(event):
                continue
        
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
            
            # Handle research button click
            if research_button.handle_click(mouse_pos):
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
                    # Try to pay cost (with day event modifiers)
                    if selected_building_type.pay_cost(resources, world):
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
            # Cancel build mode on right-click
            if build_mode and selected_building_type:
                build_mode = False
                selected_building_type = None
                deselect_building()
                print("Build mode cancelled (right-click)")
                continue
            # Skip if game over or paused
            if game_over_screen.is_visible or game_state_manager.is_paused():
                continue
            
            # Deselect building and hide panel on right-click
            deselect_building()
        
        # Handle keyboard input
        if event.type == pygame.KEYDOWN:
            # Handle start screen (menu state)
            if game_state_manager.get_state() == GameState.MENU:
                if start_screen.handle_event(event):
                    continue
            
            if event.key == pygame.K_r:
                launch_research_tree()
                continue
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
            
            # Upgrade selected building (U key) - only when not paused/over
            if event.key == pygame.K_u and not game_over_screen.is_visible and not game_state_manager.is_paused():
                # Check building panel first (if visible), then global selected_building
                building_to_upgrade = None
                if building_panel.is_visible and building_panel.selected_building:
                    building_to_upgrade = building_panel.selected_building
                elif selected_building:
                    building_to_upgrade = selected_building
                
                if building_to_upgrade:
                    upgrade_building(building_to_upgrade)
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
                    pending_construction.refund_cost(resources, ratio=0.6, world=world)
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
                        pause_menu.show()
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
