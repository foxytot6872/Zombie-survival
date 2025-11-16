"""
A* pathfinding for enemies.
"""
import heapq
from typing import List, Tuple, Optional, Set
from world.map import Grid

class Pathfinding:
    """A* pathfinding implementation"""
    
    def __init__(self, grid: Grid, building_group=None):
        """
        Initialize pathfinding.
        Args:
            grid: Grid object for pathfinding
            building_group: Building group to check for passable buildings (gates)
        """
        self.grid = grid
        self.building_group = building_group
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int], ignore_walls: bool = False, allow_gates: bool = True) -> Optional[List[Tuple[int, int]]]:
        """
        Find path from start to goal using A*.
        Args:
            start: Start position (grid_x, grid_y)
            goal: Goal position (grid_x, grid_y)
            ignore_walls: If True, ignore wall collisions (for SwarmlingZombie)
            allow_gates: If True, gates are passable (for survivors). If False, gates are solid (for enemies).
        Returns:
            List of positions from start to goal, or None if no path found
        """
        # Convert pixel positions to grid if needed
        if not isinstance(start[0], int):
            start = (int(start[0]), int(start[1]))
        if not isinstance(goal[0], int):
            goal = (int(goal[0]), int(goal[1]))
        
        # Check if start or goal is blocked (gates are passable only if allow_gates=True, walls ignored if ignore_walls=True)
        if not ignore_walls:
            if self.grid.is_blocked(start[0], start[1], check_passable=allow_gates, building_group=self.building_group):
                return None
            if self.grid.is_blocked(goal[0], goal[1], check_passable=allow_gates, building_group=self.building_group):
                # Try to find nearby unblocked tile
                goal = self._find_nearby_unblocked(goal, ignore_walls=ignore_walls, allow_gates=allow_gates)
                if goal is None:
                    return None
        
        # A* algorithm
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}
        closed_set: Set[Tuple[int, int]] = set()
        
        # Directions: up, down, left, right, diagonals
        directions = [
            (0, -1), (0, 1), (-1, 0), (1, 0),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            
            closed_set.add(current)
            
            # Check neighbors
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Check bounds
                if (neighbor[0] < 0 or neighbor[0] >= self.grid.width or
                    neighbor[1] < 0 or neighbor[1] >= self.grid.height):
                    continue
                
                # Check if blocked (gates are passable only if allow_gates=True, walls ignored if ignore_walls=True)
                if not ignore_walls:
                    if self.grid.is_blocked(neighbor[0], neighbor[1], check_passable=allow_gates, building_group=self.building_group):
                        continue
                else:
                    # If ignoring walls, only block on non-wall buildings (e.g., HQ, turrets, gates if allow_gates=False)
                    # Check if there's a non-wall building at this position
                    if self.building_group:
                        blocked_by_non_wall = False
                        for building in self.building_group:
                            if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                                building.grid_x == neighbor[0] and building.grid_y == neighbor[1]):
                                # Check if it's a wall (swarmlings can pass through walls)
                                type_id = getattr(building, 'TYPE_ID', '').lower()
                                is_gate = type_id == 'gate'
                                is_wall = type_id.startswith('wall')
                                
                                # Walls are ignored (swarmlings can pass through)
                                if is_wall:
                                    continue
                                
                                # Gates block if allow_gates=False (for enemies)
                                if is_gate and not allow_gates:
                                    blocked_by_non_wall = True
                                    break
                                
                                # Gates pass through if allow_gates=True (for survivors)
                                if is_gate and allow_gates:
                                    continue
                                
                                # Other non-wall, non-gate buildings block
                                if not getattr(building, 'PASSABLE', False):
                                    blocked_by_non_wall = True
                                    break
                        if blocked_by_non_wall:
                            continue
                
                # Check if in closed set
                if neighbor in closed_set:
                    continue
                
                # Calculate tentative g_score
                # Diagonal movement costs more
                move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
                tentative_g_score = g_score.get(current, float('inf')) + move_cost
                
                # Check if this path is better
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    
                    # Add to open set if not already there
                    if neighbor not in [item[1] for item in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found
        return None
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate heuristic distance between two points (Manhattan distance)"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _find_nearby_unblocked(self, pos: Tuple[int, int], radius: int = 3, ignore_walls: bool = False, allow_gates: bool = True) -> Optional[Tuple[int, int]]:
        """Find nearby unblocked tile"""
        for r in range(1, radius + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx == 0 and dy == 0:
                        continue
                    check_pos = (pos[0] + dx, pos[1] + dy)
                    if (0 <= check_pos[0] < self.grid.width and
                        0 <= check_pos[1] < self.grid.height):
                        # Check if blocked (gates are passable only if allow_gates=True, walls ignored if ignore_walls=True)
                        if not ignore_walls:
                            if not self.grid.is_blocked(check_pos[0], check_pos[1], check_passable=allow_gates, building_group=self.building_group):
                                return check_pos
                        else:
                            # If ignoring walls, only block on non-wall buildings (gates block if allow_gates=False)
                            if self.building_group:
                                blocked = False
                                for building in self.building_group:
                                    if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                                        building.grid_x == check_pos[0] and building.grid_y == check_pos[1]):
                                        type_id = getattr(building, 'TYPE_ID', '').lower()
                                        is_gate = type_id == 'gate'
                                        is_wall = type_id.startswith('wall')
                                        
                                        # Walls are ignored (swarmlings can pass through)
                                        if is_wall:
                                            continue
                                        
                                        # Gates block if allow_gates=False (for enemies)
                                        if is_gate and not allow_gates:
                                            blocked = True
                                            break
                                        
                                        # Gates pass through if allow_gates=True (for survivors)
                                        if is_gate and allow_gates:
                                            continue
                                        
                                        # Other non-wall, non-gate buildings block
                                        if not getattr(building, 'PASSABLE', False):
                                            blocked = True
                                            break
                                if not blocked:
                                    return check_pos
                            else:
                                return check_pos
        return None
    
    def get_next_direction(self, start: Tuple[float, float], goal: Tuple[float, float]) -> Tuple[float, float]:
        """
        Get next direction toward goal (simplified pathfinding for enemies).
        Args:
            start: Start position (pixel x, y)
            goal: Goal position (pixel x, y)
        Returns:
            Normalized direction vector (dx, dy)
        """
        import pygame
        direction = pygame.Vector2(goal) - pygame.Vector2(start)
        if direction.length() > 0:
            return direction.normalize()
        return pygame.Vector2(0, 1)  # Default to down

