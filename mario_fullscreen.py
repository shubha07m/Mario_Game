import pygame
import sys
import random

# Initialize Pygame and Mixer for sound
pygame.init()
pygame.mixer.init()

# Full-screen mode setup; get current display resolution
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Mario Clone - Fullscreen Fun Edition")

# Colors
SKY_BLUE = (135, 206, 235)
GREEN = (0, 200, 0)
BROWN = (139, 69, 19)
WHITE = (255, 255, 255)
YELLOW = (255, 223, 0)
SPARKLE_COLOR = (255, 255, 255)

# Clock and FPS
clock = pygame.time.Clock()
FPS = 60

# Level dimensions
LEVEL_WIDTH = 3000  # a wider level now for more exploration

# Load assets
try:
    mario_img_orig = pygame.image.load("mario.png").convert_alpha()
    mario_img_orig = pygame.transform.scale(mario_img_orig, (50, 50))
except Exception as e:
    print("Mario sprite not found, using placeholder.")
    mario_img_orig = None

try:
    coin_img = pygame.image.load("coin.png").convert_alpha()
    coin_img = pygame.transform.scale(coin_img, (30, 30))
except Exception as e:
    coin_img = None

# Load sounds
try:
    pygame.mixer.music.load("mario_theme.mp3")
    pygame.mixer.music.play(-1)
except Exception as e:
    print("Background music not found or failed to load.")

try:
    coin_sound = pygame.mixer.Sound("coin_sound.mp3")
except Exception as e:
    coin_sound = None

try:
    jump_sound = pygame.mixer.Sound("jump_sound.mp3")
except Exception as e:
    jump_sound = None

# Fonts
font_big = pygame.font.SysFont("Arial", 50)
font_med = pygame.font.SysFont("Arial", 30)

# Player properties
player = pygame.Rect(100, HEIGHT - 150, 50, 50)
player_vel_y = 0
GRAVITY = 1
JUMP_STRENGTH = -15
on_ground = False

# For forward-only scoring, track the furthest right reached
max_x_reached = player.x

# Platforms: Create continuous ground and some floating platforms
ground = [pygame.Rect(x, HEIGHT - 100, 100, 100) for x in range(0, LEVEL_WIDTH, 100)]
floating = [
    pygame.Rect(300, HEIGHT - 250, 100, 20),
    pygame.Rect(800, HEIGHT - 300, 120, 20),
    pygame.Rect(1300, HEIGHT - 220, 100, 20),
    pygame.Rect(1900, HEIGHT - 280, 120, 20),
    pygame.Rect(2400, HEIGHT - 240, 100, 20)
]

# Coins: on floating platforms and on the ground
coins = []
def reset_coins():
    global coins
    coins = []
    for plat in floating:
        coin_x = plat.x + plat.width // 2 - 15
        coin_y = plat.y - 35
        coins.append(pygame.Rect(coin_x, coin_y, 30, 30))
    for x in range(200, LEVEL_WIDTH, 250):
        coins.append(pygame.Rect(x, HEIGHT - 150, 30, 30))
reset_coins()

# Excitement effect variables
excitement_timer = 0  # frames to keep Mario enlarged after coin collection
EXCITEMENT_DURATION = 20  # frames to show excitement

# Sparkle effect: list of particles (each a dict with position and lifetime)
sparkles = []

def add_sparkles(x, y):
    # Add a few particles for a sparkle effect
    for _ in range(8):
        particle = {
            "x": x,
            "y": y,
            "radius": random.randint(2, 4),
            "dx": random.uniform(-2, 2),
            "dy": random.uniform(-2, 2),
            "life": random.randint(15, 30)
        }
        sparkles.append(particle)

def update_sparkles():
    for p in sparkles[:]:
        p["x"] += p["dx"]
        p["y"] += p["dy"]
        p["life"] -= 1
        if p["life"] <= 0:
            sparkles.remove(p)

def draw_sparkles(surface, offset_x):
    for p in sparkles:
        pos = (int(p["x"] - offset_x), int(p["y"]))
        pygame.draw.circle(surface, SPARKLE_COLOR, pos, p["radius"])

def draw_text(surface, text, pos, font, color=WHITE):
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, pos)

