from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional
import json
import os


class Difficulty(Enum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()
    EXTREME = auto()


@dataclass(frozen=True)
class DifficultySettings:
    name: str
    description: str
    starting_resources: Dict[str, int]
    sawmill_yield_multiplier: float
    smelter_yield_multiplier: float
    build_cost_multiplier: float
    research_cost_multiplier: float
    research_total_target: Optional[float] = None


def _load_difficulty_config_from_balance() -> Dict[Difficulty, DifficultySettings]:
    """Load difficulty config from central balance.json if available."""
    config_path = os.path.join('data', 'config', 'balance.json')
    try:
        with open(config_path, 'r') as f:
            balance_config = json.load(f)
        
        multipliers = balance_config.get("difficulty_multipliers", {})
        
        # Map multiplier keys to our settings
        configs = {}
        for diff in Difficulty:
            diff_key = diff.name.lower()
            mults = multipliers.get(diff_key, {})
            
            # Get starting resources
            starting_resources = mults.get("starting_resources", {"wood": 300, "iron": 300, "food": 300})
            
            # Get production multipliers (sawmill/smelter both use production_rate)
            prod_mult = mults.get("production_rate", 1.0)
            
            # Get other multipliers
            build_cost_mult = mults.get("building_cost", 1.0)
            research_cost_mult = mults.get("research_cost", 1.0)
            
            # Research target (only for easy in old system)
            research_target = 600.0 if diff == Difficulty.EASY else None
            
            # Descriptions
            descriptions = {
                "easy": "Generous resources and cheap research. Great for learning.",
                "medium": "Balanced challenge with modest scarcity.",
                "hard": "Tight economy and expensive research.",
                "extreme": "Brutal scarcity. Only for veterans.",
            }
            
            configs[diff] = DifficultySettings(
                name=diff.name.capitalize(),
                description=descriptions.get(diff_key, f"{diff.name} difficulty"),
                starting_resources=starting_resources,
                sawmill_yield_multiplier=prod_mult,
                smelter_yield_multiplier=prod_mult,
                build_cost_multiplier=build_cost_mult,
                research_cost_multiplier=research_cost_mult,
                research_total_target=research_target,
            )
        
        return configs
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        # Fallback to hardcoded values if balance.json doesn't exist or is invalid
        return None


# Try to load from balance.json, fallback to hardcoded values
_loaded_config = _load_difficulty_config_from_balance()

if _loaded_config:
    DIFFICULTY_CONFIG = _loaded_config
else:
    # Fallback: Original hardcoded values
    DIFFICULTY_CONFIG: Dict[Difficulty, DifficultySettings] = {
        Difficulty.EASY: DifficultySettings(
            name="Easy",
            description="Generous resources and cheap research. Great for learning.",
            starting_resources={"wood": 350, "iron": 350, "food": 350},
            sawmill_yield_multiplier=1.0,
            smelter_yield_multiplier=1.0,
            build_cost_multiplier=0.75,
            research_cost_multiplier=1.0,
            research_total_target=600.0,
        ),
        Difficulty.MEDIUM: DifficultySettings(
            name="Medium",
            description="Balanced challenge with modest scarcity.",
            starting_resources={"wood": 300, "iron": 300, "food": 300},
            sawmill_yield_multiplier=0.75,
            smelter_yield_multiplier=0.75,
            build_cost_multiplier=1.0,
            research_cost_multiplier=1.10,
            research_total_target=None,
        ),
        Difficulty.HARD: DifficultySettings(
            name="Hard",
            description="Tight economy and expensive research.",
            starting_resources={"wood": 150, "iron": 150, "food": 150},
            sawmill_yield_multiplier=0.6,
            smelter_yield_multiplier=0.6,
            build_cost_multiplier=1.4,
            research_cost_multiplier=1.5,
            research_total_target=None,
        ),
        Difficulty.EXTREME: DifficultySettings(
            name="Extreme",
            description="Brutal scarcity. Only for veterans.",
            starting_resources={"wood": 100, "iron": 100, "food": 100},
            sawmill_yield_multiplier=0.4,
            smelter_yield_multiplier=0.4,
            build_cost_multiplier=2,
            research_cost_multiplier=3,
            research_total_target=None,
        ),
    }


