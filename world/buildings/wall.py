"""Wall building - backwards compatibility wrapper for WallWood."""
# For backwards compatibility, Wall is an alias for WallWood
from world.buildings.wall_wood import WallWood

# Make Wall an alias for WallWood so existing code still works
Wall = WallWood

