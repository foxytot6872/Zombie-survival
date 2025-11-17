"""
Research system for unlocking buildings and upgrades.
"""
import copy
import json
import os
from typing import Set, Dict, Optional, Callable, List

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
        self.base_research_defs: Dict = {}
        self.research_cost_multiplier: float = 1.0
        self.research_modifiers: Dict[str, float] = {}  # Permanent research modifiers
        self._cached_effective_modifiers: Dict[str, float] = {}  # Cached effective modifiers
        self._modifiers_dirty: bool = True  # Flag to indicate if modifiers need recalculation
        
        # Callback function called when research is unlocked (for UI updates)
        self.on_unlock_callback: Optional[Callable[[str, List[str]], None]] = None
        
        # Load research definitions
        path = "data/config/research.json"
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.research_defs = json.load(f)
                    self.base_research_defs = copy.deepcopy(self.research_defs)
            else:
                print(f"Warning: Research config not found at {path}, using empty definitions")
        except Exception as e:
            print(f"Error loading research config: {e}")
            self.research_defs = {}
            self.base_research_defs = {}

        # Auto-purchase free root nodes so their branches are available
        for root_key in ("agriculture", "ballistic_engineering"):
            if root_key in self.research_defs:
                data = self.research_defs[root_key]
                cost = data.get("cost", data.get("cost_coins", 0))
                prereqs = data.get("prerequisites", [])
                if cost == 0 and not prereqs:
                    self.purchased.add(root_key)
    
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
        # Check prerequisites
        if not self._are_prerequisites_met(research_key):
            return False
        # Check affordability
        cost = self.research_defs[research_key].get("cost", self.research_defs[research_key].get("cost_coins", 0))
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

        # Check prerequisites before unlocking
        if not self._are_prerequisites_met(research_key):
            return False
        
        # Check cost
        cost = self.research_defs[research_key].get("cost", self.research_defs[research_key].get("cost_coins", 0))
        if not self.world.resources.spend_coins(cost):
            return False
        
        # Mark as purchased
        self.purchased.add(research_key)
        
        # Grant unlocks
        unlocks = self.research_defs[research_key].get("unlocks", [])
        for item in unlocks:
            self.unlocked.add(item)
        
        # Call callback to notify UI systems (e.g., update build panel)
        if self.on_unlock_callback:
            try:
                self.on_unlock_callback(research_key, unlocks)
            except Exception as e:
                print(f"Warning: Error in unlock callback: {e}")
        
        # Apply modifiers immediately
        modifiers = self.research_defs[research_key].get("modifiers", {})
        for mod_key, mod_value in modifiers.items():
            if isinstance(mod_value, (int, float)):
                # Special handling for additive modifiers (max_survivors)
                if mod_key == "max_survivors":
                    # Additive stacking for max_survivors
                    current = self.research_modifiers.get(mod_key, 0)
                    self.research_modifiers[mod_key] = current + mod_value
                else:
                    # Multiplicative stacking for other modifiers
                    # If this is the first research for this modifier, start from 1.0
                    current = self.research_modifiers.get(mod_key, 1.0)
                    self.research_modifiers[mod_key] = current * mod_value
            else:
                # For non-numeric modifiers, just set it
                self.research_modifiers[mod_key] = mod_value
        
        # Mark modifiers as dirty so they get recalculated
        self._modifiers_dirty = True
        
        return True
    
    def apply_difficulty_scaling(self, target_total: Optional[float] = None, multiplier: Optional[float] = None):
        """
        Scale research costs to approximate a desired total expenditure or apply a multiplier.
        """
        if not self.base_research_defs:
            self.base_research_defs = copy.deepcopy(self.research_defs)
        factor = 1.0
        base_total = self._base_total_cost()
        if target_total and base_total > 0:
            factor = target_total / base_total
        elif multiplier:
            factor = multiplier
        if factor <= 0:
            factor = 1.0
        self.research_cost_multiplier = factor
        for key, data in self.base_research_defs.items():
            base_cost = max(0, data.get("cost", data.get("cost_coins", 0)))
            scaled_cost = max(1, int(round(base_cost * factor)))
            if key not in self.research_defs:
                self.research_defs[key] = data.copy()
            self.research_defs[key]["cost"] = scaled_cost
    
    def _base_total_cost(self) -> float:
        if not self.base_research_defs:
            return 0.0
        return sum(max(0, data.get("cost", data.get("cost_coins", 0))) for data in self.base_research_defs.values())
    
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
        
        # Apply research modifiers on top of day event modifiers
        for mod_key, mod_value in self.research_modifiers.items():
            if isinstance(mod_value, (int, float)):
                # Special handling for additive modifiers (max_survivors)
                if mod_key == "max_survivors":
                    # Additive stacking for max_survivors
                    base_value = effective.get(mod_key, 0)
                    effective[mod_key] = base_value + mod_value
                else:
                    # Multiplicative stacking for other modifiers
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

    # ------------------------------
    # Internal helpers
    # ------------------------------
    def _are_prerequisites_met(self, research_key: str) -> bool:
        """Check that all prerequisites are already purchased for a research item."""
        data = self.research_defs.get(research_key, {})
        parents = data.get("prerequisites", [])
        if not parents:
            return True
        return all(parent in self.purchased for parent in parents)

