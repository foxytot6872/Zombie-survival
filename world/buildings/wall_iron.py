"""Iron wall - upgraded from wood wall."""
from world.buildings.wall_base import WallBase
from world.building import Cost

class WallIron(WallBase):
    """Iron wall - upgraded from wood wall, stronger."""
    TYPE_ID = "wall_iron"
    BASE_HP = 600
    BUILD_TIME = 0.8  # Quick upgrade feel
    COST = Cost(wood=10, iron=40)  # Upgrade cost
    TIER_MAX = 1  # No further upgrades
    
    def __init__(self, grid_pos, wall_tiles=None, building_group=None, tier=1, uid=None):
        super().__init__(grid_pos, wall_tiles=wall_tiles, building_group=building_group, tier=tier, uid=uid)
        self._is_iron = True

