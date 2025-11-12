"""Housing building."""
from world.building import Building, Cost

class Housing(Building):
    """Housing - provides population capacity."""
    TYPE_ID = "housing"
    BASE_HP = 150
    BUILD_TIME = 3.0
    COST = Cost(wood=50, iron=20)
    FOOTPRINT = (1, 1)
    TIER_MAX = 3

