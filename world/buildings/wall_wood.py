"""Wood wall - default wall type that can be upgraded to iron."""
from world.buildings.wall_base import WallBase
from world.building import Cost

class WallWood(WallBase):
    """Wood wall - default built wall, can be upgraded to iron."""
    TYPE_ID = "wall_wood"
    BASE_HP = 250
    BUILD_TIME = 1.0
    COST = Cost(wood=30)
    TIER_MAX = 1  # Can't tier upgrade, but can upgrade to iron
    
    def __init__(self, grid_pos, tier=1, uid=None):
        super().__init__(grid_pos, tier=tier, uid=uid)
        self._is_iron = False

