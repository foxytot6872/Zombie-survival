import pygame
import json
import os
import random
from typing import Dict, Optional
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
from world.collision_map import CollisionMap
# Core systems
from core.wave_manager import WaveManager
from core.game_state import GameState, GameStateManager
from core.save_system import SaveSystem
from core.sound import SoundSystem
from core.day_events import DayEventManager
from core.spatial_grid import SpatialGrid
from core.input_buffer import InputBuffer
from core.animation_timer import AnimationTimer, PulseAnimation
# UI components
from ui.game_over import GameOverScreen
from ui.pause_menu import PauseMenu
from ui.building_panel import BuildingPanel
from ui.hud import HUD
from ui.research_button import ResearchButton
from ui.research_panel import ResearchPanel
from ui.start_screen import StartScreen
from ui.difficulty_screen import SelectDifficultyScreen
from ui.mode_screen import SelectModeScreen, GameMode
from ui.build_tooltip import BuildTooltipManager
from ui.custom_font import load_custom_font, CustomFont
from upgrade_config import get_next_turret_upgrade, scale_upgrade_cost
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


def load_pixel_font(font_path, size, fallback_size=None):
    """
    Load a pixel font from file, with fallback to default font.
    
    Args:
        font_path: Path to the .ttf font file (e.g., 'asset/fonts/PressStart2P.ttf')
        size: Font size
        fallback_size: Size for fallback font (defaults to size)
    
    Returns:
        pygame.font.Font object
    """
    if fallback_size is None:
        fallback_size = size
    
    try:
        font = pygame.font.Font(font_path, size)
        return font
    except (pygame.error, FileNotFoundError):
        # Fallback to default system font
        print(f"Warning: Pixel font not found at {font_path}, using default font")
        return pygame.font.Font(None, fallback_size)


###################
# Load pixel font
###################
# Try to load a pixel font - you can download free pixel fonts from Google Fonts:
# - Press Start 2P: https://fonts.google.com/specimen/Press+Start+2P
# - VT323: https://fonts.google.com/specimen/VT323
# - Pixelify Sans: https://fonts.google.com/specimen/Pixelify+Sans
# - Silkscreen: https://fonts.google.com/specimen/Silkscreen
# 
# Place the .ttf file in asset/fonts/ and update the path below
PIXEL_FONT_PATH = 'asset/fonts/PressStart2P-Regular.ttf'  # Press Start 2P pixel font

# Load fonts with fallback - these will be used throughout the game
# If the font file doesn't exist, it will fall back to the default system font
# First load the pixel fonts as fallback
font_large_fallback = load_pixel_font(PIXEL_FONT_PATH, 48)
font_medium_fallback = load_pixel_font(PIXEL_FONT_PATH, 32)
font_small_fallback = load_pixel_font(PIXEL_FONT_PATH, 24)
font_tiny_fallback = load_pixel_font(PIXEL_FONT_PATH, 20)
font_huge_fallback = load_pixel_font(PIXEL_FONT_PATH, 72)

###################
# Load custom letter fonts from sprite sheets
###################
# Extract frames: 17x22, 26 frames (A-Z)
custom_font_yellow = load_custom_font('asset/fonts/YellowFont-Sheet.png', letter_width=17, letter_height=22, number_font_size=22)
custom_font_red = load_custom_font('asset/fonts/RedFont-Sheet.png', letter_width=17, letter_height=22, number_font_size=22)
custom_font_blue = load_custom_font('asset/fonts/BlueFont-Sheet.png', letter_width=17, letter_height=22, number_font_size=22)

# Use yellow font as default custom font
custom_font = custom_font_yellow if custom_font_yellow else None

# Create scaled versions if needed (for different sizes, we'll scale the letter frames)
def create_scaled_custom_font(base_font: Optional[CustomFont], scale: float, number_font_size: int) -> Optional[CustomFont]:
    """Create a scaled version of a custom font."""
    if base_font is None:
        return None
    
    try:
        # Scale letter frames
        scaled_letter_frames = {}
        for letter, frame in base_font.letter_frames.items():
            scaled_width = int(frame.get_width() * scale)
            scaled_height = int(frame.get_height() * scale)
            scaled_frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
            scaled_letter_frames[letter] = scaled_frame
        
        # Create new number font with scaled size
        try:
            scaled_number_font = pygame.font.SysFont("arial", number_font_size)
        except:
            scaled_number_font = pygame.font.Font(None, number_font_size)
        
        return CustomFont(scaled_letter_frames, scaled_number_font)
    except Exception as e:
        print(f"Error creating scaled custom font: {e}")
        return None

# Create scaled versions for different sizes
custom_font_large = create_scaled_custom_font(custom_font_yellow, 2.18, 48) if custom_font_yellow else None  # ~48px
custom_font_medium = create_scaled_custom_font(custom_font_yellow, 1.45, 32) if custom_font_yellow else None  # ~32px
custom_font_small = create_scaled_custom_font(custom_font_yellow, 1.09, 24) if custom_font_yellow else None  # ~24px
custom_font_tiny = create_scaled_custom_font(custom_font_yellow, 0.91, 20) if custom_font_yellow else None  # ~20px
custom_font_huge = create_scaled_custom_font(custom_font_yellow, 3.27, 72) if custom_font_yellow else None  # ~72px

# Use custom fonts if available, otherwise fall back to pixel fonts
font_large = custom_font_large if custom_font_large else font_large_fallback
font_medium = custom_font_medium if custom_font_medium else font_medium_fallback
font_small = custom_font_small if custom_font_small else font_small_fallback
font_tiny = custom_font_tiny if custom_font_tiny else font_tiny_fallback
font_huge = custom_font_huge if custom_font_huge else font_huge_fallback

