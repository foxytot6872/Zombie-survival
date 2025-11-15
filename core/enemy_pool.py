"""
Enemy pooling system for performance optimization.
Pre-allocates enemies at game start and reuses them instead of creating new instances.
"""
from typing import Dict, List, Type, Tuple, Optional
from world.enemy import Enemy


class EnemyPool:
    """
    Global enemy pooling system.
    Pre-allocates enemies and reuses them to avoid allocation overhead during gameplay.
    """
    
    # Pool sizes for each enemy type
    POOL_SIZES = {
        "walker": 80,
        "runner": 40,
        "swarmling": 40,
        "skeleton": 30,
        "spitter": 30,
        "archer_skeleton": 20,
        "brute": 20,
        "warrior_skeleton": 20
    }
    
    # Storage for pools: {enemy_type: [list of enemy instances]}
    pools: Dict[str, List[Enemy]] = {}
    
    # Track if pool is initialized
    _initialized = False
    
    @classmethod
    def initialize(cls, enemy_factory: Dict[str, Type[Enemy]]):
        """
        Initialize enemy pools by pre-creating all enemy instances.
        This should be called once at game start.
        
        Args:
            enemy_factory: Dictionary mapping enemy type IDs to enemy classes
        """
        if cls._initialized:
            return  # Already initialized
        
        print("Initializing enemy pools...")
        
        # Create a dummy position for initialization (will be reset when used)
        dummy_pos = (0, 0)
        
        # Pre-allocate enemies for each type
        for enemy_type, enemy_class in enemy_factory.items():
            pool_size = cls.POOL_SIZES.get(enemy_type, 20)  # Default to 20 if not specified
            pool = []
            
            for _ in range(pool_size):
                # Create enemy instance (sprites should already be cached)
                enemy = enemy_class(dummy_pos)
                # Mark as inactive (not alive, not in any group)
                enemy.alive = False
                enemy.reached_bottom = False
                pool.append(enemy)
            
            cls.pools[enemy_type] = pool
            print(f"  Created pool for {enemy_type}: {pool_size} enemies")
        
        cls._initialized = True
        print(f"Enemy pools initialized: {sum(len(pool) for pool in cls.pools.values())} total enemies")
    
    @classmethod
    def get(cls, enemy_type: str, spawn_pos: Tuple[float, float], modifiers: Optional[Dict] = None) -> Optional[Enemy]:
        """
        Get an enemy from the pool.
        
        Args:
            enemy_type: Type ID of the enemy (e.g., "walker", "runner")
            spawn_pos: Spawn position (x, y)
            modifiers: Optional modifiers dictionary (speed_mult, hp_mult, etc.)
            
        Returns:
            Enemy instance, or None if pool is empty (shouldn't happen with proper sizing)
        """
        if not cls._initialized:
            raise RuntimeError("EnemyPool not initialized! Call EnemyPool.initialize() first.")
        
        pool = cls.pools.get(enemy_type)
        if not pool:
            print(f"Warning: No pool for enemy type '{enemy_type}'")
            return None
        
        # Check if pool is empty (no available enemies)
        if len(pool) == 0:
            print(f"Warning: Pool for '{enemy_type}' is empty! Consider increasing pool size.")
            return None
        
        # Pop enemy from pool (LIFO for cache efficiency)
        enemy = pool.pop()
        
        # Reset enemy for reuse
        enemy.reset(spawn_pos, modifiers)
        
        return enemy
    
    @classmethod
    def release(cls, enemy: Enemy):
        """
        Release an enemy back to the pool for reuse.
        Should be called when enemy dies or is removed.
        
        Args:
            enemy: Enemy instance to return to pool
        """
        if not cls._initialized:
            return  # Pool not initialized, can't release
        
        # Get enemy type ID
        type_id = getattr(enemy, 'TYPE_ID', None)
        if not type_id:
            # Fallback: try to determine from class name
            class_name = enemy.__class__.__name__
            type_id_map = {
                'BasicZombie': 'walker',
                'RunnerZombie': 'runner',
                'SwarmlingZombie': 'swarmling',
                'BruteZombie': 'brute',
                'SpitterZombie': 'spitter',
                'Skeleton': 'skeleton',
                'ArcherSkeleton': 'archer_skeleton',
                'WarriorSkeleton': 'warrior_skeleton'
            }
            type_id = type_id_map.get(class_name)
        
        if not type_id:
            print(f"Warning: Could not determine type_id for enemy {enemy.__class__.__name__}, not pooling")
            return
        
        pool = cls.pools.get(type_id)
        if not pool:
            print(f"Warning: No pool for enemy type '{type_id}', cannot release")
            return
        
        # Add back to pool (only if pool isn't already full)
        max_size = cls.POOL_SIZES.get(type_id, 20)
        if len(pool) < max_size:
            pool.append(enemy)
        # If pool is full, enemy is simply discarded (shouldn't happen in normal gameplay)
    
    @classmethod
    def get_pool_size(cls, enemy_type: str) -> int:
        """Get current pool size (available enemies) for a type"""
        pool = cls.pools.get(enemy_type, [])
        return len(pool)
    
    @classmethod
    def get_total_available(cls) -> int:
        """Get total number of available enemies across all pools"""
        return sum(len(pool) for pool in cls.pools.values())
    
    @classmethod
    def reset(cls):
        """Reset pools (clear all enemies, call initialize again to recreate)"""
        cls.pools.clear()
        cls._initialized = False

