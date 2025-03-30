import pygame
pygame.init()

WIN = pygame.display.set_mode((1600, 900))  # Doubled window size
pygame.display.set_caption("Platformer")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)

# Load and scale background images
bg_sky = pygame.Surface((1600, 900))
bg_sky.fill((135, 206, 235))  # Light blue sky

bg_clouds = pygame.Surface((1600, 900), pygame.SRCALPHA)
for i in range(10):  # Add some clouds
    x = i * 160
    y = 100 + (i % 3) * 50
    pygame.draw.ellipse(bg_clouds, (255, 255, 255, 128), (x, y, 120, 60))

bg_mountains = pygame.Surface((1600, 900), pygame.SRCALPHA)
for i in range(5):  # Add mountains
    points = [(i*400-50, 900), (i*400+200, 500), (i*400+450, 900)]
    pygame.draw.polygon(bg_mountains, (100, 100, 100, 180), points)

class Door:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 60)
        self.active = False
    
    def draw(self, surface):
        if self.active:
            pygame.draw.rect(surface, BROWN, self.rect)
            # Door handle
            pygame.draw.circle(surface, BLACK, (self.rect.right - 10, self.rect.centery), 4)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.vel_y = 0
        self.jumps = 2
        self.score = 0
        self.alive = True
        self.lives = 3
        self.can_double_jump = True
        self.won = False
    
    def reset(self):
        self.rect.x = 100
        self.rect.y = 800
        self.vel_y = 0
        self.jumps = 2
        self.score = 0
        self.alive = True
        self.lives = 3
        self.can_double_jump = True
        self.won = False
    
    def move(self, platforms, coins, enemies, door):
        if not self.alive:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                self.reset()
                return True
            return False

        if self.won:
            return False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= 7  # Slightly faster movement
        if keys[pygame.K_RIGHT]:
            self.rect.x += 7
        if keys[pygame.K_SPACE]:
            if self.jumps > 0:
                self.vel_y = -15
                self.jumps -= 1
                if self.jumps == 1:
                    self.can_double_jump = True
            elif self.can_double_jump:
                self.vel_y = -15
                self.can_double_jump = False
        
        self.vel_y += 0.8  # Smoother gravity
        if self.vel_y > 10:
            self.vel_y = 10
        self.rect.y += self.vel_y
        
        for plat in platforms:
            if self.rect.colliderect(plat.rect if hasattr(plat, 'rect') else plat):
                if self.vel_y > 0:
                    self.rect.bottom = plat.rect.top if hasattr(plat, 'rect') else plat.top
                    self.vel_y = 0
                    self.jumps = 2
                    self.can_double_jump = True
                elif self.vel_y < 0:
                    self.rect.top = plat.rect.bottom if hasattr(plat, 'rect') else plat.bottom
                    self.vel_y = 0

        for coin in coins[:]:
            if self.rect.colliderect(coin.rect):
                coins.remove(coin)
                self.score += 10

        for enemy in enemies[:]:
            if self.rect.colliderect(enemy.rect):
                if self.vel_y > 0 and self.rect.bottom < enemy.rect.centery:
                    enemies.remove(enemy)
                    self.vel_y = -10
                    self.score += 50
                else:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.alive = False
                    else:
                        self.rect.x = 100
                        self.rect.y = 800  # Adjusted spawn point
                        self.vel_y = 0
        
        # Check if all enemies are defeated to activate door
        if len(enemies) == 0:
            door.active = True
            if self.rect.colliderect(door.rect):
                self.won = True
        
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 1600:  # Adjusted for larger window
            self.rect.right = 1600
        if self.rect.top > 900:  # Adjusted for larger window
            self.rect.y = 0
        return False

class MovingPlatform:
    def __init__(self, x, y, w, h, speed, x_range):
        self.rect = pygame.Rect(x, y, w, h)
        self.speed = speed
        self.x_range = x_range
        self.start_x = x
    
    def update(self):
        self.rect.x += self.speed
        if self.rect.x < self.start_x or self.rect.x > self.start_x + self.x_range:
            self.speed *= -1

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 15, 15)
        self.y_offset = 0
        self.bounce_speed = 2
        self.original_y = y
    
    def update(self):
        self.y_offset += self.bounce_speed
        if abs(self.y_offset) > 10:
            self.bounce_speed *= -1
        self.rect.y = self.original_y + self.y_offset

