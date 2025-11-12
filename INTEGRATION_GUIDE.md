# Integration Guide for New Systems

This guide explains how to integrate all the new systems into `main.py`.

## 1. Import New Modules

```python
# Core systems
from core.wave_manager import WaveManager
from core.game_state import GameState, GameStateManager
from core.save_system import SaveSystem
from core.sound import SoundSystem

# UI components
from ui.game_over import GameOverScreen
from ui.pause_menu import PauseMenu
from ui.building_panel import BuildingPanel
from ui.hud import HUD

# Enemy variants
from world.enemies import BasicZombie, RunnerZombie, BruteZombie, SpitterZombie, SwarmlingZombie

# Turret variants
from world.buildings import BallisticTurret, GatlingTurret, PiercerTurret

# Pathfinding (optional)
from world.pathfinding import Pathfinding
```

## 2. Initialize Systems

```python
# Load wave configuration
import json
with open('data/config/waves.json', 'r') as f:
    waves_config = json.load(f)

# Initialize systems
game_state_manager = GameStateManager()
wave_manager = WaveManager(world, waves_config, difficulty="normal")
save_system = SaveSystem()
sound_system = SoundSystem()
hud = HUD(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
game_over_screen = GameOverScreen(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
pause_menu = PauseMenu(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)
building_panel = BuildingPanel(c.SCREEN_WIDTH, c.SCREEN_HEIGHT)

# Enemy factory for spawner
enemy_factory = {
    "walker": BasicZombie,
    "runner": RunnerZombie,
    "brute": BruteZombie,
    "spitter": SpitterZombie,
    "swarmling": SwarmlingZombie
}

# Initialize spawner with enemy factory
zombie_spawner = Spawner(enemy_factory, spawn_interval=1.0)
```

## 3. Update Game Loop

### Update Wave Manager
```python
# In game loop
wave_state = wave_manager.update(dt, zombie_spawner, world)

# Check win condition
if wave_state == "WIN":
    game_state_manager.win()
    game_over_screen.show(GameState.WIN, wave_manager.get_current_wave_info())

# Start night when wave manager transitions to NIGHT
if wave_manager.state == WaveManager.STATE_NIGHT and not zombie_spawner.active:
    recipe = wave_manager.get_wave_recipe()
    spawn_config = waves_config["spawn"]
    zombie_spawner.begin(recipe, spawn_config)
    hud.show_event(f"Night {wave_manager.night} Begins!", 3.0)
    sound_system.play("wave_start")

# Start summary when wave completes
if wave_manager.state == WaveManager.STATE_SUMMARY:
    # Autosave
    save_system.save_world(world, wave_manager, game_state_manager, resources)
    hud.show_event(f"Night {wave_manager.night - 1} Cleared!", 3.0)
    sound_system.play("wave_clear")
```

## 4. Handle Win/Lose Conditions

```python
# Check lose condition (HQ destroyed)
for building in building_group:
    if isinstance(building, HQ) and building.state == BuildState.DESTROYED:
        game_state_manager.game_over()
        game_over_screen.show(GameState.GAME_OVER, wave_manager.get_current_wave_info())
        sound_system.play("game_over")

# Check win condition
if wave_manager.is_won():
    game_state_manager.win()
    game_over_screen.show(GameState.WIN, wave_manager.get_current_wave_info())
    sound_system.play("game_over")  # Or create "victory" sound
```

## 5. Update Enemy System

```python
# In enemy update loop
for enemy in enemy_group:
    enemy.update(dt, world)
    # Set projectile group for ranged enemies
    if hasattr(enemy, 'projectile_group'):
        enemy.projectile_group = projectile_group
    
    # Track enemy kills
    if not enemy.alive and enemy.hp <= 0:
        wave_manager.enemies_killed += 1
        sound_system.play("enemy_death")
```

## 6. Update Building System

```python
# In building update loop
for building in building_group:
    building.update(dt, world)
    
    # Check if building destroyed
    if building.state == BuildState.DESTROYED:
        sound_system.play("building_destroyed")
        # Check if HQ destroyed
        if isinstance(building, HQ):
            game_state_manager.game_over()
```

## 7. Handle Building Selection

```python
# On building click
if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
    mouse_pos = pygame.mouse.get_pos()
    selected_building = select_building(mouse_pos, building_group)
    
    if selected_building:
        building_panel.show(selected_building)
        sound_system.play("button_click")
    else:
        building_panel.hide()
```

## 8. Handle Upgrade/Repair/Sell

```python
# In building panel or main loop
if building_panel.is_visible:
    # Check button clicks (simplified - would need actual button rects)
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mouse_pos = pygame.mouse.get_pos()
        
        # Upgrade button
        if upgrade_rect.collidepoint(mouse_pos):
            building = building_panel.selected_building
            if building and building.tier < building.TIER_MAX:
                upgrade_cost = building_panel._get_upgrade_cost(building)
                if (resources.wood >= upgrade_cost.wood and
                    resources.iron >= upgrade_cost.iron and
                    resources.food >= upgrade_cost.food):
                    # Pay cost
                    resources.wood -= upgrade_cost.wood
                    resources.iron -= upgrade_cost.iron
                    resources.food -= upgrade_cost.food
                    # Upgrade building
                    building.upgrade()
                    sound_system.play("upgrade")
        
        # Repair button
        if repair_rect.collidepoint(mouse_pos):
            building = building_panel.selected_building
            if building and building.hp < building.max_hp:
                repair_cost = building_panel._get_repair_cost(building)
                if resources.wood >= repair_cost.wood:
                    # Pay cost
                    resources.wood -= repair_cost.wood
                    # Repair building
                    hp_needed = building.max_hp - building.hp
                    building.repair(hp_needed)
                    sound_system.play("repair")
        
        # Sell button
        if sell_rect.collidepoint(mouse_pos):
            building = building_panel.selected_building
            if building:
                # Refund 60% of cost
                building.refund_cost(resources, ratio=0.6)
                # Remove building
                building_group.remove(building)
                if building in turret_group:
                    turret_group.remove(building)
                # Unblock grid
                grid.set_footprint_blocked((building.grid_x, building.grid_y), building.FOOTPRINT, False)
                building_panel.hide()
                sound_system.play("button_click")
```

