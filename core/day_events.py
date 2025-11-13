"""
Day Random Event system for applying daily modifiers.
"""
import random
from typing import Optional, Dict

class DayEventManager:
    """Manages random daily events that apply temporary modifiers."""
    
    def __init__(self, world):
        """
        Initialize day event manager.
        Args:
            world: World object
        """
        self.world = world
        self.current_event: Optional[Dict] = None
        
        # Simple built-in events; we can move to JSON later if needed
        self.events = [
            {
                "id": "lucky_day",
                "name": "Lucky Day",
                "description": "Gathering yields +50% resources today.",
                "weight": 3,
                "effects": {"resource_prod_mult": 1.5}
            },
            {
                "id": "scrap_jackpot",
                "name": "Scrap Jackpot",
                "description": "Zombies drop +50% more coins today.",
                "weight": 3,
                "effects": {"coin_drop_mult": 1.5}
            },
            {
                "id": "exhausted_workers",
                "name": "Exhausted Workers",
                "description": "Production -25% today.",
                "weight": 2,
                "effects": {"resource_prod_mult": 0.75}
            },
            {
                "id": "supply_shortage",
                "name": "Supply Shortage",
                "description": "Building costs +25% resources today.",
                "weight": 2,
                "effects": {"build_cost_mult": 1.25}
            },
            {
                "id": "overclock_turrets",
                "name": "Overclock Turrets",
                "description": "Turrets fire 25% faster but take 10% more damage.",
                "weight": 2,
                "effects": {
                    "turret_fire_rate_mult": 0.75,
                    "building_damage_taken_mult": 1.1
                }
            },
            {
                "id": "foggy_day",
                "name": "Foggy Morning",
                "description": "Turret range -20% during the day.",
                "weight": 2,
                "effects": {"turret_range_mult": 0.80}
            },
            {
                "id": "bountiful_forest",
                "name": "Bountiful Forest",
                "description": "Extra tree nodes spawn today.",
                "weight": 3,
                "effects": {"node_spawn_bonus": True}
            },
            {
                "id": "rich_scrap",
                "name": "Rich Scrap Veins",
                "description": "More iron scrap nodes spawn today.",
                "weight": 3,
                "effects": {"node_spawn_bonus": True}
            },
            {
                "id": "hungry_zombies",
                "name": "Hungry Zombies",
                "description": "Zombies move +15% faster tonight.",
                "weight": 2,
                "effects": {"zombie_speed_mult": 1.15}
            },
            {
                "id": "weakened_undead",
                "name": "Weakened Undead",
                "description": "Zombies have -20% HP tonight.",
                "weight": 2,
                "effects": {"zombie_hp_mult": 0.80}
            },
            {
                "id": "stormy_weather",
                "name": "Stormy Weather",
                "description": "Random lightning strikes stun zombies.",
                "weight": 1,
                "effects": {"lightning_storm": True}
            },
            {
                "id": "supply_convoy",
                "name": "Supply Convoy",
                "description": "Free +50 wood and +25 iron delivered.",
                "weight": 1,
                "effects": {"grant_wood": 50, "grant_iron": 25}
            },
            {
                "id": "merchant_visit",
                "name": "Traveling Merchant",
                "description": "You gain +40 coins today.",
                "weight": 1,
                "effects": {"grant_coins": 40}
            },
            {
                "id": "reinforced_defenses",
                "name": "Reinforced Defenses",
                "description": "Buildings take -15% damage today.",
                "weight": 3,
                "effects": {"building_damage_taken_mult": 0.85}
            },
            {
                "id": "overwhelming_horde",
                "name": "Overwhelming Horde",
                "description": "Zombie spawn rate +30% tonight.",
                "weight": 2,
                "effects": {"zombie_spawn_mult": 1.30}
            },
            {
                "id": "broken_tools",
                "name": "Broken Tools",
                "description": "Production -40% today.",
                "weight": 2,
                "effects": {"resource_prod_mult": 0.60}
            }
        ]
    
    def _weighted_choice(self):
        """Choose a random event based on weights."""
        pool = []
        for ev in self.events:
            pool.extend([ev] * ev.get("weight", 1))
        return random.choice(pool) if pool else None
    
    def clear_event(self):
        """Clear current event and reset modifiers to neutral."""
        self.current_event = None
        # Reset modifiers to neutral
        if hasattr(self.world, 'modifiers'):
            self.world.modifiers = {
                "resource_prod_mult": 1.0,
                "coin_drop_mult": 1.0,
                "build_cost_mult": 1.0,
                "turret_fire_rate_mult": 1.0,
                "building_damage_taken_mult": 1.0,
                "zombie_spawn_mult": 1.0,
                "zombie_speed_mult": 1.0,
                "zombie_hp_mult": 1.0,
                "turret_range_mult": 1.0,
                "node_spawn_bonus": False,
                "lightning_storm": False
            }
    
    def roll_new_day_event(self, day_number: int) -> Optional[Dict]:
        """
        Roll a new random event for the day.
        Args:
            day_number: Current day number
        Returns:
            Event dict if event occurred, None otherwise
        """
        # Clear previous event
        self.clear_event()
        
        # 20% chance of no event
        if random.random() < 0.20:
            return None
        
        ev = self._weighted_choice()
        if not ev:
            return None
        
        self.current_event = ev
        
        # Apply effects to modifiers and handle grant effects
        for key, val in ev["effects"].items():
            if key.startswith("grant_"):
                # Handle grant effects (one-time resource grants)
                resource_type = key.replace("grant_", "")
                if resource_type == "wood" and hasattr(self.world, 'resources'):
                    self.world.resources.wood += val
                elif resource_type == "iron" and hasattr(self.world, 'resources'):
                    self.world.resources.iron += val
                elif resource_type == "coins" and hasattr(self.world, 'resources'):
                    self.world.resources.add_coins(val)
            else:
                # Regular modifier effects
                self.world.modifiers[key] = val
        
        # Build banner text using existing event banner system
        title = f"Day {day_number} – {ev['name']}"
        msg = ev["description"]
        
        # Use HUD's show_event method
        if hasattr(self.world, 'hud') and self.world.hud:
            self.world.hud.show_event(f"{title}: {msg}", duration=5.0)
        
        return ev

