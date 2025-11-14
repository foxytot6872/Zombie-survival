"""
Base Enemy class with common attributes and behaviors.
"""
from __future__ import annotations
import pygame
from typing import Tuple, Optional

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
        
        # Projectile group for ranged enemies (set by world)
        self.projectile_group = None
    
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
            if self.target_building is None and self.target_survivor is None:
                self.choose_target(world)
        
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
        
        # Move enemy
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
    
    def choose_target(self, world):
        """Choose target (survivor or building) using distance + priority scoring"""
        # First, check for survivors (zombies ALWAYS prioritize survivors over buildings)
        survivor_group = None
        if world and hasattr(world, 'survivor_group'):
            survivor_group = world.survivor_group
        
        best_survivor = None
        best_survivor_score = float('inf')
        
        if survivor_group:
            for survivor in survivor_group:
                if not survivor.alive:
                    continue
                
                distance = (self.pos - survivor.pos).length()
                # Always consider all survivors (no distance limit)
                # Score survivors (lower is better) - prefer closer survivors
                score = distance
                if score < best_survivor_score:
                    best_survivor_score = score
                    best_survivor = survivor
        
        # If we found any survivor, target it (survivors are always priority)
        if best_survivor:
            # Release building slot if we had one
            if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                self.target_building.release_attack_slot()
            self.target_building = None
            self.target_survivor = best_survivor
            self.last_progress_check_pos = pygame.Vector2(self.pos)
            self.time_since_progress = 0.0
            return
        
        # No survivors found, target buildings instead
        building_group = None
        if world and hasattr(world, 'building_group'):
            building_group = world.building_group
        
        if not building_group:
            self.target_building = None
            self.target_survivor = None
            return
        
        # Get all active buildings
        from world.building import BuildState
        candidates = []
        for building in building_group:
            if hasattr(building, 'state'):
                if building.state == BuildState.ACTIVE:
                    candidates.append(building)
            else:
                # Assume valid if no state attribute
                candidates.append(building)
        
        if not candidates:
            self.target_building = None
            self.target_survivor = None
            return
        
        # Score each candidate building
        best_building = None
        best_score = float('inf')
        
        # Check pathfinding cache (refresh every ~1 second)
        # Use a simple frame counter approach instead of time
        # Cache will be cleared periodically by checking cache size
        if len(self.pathfinding_cache) > 100:  # Clear cache if too large
            self.pathfinding_cache.clear()
        
        pathfinding = None
        if world and hasattr(world, 'pathfinding'):
            pathfinding = world.pathfinding
        
        for building in candidates:
            # Distance weight
            distance = (self.pos - building.pos).length()
            distance_weight = distance
            
            # Slot weight (prefer buildings with free slots)
            if building.attacker_count < building.get_attacker_capacity():
                slot_weight = self.SLOT_PENALTY_FREE
            else:
                slot_weight = self.SLOT_PENALTY_FULL
            
            # Pathfinding penalty (if pathfinding available)
            pathfinding_penalty = 0.0
            if pathfinding:
                # Check cache first
                cache_key = (int(self.pos.x // 32), int(self.pos.y // 32), 
                            building.grid_x, building.grid_y)
                if cache_key in self.pathfinding_cache:
                    has_path = self.pathfinding_cache[cache_key]
                else:
                    # Check if path exists
                    start_grid = (int(self.pos.x // 32), int(self.pos.y // 32))
                    goal_grid = (building.grid_x, building.grid_y)
                    path = pathfinding.find_path(start_grid, goal_grid)
                    has_path = path is not None
                    self.pathfinding_cache[cache_key] = has_path
                
                if not has_path:
                    pathfinding_penalty = self.PATHFINDING_PENALTY
            
            # Total score (lower is better)
            score = distance_weight + slot_weight + pathfinding_penalty
            
            if score < best_score:
                best_score = score
                best_building = building
        
        # Try to claim a slot on the best building
        if best_building:
            if best_building.request_attack_slot():
                # Release old target's slot if any
                if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                    self.target_building.release_attack_slot()
                self.target_building = best_building
                self.target_survivor = None  # Clear survivor target
                # Reset stuck detection when retargeting
                self.last_progress_check_pos = pygame.Vector2(self.pos)
                self.time_since_progress = 0.0
            else:
                # Fallback: target closest building regardless of slots
                closest = min(candidates, key=lambda b: (b.pos - self.pos).length())
                if closest != self.target_building:
                    if self.target_building and hasattr(self.target_building, 'release_attack_slot'):
                        self.target_building.release_attack_slot()
                    # Try to claim slot on closest
                    if closest.request_attack_slot():
                        self.target_building = closest
                        self.target_survivor = None  # Clear survivor target
                        self.last_progress_check_pos = pygame.Vector2(self.pos)
                        self.time_since_progress = 0.0
                    else:
                        # No slot available, but target anyway
                        self.target_building = closest
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
        """Apply damage to enemy"""
        if not self.alive:
            return
        
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
        
        # Update rect position
        self.rect.center = self.pos
        
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

