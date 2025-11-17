"""
Automated resource collection droids.
"""
import pygame
import math
import os
from typing import Tuple, Optional
from world.survivor import Survivor, SurvivorState
from world.building import BuildState, TILE

class Droid(Survivor):
    """Base class for automated resource collection droids"""
    BASE_HP = 50
    SPEED = 60.0  # Slower than survivors
    CARRY_CAPACITY = 60  # Higher capacity than survivors
    SURVIVOR_RADIUS = 8.0  # Hitbox radius for collision detection
    
    def __init__(self, pos: Tuple[float, float], resource_type: str, hp: Optional[int] = None, world=None):
        """
        Initialize droid.
        Args:
            pos: Starting position
            resource_type: "wood" or "iron"
            hp: Optional HP override
            world: World reference
        """
        hp = hp if hp is not None else self.BASE_HP
        super().__init__(pos, role="droid", hp=hp, world=world)
        self.resource_type = resource_type
        self.speed = self.SPEED
        self.carry_capacity = self.CARRY_CAPACITY
        self.carried = {"wood": 0, "iron": 0, "food": 0}
        
        # FSM state
        self.state = SurvivorState.IDLE
        self.target_node = None
        self.target_hq = None
        self.gather_timer = 0.0
        self.current_gather_tick_time = 0.0
        
        # Node search cooldown
        self.last_node_search = 0.0
        self.node_search_interval = 2.0  # Search for nodes every 2 seconds
        
        # Load droid-specific sprite sheet
        self.load_droid_sprite_sheet()
    
    def load_droid_sprite_sheet(self):
        """Load droid-specific sprite sheet"""
        sprite_path = None
        
        # Determine which sprite sheet to load based on resource type
        if self.resource_type == "iron":
            sprite_path = os.path.join('asset', 'DrillDroid-Sheet.png')
        elif self.resource_type == "wood":
            sprite_path = os.path.join('asset', 'ChaisawDroid-Sheet.png')
        
        try:
            if sprite_path and os.path.exists(sprite_path):
                droid_sheet = pygame.image.load(sprite_path).convert_alpha()
                
                # Each frame is 32x32, 16 frames total
                frame_width = 32
                frame_height = 32
                total_frames = 16
                
                # Extract all 16 frames
                self.all_frames = []
                for i in range(total_frames):
                    frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                    if frame_rect.right <= droid_sheet.get_width():
                        frame = droid_sheet.subsurface(frame_rect)
                        self.all_frames.append(frame)
                    else:
                        # Frame out of bounds - create placeholder
                        placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                        placeholder.fill((255, 0, 255, 128))  # Magenta placeholder
                        self.all_frames.append(placeholder)
                
                # Update image size to match sprite
                self.image = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                self.rect = self.image.get_rect(center=self.pos)
                
                # Set initial frames (idle: frames 1-4, 0-indexed: 0-3)
                if len(self.all_frames) >= 4:
                    self.current_frames = self.all_frames[0:4]
                    self.current_animation_type = "idle"
            else:
                # Fallback: use placeholder or empty frames
                self.all_frames = []
                self.current_frames = []
        except Exception as e:
            print(f"Warning: Could not load droid sprite sheet {sprite_path}: {e}")
            self.all_frames = []
            self.current_frames = []
    
    def update_animation(self, dt: float):
        """Update droid animation based on state"""
        if not self.all_frames:
            return
        
        # Update facing direction for horizontal flipping (East/West)
        if self.velocity.length() > 0.1:
            if self.velocity.x > 0:
                self.facing_right = True  # Moving right (East)
            elif self.velocity.x < 0:
                self.facing_right = False  # Moving left (West)
        
        # Determine which frames to use based on state
        # Frame mapping (0-indexed):
        # 0-3: idle (frames 1-4)
        # 4-7: running (frames 5-8)
        # 8-11: action (frames 9-12) - gathering
        # 12-15: hauling (frames 13-16)
        
        new_animation_type = None
        new_frames = None
        
        if not self.alive:
            # Death - use last frame of action or idle
            if len(self.all_frames) >= 4:
                new_frames = self.all_frames[0:4]
                new_animation_type = "idle"
        elif hasattr(self, 'state'):
            if self.state == SurvivorState.IDLE:
                # Idle animation (frames 0-3)
                if len(self.all_frames) >= 4:
                    new_frames = self.all_frames[0:4]
                    new_animation_type = "idle"
            elif self.state == SurvivorState.MOVE_TO_NODE:
                # Running animation (frames 4-7)
                if len(self.all_frames) >= 8:
                    new_frames = self.all_frames[4:8]
                    new_animation_type = "run"
            elif self.state == SurvivorState.GATHERING:
                # Action animation (frames 8-11)
                if len(self.all_frames) >= 12:
                    new_frames = self.all_frames[8:12]
                    new_animation_type = "action"
            elif self.state == SurvivorState.HAUL_TO_HQ or self.state == SurvivorState.DEPOSIT:
                # Hauling animation (frames 12-15) - only if carrying resources
                if self.get_total_carried() > 0:
                    if len(self.all_frames) >= 16:
                        new_frames = self.all_frames[12:16]
                        new_animation_type = "hauling"
                else:
                    # Not carrying - use running animation
                    if len(self.all_frames) >= 8:
                        new_frames = self.all_frames[4:8]
                        new_animation_type = "run"
            else:
                # Default to idle
                if len(self.all_frames) >= 4:
                    new_frames = self.all_frames[0:4]
                    new_animation_type = "idle"
        
        # Check if animation type changed - if so, reset frame index
        if new_animation_type and new_animation_type != getattr(self, 'current_animation_type', None):
            self.frame_index = 0
            self.animation_timer = 0.0
        
        # Update current frames and animation type
        if new_frames:
            self.current_frames = new_frames
        if new_animation_type:
            self.current_animation_type = new_animation_type
        
        # Update animation timer (only if we have frames)
        if self.current_frames:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_delay:
                self.animation_timer = 0.0
                self.frame_index = (self.frame_index + 1) % len(self.current_frames)
        
        # Safety check: reset frame index if out of bounds
        if self.current_frames and self.frame_index >= len(self.current_frames):
            self.frame_index = 0
    
    def draw(self, surface: pygame.Surface):
        """Draw droid with proper sprite animation"""
        if not self.alive:
            return
        
        # Get current frame (animation is updated in update() method)
        if self.current_frames and 0 <= self.frame_index < len(self.current_frames):
            frame = self.current_frames[self.frame_index]
            
            # Flip horizontally if facing left (West)
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            
            # Scale frame by 1.2
            scale_factor = 1.2
            scaled_width = int(frame.get_width() * scale_factor)
            scaled_height = int(frame.get_height() * scale_factor)
            frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
            
            # Draw frame centered on position
            frame_rect = frame.get_rect(center=self.pos)
            surface.blit(frame, frame_rect)
        else:
            # Fallback: draw simple circle
            pygame.draw.circle(surface, (100, 150, 200), (int(self.pos.x), int(self.pos.y)), 8)
    
    def get_total_carried(self) -> int:
        """Get total amount of resources carried"""
        return sum(self.carried.values())
    
    def can_carry_more(self) -> bool:
        """Check if droid can carry more resources"""
        return self.get_total_carried() < self.carry_capacity
    
    def find_nearest_node(self, node_group, world=None):
        """Find nearest node of the droid's resource type"""
        if not node_group:
            return None
        
        nearest_node = None
        nearest_distance = float('inf')
        
        for node in node_group:
            # Check if node matches resource type and is not depleted
            if not hasattr(node, 'resource'):
                continue
            if node.resource != self.resource_type:
                continue
            if node.is_depleted():
                continue
            
            # Calculate distance
            if not hasattr(node, 'pos'):
                continue
            distance = (self.pos - node.pos).length()
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_node = node
        
        return nearest_node
    
    def update(self, dt: float, world=None):
        """Update droid state and behavior"""
        if not self.alive:
            return
        
        # Update animation
        self.update_animation(dt)
        
        # Update pathfinding timer (required by move_toward)
        self.path_recalc_timer += dt
        
        # Get node group from world or global
        node_group = None
        if world:
            if hasattr(world, 'nodes'):
                node_group = world.nodes
            elif hasattr(world, 'node_group'):
                node_group = world.node_group
        
        # Fallback: try to get from global scope if available
        if not node_group:
            import sys
            main_module = sys.modules.get('__main__')
            if main_module and hasattr(main_module, 'node_group'):
                node_group = main_module.node_group
        
        # Debug: Print node group info
        if node_group:
            node_count = len(node_group)
            print(f"[{self.resource_type.upper()} DROID] Node group found: {node_count} nodes")
        else:
            print(f"[{self.resource_type.upper()} DROID] WARNING: No node group found!")
        
        # Get HQ reference
        hq = None
        if world:
            if hasattr(world, 'hq') and world.hq:
                hq = world.hq
            elif hasattr(world, 'building_group'):
                from world.buildings.hq import HQ
                for building in world.building_group:
                    if isinstance(building, HQ):
                        hq = building
                        break
        
        if hq:
            self.target_hq = hq
        
        # State machine
        if self.state == SurvivorState.IDLE:
            # Search for nodes periodically
            self.last_node_search += dt
            if self.last_node_search >= self.node_search_interval and node_group:
                print(f"[{self.resource_type.upper()} DROID] Searching for {self.resource_type} nodes...")
                self.target_node = self.find_nearest_node(node_group, world)
                if self.target_node:
                    print(f"[{self.resource_type.upper()} DROID] Found node at ({self.target_node.pos.x:.1f}, {self.target_node.pos.y:.1f}), moving to it")
                    self.target_pos = self.target_node.pos
                    self.state = SurvivorState.MOVE_TO_NODE
                    self.last_progress_check_pos = pygame.Vector2(self.pos)
                    self.time_since_progress = 0.0
                    self.last_node_search = 0.0
                else:
                    print(f"[{self.resource_type.upper()} DROID] No {self.resource_type} nodes found")
                    self.last_node_search = 0.0  # Reset if no node found
            elif not node_group:
                print(f"[{self.resource_type.upper()} DROID] IDLE: No node group available")
        
        elif self.state == SurvivorState.MOVE_TO_NODE:
            if not self.target_node or self.target_node.is_depleted():
                # Node depleted - find new node or go idle
                print(f"[{self.resource_type.upper()} DROID] Target node depleted, going idle")
                self.target_node = None
                self.state = SurvivorState.IDLE
                return
            
            # Move toward node
            node_reach_distance = self.target_node.radius_px + 8
            distance_to_node = (self.pos - self.target_node.pos).length()
            print(f"[{self.resource_type.upper()} DROID] Moving to node: distance={distance_to_node:.1f}, velocity={self.velocity.length():.1f}")
            reached = self.move_toward(self.target_node.pos, dt, world, stop_distance=node_reach_distance)
            
            if reached:
                # Reached node - start gathering
                print(f"[{self.resource_type.upper()} DROID] Reached node, starting to gather")
                self.state = SurvivorState.GATHERING
                self.gather_timer = 0.0
                self.current_gather_tick_time = 0.0
                self.velocity = pygame.Vector2(0, 0)
            elif self.time_since_progress > self.STUCK_TIME_THRESHOLD:
                # Stuck - find new node
                print(f"[{self.resource_type.upper()} DROID] Stuck, finding new node")
                self.time_since_progress = 0.0
                self.last_progress_check_pos = pygame.Vector2(self.pos)
                self.target_node = None
                self.state = SurvivorState.IDLE
        
        elif self.state == SurvivorState.GATHERING:
            if not self.target_node or self.target_node.is_depleted():
                # Node depleted - haul what we have or find new node
                print(f"[{self.resource_type.upper()} DROID] Node depleted while gathering, carried={self.get_total_carried()}")
                if self.get_total_carried() > 0:
                    self.state = SurvivorState.HAUL_TO_HQ
                    if hq:
                        self.target_pos = hq.pos
                else:
                    self.target_node = None
                    self.state = SurvivorState.IDLE
                return
            
            # Gather resources in ticks
            gather_speed_mult = 1.0
            if world and hasattr(world, 'modifiers'):
                gather_speed_mult = world.modifiers.get("gather_speed_mult", 1.0)
            
            effective_tick_sec = self.target_node.tick_sec / gather_speed_mult if gather_speed_mult > 0 else self.target_node.tick_sec
            
            self.current_gather_tick_time += dt
            if self.current_gather_tick_time >= effective_tick_sec:
                # Tick complete - gather resources
                if self.can_carry_more():
                    gathered = self.target_node.gather_tick()
                    
                    if gathered > 0:
                        resource = self.target_node.resource
                        space_available = self.carry_capacity - self.get_total_carried()
                        amount_to_add = min(gathered, space_available)
                        self.carried[resource] += amount_to_add
                        print(f"[{self.resource_type.upper()} DROID] Gathered {amount_to_add} {resource}, total carried={self.get_total_carried()}/{self.carry_capacity}")
                    self.current_gather_tick_time = 0.0
                else:
                    # At capacity - start hauling
                    print(f"[{self.resource_type.upper()} DROID] At capacity ({self.get_total_carried()}/{self.carry_capacity}), starting to haul")
                    self.state = SurvivorState.HAUL_TO_HQ
                    if hq:
                        self.target_pos = hq.pos
            
            # Check if node depleted
            if self.target_node.is_depleted():
                print(f"[{self.resource_type.upper()} DROID] Node depleted, carried={self.get_total_carried()}")
                if self.get_total_carried() > 0:
                    self.state = SurvivorState.HAUL_TO_HQ
                    if hq:
                        self.target_pos = hq.pos
                else:
                    self.target_node = None
                    self.state = SurvivorState.IDLE
        
        elif self.state == SurvivorState.HAUL_TO_HQ:
            if not hq:
                # No HQ found - go idle
                print(f"[{self.resource_type.upper()} DROID] No HQ found, going idle")
                self.state = SurvivorState.IDLE
                return
            
            print(f"[{self.resource_type.upper()} DROID] Hauling to HQ, carried={self.get_total_carried()}, pos=({self.pos.x:.1f}, {self.pos.y:.1f})")
            
            # Check if droid is adjacent to HQ footprint
            from world.building import TILE
            from world.buildings.hq import HQ
            
            hq_footprint = hq.FOOTPRINT
            hq_grid_x = hq.grid_x
            hq_grid_y = hq.grid_y
            
            survivor_grid_x = int(self.pos.x // TILE)
            survivor_grid_y = int(self.pos.y // TILE)
            
            # Check if adjacent to HQ footprint
            is_adjacent = False
            for fx in range(hq_footprint[0]):
                for fy in range(hq_footprint[1]):
                    hq_tile_x = hq_grid_x + fx
                    hq_tile_y = hq_grid_y + fy
                    
                    dx = abs(survivor_grid_x - hq_tile_x)
                    dy = abs(survivor_grid_y - hq_tile_y)
                    if (dx == 1 and dy == 0) or (dx == 0 and dy == 1):
                        is_adjacent = True
                        break
                if is_adjacent:
                    break
            
            # Move toward nearest adjacent tile if not already adjacent
            if not is_adjacent:
                nearest_adjacent = None
                min_dist = float('inf')
                for fx in range(hq_footprint[0]):
                    for fy in range(hq_footprint[1]):
                        hq_tile_x = hq_grid_x + fx
                        hq_tile_y = hq_grid_y + fy
                        
                        for adj_dx, adj_dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                            adj_x = hq_tile_x + adj_dx
                            adj_y = hq_tile_y + adj_dy
                            
                            # Check if this adjacent tile is not part of HQ footprint
                            is_hq_tile = False
                            for check_fx in range(hq_footprint[0]):
                                for check_fy in range(hq_footprint[1]):
                                    if (hq_grid_x + check_fx == adj_x and 
                                        hq_grid_y + check_fy == adj_y):
                                        is_hq_tile = True
                                        break
                                if is_hq_tile:
                                    break
                            
                            if not is_hq_tile:
                                adj_pos = pygame.Vector2(
                                    adj_x * TILE + TILE // 2,
                                    adj_y * TILE + TILE // 2
                                )
                                dist = (self.pos - adj_pos).length()
                                if dist < min_dist:
                                    min_dist = dist
                                    nearest_adjacent = adj_pos
                
                if nearest_adjacent:
                    reached = self.move_toward(nearest_adjacent, dt, world, stop_distance=16.0)
                else:
                    reached = self.move_toward(hq.pos, dt, world, stop_distance=16.0)
            else:
                reached = True
            
            if reached and is_adjacent:
                # Reached HQ - deposit
                print(f"[{self.resource_type.upper()} DROID] Reached HQ, depositing {self.get_total_carried()} resources")
                self.state = SurvivorState.DEPOSIT
                self.velocity = pygame.Vector2(0, 0)
            elif self.time_since_progress > self.STUCK_TIME_THRESHOLD:
                # Stuck - recompute path
                self.time_since_progress = 0.0
                self.last_progress_check_pos = pygame.Vector2(self.pos)
        
        elif self.state == SurvivorState.DEPOSIT:
            # Deposit resources at HQ
            wood_deposited = self.carried["wood"]
            iron_deposited = self.carried["iron"]
            food_deposited = self.carried["food"]
            
            if world and hasattr(world, 'deposit'):
                if self.carried["wood"] > 0:
                    world.deposit("wood", self.carried["wood"])
                if self.carried["iron"] > 0:
                    world.deposit("iron", self.carried["iron"])
                if self.carried["food"] > 0:
                    world.deposit("food", self.carried["food"])
                
                self.carried = {"wood": 0, "iron": 0, "food": 0}
            elif world and hasattr(world, 'resources'):
                world.resources.wood += self.carried["wood"]
                world.resources.iron += self.carried["iron"]
                world.resources.food += self.carried["food"]
                
                self.carried = {"wood": 0, "iron": 0, "food": 0}
            
            print(f"[{self.resource_type.upper()} DROID] Deposited: wood={wood_deposited}, iron={iron_deposited}, food={food_deposited}")
            
            # After depositing, find new node
            self.target_node = None
            self.state = SurvivorState.IDLE
        
        # Update position based on velocity (required for movement)
        # This must be done after move_toward() sets the velocity
        if self.velocity.length() > 0:
            self.pos += self.velocity * dt
            self.rect.center = self.pos

class DrillingDroid(Droid):
    """Drilling droid - automatically collects iron from scrap piles"""
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, world=None):
        super().__init__(pos, resource_type="iron", hp=hp, world=world)

class WoodCuttingDroid(Droid):
    """Wood cutting droid - automatically collects wood from tree patches"""
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, world=None):
        super().__init__(pos, resource_type="wood", hp=hp, world=world)

