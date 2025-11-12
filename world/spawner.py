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
        
        # Spawn area (top of screen)
        self.spawn_y = 0
        self.spawn_x_min = 0
        self.spawn_x_max = c.SCREEN_WIDTH
    
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
    
    def update(self, dt: float, enemy_group: pygame.sprite.Group):
        """Update spawner and spawn enemies if needed"""
        if not self.active or self.done:
            return
        
        # Check if wave is complete
        if self.total_to_spawn > 0 and self.spawn_count >= self.total_to_spawn:
            self.done = True
            self.active = False
            return
        
        # Update spawn timer
        self.spawn_timer += dt
        
        # Spawn batch if interval elapsed
        if self.spawn_timer >= self.spawn_interval:
            self._spawn_batch(enemy_group)
            self.spawn_timer = 0.0
    
    def _spawn_batch(self, enemy_group: pygame.sprite.Group):
        """Spawn a batch of enemies"""
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
                    
                    # Spawn enemy
                    spawn_x = random.uniform(self.spawn_x_min + 50, self.spawn_x_max - 50)
                    spawn_pos = (spawn_x, self.spawn_y - batch_count * 20)  # Stagger vertically
                    
                    enemy = enemy_class(spawn_pos)
                    enemy_group.add(enemy)
                    
                    self.spawned_counts[enemy_type] += 1
                    self.spawn_count += 1
                    batch_count += 1
    
    def spawn_enemy(self, enemy_group: pygame.sprite.Group, enemy_class: Optional[Type[Enemy]] = None):
        """Spawn a single enemy (legacy method)"""
        if enemy_class is None:
            # Use first enemy class from factory if available
            if self.enemy_factory:
                enemy_class = list(self.enemy_factory.values())[0]
            else:
                return
        
        # Random x position at top of screen
        spawn_x = random.uniform(self.spawn_x_min + 50, self.spawn_x_max - 50)
        spawn_pos = (spawn_x, self.spawn_y)
        
        # Create enemy
        enemy = enemy_class(spawn_pos)
        enemy_group.add(enemy)
        self.spawn_count += 1
    
    def spawn_horde(self, enemy_group: pygame.sprite.Group, count: int, spread: float = 100.0, enemy_class: Optional[Type[Enemy]] = None):
        """Spawn a horde of enemies (legacy method)"""
        if enemy_class is None:
            # Use first enemy class from factory if available
            if self.enemy_factory:
                enemy_class = list(self.enemy_factory.values())[0]
            else:
                return
        
        for i in range(count):
            # Spread enemies across top of screen
            spawn_x = random.uniform(
                self.spawn_x_min + spread,
                self.spawn_x_max - spread
            )
            spawn_pos = (spawn_x, self.spawn_y - i * 20)  # Stagger vertically
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

