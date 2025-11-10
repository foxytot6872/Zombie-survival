import pygame as pg
from Enemy import Enemy
from Base import Base
from Tower import Tower
from Bullet import Bullet

pg.init()

clock = pg.time.Clock()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

SCREEN = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("Base Defense Game")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)

# Game state
money = 200
wave = 1
enemies_killed = 0
game_over = False
placing_tower = False
selected_tower_pos = None

# Define enemy path (waypoints from spawn to base)
ENEMY_PATH = [
    (0, SCREEN_HEIGHT // 2),
    (SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2),
    (SCREEN_WIDTH // 3, SCREEN_HEIGHT // 4),
    (SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT // 4),
    (SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 3 // 4),
    (SCREEN_WIDTH - 50, SCREEN_HEIGHT * 3 // 4)
]

# Base position (end of path)
BASE_POS = (SCREEN_WIDTH - 50, SCREEN_HEIGHT * 3 // 4)

# Sprite groups
enemies = pg.sprite.Group()
towers = pg.sprite.Group()
bullets = pg.sprite.Group()

# Create base
base = Base(BASE_POS, max_health=100)
base_group = pg.sprite.Group(base)

# Wave management
wave_enemies_spawned = 0
wave_enemies_total = 5
spawn_timer = 0
spawn_delay = 60  # Frames between enemy spawns
wave_complete = False

# Font
font = pg.font.Font(None, 36)
small_font = pg.font.Font(None, 24)

def spawn_enemy():
    """Spawn a new enemy at the start of the path"""
    health = 50 + (wave - 1) * 20
    speed = 1 + (wave - 1) * 0.2
    reward = 10 + (wave - 1) * 2
    enemy = Enemy(ENEMY_PATH.copy(), speed=speed, health=health, reward=reward)
    enemies.add(enemy)

def start_next_wave():
    """Start the next wave"""
    global wave, wave_enemies_spawned, wave_enemies_total, wave_complete
    wave += 1
    wave_enemies_spawned = 0
    wave_enemies_total = 5 + wave * 2
    wave_complete = False

def can_place_tower(pos):
    """Check if a tower can be placed at the given position"""
    # Check if too close to base
    dx = pos[0] - BASE_POS[0]
    dy = pos[1] - BASE_POS[1]
    if (dx*dx + dy*dy) < 100*100:
        return False
    
    # Check if overlapping with existing tower
    test_rect = pg.Rect(pos[0] - 20, pos[1] - 20, 40, 40)
    for tower in towers:
        if test_rect.colliderect(tower.rect):
            return False
    
    # Check if on path (simple check)
    for i in range(len(ENEMY_PATH) - 1):
        p1 = ENEMY_PATH[i]
        p2 = ENEMY_PATH[i + 1]
        # Simple distance check from line segment
        A = pos[0] - p1[0]
        B = pos[1] - p1[1]
        C = p2[0] - p1[0]
        D = p2[1] - p1[1]
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        if len_sq != 0:
            param = dot / len_sq
            if 0 <= param <= 1:
                xx = p1[0] + param * C
                yy = p1[1] + param * D
                dx = pos[0] - xx
                dy = pos[1] - yy
                if (dx*dx + dy*dy) < 50*50:
                    return False
    
    return True

def draw_path():
    """Draw the enemy path"""
    for i in range(len(ENEMY_PATH) - 1):
        pg.draw.line(SCREEN, GRAY, ENEMY_PATH[i], ENEMY_PATH[i + 1], 30)
        pg.draw.line(SCREEN, DARK_GRAY, ENEMY_PATH[i], ENEMY_PATH[i + 1], 20)

def draw_ui():
    """Draw game UI"""
    # Money
    money_text = font.render(f"Money: ${money}", True, WHITE)
    SCREEN.blit(money_text, (10, 10))
    
    # Wave
    wave_text = font.render(f"Wave: {wave}", True, WHITE)
    SCREEN.blit(wave_text, (10, 50))
    
    # Enemies killed
    kills_text = font.render(f"Kills: {enemies_killed}", True, WHITE)
    SCREEN.blit(kills_text, (10, 90))
    
    # Base health
    health_text = font.render(f"Base Health: {base.health}/{base.max_health}", True, WHITE)
    SCREEN.blit(health_text, (10, 130))
    
    # Tower cost
    tower_cost = 50
    cost_text = small_font.render(f"Tower Cost: ${tower_cost} (Click to place)", True, WHITE)
    SCREEN.blit(cost_text, (10, SCREEN_HEIGHT - 30))
    
    # Wave progress
    if not wave_complete:
        progress = wave_enemies_spawned / wave_enemies_total
        progress_text = small_font.render(f"Wave Progress: {wave_enemies_spawned}/{wave_enemies_total}", True, WHITE)
        SCREEN.blit(progress_text, (SCREEN_WIDTH - 250, 10))
    else:
        next_wave_text = font.render("Press SPACE for next wave", True, GREEN)
        SCREEN.blit(next_wave_text, (SCREEN_WIDTH - 350, 10))

def draw_game_over():
    """Draw game over screen"""
    overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    SCREEN.blit(overlay, (0, 0))
    
    game_over_text = font.render("GAME OVER", True, RED)
    score_text = font.render(f"Final Score: {enemies_killed}", True, WHITE)
    wave_text = font.render(f"Waves Survived: {wave - 1}", True, WHITE)
    restart_text = small_font.render("Press R to restart", True, WHITE)
    
    SCREEN.blit(game_over_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 80))
    SCREEN.blit(score_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 40))
    SCREEN.blit(wave_text, (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2))
    SCREEN.blit(restart_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40))

def reset_game():
    """Reset game to initial state"""
    global money, wave, enemies_killed, game_over, placing_tower
    global wave_enemies_spawned, wave_enemies_total, spawn_timer, wave_complete
    
    money = 200
    wave = 1
    enemies_killed = 0
    game_over = False
    placing_tower = False
    wave_enemies_spawned = 0
    wave_enemies_total = 5
    spawn_timer = 0
    wave_complete = False
    
    enemies.empty()
    towers.empty()
    bullets.empty()
    base.health = base.max_health

run = True

while run:
    clock.tick(FPS)
    
    # Handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
        
        if not game_over:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pg.mouse.get_pos()
                    tower_cost = 50
                    
                    if money >= tower_cost:
                        if can_place_tower(mouse_pos):
                            tower = Tower(mouse_pos, damage=25, range=150, fire_rate=30, cost=tower_cost)
                            towers.add(tower)
                            money -= tower_cost
            
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    if wave_complete and len(enemies) == 0:
                        start_next_wave()
        else:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    reset_game()
    
    if not game_over:
        # Spawn enemies
        if not wave_complete and spawn_timer >= spawn_delay:
            if wave_enemies_spawned < wave_enemies_total:
                spawn_enemy()
                wave_enemies_spawned += 1
                spawn_timer = 0
            else:
                wave_complete = True
        else:
            spawn_timer += 1
        
        # Update game objects
        enemies.update()
        bullets.update()
        
        # Tower shooting - update towers and check if they should fire
        for tower in towers:
            should_fire = tower.update(enemies)
            if should_fire and tower.target:
                bullet = Bullet(tower.rect.center, tower.target, tower.damage)
                bullets.add(bullet)
        
        # Bullet collision with enemies
        for bullet in bullets:
            hit_enemy = bullet.check_hit(enemies)
            if hit_enemy:
                if hit_enemy.take_damage(bullet.damage):
                    money += hit_enemy.reward
                    enemies_killed += 1
                    hit_enemy.kill()
                bullet.kill()
            # Remove bullets that are off screen
            if (bullet.rect.x < -50 or bullet.rect.x > SCREEN_WIDTH + 50 or
                bullet.rect.y < -50 or bullet.rect.y > SCREEN_HEIGHT + 50):
                bullet.kill()
        
        # Enemy reaching base
        for enemy in enemies:
            if enemy.path_index >= len(enemy.path):
                base.take_damage(10)
                enemy.kill()
                if base.health <= 0:
                    game_over = True
    
    # Draw everything
    SCREEN.fill((20, 50, 20))  # Dark green background
    
    # Draw path
    draw_path()
    
    # Draw game objects
    base_group.draw(SCREEN)
    base.draw_health_bar(SCREEN)
    # Draw towers with custom draw method (for rotating head)
    for tower in towers:
        tower.draw(SCREEN)
    enemies.draw(SCREEN)
    bullets.draw(SCREEN)
    
    # Draw UI
    draw_ui()
    
    # Draw game over screen
    if game_over:
        draw_game_over()
    
    # Draw tower placement preview
    if not game_over:
        mouse_pos = pg.mouse.get_pos()
        tower_cost = 50
        if money >= tower_cost:
            if can_place_tower(mouse_pos):
                preview = pg.Surface((40, 40))
                preview.set_alpha(150)
                preview.fill((100, 200, 100))
                SCREEN.blit(preview, (mouse_pos[0] - 20, mouse_pos[1] - 20))
            else:
                preview = pg.Surface((40, 40))
                preview.set_alpha(150)
                preview.fill((200, 100, 100))
                SCREEN.blit(preview, (mouse_pos[0] - 20, mouse_pos[1] - 20))
    
    pg.display.flip()

pg.quit()