def handle_camera(player_rect):
    # Calculate camera offset so player is centered (clamped to level bounds)
    offset_x = player_rect.centerx - WIDTH // 2
    offset_x = max(0, min(offset_x, LEVEL_WIDTH - WIDTH))
    return offset_x

# Game state flags
game_active = False
game_over = False

while True:
    clock.tick(FPS)
    screen.fill(SKY_BLUE)

    # Quit on pressing Q at any time
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

    # Start or Game Over screen
    if not game_active:
        if game_over:
            draw_text(screen, "Game Over!", (WIDTH//2 - 120, HEIGHT//2 - 80), font_big)
            draw_text(screen, f"Final Score: {score}", (WIDTH//2 - 100, HEIGHT//2 - 30), font_med)
        draw_text(screen, "Press SPACE to Start", (WIDTH//2 - 160, HEIGHT//2 + 20), font_med)
        pygame.display.flip()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            # Reset state and start game
            game_active = True
            game_over = False
            player.x, player.y = 100, HEIGHT - 150
            player_vel_y = 0
            score = 0
            max_x_reached = player.x
            excitement_timer = 0
            reset_coins()
            sparkles = []
        continue

    # Handle continuous key state
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.x -= 5
    if keys[pygame.K_RIGHT]:
        player.x += 5
        # Increase score only when Mario moves beyond his furthest x reached
        if player.x > max_x_reached:
            score += (player.x - max_x_reached)
            max_x_reached = player.x
    if keys[pygame.K_SPACE] and on_ground:
        player_vel_y = JUMP_STRENGTH
        on_ground = False
        if jump_sound:
            jump_sound.play()

    # Apply gravity
    player.y += player_vel_y
    player_vel_y += GRAVITY

    # Collision with platforms (ground and floating)
    on_ground = False
    for platform in ground + floating:
        if player.colliderect(platform) and player_vel_y >= 0:
            player.bottom = platform.top
            player_vel_y = 0
            on_ground = True

    # Collect coins
    for coin in coins[:]:
        if player.colliderect(coin):
            coins.remove(coin)
            # Play coin sound
            if coin_sound:
                coin_sound.play()
            # Increase score significantly
            score += 50
            # Trigger excitement effect and add sparkles
            excitement_timer = EXCITEMENT_DURATION
            add_sparkles(player.centerx, player.y)

    # Update excitement timer
    if excitement_timer > 0:
        excitement_timer -= 1

    # Calculate camera offset
    offset_x = handle_camera(player)

    # Draw platforms (ground and floating) with camera offset
    for block in ground:
        pygame.draw.rect(screen, GREEN, (block.x - offset_x, block.y, block.width, block.height))
    for platform in floating:
        pygame.draw.rect(screen, BROWN, (platform.x - offset_x, platform.y, platform.width, platform.height))

    # Draw coins
    for coin in coins:
        coin_rect = pygame.Rect(coin.x - offset_x, coin.y, coin.width, coin.height)
        if coin_img:
            screen.blit(coin_img, coin_rect)
        else:
            pygame.draw.ellipse(screen, YELLOW, coin_rect)

    # Draw sparkles
    update_sparkles()
    draw_sparkles(screen, offset_x)

    # Draw Mario; if excitement is active, draw him slightly larger
    if excitement_timer > 0:
        scale = 1.5
    else:
        scale = 1.0

    mario_width = int(50 * scale)
    mario_height = int(50 * scale)
    if mario_img_orig:
        mario_img = pygame.transform.scale(mario_img_orig, (mario_width, mario_height))
        # Adjust drawing so center remains approximately the same
        draw_x = player.x - offset_x - (mario_width - player.width) // 2
        draw_y = player.y - (mario_height - player.height)
        screen.blit(mario_img, (draw_x, draw_y))
    else:
        draw_x = player.x - offset_x
        pygame.draw.rect(screen, (200, 0, 0), (draw_x, player.y, mario_width, mario_height))

    # Draw score
    draw_text(screen, f"Score: {score}", (10, 10), font_med)

    # Check game over (if Mario falls off the screen)
    if player.y > HEIGHT + 100:
        game_active = False
        game_over = True

    pygame.display.flip()
