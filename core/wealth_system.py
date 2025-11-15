"""
RimWorld-style wealth calculation system for raid scaling.
Calculates wealth based on buildings, turrets, and research.
"""
from typing import Dict, Optional
from world.building import BuildState


class WealthSystem:
    """
    Calculates player wealth from buildings, turrets, and research.
    Used for dynamic raid scaling similar to RimWorld.
    """
    
    def __init__(self, world):
        """
        Initialize wealth system.
        Args:
            world: World object containing building_group and research manager
        """
        self.world = world
    
    def calculate_building_wealth(self) -> float:
        """
        Calculate wealth from all buildings (walls, production, HQ, etc.).
        Each building contributes based on tier & footprint size.
        Walls are cheap, production buildings add more wealth.
        
        Returns:
            Total building wealth value
        """
        wealth = 0.0
        
        if not self.world or not hasattr(self.world, 'building_group'):
            return wealth
        
        for building in self.world.building_group:
            # Only count active buildings
            if hasattr(building, 'state') and building.state != BuildState.ACTIVE:
                continue
            
            # Get base cost (sum of all resource costs)
            base_cost = 50.0  # Default fallback
            if hasattr(building, 'COST'):
                cost = building.COST
                # Sum all resource costs (wood, iron, food, coins)
                # Don't use coins as wealth per requirements
                base_cost = (
                    getattr(cost, 'wood', 0) +
                    getattr(cost, 'iron', 0) +
                    getattr(cost, 'food', 0)
                )
                if base_cost == 0:
                    base_cost = 50.0  # Fallback if no cost
            
            # Tier multiplier: 1.0 for tier 1, 1.35 for tier 2, 1.70 for tier 3
            tier_mult = 1.0 + (0.35 * (getattr(building, 'tier', 1) - 1))
            
            # Footprint size multiplier (width * height)
            footprint = getattr(building, 'FOOTPRINT', (1, 1))
            if isinstance(footprint, (list, tuple)) and len(footprint) >= 2:
                size_mult = footprint[0] * footprint[1]
            else:
                size_mult = 1.0
            
            # Wall buildings are cheap (50% wealth multiplier)
            type_id = getattr(building, 'TYPE_ID', '').lower()
            is_wall = type_id.startswith('wall') or type_id == 'gate'
            wall_multiplier = 0.5 if is_wall else 1.0
            
            # Calculate wealth contribution
            # Reduce base cost before applying multipliers to prevent excessive wealth
            # Divide by 10 to normalize wealth values (resources are in larger numbers)
            normalized_base_cost = base_cost / 10.0
            building_wealth = normalized_base_cost * tier_mult * size_mult * wall_multiplier
            wealth += building_wealth
        
        return wealth
    
    def calculate_turret_power(self) -> float:
        """
        Calculate turret combat power (massively important for raid scaling).
        Turrets add a LOT of wealth with exponential tier scaling.
        
        Formula: (damage * fire_rate * (range/100)) * (1.5 ** (tier-1)) * 20
        
        Returns:
            Total turret power converted to raid points
        """
        power = 0.0
        
        if not self.world or not hasattr(self.world, 'building_group'):
            return power
        
        for building in self.world.building_group:
            # Only count active turrets
            if hasattr(building, 'state') and building.state != BuildState.ACTIVE:
                continue
            
            # Check if it's a turret
            type_id = getattr(building, 'TYPE_ID', '').lower()
            is_turret = type_id.startswith('turret')
            
            if not is_turret:
                continue
            
            # Get turret stats
            damage = getattr(building, 'damage', 5)
            base_cooldown = getattr(building, 'base_cooldown', 1000)  # milliseconds
            
            # Convert cooldown to fire rate (shots per second)
            # Lower cooldown = higher fire rate
            if base_cooldown > 0:
                fire_rate = 1000.0 / base_cooldown  # shots per second
            else:
                fire_rate = 1.0
            
            base_range = getattr(building, 'base_range', 120)
            tier = getattr(building, 'tier', 1)
            
            # RimWorld-style exponential scaling
            # Tier 1: 1.0, Tier 2: 1.5, Tier 3: 2.25
            tier_multiplier = 1.5 ** (tier - 1)
            
            # Calculate turret combat points
            # Formula: (damage * fire_rate * (range/100)) * tier_multiplier
            range_factor = base_range / 100.0  # Normalize range
            turret_points = (damage * fire_rate * range_factor) * tier_multiplier
            
            # Convert to raid points (multiply by 5 - reduced from 20 to prevent excessive scaling)
            # This will be further divided by 10 in calculate_raid_points for final value of 0.5x
            power += turret_points * 5.0
        
        return power
    
    def calculate_research_wealth(self) -> float:
        """
        Calculate wealth from research progression.
        Every research completed increases raid pressure slightly.
        
        Returns:
            Total research wealth value
        """
        if not self.world or not hasattr(self.world, 'research'):
            return 0.0
        
        research_manager = self.world.research
        if not research_manager:
            return 0.0
        
        # Count unlocked research items
        unlocked_count = len(getattr(research_manager, 'unlocked', set()))
        
        # Each research adds 40 wealth (reduced from 80 to prevent excessive scaling)
        return unlocked_count * 40.0
    
    def total_wealth(self) -> float:
        """
        Calculate total wealth from all sources.
        
        Returns:
            Total wealth value (building + turret + research)
        """
        building_wealth = self.calculate_building_wealth()
        turret_power = self.calculate_turret_power()
        research_wealth = self.calculate_research_wealth()
        
        return building_wealth + turret_power + research_wealth

