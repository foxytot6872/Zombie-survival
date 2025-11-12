"""Sawmill building."""
from world.building import Building, Cost, Production

class Sawmill(Building):
    """Sawmill - produces wood."""
    TYPE_ID = "sawmill"
    BASE_HP = 130
    BUILD_TIME = 3.5
    COST = Cost(wood=50, iron=10)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSIVE = Production(wood_per_min=120.0)  # 10 wood per 5 seconds = 120 per minute

