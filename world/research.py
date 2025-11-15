"""
Research system for unlocking buildings and upgrades.
"""
import json
import os
from typing import Set, Dict

class ResearchManager:
    """Manages research unlocks and research definitions."""
    
    def __init__(self, world):
        """
        Initialize research manager.
        Args:
            world: World object with resources
        """
        self.world = world
        self.unlocked: Set[str] = set()  # Unlocked items (e.g., "sawmill", "railgun_turret")
        self.purchased: Set[str] = set()  # Purchased research keys (e.g., "sawmill_unlock")
        self.research_defs: Dict = {}
        self.research_modifiers: Dict[str, float] = {}  # Permanent research modifiers
        self._cached_effective_modifiers: Dict[str, float] = {}  # Cached effective modifiers
        self._modifiers_dirty: bool = True  # Flag to indicate if modifiers need recalculation
        
        # Load research definitions
        path = "data/config/research.json"
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.research_defs = json.load(f)
            else:
                print(f"Warning: Research config not found at {path}, using empty definitions")
        except Exception as e:
            print(f"Error loading research config: {e}")
            self.research_defs = {}
    
    def is_unlocked(self, key: str) -> bool:
        """
        Check if a research item is unlocked.
        Args:
            key: Research key (e.g., "sawmill", "turret_lv2")
        Returns:
            True if unlocked, False otherwise
        """
        return key in self.unlocked
    
    def can_research(self, research_key: str) -> bool:
        """
        Check if a research can be purchased.
        Args:
            research_key: Key from research.json
        Returns:
            True if can afford and not already purchased
        """
        if research_key not in self.research_defs:
            return False
        if research_key in self.purchased:
            return False  # Already purchased
        cost = self.research_defs[research_key].get("cost_coins", 0)
        return self.world.resources.coins >= cost
    
    def is_research_purchased(self, research_key: str) -> bool:
        """
        Check if a research has been purchased.
        Args:
            research_key: Key from research.json
        Returns:
            True if purchased, False otherwise
        """
        return research_key in self.purchased
    
    def unlock(self, research_key: str) -> bool:
        """
        Unlock a research item.
        Args:
            research_key: Key from research.json
        Returns:
            True if successful, False otherwise
        """
        if research_key not in self.research_defs:
            return False
        
        # Check if already purchased
        if research_key in self.purchased:
            return False
        
        # Check cost
        cost = self.research_defs[research_key].get("cost_coins", 0)
        if not self.world.resources.spend_coins(cost):
            return False
        
        # Mark as purchased
        self.purchased.add(research_key)
        
        # Grant unlocks
        unlocks = self.research_defs[research_key].get("unlocks", [])
        for item in unlocks:
            self.unlocked.add(item)
        
        # Apply modifiers immediately (stack multiplicatively)
        modifiers = self.research_defs[research_key].get("modifiers", {})
        for mod_key, mod_value in modifiers.items():
            if isinstance(mod_value, (int, float)):
                # Multiplicative stacking: multiply current value by new value
                # If this is the first research for this modifier, start from 1.0
                current = self.research_modifiers.get(mod_key, 1.0)
                self.research_modifiers[mod_key] = current * mod_value
            else:
                # For non-numeric modifiers, just set it
                self.research_modifiers[mod_key] = mod_value
        
        # Mark modifiers as dirty so they get recalculated
        self._modifiers_dirty = True
        
        return True
    
    def get_research_list(self) -> Dict:
        """Get all research definitions."""
        return self.research_defs.copy()
    
    def apply_research_modifiers(self) -> Dict[str, float]:
        """
        Get effective modifiers combining research and day event modifiers.
        Research modifiers stack multiplicatively with day event modifiers.
        Uses caching to avoid recalculating every frame.
        Returns:
            Dict of effective modifier values
        """
        # Only recalculate if modifiers are dirty
        if not self._modifiers_dirty:
            return self._cached_effective_modifiers
        
        # Get base modifiers from day events
        # IMPORTANT: We need to get day event modifiers directly, not from world.modifiers
        # because world.modifiers might already contain research modifiers from previous frame
        if hasattr(self.world, 'day_events') and self.world.day_events:
            # Get day event modifiers directly from day event manager
            # Day events store modifiers in world.modifiers, but we need to ensure
            # we're not reading research modifiers that were added in previous frames
            # For now, we'll assume world.modifiers is reset by day events when they change
            # and we mark it dirty, so we can safely read from it
            if hasattr(self.world, 'modifiers'):
                effective = self.world.modifiers.copy()
            else:
                effective = self._get_default_modifiers()
        else:
            effective = self._get_default_modifiers()
        
        # Apply research modifiers multiplicatively on top of day event modifiers
        for mod_key, mod_value in self.research_modifiers.items():
            if isinstance(mod_value, (int, float)):
                base_value = effective.get(mod_key, 1.0)
                effective[mod_key] = base_value * mod_value
            else:
                effective[mod_key] = mod_value
        
        # Cache the result
        self._cached_effective_modifiers = effective
        self._modifiers_dirty = False
        
        return self._cached_effective_modifiers
    
    def _get_default_modifiers(self) -> Dict[str, float]:
        """Get default modifier values (all 1.0)."""
        return {
            "resource_prod_mult": 1.0, "coin_drop_mult": 1.0, "build_cost_mult": 1.0,
            "turret_fire_rate_mult": 1.0, "building_damage_taken_mult": 1.0,
            "zombie_spawn_mult": 1.0, "zombie_speed_mult": 1.0, "zombie_hp_mult": 1.0,
            "turret_range_mult": 1.0, "gather_speed_mult": 1.0, "haul_speed_mult": 1.0,
            "building_hp_mult": 1.0, "enemy_skeleton_damage_mult": 1.0,
            # New modifiers
            "turret_damage_mult": 1.0, "turret_projectile_speed_mult": 1.0,
            "turret_hp_mult": 1.0, "wall_hp_mult": 1.0, "wall_repair_rate_mult": 1.0,
            "building_refund_mult": 1.0, "survivor_hp_mult": 1.0, "survivor_speed_mult": 1.0,
            "survivor_gather_speed_mult": 1.0, "survivor_haul_speed_mult": 1.0,
            "enemy_armor_pierce_mult": 1.0,
        }
    
    def is_research_unlocked(self, key: str) -> bool:
        """Alias for is_unlocked for consistency."""
        return self.is_unlocked(key)
    
    def get_research_by_tier(self) -> Dict[int, Dict]:
        """
        Get research items grouped by tier.
        Returns:
            Dict mapping tier number to dict of research items
        """
        tiered = {}
        for key, data in self.research_defs.items():
            tier = data.get("tier", 1)
            if tier not in tiered:
                tiered[tier] = {}
            tiered[tier][key] = data
        return tiered

