"""
Survivor classes: Workers and Guards.
"""
import pygame
import json
import math
import random
from typing import Tuple, Optional, Dict
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
    
    def __init__(self, pos: Tuple[float, float], role: str = "worker", hp: Optional[int] = None):
        super().__init__()
        self.role = role
        self.max_hp = hp if hp is not None else self.BASE_HP
        self.hp = self.max_hp
        self.speed = self.SPEED
        
        # Position
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)
        self.target_pos = None
        
        # Rendering
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
        # State
        self.alive = True
        self.state = SurvivorState.IDLE
        
        # Stuck detection
        self.last_progress_check_pos = pygame.Vector2(self.pos)
        self.time_since_progress = 0.0
        self.path_recalc_timer = 0.0
        self.path_recalc_interval = 0.5  # Recalculate path every 0.5 seconds
        
        # Safe distance to enemies
        self.safe_distance_to_enemy_px = 160.0
        self.flee_on_threat = True
    
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
        """Move toward target position"""
        direction = target_pos - self.pos
        distance = direction.length()
        
        if distance <= stop_distance:
            self.velocity = pygame.Vector2(0, 0)
            return True  # Reached target
        
        # Normalize direction and set velocity
        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * self.speed
        else:
            self.velocity = pygame.Vector2(0, 0)
        
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
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.on_death()
    
    def on_death(self):
        """Called when survivor dies"""
        # Drop carried resources (MVP: just delete them)
        if hasattr(self, 'carried'):
            self.carried = {"wood": 0, "iron": 0, "food": 0}
    
    def draw(self, surface: pygame.Surface):
        """Draw survivor"""
        self.image.fill((0, 0, 0, 0))
        
        # Draw based on role
        if self.role == "worker":
            color = (100, 150, 200)  # Blue for workers
        else:  # guard
            color = (200, 100, 100)  # Red for guards
        
        # Draw body
        if self.alive:
            pygame.draw.circle(self.image, color, (12, 12), 10)
            pygame.draw.circle(self.image, (255, 255, 255), (12, 12), 10, 2)
            # Draw direction indicator
            if self.velocity.length() > 0:
                dir_normalized = self.velocity.normalize()
                end_pos = pygame.Vector2(12, 12) + dir_normalized * 8
                pygame.draw.line(self.image, (255, 255, 255), (12, 12), end_pos, 2)
        else:
            # Dead survivor (grey)
            pygame.draw.circle(self.image, (80, 80, 80), (12, 12), 10)
        
        surface.blit(self.image, self.rect)
        
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
                 carry_capacity: Optional[int] = None, speed: Optional[float] = None):
        # Load config
        config = self._load_config()
        hp = hp if hp is not None else config.get("hp", self.BASE_HP)
        speed = speed if speed is not None else config.get("speed", self.SPEED)
        carry_capacity = carry_capacity if carry_capacity is not None else config.get("carry_capacity", self.CARRY_CAPACITY)
        
        super().__init__(pos, role="worker", hp=hp)
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
            
            # Gather resources in ticks
            self.current_gather_tick_time += dt
            if self.current_gather_tick_time >= self.target_node.tick_sec:
                # Tick complete - gather resources
                if self.can_carry_more():
                    gathered = self.target_node.gather_tick()
                    if gathered > 0:
                        # Add to carried resources
                        resource = self.target_node.resource
                        space_available = self.carry_capacity - self.get_total_carried()
                        amount_to_add = min(gathered, space_available)
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
            
            # Move toward HQ
            hq_reach_distance = 32.0  # Within 1 tile of HQ center
            reached = self.move_toward(self.target_hq.pos, dt, world, stop_distance=hq_reach_distance)
            
            if reached:
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
        
        # Move worker
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
                 ranged_dmg: Optional[int] = None, cooldown: Optional[float] = None):
        # Load config
        config = self._load_config()
        hp = hp if hp is not None else config.get("hp", self.BASE_HP)
        speed = speed if speed is not None else config.get("speed", self.SPEED)
        attack_range = attack_range if attack_range is not None else config.get("range", self.ATTACK_RANGE)
        ranged_dmg = ranged_dmg if ranged_dmg is not None else config.get("ranged_dmg", self.RANGED_DAMAGE)
        cooldown = cooldown if cooldown is not None else config.get("cooldown", self.ATTACK_COOLDOWN)
        
        super().__init__(pos, role="guard", hp=hp)
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