class Enemy:
    def __init__(self, x, y, speed):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.speed = speed
        self.direction = 1
        self.vel_y = 0
    
    def update(self, platforms):
        self.vel_y += 0.8  # Gravity for enemies
        if self.vel_y > 10:
            self.vel_y = 10
        self.rect.y += self.vel_y
        
        # Horizontal movement
        self.rect.x += self.speed * self.direction
        
        # Platform collision and edge detection
        on_ground = False
        for platform in platforms:
            plat_rect = platform.rect if hasattr(platform, 'rect') else platform
            
            # Vertical collision
            if self.rect.colliderect(plat_rect):
                if self.vel_y > 0:
                    self.rect.bottom = plat_rect.top
                    self.vel_y = 0
                    on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = plat_rect.bottom
                    self.vel_y = 0
            
            # Turn around at platform edges when on ground
            if on_ground and abs(self.rect.bottom - plat_rect.top) < 5:
                if self.direction > 0 and self.rect.right >= plat_rect.right:
                    self.direction = -1
                elif self.direction < 0 and self.rect.left <= plat_rect.left:
                    self.direction = 1
        
        # Screen bounds
        if self.rect.left < 0:
            self.direction = 1
        if self.rect.right > 1600:  # Adjusted for larger window
            self.direction = -1

platforms = [
    pygame.Rect(0, 850, 1600, 50),  # Ground
    pygame.Rect(200, 700, 300, 20),
    pygame.Rect(600, 600, 300, 20),
    pygame.Rect(1000, 500, 300, 20),
    MovingPlatform(400, 400, 200, 20, 3, 300),
    MovingPlatform(800, 300, 200, 20, -3, 400)
]

coins = [
    Coin(300, 650),
    Coin(400, 650),
    Coin(700, 550),
    Coin(800, 550),
    Coin(1100, 450),
    Coin(1200, 450),
    Coin(500, 350),
    Coin(900, 250)
]

enemies = [
    Enemy(300, 820, 3),
    Enemy(700, 570, 2),
    Enemy(1100, 470, 3),
    Enemy(500, 370, 2)
]

player = Player(100, 800)
door = Door(900, 240)  # Place door on top platform

clock = pygame.time.Clock()
run = True
while run:
    clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    
    if player.move(platforms, coins, enemies, door):
        # Reset game state when player restarts
        coins = [
            Coin(300, 650),
            Coin(400, 650),
            Coin(700, 550),
            Coin(800, 550),
            Coin(1100, 450),
            Coin(1200, 450),
            Coin(500, 350),
            Coin(900, 250)
        ]
        enemies = [
            Enemy(300, 820, 3),
            Enemy(700, 570, 2),
            Enemy(1100, 470, 3),
            Enemy(500, 370, 2)
        ]
        door.active = False
    
    for plat in platforms:
        if isinstance(plat, MovingPlatform):
            plat.update()
    
    for enemy in enemies:
        enemy.update(platforms)
    
    for coin in coins:
        coin.update()
    
    # Draw layered backgrounds
    WIN.blit(bg_sky, (0, 0))
    WIN.blit(bg_clouds, (0, 0))
    WIN.blit(bg_mountains, (0, 0))
    
    # Draw grid lines
    for i in range(0, 900, 20):
        pygame.draw.line(WIN, (255, 255, 255, 128), (0, i), (1600, i), 1)
    
    for coin in coins:
        pygame.draw.rect(WIN, YELLOW, coin.rect)
    
    for enemy in enemies:
        pygame.draw.rect(WIN, GREEN, enemy.rect)
    
    if player.alive and not player.won:
        pygame.draw.rect(WIN, RED, player.rect)
    elif not player.alive:
        font = pygame.font.Font(None, 74)
        game_over_text = font.render('Game Over! Press R to restart', True, WHITE)
        text_rect = game_over_text.get_rect(center=(800, 450))
        WIN.blit(game_over_text, text_rect)
    elif player.won:
        font = pygame.font.Font(None, 74)
        win_text = font.render('You Won!', True, WHITE)
        text_rect = win_text.get_rect(center=(800, 450))
        WIN.blit(win_text, text_rect)
    
    for plat in platforms:
        pygame.draw.rect(WIN, BLACK, plat.rect if hasattr(plat, 'rect') else plat)
    
    door.draw(WIN)
    
    font = pygame.font.Font(None, 36)
    score_text = font.render(f'Score: {player.score}', True, WHITE)
    lives_text = font.render(f'Lives: {player.lives}', True, WHITE)
    WIN.blit(score_text, (10, 10))
    WIN.blit(lives_text, (10, 50))
    
    pygame.display.flip()

pygame.quit()
