"""
Wave management system for coordinating night waves.
"""
import json
import random
import math
from typing import Dict, Optional, Tuple, List

# Import wealth system for RimWorld-style raid scaling
from core.wealth_system import WealthSystem
from world.building import BuildState

class WaveManager:
    """Manages wave-based spawning and day/night cycles"""
    
    STATE_DAY = "DAY"
    STATE_NIGHT = "NIGHT"
    STATE_SUMMARY = "SUMMARY"
    
    def __init__(self, world, waves_cfg: Dict, difficulty: str = "normal"):
        """
        Initialize wave manager.
        Args:
            world: World object containing game state
            waves_cfg: Wave configuration dictionary
            difficulty: Difficulty level ("easy", "normal", "hard")
        """
        self.world = world
        self.cfg = waves_cfg
        self.difficulty = difficulty
        self.night = 1
        self.day = 1
        self.state = self.STATE_DAY
        self.timer = 0.0
        self.day_duration = waves_cfg.get("day_duration", 30.0)
        self.summary_duration = waves_cfg.get("summary_duration", 5.0)
        self.win_nights = waves_cfg.get("win_nights", 10)
        
        # Statistics
        self.enemies_killed = 0
        self.enemies_spawned = 0
        
        # Night modifiers (random nightly events)
        self.current_night_modifier: Optional[Dict] = None
        
        # Wealth system for RimWorld-style raid scaling
        self.wealth_system = WealthSystem(world)
        
        # Track last night's damage for adaptation/rubber band system
        self.last_night_hq_max_hp: float = 0.0
        self.last_night_hq_hp_after: float = 0.0
        self.last_night_total_building_hp_before: float = 0.0
        self.last_night_total_building_hp_after: float = 0.0
        
        # Track raid points (never drops, only increases)
        self.last_raid_points: float = 20.0
        
    def start_day(self):
        """Start a new day"""
        self.state = self.STATE_DAY
        self.timer = 0.0
        self.day += 1
        # Trigger node spawn event (handled by main.py)
        if hasattr(self, 'on_day_start'):
            self.on_day_start()
        
    def start_night(self):
        """Start a night wave"""
        self.state = self.STATE_NIGHT
        self.timer = 0.0
        self.enemies_spawned = 0
        
        # Record night start stats for adaptation system (before damage)
        self.record_night_start_stats()
        
        # Roll night modifier before spawning starts
        night_mod = self.roll_night_modifier(self.night)
        
        # Apply night modifier to world modifiers
        if night_mod and self.world:
            for key, value in night_mod.get("effects", {}).items():
                # Stack multiplicatively with existing modifiers (don't overwrite, multiply)
                if key.endswith("_mult"):
                    current_value = self.world.modifiers.get(key, 1.0)
                    self.world.modifiers[key] = current_value * value
                else:
                    # For non-multiplier effects, set directly (e.g., brute_spawn_chance_bonus)
                    self.world.modifiers[key] = value
        
    def start_summary(self):
        """Start the summary phase after a wave"""
        self.state = self.STATE_SUMMARY
        self.timer = 0.0
        
        # Record night end stats for adaptation system (after damage)
        self.record_night_end_stats()
        
        # Clear night modifier when night ends
        # Note: We don't reset modifiers here because day events may have active modifiers.
        # Day events will reset modifiers when they change. We only remove night modifier effects.
        if self.current_night_modifier and self.world:
            modifier_effects = self.current_night_modifier.get("effects", {})
            for key, value in modifier_effects.items():
                if key.endswith("_mult"):
                    # Divide out the night modifier (reverse multiplication)
                    # Only divide if the value was applied (check if it exists)
                    if key in self.world.modifiers:
                        current_value = self.world.modifiers.get(key, 1.0)
                        # Divide out the night modifier effect
                        self.world.modifiers[key] = current_value / value
                else:
                    # Remove non-multiplier effects (e.g., brute_spawn_chance_bonus)
                    if key in self.world.modifiers:
                        del self.world.modifiers[key]
        
        self.clear_night_modifier()
        
    def get_wave_recipe(self) -> Dict[str, int]:
        """Get the enemy recipe for the current night"""
        # Get base recipe for this night (loop if we exceed defined nights)
        night_index = min(self.night - 1, len(self.cfg["nights"]) - 1)
        base_mix = self.cfg["nights"][night_index]["mix"].copy()
        
        # Calculate difficulty multiplier
        difficulty_mult = self.cfg["difficulty"].get(self.difficulty, 1.0)
        
        # Calculate night scaling multiplier
        night_mult = self.cfg["increment"]["per_night_mult"] ** (self.night - 1)
        
        # Apply multipliers
        total_mult = difficulty_mult * night_mult
        
        # Scale enemy counts
        recipe = {}
        for enemy_type, count in base_mix.items():
            recipe[enemy_type] = int(count * total_mult)
        
        return recipe
    
    def update(self, dt: float, spawner, world) -> str:
        """
        Update wave manager.
        Returns:
            Current state or "WIN" if won
        """
        old_state = self.state
        self.timer += dt
        
        if self.state == self.STATE_DAY:
            # Day phase: wait for day duration, then start night
            if self.timer >= self.day_duration:
                self.start_night()
                
        elif self.state == self.STATE_NIGHT:
            # Night phase: spawn enemies until wave is complete
            # Spawner handles actual spawning
            # Update enemies spawned count
            if spawner:
                self.enemies_spawned = spawner.spawn_count
            
            # Check if wave is complete (spawner done and no enemies)
            if spawner and spawner.done:
                # Check if all enemies are dead
                if world and hasattr(world, 'enemy_group'):
                    if len(world.enemy_group) == 0:
                        self.start_summary()
                        
        elif self.state == self.STATE_SUMMARY:
            # Summary phase: wait for summary duration, then start next day
            if self.timer >= self.summary_duration:
                # Check win condition
                if self.night > self.win_nights:
                    return "WIN"
                self.start_day()
        
        return self.state
    
    def get_current_wave_info(self) -> Dict:
        """Get information about the current wave"""
        recipe = self.get_wave_recipe()
        return {
            "night": self.night,
            "day": self.day,
            "state": self.state,
            "recipe": recipe,
            "enemies_killed": self.enemies_killed,
            "enemies_spawned": self.enemies_spawned
        }
    
    def is_won(self) -> bool:
        """Check if game is won"""
        return self.night > self.win_nights
    
    def reset(self):
        """Reset wave manager"""
        self.night = 1
        self.day = 1
        self.state = self.STATE_DAY
        self.timer = 0.0
        self.enemies_killed = 0
        self.enemies_spawned = 0
        
        # Reset adaptation tracking
        self.last_night_hq_max_hp = 0.0
        self.last_night_hq_hp_after = 0.0
        self.last_night_total_building_hp_before = 0.0
        self.last_night_total_building_hp_after = 0.0
        self.last_raid_points = 20.0
    
    def get_spawn_side_for_night(self, night_number: int) -> str:
        """
        Get weighted random spawn side based on night number.
        
        Night 1-3:  70% Bottom, 15% Left, 15% Right
        Night 4-6:  Bottom 40%, Left 30%, Right 30%
        Night 7-9:  Equal 25% each (Bottom/Left/Right/Top)
        Night 10+:  Random Surge: 1 side gets 60%, others 40% split
        
        Args:
            night_number: Current night number
            
        Returns:
            Spawn side string: "top", "bottom", "left", or "right"
        """
        if night_number <= 3:
            # Night 1-3: 70% Bottom, 15% Left, 15% Right
            weights = {"bottom": 70, "left": 15, "right": 15, "top": 0}
        elif night_number <= 6:
            # Night 4-6: Bottom 40%, Left 30%, Right 30%
            weights = {"bottom": 40, "left": 30, "right": 30, "top": 0}
        elif night_number <= 9:
            # Night 7-9: Equal 25% each
            weights = {"bottom": 25, "left": 25, "right": 25, "top": 25}
        else:
            # Night 10+: Random Surge - 1 side gets 60%, others split remaining 40%
            sides = ["top", "bottom", "left", "right"]
            surge_side = random.choice(sides)
            # 1 side gets 60%, other 3 sides split 40% = 40/3 ≈ 13.33% each
            weights = {side: (60 if side == surge_side else 40 // 3) for side in sides}
        
        # Weighted random choice
        total_weight = sum(weights.values())
        rand = random.uniform(0, total_weight)
        cumulative = 0.0
        
        for side, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return side
        
        # Fallback to bottom if something goes wrong
        return "bottom"
    
    def roll_night_modifier(self, night_number: int) -> Optional[Dict]:
        """
        Roll a random night modifier for the current night.
        Night modifiers are separate from day events and apply during the night phase.
        
        Modifiers:
        - Blood Moon: zombie_hp_mult = 1.25
        - Fog Night: turret_range_mult = 0.8
        - Calm Night: zombie_spawn_mult = 0.8
        - Fast Night: zombie_speed_mult = 1.25
        - Brute Surge: brute_spawn_chance += 30%
        
        Args:
            night_number: Current night number
            
        Returns:
            Dictionary with modifier info, or None if no modifier
        """
        # Night modifiers list
        night_modifiers = [
            {
                "id": "blood_moon",
                "name": "Blood Moon",
                "description": "+25% Zombie HP",
                "effects": {"zombie_hp_mult": 1.25}
            },
            {
                "id": "fog_night",
                "name": "Fog Night",
                "description": "-20% Turret Range",
                "effects": {"turret_range_mult": 0.8}
            },
            {
                "id": "calm_night",
                "name": "Calm Night",
                "description": "-20% Zombie Spawn Rate",
                "effects": {"zombie_spawn_mult": 0.8}
            },
            {
                "id": "fast_night",
                "name": "Fast Night",
                "description": "+25% Zombie Speed",
                "effects": {"zombie_speed_mult": 1.25}
            },
            {
                "id": "brute_surge",
                "name": "Brute Surge",
                "description": "+30% Brute Spawn Chance",
                "effects": {"brute_spawn_chance_bonus": 0.30}
            }
        ]
        
        # 70% chance of a night modifier (30% normal night)
        if random.random() < 0.70:
            modifier = random.choice(night_modifiers)
            self.current_night_modifier = modifier
            return modifier
        
        self.current_night_modifier = None
        return None
    
    def clear_night_modifier(self):
        """Clear current night modifier"""
        self.current_night_modifier = None
    
    def _get_difficulty_wealth_multiplier(self) -> float:
        """
        Get difficulty-based wealth multiplier.
        Different difficulties convert different percentages of wealth to raid points.
        
        Returns:
            Wealth multiplier based on difficulty:
            - Easy: 0.8 (80% of wealth)
            - Medium: 0.9 (90% of wealth)
            - Hard: 1.0 (100% of wealth)
            - Extreme: 1.2 (120% of wealth)
        """
        difficulty_wealth_multipliers = {
            "easy": 0.8,      # 80% of wealth
            "normal": 0.9,    # 90% of wealth (medium)
            "medium": 0.9,    # 90% of wealth (alias)
            "hard": 1.0,      # 100% of wealth
            "extreme": 1.2    # 120% of wealth
        }
        
        # Get difficulty string (normalize to lowercase)
        difficulty_str = self.difficulty.lower() if self.difficulty else "normal"
        
        # Return multiplier, default to 1.0 (hard) if difficulty not found
        return difficulty_wealth_multipliers.get(difficulty_str, 1.0)
    
    def calculate_raid_points(self) -> float:
        """
        Calculate raid points using RimWorld-style formula.
        
        Formula:
        WealthPoints = ((BuildingWealth + ResearchWealth) * DifficultyWealthMultiplier / 100) ** 1.15 (exponential scaling)
        TurretPower = turret_power / 10 (converted to raid points)
        TimeFactor = 1 + (current_day / 20) (increases with day progression)
        Difficulty = difficulty_multiplier (from config)
        
        Final: RaidPoints = (WealthPoints + TurretPower) * TimeFactor * Difficulty
        
        Difficulty Wealth Multipliers:
        - Easy: 80% of wealth
        - Medium: 90% of wealth
        - Hard: 100% of wealth
        - Extreme: 120% of wealth
        
        Raid points never drop (only increase).
        
        Returns:
            Raid points value for wave generation
        """
        # Calculate wealth components separately (avoid double-counting turret power)
        building_wealth = self.wealth_system.calculate_building_wealth()
        research_wealth = self.wealth_system.calculate_research_wealth()
        turret_power = self.wealth_system.calculate_turret_power()
        
        # Calculate total wealth (without turret power, since it's handled separately)
        total_wealth = building_wealth + research_wealth
        
        # Apply difficulty wealth multiplier (different difficulties use different % of wealth)
        difficulty_wealth_mult = self._get_difficulty_wealth_multiplier()
        adjusted_wealth = total_wealth * difficulty_wealth_mult
        
        # Apply exponential scaling: (AdjustedWealth / 100) ** 1.15
        # The division by 100 normalizes wealth values before applying exponential
        wealth_points = (adjusted_wealth / 100.0) ** 1.15
        
        # Turret power (already multiplied by 5 in calculate_turret_power)
        # Divide by 10 to convert to raid points scale
        turret_raid_points = turret_power / 10.0
        
        # Time factor (increases more slowly with day progression)
        # Changed from (day / 10) to (day / 20) to slow down growth
        time_factor = 1.0 + (self.day / 20.0)
        
        # Difficulty multiplier
        difficulty_mult = self.cfg["difficulty"].get(self.difficulty, 1.0)
        
        # Calculate raid points
        base_raid_points = wealth_points + turret_raid_points
        raid_points = base_raid_points * time_factor * difficulty_mult
        
        # Apply adaptation/rubber band system if we have last night's data
        adaptation_mult = self._calculate_adaptation_multiplier()
        raid_points *= adaptation_mult
        
        # Never let raid points drop (only increase)
        raid_points = max(raid_points, self.last_raid_points)
        self.last_raid_points = raid_points
        
        # Ensure minimum raid points, but also cap maximum to prevent excessive waves
        raid_points = max(raid_points, 20.0)
        # Cap maximum raid points to prevent 1000+ zombie waves
        # 500 raid points ≈ 250-500 enemies depending on mix (reasonable max)
        raid_points = min(raid_points, 500.0)
        
        return raid_points
    
    def _calculate_adaptation_multiplier(self) -> float:
        """
        Calculate adaptation multiplier based on last night's damage (RimWorld-like rubber band).
        
        If HQ/buildings took huge damage (>30%) → reduce raid strength by 25%
        If no damage was taken → increase raid strength by 25%
        
        Returns:
            Adaptation multiplier (0.75, 1.0, or 1.25)
        """
        # Only apply adaptation if we have valid last night data
        if (self.last_night_hq_max_hp <= 0 or 
            self.last_night_total_building_hp_before <= 0):
            return 1.0
        
        # Calculate HQ damage percentage
        hq_hp_loss = self.last_night_hq_max_hp - self.last_night_hq_hp_after
        hq_damage_percent = (hq_hp_loss / self.last_night_hq_max_hp) if self.last_night_hq_max_hp > 0 else 0.0
        
        # Calculate total building HP loss
        building_hp_loss = self.last_night_total_building_hp_before - self.last_night_total_building_hp_after
        building_damage_percent = (building_hp_loss / self.last_night_total_building_hp_before) if self.last_night_total_building_hp_before > 0 else 0.0
        
        # Use the maximum of HQ damage or building damage
        max_damage_percent = max(hq_damage_percent, building_damage_percent)
        
        # Apply adaptation
        if max_damage_percent > 0.30:  # >30% damage
            return 0.75  # 25% easier
        elif max_damage_percent == 0.0:  # No damage taken
            return 1.25  # 25% harder (player dominating)
        else:
            return 1.0  # Normal (moderate damage)
    
    def generate_wave_from_raid_points(self, raid_points: float) -> Dict[str, int]:
        """
        Generate enemy wave recipe from raid points.
        Stronger enemies only appear after certain days to help with scaling.
        
        Enemy point costs and unlock days:
        - BasicZombie (walker): 1 point - Day 1+
        - Runner: 1.5 points - Day 1+
        - Swarmling: 0.5 points - Day 1+
        - Skeleton: 3 points - Day 3+
        - Spitter: 3 points - Day 5+
        - ArcherSkeleton: 4 points - Day 7+
        - BruteZombie: 6 points - Day 9+
        - WarriorSkeleton: 8 points - Day 9+
        
        Args:
            raid_points: Total raid points to spend
            
        Returns:
            Dictionary mapping enemy TYPE_ID to count
        """
        # Enemy point costs mapping (TYPE_ID -> cost)
        enemy_costs = {
            "walker": 1.0,
            "runner": 1.5,
            "swarmling": 0.5,
            "spitter": 3.0,
            "skeleton": 3.0,
            "archer_skeleton": 4.0,
            "brute": 6.0,
            "warrior_skeleton": 8.0
        }
        
        # Enemy unlock days (when they start appearing)
        enemy_unlock_days = {
            "walker": 1,      # Available from day 1
            "runner": 1,      # Available from day 1
            "swarmling": 1,   # Available from day 1
            "skeleton": 3,    # Available from day 3
            "spitter": 5,     # Available from day 5 (ranged attacker)
            "archer_skeleton": 7,  # Available from day 7
            "brute": 9,       # Available from day 9 (strong tank)
            "warrior_skeleton": 9  # Available from day 9 (strongest)
        }
        
        # Filter enemies based on current day
        available_enemies = {}
        for enemy_type, cost in enemy_costs.items():
            unlock_day = enemy_unlock_days.get(enemy_type, 1)
            if self.day >= unlock_day:
                available_enemies[enemy_type] = cost
        
        # If no enemies are available (shouldn't happen), fall back to basic enemies
        if not available_enemies:
            available_enemies = {
                "walker": 1.0,
                "runner": 1.5,
                "swarmling": 0.5
            }
        
        # Create enemy pool with weights (cheaper enemies spawn more often)
        # Weight is inverse of cost (cheaper = higher weight)
        enemy_pool = []
        for enemy_type, cost in available_enemies.items():
            # Weight by inverse cost (cheaper enemies are more common)
            weight = 1.0 / cost
            # Add multiple entries based on weight (normalized)
            entries = max(1, int(weight * 10))  # Scale weight
            for _ in range(entries):
                enemy_pool.append((enemy_type, cost))
        
        # Generate wave by spending raid points
        recipe = {}
        remaining_points = raid_points
        
        # Generate enemies until points are exhausted
        max_iterations = 500  # Safety limit (reduced from 1000 to prevent excessive waves)
        max_total_enemies = 200  # Hard cap on total enemy count
        iteration = 0
        total_enemies = 0
        
        while remaining_points > 0.5 and iteration < max_iterations and total_enemies < max_total_enemies:
            iteration += 1
            
            # Select random enemy from pool
            enemy_type, cost = random.choice(enemy_pool)
            
            # Check if we can afford it
            if remaining_points >= cost:
                recipe[enemy_type] = recipe.get(enemy_type, 0) + 1
                remaining_points -= cost
                total_enemies += 1
        
        return recipe
    
    def get_wave_recipe(self) -> Dict[str, int]:
        """
        Get the enemy recipe for the current night.
        Uses wealth-based scaling if enabled, otherwise falls back to config-based recipe.
        """
        # Check if wealth system is available and should be used
        if hasattr(self, 'wealth_system') and self.wealth_system:
            # Use RimWorld-style wealth-based wave generation
            raid_points = self.calculate_raid_points()
            recipe = self.generate_wave_from_raid_points(raid_points)
            return recipe
        
        # Fallback to original config-based recipe (backwards compatibility)
        # Get base recipe for this night (loop if we exceed defined nights)
        night_index = min(self.night - 1, len(self.cfg["nights"]) - 1)
        base_mix = self.cfg["nights"][night_index]["mix"].copy()
        
        # Calculate difficulty multiplier
        difficulty_mult = self.cfg["difficulty"].get(self.difficulty, 1.0)
        
        # Calculate night scaling multiplier
        night_mult = self.cfg["increment"]["per_night_mult"] ** (self.night - 1)
        
        # Apply multipliers
        total_mult = difficulty_mult * night_mult
        
        # Scale enemy counts
        recipe = {}
        for enemy_type, count in base_mix.items():
            recipe[enemy_type] = int(count * total_mult)
        
        return recipe
    
    def record_night_start_stats(self):
        """Record building HP stats at start of night for adaptation calculation"""
        if not self.world or not hasattr(self.world, 'building_group'):
            return
        
        # Find HQ
        hq = None
        for building in self.world.building_group:
            if hasattr(building, 'TYPE_ID') and building.TYPE_ID.lower() == 'hq':
                hq = building
                break
        
        # Record HQ stats
        if hq:
            self.last_night_hq_max_hp = float(getattr(hq, 'max_hp', 0))
        
        # Calculate total building HP
        total_hp = 0.0
        for building in self.world.building_group:
            if hasattr(building, 'state') and building.state == BuildState.ACTIVE:
                if hasattr(building, 'max_hp'):
                    total_hp += float(getattr(building, 'max_hp', 0))
        
        self.last_night_total_building_hp_before = total_hp
    
    def record_night_end_stats(self):
        """Record building HP stats at end of night for adaptation calculation"""
        if not self.world or not hasattr(self.world, 'building_group'):
            return
        
        # Find HQ
        hq = None
        for building in self.world.building_group:
            if hasattr(building, 'TYPE_ID') and building.TYPE_ID.lower() == 'hq':
                hq = building
                break
        
        # Record HQ stats
        if hq:
            self.last_night_hq_hp_after = float(getattr(hq, 'hp', 0))
        
        # Calculate total building HP
        total_hp = 0.0
        for building in self.world.building_group:
            if hasattr(building, 'state') and building.state == BuildState.ACTIVE:
                if hasattr(building, 'max_hp'):
                    total_hp += float(getattr(building, 'max_hp', 0))
        
        self.last_night_total_building_hp_after = total_hp

