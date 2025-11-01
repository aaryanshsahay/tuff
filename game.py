import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLUE = (100, 149, 237)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Parallax Scrolling Game")

# Clock for FPS
clock = pygame.time.Clock()
FPS = 60

# Load backgrounds
background_layer_1 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_1.png")
background_layer_2 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_2.png")
background_layer_3 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_3.png")

# Scale images to fit screen
background_layer_1 = pygame.transform.scale(background_layer_1, (SCREEN_WIDTH, SCREEN_HEIGHT))
background_layer_2 = pygame.transform.scale(background_layer_2, (SCREEN_WIDTH, SCREEN_HEIGHT))
background_layer_3 = pygame.transform.scale(background_layer_3, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Load grass sprites
grass_1 = pygame.image.load("assets/oak_woods_v1.0/decorations/grass_1.png")
grass_2 = pygame.image.load("assets/oak_woods_v1.0/decorations/grass_2.png")
grass_3 = pygame.image.load("assets/oak_woods_v1.0/decorations/grass_3.png")

# Scale grass sprites (adjust the multiplier to make them bigger or smaller)
scale_factor = 10  # Change this number: 2 = 2x bigger, 3 = 3x bigger, 4 = 4x
grass_1 = pygame.transform.scale(
    grass_1, (grass_1.get_width() * scale_factor, grass_1.get_height() * scale_factor)
)
grass_2 = pygame.transform.scale(
    grass_2, (grass_2.get_width() * scale_factor, grass_2.get_height() * scale_factor)
)
grass_3 = pygame.transform.scale(
    grass_3, (grass_3.get_width() * scale_factor, grass_3.get_height() * scale_factor)
)

# Get grass dimensions
grass_width = grass_1.get_width()
grass_height = grass_1.get_height()

# Load player sprite
player_sprite = pygame.image.load("assets/MinifolksHumans/Without Outline/MiniPrinceMan.png")
player_sprite = pygame.transform.scale(player_sprite, (64, 64))  # Scale to 64x64 pixels
player_width = player_sprite.get_width()
player_height = player_sprite.get_height()

# Player position
player_x = SCREEN_WIDTH // 2
player_y = SCREEN_HEIGHT // 2
player_speed = 5

# Parallax offsets for each layer
parallax_offset_2 = 0
parallax_offset_3 = 0
parallax_speed_2 = 0.4  # Layer 2 moves slower (background)
parallax_speed_3 = 0.8  # Layer 3 moves faster (foreground)

# Grass offset for ground scrolling
grass_offset = 0
grass_speed = 1.0  # Grass moves at same speed as player input

# Game loop
running = True
while running:
    clock.tick(FPS)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Input handling
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        parallax_offset_2 += player_speed * parallax_speed_2
        parallax_offset_3 += player_speed * parallax_speed_3
        grass_offset -= player_speed * grass_speed
    if keys[pygame.K_RIGHT]:
        parallax_offset_2 -= player_speed * parallax_speed_2
        parallax_offset_3 -= player_speed * parallax_speed_3
        grass_offset += player_speed * grass_speed

    # Draw background layer 1 (static)
    screen.blit(background_layer_1, (0, 0))

    # Draw tiling parallax layer 2 (background, slower)
    tile_offset_2 = parallax_offset_2 % SCREEN_WIDTH
    for i in range(-1, 3):
        x_pos = i * SCREEN_WIDTH + tile_offset_2
        screen.blit(background_layer_2, (x_pos, 0))

    # Draw tiling parallax layer 3 (foreground, faster) on top
    tile_offset_3 = parallax_offset_3 % SCREEN_WIDTH
    for i in range(-1, 3):
        x_pos = i * SCREEN_WIDTH + tile_offset_3
        screen.blit(background_layer_3, (x_pos, 0))

    # Draw grass ground at the bottom
    # Pattern: 4x grass_1, 3x grass_2, 2x grass_3 (total width = 9 grass sprites)
    pattern = [grass_1] * 4 + [grass_2] * 3 + [grass_3] * 2
    pattern_width = grass_width * 9

    # Calculate grass position with offset
    grass_y = SCREEN_HEIGHT - grass_height
    tile_offset_grass = grass_offset % pattern_width

    # Draw grass tiles
    x_pos = -tile_offset_grass
    for i in range(10):  # Draw enough tiles to cover screen
        for grass_sprite in pattern:
            screen.blit(grass_sprite, (x_pos, grass_y))
            x_pos += grass_width

    # Draw player sprite in the center
    screen.blit(player_sprite, (player_x - player_width // 2, player_y - player_height // 2))

    # Update display
    pygame.display.flip()

pygame.quit()
sys.exit()
