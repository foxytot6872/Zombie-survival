"""
Zombie Colony Defense - Main Game Loop
"""
import pygame as pg
import math
import time
import random
from config import *
from Resources import Resources
from GameState import GameState
from Grid import Grid
from Building import Building
from Tower import Tower
from Enemy import Enemy
from Bullet import Bullet
from Base import Base

# Initialize Pygame
pg.init()

# Set up screen
SCREEN = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("Zombie Colony Defense")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)

# Initialize systems
clock = pg.time.Clock()
resources = Resources(STARTING_WOOD, STARTING_METAL, STARTING_FOOD, STARTING_RESEARCH)
game_state = GameState("Normal")
grid = Grid()

# Sprite groups
buildings = pg.sprite.Group()
towers = pg.sprite.Group()
enemies = pg.sprite.Group()
bullets = pg.sprite.Group()
survivors = pg.sprite.Group()

# Create HQ (loss condition)
hq = Building(SCREEN_WIDTH // (2 * GRID_SIZE), (WALL_Y + 20) // GRID_SIZE, "HQ", tier=1)
hq.construction_phase = Building.COMPLETE
hq.construction_progress = 1.0
hq.update_image()
buildings.add(hq)

# Game state
placing_building = None
selected_building_type = None
selected_building = None  # Currently selected building for management
enemies_killed = 0
debug_mode = True  # Set to False to disable debug tools

# Fonts
font_large = pg.font.Font(None, 48)
font = pg.font.Font(None, 36)
font_small = pg.font.Font(None, 24)

def draw_grid(screen):
    """Draw grid lines for debugging"""
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pg.draw.line(screen, (40, 40, 40), (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pg.draw.line(screen, (40, 40, 40), (0, y), (SCREEN_WIDTH, y), 1)

def draw_wall_line(screen):
    """Draw the wall line separating outside and inside zones"""
    pg.draw.line(screen, (100, 100, 100), (0, WALL_Y), (SCREEN_WIDTH, WALL_Y), 3)
    pg.draw.line(screen, (150, 150, 150), (0, WALL_Y + 1), (SCREEN_WIDTH, WALL_Y + 1), 1)

def draw_ui(screen):
    """Draw game UI"""
    # Top bar - Resources and Day counter
    top_bar_height = 60
    pg.draw.rect(screen, (30, 30, 30), (0, 0, SCREEN_WIDTH, top_bar_height))
    pg.draw.line(screen, WHITE, (0, top_bar_height), (SCREEN_WIDTH, top_bar_height), 2)
    
    y_offset = 10
    # Resources
    resource_texts = [
        font.render(f"Wood: {resources.wood}", True, BROWN),
        font.render(f"Metal: {resources.metal}", True, GRAY),
        font.render(f"Food: {resources.food}", True, GREEN),
        font.render(f"Research: {resources.research}", True, BLUE)
    ]
    
    x_pos = 20
    for text in resource_texts:
        screen.blit(text, (x_pos, y_offset))
        x_pos += 200
    
    # Day counter and phase
    phase_text = "DAY" if game_state.is_day else "NIGHT"
    phase_color = YELLOW if game_state.is_day else (200, 0, 0)
    day_text = font_large.render(f"Day {game_state.day} - {phase_text}", True, phase_color)
    screen.blit(day_text, (SCREEN_WIDTH - 300, 5))
    
    # Time remaining
    time_remaining = int(game_state.get_time_remaining())
    time_text = font_small.render(f"Time: {time_remaining}s", True, WHITE)
    screen.blit(time_text, (SCREEN_WIDTH - 300, 45))
    
    # Bottom bar - Build buttons
    bottom_bar_height = 80
    bar_y = SCREEN_HEIGHT - bottom_bar_height
    pg.draw.rect(screen, (30, 30, 30), (0, bar_y, SCREEN_WIDTH, bottom_bar_height))
    pg.draw.line(screen, WHITE, (0, bar_y), (SCREEN_WIDTH, bar_y), 2)
    
    # Build buttons
    build_buttons = [
        ("Wall", "Wall"),
        ("Gate", "Gate"),
        ("Turret Mk1", "Turret_Mk1"),
        ("Farm", "Farm"),
        ("Sawmill", "Sawmill"),
        ("Smelter", "Smelter"),
        ("Housing", "Housing")
    ]
    
    button_width = 120
    button_height = 60
    button_spacing = 10
    start_x = 20
    
    for i, (label, building_type) in enumerate(build_buttons):
        x = start_x + i * (button_width + button_spacing)
        y = bar_y + 10
        
        # Check if can afford
        cost = Building.get_cost(building_type, game_state.get_cost_multiplier())
        can_afford = resources.can_afford(cost)
        
        # Button color
        if selected_building_type == building_type:
            color = YELLOW
        elif can_afford:
            color = GREEN
        else:
            color = GRAY
        
        # Draw button
        pg.draw.rect(screen, color, (x, y, button_width, button_height))
        pg.draw.rect(screen, WHITE, (x, y, button_width, button_height), 2)
        
        # Button text
        text = font_small.render(label, True, BLACK)
        text_rect = text.get_rect(center=(x + button_width // 2, y + button_height // 2))
        screen.blit(text, text_rect)
        
        # Cost text
        cost_str = f"W:{cost.get('Wood', 0)} M:{cost.get('Metal', 0)}"
        cost_text = pg.font.Font(None, 18).render(cost_str, True, BLACK)
        screen.blit(cost_text, (x + 5, y + button_height - 18))

def handle_mouse_click(pos, button):
    """Handle mouse clicks"""
    global placing_building, selected_building_type, selected_building
    
    # Check if clicking on building management UI
    if selected_building and button == 1:
        # Check if click is on upgrade button
        ui_x, ui_y, ui_width, ui_height = get_building_ui_rect(selected_building)
        button_y = ui_y + ui_height - 60
        
        # Upgrade button
        upgrade_rect = pg.Rect(ui_x + 10, button_y, (ui_width - 30) // 2, 40)
        # Demolish button
        demolish_rect = pg.Rect(ui_x + 20 + (ui_width - 30) // 2, button_y, (ui_width - 30) // 2, 40)
        
        if upgrade_rect.collidepoint(pos):
            upgrade_building(selected_building)
            return
        elif demolish_rect.collidepoint(pos):
            demolish_building(selected_building)
            selected_building = None
            return
        elif not pg.Rect(ui_x, ui_y, ui_width, ui_height).collidepoint(pos):
            # Clicked outside UI, deselect
            selected_building = None
    
    # Check if clicking on a building (only if not placing a building)
    if button == 1 and not placing_building:  # Left click
        clicked_building = None
        for building in buildings:
            if building.rect.collidepoint(pos):
                clicked_building = building
                break
        
        if clicked_building:
            selected_building = clicked_building
            placing_building = None
            selected_building_type = None
            return
    
    # Check if clicking on build buttons
    bottom_bar_y = SCREEN_HEIGHT - 80
    if pos[1] > bottom_bar_y:
        button_width = 120
        button_spacing = 10
        start_x = 20
        
        build_buttons = [
            ("Wall", "Wall"),
            ("Gate", "Gate"),
            ("Turret Mk1", "Turret_Mk1"),
            ("Farm", "Farm"),
            ("Sawmill", "Sawmill"),
            ("Smelter", "Smelter"),
            ("Housing", "Housing")
        ]
        
        for i, (label, building_type) in enumerate(build_buttons):
            x = start_x + i * (button_width + button_spacing)
            y = bottom_bar_y + 10
            
            if x <= pos[0] <= x + button_width and y <= pos[1] <= y + 60:
                if button == 1:  # Left click
                    cost = Building.get_cost(building_type, game_state.get_cost_multiplier())
                    if resources.can_afford(cost):
                        selected_building_type = building_type
                        placing_building = building_type
                elif button == 3:  # Right click
                    selected_building_type = None
                    placing_building = None
                return
    
    # Handle building placement
    if button == 1 and placing_building:  # Left click to place
        grid_x, grid_y = grid.world_to_grid(pos[0], pos[1])
        
        # Check if valid position
        if grid.is_valid_position(grid_x, grid_y):
            cost = Building.get_cost(placing_building, game_state.get_cost_multiplier())
            if resources.can_afford(cost):
                # Create building
                building = Building(grid_x, grid_y, placing_building)
                buildings.add(building)
                grid.occupy_cells(grid_x, grid_y, building)
                resources.spend(cost)
                
                # If it's a turret, create a Tower instance when complete
                # (Tower will be created when building completes construction)
                
                placing_building = None
    
    elif button == 3:  # Right click to cancel
        placing_building = None
        selected_building_type = None

def draw_building_preview(screen, mouse_pos):
    """Draw preview of building to be placed"""
    if placing_building:
        grid_x, grid_y = grid.world_to_grid(mouse_pos[0], mouse_pos[1])
        world_x, world_y = grid.grid_to_world(grid_x, grid_y)
        
        # Check if valid
        is_valid = grid.is_valid_position(grid_x, grid_y)
        cost = Building.get_cost(placing_building, game_state.get_cost_multiplier())
        can_afford = resources.can_afford(cost)
        
        # Preview color
        if is_valid and can_afford:
            color = (0, 255, 0, 100)  # Green, semi-transparent
        else:
            color = (255, 0, 0, 100)  # Red, semi-transparent
        
        # Draw preview
        preview = pg.Surface((GRID_SIZE, GRID_SIZE), pg.SRCALPHA)
        preview.fill(color)
        screen.blit(preview, (world_x - GRID_SIZE // 2, world_y - GRID_SIZE // 2))
        
        # Draw grid cell outline
        pg.draw.rect(screen, WHITE, 
                    (world_x - GRID_SIZE // 2, world_y - GRID_SIZE // 2, 
                     GRID_SIZE, GRID_SIZE), 2)

def get_building_ui_rect(building):
    """Get the rectangle for building management UI"""
    ui_width = 250
    ui_height = 200
    # Position UI near building, but keep it on screen
    ui_x = building.rect.centerx + 40
    ui_y = building.rect.centery - ui_height // 2
    
    # Keep UI on screen
    if ui_x + ui_width > SCREEN_WIDTH:
        ui_x = building.rect.centerx - ui_width - 40
    if ui_y < 0:
        ui_y = 10
    if ui_y + ui_height > SCREEN_HEIGHT - 80:  # Above bottom bar
        ui_y = SCREEN_HEIGHT - 80 - ui_height - 10
    
    return ui_x, ui_y, ui_width, ui_height

def draw_building_management_ui(screen, building):
    """Draw building management popup UI"""
    ui_x, ui_y, ui_width, ui_height = get_building_ui_rect(building)
    
    # Draw background panel
    panel = pg.Surface((ui_width, ui_height), pg.SRCALPHA)
    panel.fill((40, 40, 40, 240))
    pg.draw.rect(panel, WHITE, (0, 0, ui_width, ui_height), 2)
    screen.blit(panel, (ui_x, ui_y))
    
    # Title
    title_font = pg.font.Font(None, 28)
    title_text = title_font.render(building.building_type, True, YELLOW)
    screen.blit(title_text, (ui_x + 10, ui_y + 10))
    
    # Stats
    stats_font = pg.font.Font(None, 20)
    y_offset = 40
    stats = [
        f"Tier: {building.tier}",
        f"HP: {building.hp}/{building.max_hp}",
        f"Status: {'Complete' if building.is_complete() else 'Under Construction'}"
    ]
    
    for stat in stats:
        stat_text = stats_font.render(stat, True, WHITE)
        screen.blit(stat_text, (ui_x + 10, ui_y + y_offset))
        y_offset += 25
    
    # Construction progress if not complete
    if not building.is_complete():
        progress_text = stats_font.render(f"Progress: {int(building.construction_progress * 100)}%", True, GREEN)
        screen.blit(progress_text, (ui_x + 10, ui_y + y_offset))
        y_offset += 25
    
    # Buttons
    button_y = ui_y + ui_height - 60
    button_height = 40
    button_width = (ui_width - 30) // 2
    
    # Upgrade button
    upgrade_rect = pg.Rect(ui_x + 10, button_y, button_width, button_height)
    upgrade_color = GREEN if can_upgrade_building(building) else GRAY
    pg.draw.rect(screen, upgrade_color, upgrade_rect)
    pg.draw.rect(screen, WHITE, upgrade_rect, 2)
    upgrade_text = stats_font.render("Upgrade", True, BLACK)
    text_rect = upgrade_text.get_rect(center=upgrade_rect.center)
    screen.blit(upgrade_text, text_rect)
    
    # Show upgrade cost if available
    if can_upgrade_building(building):
        upgrade_cost = Building.get_upgrade_cost(building.building_type, building.tier, game_state.get_cost_multiplier())
        if upgrade_cost:
            cost_text = pg.font.Font(None, 16).render(f"W:{upgrade_cost.get('Wood', 0)} M:{upgrade_cost.get('Metal', 0)}", True, BLACK)
            cost_rect = cost_text.get_rect(center=(upgrade_rect.centerx, upgrade_rect.centery + 12))
            screen.blit(cost_text, cost_rect)
    
    # Demolish button
    demolish_rect = pg.Rect(ui_x + 20 + button_width, button_y, button_width, button_height)
    pg.draw.rect(screen, RED, demolish_rect)
    pg.draw.rect(screen, WHITE, demolish_rect, 2)
    demolish_text = stats_font.render("Demolish", True, WHITE)
    text_rect = demolish_text.get_rect(center=demolish_rect.center)
    screen.blit(demolish_text, text_rect)
    
    # Refund info
    refund = Building.get_refund(building.building_type, building.tier, game_state.get_cost_multiplier())
    if refund:
        refund_text = pg.font.Font(None, 14).render(f"Refund: W:{refund.get('Wood', 0)} M:{refund.get('Metal', 0)}", True, YELLOW)
        screen.blit(refund_text, (ui_x + 10, ui_y + ui_height - 20))

def can_upgrade_building(building):
    """Check if building can be upgraded"""
    if not building.is_complete():
        return False
    if building.tier >= 3:  # Max tier
        return False
    upgrade_cost = Building.get_upgrade_cost(building.building_type, building.tier, game_state.get_cost_multiplier())
    if not upgrade_cost:
        return False
    return resources.can_afford(upgrade_cost)

def upgrade_building(building):
    """Upgrade a building"""
    if not can_upgrade_building(building):
        return
    
    upgrade_cost = Building.get_upgrade_cost(building.building_type, building.tier, game_state.get_cost_multiplier())
    resources.spend(upgrade_cost)
    building.tier += 1
    
    # Update building type name for turrets (Mk1 -> Mk2 -> Mk3)
    if "Turret" in building.building_type:
        if building.tier == 2:
            building.building_type = "Turret_Mk2"
        elif building.tier == 3:
            building.building_type = "Turret_Mk3"
    
    building.max_hp = int(building.max_hp * 1.5)  # Increase HP
    building.hp = building.max_hp
    building.update_image()
    
    # If it's a turret, we need to recreate the tower with new stats and tier
    if "Turret" in building.building_type:
        # Remove old tower
        for tower in towers:
            if hasattr(tower, 'building') and tower.building == building:
                tower.kill()
                break
    
    print(f"DEBUG: Upgraded {building.building_type} to tier {building.tier}")

def demolish_building(building):
    """Demolish a building and refund resources"""
    # Refund resources
    refund = Building.get_refund(building.building_type, building.tier, game_state.get_cost_multiplier())
    if refund:
        resources.add(refund)
    
    # Remove associated tower if it's a turret
    if "Turret" in building.building_type:
        for tower in towers:
            if hasattr(tower, 'building') and tower.building == building:
                tower.kill()
                break
    
    # Free grid cells
    grid.free_cells(building.grid_x, building.grid_y, building.width, building.height)
    
    # Remove building
    building.kill()
    print(f"DEBUG: Demolished {building.building_type}")

def draw_debug_info(screen):
    """Draw debug tool information"""
    debug_y = SCREEN_HEIGHT - 200
    debug_font = pg.font.Font(None, 20)
    
    debug_texts = [
        "DEBUG MODE - Hotkeys:",
        "F1: +100 All Resources",
        "F2: +100 Wood  F3: +100 Metal  F4: +100 Food  F5: +100 Research",
        "Z/S: Spawn Enemy",
        "C: Complete All Buildings",
        "T: Toggle Day/Night",
        "N: Next Day",
        "X: Clear Enemies",
        "H: Heal All Buildings",
        "K: Kill All Enemies (Get Rewards)"
    ]
    
    for i, text in enumerate(debug_texts):
        color = YELLOW if i == 0 else WHITE
        text_surface = debug_font.render(text, True, color)
        screen.blit(text_surface, (10, debug_y + i * 18))

def spawn_enemy():
    """Spawn enemy from upper edges"""
    # Spawn from top or sides
    side = random.randint(0, 3)
    if side == 0:  # Top
        x = random.randint(0, SCREEN_WIDTH)
        y = 0
    elif side == 1:  # Right
        x = SCREEN_WIDTH
        y = random.randint(0, WALL_Y)
    elif side == 2:  # Left
        x = 0
        y = random.randint(0, WALL_Y)
    else:  # Top center
        x = SCREEN_WIDTH // 2
        y = 0
    
    # Path to wall/gate
    target_x = SCREEN_WIDTH // 2
    target_y = WALL_Y
    
    path = [(x, y), (target_x, target_y)]
    
    # Apply difficulty multiplier
    health = int(50 * game_state.get_enemy_multiplier())
    speed = 1.0 * game_state.get_enemy_multiplier()
    
    enemy = Enemy(path, speed=speed, health=health, reward=10)
    enemies.add(enemy)

# Main game loop
run = True
spawn_timer = 0
spawn_delay = 120  # Frames between spawns during night

while run:
    clock.tick(FPS)
    
    # Update game state
    game_state.update()
    
    # Handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
        
        if event.type == pg.MOUSEBUTTONDOWN:
            handle_mouse_click(event.pos, event.button)
        
        # Debug tools (only if debug_mode is True)
        if debug_mode and event.type == pg.KEYDOWN:
            # Resource debug tools
            if event.key == pg.K_F1:
                # Add 100 of all resources
                resources.add({"Wood": 100, "Metal": 100, "Food": 100, "Research": 100})
                print("DEBUG: Added 100 of all resources")
            elif event.key == pg.K_F2:
                # Add 100 Wood
                resources.add({"Wood": 100})
                print("DEBUG: Added 100 Wood")
            elif event.key == pg.K_F3:
                # Add 100 Metal
                resources.add({"Metal": 100})
                print("DEBUG: Added 100 Metal")
            elif event.key == pg.K_F4:
                # Add 100 Food
                resources.add({"Food": 100})
                print("DEBUG: Added 100 Food")
            elif event.key == pg.K_F5:
                # Add 100 Research
                resources.add({"Research": 100})
                print("DEBUG: Added 100 Research")
            
            # Enemy spawn debug
            elif event.key == pg.K_z or event.key == pg.K_s:
                # Spawn enemy at mouse position or random edge
                spawn_enemy()
                print("DEBUG: Spawned enemy")
            
            # Building debug tools
            elif event.key == pg.K_c:
                # Complete all buildings under construction
                for building in buildings:
                    if not building.is_complete():
                        building.construction_phase = Building.COMPLETE
                        building.construction_progress = 1.0
                        building.update_image()
                print("DEBUG: Completed all buildings")
            
            # Time debug tools
            elif event.key == pg.K_t:
                # Toggle day/night
                game_state.is_day = not game_state.is_day
                if game_state.is_day:
                    game_state.day_start_time = time.time()
                else:
                    game_state.night_start_time = time.time()
                print(f"DEBUG: Toggled to {'DAY' if game_state.is_day else 'NIGHT'}")
            
            elif event.key == pg.K_n:
                # Advance to next day
                game_state.day += 1
                game_state.is_day = True
                game_state.day_start_time = time.time()
                print(f"DEBUG: Advanced to Day {game_state.day}")
            
            # Clear enemies
            elif event.key == pg.K_x:
                enemies.empty()
                print("DEBUG: Cleared all enemies")
            
            # Heal all buildings
            elif event.key == pg.K_h:
                for building in buildings:
                    building.hp = building.max_hp
                print("DEBUG: Healed all buildings")
            
            # Kill all enemies
            elif event.key == pg.K_k:
                for enemy in enemies:
                    resources.add({"Wood": enemy.reward // 2, "Metal": enemy.reward // 4})
                    enemies_killed += 1
                enemies.empty()
                print("DEBUG: Killed all enemies and awarded resources")
    
    # Spawn enemies during night
    if not game_state.is_day:
        spawn_timer += 1
        if spawn_timer >= spawn_delay:
            spawn_enemy()
            spawn_timer = 0
    
    # Update game objects
    buildings.update()
    enemies.update()
    bullets.update()
    
    # Create Tower instances for completed turret buildings
    for building in buildings:
        if building.is_complete() and "Turret" in building.building_type:
            # Check if we already have a tower for this building
            building_has_tower = False
            for tower in towers:
                if hasattr(tower, 'building') and tower.building == building:
                    building_has_tower = True
                    break
            
            if not building_has_tower:
                # Create tower based on tier
                tier = building.tier
                if "Mk1" in building.building_type or tier == 1:
                    damage, range_val, fire_rate = 25, 150, 30
                elif "Mk2" in building.building_type or tier == 2:
                    damage, range_val, fire_rate = 40, 200, 25
                elif "Mk3" in building.building_type or tier == 3:
                    damage, range_val, fire_rate = 60, 250, 20
                else:
                    damage, range_val, fire_rate = 25, 150, 30
                    tier = 1
                
                tower = Tower((building.world_x, building.world_y), 
                             damage=damage, range=range_val, fire_rate=fire_rate, cost=0, tier=tier)
                tower.building = building  # Link tower to building
                towers.add(tower)
    
    # Update towers and handle shooting
    for tower in towers:
        # Update tower position if building moved (shouldn't happen, but just in case)
        if hasattr(tower, 'building') and tower.building:
            tower.rect.center = (tower.building.world_x, tower.building.world_y)
        
        # Check if building is destroyed
        if hasattr(tower, 'building') and tower.building and tower.building.hp <= 0:
            tower.kill()
            continue
        
        # Update and shoot
        should_fire = tower.update(enemies)
        if should_fire and tower.target:
            bullet = Bullet(tower.rect.center, tower.target, tower.damage)
            bullets.add(bullet)
    
    # Bullet collision with enemies
    for bullet in bullets:
        hit_enemy = bullet.check_hit(enemies)
        if hit_enemy:
            if hit_enemy.take_damage(bullet.damage):
                resources.add({"Wood": hit_enemy.reward // 2, "Metal": hit_enemy.reward // 4})
                enemies_killed += 1
                hit_enemy.kill()
            bullet.kill()
        # Remove bullets that are off screen
        if (bullet.rect.x < -50 or bullet.rect.x > SCREEN_WIDTH + 50 or
            bullet.rect.y < -50 or bullet.rect.y > SCREEN_HEIGHT + 50):
            bullet.kill()
    
    # Enemy reaching wall/HQ
    for enemy in enemies:
        if enemy.path_index >= len(enemy.path):
            # Enemy reached target - damage wall or HQ
            if hq.rect.collidepoint(enemy.rect.center):
                hq.take_damage(10)
            else:
                # Damage wall (simplified - in full game, find nearest wall segment)
                pass
            enemy.kill()
    
    # Draw everything
    SCREEN.fill((20, 30, 20))  # Dark background
    
    # Draw grid (optional, for debugging)
    # draw_grid(SCREEN)
    
    # Draw wall line
    draw_wall_line(SCREEN)
    
    # Draw buildings (using sprite group draw)
    buildings.draw(SCREEN)
    for building in buildings:
        building.draw_construction_bar(SCREEN)
        building.draw_health_bar(SCREEN)
    
    # Draw towers (with rotating heads)
    for tower in towers:
        tower.draw(SCREEN)
    
    # Draw enemies
    enemies.draw(SCREEN)
    
    # Draw bullets
    bullets.draw(SCREEN)
    
    # Draw building preview
    mouse_pos = pg.mouse.get_pos()
    draw_building_preview(SCREEN, mouse_pos)
    
    # Draw selected building highlight
    if selected_building:
        highlight = pg.Surface((selected_building.rect.width + 4, selected_building.rect.height + 4), pg.SRCALPHA)
        pg.draw.rect(highlight, (255, 255, 0, 150), (0, 0, highlight.get_width(), highlight.get_height()), 3)
        SCREEN.blit(highlight, (selected_building.rect.x - 2, selected_building.rect.y - 2))
    
    # Draw building management UI
    if selected_building:
        draw_building_management_ui(SCREEN, selected_building)
    
    # Draw UI
    draw_ui(SCREEN)
    
    # Draw debug info
    if debug_mode:
        draw_debug_info(SCREEN)
    
    # Check game over
    if hq.hp <= 0:
        game_state.game_over = True
        # Draw game over screen
        overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        SCREEN.blit(overlay, (0, 0))
        
        game_over_text = font_large.render("GAME OVER", True, RED)
        day_text = font.render(f"Survived {game_state.day} days", True, WHITE)
        kills_text = font.render(f"Enemies killed: {enemies_killed}", True, WHITE)
        
        SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 60))
        SCREEN.blit(day_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2))
        SCREEN.blit(kills_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 40))
    
    pg.display.flip()

pg.quit()

