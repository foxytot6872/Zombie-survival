"""Smelter building."""
from world.building import Building, Cost, Production

class Smelter(Building):
    """Smelter - produces iron."""
    TYPE_ID = "smelter"
    BASE_HP = 140
    BUILD_TIME = 4.5
    COST = Cost(wood=40, iron=40)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSIVE = Production(iron_per_min=120.0)  # 10 iron per 5 seconds = 120 per minute