## 9. Handle Pause Menu

```python
# In event loop
if event.type == pygame.KEYDOWN:
    if event.key == pygame.K_ESCAPE:
        if game_state_manager.is_playing():
            game_state_manager.pause()
            pause_menu.show()
        elif game_state_manager.is_paused():
            game_state_manager.resume()
            pause_menu.hide()

# Handle pause menu events
if pause_menu.is_visible:
    if pause_menu.handle_event(event):
        # Event handled
        continue

# Set pause menu callbacks
pause_menu.on_resume = lambda: game_state_manager.resume() or pause_menu.hide()
pause_menu.on_save = lambda: save_system.save_world(world, wave_manager, game_state_manager, resources)
pause_menu.on_load = lambda: load_game()
pause_menu.on_quit = lambda: set_running(False)
```

## 10. Handle Game Over Screen

```python
# Set game over screen callbacks
game_over_screen.on_restart = lambda: restart_game()
game_over_screen.on_quit = lambda: set_running(False)

# Handle game over screen events
if game_over_screen.is_visible:
    if game_over_screen.handle_event(event):
        continue
```

## 11. Update HUD

```python
# In game loop
hud.update(dt, wave_manager.day, wave_manager.night, wave_manager.state, {
    "enemies_spawned": zombie_spawner.spawn_count,
    "total_to_spawn": zombie_spawner.total_to_spawn,
    "enemies_killed": wave_manager.enemies_killed
})

# Draw HUD
hud.draw(screen)
```

## 12. Update Drawing Order

```python
# In game loop drawing section
# 1. Draw background
screen.fill((0, 0, 0))

# 2. Draw buildings
for building in building_group:
    building.draw(screen)

# 3. Draw projectiles
for projectile in projectile_group:
    projectile.draw(screen)

# 4. Draw enemies
for enemy in enemy_group:
    enemy.draw(screen)

# 5. Draw HUD
hud.draw(screen)

# 6. Draw building panel
building_panel.draw(screen, resources)

# 7. Draw pause menu (if paused)
if game_state_manager.is_paused():
    pause_menu.draw(screen)

# 8. Draw game over screen (if game over)
if game_over_screen.is_visible:
    game_over_screen.draw(screen)

# 9. Draw debug overlay (if debug mode)
if debug_system.is_active():
    debug_system.draw(screen, mouse_pos, current_fps)
```

## 13. Sound Integration

```python
# Play sounds at appropriate events
# Building placed
sound_system.play("build_placed")

# Turret fires
sound_system.play("turret_fire")

# Enemy dies
sound_system.play("enemy_death")

# Building destroyed
sound_system.play("building_destroyed")

# Wave starts
sound_system.play("wave_start")

# Wave clears
sound_system.play("wave_clear")

# Game over
sound_system.play("game_over")
```

## 14. Save/Load Integration

```python
# Save game
def save_game():
    save_system.save_world(world, wave_manager, game_state_manager, resources)
    print("Game saved!")

# Load game
def load_game():
    save_data = save_system.load_world()
    if save_data:
        # Restore resources
        resources.wood = save_data["resources"]["wood"]
        resources.iron = save_data["resources"]["iron"]
        resources.food = save_data["resources"]["food"]
        
        # Restore wave manager
        wave_manager.night = save_data["wave_manager"]["night"]
        wave_manager.day = save_data["wave_manager"]["day"]
        wave_manager.state = save_data["wave_manager"]["state"]
        wave_manager.enemies_killed = save_data["wave_manager"]["enemies_killed"]
        wave_manager.enemies_spawned = save_data["wave_manager"]["enemies_spawned"]
        
        # Restore buildings
        building_group.empty()
        turret_group.empty()
        for building_data in save_data["buildings"]:
            # Recreate buildings from data
            # (implementation depends on building type)
            pass
        
        # Restore game state
        game_state_manager.set_state(GameState(save_data["game_state"]))
        
        print("Game loaded!")
    else:
        print("No save file found!")
```

## 15. Pathfinding Integration (Optional)

```python
# Initialize pathfinding
pathfinding = Pathfinding(grid)

# Update enemy movement with pathfinding (optional)
# This can be added to enemy.update() method
if self.target_building:
    # Convert positions to grid
    start_grid = (int(self.pos.x // 32), int(self.pos.y // 32))
    goal_grid = (int(self.target_building.pos.x // 32), int(self.target_building.pos.y // 32))
    
    # Find path
    path = pathfinding.find_path(start_grid, goal_grid)
    
    if path and len(path) > 1:
        # Move toward next waypoint
        next_waypoint = path[1]
        next_pos = pygame.Vector2(next_waypoint[0] * 32 + 16, next_waypoint[1] * 32 + 16)
        direction = (next_pos - self.pos)
        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * self.speed
    else:
        # Fallback to direct movement
        direction = (self.target_building.pos - self.pos)
        if direction.length() > 0:
            direction = direction.normalize()
            self.velocity = direction * self.speed
```

## Notes

- This is a comprehensive guide. Actual implementation may vary based on your specific needs.
- Some systems are optional (pathfinding, sound) and can be added incrementally.
- Error handling should be added for file loading and saving.
- Button click detection should be improved with proper button rects.
- Pathfinding can be expensive, so consider caching paths or using it only when needed.

