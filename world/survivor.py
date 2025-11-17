"""
Survivor classes: Workers and Guards.
"""
import pygame
import json
import math
import random
import os
from typing import Tuple, Optional, Dict, List
from enum import Enum

class SurvivorState(Enum):
    """FSM states for survivors"""
    IDLE = "idle"
    MOVE_TO_NODE = "move_to_node"
    GATHERING = "gathering"
    HAUL_TO_HQ = "haul_to_hq"
    DEPOSIT = "deposit"
    FLEE = "flee"
    REPAIRING = "repairing"

class Survivor(pygame.sprite.Sprite):
    """Base class for survivors (Workers and Guards)"""
    ROLE: str = "survivor"
    BASE_HP: int = 100
    SPEED: float = 90.0  # pixels per second
    
    # Separation constants (smaller than zombies)
    SURVIVOR_RADIUS: float = 8.0
    SEPARATION_PUSH: float = 60.0
    SEPARATION_MAX_NEIGHBORS: int = 4
    SEPARATION_RANGE: float = 32.0
    
    # Stuck detection
    STUCK_TIME_THRESHOLD: float = 2.0
    STUCK_PROGRESS_THRESHOLD: float = 8.0
    
    def __init__(self, pos: Tuple[float, float], role: str = "worker", hp: Optional[int] = None, world=None):
        super().__init__()
        self.role = role
        # Apply survivor HP modifier if available
        base_hp = hp if hp is not None else self.BASE_HP
        if world and hasattr(world, 'modifiers'):
            hp_mult = world.modifiers.get("survivor_hp_mult", 1.0)
            self.max_hp = int(base_hp * hp_mult)
        else:
            self.max_hp = base_hp
        self.hp = self.max_hp
        self.speed = self.SPEED
        self.base_speed = self.SPEED  # Store base speed for modifier calculations
        
        # Position
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        self.target_pos = None
        
        # Rendering
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
        # Sprite sheet and animation
        self.all_frames = []  # All frames from the sheet
        self.current_frames = []
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.15  # seconds per frame
        self.facing_right = True
        self.direction = "s"  # Current direction: "s", "se", "ne", "n"
        self.is_hurt = False
        self.hurt_timer = 0.0
        self.hurt_duration = 0.5  # How long to show hurt animation
        self.sprite_scale = 1.2  # Scale factor for sprite (1.5x = 50% bigger)
        self.current_animation_type = "idle"  # Track current animation: "idle", "run", "axe", "mining", "carry", "hurt", "death"
        
        # Load sprite sheets
        self.load_sprite_sheets()
        
        # State
        self.alive = True
        self.state = SurvivorState.IDLE
        self.can_gather_today = True  # Can gather today (injured survivors cannot)
        
        # Stuck detection
        self.last_progress_check_pos = pygame.Vector2(self.pos)
        self.time_since_progress = 0.0
        self.path_recalc_timer = 0.0
        self.path_recalc_interval = 1.0  # Recalculate path every 1.0 seconds (optimized from 0.5)
        
        # Pathfinding
        self.current_path = []  # List of (grid_x, grid_y) positions
        self.path_target = None  # Target position for pathfinding
        self.path_index = 0  # Current index in path
        
        # Safe distance to enemies
        self.safe_distance_to_enemy_px = 160.0
        self.flee_on_threat = True
    def _get_effective_speed(self, world=None):
        """Get effective speed with modifiers applied"""
        if world and hasattr(world, 'modifiers'):
            speed_mult = world.modifiers.get("survivor_speed_mult", 1.0)
            return self.base_speed * speed_mult
        return self.speed
    
    def load_sprite_sheets(self):
        """Load new survivor sprite sheets - Survivor1-4-Sheet.png with 78 frames (96x64 each)"""
        try:
            # Try to load one of the new survivor sprite sheets (randomly select for variety)
            survivor_paths = [
                os.path.join('asset', 'Survivor', 'Survivor1-Sheet.png'),
                os.path.join('asset', 'Survivor', 'Survivor2-Sheet.png'),
                os.path.join('asset', 'Survivor', 'Survivor3-Sheet.png'),
                os.path.join('asset', 'Survivor', 'Survivor4-Sheet.png'),
            ]
            
            # Randomly select one of the available sprite sheets for variety
            available_paths = [path for path in survivor_paths if os.path.exists(path)]
            survivor_sheet = None
            
            if available_paths:
                # Randomly pick one
                selected_path = random.choice(available_paths)
                try:
                    survivor_sheet = pygame.image.load(selected_path).convert_alpha()
                except:
                    # If selected one fails, try others
                    for path in available_paths:
                        if path != selected_path:
                            try:
                                survivor_sheet = pygame.image.load(path).convert_alpha()
                                break
                            except:
                                continue
            
            # If no new sprites found, try old path as fallback
            if not survivor_sheet:
                old_paths = [
                    os.path.join('asset', 'survival-Sheet.png'),
                    'asset/survival-Sheet.png',
                ]
                for path in old_paths:
                    if os.path.exists(path):
                        try:
                            survivor_sheet = pygame.image.load(path).convert_alpha()
                            break
                        except:
                            continue
            
            if survivor_sheet:
                frame_width = 96
                frame_height = 64
                total_frames = 78
                
                # Extract all 78 frames
                self.all_frames = []
                for i in range(total_frames):
                    frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                    if frame_rect.right <= survivor_sheet.get_width():
                        frame = survivor_sheet.subsurface(frame_rect)
                        self.all_frames.append(frame)
                    else:
                        # Frame out of bounds - create placeholder
                        placeholder = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                        placeholder.fill((255, 0, 255, 128))  # Magenta placeholder
                        self.all_frames.append(placeholder)
                
                # Scale frames and update image size to match scaled sprite
                scaled_width = int(frame_width * self.sprite_scale)
                scaled_height = int(frame_height * self.sprite_scale)
                self.image = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                self.rect = self.image.get_rect(center=self.pos)
                
                # Set initial frames (idle: frames 1-4, 0-indexed: 0-3)
                if len(self.all_frames) >= 4:
                    self.current_frames = self.all_frames[0:4]
            else:
                # Fallback to old sprite sheets if new ones don't exist
                try:
                    idle_sheet = pygame.image.load('asset/16x32 Idle-Sheet.png').convert_alpha()
                    run_sheet = pygame.image.load('asset/16x32 Run Cycle-Sheet.png').convert_alpha()
                    
                    frame_width = 16
                    frame_height = 32
                    
                    # Extract frames from idle sheet (4 frames)
                    idle_frames = []
                    for i in range(4):
                        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                        frame = idle_sheet.subsurface(frame_rect)
                        idle_frames.append(frame)
                    
                    # Extract frames from run sheet (6 frames)
                    run_frames = []
                    for i in range(6):
                        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                        frame = run_sheet.subsurface(frame_rect)
                        run_frames.append(frame)
                    
                    # Store as all_frames for compatibility
                    self.all_frames = idle_frames + run_frames
                    self.current_frames = idle_frames
                    
                    # Update image size
                    self.image = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    self.rect = self.image.get_rect(center=self.pos)
                except:
                    # If sprite sheets don't exist, frames will remain empty and fallback to circles
                    self.all_frames = []
                    self.current_frames = []
        except Exception as e:
            print(f"Warning: Could not load survivor sprites: {e}")
            self.all_frames = []
            self.current_frames = []
    
    def get_direction_from_velocity(self) -> str:
        """Get direction string from velocity vector: 's', 'se', 'ne', 'n'"""
        if self.velocity.length() < 0.1:
            return self.direction  # Keep last direction when not moving
        
        # Normalize velocity
        vel_norm = self.velocity.normalize()
        angle = math.degrees(math.atan2(vel_norm.y, vel_norm.x))
        
        # Convert angle to direction
        # -45 to 45: east (use se for right side)
        # 45 to 135: south
        # 135 to 225: west (use ne for left side, flipped)
        # 225 to 315: north
        # -135 to -45: north (wrapped)
        
        # Adjust angle to 0-360 range
        if angle < 0:
            angle += 360
        
        # Map to 4 directions
        if 22.5 <= angle < 67.5:
            return "se"  # Southeast
        elif 67.5 <= angle < 112.5:
            return "s"  # South
        elif 112.5 <= angle < 157.5:
            return "se"  # Southwest (use se, will be flipped)
        elif 157.5 <= angle < 202.5:
            return "s"  # West (use s, will be flipped)
        elif 202.5 <= angle < 247.5:
            return "ne"  # Northwest (use ne frames, will be flipped for correct NW display)
        elif 247.5 <= angle < 292.5:
            return "n"  # North
        elif 292.5 <= angle < 337.5:
            return "ne"  # Northeast (use ne frames, not flipped - correct NE display)
        else:  # 337.5-360 or 0-22.5
            return "se"  # East (use se)
    
    def update_animation(self, dt: float):
        """Update animation frame based on state and direction - new sprite sheet format"""
        if not self.all_frames:
            return
        
        # Update hurt timer
        if self.is_hurt:
            self.hurt_timer += dt
            if self.hurt_timer >= self.hurt_duration:
                self.is_hurt = False
                self.hurt_timer = 0.0
        
        # Determine direction from velocity
        self.direction = self.get_direction_from_velocity()
        
        # Update facing direction for horizontal flipping (East/West)
        if self.velocity.length() > 0.1:
            if self.velocity.x > 0:
                self.facing_right = True  # Moving right (East)
            elif self.velocity.x < 0:
                self.facing_right = False  # Moving left (West)
        
        # Determine which frames to use based on state
        # New sprite sheet frame mapping:
        # 1-4: idle (0-3 indexed)
        # 13-20: carry (12-19 indexed)
        # 30-37: hurt (29-36 indexed)
        # 38-50: death (37-49 indexed)
        # 51-58: run East (50-57 indexed) - flip for West
        # 59-68: axe East (58-67 indexed) - flip for West (wood gathering)
        # 69-78: mining East (68-77 indexed) - flip for West (iron gathering)
        
        # Check if dead first
        if not self.alive:
            # Death animation (frames 38-50, 0-indexed: 37-49)
            if len(self.all_frames) >= 50:
                self.current_frames = self.all_frames[37:50]
                self.current_animation_type = "death"
                # Don't loop death animation - stay on last frame
                if self.frame_index >= len(self.current_frames):
                    self.frame_index = len(self.current_frames) - 1
        elif self.is_hurt:
            # Hurt animation (frames 30-37, 0-indexed: 29-36)
            if len(self.all_frames) >= 37:
                self.current_frames = self.all_frames[29:37]
                self.current_animation_type = "hurt"
        elif hasattr(self, 'state'):
            # Check worker-specific states
            if self.state == SurvivorState.GATHERING:
                # Check if gathering wood or iron
                if hasattr(self, 'target_node') and self.target_node:
                    if hasattr(self.target_node, 'resource'):
                        if self.target_node.resource == "wood":
                            # Wood gathering - axe animation (frames 59-68, 0-indexed: 58-67) - East facing
                            if len(self.all_frames) >= 68:
                                self.current_frames = self.all_frames[58:68]
                                self.current_animation_type = "axe"
                        elif self.target_node.resource == "iron":
                            # Iron gathering - mining animation (frames 69-78, 0-indexed: 68-77) - East facing
                            if len(self.all_frames) >= 78:
                                self.current_frames = self.all_frames[68:78]
                                self.current_animation_type = "mining"
                        else:
                            # Default to wood gathering (axe)
                            if len(self.all_frames) >= 68:
                                self.current_frames = self.all_frames[58:68]
                                self.current_animation_type = "axe"
                    else:
                        # Default to wood gathering (axe)
                        if len(self.all_frames) >= 68:
                            self.current_frames = self.all_frames[58:68]
                            self.current_animation_type = "axe"
                else:
                    # Default to wood gathering (axe)
                    if len(self.all_frames) >= 68:
                        self.current_frames = self.all_frames[58:68]
                        self.current_animation_type = "axe"
            elif self.state == SurvivorState.HAUL_TO_HQ or self.state == SurvivorState.DEPOSIT:
                # Hauling - carry animation (frames 13-20, 0-indexed: 12-19)
                if len(self.all_frames) >= 20:
                    self.current_frames = self.all_frames[12:20]
                    self.current_animation_type = "carry"
            else:
                # Idle or moving
                is_moving = self.velocity.length() > 0.1
                
                if is_moving:
                    # Run animation (frames 51-58, 0-indexed: 50-57) - East facing, will flip for West
                    if len(self.all_frames) >= 58:
                        self.current_frames = self.all_frames[50:58]
                        self.current_animation_type = "run"
                else:
                    # Idle animation (frames 1-4, 0-indexed: 0-3)
                    if len(self.all_frames) >= 4:
                        self.current_frames = self.all_frames[0:4]
                        self.current_animation_type = "idle"
        else:
            # Fallback: use idle
            if len(self.all_frames) >= 4:
                self.current_frames = self.all_frames[0:4]
                self.current_animation_type = "idle"
        
        # Update animation timer
        if self.current_frames:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_delay:
                self.animation_timer = 0.0
                # Don't loop death animation
                if not self.alive and self.frame_index >= len(self.current_frames) - 1:
                    pass  # Stay on last frame
                else:
                    self.frame_index = (self.frame_index + 1) % len(self.current_frames)
        
    def apply_separation(self, dt: float, neighbors):
        """Apply separation force to avoid overlapping with other survivors"""
        if not neighbors:
            return
        
        push = pygame.Vector2(0, 0)
        count = 0
        
        for other in neighbors[:self.SEPARATION_MAX_NEIGHBORS]:
            if other is self or not other.alive:
                continue
            
            delta = self.pos - other.pos
            dist = delta.length()
            min_dist = self.SURVIVOR_RADIUS * 2
            
            if dist > 0 and dist < min_dist:
                if dist > 0.1:
                    push += delta.normalize() * (min_dist - dist)
                    count += 1
        
        if count > 0:
            push /= count
            push_length = push.length()
            if push_length > 0.1:
                push = push.normalize() * min(self.SEPARATION_PUSH * dt, push_length)
                self.pos += push
                self.rect.center = self.pos
    
    
    def check_threat(self, world) -> bool:
        """Check if there are enemies within safe distance"""
        if not world or not hasattr(world, 'enemy_group'):
            return False
        
        enemy_group = world.enemy_group
        for enemy in enemy_group:
            if enemy.alive:
                dist = (self.pos - enemy.pos).length()
                if dist <= self.safe_distance_to_enemy_px:
                    return True
        return False
    
    def is_night(self, world) -> bool:
        """Check if it's night time"""
        if world and hasattr(world, 'wave_manager'):
            return world.wave_manager.state == "NIGHT"
        return False
    
    def move_toward(self, target_pos: pygame.Vector2, dt: float, world=None, stop_distance: float = 8.0):
        """Move toward target position using pathfinding if available"""
        direction = target_pos - self.pos
        distance = direction.length()
        
        if distance <= stop_distance:
            self.velocity = pygame.Vector2(0, 0)
            self.current_path = []
            self.path_target = None
            return True  # Reached target
        
        # Use pathfinding if available
        if world and hasattr(world, 'pathfinding') and world.pathfinding:
            # Check if we need to recalculate path
            need_recalc = False
            # OPTIMIZED: Increased threshold from 32 to 64 pixels to reduce pathfinding calls
            if self.path_target is None or (target_pos - self.path_target).length() > 64:
                need_recalc = True
            elif self.path_recalc_timer >= self.path_recalc_interval:
                need_recalc = True
                self.path_recalc_timer = 0.0
            
            # Recalculate path if needed
            if need_recalc or not self.current_path or self.path_index >= len(self.current_path):
                # Convert positions to grid coordinates
                from world.map import Grid
                grid = world.pathfinding.grid
                start_grid = (grid.px_to_tile(int(self.pos.x)), grid.px_to_tile(int(self.pos.y)))
                target_grid = (grid.px_to_tile(int(target_pos.x)), grid.px_to_tile(int(target_pos.y)))
                
                # Find path
                path = world.pathfinding.find_path(start_grid, target_grid)
                if path and len(path) > 1:
                    self.current_path = path
                    self.path_index = 1  # Start at index 1 (skip start position)
                    self.path_target = target_pos
                else:
                    # No path found - fall back to direct movement
                    self.current_path = []
                    self.path_index = 0
                    self.path_target = None
            
            # Follow path if we have one
            if self.current_path and self.path_index < len(self.current_path):
                # Get next waypoint in path
                next_waypoint_grid = self.current_path[self.path_index]
                grid = world.pathfinding.grid
                next_waypoint_px = pygame.Vector2(
                    grid.tile_to_px(next_waypoint_grid[0]) + grid.TILE // 2,
                    grid.tile_to_px(next_waypoint_grid[1]) + grid.TILE // 2
                )
                
                # Move toward waypoint
                waypoint_dir = next_waypoint_px - self.pos
                waypoint_dist = waypoint_dir.length()
                
                if waypoint_dist <= 8.0:  # Reached waypoint
                    self.path_index += 1
                    if self.path_index >= len(self.current_path):
                        # Reached end of path - check if we're close enough to target
                        if distance <= stop_distance:
                            self.velocity = pygame.Vector2(0, 0)
                            self.current_path = []
                            self.path_target = None
                            return True
                        else:
                            # Need to recalculate
                            self.current_path = []
                            self.path_index = 0
                    else:
                        # Continue to next waypoint
                        next_waypoint_grid = self.current_path[self.path_index]
                        next_waypoint_px = pygame.Vector2(
                            grid.tile_to_px(next_waypoint_grid[0]) + grid.TILE // 2,
                            grid.tile_to_px(next_waypoint_grid[1]) + grid.TILE // 2
                        )
                        waypoint_dir = next_waypoint_px - self.pos
                        waypoint_dist = waypoint_dir.length()
                
                if waypoint_dir.length() > 0:
                    direction = waypoint_dir.normalize()
                    # Apply speed modifier
                    effective_speed = self._get_effective_speed(world)
                    self.velocity = direction * effective_speed
                else:
                    self.velocity = pygame.Vector2(0, 0)
            else:
                # No path - fall back to direct movement
                if direction.length() > 0:
                    direction = direction.normalize()
                    # Apply speed modifier
                    effective_speed = self._get_effective_speed(world)
                    self.velocity = direction * effective_speed
                else:
                    self.velocity = pygame.Vector2(0, 0)
        else:
            # No pathfinding - use direct movement
            if direction.length() > 0:
                direction = direction.normalize()
                # Apply speed modifier
                effective_speed = self._get_effective_speed(world)
                self.velocity = direction * effective_speed
            else:
                self.velocity = pygame.Vector2(0, 0)
        
        # Update pathfinding timer
        self.path_recalc_timer += dt
        
        # Check progress for stuck detection
        progress_distance = (self.pos - self.last_progress_check_pos).length()
        if progress_distance < self.STUCK_PROGRESS_THRESHOLD:
            self.time_since_progress += dt
        else:
            self.time_since_progress = 0.0
            self.last_progress_check_pos = pygame.Vector2(self.pos)
        
        return False  # Not yet reached
    
    def take_damage(self, amount: int):
        """Apply damage to survivor"""
        if not self.alive:
            return
        
        self.hp -= amount
        self.is_hurt = True
        self.hurt_timer = 0.0
        
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.frame_index = 0  # Reset to start of death animation
            self.on_death()
    
    def on_death(self):
        """Called when survivor dies"""
        # Drop carried resources (MVP: just delete them)
        if hasattr(self, 'carried'):
            self.carried = {"wood": 0, "iron": 0, "food": 0}
    
    def draw(self, surface: pygame.Surface):
        """Draw survivor with idle behavior offsets"""
        self.image.fill((0, 0, 0, 0))
        
        if not self.alive:
            # Dead survivor - draw grey circle
            pygame.draw.circle(self.image, (80, 80, 80), (12, 12), 10)
        elif self.current_frames and self.frame_index < len(self.current_frames):
            # Draw sprite frame
            frame = self.current_frames[self.frame_index]
            
            # Flip frame for East-facing sprites when moving West
            # New sprite sheet: run, axe, mining, and carry animations are East-facing
            # Need to flip when moving left (West direction)
            if len(self.all_frames) >= 78:
                # New sprite sheet format - flip East-facing animations when moving West
                if self.current_animation_type in ("run", "axe", "mining", "carry"):
                    if not self.facing_right:  # Moving left (West) - flip East-facing sprite
                        frame = pygame.transform.flip(frame, True, False)
            else:
                # Old sprite sheet format - use old flipping logic
                if self.direction == "ne":
                    if self.facing_right:
                        frame = pygame.transform.flip(frame, True, False)
                elif self.direction == "se" and not self.facing_right:
                    frame = pygame.transform.flip(frame, True, False)
            
            # Scale frame
            if self.sprite_scale != 1.0:
                scaled_width = int(frame.get_width() * self.sprite_scale)
                scaled_height = int(frame.get_height() * self.sprite_scale)
                frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
            
            # Blit frame centered on image
            frame_rect = frame.get_rect()
            frame_rect.center = (self.image.get_width() // 2, self.image.get_height() // 2)
            self.image.blit(frame, frame_rect)
        else:
            # Fallback to circles if no sprites loaded
            if self.role == "worker":
                color = (100, 150, 200)  # Blue for workers
            else:  # guard
                color = (200, 100, 100)  # Red for guards
            
            pygame.draw.circle(self.image, color, (12, 12), 10)
            pygame.draw.circle(self.image, (255, 255, 255), (12, 12), 10, 2)
            # Draw direction indicator
            if self.velocity.length() > 0:
                dir_normalized = self.velocity.normalize()
                end_pos = pygame.Vector2(12, 12) + dir_normalized * 8
                pygame.draw.line(self.image, (255, 255, 255), (12, 12), end_pos, 2)
        
        surface.blit(self.image, self.rect.topleft)
        
        # Draw carried resources indicator (if worker)
        if self.role == "worker" and hasattr(self, 'carried'):
            total_carried = sum(self.carried.values())
            if total_carried > 0:
                # Draw small backpack icon
                backpack_surface = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.rect(backpack_surface, (150, 100, 50), (4, 6, 8, 10))
                pygame.draw.rect(backpack_surface, (200, 150, 100), (4, 6, 8, 10), 1)
                backpack_rect = backpack_surface.get_rect(center=(self.pos.x, self.pos.y - 20))
                surface.blit(backpack_surface, backpack_rect)

class Worker(Survivor):
    """Worker survivor - gathers resources and hauls to HQ"""
    ROLE = "worker"
    BASE_HP = 100
    SPEED = 90.0
    CARRY_CAPACITY = 40
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, 
                 carry_capacity: Optional[int] = None, speed: Optional[float] = None, world=None):
        # Load config
        config = self._load_config()
        hp = hp if hp is not None else config.get("hp", self.BASE_HP)
        speed = speed if speed is not None else config.get("speed", self.SPEED)
        carry_capacity = carry_capacity if carry_capacity is not None else config.get("carry_capacity", self.CARRY_CAPACITY)
        
        super().__init__(pos, role="worker", hp=hp, world=world)
        self.speed = speed
        self.carry_capacity = carry_capacity
        self.carried = {"wood": 0, "iron": 0, "food": 0}
        
        # FSM state
        self.state = SurvivorState.IDLE
        self.target_node = None
        self.target_hq = None
        self.gather_timer = 0.0
        self.current_gather_tick_time = 0.0
        
        # Job queue (for gather assignments)
        self.assigned_node = None
    
    @classmethod
    def _load_config(cls) -> Dict:
        """Load worker config from survivors.json"""
        try:
            with open('data/config/survivors.json', 'r') as f:
                data = json.load(f)
                return data.get("worker", {})
        except:
            return {}
    
    def assign_gather(self, node):
        """Assign worker to gather from a node"""
        self.assigned_node = node
        self.target_node = node
        self.target_pos = node.pos
        self.state = SurvivorState.MOVE_TO_NODE
        self.last_progress_check_pos = pygame.Vector2(self.pos)
        self.time_since_progress = 0.0
    
    def get_total_carried(self) -> int:
        """Get total amount of resources carried"""
        return sum(self.carried.values())
    
    def can_carry_more(self) -> bool:
        """Check if worker can carry more resources"""
        return self.get_total_carried() < self.carry_capacity
    
    def update(self, dt: float, world=None):
        """Update worker state and behavior"""
        if not self.alive:
            return
        
        # Check for threats or night time
        is_night = self.is_night(world)
        has_threat = self.check_threat(world) if world else False
        
        # Safety check: if night or threat while outside, return to HQ for safety
        if (is_night or has_threat):
            # Find HQ (try world.hq first, then search building_group)
            hq = None
            if world and hasattr(world, 'hq') and world.hq:
                hq = world.hq
            elif world and hasattr(world, 'building_group'):
                for building in world.building_group:
                    from world.buildings.hq import HQ
                    if isinstance(building, HQ):
                        hq = building
                        break
            
            if hq:
                self.target_hq = hq
                # Calculate safe position around HQ (gather around HQ)
                # Use a position offset from HQ to cluster workers around it
                # Each worker gets a slightly different offset to avoid stacking
                # Use worker's ID or position hash to get consistent offset
                worker_id = id(self) % 1000  # Simple hash for consistency
                angle = (worker_id * 137.5) % 360  # Golden angle distribution
                distance = 40 + (worker_id % 20)  # Distance 40-60 pixels from HQ
                offset_x = math.cos(math.radians(angle)) * distance
                offset_y = math.sin(math.radians(angle)) * distance
                self.target_pos = pygame.Vector2(hq.pos.x + offset_x, hq.pos.y + offset_y)
                
                # If carrying resources, haul to HQ immediately
                if self.get_total_carried() > 0:
                    if self.state != SurvivorState.HAUL_TO_HQ and self.state != SurvivorState.DEPOSIT:
                        self.state = SurvivorState.HAUL_TO_HQ
                        # When hauling, go directly to HQ center for deposit
                        self.target_pos = hq.pos
                else:
                    # Not carrying - move to safe zone around HQ and idle
                    if self.state != SurvivorState.IDLE:
                        self.state = SurvivorState.MOVE_TO_NODE  # Reuse move state to go to safe zone
                        self.target_node = None
                        self.assigned_node = None  # Clear node assignment when fleeing
        
        # Update pathfinding timer
        self.path_recalc_timer += dt
        
        # FSM update
        if self.state == SurvivorState.IDLE:
            # Don't start gathering if it's night or there's a threat
            if is_night or has_threat:
                # Stay idle near HQ (already positioned by threat detection above)
                # If we're far from HQ, move toward it
                if world and hasattr(world, 'hq') and world.hq:
                    hq_distance = (self.pos - world.hq.pos).length()
                    if hq_distance > 80:  # If far from HQ, move closer
                        self.state = SurvivorState.MOVE_TO_NODE
                        # Calculate safe position around HQ
                        worker_id = id(self) % 1000
                        angle = (worker_id * 137.5) % 360
                        distance = 40 + (worker_id % 20)
                        offset_x = math.cos(math.radians(angle)) * distance
                        offset_y = math.sin(math.radians(angle)) * distance
                        self.target_pos = pygame.Vector2(world.hq.pos.x + offset_x, world.hq.pos.y + offset_y)
                        self.target_node = None
                return
            
            # Check if we have an assigned node (only during day and no threats)
            if self.assigned_node and not self.assigned_node.is_depleted():
                self.state = SurvivorState.MOVE_TO_NODE
                self.target_node = self.assigned_node
                self.target_pos = self.assigned_node.pos
                self.last_progress_check_pos = pygame.Vector2(self.pos)
                self.time_since_progress = 0.0
        
        elif self.state == SurvivorState.MOVE_TO_NODE:
            # Check if we're moving to a node or to a safe position (target_node will be None for safe position)
            if self.target_node:
                # Moving to a node for gathering
                if self.target_node.is_depleted():
                    # Node depleted or invalid - clear assignment
                    self.target_node = None
                    self.assigned_node = None
                    self.state = SurvivorState.IDLE
                    return
                
                # Check if reached node (within radius + small buffer)
                node_reach_distance = self.target_node.radius_px + 8
                reached = self.move_toward(self.target_node.pos, dt, world, stop_distance=node_reach_distance)
                
                if reached:
                    # Reached node - start gathering
                    self.state = SurvivorState.GATHERING
                    self.gather_timer = 0.0
                    self.current_gather_tick_time = 0.0
                    self.velocity = pygame.Vector2(0, 0)
                elif self.time_since_progress > self.STUCK_TIME_THRESHOLD:
                    # Stuck - retry or find alternative node
                    self.time_since_progress = 0.0
                    # For now, just continue trying (could implement retry logic)
            else:
                # Moving to a safe position (around HQ)
                if self.target_pos:
                    reached = self.move_toward(self.target_pos, dt, world, stop_distance=16.0)
                    if reached:
                        # Reached safe position - go idle
                        self.state = SurvivorState.IDLE
                        self.velocity = pygame.Vector2(0, 0)
                else:
                    # No target position - go idle
                    self.state = SurvivorState.IDLE
        
        elif self.state == SurvivorState.GATHERING:
            if not self.target_node or self.target_node.is_depleted():
                # Node depleted - haul what we have or go idle
                if self.get_total_carried() > 0:
                    self.state = SurvivorState.HAUL_TO_HQ
                    # Find HQ
                    if world and hasattr(world, 'building_group'):
                        for building in world.building_group:
                            from world.buildings.hq import HQ
                            if isinstance(building, HQ):
                                self.target_hq = building
                                self.target_pos = building.pos
                                break
                else:
                    self.target_node = None
                    self.assigned_node = None
                    self.state = SurvivorState.IDLE
                return
            
            # Check if survivor can gather today (injured survivors cannot gather)
            if not getattr(self, 'can_gather_today', True):
                # Injured survivor cannot gather - go idle
                self.target_node = None
                self.assigned_node = None
                self.state = SurvivorState.IDLE
                return
            
            # Gather resources in ticks
            # Apply gather speed modifier
            gather_speed_mult = 1.0
            if world and hasattr(world, 'modifiers'):
                # Support both gather_speed_mult and survivor_gather_speed_mult (alias)
                gather_speed_mult = world.modifiers.get("survivor_gather_speed_mult", 
                                                         world.modifiers.get("gather_speed_mult", 1.0))
            
            # Reduce tick time based on gather speed (faster gathering = lower tick time)
            effective_tick_sec = self.target_node.tick_sec / gather_speed_mult if gather_speed_mult > 0 else self.target_node.tick_sec
            
            self.current_gather_tick_time += dt
            if self.current_gather_tick_time >= effective_tick_sec:
                # Tick complete - gather resources
                if self.can_carry_more():
                    gathered = self.target_node.gather_tick()
                    
                    # Apply gather bonus per node (from Clear Skies event)
                    gather_bonus = 0
                    if world and hasattr(world, 'modifiers'):
                        gather_bonus = world.modifiers.get("gather_bonus_per_node", 0)
                    
                    if gathered > 0:
                        # Add bonus to gathered amount
                        total_gathered = gathered + gather_bonus
                        # Add to carried resources
                        resource = self.target_node.resource
                        space_available = self.carry_capacity - self.get_total_carried()
                        amount_to_add = min(total_gathered, space_available)
                        self.carried[resource] += amount_to_add
                    self.current_gather_tick_time = 0.0
                else:
                    # At capacity - start hauling
                    self.state = SurvivorState.HAUL_TO_HQ
                    # Find HQ (try world.hq first, then search building_group)
                    if world and hasattr(world, 'hq') and world.hq:
                        self.target_hq = world.hq
                        self.target_pos = world.hq.pos
                    elif world and hasattr(world, 'building_group'):
                        for building in world.building_group:
                            from world.buildings.hq import HQ
                            if isinstance(building, HQ):
                                self.target_hq = building
                                self.target_pos = building.pos
                                break
            
            # Check if node depleted
            if self.target_node.is_depleted():
                if self.get_total_carried() > 0:
                    self.state = SurvivorState.HAUL_TO_HQ
                    # Find HQ (try world.hq first, then search building_group)
                    if world and hasattr(world, 'hq') and world.hq:
                        self.target_hq = world.hq
                        self.target_pos = world.hq.pos
                    elif world and hasattr(world, 'building_group'):
                        for building in world.building_group:
                            from world.buildings.hq import HQ
                            if isinstance(building, HQ):
                                self.target_hq = building
                                self.target_pos = building.pos
                                break
                else:
                    self.target_node = None
                    self.assigned_node = None
                    self.state = SurvivorState.IDLE
        
        elif self.state == SurvivorState.HAUL_TO_HQ:
            # Find HQ if not already found (try world.hq first, then search building_group)
            if not self.target_hq:
                if world and hasattr(world, 'hq') and world.hq:
                    self.target_hq = world.hq
                    self.target_pos = world.hq.pos
                elif world and hasattr(world, 'building_group'):
                    for building in world.building_group:
                        from world.buildings.hq import HQ
                        if isinstance(building, HQ):
                            self.target_hq = building
                            self.target_pos = building.pos
                            break
            
            if not self.target_hq:
                # No HQ found - go idle
                self.state = SurvivorState.IDLE
                return
            
            # Move toward HQ (apply haul speed modifier)
            # Check if survivor is adjacent to HQ footprint (not just center)
            from world.building import TILE
            from world.buildings.hq import HQ
            
            # Get HQ footprint
            hq_footprint = self.target_hq.FOOTPRINT  # (width, height) in tiles
            hq_grid_x = self.target_hq.grid_x
            hq_grid_y = self.target_hq.grid_y
            
            # Get survivor grid position
            survivor_grid_x = int(self.pos.x // TILE)
            survivor_grid_y = int(self.pos.y // TILE)
            
            # Check if survivor is adjacent to any tile in HQ footprint
            # Adjacent means 1 tile away horizontally or vertically (not diagonally)
            is_adjacent = False
            for fx in range(hq_footprint[0]):
                for fy in range(hq_footprint[1]):
                    hq_tile_x = hq_grid_x + fx
                    hq_tile_y = hq_grid_y + fy
                    
                    # Check if survivor is adjacent (horizontally or vertically)
                    dx = abs(survivor_grid_x - hq_tile_x)
                    dy = abs(survivor_grid_y - hq_tile_y)
                    if (dx == 1 and dy == 0) or (dx == 0 and dy == 1):
                        is_adjacent = True
                        break
                if is_adjacent:
                    break
            
            # Temporarily apply haul speed modifier
            if world and hasattr(world, 'modifiers'):
                haul_speed_mult = world.modifiers.get("survivor_haul_speed_mult", 
                                                      world.modifiers.get("haul_speed_mult", 1.0))
                old_base_speed = self.base_speed
                self.base_speed = self.SPEED * haul_speed_mult
                # Move toward nearest adjacent tile if not already adjacent
                if not is_adjacent:
                    # Find nearest adjacent tile to move toward
                    nearest_adjacent = None
                    min_dist = float('inf')
                    for fx in range(hq_footprint[0]):
                        for fy in range(hq_footprint[1]):
                            hq_tile_x = hq_grid_x + fx
                            hq_tile_y = hq_grid_y + fy
                            
                            # Check adjacent positions (N, S, E, W)
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
                                    # This is a valid adjacent tile
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
                        # Fallback: move toward HQ center
                        reached = self.move_toward(self.target_hq.pos, dt, world, stop_distance=16.0)
                else:
                    reached = True  # Already adjacent
                self.base_speed = old_base_speed  # Restore
            else:
                # Same logic without speed modifier
                if not is_adjacent:
                    # Find nearest adjacent tile to move toward
                    nearest_adjacent = None
                    min_dist = float('inf')
                    for fx in range(hq_footprint[0]):
                        for fy in range(hq_footprint[1]):
                            hq_tile_x = hq_grid_x + fx
                            hq_tile_y = hq_grid_y + fy
                            
                            # Check adjacent positions (N, S, E, W)
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
                                    # This is a valid adjacent tile
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
                        # Fallback: move toward HQ center
                        reached = self.move_toward(self.target_hq.pos, dt, world, stop_distance=16.0)
                else:
                    reached = True  # Already adjacent
            
            if reached and is_adjacent:
                # Reached HQ - deposit
                self.state = SurvivorState.DEPOSIT
                self.velocity = pygame.Vector2(0, 0)
            elif self.time_since_progress > self.STUCK_TIME_THRESHOLD:
                # Stuck - recompute path
                self.time_since_progress = 0.0
                self.last_progress_check_pos = pygame.Vector2(self.pos)
        
        elif self.state == SurvivorState.DEPOSIT:
            # Deposit resources at HQ
            if world and hasattr(world, 'deposit'):
                # Deposit each resource type
                if self.carried["wood"] > 0:
                    world.deposit("wood", self.carried["wood"])
                if self.carried["iron"] > 0:
                    world.deposit("iron", self.carried["iron"])
                if self.carried["food"] > 0:
                    world.deposit("food", self.carried["food"])
                
                # Clear carried resources
                self.carried = {"wood": 0, "iron": 0, "food": 0}
            elif world and hasattr(world, 'resources'):
                # Fallback: direct resource access
                world.resources.wood += self.carried["wood"]
                world.resources.iron += self.carried["iron"]
                world.resources.food += self.carried["food"]
                
                # Clear carried resources
                self.carried = {"wood": 0, "iron": 0, "food": 0}
            
            # Check if node still exists and not depleted
            # But don't return to node if it's night or there's a threat
            if (not is_night and not has_threat) and self.target_node and not self.target_node.is_depleted():
                # Return to node
                self.state = SurvivorState.MOVE_TO_NODE
                self.target_pos = self.target_node.pos
                self.last_progress_check_pos = pygame.Vector2(self.pos)
                self.time_since_progress = 0.0
            else:
                # Node depleted, invalid, or it's night/threat - go idle (will be positioned near HQ)
                self.target_node = None
                self.assigned_node = None
                self.state = SurvivorState.IDLE
                # If it's night or threat, ensure we're heading to HQ safe zone
                if is_night or has_threat:
                    if world and hasattr(world, 'hq') and world.hq:
                        worker_id = id(self) % 1000
                        angle = (worker_id * 137.5) % 360
                        distance = 40 + (worker_id % 20)
                        offset_x = math.cos(math.radians(angle)) * distance
                        offset_y = math.sin(math.radians(angle)) * distance
                        self.target_pos = pygame.Vector2(world.hq.pos.x + offset_x, world.hq.pos.y + offset_y)
                        self.state = SurvivorState.MOVE_TO_NODE
                        self.target_node = None
        
        # Update animation
        self.update_animation(dt)
        
        # Handle wall collisions using tile-based collision map (BEFORE movement)
        # Survivors ignore gates (can pass through them)
        def tile_blocks(tile_x: int, tile_y: int) -> bool:
            if not world or not hasattr(world, 'collision_map') or not world.collision_map:
                return False
            if not world.collision_map.is_solid(tile_x, tile_y):
                return False
            if world and hasattr(world, 'building_group'):
                for building in world.building_group:
                    if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                        building.grid_x == tile_x and building.grid_y == tile_y):
                        building_type = getattr(building, 'TYPE_ID', '').lower()
                        if building_type == 'gate':
                            return False
            return True
        
        if world and hasattr(world, 'collision_map') and world.collision_map and hasattr(world, 'tile_size'):
            tile_x = int(self.pos.x // world.tile_size)
            tile_y = int(self.pos.y // world.tile_size)
            if tile_blocks(tile_x, tile_y):
                self.pos -= self.velocity * dt * 0.5
            
            next_pos = self.pos + self.velocity * dt
            next_tile_x = int(next_pos.x // world.tile_size)
            next_tile_y = int(next_pos.y // world.tile_size)
            
            if tile_blocks(next_tile_x, next_tile_y):
                moved = False
                if abs(self.velocity.x) > 0.1:
                    tentative_x = self.pos.x + self.velocity.x * dt
                    tile_x_only = int(tentative_x // world.tile_size)
                    if not tile_blocks(tile_x_only, tile_y):
                        self.pos.x = tentative_x
                        moved = True
                if not moved and abs(self.velocity.y) > 0.1:
                    tentative_y = self.pos.y + self.velocity.y * dt
                    tile_y_only = int(tentative_y // world.tile_size)
                    if not tile_blocks(tile_x, tile_y_only):
                        self.pos.y = tentative_y
                        moved = True
                if not moved:
                    self.pos -= self.velocity * dt * 0.5
            else:
                self.pos = next_pos
        else:
            # Fallback: normal movement if no collision map
            self.pos += self.velocity * dt
        
        self.rect.center = self.pos
    
    def draw(self, surface: pygame.Surface):
        """Draw worker with carried resources indicator"""
        super().draw(surface)
        
        # Draw carried resources text (optional, for debugging)
        # if self.get_total_carried() > 0:
        #     font = pygame.font.Font(None, 16)
        #     text = font.render(str(self.get_total_carried()), True, (255, 255, 255))
        #     text_rect = text.get_rect(center=(self.pos.x, self.pos.y - 30))
        #     surface.blit(text, text_rect)

class Guard(Survivor):
    """Guard survivor - defends the base"""
    ROLE = "guard"
    BASE_HP = 120
    SPEED = 85.0
    ATTACK_RANGE = 160.0
    RANGED_DAMAGE = 8
    ATTACK_COOLDOWN = 0.8
    
    def __init__(self, pos: Tuple[float, float], hp: Optional[int] = None, 
                 speed: Optional[float] = None, attack_range: Optional[float] = None,
                 ranged_dmg: Optional[int] = None, cooldown: Optional[float] = None, world=None):
        # Load config
        config = self._load_config()
        hp = hp if hp is not None else config.get("hp", self.BASE_HP)
        speed = speed if speed is not None else config.get("speed", self.SPEED)
        attack_range = attack_range if attack_range is not None else config.get("range", self.ATTACK_RANGE)
        ranged_dmg = ranged_dmg if ranged_dmg is not None else config.get("ranged_dmg", self.RANGED_DAMAGE)
        cooldown = cooldown if cooldown is not None else config.get("cooldown", self.ATTACK_COOLDOWN)
        
        super().__init__(pos, role="guard", hp=hp, world=world)
        self.speed = speed
        self.attack_range = attack_range
        self.ranged_damage = ranged_dmg
        self.attack_cooldown = cooldown
        
        # Guard-specific
        self.post_position = pygame.Vector2(pos)  # Defensive post
        self.attack_timer = 0.0
        self.target_enemy = None
        self.projectile_group = None
    
    @classmethod
    def _load_config(cls) -> Dict:
        """Load guard config from survivors.json"""
        try:
            with open('data/config/survivors.json', 'r') as f:
                data = json.load(f)
                return data.get("guard", {})
        except:
            return {}
    
    def update(self, dt: float, world=None):
        """Update guard state and behavior"""
        if not self.alive:
            return
        
        # Set projectile group
        if world and hasattr(world, 'projectile_group'):
            self.projectile_group = world.projectile_group
        
        # Update attack timer
        self.attack_timer += dt
        
        # Check if night (active) or day (idle at post)
        is_night = self.is_night(world)
        
        if is_night:
            # Night: active defense
            # Find nearest enemy
            self.target_enemy = None
            nearest_distance = float('inf')
            
            if world and hasattr(world, 'enemy_group'):
                for enemy in world.enemy_group:
                    if enemy.alive:
                        distance = (self.pos - enemy.pos).length()
                        if distance <= self.attack_range and distance < nearest_distance:
                            nearest_distance = distance
                            self.target_enemy = enemy
            
            if self.target_enemy:
                # Attack enemy
                if self.attack_timer >= self.attack_cooldown:
                    self.attack_enemy(self.target_enemy, world)
                    self.attack_timer = 0.0
            else:
                # No enemy in range - return to post
                self.move_toward(self.post_position, dt, world, stop_distance=16.0)
        else:
            # Day: idle at post
            self.move_toward(self.post_position, dt, world, stop_distance=16.0)
        
        # Update animation
        self.update_animation(dt)
        
        # Move guard
        self.pos += self.velocity * dt
        self.rect.center = self.pos
    
    def attack_enemy(self, enemy, world):
        """Attack enemy with ranged attack"""
        if not enemy or not enemy.alive:
            return
        
        # Spawn projectile (reuse Projectile class)
        if self.projectile_group:
            from world.projectile import Projectile
            projectile = Projectile(
                start_pos=(self.pos.x, self.pos.y),
                target_pos=(enemy.pos.x, enemy.pos.y),
                speed=400.0,
                damage=self.ranged_damage,
                target_type="enemy"
            )
            self.projectile_group.add(projectile)
            
            # Play sound if available
            if world and hasattr(world, 'sound_system'):
                world.sound_system.play("turret_fire")
    
    def draw(self, surface: pygame.Surface):
        """Draw guard"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw guard (red circle)
        if self.alive:
            pygame.draw.circle(self.image, (200, 100, 100), (12, 12), 10)
            pygame.draw.circle(self.image, (255, 255, 255), (12, 12), 10, 2)
            # Draw weapon indicator
            if self.target_enemy:
                dir_to_enemy = (self.target_enemy.pos - self.pos)
                if dir_to_enemy.length() > 0:
                    dir_normalized = dir_to_enemy.normalize()
                    end_pos = pygame.Vector2(12, 12) + dir_normalized * 10
                    pygame.draw.line(self.image, (255, 200, 100), (12, 12), end_pos, 2)
        else:
            pygame.draw.circle(self.image, (80, 80, 80), (12, 12), 10)
        
        surface.blit(self.image, self.rect)
        
        # Draw attack range (optional, for debugging)
        # if self.alive and self.target_enemy:
        #     pygame.draw.circle(surface, (255, 0, 0, 50), (int(self.pos.x), int(self.pos.y)), 
        #                        int(self.attack_range), 1)

