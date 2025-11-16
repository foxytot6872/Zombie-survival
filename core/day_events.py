"""
Random Event system for applying daily and nightly modifiers.
"""
import random
from typing import Optional, Dict, List

from difficulty_config import Difficulty


# Difficulty-based weighting for event types
DIFFICULTY_EVENT_WEIGHTS: Dict[Difficulty, Dict[str, float]] = {
    # Easy mode: very forgiving
    Difficulty.EASY: {
        "positive": 0.70,
        "mixed": 0.20,
        "negative": 0.10,
    },
    # Medium: balanced
    Difficulty.MEDIUM: {
        "positive": 0.33,
        "mixed": 0.34,
        "negative": 0.33,
    },
    # Hard: punishing, negative events matter
    Difficulty.HARD: {
        "positive": 0.20,
        "mixed": 0.30,
        "negative": 0.50,
    },
    # Extreme: brutal, chaos-heavy
    Difficulty.EXTREME: {
        "positive": 0.12,
        "mixed": 0.28,
        "negative": 0.60,
    },
}


class DayEventManager:
    """Manages random daily and nightly events that apply temporary modifiers."""
    
    def __init__(self, world):
        """
        Initialize day event manager.
        Args:
            world: World object
        """
        self.world = world
        self.current_event: Optional[Dict] = None
        
        # Complete event list with all 30 events (10 positive, 10 mixed, 10 negative)
        # Each event defines:
        # - id: unique identifier
        # - name: title shown in popup
        # - description: text shown in popup
        # - type: "positive" | "mixed" | "negative"
        # - phase: "day" | "night" | "both"
        # - weight: probability weight for selection
        # - effects: dict of modifier keys and values
        self.events = [
            # ========== POSITIVE EVENTS (10 events) ==========
            {
                "id": "clear_skies",
                "name": "Clear Skies",
                "description": "Perfect weather increases resource gathering efficiency.",
                "type": "positive",
                "phase": "day",
                "weight": 3,
                "effects": {"gather_bonus_per_node": 1}  # +1 resource per gather
            },
            {
                "id": "found_stash",
                "name": "Found Survivors' Stash",
                "description": "You discover a hidden cache of supplies.",
                "type": "positive",
                "phase": "day",
                "weight": 2,
                "effects": {"grant_food": 3, "grant_wood": 2}
            },
            {
                "id": "well_fed_morning",
                "name": "Well-Fed Morning",
                "description": "Your survivors wake up energized and efficient.",
                "type": "positive",
                "phase": "day",
                "weight": 2,
                "effects": {"survivor_gather_speed_mult": 1.10}  # +10% gather efficiency
            },
            {
                "id": "abandoned_toolbox",
                "name": "Abandoned Toolbox",
                "description": "You find useful tools left behind.",
                "type": "positive",
                "phase": "day",
                "weight": 2,
                "effects": {"grant_iron": 2}
            },
            {
                "id": "lucky_recruit",
                "name": "Lucky Recruit",
                "description": "A new survivor joins your colony.",
                "type": "positive",
                "phase": "day",
                "weight": 1,
                "effects": {"grant_survivor": 1}  # Add +1 survivor
            },
            {
                "id": "repaired_walls",
                "name": "Repaired Walls",
                "description": "Your walls have been reinforced overnight.",
                "type": "positive",
                "phase": "day",
                "weight": 2,
                "effects": {"wall_hp_bonus": 5}  # All walls +5 HP
            },
            {
                "id": "farm_bloom",
                "name": "Farm Bloom",
                "description": "Your farm produces extra food today.",
                "type": "positive",
                "phase": "day",
                "weight": 2,
                "effects": {"farm_food_bonus": 2}  # Farm produces +2 bonus Food
            },
            {
                "id": "quiet_night",
                "name": "Quiet Night",
                "description": "The zombie horde seems weaker tonight.",
                "type": "positive",
                "phase": "night",
                "weight": 2,
                "effects": {"zombie_wave_size_mult": 0.90}  # Wave size -10%
            },
            {
                "id": "bright_moon",
                "name": "Bright Moon",
                "description": "Excellent visibility improves turret accuracy.",
                "type": "positive",
                "phase": "night",
                "weight": 2,
                "effects": {"turret_accuracy_mult": 1.05}  # Turrets +5% accuracy
            },
            {
                "id": "green_forest_regrowth",
                "name": "Green Forest Regrowth",
                "description": "Nature provides extra wood resources.",
                "type": "positive",
                "phase": "day",
                "weight": 2,
                "effects": {"extra_wood_nodes": 2}  # Spawn +2 extra wood nodes
            },
            
            # ========== MIXED EVENTS (10 events) ==========
            {
                "id": "calm_day",
                "name": "Calm Day",
                "description": "A peaceful day with no significant events.",
                "type": "mixed",
                "phase": "day",
                "weight": 10,
                "effects": {}  # No effect
            },
            {
                "id": "cold_breeze",
                "name": "Cold Breeze",
                "description": "Chilly weather slows survivors but clears the air.",
                "type": "mixed",
                "phase": "day",
                "weight": 2,
                "effects": {
                    "survivor_speed_mult": 0.95,  # -5% survivor speed
                    "turret_accuracy_mult": 1.05  # +5% turret accuracy
                }
            },
            {
                "id": "foggy_morning",
                "name": "Foggy Morning",
                "description": "Thick fog reduces visibility but provides cover.",
                "type": "mixed",
                "phase": "day",
                "weight": 2,
                "effects": {
                    "survivor_stealth_bonus": 0.10,  # +10% stealth (flavor only for now)
                    "turret_range_mult": 0.90  # -10% turret range
                }
            },
            {
                "id": "uninspired_mood",
                "name": "Uninspired Mood",
                "description": "A quiet, uneventful day passes by.",
                "type": "mixed",
                "phase": "day",
                "weight": 10,
                "effects": {}  # Flavor only
            },
            {
                "id": "wanderer_at_gate",
                "name": "Wanderer at the Gate",
                "description": "A traveler passes by but doesn't stay.",
                "type": "mixed",
                "phase": "day",
                "weight": 1,
                "effects": {}  # Flavor only
            },
            {
                "id": "light_drizzle",
                "name": "Light Drizzle",
                "description": "A gentle rain falls, providing no gameplay effect.",
                "type": "mixed",
                "phase": "day",
                "weight": 10,
                "effects": {}  # No gameplay effect
            },
            {
                "id": "uneventful_night",
                "name": "Uneventful Night",
                "description": "A quiet night with no unusual occurrences.",
                "type": "mixed",
                "phase": "night",
                "weight": 10,
                "effects": {}  # No effect
            },
            {
                "id": "birds_singing",
                "name": "Birds Singing",
                "description": "The sound of birds brings a sense of peace.",
                "type": "mixed",
                "phase": "day",
                "weight": 5,
                "effects": {}  # Flavor only
            },
            {
                "id": "mild_wind",
                "name": "Mild Wind",
                "description": "A gentle breeze rustles the trees.",
                "type": "mixed",
                "phase": "day",
                "weight": 10,
                "effects": {}  # Flavor only
            },
            {
                "id": "tired_workers",
                "name": "Tired Workers",
                "description": "Workers move slower but find more resource nodes.",
                "type": "mixed",
                "phase": "day",
                "weight": 2,
                "effects": {
                    "survivor_gather_speed_mult": 0.95,  # -5% gather speed
                    "node_spawn_bonus": True  # +5% resource node spawn chance (flavor)
                }
            },
            
            # ========== NEGATIVE EVENTS (10 events) ==========
            {
                "id": "food_spoilage",
                "name": "Food Spoilage",
                "description": "Some of your food has spoiled.",
                "type": "negative",
                "phase": "day",
                "weight": 2,
                "effects": {"grant_food": -2}  # -2 Food
            },
            {
                "id": "storm_damage",
                "name": "Storm Damage",
                "description": "A violent storm damages one of your buildings.",
                "type": "negative",
                "phase": "day",
                "weight": 1,
                "effects": {"random_building_damage": 5}  # Random building -5 HP
            },
            {
                "id": "broken_tools_event",
                "name": "Broken Tools",
                "description": "Some of your tools break beyond repair.",
                "type": "negative",
                "phase": "day",
                "weight": 2,
                "effects": {"grant_iron": -1}  # -1 Iron
            },
            {
                "id": "farm_pest_attack",
                "name": "Farm Pest Attack",
                "description": "Pests damage your crops.",
                "type": "negative",
                "phase": "day",
                "weight": 2,
                "effects": {"farm_food_bonus": -1}  # Farm production -1 today
            },
            {
                "id": "low_morale",
                "name": "Low Morale",
                "description": "Your survivors work slower due to low spirits.",
                "type": "negative",
                "phase": "day",
                "weight": 2,
                "effects": {"survivor_gather_speed_mult": 0.90}  # -10% gather speed
            },
            {
                "id": "supply_theft",
                "name": "Supply Theft",
                "description": "Some of your supplies go missing.",
                "type": "negative",
                "phase": "day",
                "weight": 2,
                "effects": {"grant_wood": -2}  # -2 Wood
            },
            {
                "id": "harsh_winds",
                "name": "Harsh Winds",
                "description": "Strong winds reduce turret accuracy tonight.",
                "type": "negative",
                "phase": "night",
                "weight": 2,
                "effects": {"turret_accuracy_mult": 0.95}  # Turrets -5% accuracy
            },
            {
                "id": "uneasy_night",
                "name": "Uneasy Night",
                "description": "The zombie horde seems larger tonight.",
                "type": "negative",
                "phase": "night",
                "weight": 2,
                "effects": {"zombie_wave_size_mult": 1.05}  # Wave +5% size
            },
            {
                "id": "heavy_fog",
                "name": "Heavy Fog",
                "description": "Dense fog reduces turret visibility tonight.",
                "type": "negative",
                "phase": "night",
                "weight": 2,
                "effects": {"turret_range_mult": 0.90}  # -10% turret range
            },
            {
                "id": "injured_survivor",
                "name": "Injured Survivor",
                "description": "One of your survivors is injured and cannot work today.",
                "type": "negative",
                "phase": "day",
                "weight": 1,
                "effects": {"injured_survivor": 1}  # Random survivor cannot gather today
            },
        ]
    
    def _get_current_difficulty(self) -> Difficulty:
        """Resolve current difficulty from world, defaulting to MEDIUM."""
        diff = getattr(self.world, "current_difficulty", Difficulty.MEDIUM)
        # Ensure it's a Difficulty enum
        if not isinstance(diff, Difficulty):
            try:
                diff = Difficulty[ str(diff).upper() ]
            except Exception:
                diff = Difficulty.MEDIUM
        return diff

    def _choose_event(self, phase: str) -> Optional[Dict]:
        """
        Choose a random event based on difficulty-weighted event type and phase.
        phase: "day" or "night"
        """
        # Determine difficulty weights
        difficulty = self._get_current_difficulty()
        type_weights = DIFFICULTY_EVENT_WEIGHTS.get(difficulty, DIFFICULTY_EVENT_WEIGHTS[Difficulty.MEDIUM])

        # First choose an event type based on weights
        event_types: List[str] = ["positive", "mixed", "negative"]
        total_weight = sum(type_weights[t] for t in event_types)
        r = random.random() * total_weight
        accum = 0.0
        chosen_type = "positive"
        for t in event_types:
            accum += type_weights[t]
            if r <= accum:
                chosen_type = t
                break

        # Filter events by chosen type and phase
        candidates = [
            ev for ev in self.events
            if ev.get("type") == chosen_type and ev.get("phase") in (phase, "both")
        ]

        # Fallback: any event for this phase if none of chosen type
        if not candidates:
            candidates = [
                ev for ev in self.events
                if ev.get("phase") in (phase, "both")
            ]

        if not candidates:
            return None

        # Use per-event weight within chosen bucket
        pool: List[Dict] = []
        for ev in candidates:
            pool.extend([ev] * ev.get("weight", 1))

        return random.choice(pool) if pool else None
    
    def clear_event(self):
        """Clear current event and reset modifiers to neutral."""
        self.current_event = None
        # Reset modifiers to neutral (day event modifiers only, no research modifiers)
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
                "turret_accuracy_mult": 1.0,
                "survivor_gather_speed_mult": 1.0,
                "survivor_speed_mult": 1.0,
                "survivor_stealth_bonus": 0.0,
                "zombie_wave_size_mult": 1.0,
                "gather_bonus_per_node": 0,
                "node_spawn_bonus": False,
                "lightning_storm": False,
                "wall_hp_bonus": 0,
                "farm_food_bonus": 0,
                "extra_wood_nodes": 0,
                "injured_survivor": 0,
                "random_building_damage": 0
            }
        # Mark research modifiers as dirty so they get recalculated
        if hasattr(self.world, 'research') and hasattr(self.world.research, '_modifiers_dirty'):
            self.world.research._modifiers_dirty = True
    
    def _apply_event_effects(self, ev: Dict):
        """Apply event effects to the world."""
        if not ev.get("effects"):
            return
        
        effects = ev["effects"]
        
        # Handle resource grants/penalties
        if "grant_wood" in effects:
            if hasattr(self.world, 'resources'):
                self.world.resources.wood += effects["grant_wood"]
        if "grant_iron" in effects:
            if hasattr(self.world, 'resources'):
                self.world.resources.iron += effects["grant_iron"]
        if "grant_food" in effects:
            if hasattr(self.world, 'resources'):
                self.world.resources.food += effects["grant_food"]
        if "grant_coins" in effects:
            if hasattr(self.world, 'resources'):
                self.world.resources.add_coins(effects["grant_coins"])
        
        # Handle survivor addition
        if "grant_survivor" in effects:
            # This will be handled in main.py where survivor_group is accessible
            self.world.modifiers["grant_survivor"] = effects["grant_survivor"]
        
        # Handle wall HP bonus
        if "wall_hp_bonus" in effects:
            # This will be handled in main.py where building_group is accessible
            self.world.modifiers["wall_hp_bonus"] = effects["wall_hp_bonus"]
        
        # Handle farm food bonus
        if "farm_food_bonus" in effects:
            self.world.modifiers["farm_food_bonus"] = effects["farm_food_bonus"]
        
        # Handle extra wood nodes
        if "extra_wood_nodes" in effects:
            self.world.modifiers["extra_wood_nodes"] = effects["extra_wood_nodes"]
        
        # Handle injured survivor
        if "injured_survivor" in effects:
            # This will be handled in main.py where survivor_group is accessible
            self.world.modifiers["injured_survivor"] = effects["injured_survivor"]
        
        # Handle random building damage
        if "random_building_damage" in effects:
            # This will be handled in main.py where building_group is accessible
            self.world.modifiers["random_building_damage"] = effects["random_building_damage"]
        
        # Handle all modifier multipliers
        for key in ["resource_prod_mult", "coin_drop_mult", "build_cost_mult",
                    "turret_fire_rate_mult", "building_damage_taken_mult",
                    "zombie_spawn_mult", "zombie_speed_mult", "zombie_hp_mult",
                    "turret_range_mult", "turret_accuracy_mult",
                    "survivor_gather_speed_mult", "survivor_speed_mult",
                    "survivor_stealth_bonus", "zombie_wave_size_mult",
                    "gather_bonus_per_node", "node_spawn_bonus", "lightning_storm"]:
            if key in effects:
                self.world.modifiers[key] = effects[key]
    
    def roll_new_day_event(self, day_number: int, phase: str = "day") -> Optional[Dict]:
        """
        Roll a new random event for the given phase (LUCK-BASED SYSTEM).
        Always rolls an event type (positive/mixed/negative) based on difficulty.
        Args:
            day_number: Current day/night number
            phase: "day" or "night"
        Returns:
            Event dict if event occurred, None otherwise
        """
        # Clear previous event
        self.clear_event()
        
        # LUCK ROLL: Always choose an event type based on difficulty weights
        ev = self._choose_event(phase=phase)
        
        # Handle Mixed events (neutral day/night) with no effects
        if ev and ev.get("type") == "mixed" and not ev.get("effects"):
            # Pure mixed event with no effects = neutral day
            if hasattr(self.world, 'hud') and self.world.hud:
                phase_label = "day" if phase == "day" else "night"
                title = "Calm Day" if phase == "day" else "Uneventful Night"
                desc_map = {
                    "calm_day": "A peaceful day with no significant events.",
                    "uninspired_mood": "A quiet, uneventful day passes by.",
                    "light_drizzle": "A gentle rain falls, providing no gameplay effect.",
                    "uneventful_night": "A quiet night with no unusual occurrences.",
                    "birds_singing": "The sound of birds brings a sense of peace.",
                    "mild_wind": "A gentle breeze rustles the trees.",
                    "wanderer_at_gate": "A traveler passes by but doesn't stay."
                }
                description = desc_map.get(ev.get("id"), f"A normal {phase_label} passes with no unusual events.")
                
                self.world.hud.show_event(
                    text=f"{title}: {description}",
                    duration=3.5,
                    title=title,
                    description=description,
                    effects=[],
                    event_type="mixed"
                )
            return ev  # Return event but don't apply any effects
        
        if not ev:
            # Fallback: create a neutral mixed event if no events available
            if hasattr(self.world, 'hud') and self.world.hud:
                phase_label = "day" if phase == "day" else "night"
                self.world.hud.show_event(
                    text=f"A normal {phase_label} passes with no unusual events.",
                    duration=3.5,
                    title="Normal Day" if phase == "day" else "Normal Night",
                    description=f"A normal {phase_label} passes with no unusual events.",
                    effects=[],
                    event_type="mixed"
                )
            return None
        
        self.current_event = ev
        
        # Apply event effects
        self._apply_event_effects(ev)
        
        # Build event popup with improved formatting
        title = ev['name']
        description = ev.get("description", "")
        event_type = ev.get("type", "mixed")
        
        # Format effects list for display (only if event has effects)
        effects_display = []
        if ev.get("effects"):
            for key, val in ev["effects"].items():
                if key.startswith("grant_"):
                    resource_type = key.replace("grant_", "").title()
                    if val > 0:
                        effects_display.append(f"+{val} {resource_type}")
                    else:
                        effects_display.append(f"{val} {resource_type}")  # Negative already has minus sign
                elif key == "resource_prod_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Resource Production")
                    else:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Resource Production")
                elif key == "coin_drop_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Coin Drops")
                elif key == "build_cost_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Building Costs")
                elif key == "turret_fire_rate_mult":
                    if val < 1.0:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"+{pct}% Turret Fire Rate")
                elif key == "building_damage_taken_mult":
                    if val < 1.0:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Building Damage Taken")
                    elif val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Building Damage Taken")
                elif key == "zombie_spawn_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Zombie Spawn Rate")
                elif key == "zombie_speed_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Zombie Speed")
                elif key == "zombie_hp_mult":
                    if val < 1.0:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Zombie HP")
                elif key == "turret_range_mult":
                    if val < 1.0:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Turret Range")
                elif key == "turret_accuracy_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Turret Accuracy")
                    else:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Turret Accuracy")
                elif key == "survivor_gather_speed_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Gather Efficiency")
                    else:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Gather Efficiency")
                elif key == "survivor_speed_mult":
                    if val < 1.0:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Survivor Speed")
                    else:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Survivor Speed")
                elif key == "zombie_wave_size_mult":
                    if val > 1.0:
                        pct = int((val - 1.0) * 100)
                        effects_display.append(f"+{pct}% Zombie Wave Size")
                    else:
                        pct = int((1.0 - val) * 100)
                        effects_display.append(f"-{pct}% Zombie Wave Size")
                elif key == "gather_bonus_per_node":
                    effects_display.append(f"+{val} Resource per Gather")
                elif key == "wall_hp_bonus":
                    effects_display.append(f"+{val} HP to All Walls")
                elif key == "farm_food_bonus":
                    if val > 0:
                        effects_display.append(f"+{val} Bonus Farm Food")
                    else:
                        effects_display.append(f"{val} Farm Food Production")
                elif key == "extra_wood_nodes":
                    effects_display.append(f"+{val} Extra Wood Nodes")
                elif key == "grant_survivor":
                    effects_display.append(f"+{val} Survivor")
                elif key == "injured_survivor":
                    effects_display.append("1 Survivor Injured (Cannot Work)")
                elif key == "random_building_damage":
                    effects_display.append(f"-{val} HP to Random Building")
                elif key == "node_spawn_bonus":
                    if val:
                        effects_display.append("Extra Resource Nodes Spawn")
                elif key == "lightning_storm":
                    if val:
                        effects_display.append("Lightning Strikes Stun Zombies")
        
        # Use HUD's improved show_event method with formatted popup
        if hasattr(self.world, 'hud') and self.world.hud:
            self.world.hud.show_event(
                text=f"{title}: {description}",
                duration=4.0,  # 3-4 seconds as required
                title=title,
                description=description,
                effects=effects_display,
                event_type=event_type,
            )
        
        return ev
