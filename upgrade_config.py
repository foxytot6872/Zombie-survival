from __future__ import annotations

from typing import Dict, Optional, Union

from difficulty_config import Difficulty

UPGRADE_STEPS_PER_TIER = 2  # Changed from 3 to 2: 1->2->MAX(3) means 2 steps per tier

TURRET_UPGRADE_CONFIG: Dict[str, list] = {
    "tier_1": [
        {"step": 1, "base_cost": {"wood": 30, "iron": 10}},
        {"step": 2, "base_cost": {"wood": 50, "iron": 20}},  # Step 2 upgrades to tier 2
    ],
    "tier_2": [
        {"step": 1, "base_cost": {"wood": 60, "iron": 25}},
        {"step": 2, "base_cost": {"wood": 80, "iron": 35}},  # Step 2 upgrades to tier 3 (MAX)
    ],
    # Tier 3 is MAX - no upgrades available
}

DIFFICULTY_UPGRADE_MULTIPLIER: Dict[Difficulty, float] = {
    Difficulty.EASY: 0.5,    # Easy: 0.5× upgrade cost (as per requirements)
    Difficulty.MEDIUM: 1.0,   # Normal: 1.0× upgrade cost
    Difficulty.HARD: 2.0,     # Hard: 2.0× upgrade cost (as per requirements)
    Difficulty.EXTREME: 2.5,  # Extreme: 2.5× upgrade cost (more punishing than hard)
}


def _normalize_difficulty(value: Union[str, Difficulty, None]) -> Difficulty:
    if isinstance(value, Difficulty):
        return value
    if isinstance(value, str):
        value_lower = value.lower()
        for diff in Difficulty:
            if diff.name.lower() == value_lower:
                return diff
    return Difficulty.MEDIUM


def scale_upgrade_cost(base_cost: Dict[str, int], difficulty: Union[str, Difficulty, None]) -> Dict[str, int]:
    diff_enum = _normalize_difficulty(difficulty)
    mult = DIFFICULTY_UPGRADE_MULTIPLIER.get(diff_enum, 1.0)
    scaled = {}
    for resource, amount in base_cost.items():
        try:
            scaled[resource] = max(0, int(round(amount * mult)))
        except (TypeError, ValueError):
            scaled[resource] = 0
    return scaled


def get_next_turret_upgrade(building) -> Optional[Dict]:
    """Return information about the upcoming turret upgrade."""
    if building is None:
        return None

    tier = getattr(building, "tier", 1)
    tier_max = getattr(building, "TIER_MAX", 3)
    progress = getattr(building, "upgrade_progress", 0)
    config_key = f"tier_{tier}"
    config = TURRET_UPGRADE_CONFIG.get(config_key)

    if config is None:
        return None

    # Max tier handling
    if tier >= tier_max and progress >= len(config):
        return {"is_max": True}

    if tier >= tier_max and progress >= UPGRADE_STEPS_PER_TIER:
        return {"is_max": True}

    if progress >= len(config):
        # Move to next tier config if available
        next_tier = tier + 1
        next_key = f"tier_{next_tier}"
        next_config = TURRET_UPGRADE_CONFIG.get(next_key)
        if not next_config or next_tier > tier_max:
            return {"is_max": True}
        entry = next_config[0]
        return {
            "is_max": False,
            "base_cost": entry["base_cost"],
            "target_tier": next_tier,
            "target_step": 1,
            "step_total": UPGRADE_STEPS_PER_TIER,
        }

    entry = config[progress]
    if tier >= tier_max:
        target_tier = tier
        target_step = progress + 1
    else:
        if progress >= UPGRADE_STEPS_PER_TIER - 1:
            target_tier = tier + 1
            target_step = 1
        else:
            target_tier = tier
            target_step = progress + 1

    return {
        "is_max": False,
        "base_cost": entry["base_cost"],
        "target_tier": target_tier,
        "target_step": target_step,
        "step_total": UPGRADE_STEPS_PER_TIER,
    }

