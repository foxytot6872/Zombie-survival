"""
Configuration file for Zombie Colony Defense
"""
import os

# Screen settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
GRID_SIZE = 32  # 32x32 pixel cells

# Screen layout (vertical split)
OUTSIDE_HEIGHT = int(SCREEN_HEIGHT * 4 / 6)  # Upper 4/6 for outside/combat
INSIDE_HEIGHT = int(SCREEN_HEIGHT * 2 / 6)   # Lower 2/6 for inside/colony
WALL_Y = OUTSIDE_HEIGHT  # Wall line at the split

# Day/Night cycle (in seconds)
DAY_DURATION = 180  # 3 minutes
NIGHT_DURATION = 120  # 2 minutes

# Starting resources
STARTING_WOOD = 200
STARTING_METAL = 100
STARTING_FOOD = 100
STARTING_RESEARCH = 0

# Difficulty multipliers
DIFFICULTY_SETTINGS = {
    "Easy": {"enemy": 0.85, "cost": 0.5},
    "Normal": {"enemy": 1.0, "cost": 1.0},
    "Hard": {"enemy": 1.5, "cost": 2.0}
}

# Resource production rates (per minute)
PRODUCTION_RATES = {
    "Farm": {"Food": 10},
    "Sawmill": {"Wood": 15},
    "Smelter": {"Metal": 12}
}

# Building costs and stats
BUILDING_COSTS = {
    "Wall": {"Wood": 10, "Metal": 5},
    "Gate": {"Wood": 15, "Metal": 10},
    "Turret_Mk1": {"Wood": 20, "Metal": 30},
    "Turret_Mk2": {"Wood": 40, "Metal": 60},
    "Turret_Mk3": {"Wood": 80, "Metal": 120},
    "Housing": {"Wood": 50, "Metal": 20},
    "Farm": {"Wood": 30, "Metal": 10},
    "Sawmill": {"Wood": 40, "Metal": 20},
    "Smelter": {"Wood": 30, "Metal": 50},
    "Hospital": {"Wood": 60, "Metal": 40},
    "Research_Lab": {"Wood": 50, "Metal": 80}
}

# Asset paths
ASSET_DIR = os.path.join("asset")