def load_build_item_config(path: str = os.path.join("data", "config", "build_items.json")) -> Dict:
    """Load build item metadata for tooltips."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: build item config not found at {path}, using defaults")
        return {}
    except Exception as e:
        print(f"Error loading build item config at {path}: {e}")
        return {}


build_item_config = load_build_item_config()


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

# Set sprite sheets for zombie classes (legacy - kept for compatibility)
BasicZombie.sprite_sheet = zombie_sprite_sheet
RunnerZombie.sprite_sheet = runner_sprite_sheet
BruteZombie.sprite_sheet = brute_sprite_sheet
SwarmlingZombie.sprite_sheet = swarmling_sprite_sheet
SpitterZombie.sprite_sheet = spitter_sprite_sheet

# Set sprite sheets in EnemyAssets cache (for pooling system)
from world.enemy import EnemyAssets
EnemyAssets.zombie_sprite_sheet = zombie_sprite_sheet
EnemyAssets.runner_sprite_sheet = runner_sprite_sheet
EnemyAssets.brute_sprite_sheet = brute_sprite_sheet
EnemyAssets.swarmling_sprite_sheet = swarmling_sprite_sheet
EnemyAssets.spitter_sprite_sheet = spitter_sprite_sheet

# Skeleton sprite sheet (40 frames, 48x48 each)
skeleton_sprite_sheet = load_image_or_placeholder(
    'asset/NormalSkeleton_Sheet.png',
    (48 * 40, 48),  # 40 frames * 48 pixels = 1920 pixels wide, 48 pixels tall
    (200, 200, 200, 255),
    "Skeleton sprite sheet"
)

# Set sprite sheet for Skeleton class (legacy - kept for compatibility)
Skeleton.sprite_sheet = skeleton_sprite_sheet

# Set sprite sheet in EnemyAssets cache
EnemyAssets.skeleton_sprite_sheet = skeleton_sprite_sheet

# Archer Skeleton sprite sheet (34 frames, 48x48 each)
archer_skeleton_sprite_sheet = load_image_or_placeholder(
    'asset/ArcherSkeleton_Sheet.png',
    (48 * 34, 48),  # 34 frames * 48 pixels = 1632 pixels wide, 48 pixels tall
    (200, 200, 200, 255),
    "Archer Skeleton sprite sheet"
)

# Set sprite sheet for ArcherSkeleton class (legacy - kept for compatibility)
ArcherSkeleton.sprite_sheet = archer_skeleton_sprite_sheet

# Set sprite sheet in EnemyAssets cache
EnemyAssets.archer_skeleton_sprite_sheet = archer_skeleton_sprite_sheet

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

# Coin sprite sheet (frames, 16x16 each)
coin_sheet = load_image_or_placeholder(
    'asset/Coin-Sheet.png',
    (16 * 8, 16),  # Assuming 8 frames * 16 pixels = 128 pixels wide, 16 pixels tall
    (255, 215, 0, 255),  # Gold color placeholder
    "Coin sprite sheet"
)
# Extract coin frames
coin_frame_size = 16
coin_frames = []
if coin_sheet:
    coin_frames_count = coin_sheet.get_width() // coin_frame_size
    for i in range(coin_frames_count):
        frame_rect = pygame.Rect(i * coin_frame_size, 0, coin_frame_size, coin_frame_size)
        if frame_rect.right <= coin_sheet.get_width():
            frame = coin_sheet.subsurface(frame_rect)
            coin_frames.append(frame)
    print(f"Loaded {len(coin_frames)} coin frames from sprite sheet")

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

# Set sprite sheet for WarriorSkeleton class (legacy - kept for compatibility)
WarriorSkeleton.sprite_sheet = warrior_skeleton_sprite_sheet

# Set sprite sheet in EnemyAssets cache
EnemyAssets.warrior_skeleton_sprite_sheet = warrior_skeleton_sprite_sheet

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

# Red number sprite sheet (10 frames, 42x74 each) - for day numbers
red_number_sheet = load_image_or_placeholder(
    'asset/hud/Rednumber-Sheet.png',
    (42 * 10, 74),  # 10 frames * 42 pixels = 420 pixels wide, 74 pixels tall
    (255, 0, 0, 255),
    "Red number sprite sheet"
)
# Extract 10 frames (0-9) from the sheet
red_number_frames = []
if red_number_sheet:
    # Get actual dimensions and calculate frame width
    sheet_width = red_number_sheet.get_width()
    sheet_height = red_number_sheet.get_height()
    # Calculate frame width based on actual sheet dimensions (10 frames expected)
    frame_width = sheet_width // 10
    frame_height = sheet_height
    print(f"Red number sheet: {sheet_width}x{sheet_height}, frame size: {frame_width}x{frame_height}")
    
    for i in range(10):
        try:
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            # Double-check bounds before creating subsurface
            if (frame_rect.right <= sheet_width and frame_rect.bottom <= sheet_height and
                frame_rect.x >= 0 and frame_rect.y >= 0):
                frame = red_number_sheet.subsurface(frame_rect)
                red_number_frames.append(frame)
            else:
                # Frame out of bounds, use placeholder
                if red_number_frames:
                    red_number_frames.append(red_number_frames[0])
                else:
                    placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    placeholder.fill((255, 0, 0, 255))
                    red_number_frames.append(placeholder)
        except (ValueError, pygame.error) as e:
            # If subsurface fails, use placeholder
            print(f"Warning: Failed to extract red number frame {i}: {e}")
            if red_number_frames:
                red_number_frames.append(red_number_frames[0])
            else:
                placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                placeholder.fill((255, 0, 0, 255))
                red_number_frames.append(placeholder)
    
    # Ensure we have exactly 10 frames
    while len(red_number_frames) < 10:
        if red_number_frames:
            red_number_frames.append(red_number_frames[0])
        else:
            placeholder = pygame.Surface((42, 74), pygame.SRCALPHA)
            placeholder.fill((255, 0, 0, 255))
            red_number_frames.append(placeholder)
else:
    # Create placeholder frames if sheet not loaded
    for i in range(10):
        placeholder = pygame.Surface((42, 74), pygame.SRCALPHA)
        placeholder.fill((255, 0, 0, 255))
        red_number_frames.append(placeholder)

# Blue number sprite sheet (10 frames, 42x74 each) - for night numbers
blue_number_sheet = load_image_or_placeholder(
    'asset/hud/Bluenumber-Sheet.png',
    (42 * 10, 74),  # 10 frames * 42 pixels = 420 pixels wide, 74 pixels tall
    (0, 0, 255, 255),
    "Blue number sprite sheet"
)
# Extract 10 frames (0-9) from the sheet
blue_number_frames = []
if blue_number_sheet:
    # Get actual dimensions and calculate frame width
    sheet_width = blue_number_sheet.get_width()
    sheet_height = blue_number_sheet.get_height()
    # Calculate frame width based on actual sheet dimensions (10 frames expected)
    frame_width = sheet_width // 10
    frame_height = sheet_height
    print(f"Blue number sheet: {sheet_width}x{sheet_height}, frame size: {frame_width}x{frame_height}")
    
    for i in range(10):
        try:
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            # Double-check bounds before creating subsurface
            if (frame_rect.right <= sheet_width and frame_rect.bottom <= sheet_height and
                frame_rect.x >= 0 and frame_rect.y >= 0):
                frame = blue_number_sheet.subsurface(frame_rect)
                blue_number_frames.append(frame)
            else:
                # Frame out of bounds, use placeholder
                if blue_number_frames:
                    blue_number_frames.append(blue_number_frames[0])
                else:
                    placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    placeholder.fill((0, 0, 255, 255))
                    blue_number_frames.append(placeholder)
        except (ValueError, pygame.error) as e:
            # If subsurface fails, use placeholder
            print(f"Warning: Failed to extract blue number frame {i}: {e}")
            if blue_number_frames:
                blue_number_frames.append(blue_number_frames[0])
            else:
                placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                placeholder.fill((0, 0, 255, 255))
                blue_number_frames.append(placeholder)
    
    # Ensure we have exactly 10 frames
    while len(blue_number_frames) < 10:
        if blue_number_frames:
            blue_number_frames.append(blue_number_frames[0])
        else:
            placeholder = pygame.Surface((42, 74), pygame.SRCALPHA)
            placeholder.fill((0, 0, 255, 255))
            blue_number_frames.append(placeholder)
else:
    # Create placeholder frames if sheet not loaded
    for i in range(10):
        placeholder = pygame.Surface((42, 74), pygame.SRCALPHA)
        placeholder.fill((0, 0, 255, 255))
        blue_number_frames.append(placeholder)

# HQ building image
hq_image = load_image_or_placeholder(
    'asset/base.png',
    (64, 64),  # 2x2 tile building
    (50, 100, 150, 255),
    "HQ building image"
)

# Set image for HQ class
HQ.building_image = hq_image

# Upgrade panel image - extract 3 frames (375x475 each) - for upgrade progress indicator
upgrade_panel_sheet = None
frame_width = 375
frame_height = 475
try:
    upgrade_panel_sheet = pygame.image.load('asset/hud/UpgradePanel-Sheet.png').convert_alpha()
    sheet_width, sheet_height = upgrade_panel_sheet.get_size()
    print(f"Loaded upgrade panel sheet: {sheet_width}x{sheet_height}")
    
    # Verify dimensions match expected size (4 frames * 375 = 1500 wide, 475 tall)
    if sheet_width < 375 * 4 or sheet_height < 475:
        print(f"Warning: Upgrade panel sheet size {sheet_width}x{sheet_height} doesn't match expected (1500x475)")
        print(f"  Using actual dimensions: frame_width={sheet_width // 4}, frame_height={sheet_height}")
        frame_width = sheet_width // 4
        frame_height = sheet_height
    else:
        frame_width = 375
        frame_height = 475
except Exception as e:
    print(f"Error loading upgrade panel sheet: {e}")
    upgrade_panel_sheet = load_image_or_placeholder(
        'asset/hud/UpgradePanel-Sheet.png',
        (375 * 4, 475),
        (100, 100, 100, 255),
        "Upgrade panel sprite sheet"
    )
    frame_width = 375
    frame_height = 475

# Extract 4 frames from the sheet
upgrade_panel_frames = []
if upgrade_panel_sheet:
    for i in range(4):
        try:
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            frame = upgrade_panel_sheet.subsurface(frame_rect)
            upgrade_panel_frames.append(frame)
            print(f"Extracted upgrade panel frame {i+1}: {frame.get_size()}")
        except Exception as e:
            print(f"Error extracting frame {i+1}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            upgrade_panel_frames.append(placeholder)

# Upgrade panel darkened image - extract 4 frames
# Create darkened version programmatically from the main sheet
upgrade_panel_darken_frames = []
if upgrade_panel_sheet:
    for i in range(4):
        try:
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            frame = upgrade_panel_sheet.subsurface(frame_rect).copy()
            # Darken the frame by applying a semi-transparent black overlay
            darken_overlay = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            darken_overlay.fill((0, 0, 0, 128))  # 50% opacity black overlay
            frame.blit(darken_overlay, (0, 0))
            upgrade_panel_darken_frames.append(frame)
        except Exception as e:
            print(f"Error creating darkened frame {i+1}: {e}")
            # Create placeholder darkened frame
            placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            placeholder.fill((50, 50, 50, 255))  # Darker placeholder
            upgrade_panel_darken_frames.append(placeholder)


# Upgrade button image - extract 4 frames (277x84 each) - for hover and press animation
try:
    upgrade_button_sheet = pygame.image.load('asset/hud/UpgradeButton-Sheet.png').convert_alpha()
    button_sheet_width, button_sheet_height = upgrade_button_sheet.get_size()
    print(f"Loaded upgrade button sheet: {button_sheet_width}x{button_sheet_height}")
    
    # Verify dimensions match expected size (4 frames * 277 = 1108 wide, 84 tall)
    if button_sheet_width < 277 * 4 or button_sheet_height < 84:
        print(f"Warning: Upgrade button sheet size {button_sheet_width}x{button_sheet_height} doesn't match expected (1108x84)")
        print(f"  Using actual dimensions: button_frame_width={button_sheet_width // 4}, button_frame_height={button_sheet_height}")
        button_frame_width = button_sheet_width // 4
        button_frame_height = button_sheet_height
    else:
        button_frame_width = 277
        button_frame_height = 84
except Exception as e:
    print(f"Error loading upgrade button sheet: {e}")
    upgrade_button_sheet = load_image_or_placeholder(
        'asset/hud/UpgradeButton-Sheet.png',
        (277 * 4, 84),
        (100, 100, 100, 255),
        "Upgrade button sprite sheet"
    )
    button_frame_width = 277
    button_frame_height = 84

# Extract 4 frames from the upgrade button sheet
upgrade_button_frames = []
if upgrade_button_sheet:
    for i in range(4):
        try:
            frame_rect = pygame.Rect(i * button_frame_width, 0, button_frame_width, button_frame_height)
            frame = upgrade_button_sheet.subsurface(frame_rect)
            upgrade_button_frames.append(frame)
            print(f"Extracted upgrade button frame {i+1}: {frame.get_size()}")
        except Exception as e:
            print(f"Error extracting upgrade button frame {i+1}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((button_frame_width, button_frame_height), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            upgrade_button_frames.append(placeholder)

# Demolish button image - extract 4 frames (91x68 each) - for pulsing animation
try:
    demolish_button_sheet = pygame.image.load('asset/hud/DemolishButton-Sheet.png').convert_alpha()
    demolish_sheet_width, demolish_sheet_height = demolish_button_sheet.get_size()
    print(f"Loaded demolish button sheet: {demolish_sheet_width}x{demolish_sheet_height}")
    
    # Verify dimensions match expected size (4 frames * 91 = 364 wide, 68 tall)
    if demolish_sheet_width < 91 * 4 or demolish_sheet_height < 68:
        print(f"Warning: Demolish button sheet size {demolish_sheet_width}x{demolish_sheet_height} doesn't match expected (364x68)")
        print(f"  Using actual dimensions: demolish_frame_width={demolish_sheet_width // 4}, demolish_frame_height={demolish_sheet_height}")
        demolish_frame_width = demolish_sheet_width // 4
        demolish_frame_height = demolish_sheet_height
    else:
        demolish_frame_width = 91
        demolish_frame_height = 68
except Exception as e:
    print(f"Error loading demolish button sheet: {e}")
    demolish_button_sheet = load_image_or_placeholder(
        'asset/hud/DemolishButton-Sheet.png',
        (91 * 4, 68),
        (100, 100, 100, 255),
        "Demolish button sprite sheet"
    )
    demolish_frame_width = 91
    demolish_frame_height = 68

# Extract 4 frames from the demolish button sheet
demolish_button_frames = []
if demolish_button_sheet:
    for i in range(4):
        try:
            frame_rect = pygame.Rect(i * demolish_frame_width, 0, demolish_frame_width, demolish_frame_height)
            frame = demolish_button_sheet.subsurface(frame_rect)
            demolish_button_frames.append(frame)
            print(f"Extracted demolish button frame {i+1}: {frame.get_size()}")
        except Exception as e:
            print(f"Error extracting demolish button frame {i+1}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((demolish_frame_width, demolish_frame_height), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            demolish_button_frames.append(placeholder)

# HQ Health bar image - extract 21 frames (550x28 each) - for HQ health display at top of screen
# Frame 1 = 100% health, Frame 21 = 0% health (death)
try:
    hq_health_bar_sheet = pygame.image.load('asset/hud/BaseHealthBar-Sheet.png').convert_alpha()
    hq_health_sheet_width, hq_health_sheet_height = hq_health_bar_sheet.get_size()
    print(f"Loaded HQ health bar sheet: {hq_health_sheet_width}x{hq_health_sheet_height}")
    
    # Verify dimensions match expected size (21 frames * 550 = 11550 wide, 28 tall)
    hq_health_frame_width = 550
    hq_health_frame_height = 28
    if hq_health_sheet_width < 550 * 21 or hq_health_sheet_height < 28:
        print(f"Warning: HQ health bar sheet size {hq_health_sheet_width}x{hq_health_sheet_height} doesn't match expected (11550x28)")
        print(f"  Using actual dimensions: hq_health_frame_width={hq_health_sheet_width // 21}, hq_health_frame_height={hq_health_sheet_height}")
        hq_health_frame_width = hq_health_sheet_width // 21
        hq_health_frame_height = hq_health_sheet_height
except Exception as e:
    print(f"Error loading HQ health bar sheet: {e}")
    hq_health_bar_sheet = load_image_or_placeholder(
        'asset/hud/BaseHealthBar-Sheet.png',
        (550 * 21, 28),
        (100, 100, 100, 255),
        "HQ health bar sprite sheet"
    )
    hq_health_frame_width = 550
    hq_health_frame_height = 28

# Extract 21 frames from the HQ health bar sheet (Frame 1 = 100%, Frame 21 = 0%)
hq_health_bar_frames = []
if hq_health_bar_sheet:
    for i in range(21):
        try:
            frame_rect = pygame.Rect(i * hq_health_frame_width, 0, hq_health_frame_width, hq_health_frame_height)
            frame = hq_health_bar_sheet.subsurface(frame_rect)
            hq_health_bar_frames.append(frame)
            hp_percentage = 100.0 - (i * (100.0 / 20.0))  # Frame 0 = 100%, Frame 20 = 0%
            print(f"Extracted HQ health bar frame {i+1} ({hp_percentage:.1f}%): {frame.get_size()}")
        except Exception as e:
            print(f"Error extracting HQ health bar frame {i+1}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((hq_health_frame_width, hq_health_frame_height), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            hq_health_bar_frames.append(placeholder)
    print(f"HQ health bar: Extracted {len(hq_health_bar_frames)} frames total")
else:
    print(f"Warning: HQ health bar sheet not loaded, frames list will be empty")

# Health bar image - extract 11 frames (280x27 each) - for building health display in upgrade panel
try:
    health_bar_sheet = pygame.image.load('asset/hud/HealthBar-Sheet.png').convert_alpha()
    health_sheet_width, health_sheet_height = health_bar_sheet.get_size()
    print(f"Loaded health bar sheet: {health_sheet_width}x{health_sheet_height}")
    
    # Verify dimensions match expected size (11 frames * 280 = 3080 wide, 27 tall)
    if health_sheet_width < 280 * 11 or health_sheet_height < 27:
        print(f"Warning: Health bar sheet size {health_sheet_width}x{health_sheet_height} doesn't match expected (3080x27)")
        print(f"  Using actual dimensions: health_frame_width={health_sheet_width // 11}, health_frame_height={health_sheet_height}")
        health_frame_width = health_sheet_width // 11
        health_frame_height = health_sheet_height
    else:
        health_frame_width = 280
        health_frame_height = 27
except Exception as e:
    print(f"Error loading health bar sheet: {e}")
    health_bar_sheet = load_image_or_placeholder(
        'asset/hud/HealthBar-Sheet.png',
        (280 * 11, 27),
        (100, 100, 100, 255),
        "Health bar sprite sheet"
    )
    health_frame_width = 280
    health_frame_height = 27

# Extract 11 frames from the health bar sheet (0% to 100% in 10% increments) - for building panel
health_bar_frames = []
if health_bar_sheet:
    for i in range(11):
        try:
            frame_rect = pygame.Rect(i * health_frame_width, 0, health_frame_width, health_frame_height)
            frame = health_bar_sheet.subsurface(frame_rect)
            health_bar_frames.append(frame)
            print(f"Extracted health bar frame {i+1} ({i*10}%): {frame.get_size()}")
        except Exception as e:
            print(f"Error extracting health bar frame {i+1}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((health_frame_width, health_frame_height), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            health_bar_frames.append(placeholder)

# Current level number image - extract 3 frames (70x80 each) - for tier display (1, 2, 3)
# Note: Frames have 16x16 padding from top left corner
try:
    current_level_sheet = pygame.image.load('asset/hud/CurrentLevelNumber-Sheet.png').convert_alpha()
    level_sheet_width, level_sheet_height = current_level_sheet.get_size()
    print(f"Loaded current level number sheet: {level_sheet_width}x{level_sheet_height}")
    
    # Frame dimensions
    level_frame_width = 70
    level_frame_height = 80
    padding = 16  # 16x16 padding from top left
    
    # Verify dimensions match expected size
    # With padding: 16 + 70*3 = 226 wide, 16 + 80 = 96 tall
    expected_width = padding + level_frame_width * 3
    expected_height = padding + level_frame_height
    
    if level_sheet_width < expected_width or level_sheet_height < expected_height:
        print(f"Warning: Current level sheet size {level_sheet_width}x{level_sheet_height} doesn't match expected ({expected_width}x{expected_height})")
        # Try to calculate actual frame size
        if level_sheet_width >= padding:
            level_frame_width = (level_sheet_width - padding) // 3
        if level_sheet_height >= padding:
            level_frame_height = level_sheet_height - padding
except Exception as e:
    print(f"Error loading current level number sheet: {e}")
    current_level_sheet = load_image_or_placeholder(
        'asset/hud/CurrentLevelNumber-Sheet.png',
        (padding + level_frame_width * 3, padding + level_frame_height),
        (100, 100, 100, 255),
        "Current level number sprite sheet"
    )
    level_frame_width = 70
    level_frame_height = 80
    padding = 16

# Extract 3 frames from the current level number sheet (accounting for 16x16 padding)
current_level_frames = []
if current_level_sheet:
    for i in range(3):
        try:
            # Frame positions: (16, 16), (86, 16), (156, 16) accounting for padding
            frame_x = padding + (i * level_frame_width)
            frame_y = padding
            frame_rect = pygame.Rect(frame_x, frame_y, level_frame_width, level_frame_height)
            frame = current_level_sheet.subsurface(frame_rect)
            current_level_frames.append(frame)
            print(f"Extracted current level frame {i+1} (number {i+1}): {frame.get_size()}")
        except Exception as e:
            print(f"Error extracting current level frame {i+1}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((level_frame_width, level_frame_height), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            current_level_frames.append(placeholder)

# Next level number image - extract 3 frames (70x80 each) - for next tier display (1, 2, 3)
# Note: Frames have 16x16 padding from top left corner
try:
    next_level_sheet = pygame.image.load('asset/hud/NextLevelNumber-Sheet.png').convert_alpha()
    next_level_sheet_width, next_level_sheet_height = next_level_sheet.get_size()
    print(f"Loaded next level number sheet: {next_level_sheet_width}x{next_level_sheet_height}")
    
    # Use same frame dimensions as current level
    # Frame dimensions
    next_level_frame_width = 70
    next_level_frame_height = 80
    next_padding = 16  # 16x16 padding from top left
    
    # Verify dimensions match expected size
    # With padding: 16 + 70*3 = 226 wide, 16 + 80 = 96 tall
    next_expected_width = next_padding + next_level_frame_width * 3
    next_expected_height = next_padding + next_level_frame_height
    
    if next_level_sheet_width < next_expected_width or next_level_sheet_height < next_expected_height:
        print(f"Warning: Next level sheet size {next_level_sheet_width}x{next_level_sheet_height} doesn't match expected ({next_expected_width}x{next_expected_height})")
        # Try to calculate actual frame size
        if next_level_sheet_width >= next_padding:
            next_level_frame_width = (next_level_sheet_width - next_padding) // 3
        if next_level_sheet_height >= next_padding:
            next_level_frame_height = next_level_sheet_height - next_padding
except Exception as e:
    print(f"Error loading next level number sheet: {e}")
    next_level_sheet = load_image_or_placeholder(
        'asset/hud/NextLevelNumber-Sheet.png',
        (next_padding + next_level_frame_width * 3, next_padding + next_level_frame_height),
        (100, 100, 100, 255),
        "Next level number sprite sheet"
    )
    next_level_frame_width = 70
    next_level_frame_height = 80
    next_padding = 16

# Extract 3 frames from the next level number sheet (accounting for 16x16 padding)
next_level_frames = []
if next_level_sheet:
    for i in range(3):
        try:
            # Frame positions: (16, 16), (86, 16), (156, 16) accounting for padding
            frame_x = next_padding + (i * next_level_frame_width)
            frame_y = next_padding
            frame_rect = pygame.Rect(frame_x, frame_y, next_level_frame_width, next_level_frame_height)
            frame = next_level_sheet.subsurface(frame_rect)
            next_level_frames.append(frame)
            print(f"Extracted next level frame {i+1} (number {i+1}): {frame.get_size()}")
        except Exception as e:
            print(f"Error extracting next level frame {i+1}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((next_level_frame_width, next_level_frame_height), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100, 255))
            next_level_frames.append(placeholder)

# Load building construction menu background (bottom left)
try:
    building_menu_bg = pygame.image.load('asset/hud/BuildingPanel.png').convert_alpha()
    print(f"Loaded building menu background: {building_menu_bg.get_size()}")
except Exception as e:
    print(f"Warning: Failed to load BuildingPanel.png: {e}")
    building_menu_bg = None

# Load custom building button image
try:
    building_button_image = pygame.image.load('asset/hud/BuildingButton.png').convert_alpha()
    print(f"Loaded building button image: {building_button_image.get_size()}")
except Exception as e:
    print(f"Warning: Failed to load BuildingButton.png: {e}")
    building_button_image = None

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

# Load wall auto-tiling sprites (level 1 and level 2)
wall_tiles_lv1 = {}
wall_tiles_lv2 = {}

wall_sprite_paths_lv1 = {
    "4way": "asset/Wall/Wall-4way_lv1.png",
    "corner_tl": "asset/Wall/Wall-corner-tl_lv1.png",
    "corner_tr": "asset/Wall/Wall-corner-tr_lv1.png",
    "corner_bl": "asset/Wall/Wall-corner-bl_lv1.png",
    "corner_br": "asset/Wall/Wall-corner-br_lv1.png",
    "horizontal": "asset/Wall/Wall-horizontal_lv1.png",
    "vertical_l": "asset/Wall/Wall-vertical-l_lv1.png",
    "vertical_r": "asset/Wall/Wall-vertical-r_lv1.png",
    "t_up": "asset/Wall/Wall-t-up_lv1.png",
    "t_down": "asset/Wall/Wall-t-down_lv1.png",
    "t_left": "asset/Wall/Wall-t-left_lv1.png",
    "t_right": "asset/Wall/Wall-t-right_lv1.png",
}

wall_sprite_paths_lv2 = {
    "4way": "asset/Wall/Wall-4way_lv2.png",
    "corner_tl": "asset/Wall/Wall-corner-tl_lv2.png",
    "corner_tr": "asset/Wall/Wall-corner-tr_lv2.png",
    "corner_bl": "asset/Wall/Wall-corner-bl_lv2.png",
    "corner_br": "asset/Wall/Wall-corner-br_lv2.png",
    "horizontal": "asset/Wall/Wall-horizontal_lv2.png",
    "vertical_l": "asset/Wall/Wall-vertical-l_lv2.png",
    "vertical_r": "asset/Wall/Wall-vertical-r_lv2.png",
    "t_up": "asset/Wall/Wall-t-up_lv2.png",
    "t_down": "asset/Wall/Wall-t-down_lv2.png",
    "t_left": "asset/Wall/Wall-t-left_lv2.png",
    "t_right": "asset/Wall/Wall-t-right_lv2.png",
}

for tile_name, path in wall_sprite_paths_lv1.items():
    wall_tiles_lv1[tile_name] = load_image_or_placeholder(
        path,
        (TILE, TILE),  # 32x32 pixels
        (100, 100, 100, 255),
        f"Wall tile Lv1: {tile_name}"
    )

for tile_name, path in wall_sprite_paths_lv2.items():
    wall_tiles_lv2[tile_name] = load_image_or_placeholder(
        path,
        (TILE, TILE),  # 32x32 pixels
        (100, 100, 100, 255),
        f"Wall tile Lv2: {tile_name}"
    )

print(f"Loaded {len(wall_tiles_lv1)} wall Lv1 tile sprites and {len(wall_tiles_lv2)} wall Lv2 tile sprites")

# Set wall tiles in WallBase module for auto-tiling
from world.buildings.wall_base import set_wall_tiles
set_wall_tiles(wall_tiles_lv1, wall_tiles_lv2)

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

# Collision map for fast tile-based collision detection
collision_map = CollisionMap(GRID_WIDTH, GRID_HEIGHT, TILE)
resources = Resources(wood=0, iron=0, food=0, coins=0)
current_difficulty = Difficulty.EASY
current_game_mode = GameMode.TEN_DAY

# Building groups
building_group = pygame.sprite.Group()
turret_group = pygame.sprite.Group()

# Enemy groups
enemy_group = pygame.sprite.Group()

# Projectile groups
projectile_group = pygame.sprite.Group()

# Coin drops list for visual coin effects
coin_drops = []

build_mode = False  # True when player wants to build
selected_building_type = None  # Building class to build
selected_building = None  # Currently selected building
pending_construction = None  # Building being constructed (can cancel)

gather_mode = False  # True when player wants to assign workers to nodes
debug_movable_nodes = False  # True when player wants to move research nodes (M key)

# Build ghost responsiveness - track mouse position separately for instant updates
build_ghost_grid_pos = None  # Grid position for build ghost (updated on MOUSEMOTION)
build_ghost_can_place = False  # Whether current position is valid

# Building placement feedback
placement_glow_tiles = []  # List of (grid_pos, time) for placement glow effects
selection_highlight_building = None  # Building currently showing selection highlight
selection_highlight_timer = None  # AnimationTimer for selection highlight

# Button animations - store animation timers per button
button_animations = {}  # {(building_class, 'hover'|'click'): AnimationTimer}

# Coin Drop System
class CoinDrop:
    """Visual coin drop effect when enemies are killed"""
    def __init__(self, pos: pygame.Vector2, coin_value: int, frames: list):
        self.pos = pygame.Vector2(pos)
        self.start_y = pos.y
        self.coin_value = coin_value
        self.frames = frames
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.1  # 100ms per frame
        
        # Physics
        self.velocity_y = -150.0  # Initial upward velocity (bounce up)
        self.gravity = 400.0  # Gravity acceleration
        self.collected = False
        self.collect_timer = 0.0
        self.collect_delay = 1.5  # Auto-collect after 1.5 seconds
        
        # Image and rect
        if self.frames:
            self.image = self.frames[0]
            self.rect = self.image.get_rect(center=self.pos)
        else:
            self.image = None
            self.rect = pygame.Rect(self.pos.x, self.pos.y, 16, 16)
    
    def update(self, dt: float, resources):
        """Update coin drop physics and animation"""
        if self.collected:
            return
        
        # Update position with physics
        self.velocity_y += self.gravity * dt
        self.pos.y += self.velocity_y * dt
        
        # Bounce effect - if coin falls below start position, stop it
        if self.pos.y >= self.start_y:
            self.pos.y = self.start_y
            self.velocity_y = 0.0  # Stop falling
        
        # Update animation
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay and self.frames:
            self.animation_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]
        
        # Auto-collect timer
        self.collect_timer += dt
        if self.collect_timer >= self.collect_delay:
            self.collect(resources)
        
        # Update rect
        if self.image:
            self.rect = self.image.get_rect(center=self.pos)
        else:
            self.rect.center = self.pos
    
    def collect(self, resources):
        """Collect the coin and award coins to player"""
        if not self.collected:
            self.collected = True
            resources.add_coins(self.coin_value)
    
    def draw(self, surface: pygame.Surface):
        """Draw the coin drop"""
        if self.collected or not self.image:
            return
        surface.blit(self.image, self.rect)

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

# Initialize enemy pooling system (pre-allocates enemies at game start)
from core.enemy_pool import EnemyPool
EnemyPool.initialize(enemy_factory)
print("Enemy pooling system initialized")

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
    def __init__(self, resources, grid, screen_height=c.SCREEN_HEIGHT, enemy_group=None, projectile_group=None, building_group=None, sound_system=None, wave_manager=None, pathfinding=None, node_group=None, survivor_group=None, collision_map=None):
        self.resources = resources
        self.grid = grid
        self.screen_height = screen_height
        self.enemy_group = enemy_group
        self.projectile_group = projectile_group
        self.building_group = building_group
        self.sound_system = sound_system
        self.wave_manager = wave_manager
        self.pathfinding = pathfinding
        self.collision_map = collision_map
        self.tile_size = TILE  # For easy access
        
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
            "max_survivors": 0,  # Base max survivors (can be increased by research)
        }
        
        # Day event manager (will be set after initialization)
        self.day_events = None
        self.hud = None
        self.nodes = node_group if node_group else pygame.sprite.Group()
        self.survivor_group = survivor_group if survivor_group else pygame.sprite.Group()
        
        # Cache HQ reference for performance (avoid searching building_group every frame)
        self.hq = None

        self.production_multipliers = {"sawmill": 1.0, "smelter": 1.0}
        self.current_difficulty = Difficulty.EASY
        self.sawmill_level = 0

        self.buildings_by_type: Dict[str, list] = {}
        # Visual phase decoupled from logic state (to control when background changes)
        self.visual_phase = None  # will be set after WaveManager is attached
    
    def enemy_count(self):
        """Get current enemy count"""
        return len(self.enemy_group) if self.enemy_group else 0
    
    def get_max_survivors(self) -> int:
        """Get maximum survivors allowed (base + research modifiers)"""
        base_max = 3  # Starting 3 survivors
        research_bonus = self.modifiers.get("max_survivors", 0)
        return base_max + int(research_bonus)
    
    def get_current_survivor_count(self) -> int:
        """Get current alive survivor count"""
        return sum(1 for s in self.survivor_group if s.alive)
    
    def can_hire_survivor(self) -> bool:
        """Check if player can hire another survivor"""
        return self.get_current_survivor_count() < self.get_max_survivors()
    
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
            if b and hasattr(b, "update_sprite"):
                b.world = self  # Ensure world is set
                b.update_sprite()
    
    def autotile_wall_and_neighbors(self, gx, gy):
        """Alias for refresh_wall_and_neighbors (backwards compatibility)."""
        self.refresh_wall_and_neighbors(gx, gy)

    # ----- Building registry helpers -----
    def register_building(self, building):
        type_id = getattr(building, "TYPE_ID", building.__class__.__name__.lower())
        type_id = type_id.lower()
        self.buildings_by_type.setdefault(type_id, []).append(building)
        
        # Cache HQ reference when registering
        from world.buildings.hq import HQ
        if isinstance(building, HQ):
            self.hq = building

    def unregister_building(self, building):
        type_id = getattr(building, "TYPE_ID", building.__class__.__name__.lower()).lower()
        if type_id in self.buildings_by_type:
            try:
                self.buildings_by_type[type_id].remove(building)
                if not self.buildings_by_type[type_id]:
                    del self.buildings_by_type[type_id]
            except ValueError:
                pass
        
        # Clear HQ cache if this building was HQ
        from world.buildings.hq import HQ
        if isinstance(building, HQ) and self.hq == building:
            self.hq = None

    def upgrade_buildings(self, type_id: str, new_level: int):
        type_id = type_id.lower()
        for building in self.buildings_by_type.get(type_id, []):
            building.upgrade_level(new_level)
    
    def get_quadrant_noise(self) -> Dict[str, float]:
        """
        Calculate noise value for each quadrant based on turret positions.
        Divides map into 4 quadrants and sums turret.noise_value inside each.
        
        Returns:
            Dictionary mapping quadrants to noise values: {"top": N1, "bottom": N2, "left": N3, "right": N4}
        """
        import constants as c
        
        # Get screen dimensions for quadrant calculation
        screen_width = c.SCREEN_WIDTH
        screen_height = c.SCREEN_HEIGHT
        mid_x = screen_width // 2
        mid_y = screen_height // 2
        
        # Initialize noise values for each quadrant
        noise_values = {
            "top": 0.0,
            "bottom": 0.0,
            "left": 0.0,
            "right": 0.0
        }
        
        # Check all buildings for turrets
        if not self.building_group:
            return noise_values
        
        for building in self.building_group:
            # Check if building has noise_value (turrets)
            if hasattr(building, 'noise_value'):
                noise = getattr(building, 'noise_value', 0.0)
                if noise > 0:
                    # Determine which quadrant(s) this turret is in
                    pos_x = building.pos.x if hasattr(building, 'pos') else (building.grid_x * 32 + 16) if hasattr(building, 'grid_x') else screen_width // 2
                    pos_y = building.pos.y if hasattr(building, 'pos') else (building.grid_y * 32 + 16) if hasattr(building, 'grid_y') else screen_height // 2
                    
                    # Determine quadrant (top/bottom/left/right based on position)
                    # Top: y < mid_y
                    # Bottom: y >= mid_y
                    # Left: x < mid_x
                    # Right: x >= mid_x
                    
                    if pos_y < mid_y:
                        noise_values["top"] += noise
                    else:
                        noise_values["bottom"] += noise
                    
                    if pos_x < mid_x:
                        noise_values["left"] += noise
                    else:
                        noise_values["right"] += noise
        
        return noise_values

# Initialize core systems first
game_state_manager = GameStateManager()
# Start in menu state
game_state_manager.set_state(GameState.MENU)
game_state_manager.difficulty = Difficulty.EASY
save_system = SaveSystem()
sound_system = SoundSystem()

# Initialize pathfinding (will be updated with building_group after buildings are created)
from world.pathfinding import Pathfinding
pathfinding = Pathfinding(grid, building_group)

# Node and survivor groups
node_group = pygame.sprite.Group()
survivor_group = pygame.sprite.Group()

# Initialize world (wave_manager will be added after initialization)
world = World(resources, grid, enemy_group=enemy_group, projectile_group=projectile_group, building_group=building_group, sound_system=sound_system, pathfinding=pathfinding, node_group=node_group, survivor_group=survivor_group, collision_map=collision_map)

# Initialize research system (needed before building buttons)
research_manager = ResearchManager(world)
world.research = research_manager

# Initialize wave manager
wave_manager = WaveManager(world, waves_config, difficulty="normal")
# Update world with wave_manager reference
world.wave_manager = wave_manager

# Initialize visual phase to current logical state at startup
world.visual_phase = wave_manager.state

# Initialize responsiveness systems
input_buffer = InputBuffer(buffer_duration=0.125)  # 125ms buffer

# Initialize UI components with pixel fonts
hud = HUD(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, daycounter_frames, red_number_frames, blue_number_frames, font_large, font_medium, font_small, hq_health_bar_frames)
# Set HUD reference in world for day events
world.hud = hud

# Initialize day event manager
day_event_manager = DayEventManager(world)
world.day_events = day_event_manager
game_over_screen = GameOverScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, font_huge, font_medium, font_small)
pause_menu = PauseMenu(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, font_huge, font_medium)
start_screen = StartScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, font_huge, font_medium)
difficulty_screen = SelectDifficultyScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, sound_system)
mode_screen = SelectModeScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT, font_huge, sound_system)
# Play gamestart sound when start screen is first shown
sound_system.play("gamestart")
# Create scaled versions for building panel fonts
custom_font_blue_large = create_scaled_custom_font(custom_font_blue, 2.18, 48) if custom_font_blue else None  # ~48px
custom_font_blue_medium_panel = create_scaled_custom_font(custom_font_blue, 1.45, 32) if custom_font_blue else None  # ~32px
custom_font_red_medium_panel = create_scaled_custom_font(custom_font_red, 1.45, 32) if custom_font_red else None  # ~32px for unavailable

building_panel = BuildingPanel(
    c.SCREEN_WIDTH, c.SCREEN_HEIGHT, 
    upgrade_panel_frames, upgrade_panel_darken_frames, [], 
    upgrade_button_frames, demolish_button_frames, 
    health_bar_frames, current_level_frames, next_level_frames, 
    font_large=custom_font_large if custom_font_large else font_large,
    font_medium=custom_font_medium if custom_font_medium else font_medium,
    font_small=custom_font_small if custom_font_small else font_small,
    font_blue=custom_font_blue_medium_panel if custom_font_blue_medium_panel else custom_font_medium if custom_font_medium else font_medium,  # Blue for hover
    font_red=custom_font_red_medium_panel if custom_font_red_medium_panel else font_medium,  # Red for demolish/unavailable
    font_yellow=custom_font_medium if custom_font_medium else font_medium  # Yellow for default
)
# Create scaled versions for tooltip fonts
custom_font_blue_medium = create_scaled_custom_font(custom_font_blue, 1.45, 32) if custom_font_blue else None  # ~32px for tooltips
custom_font_blue_small = create_scaled_custom_font(custom_font_blue, 1.09, 24) if custom_font_blue else None  # ~24px for tooltips
custom_font_red_medium = create_scaled_custom_font(custom_font_red, 1.45, 32) if custom_font_red else None  # ~32px for warnings
custom_font_red_small = create_scaled_custom_font(custom_font_red, 1.09, 24) if custom_font_red else None  # ~24px for warnings

tooltip_manager = BuildTooltipManager(
    build_item_config, 
    (c.SCREEN_WIDTH, c.SCREEN_HEIGHT),
    font_blue=custom_font_blue_medium if custom_font_blue_medium else custom_font_medium,  # Blue for hover/selection
    font_red=custom_font_red_small if custom_font_red_small else font_small,  # Red for warnings/unavailable
    font_yellow=custom_font_small if custom_font_small else font_small  # Yellow for default
)


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
    """Spawn starting layout: HQ in center, 1 starting turret"""
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
    
    hq = HQ((hq_gx, hq_gy), tier=1, world=world)
    hq.state = BuildState.ACTIVE
    hq.hp = hq.max_hp
    hq.progress = hq.BUILD_TIME
    building_group.add(hq)
    world.register_building(hq)
    grid.set_footprint_blocked((hq_gx, hq_gy), HQ.FOOTPRINT, True)
    # Mark tiles as solid in collision map
    hq.on_complete(world)
    
    # Store HQ reference in world
    if 'world' in globals():
        world.hq = hq
    
    print(f"HQ spawned at grid position ({hq_gx}, {hq_gy}) - center")
    
    # --- Place single starting turret ---
    global turret_sprite_sheets, turret_base_images
    
    # Place 1 turret above HQ
    turret_gx = center_x
    turret_gy = center_y - 4  # 4 tiles above HQ center
    if 0 <= turret_gx < W_TILES and 0 <= turret_gy < H_TILES:
        t = BallisticTurret((turret_gx, turret_gy), turret_sprite_sheets, turret_base_images, tier=1)
        t.state = BuildState.ACTIVE
        t.hp = t.max_hp
        t.progress = t.BUILD_TIME
        building_group.add(t)
        world.register_building(t)
        turret_group.add(t)
        grid.set_footprint_blocked((turret_gx, turret_gy), BallisticTurret.FOOTPRINT, True)
        print(f"Starting turret placed at ({turret_gx}, {turret_gy})")
    
    print(f"Starting layout spawned: HQ at center ({hq_gx}, {hq_gy}), 1 turret")
    
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

def hire_survivor():
    """Hire a new survivor at HQ (cost: 50 coins)"""
    global survivor_group, building_group, resources, world
    
    # Check if player can hire more survivors
    if not world or not world.can_hire_survivor():
        return False
    
    # Check if player has enough coins
    if resources.coins < HIRE_SURVIVOR_COST:
        return False
    
    # Find HQ position
    hq_pos = None
    for building in building_group:
        if isinstance(building, HQ):
            hq_pos = building.pos
            break
    
    if not hq_pos:
        return False
    
    # Deduct coins
    resources.coins -= HIRE_SURVIVOR_COST
    
    # Spawn worker near HQ with slight random offset
    import random
    offset_x = random.randint(-50, 50)
    offset_y = random.randint(30, 60)
    worker_pos = (hq_pos.x + offset_x, hq_pos.y + offset_y)
    worker = Worker(worker_pos, world=world)
    survivor_group.add(worker)
    
    print(f"Hired new survivor at ({worker_pos[0]:.1f}, {worker_pos[1]:.1f}), cost: {HIRE_SURVIVOR_COST} coins")
    return True

def apply_special_event_effects(world, building_group, survivor_group, node_group, grid):
    """Apply special event effects that require direct access to game objects."""
    if not hasattr(world, 'modifiers'):
        return
    
    modifiers = world.modifiers
    
    # Handle wall HP bonus
    if "wall_hp_bonus" in modifiers and modifiers["wall_hp_bonus"] > 0:
        from world.buildings.wall_wood import WallWood
        from world.buildings.wall_iron import WallIron
        bonus = modifiers["wall_hp_bonus"]
        for building in building_group:
            if isinstance(building, (WallWood, WallIron, Wall)):
                building.hp = min(building.max_hp, building.hp + bonus)
    
    # Handle survivor grant
    if "grant_survivor" in modifiers and modifiers["grant_survivor"] > 0:
        count = modifiers["grant_survivor"]
        # Find HQ position for spawning
        hq_pos = None
        for building in building_group:
            if isinstance(building, HQ):
                hq_pos = (building.grid_x * 32 + 16, building.grid_y * 32 + 16)
                break
        if hq_pos:
            for _ in range(count):
                # Spawn a new worker near HQ
                spawn_x = hq_pos[0] + random.randint(-50, 50)
                spawn_y = hq_pos[1] + random.randint(-50, 50)
                worker = Worker((spawn_x, spawn_y), world=world)
                survivor_group.add(worker)
                if hasattr(world, 'register_survivor'):
                    world.register_survivor(worker)
    
    # Handle injured survivor
    if "injured_survivor" in modifiers and modifiers["injured_survivor"] > 0:
        # Mark a random survivor as injured (cannot gather)
        alive_workers = [s for s in survivor_group if s.alive and s.role == "worker"]
        if alive_workers:
            injured = random.choice(alive_workers)
            # Store injured status in survivor (can't gather today)
            injured.can_gather_today = False
    
    # Handle random building damage
    if "random_building_damage" in modifiers and modifiers["random_building_damage"] > 0:
        damage = modifiers["random_building_damage"]
        # Get all non-HQ buildings
        target_buildings = [b for b in building_group if not isinstance(b, HQ) and b.state == BuildState.ACTIVE]
        if target_buildings:
            target = random.choice(target_buildings)
            target.hp = max(1, target.hp - damage)
    
    # Handle extra wood nodes (applied when spawning daily nodes)
    # This is handled in spawn_daily_resource_nodes()

def spawn_daily_resource_nodes():
    """Spawn daily resource nodes in clusters around the starting structure"""
    global node_group, world, grid, building_group, building_panel
    
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
    if hasattr(world, 'modifiers'):
        if world.modifiers.get("node_spawn_bonus", False):
            num_trees += 2  # Bonus trees
            num_scrap += 2  # Bonus scrap
        # Apply extra wood nodes from events
        extra_wood = world.modifiers.get("extra_wood_nodes", 0)
        if extra_wood > 0:
            num_trees += extra_wood
    
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
                
                # Check if position is in building panel area (bottom-right corner)
                in_building_panel_area = False
                if building_panel and hasattr(building_panel, 'panel_rect'):
                    panel_rect = building_panel.panel_rect
                    # Add some padding around the panel to prevent nodes from spawning too close
                    padding = 64  # 2 tiles
                    panel_area = pygame.Rect(
                        panel_rect.left - padding,
                        panel_rect.top - padding,
                        panel_rect.width + padding * 2,
                        panel_rect.height + padding * 2
                    )
                    if panel_area.collidepoint(node_x_px, node_y_px):
                        in_building_panel_area = True
                
                # Check if position is in the bottom UI area (invisible rect: (0,960) to (1365,1080))
                ui_exclusion_rect = pygame.Rect(0, 960, 1365, 1080 - 960)
                in_ui_exclusion_area = ui_exclusion_rect.collidepoint(node_x_px, node_y_px)
                
                # Ensure position is valid and not too close to compound and not in building panel or UI exclusion area
                if (0 <= node_gx < grid.width and 0 <= node_gy < grid.height and
                    not grid.is_blocked(node_gx, node_gy) and
                    not in_building_panel_area and
                    not in_ui_exclusion_area and
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
            
            # Check if position is in building panel area (bottom-right corner)
            in_building_panel_area = False
            if building_panel and hasattr(building_panel, 'panel_rect'):
                panel_rect = building_panel.panel_rect
                # Add some padding around the panel to prevent nodes from spawning too close
                padding = 64  # 2 tiles
                panel_area = pygame.Rect(
                    panel_rect.left - padding,
                    panel_rect.top - padding,
                    panel_rect.width + padding * 2,
                    panel_rect.height + padding * 2
                )
                if panel_area.collidepoint(node_x_px, node_y_px):
                    in_building_panel_area = True
            
            # Check if position is in the bottom UI area (invisible rect: (0,960) to (1365,1080))
            ui_exclusion_rect = pygame.Rect(0, 960, 1365, 1080 - 960)
            in_ui_exclusion_area = ui_exclusion_rect.collidepoint(node_x_px, node_y_px)
            
            if (0 <= node_gx < grid.width and 0 <= node_gy < grid.height and
                not grid.is_blocked(node_gx, node_gy) and
                not in_building_panel_area and
                not in_ui_exclusion_area):
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
            
            # Check if position is in building panel area (bottom-right corner)
            in_building_panel_area = False
            if building_panel and hasattr(building_panel, 'panel_rect'):
                panel_rect = building_panel.panel_rect
                # Add some padding around the panel to prevent nodes from spawning too close
                padding = 64  # 2 tiles
                panel_area = pygame.Rect(
                    panel_rect.left - padding,
                    panel_rect.top - padding,
                    panel_rect.width + padding * 2,
                    panel_rect.height + padding * 2
                )
                if panel_area.collidepoint(node_x_px, node_y_px):
                    in_building_panel_area = True
            
            # Check if position is in the bottom UI area (invisible rect: (0,960) to (1365,1080))
            ui_exclusion_rect = pygame.Rect(0, 960, 1365, 1080 - 960)
            in_ui_exclusion_area = ui_exclusion_rect.collidepoint(node_x_px, node_y_px)
            
            if (0 <= node_gx < grid.width and 0 <= node_gy < grid.height and
                not grid.is_blocked(node_gx, node_gy) and
                not in_building_panel_area and
                not in_ui_exclusion_area):
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
    game_state_manager.difficulty = difficulty
    if 'tooltip_manager' in globals() and tooltip_manager:
        tooltip_manager.set_difficulty(difficulty)
    if hasattr(wave_manager, "difficulty"):
        wave_manager.difficulty = difficulty.name.lower()
    research_manager.apply_difficulty_scaling(settings.research_total_target, settings.research_cost_multiplier)


def restart_game():
    """Restart game"""
    global building_group, turret_group, enemy_group, projectile_group, resources, wave_manager, game_state_manager, node_group, survivor_group, coin_drops
    # Reset game state
    building_group.empty()
    turret_group.empty()
    enemy_group.empty()
    projectile_group.empty()
    node_group.empty()
    survivor_group.empty()
    coin_drops.clear()  # Clear coin drops on restart
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
        
        # Auto-tile all walls after loading (ensures walls have correct sprites)
        for building in building_group:
            if hasattr(building, 'TYPE_ID') and building.TYPE_ID.startswith("wall"):
                if hasattr(building, 'update_sprite'):
                    building.world = world
                    building.update_sprite()
        
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
    sound_system.play("gamestart")
    game_state_manager.set_state(GameState.SELECT_DIFFICULTY)


def handle_difficulty_selected(selection: Difficulty):
    """Apply difficulty and show mode selection."""
    global current_difficulty
    current_difficulty = selection
    apply_difficulty_settings(selection, reset_resources=True)
    difficulty_screen.hide()
    mode_screen.show()
    sound_system.play("gamestart")
    game_state_manager.set_state(GameState.SELECT_MODE)


def handle_difficulty_cancel():
    """Return to start screen from difficulty selection."""
    difficulty_screen.hide()
    start_screen.show()
    sound_system.play("gamestart")
    game_state_manager.set_state(GameState.MENU)


def handle_mode_selected(mode: GameMode):
    """Apply mode and start gameplay."""
    global current_game_mode
    current_game_mode = mode
    mode_screen.hide()
    game_state_manager.set_state(GameState.PLAYING)


def handle_mode_cancel():
    """Return to difficulty selection from mode selection."""
    mode_screen.hide()
    difficulty_screen.show()
    game_state_manager.set_state(GameState.SELECT_DIFFICULTY)


start_screen.on_start = open_difficulty_selection
difficulty_screen.on_select = handle_difficulty_selected
difficulty_screen.on_cancel = handle_difficulty_cancel
mode_screen.on_select = handle_mode_selected
mode_screen.on_cancel = handle_mode_cancel

# Building panel callbacks (will be set up in game loop)
def upgrade_building(building):
    """Upgrade building"""
    if not building or building.state != BuildState.ACTIVE:
        return

    current_difficulty = getattr(game_state_manager, "difficulty", world.current_difficulty)
    type_id = getattr(building, "TYPE_ID", "").lower()
    is_turret_building = type_id.startswith("turret")

    def has_resources(cost_dict):
        return (
            resources.wood >= cost_dict.get("wood", 0) and
            resources.iron >= cost_dict.get("iron", 0) and
            resources.food >= cost_dict.get("food", 0)
        )

    def pay_resources(cost_dict):
        resources.wood -= cost_dict.get("wood", 0)
        resources.iron -= cost_dict.get("iron", 0)
        resources.food -= cost_dict.get("food", 0)

    # Special case: upgrade wood wall -> iron wall
    from world.buildings.wall_wood import WallWood
    from world.buildings.wall_iron import WallIron
    if isinstance(building, WallWood):
        # Use WallIron.COST as upgrade cost (no coins)
        upgrade_cost_dict = {
            "wood": WallIron.COST.wood,
            "iron": WallIron.COST.iron,
            "food": WallIron.COST.food,
        }
        if not has_resources(upgrade_cost_dict):
            print("Not enough resources to upgrade wall to iron.")
            return

        # Pay cost
        pay_resources(upgrade_cost_dict)

        # Replace WallWood with WallIron at same position, carrying over HP ratio
        gx, gy = building.grid_x, building.grid_y
        # Compute HP ratio and new HP
        hp_ratio = building.hp / building.max_hp if building.max_hp > 0 else 1.0
        new_max_hp = WallIron.BASE_HP
        new_hp = int(new_max_hp * max(0.0, min(1.0, hp_ratio)))

        # Remove old wall from world registries
        world.unregister_building(building)
        building_group.remove(building)

        # Create new iron wall
        new_wall = WallIron((gx, gy), tier=1)
        new_wall.world = world
        new_wall.state = BuildState.ACTIVE
        new_wall.max_hp = new_max_hp
        new_wall.hp = max(1, new_hp)
        new_wall.progress = new_wall.BUILD_TIME

        # Register and add to groups
        world.register_building(new_wall)
        building_group.add(new_wall)

        # Auto-tile this wall and its neighbors
        if hasattr(world, "autotile_wall_and_neighbors"):
            world.autotile_wall_and_neighbors(gx, gy)

        # Update building panel selection to new wall
        building_panel.selected_building = new_wall

        sound_system.play("upgrade")
        print(f"Upgraded wall_wood at ({gx},{gy}) to wall_iron")
        return

    if is_turret_building:
        upgrade_info = get_next_turret_upgrade(building)
        if not upgrade_info or upgrade_info.get("is_max"):
            print("Turret is at maximum level.")
            return
        scaled_cost = scale_upgrade_cost(upgrade_info["base_cost"], current_difficulty)
        if not has_resources(scaled_cost):
            print("Not enough resources for turret upgrade.")
            return
        pay_resources(scaled_cost)
        building.upgrade(world)
        sound_system.play("upgrade")
        return

    if building.tier < building.TIER_MAX:
        # Check if gate level 2 upgrade requires structural_reinforcement research
        from world.buildings.gate import Gate
        if isinstance(building, Gate) and building.tier == 1:
            # Gate level 1 -> level 2 requires structural_reinforcement research
            if not research_manager.is_unlocked("gate_lv2"):
                print("Gate level 2 requires Structural Reinforcement research.")
                return
        
        from world.building import Cost
        # Base upgrade multiplier (1.25× per tier level)
        upgrade_mult = 1.25
        base_cost = building.COST
        base_upgrade_cost = {
            "wood": int(base_cost.wood * upgrade_mult * building.tier),
            "iron": int(base_cost.iron * upgrade_mult * building.tier),
            "food": int(base_cost.food * upgrade_mult * building.tier)
        }
        # Apply difficulty-based upgrade cost multiplier
        upgrade_cost_dict = scale_upgrade_cost(base_upgrade_cost, current_difficulty)
        upgrade_cost = Cost(
            wood=upgrade_cost_dict.get("wood", 0),
            iron=upgrade_cost_dict.get("iron", 0),
            food=upgrade_cost_dict.get("food", 0)
        )
        if has_resources({"wood": upgrade_cost.wood, "iron": upgrade_cost.iron, "food": upgrade_cost.food, "coins": 0}):
            resources.wood -= upgrade_cost.wood
            resources.iron -= upgrade_cost.iron
            resources.food -= upgrade_cost.food
            building.upgrade(world)
            if hasattr(building, 'on_upgrade') and callable(building.on_upgrade):
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
        
        # Check if this is a wall before removal
        is_wall = hasattr(building, 'TYPE_ID') and building.TYPE_ID.startswith("wall")
        gx, gy = building.grid_x, building.grid_y
        
        building.refund_cost(resources, ratio=0.6, world=world)
        grid.set_footprint_blocked((gx, gy), building.FOOTPRINT, False)
        world.unregister_building(building)
        building_group.remove(building)
        if building in turret_group:
            turret_group.remove(building)
        
        # Update wall neighbors if this was a wall
        if is_wall:
            world.autotile_wall_and_neighbors(gx, gy)
        
        building_panel.hide()
        sound_system.play("button_click")
        print(f"Sold {building.TYPE_ID}")

def demolish_building(building):
    """Demolish building (no refund)"""
    if building:
        # Prevent demolishing HQ (main base)
        if isinstance(building, HQ):
            print("Cannot demolish HQ - it's the main base!")
            return
        
        # Check if this is a wall before removal
        is_wall = hasattr(building, 'TYPE_ID') and building.TYPE_ID.startswith("wall")
        gx, gy = building.grid_x, building.grid_y
        
        # Demolish without refund
        grid.set_footprint_blocked((gx, gy), building.FOOTPRINT, False)
        world.unregister_building(building)
        building_group.remove(building)
        if building in turret_group:
            turret_group.remove(building)
        
        # Update wall neighbors if this was a wall
        if is_wall:
            world.autotile_wall_and_neighbors(gx, gy)
        
        building_panel.hide()
        sound_system.play("button_click")
        print(f"Demolished {building.TYPE_ID}")

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
    """Clear all enemies (release to pool)"""
    count = len(enemy_group)
    for enemy in list(enemy_group):
        enemy_group.remove(enemy)
        EnemyPool.release(enemy)
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
    """Kill all enemies (they will be released to pool on death)"""
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

def debug_toggle_ui_rectangles():
    """Toggle showing UI element rectangles"""
    debug_system.show_ui_rectangles = not debug_system.show_ui_rectangles
    status = "ON" if debug_system.show_ui_rectangles else "OFF"
    print(f"Debug: Show UI rectangles {status}")

def debug_skip_state():
    """Skip to the next game state (DAY -> NIGHT -> SUMMARY -> DAY)"""
    current_state = wave_manager.state
    if current_state == WaveManager.STATE_DAY:
        # Skip to night - increment night counter when transitioning from DAY to NIGHT
        print(f"[NIGHT COUNTER] debug_skip_state: Before increment: night={wave_manager.night}")
        wave_manager.night += 1
        print(f"[NIGHT COUNTER] debug_skip_state: After increment: night={wave_manager.night}")
        wave_manager.start_night()
        recipe = wave_manager.get_wave_recipe()
        spawn_config = waves_config["spawn"]
        zombie_spawner.begin(recipe, spawn_config)
        hud.show_event(f"Debug: Skipped to Night {wave_manager.night}", 3.0)
        print(f"Debug: Skipped to night {wave_manager.night}")
    elif current_state == WaveManager.STATE_NIGHT:
        # Skip to summary (clear all enemies first - release to pool)
        for enemy in list(enemy_group):
            enemy_group.remove(enemy)
            EnemyPool.release(enemy)
        zombie_spawner.done = True
        zombie_spawner.active = False
        wave_manager.start_summary()
        hud.show_event("Debug: Skipped to Summary", 3.0)
        print("Debug: Skipped to summary")
    elif current_state == WaveManager.STATE_SUMMARY:
        # Skip to next day
        wave_manager.start_day()
        if world.day_events:
            world.day_events.roll_new_day_event(wave_manager.day)
        spawn_daily_resource_nodes()
        hud.show_event(f"Debug: Skipped to Day {wave_manager.day}", 3.0)
        print(f"Debug: Skipped to day {wave_manager.day}")

def debug_pause_cycle():
    """Pause/stop the current wave cycle (stop spawning, freeze enemies)"""
    global zombie_spawner
    if zombie_spawner.active:
        zombie_spawner.done = True
        zombie_spawner.active = False
        hud.show_event("Debug: Cycle Paused", 3.0)
        print("Debug: Wave cycle paused")
    else:
        # Resume if paused
        if wave_manager.state == WaveManager.STATE_NIGHT:
            zombie_spawner.active = True
            zombie_spawner.done = False
            hud.show_event("Debug: Cycle Resumed", 3.0)
            print("Debug: Wave cycle resumed")
        else:
            hud.show_event("Debug: Not in night phase", 2.0)
            print("Debug: Cannot resume - not in night phase")

# Register debug actions
debug_system.register_action(pygame.K_F1, "Add +100 Resources", debug_add_resources)
debug_system.register_action(pygame.K_F2, "Instant Build", debug_instant_build)
debug_system.register_action(pygame.K_F3, "Spawn Zombie @ Mouse", lambda: None)  # Handled separately
debug_system.register_action(pygame.K_F4, "Clear All Enemies", debug_clear_enemies)
debug_system.register_action(pygame.K_F5, "Clear All Buildings", debug_clear_buildings)
debug_system.register_action(pygame.K_F6, "Toggle Spawner", debug_toggle_spawner)
debug_system.register_action(pygame.K_F7, "Pause/Resume Cycle", debug_pause_cycle)
# F8: Skip State (handled manually in event loop to support Shift+F8 for Complete All Buildings)
# Additional debug actions (using number keys)
debug_system.register_action(pygame.K_1, "Add +100 Coins", debug_add_coins)
debug_system.register_action(pygame.K_2, "Unlock All Research", debug_unlock_all_research)
debug_system.register_action(pygame.K_3, "Roll Day Event", debug_roll_day_event)
debug_system.register_action(pygame.K_f, "Toggle Footprints", debug_toggle_footprints)
debug_system.register_action(pygame.K_u, "Toggle UI Rects", debug_toggle_ui_rectangles)
# F9-F11: Wave skipping (handled in event loop)
# F12: Toggle debug mode only (handled in event loop)

###################
# Helper functions for buttons
###################
def create_button_image(text, color=(100, 150, 100), width=100, height=40, use_blue_font=False):
    """Create a button image using custom button image, scaled to the specified size."""
    global building_button_image
    
    if building_button_image:
        # Scale the custom button image to the desired size
        button_img = pygame.transform.scale(building_button_image, (width, height))
    else:
        # Fallback: create a colored surface if image not loaded
        button_img = pygame.Surface((width, height))
        button_img.fill(color)
    # Text is drawn dynamically on top of buttons, so we don't draw it here
    return button_img

###################
# Create buttons for all buildings
###################
# Building buttons will be horizontal at bottom left
button_x_start = 5  # Moved left from 10
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
    (WallWood, "Wall", (120, 120, 120)),  # WallWood is level 1 wall, unlocked via perimeter_fortification
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
    GatlingTurret: "gatling",  # Research "multibarrel_mechanism" unlocks "gatling"
    WallWood: "wall_wood",  # Research "perimeter_fortification" unlocks "wall_wood"
    WallIron: "wall_iron",  # Research "structural_reinforcement" unlocks "wall_iron"
    Gate: "gate",  # Research "perimeter_fortification" unlocks "gate" (lv1)
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
        button_y = c.SCREEN_HEIGHT - button_height - 15  # 25px from bottom (moved up from 10)
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
    """Toggle the research panel overlay."""
    research_panel_ui.toggle()

research_button = ResearchButton(10, 10, 120, 40, launch_research_tree)

# Hire survivor button (cost: 50 coins)
HIRE_SURVIVOR_COST = 50
def hire_survivor_callback():
    """Callback for hire survivor button"""
    if hire_survivor():
        sound_system.play("button_click")
        return True
    return False

# Create hire survivor button similar to research button
class HireSurvivorButton:
    """Button to hire a new survivor."""
    def __init__(self, x: int, y: int, width: int, height: int, callback):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.callback = callback
        self.text = "Hire Survivor"
        self.enabled = True
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen: pygame.Surface):
        """Draw the hire survivor button."""
        # Draw button background
        bg_color = (60, 80, 100) if self.enabled else (40, 40, 40)
        pygame.draw.rect(screen, bg_color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200) if self.enabled else (100, 100, 100), self.rect, 2)
        
        # Draw text
        font = pygame.font.Font(None, 24)
        text_color = (255, 255, 255) if self.enabled else (150, 150, 150)
        label = font.render(self.text, True, text_color)
        label_rect = label.get_rect(center=(self.rect.centerx, self.rect.centery))
        screen.blit(label, label_rect)
    
    def handle_click(self, mouse_pos: tuple) -> bool:
        """Handle mouse click on button."""
        if self.enabled and self.rect.collidepoint(mouse_pos):
            self.callback()
            return True
        return False

hire_survivor_button = HireSurvivorButton(25, 200, 150, 40, hire_survivor_callback)

# Research panel UI
research_panel_ui = ResearchPanel(world, research_manager, c.SCREEN_WIDTH, c.SCREEN_HEIGHT,
                                  font_large=font_large, font_medium=font_medium, font_small=font_small)

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
    """Draw building preview at grid position with responsive feedback."""
    w, h = footprint
    gx, gy = grid_pos
    
    # Calculate pixel position for top-left corner
    px = gx * TILE
    py = gy * TILE
    
    # Draw tile highlights BEFORE preview (cheap alpha overlay)
    # Highlight each tile in the footprint
    for dx in range(w):
        for dy in range(h):
            tile_px = (gx + dx) * TILE
            tile_py = (gy + dy) * TILE
            # Light tint overlay (very cheap)
            highlight = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            if can_place:
                highlight.fill((100, 200, 255, 40))  # Soft light-blue tint for valid
            else:
                highlight.fill((255, 100, 100, 40))  # Soft red tint for invalid
            screen.blit(highlight, (tile_px, tile_py))
    
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
    """Select a building at mouse position with visual feedback."""
    global selected_building, selection_highlight_building, selection_highlight_timer
    
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
            # Start selection highlight animation (150ms)
            selection_highlight_building = building
            selection_highlight_timer = AnimationTimer(duration=0.15)
            selection_highlight_timer.start()
            return True
    
    return False

def draw_resources(screen, resources, font):
    """
    Draw resource display as a clean vertical panel on the left center.
    Uses a semi-transparent background box with proper spacing.
    """
    import math
    
    # Handle NaN values by converting to 0
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
    
    # Use consistent font for resources
    resource_font = font_small
    line_height = resource_font.get_linesize() + 4  # Extra spacing between lines
    padding = 12  # Internal padding inside the panel
    panel_x = 25  # Position from left edge (slightly inset)
    
    # Prepare resource data with labels and colors
    resource_data = [
        ("Wood", int(wood_val), (255, 255, 255)),
        ("Iron", int(iron_val), (255, 255, 255)),
        ("Food", int(food_val), (255, 255, 255)),
        ("Coins", int(coins_val), (255, 215, 0)),  # Gold color for coins
        ("Zombies", len(enemy_group), (255, 120, 120)),  # Light red for zombies
    ]
    
    # Render all text surfaces and calculate panel dimensions
    text_surfaces = []
    max_width = 0
    for label, value, color in resource_data:
        text = f"{label}: {value}"
        if label == "Zombies" and custom_font_red:
            # Use red custom font for zombie counter if available
            zombie_font = create_scaled_custom_font(custom_font_red, 1.09, 24) if custom_font_red else resource_font
            text_surface = zombie_font.render(text, True, color)
        else:
            text_surface = resource_font.render(text, True, color)
        text_surfaces.append((text_surface, label, value, color))
        max_width = max(max_width, text_surface.get_width())
    
    # Calculate panel dimensions
    panel_width = max_width + padding * 2
    panel_height = len(resource_data) * line_height + padding * 2

    # Center panel vertically on the left side (กลางซ้าย)
    panel_y = c.SCREEN_HEIGHT // 2 - panel_height // 2
    
    # Draw semi-transparent background panel
    panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_bg.fill((30, 30, 40, 200))  # Dark semi-transparent background
    # Draw border
    pygame.draw.rect(panel_bg, (80, 100, 120, 255), panel_bg.get_rect(), width=2)
    screen.blit(panel_bg, (panel_x, panel_y))
    
    # Draw resource text lines vertically with proper spacing
    current_y = panel_y + padding
    for text_surface, label, value, color in text_surfaces:
        screen.blit(text_surface, (panel_x + padding, current_y))
        current_y += line_height
    
    # DEBUG: Draw overlay rectangle for resource display area
    if debug_system.is_active() and debug_system.show_ui_rectangles:
        debug_overlay = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        debug_overlay.fill((0, 255, 255, 80))  # Cyan overlay
        screen.blit(debug_overlay, (panel_x, panel_y))

def create_building(building_class, grid_pos, *args):
    """Create a building instance based on the building class."""
    # Check if it's a turret (needs sprite sheet and base image)
    if building_class is BallisticTurret:
        if len(args) >= 2:
            sprite_sheets, base_images = args[0], args[1]
            building = building_class(grid_pos, sprite_sheets, base_images, tier=1, world=world)
            world.register_building(building)
            turret_group.add(building)
            return building
    elif building_class is PiercerTurret:
        if len(args) >= 2:
            sprite_sheets, base_images = args[0], args[1]
            building = building_class(grid_pos, sprite_sheets, base_images, tier=1, world=world)
            world.register_building(building)
            turret_group.add(building)
            return building
    elif building_class is GatlingTurret:
        if len(args) >= 2:
            sprite_sheets, base_images = args[0], args[1]
            building = building_class(grid_pos, sprite_sheets, base_images, tier=1, world=world)
            world.register_building(building)
            turret_group.add(building)
            return building
    else:
        # Other buildings just need grid position
        building = building_class(grid_pos, tier=1, world=world)
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
font = font_small  # Use pixel font for debug/info text
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
        # Update world.modifiers with effective modifiers (including max_survivors)
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
    
    if game_state_manager.get_state() == GameState.SELECT_MODE:
        mode_screen.update(dt)
        mode_screen.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                mode_screen.handle_event(event)
        pygame.display.flip()
        continue
    
    # Fill screen with background
    # Draw grass tile map background
    
    # Get mouse position
    mouse_pos = pygame.mouse.get_pos()
    
    # Calculate how many tiles we need to cover the screen
    tiles_x = (c.SCREEN_WIDTH + TILE - 1) // TILE  # Ceiling division to ensure full coverage
    tiles_y = (c.SCREEN_HEIGHT + TILE - 1) // TILE  # Ceiling division to ensure full coverage
    
    # Draw grass tiles across the entire screen with variation
    # Select day or night tiles based on world.visual_phase (decoupled from logic state)
    is_night = (getattr(world, "visual_phase", wave_manager.state) == WaveManager.STATE_NIGHT)
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
    
    
    # Update selection highlight animation
    if selection_highlight_timer:
        if selection_highlight_timer.is_complete():
            selection_highlight_building = None
            selection_highlight_timer = None
        else:
            selection_highlight_timer.get_progress()  # Update timer
    
    # Update placement glow effects (remove expired ones)
    import time as time_module
    current_time = time_module.time()
    placement_glow_tiles = [(pos, t) for pos, t in placement_glow_tiles if (current_time - t) < 0.1]  # 100ms glow
    
    ###################
    # Draw building construction menu background (bottom left)
    ###################
    if building_menu_bg and buttons:
        # Calculate button area bounds
        num_buttons = len(buttons)
        menu_width = max(building_menu_bg.get_width(), num_buttons * button_spacing + 20)
        menu_height = building_menu_bg.get_height()
        menu_x = 0  # Bottom left
        menu_y = c.SCREEN_HEIGHT - menu_height
        
        # Draw the background
        screen.blit(building_menu_bg, (menu_x, menu_y))
    
    ###################
    # Handle button clicks and hover tooltips with animations
    ###################
    tooltip_shown = False
    active_difficulty = getattr(game_state_manager, "difficulty", world.current_difficulty)
    for building_class, button_data in buttons.items():
        button_obj = button_data['button']
        is_hovering = button_obj.rect.collidepoint(mouse_pos)
        is_selected = (selected_building_type == building_class)
        
        # Handle button hover animation (1.00 -> 1.05 on hover, 80ms)
        hover_key = (building_class, 'hover')
        click_key = (building_class, 'click')
        
        if is_hovering:
            if hover_key not in button_animations:
                anim = AnimationTimer(duration=0.08)  # 80ms
                anim.start()
                button_animations[hover_key] = anim
            hover_anim = button_animations[hover_key]
            hover_scale = hover_anim.get_value(1.0, 1.05)
        else:
            if hover_key in button_animations:
                hover_anim = button_animations[hover_key]
                if hover_anim.is_active:
                    hover_anim.stop()
                del button_animations[hover_key]
            hover_scale = 1.0
        
        # Handle button click animation (1.05 -> 0.95 -> 1.00, 30ms)
        if click_key in button_animations:
            click_anim = button_animations[click_key]
            if click_anim.is_active:
                click_progress = click_anim.get_progress()
                if click_progress < 0.5:
                    # First half: 1.05 -> 0.95
                    click_scale = click_anim.get_value(1.05, 0.95)
                else:
                    # Second half: 0.95 -> 1.00
                    click_scale = click_anim.get_value(0.95, 1.0)
            else:
                del button_animations[click_key]
                click_scale = 1.0
        else:
            click_scale = 1.0
        
        # Combine scales (hover takes precedence if both active)
        final_scale = hover_scale if is_hovering else click_scale
        
        # Draw button with scale
        button_center = button_obj.rect.center
        button_image = button_obj.image
        if final_scale != 1.0:
            # Scale button
            scaled_size = (int(button_image.get_width() * final_scale), 
                          int(button_image.get_height() * final_scale))
            scaled_image = pygame.transform.scale(button_image, scaled_size)
            scaled_rect = scaled_image.get_rect(center=button_center)
            screen.blit(scaled_image, scaled_rect)
        else:
            screen.blit(button_image, button_obj.rect)
        
        # Handle click detection (check original rect, not scaled)
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if is_hovering and mouse_pressed and not button_obj.clicked:
            button_obj.clicked = True
            # Start click animation
            click_anim = AnimationTimer(duration=0.03)  # 30ms
            click_anim.start()
            button_animations[click_key] = click_anim
            sound_system.play("button_click")
            
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
        
        # Reset clicked state when mouse released
        if not mouse_pressed:
            button_obj.clicked = False
        
        # Draw blue glow for selected building button
        if is_selected:
            glow_surface = pygame.Surface((button_obj.rect.width + 6, button_obj.rect.height + 6), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (100, 150, 255, 120), (0, 0, button_obj.rect.width + 6, button_obj.rect.height + 6), 3)
            glow_rect = glow_surface.get_rect(center=button_center)
            screen.blit(glow_surface, glow_rect)
        
        # Show tooltip on hover
        if is_hovering:
            tooltip_manager.show_build_tooltip(
                building_class,
                button_obj.rect,
                resources,
                research_manager,
                world=world,
                difficulty=active_difficulty,
            )
            tooltip_shown = True

    if (
        building_panel.is_visible
        and building_panel.selected_building
        and getattr(building_panel.selected_building, "TYPE_ID", "").startswith("turret")
        and building_panel.upgrade_button_rect
        and building_panel.upgrade_button_rect.collidepoint(mouse_pos)
    ):
        tooltip_manager.show_upgrade_tooltip(
            building_panel.selected_building,
            building_panel.upgrade_button_rect,
            resources,
            active_difficulty,
        )
        tooltip_shown = True

    if not tooltip_shown:
        tooltip_manager.hide_tooltip()
    
    # DEBUG: Draw overlay rectangles for build menu buttons (bottom-left)
    if debug_system.is_active() and debug_system.show_ui_rectangles and buttons:
        # Calculate total width of button row
        num_buttons = len(buttons)
        total_button_width = num_buttons * button_spacing
        button_row_y = c.SCREEN_HEIGHT - button_height - 15  # Match button_y position
        button_overlay = pygame.Surface((total_button_width, button_height), pygame.SRCALPHA)
        button_overlay.fill((255, 128, 0, 80))  # Orange overlay
        screen.blit(button_overlay, (button_x_start, button_row_y))
    
    # Highlight selected button and draw button text with appropriate colors
    active_difficulty = getattr(game_state_manager, "difficulty", world.current_difficulty)
    for building_class, button_data in buttons.items():
        button_obj = button_data['button']
        label = button_data['label']
        
        # Determine font color: Blue if selected (build mode), Red if not enough resources, Yellow if enough resources
        is_selected = (selected_building_type == building_class)
        has_enough_resources = True
        
        if not is_selected:
            # Check if we have enough resources to build
            effective_cost = building_class.get_scaled_cost(world=world, difficulty=active_difficulty)
            has_enough_resources = (
                resources.wood >= effective_cost.wood and
                resources.iron >= effective_cost.iron and
                resources.food >= effective_cost.food and
                resources.coins >= effective_cost.coins
            )
        
        # Select appropriate font based on state
        if is_selected:
            # Blue font for selected (build mode)
            button_font = create_scaled_custom_font(custom_font_blue, 0.91, 20) if custom_font_blue else font_tiny
            text_color = (255, 255, 255)  # White color with blue font
        elif not has_enough_resources:
            # Red font for not enough resources
            button_font = create_scaled_custom_font(custom_font_red, 0.91, 20) if custom_font_red else font_tiny
            text_color = (255, 255, 255)  # White color with red font
        else:
            # Yellow font for enough resources (default)
            button_font = custom_font_tiny if custom_font_tiny else font_tiny
            text_color = (255, 255, 255)  # White color with yellow font
        
        # Draw text on top of button
        text_surface = button_font.render(label, True, text_color)
        text_rect = text_surface.get_rect(center=button_obj.rect.center)
        screen.blit(text_surface, text_rect)
        
        # Draw highlight for selected button
        if is_selected:
            pygame.draw.rect(screen, (255, 255, 0), button_obj.rect, 3)

    tooltip_manager.draw(screen)
    
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
        # OPTIMIZED: Also cache HQ reference when we see it
        if isinstance(building, HQ):
            if world and not world.hq:
                world.hq = building  # Cache HQ reference
            if building.hp <= 0:
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
        
        # Check if this is HQ before unregistering (to clear cache)
        is_hq = isinstance(building, HQ)
        
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
                # PERFECT FLOW FOR DAY PHASE START:
                # 1. System Popup: "Day X Begins"
                # 2. Daily Upkeep (survivor food consumption - NOT an event)
                # 3. Luck Roll → Event Type
                # 4. Pick Random Event Matching Type + Phase = Day
                # 5. Show Event Popup
                # 6. Apply Event Effects
                # 7. Spawn daily nodes
                
                # STEP 1: SYSTEM POPUP - "Day X Begins" (separate from events)
                if hud:
                    hud.show_event(
                        text=f"Day {wave_manager.day} Begins",
                        duration=2.0,
                        title=f"Day {wave_manager.day} Begins",
                        description="",
                        effects=[],
                        event_type="neutral"
                    )
                
                # STEP 2: DAILY UPKEEP - Survivor food consumption (automatic, not an event)
                # Reset all survivors to can gather (injured status cleared)
                for survivor in survivor_group:
                    if survivor.alive:
                        survivor.can_gather_today = True
                
                alive_survivors = sum(1 for s in survivor_group if s.alive)
                food_needed = alive_survivors
                
                if food_needed > 0:
                    if resources.food >= food_needed:
                        # Deduct food (automatic upkeep)
                        resources.food -= food_needed
                        # Don't show popup for normal consumption - it's expected
                    else:
                        # Insufficient food - reduce HQ HP (starvation effect)
                        food_shortage = food_needed - resources.food
                        starving_survivors = food_shortage
                        resources.food = 0  # Use all remaining food
                        
                        # Find HQ and reduce HP - OPTIMIZED: Use cached HQ reference
                        hq_building = world.hq if world and hasattr(world, 'hq') and world.hq else None
                        
                        if hq_building:
                            # Reduce HP by shortage amount (each missing food = 1 HP damage)
                            damage = starving_survivors
                            hq_building.hp = max(0, hq_building.hp - damage)
                            if hud:
                                hud.show_event(
                                    text=f"Food Shortage! {starving_survivors} survivors starving.",
                                    duration=3.0,
                                    title="Starvation Warning",
                                    description=f"HQ took {damage} damage from food shortage.",
                                    effects=[],
                                    event_type="negative"
                                )
                                sound_system.play("building_damaged")
                            
                            # Check if HQ died from food shortage
                            if hq_building.hp <= 0:
                                if not game_over_screen.is_visible:
                                    game_state_manager.game_over()
                                    game_over_screen.show(GameState.GAME_OVER, {
                                        "nights": wave_manager.night - 1,
                                        "enemies_killed": wave_manager.enemies_killed,
                                        "buildings_built": len([b for b in building_group if not isinstance(b, HQ)])
                                    })
                                    sound_system.play("game_over")
                                    hq_building.state = BuildState.DESTROYED
                                    # Game over - continue to next iteration (game over screen will be shown)
                
                # STEP 3-6: LUCK-BASED RANDOM EVENT SYSTEM
                # Always roll an event (luck determines type: positive/mixed/negative)
                if world.day_events:
                    world.day_events.roll_new_day_event(wave_manager.day, phase="day")
                    # Apply special event effects (wall HP, survivors, etc.)
                    apply_special_event_effects(world, building_group, survivor_group, node_group, grid)
                
                # STEP 7: Spawn daily resource nodes
                spawn_daily_resource_nodes()

                # Only after all day-start tasks are complete, switch visual theme to DAY
                world.visual_phase = WaveManager.STATE_DAY
            elif wave_manager.state == WaveManager.STATE_NIGHT:
                # PERFECT FLOW FOR NIGHT PHASE START:
                # 1. Luck Roll → Event Type
                # 2. Pick Random Event Matching Type + Phase = Night
                # 3. Show Event Popup
                # 4. Apply Event Effects
                # 5. Spawn waves (with wave size modifier if present)
                
                # STEP 1-4: LUCK-BASED RANDOM EVENT SYSTEM
                # Always roll a night event (luck determines type: positive/mixed/negative)
                if world.day_events:
                    world.day_events.roll_new_day_event(wave_manager.night, phase="night")
                    # Apply special event effects
                    apply_special_event_effects(world, building_group, survivor_group, node_group, grid)
                
                # STEP 5: Spawn zombie waves (apply wave size modifier if present)
                recipe = wave_manager.get_wave_recipe()
                # Apply wave size modifier from event if present
                if hasattr(world, 'modifiers') and "zombie_wave_size_mult" in world.modifiers:
                    size_mult = world.modifiers["zombie_wave_size_mult"]
                    if size_mult != 1.0:
                        # Scale all enemy counts in recipe
                        scaled_recipe = {}
                        for enemy_type, count in recipe.items():
                            scaled_recipe[enemy_type] = max(1, int(count * size_mult))
                        recipe = scaled_recipe
                
                spawn_config = waves_config["spawn"]
                zombie_spawner.begin(recipe, spawn_config)
                
                sound_system.play("wave_start")
                wave_manager.enemies_spawned = 0

                # After night-start setup, switch visual theme to NIGHT
                world.visual_phase = WaveManager.STATE_NIGHT
            elif wave_manager.state == WaveManager.STATE_SUMMARY:
                # Just started summary - autosave
                save_system.save_world(world, wave_manager, game_state_manager, resources)
                # SYSTEM POPUP - "Night X Clear" (separate from events)
                if hud:
                    # Use wave_manager.night value (the night that just completed)
                    # When summary starts, night number is correct (before increment)
                    print(f"[NIGHT COUNTER] In STATE_SUMMARY - wave_manager.night={wave_manager.night}")
                    last_night_num = max(1, wave_manager.night)
                    print(f"[NIGHT COUNTER] Announcement will show: 'Night {last_night_num} Cleared'")
                    hud.show_event(
                        text=f"Night {last_night_num} Cleared",
                        duration=2.0,
                        title=f"Night {last_night_num} Cleared",
                        description="",
                        effects=[],
                        event_type="neutral"
                    )
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
    
    # Build spatial grid for turret targeting (before turrets update)
    # OPTIMIZED: Reuse spatial grid instead of creating new one every frame
    if not hasattr(world, '_spatial_grid') or world._spatial_grid is None:
        world._spatial_grid = SpatialGrid(cell_size=128)
    spatial_grid = world._spatial_grid
    spatial_grid.clear()  # Clear instead of creating new object
    for enemy in enemy_group:
        if enemy.alive:
            spatial_grid.insert(enemy)
    world.spatial_grid = spatial_grid  # Make spatial grid available to turrets
    
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
        if hasattr(enemy, 'reached_bottom') and enemy.reached_bottom:
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
    
    # Debug: Print removal info if any enemies being removed
    if enemies_to_remove and ('_last_remove_log' not in globals() or globals()['_last_remove_log'] != len(enemies_to_remove)):
        globals()['_last_remove_log'] = len(enemies_to_remove)
        print(f"DEBUG: Removing {len(enemies_to_remove)} enemies (before: {len(enemy_group)}, after: {len(enemy_group) - len(enemies_to_remove)})")
    
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
            
            # Spawn visual coin drop instead of directly adding coins
            if coin_frames:
                coin_drop = CoinDrop(enemy.pos.copy(), coin_reward, coin_frames)
                coin_drops.append(coin_drop)
                # Play coin drop sound
                sound_system.play("coin")
            else:
                # Fallback: directly add coins if no sprite frames available
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
    
    # Remove dead/reached-bottom enemies (release to pool instead of deleting)
    for enemy in enemies_to_remove:
        enemy_group.remove(enemy)
        # Release enemy back to pool for reuse
        EnemyPool.release(enemy)
    
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
            
            # Handle collision with enemies (prevent overlap) - OPTIMIZED: Use spatial grid
            if world and hasattr(world, 'spatial_grid') and world.spatial_grid:
                # Use spatial grid for efficient nearby enemy lookup instead of checking all enemies
                nearby_enemies = world.spatial_grid.get_nearby(survivor.pos, radius_cells=1)
                for enemy in nearby_enemies:
                    if not enemy.alive:
                        continue
                    enemy_dist = (survivor.pos - enemy.pos).length()
                    min_dist = survivor.SURVIVOR_RADIUS + enemy.ZOMBIE_RADIUS
                    if enemy_dist < min_dist and enemy_dist > 0.1:
                        # Push apart
                        push_dir = (survivor.pos - enemy.pos).normalize()
                        overlap = min_dist - enemy_dist
                        # Apply push to both entities
                        push = push_dir * overlap * 0.5
                        survivor.pos += push
                        enemy.pos -= push
                        survivor.rect.center = survivor.pos
                        enemy.rect.center = enemy.pos
    
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
    
    ###################
    # Update coin drops
    ###################
    coin_drops_to_remove = []
    for coin_drop in coin_drops:
        coin_drop.update(dt, resources)
        if coin_drop.collected:
            coin_drops_to_remove.append(coin_drop)
    
    # Remove collected coin drops
    for coin_drop in coin_drops_to_remove:
        coin_drops.remove(coin_drop)
    
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
    # Draw nodes (hide when building panel is visible)
    ###################
    if not building_panel.is_visible:
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
    # Draw coin drops
    ###################
    for coin_drop in coin_drops:
        coin_drop.draw(screen)
    
    ###################
    # Draw enemies
    ###################
    # Debug: Print enemy count periodically
    if len(enemy_group) > 0:
        if '_last_enemy_count_log' not in globals() or globals()['_last_enemy_count_log'] != len(enemy_group):
            globals()['_last_enemy_count_log'] = len(enemy_group)
            alive_count = sum(1 for e in enemy_group if hasattr(e, 'alive') and e.alive)
            print(f"DEBUG: Drawing {alive_count}/{len(enemy_group)} enemies")
    
    for enemy in enemy_group:
        # Debug: Check if enemy is valid before drawing
        if not hasattr(enemy, 'alive'):
            continue
        
        # Allow drawing dead enemies if they have a death animation that's still playing
        if not enemy.alive:
            # Check if enemy has death animation support
            if isinstance(enemy, (BasicZombie, RunnerZombie, BruteZombie, Skeleton, ArcherSkeleton, WarriorSkeleton)):
                # Only skip if death animation is complete
                if hasattr(enemy, 'death_animation_complete') and enemy.death_animation_complete:
                    continue  # Skip enemies with completed death animation
                # Otherwise, draw them (death animation still playing)
            else:
                # For enemies without death animations, skip immediately
                continue
        
        if not hasattr(enemy, 'pos'):
            print(f"WARNING: Enemy missing pos attribute: {type(enemy).__name__}")
            continue
        if not hasattr(enemy, 'rect'):
            print(f"WARNING: Enemy missing rect attribute: {type(enemy).__name__}")
            continue
        enemy.draw(screen)
    
    # Draw placement glow effects (after all world objects)
    for grid_pos, glow_time in placement_glow_tiles:
        elapsed = current_time - glow_time
        if elapsed < 0.1:  # 100ms glow
            alpha = int(255 * (1.0 - elapsed / 0.1))
            # Get footprint from stored building type or default
            w, h = (1, 1)  # Default footprint
            # Try to find building at this position to get footprint
            for building in building_group:
                if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                    building.grid_x == grid_pos[0] and building.grid_y == grid_pos[1]):
                    w, h = getattr(building, 'FOOTPRINT', (1, 1))
                    break
            gx, gy = grid_pos
            px = gx * TILE
            py = gy * TILE
            glow_surface = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
            glow_surface.fill((255, 255, 255, alpha))  # White glow
            screen.blit(glow_surface, (px, py))
    
    # Draw selection highlight (white outline pulse)
    if selection_highlight_building and selection_highlight_timer:
        progress = selection_highlight_timer.get_progress()
        if progress < 1.0:
            # Fade from full alpha to 0 over 150ms
            alpha = int(255 * (1.0 - progress))
            building = selection_highlight_building
            # Draw white outline
            if hasattr(building, 'rect'):
                outline_rect = building.rect.inflate(4, 4)
                # Create outline surface with alpha
                outline_surf = pygame.Surface((outline_rect.width, outline_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(outline_surf, (255, 255, 255, alpha), (0, 0, outline_rect.width, outline_rect.height), 3)
                screen.blit(outline_surf, outline_rect)
    
    ###################
    # Apply night blue tint overlay
    ###################
    if is_night:
        night_overlay = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        night_overlay.fill((30, 40, 80, 80))  # Darkish blue tint with transparency
        screen.blit(night_overlay, (0, 0))
    
    # Note: HUD and UI panels are drawn later, after all game world elements, to ensure they're on top
    
    ###################
    # Draw research button (only when panel is not visible)
    ###################
    if not research_panel_ui.visible:
        # DEBUG: Draw overlay rectangle for research button (top-left, 10px padding)
        if debug_system.is_active() and debug_system.show_ui_rectangles and hasattr(research_button, 'rect'):
            research_overlay = pygame.Surface((research_button.rect.width, research_button.rect.height), pygame.SRCALPHA)
            research_overlay.fill((128, 0, 255, 80))  # Purple overlay
            screen.blit(research_overlay, research_button.rect)
        research_button.draw(screen)
    
    ###################
    # Draw pause menu
    ###################
    if game_state_manager.is_paused():
        pause_menu.draw(screen, show_ui_rects)
    
    ###################
    # Draw game over screen
    ###################
    if game_over_screen.is_visible:
        game_over_screen.draw(screen, show_ui_rects)
    
    ###################
    # Draw start screen (should not be visible during gameplay, but just in case)
    ###################
    if start_screen.is_visible:
        start_screen.draw(screen)
    if difficulty_screen.is_visible:
        difficulty_screen.draw(screen)
    if mode_screen.is_visible:
        mode_screen.draw(screen)
    
    ###################
    # Draw preview when in build mode - use cached ghost position for responsiveness
    ###################
    if build_mode and selected_building_type:
        # Use cached grid position (updated on MOUSEMOTION for instant response)
        if build_ghost_grid_pos is None:
            build_ghost_grid_pos = pixel_to_grid(mouse_pos)
        grid_pos = build_ghost_grid_pos
        can_place = build_ghost_can_place
        
        gx, gy = grid_pos
        w, h = selected_building_type.FOOTPRINT
        px = gx * TILE
        py = gy * TILE
        
        # Draw tile highlights
        for dx in range(w):
            for dy in range(h):
                tile_px = (gx + dx) * TILE
                tile_py = (gy + dy) * TILE
                highlight = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                if can_place:
                    highlight.fill((100, 200, 255, 40))  # Soft light-blue tint
                else:
                    highlight.fill((255, 100, 100, 40))  # Soft red tint
                screen.blit(highlight, (tile_px, tile_py))
        
        # Draw preview ghost
        if can_place:
            color = (0, 255, 0, 100)
            outline_color = (0, 255, 0)
        else:
            color = (255, 0, 0, 100)
            outline_color = (255, 0, 0)
        
        preview_surface = pygame.Surface((w * TILE, h * TILE), pygame.SRCALPHA)
        preview_surface.fill(color)
        screen.blit(preview_surface, (px, py))
        pygame.draw.rect(screen, outline_color, (px, py, w * TILE, h * TILE), 2)
    
    ###################
    # Draw gather mode indicator
    ###################
    if gather_mode:
        # Draw text indicator
        gather_text = font.render("GATHER MODE - Click on nodes to assign workers (G to cancel)", True, (255, 255, 0))
        text_rect = gather_text.get_rect(center=(c.SCREEN_WIDTH // 2, 100))
        screen.blit(gather_text, text_rect)
    
    ###################
    # Draw resources (only when research panel is not visible)
    ###################
    if not research_panel_ui.visible:
        draw_resources(screen, resources, font)
        
        # Draw hire survivor button (below resource display)
        # Update button state based on affordability and max survivors
        if hire_survivor_button and world:
            can_afford = resources.coins >= HIRE_SURVIVOR_COST
            can_hire = world.can_hire_survivor()
            # Check if hiring is unlocked through research
            hiring_unlocked = research_manager.is_unlocked("hire_survivor")
            hire_survivor_button.enabled = can_afford and can_hire and hiring_unlocked
            # Only show button if hiring is unlocked
            if hiring_unlocked:
                # Show tooltip if disabled
                if not can_hire:
                    hire_survivor_button.text = f"Hire ({world.get_current_survivor_count()}/{world.get_max_survivors()})"
                elif not can_afford:
                    hire_survivor_button.text = f"Hire ({HIRE_SURVIVOR_COST} coins)"
                else:
                    hire_survivor_button.text = f"Hire Survivor ({HIRE_SURVIVOR_COST} coins)"
                hire_survivor_button.draw(screen)
    
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
    # Draw HUD (after all game world elements to ensure it's on top)
    ###################
    # Find HQ for HP display
    hq = None
    hq_hp = 0
    hq_max_hp = 2000
    # OPTIMIZED: Use cached HQ reference instead of searching building_group
    hq = world.hq if world and hasattr(world, 'hq') and world.hq else None
    if hq:
        hq_hp = hq.hp
        hq_max_hp = hq.max_hp
    else:
        hq_hp = 0
        hq_max_hp = 1
    
    hud.update(dt, wave_manager.day, wave_manager.night, wave_manager.state, {
        "enemies_spawned": zombie_spawner.spawn_count,
        "total_to_spawn": zombie_spawner.total_to_spawn,
        "enemies_killed": wave_manager.enemies_killed
    }, hq_hp, hq_max_hp)
    
    # Show "Starting Defenses" hint on Day 1 (once)
    if wave_manager.day == 1 and wave_manager.state == "DAY" and not hasattr(hud, '_starting_hint_shown'):
        hud.show_starting_defenses_hint()
        hud._starting_hint_shown = True
    
    # Get UI rectangle toggle state for passing to UI components
    show_ui_rects = debug_system.is_active() and debug_system.show_ui_rectangles
    
    hud.draw(screen, show_ui_rects)
    
    ###################
    # Draw building panel (after HUD, on top of everything)
    ###################
    if building_panel.is_visible:
        building_panel.draw(screen, resources, mouse_pos, show_ui_rects, dt)
    
    # Draw research panel (overlay UI, on top of everything)
    if research_panel_ui.visible:
        research_panel_ui.draw(screen, show_ui_rects)
    
    ###################
    # Draw debug system (after HUD and UI panels)
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
        
        if game_state_manager.get_state() == GameState.SELECT_MODE:
            if mode_screen.handle_event(event):
                continue
        
        # Handle MOUSEMOTION for responsive build ghost (NOT tied to frame rate)
        if event.type == pygame.MOUSEMOTION:
            if build_mode and selected_building_type:
                # Update build ghost instantly on mouse movement
                mouse_pos = event.pos
                build_ghost_grid_pos = pixel_to_grid(mouse_pos)
                build_ghost_can_place = can_place_building(selected_building_type, build_ghost_grid_pos, grid)
                
                # Check if we have enough resources
                preview_difficulty = getattr(game_state_manager, "difficulty", world.current_difficulty)
                effective_cost = selected_building_type.get_scaled_cost(world=world, difficulty=preview_difficulty)
                
                if (
                    resources.wood < effective_cost.wood
                    or resources.iron < effective_cost.iron
                    or resources.food < effective_cost.food
                    or resources.coins < effective_cost.coins
                ):
                    build_ghost_can_place = False

            # Debug: drag research nodes when research panel is open and movable nodes mode is ON
            if debug_movable_nodes and research_panel_ui.visible:
                mouse_pos = event.pos
                left_down = pygame.mouse.get_pressed()[0]
                research_panel_ui.debug_handle_drag(mouse_pos, left_down)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # Add to input buffer for responsive handling
            input_buffer.add_input('left_click', {'pos': mouse_pos, 'event': event})
            
            # Skip input if game over or paused
            if game_over_screen.is_visible:
                if game_over_screen.handle_event(event):
                    continue
                continue
            
            if game_state_manager.is_paused():
                if pause_menu.handle_event(event):
                    continue
                continue
            
            # Debug mode helpers
            if debug_system.is_active():
                keys = pygame.key.get_pressed()
                # F3 + Click to spawn zombie at mouse
                if keys[pygame.K_F3]:
                    debug_spawn_zombie_at_mouse(mouse_pos)
                    continue
                # When research panel is open and movable nodes mode is ON, use mouse to drag nodes instead of unlocking
                if debug_movable_nodes and research_panel_ui.visible:
                    research_panel_ui.debug_handle_drag(mouse_pos, True)
                    continue
            
            # Handle research button click (with animation feedback)
            if research_button.handle_click(mouse_pos):
                sound_system.play("button_click")
                continue
            
            # Handle hire survivor button click
            if hire_survivor_button and hire_survivor_button.handle_click(mouse_pos):
                continue  # Sound already played in callback
            
            # Research panel click handling
            if research_panel_ui.visible:
                if research_panel_ui.handle_click(mouse_pos):
                    # If panel was closed or research clicked, refresh building buttons after changes
                    if not research_panel_ui.visible:
                        rebuild_building_buttons()
                    continue
            
            # Handle building panel clicks (upgrade/repair/sell)
            if building_panel.is_visible:
                button_clicked = building_panel.handle_event(event, mouse_pos)
                if button_clicked == "close":
                    # Clicked outside panel - deselect building and hide panel
                    deselect_building()
                elif button_clicked in ("upgrade", "upgrade_to_iron"):
                    print(f"DEBUG: building panel click -> {button_clicked}")
                    # CONSTRUCTION RULES: Can only build/upgrade during Day Phase
                    if wave_manager.state != WaveManager.STATE_DAY:
                        hud.show_event("Can only upgrade during Day Phase!", 2.0)
                        sound_system.play("button_click")
                    else:
                        building = building_panel.selected_building
                        if building:
                            print(f"DEBUG: upgrading building TYPE_ID={getattr(building,'TYPE_ID',None)} tier={getattr(building,'tier',None)} state={getattr(building,'state',None)}")
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
                elif button_clicked == "demolish":
                    building = building_panel.selected_building
                    if building:
                        demolish_building(building)
                        # Building is demolished, so deselect it
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
                # CONSTRUCTION RULES: Can only build/upgrade during Day Phase
                if wave_manager.state != WaveManager.STATE_DAY:
                    hud.show_event("Can only build during Day Phase!", 2.0)
                    sound_system.play("button_click")
                    continue
                
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
                            
                            # Add placement glow feedback (100ms white flash)
                            import time as time_module
                            placement_glow_tiles.append((grid_pos, time_module.time()))
                            
                            # Add white outline flash (1 frame)
                            # This is handled by placement_glow_tiles above
                            
                            sound_system.play("build_placed")
            else:
                # Try to select a building
                building_clicked = select_building(mouse_pos, building_group)
                if building_clicked:
                    # Building selected - show building panel
                    if selected_building:
                        building_panel.show(selected_building)
                        sound_system.play("button_click")
                        # Selection highlight is handled in select_building()
                else:
                    # No building clicked - deselect building and hide panel
                    deselect_building()
        
        # Handle right-click to dismiss panel and deselect building
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right mouse button
            # Add to input buffer for responsive handling
            input_buffer.add_input('right_click', {'pos': pygame.mouse.get_pos(), 'event': event})
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
                # Add to input buffer for responsive handling
                input_buffer.add_input('key_r', {})
                launch_research_tree()
                sound_system.play("button_click")
                continue
            # F12: Toggle debug mode only
            if event.key == pygame.K_F12:
                debug_system.toggle()
                print(f"Debug mode: {'ON' if debug_system.is_active() else 'OFF'}")
                continue
            
            # M: Toggle movable nodes mode (for research panel node positioning)
            if event.key == pygame.K_m:
                debug_movable_nodes = not debug_movable_nodes
                status = "ON" if debug_movable_nodes else "OFF"
                print(f"Debug: Movable nodes mode {status} (M key)")
                if debug_movable_nodes:
                    hud.show_event("Movable Nodes Mode: ON (Press M to toggle)", 2.0)
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
                # Add to input buffer for responsive handling
                input_buffer.add_input('key_g', {})
                gather_mode = not gather_mode
                build_mode = False  # Disable build mode when entering gather mode
                selected_building_type = None
                sound_system.play("button_click")
                if gather_mode:
                    print("Gather mode enabled - Click on nodes to assign workers")
                else:
                    print("Gather mode disabled")
                continue
            
            # Upgrade selected building (U key) - only when not paused/over
            if event.key == pygame.K_u and not game_over_screen.is_visible and not game_state_manager.is_paused():
                # CONSTRUCTION RULES: Can only build/upgrade during Day Phase
                if wave_manager.state != WaveManager.STATE_DAY:
                    hud.show_event("Can only upgrade during Day Phase!", 2.0)
                    sound_system.play("button_click")
                    continue
                
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
                elif event.key == pygame.K_F8:
                    # F8: Skip state (or Shift+F8: Complete All Buildings)
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                        # Shift+F8: Complete All Buildings
                        debug_complete_all_buildings()
                    else:
                        # F8: Skip state
                        debug_skip_state()
                    continue
                elif debug_system.handle_key(event.key):
                    # Debug action handled by debug system (F1, F2, F4-F7)
                    continue
                elif event.key == pygame.K_F9:
                    # F9: Skip to night - increment night counter when transitioning from DAY to NIGHT
                    if wave_manager.state == WaveManager.STATE_DAY:
                        print(f"[NIGHT COUNTER] F9 skip: Before increment: night={wave_manager.night}")
                        wave_manager.night += 1
                        print(f"[NIGHT COUNTER] F9 skip: After increment: night={wave_manager.night}")
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
