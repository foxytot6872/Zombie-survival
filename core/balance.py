"""
Central balance configuration system.
Loads base values (normal difficulty) and applies difficulty multipliers.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional, Union
from difficulty_config import Difficulty


class BalanceConfig:
    """Central balance configuration manager."""
    
    _instance: Optional['BalanceConfig'] = None
    _config: Dict[str, Any] = {}
    _current_difficulty: Difficulty = Difficulty.MEDIUM
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load the central balance configuration."""
        config_path = os.path.join('data', 'config', 'balance.json')
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"Warning: balance.json not found at {config_path}, using defaults")
            self._config = {"base": {}, "difficulty_multipliers": {}}
        except Exception as e:
            print(f"Error loading balance.json: {e}, using defaults")
            self._config = {"base": {}, "difficulty_multipliers": {}}
    
    def set_difficulty(self, difficulty: Difficulty):
        """Set the current difficulty for balance calculations."""
        self._current_difficulty = difficulty
    
    def _get_multiplier(self, key: str, default: float = 1.0) -> float:
        """Get a multiplier for the current difficulty."""
        diff_key = self._current_difficulty.name.lower()
        multipliers = self._config.get("difficulty_multipliers", {}).get(diff_key, {})
        return multipliers.get(key, default)
    
    def _apply_multiplier(self, value: Union[int, float], mult_key: str) -> Union[int, float]:
        """Apply a difficulty multiplier to a value."""
        mult = self._get_multiplier(mult_key, 1.0)
        result = value * mult
        return int(result) if isinstance(value, int) else result
    
    def _get_base_value(self, path: str, default: Any = None) -> Any:
        """Get a base value from the config using dot notation (e.g., 'buildings.farm.cost')."""
        keys = path.split('.')
        value = self._config.get("base", {})
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    # ============ BUILDINGS ============
    
    def get_building_cost(self, building_type: str) -> Dict[str, int]:
        """Get building cost, applying difficulty multiplier."""
        cost = self._get_base_value(f"buildings.{building_type}.cost", {})
        mult = self._get_multiplier("building_cost")
        return {k: int(v * mult) for k, v in cost.items()}
    
    def get_building_hp(self, building_type: str, default: int = 200) -> int:
        """Get building base HP, applying difficulty multiplier."""
        hp = self._get_base_value(f"buildings.{building_type}.base_hp", default)
        mult = self._get_multiplier("building_hp")
        return int(hp * mult)
    
    def get_building_build_time(self, building_type: str, default: float = 3.0) -> float:
        """Get building build time."""
        return self._get_base_value(f"buildings.{building_type}.build_time", default)
    
    def get_building_production(self, building_type: str) -> Dict[str, float]:
        """Get building production rates, applying difficulty multiplier."""
        production = self._get_base_value(f"buildings.{building_type}.production", {})
        mult = self._get_multiplier("production_rate")
        return {k: v * mult for k, v in production.items()}
    
    def get_repair_cost(self) -> float:
        """Get repair cost (wood per HP)."""
        return self._get_base_value("buildings.repair_cost.wood_per_hp", 0.2)
    
    def get_upgrade_cost_mult(self) -> float:
        """Get upgrade cost multiplier."""
        return self._get_base_value("buildings.upgrade_cost_mult", 1.25)
    
    def get_wall_upgrade_cost(self, wall_type: str) -> Dict[str, int]:
        """Get wall upgrade cost, applying difficulty multiplier."""
        cost = self._get_base_value(f"buildings.{wall_type}.upgrade_cost", {})
        mult = self._get_multiplier("building_cost")
        return {k: int(v * mult) for k, v in cost.items()}
    
    # ============ TURRETS ============
    
    def get_turret_cost(self, turret_type: str) -> Dict[str, int]:
        """Get turret cost, applying difficulty multiplier."""
        cost = self._get_base_value(f"turrets.{turret_type}.cost", {})
        mult = self._get_multiplier("building_cost")
        return {k: int(v * mult) for k, v in cost.items()}
    
    def get_turret_hp(self, turret_type: str, default: int = 200) -> int:
        """Get turret base HP, applying difficulty multiplier."""
        hp = self._get_base_value(f"turrets.{turret_type}.base_hp", default)
        mult = self._get_multiplier("building_hp")
        return int(hp * mult)
    
    def get_turret_build_time(self, turret_type: str, default: float = 2.5) -> float:
        """Get turret build time."""
        return self._get_base_value(f"turrets.{turret_type}.build_time", default)
    
    def get_turret_range(self, turret_type: str, default: float = 200.0) -> float:
        """Get turret attack range."""
        return self._get_base_value(f"turrets.{turret_type}.range", default)
    
    def get_turret_damage(self, turret_type: str, default: int = 10) -> int:
        """Get turret damage."""
        return self._get_base_value(f"turrets.{turret_type}.damage", default)
    
    def get_turret_cooldown(self, turret_type: str, default: int = 1000) -> int:
        """Get turret cooldown in milliseconds."""
        return self._get_base_value(f"turrets.{turret_type}.cooldown", default)
    
    def get_turret_projectile_speed(self, turret_type: str, default: float = 400.0) -> float:
        """Get turret projectile speed."""
        return self._get_base_value(f"turrets.{turret_type}.projectile_speed", default)
    
    def get_turret_pierce(self, turret_type: str) -> tuple[bool, int]:
        """Get turret pierce settings: (has_pierce, pierce_count)."""
        pierce = self._get_base_value(f"turrets.{turret_type}.pierce", False)
        pierce_count = self._get_base_value(f"turrets.{turret_type}.pierce_count", 0)
        return (pierce, pierce_count)
    
    # ============ ENEMIES ============
    
    def get_enemy_hp(self, enemy_type: str, default: int = 50) -> int:
        """Get enemy base HP, applying difficulty multiplier."""
        hp = self._get_base_value(f"enemies.{enemy_type}.base_hp", default)
        mult = self._get_multiplier("enemy_hp")
        return int(hp * mult)
    
    def get_enemy_speed(self, enemy_type: str, default: float = 30.0) -> float:
        """Get enemy speed, applying difficulty multiplier."""
        speed = self._get_base_value(f"enemies.{enemy_type}.speed", default)
        mult = self._get_multiplier("enemy_speed")
        return speed * mult
    
    def get_enemy_damage(self, enemy_type: str, default: int = 5) -> int:
        """Get enemy damage, applying difficulty multiplier."""
        damage = self._get_base_value(f"enemies.{enemy_type}.damage", default)
        mult = self._get_multiplier("enemy_damage")
        return int(damage * mult)
    
    def get_enemy_attack_range(self, enemy_type: str, default: float = 32.0) -> float:
        """Get enemy attack range."""
        return self._get_base_value(f"enemies.{enemy_type}.attack_range", default)
    
    def get_enemy_attack_cooldown(self, enemy_type: str, default: float = 1.0) -> float:
        """Get enemy attack cooldown."""
        return self._get_base_value(f"enemies.{enemy_type}.attack_cooldown", default)
    
    def get_enemy_ranged_damage(self, enemy_type: str, default: int = 8) -> int:
        """Get enemy ranged damage, applying difficulty multiplier."""
        damage = self._get_base_value(f"enemies.{enemy_type}.ranged_damage", default)
        mult = self._get_multiplier("enemy_damage")
        return int(damage * mult)
    
    def get_enemy_projectile_speed(self, enemy_type: str, default: float = 200.0) -> float:
        """Get enemy projectile speed."""
        return self._get_base_value(f"enemies.{enemy_type}.projectile_speed", default)
    
    def get_enemy_block_chance(self, enemy_type: str, default: float = 0.0) -> float:
        """Get enemy block chance."""
        return self._get_base_value(f"enemies.{enemy_type}.block_chance", default)
    
    def get_enemy_block_damage_reduction(self, enemy_type: str, default: float = 0.5) -> float:
        """Get enemy block damage reduction."""
        return self._get_base_value(f"enemies.{enemy_type}.block_damage_reduction", default)
    
    # ============ SURVIVORS ============
    
    def get_survivor_hp(self, survivor_type: str, default: int = 100) -> int:
        """Get survivor HP."""
        return self._get_base_value(f"survivors.{survivor_type}.hp", default)
    
    def get_survivor_speed(self, survivor_type: str, default: float = 90.0) -> float:
        """Get survivor speed."""
        return self._get_base_value(f"survivors.{survivor_type}.speed", default)
    
    def get_survivor_carry_capacity(self, survivor_type: str, default: int = 40) -> int:
        """Get survivor carry capacity."""
        return self._get_base_value(f"survivors.{survivor_type}.carry_capacity", default)
    
    def get_guard_range(self, default: float = 160.0) -> float:
        """Get guard attack range."""
        return self._get_base_value("survivors.guard.range", default)
    
    def get_guard_damage(self, default: int = 8) -> int:
        """Get guard damage."""
        return self._get_base_value("survivors.guard.ranged_dmg", default)
    
    def get_guard_cooldown(self, default: float = 0.8) -> float:
        """Get guard attack cooldown."""
        return self._get_base_value("survivors.guard.cooldown", default)
    
    # ============ WAVES ============
    
    def get_wave_nights(self) -> list:
        """Get wave night compositions."""
        nights = self._get_base_value("waves.nights", [])
        # Apply enemy count multiplier to each night's mix
        count_mult = self._get_multiplier("enemy_count")
        result = []
        for night in nights:
            new_mix = {}
            if "mix" in night:
                for enemy_type, count in night["mix"].items():
                    new_mix[enemy_type] = max(1, int(count * count_mult))
            result.append({"mix": new_mix})
        return result
    
    def get_wave_increment_mult(self) -> float:
        """Get wave increment multiplier."""
        return self._get_base_value("waves.increment.per_night_mult", 1.12)
    
    def get_spawn_interval(self) -> float:
        """Get spawn interval in seconds."""
        return self._get_base_value("waves.spawn.interval_sec", 1.0)
    
    def get_spawn_batch_size(self) -> int:
        """Get spawn batch size."""
        return self._get_base_value("waves.spawn.batch_size", 2)
    
    def get_day_duration(self) -> float:
        """Get day phase duration."""
        return self._get_base_value("waves.day_duration", 30.0)
    
    def get_summary_duration(self) -> float:
        """Get summary phase duration."""
        return self._get_base_value("waves.summary_duration", 5.0)
    
    def get_win_nights(self) -> int:
        """Get nights required to win."""
        return self._get_base_value("waves.win_nights", 10)
    
    # ============ NODES ============
    
    def get_node_yield_total(self, node_type: str, default: int = 100) -> int:
        """Get node total yield."""
        return self._get_base_value(f"nodes.{node_type}.yield_total", default)
    
    def get_node_gather_per_tick(self, node_type: str, default: int = 5) -> int:
        """Get node gather per tick."""
        return self._get_base_value(f"nodes.{node_type}.gather_per_tick", default)
    
    def get_node_tick_sec(self, node_type: str, default: float = 0.6) -> float:
        """Get node tick duration."""
        return self._get_base_value(f"nodes.{node_type}.tick_sec", default)
    
    def get_daily_spawn_trees(self) -> int:
        """Get daily tree spawn count."""
        return self._get_base_value("nodes.daily_spawn.trees", 4)
    
    def get_daily_spawn_scrap(self) -> int:
        """Get daily scrap spawn count."""
        return self._get_base_value("nodes.daily_spawn.scrap", 3)
    
    def get_daily_spawn_min_dist(self) -> int:
        """Get minimum distance from wall for node spawns."""
        return self._get_base_value("nodes.daily_spawn.min_dist_from_wall_px", 96)
    
    # ============ ECONOMY ============
    
    def get_coin_reward(self, enemy_type: str) -> int:
        """Get coin reward for enemy type, applying difficulty multiplier."""
        base_reward = self._get_base_value(f"economy.coin_rewards.{enemy_type}")
        if base_reward is None:
            base_reward = self._get_base_value("economy.coin_rewards.base_reward", 2)
        mult = self._get_multiplier("coin_rewards")
        return int(base_reward * mult)
    
    def get_hire_survivor_cost(self) -> int:
        """Get cost to hire a survivor, applying difficulty multiplier."""
        cost = self._get_base_value("economy.hire_survivor_cost", 50)
        # Hire cost scales with building cost multiplier
        mult = self._get_multiplier("building_cost")
        return int(cost * mult)
    
    def get_food_per_survivor_per_day(self) -> int:
        """Get food consumption per survivor per day."""
        return self._get_base_value("economy.food_per_survivor_per_day", 1)
    
    def get_starting_resources(self) -> Dict[str, int]:
        """Get starting resources for current difficulty."""
        diff_key = self._current_difficulty.name.lower()
        multipliers = self._config.get("difficulty_multipliers", {}).get(diff_key, {})
        return multipliers.get("starting_resources", {"wood": 300, "iron": 300, "food": 300})
    
    # ============ UPGRADES ============
    
    def get_upgrade_config(self) -> Dict[str, list]:
        """Get turret upgrade configuration, applying difficulty multiplier."""
        config = self._get_base_value("upgrades", {})
        mult = self._get_multiplier("upgrade_cost")
        result = {}
        for tier_key, steps in config.items():
            if tier_key == "steps_per_tier":
                result[tier_key] = steps
                continue
            new_steps = []
            for step in steps:
                new_step = step.copy()
                if "base_cost" in new_step:
                    new_step["base_cost"] = {
                        k: int(v * mult) for k, v in new_step["base_cost"].items()
                    }
                new_steps.append(new_step)
            result[tier_key] = new_steps
        return result
    
    def get_upgrade_steps_per_tier(self) -> int:
        """Get number of upgrade steps per tier."""
        return self._get_base_value("upgrades.steps_per_tier", 2)


# Global instance
_balance_config: Optional[BalanceConfig] = None


def get_balance_config() -> BalanceConfig:
    """Get the global balance config instance."""
    global _balance_config
    if _balance_config is None:
        _balance_config = BalanceConfig()
    return _balance_config

