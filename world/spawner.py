"""
Enemy spawner system for managing hordes and waves.
"""
import pygame
import random
from typing import List, Type, Dict, Optional, Tuple
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
        
        # Staggered spawning: spawn 1 enemy per frame instead of batches
        self.to_spawn_queue: List[str] = []  # Flat list of enemy types to spawn (shuffled)
        
        # Spawn area (all edges of screen) - must be initialized BEFORE cache generation
        self.spawn_y = 0
        self.spawn_x_min = 0
        self.spawn_x_max = c.SCREEN_WIDTH
        self.spawn_y_min = 0
        self.spawn_y_max = c.SCREEN_HEIGHT
        
        # Precomputed spawn positions cache (200 positions)
        self.spawn_cache: List[Tuple[float, float]] = []
        self.spawn_cache_size = 200
        self._generate_spawn_cache()
    
    def begin(self, recipe: Dict[str, int], spawn_config: Dict):
        """
        Begin a wave with a recipe.
        Args:
            recipe: Dictionary mapping enemy type IDs to counts
            spawn_config: Spawn configuration (interval_sec)
        """
        self.wave_recipe = recipe.copy()
        self.spawned_counts = {k: 0 for k in recipe.keys()}
        self.total_to_spawn = sum(recipe.values())
        self.spawn_count = 0
        self.done = False
        self.active = True
        self.spawn_timer = 0.0
        
        # Expand recipe into flat list for staggered spawning (1 enemy per frame)
        self.to_spawn_queue = []
        for enemy_type, count in recipe.items():
            for _ in range(count):
                self.to_spawn_queue.append(enemy_type)
        # Shuffle queue for variety
        random.shuffle(self.to_spawn_queue)
        
        # Debug output
        print(f"Spawner.begin(): Recipe = {recipe}, Total to spawn = {self.total_to_spawn}, Queue size = {len(self.to_spawn_queue)}")
        
        # Update spawn config
        if "interval_sec" in spawn_config:
            self.spawn_interval = spawn_config["interval_sec"]
    
    def update(self, dt: float, enemy_group: pygame.sprite.Group, world=None):
        """
        Update spawner and spawn enemies if needed.
        Spawns exactly ONE enemy per frame when interval elapsed (staggered spawning).
        """
        if not self.active or self.done:
            return
        
        # Check if queue is empty (wave complete)
        if not self.to_spawn_queue:
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
        
        # Spawn exactly ONE enemy if interval elapsed and queue not empty
        if self.spawn_timer >= effective_interval and self.to_spawn_queue:
            enemy_type = self.to_spawn_queue.pop()
            enemy = self._spawn_single_enemy(enemy_type, enemy_group, world)
            if enemy:
                self.spawn_timer = 0.0
            else:
                # Failed to spawn - put enemy type back in queue and try again next frame
                self.to_spawn_queue.append(enemy_type)
                print(f"Warning: Failed to spawn {enemy_type}, will retry")
    
    def _spawn_single_enemy(self, enemy_type: str, enemy_group: pygame.sprite.Group, world=None):
        """
        Spawn a single enemy - simple approach like F3 debug mode.
        Args:
            enemy_type: Type ID of enemy to spawn
            enemy_group: Group to add enemy to
            world: World object for modifiers
        Returns:
            Enemy instance if spawned successfully, None otherwise
        """
        # Get enemy class from factory
        if enemy_type not in self.enemy_factory:
            return None
        
        enemy_class = self.enemy_factory[enemy_type]
        
        # Get spawn position at edge of screen (simple - just pick random edge)
        import constants as c
        margin = 50
        edge = random.choice(["top", "bottom", "left", "right"])
        
        if edge == "top":
            spawn_x = random.uniform(margin, c.SCREEN_WIDTH - margin)
            spawn_y = random.uniform(-50, 0)  # Just above screen
        elif edge == "bottom":
            spawn_x = random.uniform(margin, c.SCREEN_WIDTH - margin)
            spawn_y = random.uniform(c.SCREEN_HEIGHT, c.SCREEN_HEIGHT + 50)  # Just below screen
        elif edge == "left":
            spawn_x = random.uniform(-50, 0)  # Just left of screen
            spawn_y = random.uniform(margin, c.SCREEN_HEIGHT - margin)
        else:  # right
            spawn_x = random.uniform(c.SCREEN_WIDTH, c.SCREEN_WIDTH + 50)  # Just right of screen
            spawn_y = random.uniform(margin, c.SCREEN_HEIGHT - margin)
        
        spawn_pos = pygame.Vector2(spawn_x, spawn_y)
        
        # Create enemy directly (same as F3 debug mode)
        enemy = enemy_class(spawn_pos)
        
        # Apply modifiers if available
        if world and hasattr(world, 'modifiers'):
            modifiers = world.modifiers
            if modifiers.get("zombie_speed_mult", 1.0) != 1.0:
                enemy.speed *= modifiers.get("zombie_speed_mult", 1.0)
            if modifiers.get("zombie_hp_mult", 1.0) != 1.0:
                hp_mult = modifiers.get("zombie_hp_mult", 1.0)
                enemy.max_hp = int(enemy.max_hp * hp_mult)
                enemy.hp = enemy.max_hp
        
        # Add to group (same as F3 debug mode)
        enemy_group.add(enemy)
        self.spawned_counts[enemy_type] = self.spawned_counts.get(enemy_type, 0) + 1
        self.spawn_count += 1
        
        return enemy
    
    def _generate_spawn_cache(self):
        """Pre-generate 200 spawn positions to avoid recalculating during gameplay"""
        self.spawn_cache = []
        for _ in range(self.spawn_cache_size):
            # Use existing spawn position logic to generate positions
            pos = self._get_random_edge_spawn_position(0, world=None)
            self.spawn_cache.append(pos)
    
    def _get_cached_spawn_position(self, world=None) -> Tuple[float, float]:
        """
        Get a cached spawn position (fast, no recalculation).
        Occasionally refreshes cache with new positions.
        Args:
            world: World object for noise calculation (only used for cache refresh)
        Returns:
            Tuple (x, y) spawn position
        """
        # Occasionally refresh cache (every 50 spawns, regenerate 10% of positions)
        if random.random() < 0.02:  # 2% chance per spawn
            for _ in range(10):  # Refresh 10 positions
                idx = random.randint(0, len(self.spawn_cache) - 1)
                self.spawn_cache[idx] = self._get_random_edge_spawn_position(0, world)
        
        # Return random cached position
        return random.choice(self.spawn_cache)
    
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
            # Spawn from bottom edge - must spawn BELOW screen so enemies move UP onto screen
            spawn_x = random.uniform(self.spawn_x_min + margin, self.spawn_x_max - margin)
            # Spawn 100+ pixels below screen to give enemies room to move onto screen
            spawn_y = self.spawn_y_max + 100 + offset * 20
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
        self.to_spawn_queue = []

