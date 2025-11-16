"""
Base Enemy class with common attributes and behaviors.
"""
from __future__ import annotations
import pygame
import time
from typing import Tuple, Optional, Dict


class EnemyAssets:
    """
    Global enemy sprite assets cache.
    Loads and caches all enemy sprites once at game start.
    """
    # Cached sprite sheets (set from main.py after loading)
    zombie_sprite_sheet = None
    runner_sprite_sheet = None
    brute_sprite_sheet = None
    swarmling_sprite_sheet = None
    spitter_sprite_sheet = None
    skeleton_sprite_sheet = None
    archer_skeleton_sprite_sheet = None
    warrior_skeleton_sprite_sheet = None
    
    # Cached animation frames (loaded once, reused by all instances)
    # Format: {sprite_sheet: [frame1, frame2, ...]}
    _frame_cache: Dict[pygame.Surface, list] = {}
    
    @classmethod
    def load_frames(cls, sprite_sheet, frame_size: int) -> list:
        """
        Load animation frames from a sprite sheet.
        Caches frames to avoid reloading.
        
        Args:
            sprite_sheet: The sprite sheet surface
            frame_size: Size of each frame (width = height)
            
        Returns:
            List of frame surfaces
        """
        if not sprite_sheet:
            return []
        
        # Check cache first
        if sprite_sheet in cls._frame_cache:
            return cls._frame_cache[sprite_sheet]
        
        # Load frames
        frames = []
        sheet_width = sprite_sheet.get_width()
        num_frames = sheet_width // frame_size
        
        for i in range(num_frames):
            frame_rect = pygame.Rect(i * frame_size, 0, frame_size, frame_size)
            frame = sprite_sheet.subsurface(frame_rect)
            frames.append(frame)
        
        # Cache frames
        cls._frame_cache[sprite_sheet] = frames
        return frames


