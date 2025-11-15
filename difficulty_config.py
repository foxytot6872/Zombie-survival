from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


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
    research_total_target: float | None = None


DIFFICULTY_CONFIG: Dict[Difficulty, DifficultySettings] = {
    Difficulty.EASY: DifficultySettings(
        name="Easy",
        description="Generous resources and cheap research. Great for learning.",
        starting_resources={"wood": 500, "iron": 500, "food": 500},
        sawmill_yield_multiplier=1.0,
        smelter_yield_multiplier=1.0,
        build_cost_multiplier=0.75,
        research_cost_multiplier=1.0,
        research_total_target=600.0,
    ),
    Difficulty.MEDIUM: DifficultySettings(
        name="Medium",
        description="Balanced challenge with modest scarcity.",
        starting_resources={"wood": 375, "iron": 375, "food": 375},
        sawmill_yield_multiplier=0.75,
        smelter_yield_multiplier=0.75,
        build_cost_multiplier=1.0,
        research_cost_multiplier=1.10,
        research_total_target=None,
    ),
    Difficulty.HARD: DifficultySettings(
        name="Hard",
        description="Tight economy and expensive research.",
        starting_resources={"wood": 300, "iron": 300, "food": 300},
        sawmill_yield_multiplier=0.6,
        smelter_yield_multiplier=0.6,
        build_cost_multiplier=1.2,
        research_cost_multiplier=1.30,
        research_total_target=None,
    ),
    Difficulty.EXTREME: DifficultySettings(
        name="Extreme",
        description="Brutal scarcity. Only for veterans.",
        starting_resources={"wood": 200, "iron": 200, "food": 200},
        sawmill_yield_multiplier=0.4,
        smelter_yield_multiplier=0.4,
        build_cost_multiplier=1.5,
        research_cost_multiplier=1.60,
        research_total_target=None,
    ),
}


