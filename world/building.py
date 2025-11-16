from __future__ import annotations
import pygame
import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List, Union

from difficulty_config import Difficulty
from economy import scale_cost

TILE = 32

@dataclass
class Cost:
    wood: int = 0
    iron: int = 0
    food: int = 0
    coins: int = 0

@dataclass
class Production:
    wood_per_min: float = 0.0
    iron_per_min: float = 0.0
    food_per_min: float = 0.0

class BuildState:
    PLANNING = "planning"           # ghost preview (no payment yet)
    CONSTRUCTING = "constructing"   # paid; build_time progressing
    ACTIVE = "active"               # finished
    DESTROYED = "destroyed"

class Building(pygame.sprite.Sprite):
    """
    Base class for all buildings. Subclasses should override:
      - TYPE_ID (string)
      - BASE_HP, BUILD_TIME, COST, FOOTPRINT (w,h), TIER_MAX
      - draw_body(surface) if custom rendering is needed
      - on_complete(), on_destroy(), on_upgrade()
    """
    TYPE_ID: str = "building"
    BASE_HP: int = 200
    BUILD_TIME: float = 3.0  # seconds
    COST: Cost = Cost()
    FOOTPRINT: Tuple[int,int] = (1,1)  # in tiles (w,h)
    TIER_MAX: int = 3
    PASSIVE: Production = Production()  # per minute when ACTIVE
    ALLOW_MAX_TIER_PROGRESS: bool = False

    # Load config from JSON if available (per-class, not per-instance)
    _config_cache = {}  # Class-level cache: {class_name: config_data}

    @classmethod
    def _load_config(cls):
        """Load building config from JSON file (per building class)"""
        # Use class name as cache key to allow per-class config
        class_key = cls.__name__
        if class_key in cls._config_cache:
            return
        
        # Initialize empty config for this class
        cls._config_cache[class_key] = {}
        
        # Try to load from buildings.json first (general config)
        try:
            with open('data/config/buildings.json', 'r') as f:
                all_config = json.load(f)
                # Get config for this building type
                building_key = cls.TYPE_ID.replace('_', '')  # turret_ballistic -> turretballistic
                # Also try without underscores
                if cls.TYPE_ID in all_config:
                    cls._config_cache[class_key] = all_config[cls.TYPE_ID]
                elif building_key in all_config:
                    cls._config_cache[class_key] = all_config[building_key]
                else:
                    # Try partial match (e.g., "turret" matches "turret_ballistic")
                    for key in all_config.keys():
                        if key in cls.TYPE_ID or cls.TYPE_ID in key:
                            cls._config_cache[class_key] = all_config[key]
                            break
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Warning: Could not load building config for {cls.TYPE_ID}: {e}")
        
        # Also check walls.json for wall types (wall_wood, wall_iron)
        if cls.TYPE_ID in ("wall_wood", "wall_iron"):
            try:
                with open('data/config/walls.json', 'r') as f:
                    walls_config = json.load(f)
                    if cls.TYPE_ID in walls_config:
                        # Merge with existing config (walls.json takes precedence)
                        if class_key in cls._config_cache:
                            cls._config_cache[class_key].update(walls_config[cls.TYPE_ID])
                        else:
                            cls._config_cache[class_key] = walls_config[cls.TYPE_ID]
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Warning: Could not load wall config from walls.json for {cls.TYPE_ID}: {e}")

    @classmethod
    def _get_config_value(cls, key: str, default):
        """Get a config value from JSON, falling back to default"""
        cls._load_config()
        class_key = cls.__name__
        config_data = cls._config_cache.get(class_key, {})
        if key in config_data:
            if key == "cost" and isinstance(config_data[key], dict):
                return Cost(**config_data[key])
            elif key == "production" and isinstance(config_data[key], dict):
                return Production(**config_data[key])
            return config_data[key]
        return default

    def __init__(self, grid_pos: Tuple[int,int], tier: int = 1, uid: Optional[str] = None, world=None):
        # Production batch system
        self.production_timer: float = 0.0  # Timer for batch production
        self.production_interval: float = 5.0  # Seconds between batches
        self.base_batch_amount: int = 50  # Base amount per batch (scales with tier)
        
        # Initialize pygame sprite
        pygame.sprite.Sprite.__init__(self)
        self.uid = uid or str(uuid.uuid4())
        self.grid_x, self.grid_y = grid_pos
        self.level = 1
        self.level_sprites: Dict[int, Union[pygame.Surface, List[pygame.Surface]]] = {}
        self.animation_frames: List[pygame.Surface] = []
        
        # Store world reference for collision map access
        self.world = world
        
        # Load config overrides
        self._load_config()
        base_hp = self._get_config_value("base_hp", self.BASE_HP)
        build_time = self._get_config_value("build_time", self.BUILD_TIME)
        cost = self._get_config_value("cost", self.COST)
        production = self._get_config_value("production", self.PASSIVE)
        
        self.tier = tier
        self.state = BuildState.CONSTRUCTING
        self.progress = 0.0
        self.upgrade_progress = 0  # 0-2, where 2 upgrades = tier increase
        # Store as instance attributes (may differ from class defaults due to config)
        self.BUILD_TIME = build_time if isinstance(build_time, (int, float)) else self.BUILD_TIME
        self.BASE_HP = base_hp if isinstance(base_hp, int) else self.BASE_HP
        # COST and PASSIVE are class attributes, use them as fallback
        self.COST = cost if isinstance(cost, Cost) else self.COST
        self.PASSIVE = production if isinstance(production, Production) else self.PASSIVE
        
        # Calculate base max_hp from tier (modifiers applied when building becomes active)
        base_max_hp = int(self.BASE_HP * (1 + 0.15*(tier-1)))
        self.max_hp = base_max_hp
        self.hp = 1
        
        # Attacker slot tracking for load balancing
        self.attacker_count = 0
        
        # world position (center of base footprint)
        w, h = self.FOOTPRINT
        cx = (self.grid_x + w/2)*TILE
        cy = (self.grid_y + h/2)*TILE
        self.pos = pygame.Vector2(cx, cy)
        
        # rendering
        # rect represents the footprint area (top-left aligned)
        pixel_w = w * TILE
        pixel_h = h * TILE
        self.rect = pygame.Rect(self.grid_x * TILE, self.grid_y * TILE, pixel_w, pixel_h)
        self.image = pygame.Surface((pixel_w, pixel_h), pygame.SRCALPHA)

    # ------------------------------------------------------------------
    # Dynamic sprite / level support
    # ------------------------------------------------------------------
    def upgrade_level(self, new_level: int):
        """Upgrade building appearance level."""
        if new_level <= 0:
            new_level = 1
        if new_level == self.level:
            return
        self.level = new_level
        self.update_sprite()

    def update_sprite(self):
        """Update sprite based on current level (supports static or sheet)."""
        if not self.level_sprites:
            return

        sprite_data = self.level_sprites.get(self.level)
        if sprite_data is None:
            # Fall back to highest available level
            max_level = max(self.level_sprites.keys())
            sprite_data = self.level_sprites.get(max_level)
            if sprite_data is None:
                return

        if isinstance(sprite_data, list):
            if not sprite_data:
                return
            self.animation_frames = [frame.copy() for frame in sprite_data]
            new_image = self.animation_frames[0]
        else:
            self.animation_frames = []
            new_image = sprite_data.copy()

        self.image = new_image
        # Keep rect as footprint area - don't change it based on sprite size

    # ------------------------------------------------------------------
    # Dynamic sprite / level support
    # ------------------------------------------------------------------
    def upgrade_level(self, new_level: int):
        """Upgrade building appearance level."""
        if new_level <= 0:
            new_level = 1
        if new_level == self.level:
            return
        self.level = new_level
        self.update_sprite()

    def update_sprite(self):
        """Update sprite based on current level (supports static or sheet)."""
        if not self.level_sprites:
            return

        sprite_data = self.level_sprites.get(self.level)
        if sprite_data is None:
            # Fall back to highest available level
            max_level = max(self.level_sprites.keys())
            sprite_data = self.level_sprites.get(max_level)
            if sprite_data is None:
                return

        center = self.rect.center if hasattr(self, "rect") else (self.pos.x, self.pos.y)

        if isinstance(sprite_data, list):
            if not sprite_data:
                return
            self.animation_frames = [frame.copy() for frame in sprite_data]
            new_image = self.animation_frames[0]
        else:
            self.animation_frames = []
            new_image = sprite_data.copy()

        self.image = new_image
        self.rect = self.image.get_rect(center=center)

    # ----- Placement & Economy -----
    @classmethod
    def can_place(cls, grid, grid_pos: Tuple[int,int], building_group=None) -> bool:
        """Return True if footprint fits and tiles are free/buildable."""
        w, h = cls.FOOTPRINT
        gx, gy = grid_pos
        # bounds
        if gx < 0 or gy < 0 or gx+w > grid.width or gy+h > grid.height:
            return False
        # blocked tiles? (for placement, gates still block even though they're passable)
        for x in range(gx, gx+w):
            for y in range(gy, gy+h):
                # Check if tile is blocked (for placement, don't check passable - gates block placement)
                if grid.is_blocked(x, y, check_passable=False, building_group=None):
                    return False
                # Also check if there's an active building at this position
                if building_group:
                    for building in building_group:
                        if (hasattr(building, 'grid_x') and hasattr(building, 'grid_y') and
                            building.grid_x == x and building.grid_y == y and
                            hasattr(building, 'state')):
                            from world.building import BuildState
                            # Don't allow placement on active or constructing buildings (even passable ones)
                            if building.state in (BuildState.ACTIVE, BuildState.CONSTRUCTING):
                                return False
        return True

    @classmethod
    def get_cost(cls) -> Cost:
        cls._load_config()
        cost = cls._get_config_value("cost", cls.COST)
        if isinstance(cost, dict):
            return Cost(**cost)
        return cost if isinstance(cost, Cost) else cls.COST

    @classmethod
    def get_scaled_cost(cls, world=None, difficulty: Optional[Difficulty] = None) -> Cost:
        base_cost = cls.get_cost()
        if difficulty is None:
            if world and hasattr(world, "current_difficulty"):
                difficulty = world.current_difficulty
            else:
                difficulty = Difficulty.EASY
        scaled_dict = scale_cost(
            {"wood": base_cost.wood, "iron": base_cost.iron, "food": base_cost.food, "coins": base_cost.coins},
            difficulty,
            cost_type="build",
        )
        cost_mult = 1.0
        if world and hasattr(world, 'modifiers'):
            cost_mult = world.modifiers.get("build_cost_mult", 1.0)
        return Cost(
            wood=int(scaled_dict.get("wood", 0) * cost_mult),
            iron=int(scaled_dict.get("iron", 0) * cost_mult),
            food=int(scaled_dict.get("food", 0) * cost_mult),
            coins=scaled_dict.get("coins", 0),
        )

    @classmethod
    def pay_cost(cls, resources, world=None) -> bool:
        """Try deducting resources; return True if success (with difficulty/day-event modifiers)."""
        c = cls.get_scaled_cost(world=world)
        if (
            resources.wood < c.wood
            or resources.iron < c.iron
            or resources.food < c.food
            or resources.coins < c.coins
        ):
            return False
        resources.wood -= c.wood
        resources.iron -= c.iron
        resources.food -= c.food
        if c.coins:
            resources.coins -= c.coins
        return True

    def refund_cost(self, resources, ratio: float = 1.0, world=None):
        """Refund cost using this building's cost (instance method)."""
        # Use instance COST if available (set in __init__), otherwise use class method
        c = self.COST
        # Apply building refund modifier
        if world and hasattr(world, 'modifiers'):
            refund_mult = world.modifiers.get("building_refund_mult", 1.0)
            ratio = ratio * refund_mult
        resources.wood += int(c.wood * ratio)
        resources.iron += int(c.iron * ratio)
        resources.food += int(c.food * ratio)
        if hasattr(c, "coins") and c.coins:
            resources.coins += int(c.coins * ratio)

    # ----- Lifecycle -----
    def start_construction(self):
        self.state = BuildState.CONSTRUCTING
        self.progress = 0.0
        # Apply HP modifiers when construction starts (world should be available)
        self._apply_hp_modifiers()
        self.hp = max(1, int(0.1*self.max_hp))  # vulnerable during build
    
    def _apply_hp_modifiers(self):
        """Apply HP modifiers from research/day events"""
        # Calculate base max_hp from tier
        base_max_hp = int(self.BASE_HP * (1 + 0.15*(self.tier-1)))
        # Apply HP modifiers if world is available
        world = getattr(self, 'world', None)
        if world and hasattr(world, 'modifiers'):
            building_hp_mult = world.modifiers.get("building_hp_mult", 1.0)
            # Check if this is a turret and apply turret_hp_mult
            if hasattr(self, 'TYPE_ID') and 'turret' in self.TYPE_ID:
                turret_hp_mult = world.modifiers.get("turret_hp_mult", 1.0)
                self.max_hp = int(base_max_hp * building_hp_mult * turret_hp_mult)
            # Check if this is a wall and apply wall_hp_mult as well
            elif hasattr(self, 'TYPE_ID') and self.TYPE_ID.startswith('wall'):
                wall_hp_mult = world.modifiers.get("wall_hp_mult", 1.0)
                self.max_hp = int(base_max_hp * building_hp_mult * wall_hp_mult)
            else:
                self.max_hp = int(base_max_hp * building_hp_mult)
        else:
            self.max_hp = base_max_hp

    def update(self, dt: float, world=None):
        if self.state == BuildState.CONSTRUCTING:
            self.progress += dt
            if self.progress >= self.BUILD_TIME:
                self.progress = self.BUILD_TIME
                self.state = BuildState.ACTIVE
                self.hp = self.max_hp
                self.on_complete(world)

        elif self.state == BuildState.ACTIVE:
            # Batch-based production system
            if world and hasattr(world, "resources"):
                # Update production timer
                self.production_timer += dt
                
                # Calculate tier multiplier for batch amount
                tier_mult = 1.0 + 0.2 * (self.tier - 1)  # Tier 1: 1.0x, Tier 2: 1.2x, Tier 3: 1.4x
                
                # Apply resource production modifier from day events/research
                prod_mult = world.modifiers.get("resource_prod_mult", 1.0) if hasattr(world, 'modifiers') else 1.0
                
                # Check if it's time to produce a batch
                if self.production_timer >= self.production_interval:
                    # Calculate batch amount (scaled by tier, difficulty, and modifiers)
                    type_id = getattr(self, "TYPE_ID", "").lower()
                    prod_multiplier = 1.0
                    if hasattr(world, "production_multipliers"):
                        if type_id == "sawmill":
                            prod_multiplier = world.production_multipliers.get("sawmill", 1.0)
                        elif type_id == "smelter":
                            prod_multiplier = world.production_multipliers.get("smelter", 1.0)
                    batch_amount = int(self.base_batch_amount * tier_mult * prod_mult * prod_multiplier)
                    
                    # Get what this building produces
                    p = self._current_production()
                    
                    # Prevent NaN values
                    import math
                    if not math.isnan(batch_amount) and not math.isinf(batch_amount) and batch_amount > 0:
                        # Give resources based on what this building produces
                        if p.wood_per_min > 0:
                            world.resources.wood += batch_amount
                        if p.iron_per_min > 0:
                            world.resources.iron += batch_amount
                        if p.food_per_min > 0:
                            # Apply farm food bonus from day events
                            farm_bonus = 0
                            if hasattr(world, 'modifiers'):
                                farm_bonus = world.modifiers.get("farm_food_bonus", 0)
                            world.resources.food += batch_amount + farm_bonus
                    
                    # Reset timer (keep remainder for smooth timing)
                    self.production_timer -= self.production_interval

    def take_damage(self, amount: int, world=None):
        if self.state not in (BuildState.CONSTRUCTING, BuildState.ACTIVE):
            return
        # Apply building damage taken modifier from day events
        if world and hasattr(world, 'modifiers'):
            damage_mult = world.modifiers.get("building_damage_taken_mult", 1.0)
            amount = int(amount * damage_mult)
        self.hp -= amount
        
        if self.hp <= 0:
            self.hp = 0
            self.state = BuildState.DESTROYED
            self.on_destroy()

    def repair(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def upgrade(self, world=None) -> bool:
        """Upgrade building - increments progress, increases tier when progress reaches 3"""
        allow_max_progress = getattr(self, "ALLOW_MAX_TIER_PROGRESS", False)
        if self.tier >= self.TIER_MAX:
            if allow_max_progress:
                if not hasattr(self, 'upgrade_progress'):
                    self.upgrade_progress = 0
                if self.upgrade_progress >= 2:  # Changed from 3 to 2
                    return False
                self.upgrade_progress += 1
                self.on_upgrade()
                return True
            return False
        
        # Initialize upgrade_progress if not set (backwards compatibility)
        if not hasattr(self, 'upgrade_progress'):
            self.upgrade_progress = 0
        
        # Increment upgrade progress
        self.upgrade_progress += 1
        
        # When progress reaches 2, actually upgrade the tier (changed from 3 to 2)
        if self.upgrade_progress >= 2:
            self.tier += 1
            self.upgrade_progress = 0  # Reset progress for next tier
            # Recalculate max_hp with modifiers when upgrading
            base_max_hp = int(self.BASE_HP * (1 + 0.15*(self.tier-1)))
            if world and hasattr(world, 'modifiers'):
                building_hp_mult = world.modifiers.get("building_hp_mult", 1.0)
                # Check if this is a turret and apply turret_hp_mult
                if hasattr(self, 'TYPE_ID') and 'turret' in self.TYPE_ID:
                    turret_hp_mult = world.modifiers.get("turret_hp_mult", 1.0)
                    self.max_hp = int(base_max_hp * building_hp_mult * turret_hp_mult)
                elif hasattr(self, 'TYPE_ID') and self.TYPE_ID.startswith('wall'):
                    wall_hp_mult = world.modifiers.get("wall_hp_mult", 1.0)
                    self.max_hp = int(base_max_hp * building_hp_mult * wall_hp_mult)
                else:
                    self.max_hp = int(base_max_hp * building_hp_mult)
            else:
                self.max_hp = base_max_hp
            self.on_upgrade()
        
        return True

    # ----- Hooks -----
    def on_complete(self, world=None):
        """Called when building finishes construction. Mark tiles as solid if needed."""
        if not world or not hasattr(world, 'collision_map') or not world.collision_map:
            return
        
        # Only mark walls, gates, and HQ as solid (not turrets, farms, sawmills, etc.)
        building_type = getattr(self, 'TYPE_ID', '').lower()
        is_wall = building_type.startswith('wall')
        is_gate = building_type == 'gate'
        is_hq = building_type == 'hq'
        
        if is_wall or is_gate or is_hq:
            # Get building footprint
            footprint = getattr(self, 'FOOTPRINT', (1, 1))
            if isinstance(footprint, (list, tuple)) and len(footprint) >= 2:
                footprint_w, footprint_h = footprint[0], footprint[1]
            else:
                footprint_w, footprint_h = 1, 1
            
            # Mark all tiles in footprint as solid
            world.collision_map.set_footprint_solid(self.grid_x, self.grid_y, footprint_w, footprint_h)

    def get_attacker_capacity(self) -> int:
        """Get the maximum number of attackers this building can handle."""
        w, h = self.FOOTPRINT
        return max(1, w * h * 2)  # Simple default: 2 attackers per tile
    
    def request_attack_slot(self) -> bool:
        """Request an attack slot. Returns True if slot was granted."""
        if self.state != BuildState.ACTIVE:
            return False
        if self.attacker_count < self.get_attacker_capacity():
            self.attacker_count += 1
            return True
        return False
    
    def release_attack_slot(self):
        """Release an attack slot when enemy retargets or dies."""
        if self.attacker_count > 0:
            self.attacker_count -= 1
    
    def on_destroy(self):
        """Called when building is destroyed. Unmark tiles from collision map if needed."""
        # Release all attacker slots when destroyed
        self.attacker_count = 0
        
        # Get world from building instance (should be set during construction)
        world = getattr(self, 'world', None)
        if not world or not hasattr(world, 'collision_map') or not world.collision_map:
            return
        
        # Only unmark walls, gates, and HQ (same as on_complete)
        building_type = getattr(self, 'TYPE_ID', '').lower()
        is_wall = building_type.startswith('wall')
        is_gate = building_type == 'gate'
        is_hq = building_type == 'hq'
        
        if is_wall or is_gate or is_hq:
            # Get building footprint
            footprint = getattr(self, 'FOOTPRINT', (1, 1))
            if isinstance(footprint, (list, tuple)) and len(footprint) >= 2:
                footprint_w, footprint_h = footprint[0], footprint[1]
            else:
                footprint_w, footprint_h = 1, 1
            
            # Unmark all tiles in footprint
            world.collision_map.set_footprint_empty(self.grid_x, self.grid_y, footprint_w, footprint_h)

    def on_upgrade(self): 
        pass

    # ----- Production scaling with tier -----
    def _current_production(self) -> Production:
        mul = 1.0 + 0.2*(self.tier-1)
        base = self.PASSIVE
        return Production(
            wood_per_min=base.wood_per_min*mul,
            iron_per_min=base.iron_per_min*mul,
            food_per_min=base.food_per_min*mul,
        )

    # ----- Save/Load -----
    def to_dict(self) -> Dict:
        return {
            "uid": self.uid,
            "type": self.TYPE_ID,
            "grid": [self.grid_x, self.grid_y],
            "tier": self.tier,
            "hp": self.hp,
            "state": self.state,
            "progress": self.progress
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Building":
        obj = cls(tuple(data["grid"]), tier=data.get("tier", 1), uid=data.get("uid"))
        obj.hp = data.get("hp", obj.max_hp)
        obj.state = data.get("state", BuildState.ACTIVE)
        obj.progress = data.get("progress", 0.0)
        return obj

    # ----- Rendering -----
    def draw(self, surface: pygame.Surface):
        # default placeholder: grey rect + build bar
        self.image.fill((0,0,0,0))
        w, h = self.FOOTPRINT
        color = (120,120,120) if self.state != BuildState.DESTROYED else (80,30,30)
        pygame.draw.rect(self.image, color, (0,0,w*TILE,h*TILE))
        
        # build progress
        if self.state == BuildState.CONSTRUCTING:
            pct = self.progress/self.BUILD_TIME if self.BUILD_TIME > 0 else 1.0
            pygame.draw.rect(self.image, (200,220,80), (2, h*TILE-6, int((w*TILE-4)*pct), 4))
        
        # HP bar (if damaged)
        if self.state == BuildState.ACTIVE and self.hp < self.max_hp:
            hp_pct = self.hp / self.max_hp
            hp_color = (0, 255, 0) if hp_pct > 0.5 else (255, 255, 0) if hp_pct > 0.25 else (255, 0, 0)
            pygame.draw.rect(self.image, hp_color, (2, 2, int((w*TILE-4)*hp_pct), 4))
        
        self.rect = self.image.get_rect(center=self.pos)
        surface.blit(self.image, self.rect)