class Enemy(pygame.sprite.Sprite):
    """
    Base class for all enemies.
    Subclasses should override:
      - TYPE_ID (string)
      - BASE_HP, SPEED, DAMAGE
      - draw_body(surface) if custom rendering is needed
    """
    TYPE_ID: str = "enemy"
    BASE_HP: int = 100
    SPEED: float = 50.0  # pixels per second
    DAMAGE: int = 10
    ATTACK_RANGE: float = 32.0  # pixels - range for attacking buildings
    ATTACK_COOLDOWN: float = 1.0  # seconds - time between attacks
    
    # Separation and stuck detection constants
    ZOMBIE_RADIUS: float = 12.0  # Circle hitbox radius in pixels
    SEPARATION_PUSH: float = 80.0  # px/sec applied as displacement
    SEPARATION_MAX_NEIGHBORS: int = 8
    SEPARATION_RANGE: float = 40.0  # Check neighbors within this range
    STUCK_TIME_THRESHOLD: float = 2.0  # seconds before retargeting
    STUCK_PROGRESS_THRESHOLD: float = 8.0  # pixels - minimum movement to count as progress
    SLOT_PENALTY_FREE: float = 200.0  # Score penalty if building has free slot
    SLOT_PENALTY_FULL: float = 10000.0  # Score penalty if building slot is full
    PATHFINDING_PENALTY: float = 5000.0  # Score penalty if no path found
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None):
        super().__init__()
        self.max_hp = hp if hp is not None else self.BASE_HP
        self.hp = self.max_hp
        self.speed = self.SPEED
        self.damage = self.DAMAGE
        self.attack_range = self.ATTACK_RANGE
        self.attack_cooldown = self.ATTACK_COOLDOWN
        
        # Position
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        
        # Rendering
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
        # State
        self.alive = True
        self.reached_bottom = False
        self.coins_dropped = False  # Track if coins were already dropped
        
        # Targeting and combat
        self.target_building = None
        self.target_survivor = None  # Can target survivors too
        self.attack_timer = 0.0  # Time since last attack
        self.is_attacking = False
        
        # Stuck detection
        self.last_progress_check_pos = pygame.Vector2(self.pos)
        self.time_since_progress = 0.0
        self.pathfinding_cache = {}  # Cache pathfinding results (cleared when > 100 entries)
        
        # Pathfinding cooldown - only recalculate path every 0.5 seconds
        self.last_path_update = 0.0
        self.path_update_interval = 0.5  # seconds
        
        # Delay target selection on spawn to avoid expensive pathfinding during spawning
        self.spawn_time = time.time()  # Time when enemy was spawned
        self.target_selection_delay = 0.1  # Wait 100ms before selecting target (defers expensive pathfinding)
        
        # Target priority system - re-evaluate every 1.0 seconds (optimized from 0.25)
        self.last_target_evaluation = 0.0
        self.target_evaluation_interval = 1.0  # seconds (reduced frequency for performance)
        
        # Projectile group for ranged enemies (set by world)
        self.projectile_group = None
    
    def reset(self, spawn_pos: Tuple[float, float], modifiers: Optional[Dict] = None):
        """
        Reset enemy for reuse in pooling system.
        Does NOT create new surfaces or animations (reuses existing).
        
        Args:
            spawn_pos: Spawn position (x, y)
            modifiers: Optional modifiers dictionary (speed_mult, hp_mult, etc.)
        """
        # Reset position
        self.pos = pygame.Vector2(spawn_pos)
        self.velocity = pygame.Vector2(0, 0)
        self.rect.center = self.pos
        
        # Reset HP
        self.max_hp = self.BASE_HP
        self.hp = self.max_hp
        self.speed = self.SPEED
        self.damage = self.DAMAGE
        self.attack_range = self.ATTACK_RANGE
        self.attack_cooldown = self.ATTACK_COOLDOWN
        
        # Reset state
        self.alive = True
        self.reached_bottom = False
        self.coins_dropped = False
        
        # Reset targeting
        # Release building slot if we have one
        if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
            try:
                self.target_building.release_attack_slot()
            except:
                pass  # Building might be destroyed, ignore
        self.target_building = None
        self.target_survivor = None
        
        # Reset combat
        self.attack_timer = 0.0
        self.is_attacking = False
        
        # Reset stuck detection
        self.last_progress_check_pos = pygame.Vector2(self.pos)
        self.time_since_progress = 0.0
        self.pathfinding_cache.clear()
        
        # Reset pathfinding cooldown
        self.last_path_update = 0.0
        
        # Reset spawn time for delayed target selection
        self.spawn_time = time.time()
        
        # Apply modifiers if provided
        if modifiers:
            # Speed modifier
            speed_mult = modifiers.get("zombie_speed_mult", 1.0)
            self.speed *= speed_mult
            
            # HP modifier
            hp_mult = modifiers.get("zombie_hp_mult", 1.0)
            self.max_hp = int(self.max_hp * hp_mult)
            self.hp = self.max_hp
        
        # Start moving immediately (direction depends on spawn position)
        # This ensures enemies are visible and moving right away
        if self.velocity.length() == 0:
            # If spawning below screen (from bottom), move UP. Otherwise move down.
            screen_height = 1080  # Default fallback
            try:
                import constants as c
                screen_height = c.SCREEN_HEIGHT
            except:
                pass
            if self.pos.y > screen_height + 50:  # Spawned below screen
                self.set_direction((0, -1))  # Move UP toward screen
            else:
                self.set_direction((0, 1))  # Move straight down initially
        
        # Call subclass-specific reset (for animation states, etc.)
        self.on_reset()
    
    def on_reset(self):
        """
        Subclass-specific reset logic.
        Override in subclasses to reset animation states, etc.
        """
        pass
    
    def apply_separation(self, dt: float, neighbors):
        """Apply separation force to avoid overlapping with other zombies"""
        if not neighbors:
            return
        
        push = pygame.Vector2(0, 0)
        count = 0
        
        for other in neighbors[:self.SEPARATION_MAX_NEIGHBORS]:
            if other is self or not other.alive:
                continue
            
            delta = self.pos - other.pos
            dist = delta.length()
            min_dist = self.ZOMBIE_RADIUS * 2
            
            if dist > 0 and dist < min_dist:
                # Normalized push away proportional to overlap
                if dist > 0.1:  # Avoid division by zero
                    push += delta.normalize() * (min_dist - dist)
                    count += 1
        
        if count > 0:
            push /= count
            push_length = push.length()
            if push_length > 0.1:
                push = push.normalize() * min(self.SEPARATION_PUSH * dt, push_length)
                self.pos += push
                self.rect.center = self.pos
    
    
    def update(self, dt: float, world=None):
        """Update enemy position and state"""
        if not self.alive:
            return
        
        # Update attack timer
        self.attack_timer += dt
        
        # Force path recalculation if we reached end of waypoint or target changed
        # This is handled in choose_target by checking target_building != building
        
        # Set projectile group for ranged enemies
        if world and hasattr(world, 'projectile_group'):
            self.projectile_group = world.projectile_group
        
        # Check if current survivor target is still valid
        if self.target_survivor is not None:
            if not self.target_survivor.alive:
                self.target_survivor = None
            elif world and hasattr(world, 'survivor_group'):
                if self.target_survivor not in world.survivor_group:
                    self.target_survivor = None
        
        # Find target building or survivor if we don't have one or current target is destroyed
        building_group = None
        if world and hasattr(world, 'building_group'):
            building_group = world.building_group
        
        if building_group:
            # Check if current target is still valid
            if self.target_building is not None:
                # Check if target is destroyed or not in building group
                from world.building import BuildState
                if (hasattr(self.target_building, 'state') and 
                    self.target_building.state == BuildState.DESTROYED):
                    # Release slot before clearing target
                    if hasattr(self.target_building, 'release_attack_slot'):
                        self.target_building.release_attack_slot()
                    self.target_building = None
                elif self.target_building not in building_group:
                    if hasattr(self.target_building, 'release_attack_slot'):
                        self.target_building.release_attack_slot()
                    self.target_building = None
            
            # Choose target if no target or need to retarget
            # Defer target selection slightly after spawn to avoid expensive pathfinding during spawning
            if self.target_building is None and self.target_survivor is None:
                current_time = time.time()
                time_since_spawn = current_time - self.spawn_time
                
                # Only choose target after delay period (avoids freeze during spawning)
                if time_since_spawn >= self.target_selection_delay:
                    self.choose_target(world)
            else:
                # Re-evaluate target priority periodically (every 0.25s)
                current_time = time.time()
                if (current_time - self.last_target_evaluation) >= self.target_evaluation_interval:
                    # Check if we should switch targets (higher priority available)
                    self.choose_target(world)
                    self.last_target_evaluation = current_time
        
        # Move toward target (survivor or building) or straight down
        # Prioritize survivors if we have one as target
        if self.target_survivor and self.target_survivor.alive:
            # Check if we're in attack range
            distance = (self.pos - self.target_survivor.pos).length()
            
            # Check if enemy is ranged
            is_ranged = hasattr(self, 'ranged') and self.ranged
            
            # For ranged enemies, use full attack_range. For melee, add radius.
            if is_ranged:
                attack_distance = self.attack_range
            else:
                attack_distance = self.attack_range + self.ZOMBIE_RADIUS
            
            if distance <= attack_distance:
                # Stop moving and attack
                self.velocity = pygame.Vector2(0, 0)
                self.is_attacking = True
                
                # Attack survivor
                if self.attack_timer >= self.attack_cooldown:
                    self.attack_survivor(self.target_survivor, world)
                    self.attack_timer = 0.0
                
                # Reset stuck detection when attacking
                self.time_since_progress = 0.0
            else:
                # Move toward survivor
                self.is_attacking = False
                direction = (self.target_survivor.pos - self.pos)
                if direction.length() > 0:
                    direction = direction.normalize()
                    self.velocity = direction * self.speed
                
                # Check stuck detection (progress toward target)
                progress_distance = (self.pos - self.last_progress_check_pos).length()
                if progress_distance < self.STUCK_PROGRESS_THRESHOLD:
                    self.time_since_progress += dt
                else:
                    # Made progress - reset timer
                    self.time_since_progress = 0.0
                    self.last_progress_check_pos = pygame.Vector2(self.pos)
                
                # Retarget if stuck for too long
                if self.time_since_progress > self.STUCK_TIME_THRESHOLD:
                    self.target_survivor = None
                    self.time_since_progress = 0.0
                    # Will retarget next frame
        elif self.target_building and self.target_building in building_group:
            # Check if we're in attack range
            distance = (self.pos - self.target_building.pos).length()
            
            # Check if enemy is ranged (like spitter or archer skeleton)
            is_ranged = hasattr(self, 'ranged') and self.ranged
            
            # For ranged enemies, use full attack_range. For melee, add radius.
            if is_ranged:
                attack_distance = self.attack_range
            else:
                attack_distance = self.attack_range + self.ZOMBIE_RADIUS
            
            if distance <= attack_distance:
                # Stop moving and attack
                self.velocity = pygame.Vector2(0, 0)
                self.is_attacking = True
                
                # Attack building
                if self.attack_timer >= self.attack_cooldown:
                    self.attack_building(self.target_building, world)
                    self.attack_timer = 0.0
                
                # Reset stuck detection when attacking
                self.time_since_progress = 0.0
            else:
                # Move toward building
                self.is_attacking = False
                direction = (self.target_building.pos - self.pos)
                if direction.length() > 0:
                    direction = direction.normalize()
                    self.velocity = direction * self.speed
                
                # Check stuck detection (progress toward target)
                progress_distance = (self.pos - self.last_progress_check_pos).length()
                if progress_distance < self.STUCK_PROGRESS_THRESHOLD:
                    self.time_since_progress += dt
                else:
                    # Made progress - reset timer
                    self.time_since_progress = 0.0
                    self.last_progress_check_pos = pygame.Vector2(self.pos)
                
                # Retarget if stuck for too long
                if self.time_since_progress > self.STUCK_TIME_THRESHOLD:
                    # Release current target's slot
                    if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                        self.target_building.release_attack_slot()
                    self.target_building = None
                    self.time_since_progress = 0.0
                    # Will retarget next frame
        else:
            # No target - move straight down (default behavior)
            self.is_attacking = False
            if self.velocity.length() == 0:
                self.set_direction((0, 1))  # Down direction
        
        # Handle wall collisions using tile-based collision map (BEFORE movement)
        if world and hasattr(world, 'collision_map') and world.collision_map and hasattr(world, 'tile_size'):
            # Convert position to tile index
            tile_x = int(self.pos.x // world.tile_size)
            tile_y = int(self.pos.y // world.tile_size)
            
            # Check if current tile is solid (walls/gates/HQ)
            if world.collision_map.is_solid(tile_x, tile_y):
                # Push enemy back out of the wall
                self.pos -= self.velocity * dt * 1.5
                
                # Slide along the wall axis (horizontal or vertical)
                # Check adjacent tiles to determine slide direction
                if world.collision_map.is_solid(tile_x, tile_y - 1) or world.collision_map.is_solid(tile_x, tile_y + 1):
                    # Wall is horizontal - allow horizontal slide
                    self.pos.x += self.velocity.x * dt
                if world.collision_map.is_solid(tile_x - 1, tile_y) or world.collision_map.is_solid(tile_x + 1, tile_y):
                    # Wall is vertical - allow vertical slide
                    self.pos.y += self.velocity.y * dt
            else:
                # Check the tile we're moving into (prevent moving into walls)
                next_pos = self.pos + self.velocity * dt
                next_tile_x = int(next_pos.x // world.tile_size)
                next_tile_y = int(next_pos.y // world.tile_size)
                
                if world.collision_map.is_solid(next_tile_x, next_tile_y):
                    # About to move into wall - slide along it instead
                    if world.collision_map.is_solid(next_tile_x, tile_y - 1) or world.collision_map.is_solid(next_tile_x, tile_y + 1):
                        # Wall is horizontal - allow horizontal slide only
                        self.velocity.y = 0
                        self.pos.x += self.velocity.x * dt
                    elif world.collision_map.is_solid(tile_x - 1, next_tile_y) or world.collision_map.is_solid(tile_x + 1, next_tile_y):
                        # Wall is vertical - allow vertical slide only
                        self.velocity.x = 0
                        self.pos.y += self.velocity.y * dt
                    else:
                        # Moving into corner - stop movement
                        self.pos -= self.velocity * dt * 1.2
                else:
                    # No collision - normal movement
                    self.pos += self.velocity * dt
        else:
            # Fallback: normal movement if no collision map
            self.pos += self.velocity * dt
        
        # Update rect for collision (circle-based collision handled separately)
        self.rect.center = self.pos
        
        # Check if reached bottom of screen (use constants if available)
        screen_height = 1080  # Default, can be overridden
        if world and hasattr(world, 'screen_height'):
            screen_height = world.screen_height
        elif hasattr(self, 'screen_height'):
            screen_height = self.screen_height
        
        if self.pos.y > screen_height:
            self.reached_bottom = True
            self.on_reach_bottom()
    
    def can_reach_target_fast(self, world, target_grid):
        """
        Fast reachability check using collision map instead of A* pathfinding.
        Simple heuristic: target is reachable unless it's inside a solid area.
        
        Args:
            world: World object with collision_map
            target_grid: Target position as (grid_x, grid_y)
            
        Returns:
            True if target appears reachable, False otherwise
        """
        if not world or not hasattr(world, 'collision_map') or not world.collision_map:
            return True  # Assume reachable if no collision map
        
        gx, gy = target_grid
        # Simple check: target is unreachable if it's in a solid tile
        # This is much faster than A* pathfinding
        return not world.collision_map.is_solid(gx, gy)
    
    def choose_target(self, world):
        """
        Choose target using priority system:
        1. Survivors in attack range
        2. Buildings doing damage (turrets > HQ > other buildings)
        3. Walls/Gates blocking shortest path
        4. HQ (fallback)
        
        OPTIMIZED: Uses fast reachability checks instead of expensive A* pathfinding.
        """
        # Throttle target evaluation to reduce CPU load
        current_time = time.time()
        if (current_time - self.last_target_evaluation) < self.target_evaluation_interval:
            return  # Skip evaluation if too soon
        self.last_target_evaluation = current_time
        
        # Use spatial grid if available for performance
        spatial_grid = None
        if world and hasattr(world, 'spatial_grid'):
            spatial_grid = world.spatial_grid
        
        # PRIORITY 1: Survivors in attack range
        survivor_group = None
        if world and hasattr(world, 'survivor_group'):
            survivor_group = world.survivor_group
        
        best_survivor = None
        best_survivor_distance = float('inf')
        
        if survivor_group:
            # Check if enemy is ranged
            is_ranged = hasattr(self, 'ranged') and self.ranged
            attack_distance = self.attack_range if is_ranged else self.attack_range + self.ZOMBIE_RADIUS
            
            # Use spatial grid if available
            if spatial_grid:
                nearby_survivors = spatial_grid.get_nearby(self.pos, radius_cells=2)
                survivors_to_check = [s for s in nearby_survivors if s in survivor_group and s.alive]
            else:
                survivors_to_check = [s for s in survivor_group if s.alive]
            
            for survivor in survivors_to_check:
                distance = (self.pos - survivor.pos).length()
                # Only target survivors within attack range
                if distance <= attack_distance:
                    if distance < best_survivor_distance:
                        best_survivor_distance = distance
                        best_survivor = survivor
        
        # If we found a survivor in range, target it (highest priority)
        if best_survivor:
            # Release building slot if we had one
            if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                self.target_building.release_attack_slot()
            self.target_building = None
            self.target_survivor = best_survivor
            self.last_progress_check_pos = pygame.Vector2(self.pos)
            self.time_since_progress = 0.0
            return
        
        # PRIORITY 2-4: Target buildings (turrets > HQ > other buildings > walls/gates)
        building_group = None
        if world and hasattr(world, 'building_group'):
            building_group = world.building_group
        
        if not building_group:
            self.target_building = None
            self.target_survivor = None
            return
        
        # Get all active buildings
        from world.building import BuildState
        from world.buildings.hq import HQ
        # Import wall/gate types
        try:
            from world.buildings import Gate
            from world.buildings.wall_wood import WallWood
            from world.buildings.wall_iron import WallIron
            # Wall is an alias for WallWood, but we need to check both WallWood and WallIron
            Wall = (WallWood, WallIron)
        except ImportError:
            try:
                from world.buildings.gate import Gate
                from world.buildings.wall_wood import WallWood
                from world.buildings.wall_iron import WallIron
                Wall = (WallWood, WallIron)
            except ImportError:
                Wall = None
                Gate = None
        
        candidates = []
        turrets = []
        hq_building = None
        walls_gates = []
        other_buildings = []
        
        for building in building_group:
            if hasattr(building, 'state'):
                if building.state != BuildState.ACTIVE:
                    continue
            # Categorize buildings by type
            if isinstance(building, HQ):
                hq_building = building
            elif hasattr(building, 'attack_range') or hasattr(building, 'damage'):
                # Turret or building that can attack
                turrets.append(building)
            elif Wall is not None or Gate is not None:
                # Check if building is a wall or gate
                is_wall_or_gate = False
                if Gate is not None and isinstance(building, Gate):
                    is_wall_or_gate = True
                elif Wall is not None:
                    # Wall is always a tuple of (WallWood, WallIron) for isinstance check
                    is_wall_or_gate = isinstance(building, Wall)
                
                if is_wall_or_gate:
                    walls_gates.append(building)
                else:
                    other_buildings.append(building)
            else:
                # Fallback: check building TYPE_ID
                building_type = getattr(building, 'TYPE_ID', '')
                if 'wall' in building_type or 'gate' in building_type:
                    walls_gates.append(building)
                else:
                    other_buildings.append(building)
        
        # Use spatial grid if available for performance
        if spatial_grid:
            # Filter candidates by nearby buildings only
            nearby_buildings = spatial_grid.get_nearby(self.pos, radius_cells=3)
            nearby_turrets = [b for b in turrets if b in nearby_buildings]
            nearby_walls = [b for b in walls_gates if b in nearby_buildings]
            nearby_other = [b for b in other_buildings if b in nearby_buildings]
            
            turrets = nearby_turrets
            walls_gates = nearby_walls
            other_buildings = nearby_other
        
        # PRIORITY 2: Buildings doing damage (turrets > HQ > other buildings)
        # Sort by distance for each category
        def get_distance(b):
            return (self.pos - b.pos).length()
        
        turrets.sort(key=get_distance)
        other_buildings.sort(key=get_distance)
        walls_gates.sort(key=get_distance)
        
        # Score each candidate building
        best_building = None
        best_score = float('inf')
        
        # Helper function to score a building
        def score_building(building):
            distance = (self.pos - building.pos).length()
            distance_weight = distance
            
            # Slot weight (prefer buildings with free slots)
            if hasattr(building, 'attacker_count') and hasattr(building, 'get_attacker_capacity'):
                if building.attacker_count < building.get_attacker_capacity():
                    slot_weight = self.SLOT_PENALTY_FREE
                else:
                    slot_weight = self.SLOT_PENALTY_FULL
            else:
                slot_weight = 0
            
            # Fast reachability check using collision map (replaces expensive A* pathfinding)
            # We skip unreachable targets entirely to avoid wasting computation
            if hasattr(building, 'grid_x') and hasattr(building, 'grid_y'):
                target_grid = (building.grid_x, building.grid_y)
                if not self.can_reach_target_fast(world, target_grid):
                    # Target is unreachable (in solid tile), skip it
                    return float('inf')  # Effectively skips this building
            # Pathfinding penalty removed - we use fast collision map check instead
            return distance_weight + slot_weight
        
        # PRIORITY 2: Buildings doing damage (turrets > HQ > other buildings)
        # Check turrets first (highest priority)
        # OPTIMIZED: Only evaluate top 2 closest turrets instead of 5
        if turrets:
            for building in turrets[:2]:  # Top 2 closest (reduced from 5 for performance)
                score = score_building(building)
                if score < best_score and score != float('inf'):  # Skip unreachable targets
                    best_score = score
                    best_building = building
                    if best_building:  # Found a good target, stop searching
                        break
        
        # Check HQ (fallback but higher priority than walls)
        if not best_building and hq_building:
            score = score_building(hq_building)
            if score < best_score and score != float('inf'):  # Skip unreachable targets
                best_score = score
                best_building = hq_building
        
        # Check other buildings (non-turrets, non-HQ, non-walls)
        if not best_building and other_buildings:
            for building in other_buildings[:3]:  # Top 3 closest
                score = score_building(building)
                if score < best_score and score != float('inf'):  # Skip unreachable targets
                    best_score = score
                    best_building = building
                    break
        
        # PRIORITY 3: Walls/Gates blocking shortest path (only if no other target)
        if not best_building and walls_gates:
            for building in walls_gates[:3]:  # Top 3 closest
                score = score_building(building)
                if score < best_score and score != float('inf'):  # Skip unreachable targets
                    best_score = score
                    best_building = building
                    break
        
        # PRIORITY 4: HQ fallback (if not already checked)
        if not best_building and hq_building:
            best_building = hq_building
        
        # Try to claim a slot on the best building
        if best_building:
            if hasattr(best_building, 'request_attack_slot') and best_building.request_attack_slot():
                # Release old target's slot if any
                if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                    self.target_building.release_attack_slot()
                self.target_building = best_building
                self.target_survivor = None  # Clear survivor target
                # Reset stuck detection when retargeting
                self.last_progress_check_pos = pygame.Vector2(self.pos)
                self.time_since_progress = 0.0
            else:
                # Fallback: target building anyway (slot full or no slot system)
                if self.target_building != best_building:
                    if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                        self.target_building.release_attack_slot()
                    self.target_building = best_building
                    self.target_survivor = None  # Clear survivor target
                    self.last_progress_check_pos = pygame.Vector2(self.pos)
                    self.time_since_progress = 0.0
        else:
            self.target_building = None
            self.target_survivor = None
    
    def find_nearest_building(self, building_group):
        """Legacy method - now uses choose_target instead"""
        # This is kept for backwards compatibility
        # New code should use choose_target()
        if not building_group:
            return None
        
        from world.building import BuildState
        nearest_building = None
        nearest_distance = float('inf')
        
        for building in building_group:
            if hasattr(building, 'state'):
                if building.state == BuildState.ACTIVE:
                    distance = (self.pos - building.pos).length()
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_building = building
        
        return nearest_building
    
    def attack_building(self, building, world=None):
        """Attack a building, dealing damage"""
        if building and hasattr(building, 'take_damage'):
            # Melee attack by default
            building.take_damage(self.damage, world)
            self.on_attack(building)
    
    def attack_survivor(self, survivor, world=None):
        """Attack a survivor, dealing damage"""
        if survivor and survivor.alive and hasattr(survivor, 'take_damage'):
            # Melee attack
            survivor.take_damage(self.damage)
            self.on_attack_survivor(survivor)
    
    def take_damage(self, amount: int):
        """Apply damage to enemy. SwarmlingZombie takes double damage."""
        if not self.alive:
            return
        
        # SwarmlingZombie takes double damage
        from world.enemies.swarmling import SwarmlingZombie
        if isinstance(self, SwarmlingZombie):
            amount *= 2
        
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            # Release attack slot on death
            if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                self.target_building.release_attack_slot()
            # Clear survivor target
            self.target_survivor = None
            self.on_death()
    
    def heal(self, amount: int):
        """Heal enemy"""
        if not self.alive:
            return
        
        self.hp = min(self.max_hp, self.hp + amount)
    
    def set_direction(self, direction: Tuple[float, float]):
        """Set movement direction (normalized vector)"""
        self.velocity = pygame.Vector2(direction).normalize() * self.speed
    
    def set_velocity(self, velocity: Tuple[float, float]):
        """Set velocity directly"""
        self.velocity = pygame.Vector2(velocity)
    
    def on_death(self):
        """Called when enemy dies"""
        pass
    
    def on_reach_bottom(self):
        """Called when enemy reaches bottom of screen"""
        pass
    
    def on_attack(self, building):
        """Called when enemy attacks a building"""
        pass
    
    def on_attack_survivor(self, survivor):
        """Called when enemy attacks a survivor"""
        pass
    
    def draw(self, surface: pygame.Surface):
        """Draw the enemy"""
        if not self.alive:
            return
        
        # Ensure rect exists
        if not hasattr(self, 'rect') or self.rect is None:
            # Create rect if missing
            if not hasattr(self, 'image') or self.image is None:
                self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=self.pos if hasattr(self, 'pos') else (0, 0))
        
        # Update rect position
        if hasattr(self, 'pos'):
            self.rect.center = self.pos
        else:
            return  # Can't draw without position
        
        # Draw enemy body (subclasses can override)
        self.draw_body(surface)
        
        # Draw HP bar
        if self.hp < self.max_hp:
            self.draw_hp_bar(surface)
    
    def draw_body(self, surface: pygame.Surface):
        """Draw the enemy body - override in subclasses"""
        # Default: red rectangle
        self.image.fill((0, 0, 0, 0))
        color = (150, 0, 0) if self.alive else (50, 50, 50)
        pygame.draw.rect(self.image, color, (0, 0, 32, 32))
        surface.blit(self.image, self.rect)
    
    def draw_hp_bar(self, surface: pygame.Surface):
        """Draw HP bar above enemy"""
        if self.hp <= 0:
            return
        
        bar_width = 30
        bar_height = 4
        hp_percent = self.hp / self.max_hp
        
        # Position above enemy
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 8
        
        # Background (black)
        pygame.draw.rect(surface, (0, 0, 0), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))
        
        # HP bar (green to red based on health)
        hp_color = (
            int(255 * (1 - hp_percent)),  # Red component
            int(255 * hp_percent),         # Green component
            0                              # Blue component
        )
        hp_width = int(bar_width * hp_percent)
        pygame.draw.rect(surface, hp_color, (bar_x, bar_y, hp_width, bar_height))

