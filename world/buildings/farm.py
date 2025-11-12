"""Farm building."""
from world.building import Building, Cost, Production

class Farm(Building):
    """Farm - produces food."""
    TYPE_ID = "farm"
    BASE_HP = 120
    BUILD_TIME = 4.0
    COST = Cost(wood=60, iron=0)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3
    PASSIVE = Production(food_per_min=120.0)  # 10 food per 5 seconds = 120 per minute

