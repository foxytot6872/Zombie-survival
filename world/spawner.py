"""
Enemy spawner system for managing hordes and waves.
"""
import pygame
import random
from typing import List, Type, Dict, Optional
from world.enemy import Enemy
import constants as c

class Spawner:
    """Manages enemy spawning"""
    
    def __init__(self, enemy_factory: Optional[Dict[str, Type[Enemy]]] = None, spawn_interval: float = 2.0):
        """
        Initialize spawner.
        Args:
            enemy_factory: Dictionary mapping enemy type IDs to enemy classes
            spawn_interval: Time between spawns in seconds
        """
        self.enemy_factory = enemy_factory or {}
        self.spawn_interval = spawn_interval
        self.spawn_timer = 0.0
        self.spawn_count = 0
        self.max_spawns = -1  # -1 for infinite
        self.active = True
        self.done = False
        
        # Wave-based spawning
        self.wave_recipe: Dict[str, int] = {}  # {enemy_type: count}
        self.spawned_counts: Dict[str, int] = {}  # Track how many of each type spawned
        self.total_to_spawn = 0
        self.batch_size = 2  # Enemies per spawn batch
        
        # Spawn area (all edges of screen)
        self.spawn_y = 0
        self.spawn_x_min = 0
        self.spawn_x_max = c.SCREEN_WIDTH
        self.spawn_y_min = 0
        self.spawn_y_max = c.SCREEN_HEIGHT
    
    def begin(self, recipe: Dict[str, int], spawn_config: Dict):
        """
        Begin a wave with a recipe.
        Args:
            recipe: Dictionary mapping enemy type IDs to counts
            spawn_config: Spawn configuration (interval_sec, batch_size)
        """
        self.wave_recipe = recipe.copy()
        self.spawned_counts = {k: 0 for k in recipe.keys()}
        self.total_to_spawn = sum(recipe.values())
        self.spawn_count = 0
        self.done = False
        self.active = True
        self.spawn_timer = 0.0
        
        # Update spawn config
        if "interval_sec" in spawn_config:
            self.spawn_interval = spawn_config["interval_sec"]
        if "batch_size" in spawn_config:
            self.batch_size = spawn_config["batch_size"]
    
    def update(self, dt: float, enemy_group: pygame.sprite.Group, world=None):
        """Update spawner and spawn enemies if needed"""
        if not self.active or self.done:
            return
        
        # Check if wave is complete
        if self.total_to_spawn > 0 and self.spawn_count >= self.total_to_spawn:
            self.done = True
            self.active = False
            return
        
        # Apply zombie spawn rate modifier from day events
        effective_interval = self.spawn_interval
        if world and hasattr(world, 'modifiers'):
            spawn_mult = world.modifiers.get("zombie_spawn_mult", 1.0)
            effective_interval = self.spawn_interval / spawn_mult  # Lower interval = faster spawning
        
        # Update spawn timer
        self.spawn_timer += dt
        
        # Spawn batch if interval elapsed
        if self.spawn_timer >= effective_interval:
            self._spawn_batch(enemy_group, world)
            self.spawn_timer = 0.0
    
    def _spawn_batch(self, enemy_group: pygame.sprite.Group, world=None):
        """Spawn a batch of enemies from random edges"""
        batch_count = 0
        
        # Spawn enemies from recipe (iterate through all types to ensure balanced spawning)
        enemy_types = list(self.wave_recipe.keys())
        random.shuffle(enemy_types)  # Randomize order for variety
        
        for enemy_type in enemy_types:
            if batch_count >= self.batch_size:
                break
            
            total_count = self.wave_recipe[enemy_type]
            
            # Check if we need more of this type
            if self.spawned_counts[enemy_type] < total_count:
                # Get enemy class from factory
                if enemy_type in self.enemy_factory:
                    enemy_class = self.enemy_factory[enemy_type]
                    
                    # Spawn enemy from weighted random edge (based on night bias + turret noise)
                    spawn_pos = self._get_random_edge_spawn_position(batch_count, world)
                    
                    enemy = enemy_class(spawn_pos)
                    
                    # Apply day event modifiers to enemy
                    if world and hasattr(world, 'modifiers'):
                        # Apply speed modifier
                        speed_mult = world.modifiers.get("zombie_speed_mult", 1.0)
                        enemy.speed *= speed_mult
                        
                        # Apply HP modifier
                        hp_mult = world.modifiers.get("zombie_hp_mult", 1.0)
                        enemy.max_hp = int(enemy.max_hp * hp_mult)
                        enemy.hp = enemy.max_hp  # Set current HP to max
                    
                    enemy_group.add(enemy)
                    
                    self.spawned_counts[enemy_type] += 1
                    self.spawn_count += 1
                    batch_count += 1
    
    def _get_random_edge_spawn_position(self, offset: int = 0, world=None):
        """
        Get a random spawn position on one of the four screen edges.
        Uses night-based spawn bias and turret noise system.
        
        Args:
            offset: Offset for staggering multiple spawns
            world: World object (for noise calculation and night number)
        Returns:
            Tuple (x, y) spawn position
        """
        # Get base spawn side from night bias
        edge = "bottom"  # Default fallback
        if world and hasattr(world, 'wave_manager') and world.wave_manager:
            night = getattr(world.wave_manager, 'night', 1)
            edge = world.wave_manager.get_spawn_side_for_night(night)
        
        # Apply turret noise influence if world is available
        if world:
            noise_weights = self._calculate_spawn_weights_with_noise(edge, world)
            if noise_weights:
                # Use weighted random with noise-influenced weights
                total_weight = sum(noise_weights.values())
                if total_weight > 0:
                    rand = random.uniform(0, total_weight)
                    cumulative = 0.0
                    for side, weight in noise_weights.items():
                        cumulative += weight
                        if rand <= cumulative:
                            edge = side
                            break
        margin = 50  # Margin from screen edge
        
        if edge == "top":
            # Spawn from top edge
            spawn_x = random.uniform(self.spawn_x_min + margin, self.spawn_x_max - margin)
            spawn_y = self.spawn_y_min - offset * 20  # Stagger vertically above screen
        elif edge == "bottom":
            # Spawn from bottom edge
            spawn_x = random.uniform(self.spawn_x_min + margin, self.spawn_x_max - margin)
            spawn_y = self.spawn_y_max + offset * 20  # Stagger vertically below screen
        elif edge == "left":
            # Spawn from left edge
            spawn_x = self.spawn_x_min - offset * 20  # Stagger horizontally left of screen
            spawn_y = random.uniform(self.spawn_y_min + margin, self.spawn_y_max - margin)
        else:  # right
            # Spawn from right edge
            spawn_x = self.spawn_x_max + offset * 20  # Stagger horizontally right of screen
            spawn_y = random.uniform(self.spawn_y_min + margin, self.spawn_y_max - margin)
        
        return (spawn_x, spawn_y)
    
    def _calculate_spawn_weights_with_noise(self, base_edge: str, world) -> Dict[str, float]:
        """
        Calculate spawn weights combining night bias and turret noise.
        
        Final weight = bias_weight + (quadrant_noise * 0.5)
        Never let a weight hit 0.
        
        Args:
            base_edge: Base spawn side from night bias
            world: World object for noise calculation
            
        Returns:
            Dictionary mapping sides to weights
        """
        # Get quadrant noise from world
        quadrant_noise = {}
        if hasattr(world, 'get_quadrant_noise'):
            quadrant_noise = world.get_quadrant_noise()
        
        # Base weights from night bias (assume equal weight if not specified)
        base_weights = {
            "top": 0.0,
            "bottom": 0.0,
            "left": 0.0,
            "right": 0.0
        }
        # Give base edge a weight of 1.0
        base_weights[base_edge] = 1.0
        
        # Combine with noise (noise adds 0.5 * noise_value to weight)
        noise_multiplier = 0.5
        final_weights = {}
        for side in ["top", "bottom", "left", "right"]:
            noise_value = quadrant_noise.get(side, 0.0)
            weight = base_weights.get(side, 0.0) + (noise_value * noise_multiplier)
            # Never let weight hit 0
            final_weights[side] = max(0.1, weight)
        
        return final_weights
    
    def spawn_enemy(self, enemy_group: pygame.sprite.Group, enemy_class: Optional[Type[Enemy]] = None):
        """Spawn a single enemy (legacy method) - spawns from random edge"""
        if enemy_class is None:
            # Use first enemy class from factory if available
            if self.enemy_factory:
                enemy_class = list(self.enemy_factory.values())[0]
            else:
                return
        
        # Spawn from weighted random edge (based on night bias + turret noise)
        spawn_pos = self._get_random_edge_spawn_position(0, world=None)
        
        # Create enemy
        enemy = enemy_class(spawn_pos)
        enemy_group.add(enemy)
        self.spawn_count += 1
    
    def spawn_horde(self, enemy_group: pygame.sprite.Group, count: int, spread: float = 100.0, enemy_class: Optional[Type[Enemy]] = None):
        """Spawn a horde of enemies (legacy method) - spawns from random edges"""
        if enemy_class is None:
            # Use first enemy class from factory if available
            if self.enemy_factory:
                enemy_class = list(self.enemy_factory.values())[0]
            else:
                return
        
        for i in range(count):
            # Spawn from weighted random edge (based on night bias + turret noise)
            spawn_pos = self._get_random_edge_spawn_position(i, world=None)
            enemy = enemy_class(spawn_pos)
            enemy_group.add(enemy)
            self.spawn_count += 1
    
    def set_active(self, active: bool):
        """Enable/disable spawner"""
        self.active = active
    
    def set_spawn_interval(self, interval: float):
        """Change spawn interval"""
        self.spawn_interval = interval
    
    def reset(self):
        """Reset spawner"""
        self.spawn_timer = 0.0
        self.spawn_count = 0
        self.active = True
        self.done = False
        self.wave_recipe = {}
        self.spawned_counts = {}
        self.total_to_spawn = 0

