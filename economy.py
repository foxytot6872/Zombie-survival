from __future__ import annotations

from typing import Dict, Union

from difficulty_config import Difficulty, DIFFICULTY_CONFIG

Number = Union[int, float]
CostDict = Dict[str, Number]


def scale_cost(base_cost: Union[CostDict, "Cost"], difficulty: Difficulty, *, cost_type: str = "build") -> CostDict:
    """
    Scale a cost dictionary based on the selected difficulty.
    cost_type: "build" (default) or "research" to pick the correct multiplier.
    Returns a dictionary with the same keys as the input.
    """
    if difficulty not in DIFFICULTY_CONFIG:
        difficulty = Difficulty.EASY
    settings = DIFFICULTY_CONFIG[difficulty]
    multiplier = settings.build_cost_multiplier if cost_type == "build" else settings.research_cost_multiplier

    if hasattr(base_cost, "__dict__"):
        raw_cost = {k: getattr(base_cost, k) for k in ("wood", "iron", "food", "coins") if hasattr(base_cost, k)}
    else:
        raw_cost = {k: base_cost.get(k, 0) for k in ("wood", "iron", "food", "coins")}

    scaled: CostDict = {}
    for key, value in raw_cost.items():
        try:
            scaled_value = max(0, int(round(float(value) * multiplier)))
        except (TypeError, ValueError):
            scaled_value = 0
        scaled[key] = scaled_value

    return scaled


