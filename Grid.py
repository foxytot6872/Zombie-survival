"""
Grid system for building placement
"""
from config import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, WALL_Y

class Grid:
    def __init__(self):
        self.grid_width = SCREEN_WIDTH // GRID_SIZE
        self.grid_height = SCREEN_HEIGHT // GRID_SIZE
        self.cell_size = GRID_SIZE
        # Track occupied cells (grid_x, grid_y) -> building
        self.occupied = {}
    
    def world_to_grid(self, world_x, world_y):
        """Convert world coordinates to grid coordinates"""
        grid_x = int(world_x // self.cell_size)
        grid_y = int(world_y // self.cell_size)
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x, grid_y):
        """Convert grid coordinates to world coordinates (center of cell)"""
        world_x = grid_x * self.cell_size + self.cell_size // 2
        world_y = grid_y * self.cell_size + self.cell_size // 2
        return world_x, world_y
    
    def snap_to_grid(self, world_x, world_y):
        """Snap world coordinates to nearest grid cell center"""
        grid_x, grid_y = self.world_to_grid(world_x, world_y)
        return self.grid_to_world(grid_x, grid_y)
    
    def is_valid_position(self, grid_x, grid_y, width=1, height=1):
        """Check if a grid position is valid for building"""
        # Check bounds
        if grid_x < 0 or grid_y < 0:
            return False
        if grid_x + width > self.grid_width or grid_y + height > self.grid_height:
            return False
        
        # Check if cells are occupied
        for x in range(grid_x, grid_x + width):
            for y in range(grid_y, grid_y + height):
                if (x, y) in self.occupied:
                    return False
        
        return True
    
    def occupy_cells(self, grid_x, grid_y, building, width=1, height=1):
        """Mark cells as occupied"""
        for x in range(grid_x, grid_x + width):
            for y in range(grid_y, grid_y + height):
                self.occupied[(x, y)] = building
    
    def free_cells(self, grid_x, grid_y, width=1, height=1):
        """Free cells (when building is destroyed)"""
        for x in range(grid_x, grid_x + width):
            for y in range(grid_y, grid_y + height):
                if (x, y) in self.occupied:
                    del self.occupied[(x, y)]
    
    def is_inside_zone(self, grid_y):
        """Check if grid position is in the inside (colony) zone"""
        wall_grid_y = WALL_Y // self.cell_size
        return grid_y >= wall_grid_y
    
    def is_outside_zone(self, grid_y):
        """Check if grid position is in the outside (combat) zone"""
        wall_grid_y = WALL_Y // self.cell_size
        return grid_y < wall_grid_y

