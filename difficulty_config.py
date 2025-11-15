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
    research_total_target: float


DIFFICULTY_CONFIG: Dict[Difficulty, DifficultySettings] = {
    Difficulty.EASY: DifficultySettings(
        name="Easy",
        description="Generous resources and cheap research. Great for learning.",
        starting_resources={"wood": 500, "iron": 500, "food": 500},
        sawmill_yield_multiplier=1.0,
        smelter_yield_multiplier=1.0,
        research_total_target=600.0,
    ),
    Difficulty.MEDIUM: DifficultySettings(
        name="Medium",
        description="Balanced challenge with modest scarcity.",
        starting_resources={"wood": 375, "iron": 375, "food": 375},
        sawmill_yield_multiplier=0.75,
        smelter_yield_multiplier=0.75,
        research_total_target=750.0,
    ),
    Difficulty.HARD: DifficultySettings(
        name="Hard",
        description="Tight economy and expensive research.",
        starting_resources={"wood": 250, "iron": 250, "food": 250},
        sawmill_yield_multiplier=0.5,
        smelter_yield_multiplier=0.5,
        research_total_target=900.0,
    ),
    Difficulty.EXTREME: DifficultySettings(
        name="Extreme",
        description="Brutal scarcity. Only for veterans.",
        starting_resources={"wood": 100, "iron": 100, "food": 100},
        sawmill_yield_multiplier=0.2,
        smelter_yield_multiplier=0.2,
        research_total_target=1000.0,
    ),
}


