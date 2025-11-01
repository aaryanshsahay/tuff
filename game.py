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

# Load heart sprite for health bar
heart_sprite = pygame.image.load("assets/hearts/PNG/basic/heart.png")
heart_sprite = pygame.transform.scale(heart_sprite, (32, 32))  # Scale heart to 32x32
heart_width = heart_sprite.get_width()
heart_height = heart_sprite.get_height()

# Health system
max_health = 5
current_health = 5
heart_spacing = 40  # Space between hearts

# Load dialogue box
dialogue_box = pygame.image.load("assets/dialogue_box/20240707dragonHeaderB.png")
dialogue_box = pygame.transform.scale(dialogue_box, (600, 150))  # Adjust size as needed
dialogue_box_width = dialogue_box.get_width()
dialogue_box_height = dialogue_box.get_height()

# Dialogue text
dialogue_font = pygame.font.Font(None, 32)  # None uses default font, 32 is size
dialogue_text = "Mushroom: You shall not pass!"
dialogue_color = (0, 0, 0)  # Black text

# Load player sprite sheet
sprite_sheet = pygame.image.load("assets/MinifolksHumans/Without Outline/MiniPrinceMan.png")

# Sprite sheet dimensions
sprite_width = 32  # Width of each sprite frame
sprite_height = 32  # Height of each sprite frame
player_scale = 3.5  # Change this number to make player bigger or smaller


# Function to extract and scale frames from a row
def extract_row_frames(sprite_sheet, row, num_frames_to_extract, skip_last=0):
    frames = []
    num_frames = sprite_sheet.get_width() // sprite_width
    for i in range(max(1, num_frames - skip_last)):
        if i >= num_frames_to_extract:
            break
        frame = sprite_sheet.subsurface(
            pygame.Rect(i * sprite_width, row * sprite_height, sprite_width, sprite_height)
        )
        frame = pygame.transform.scale(frame, (64, 64))
        frame = pygame.transform.scale(
            frame, (frame.get_width() * player_scale, frame.get_height() * player_scale)
        )
        frames.append(frame)
    return frames


# Load animations for different directions
idle_frames = extract_row_frames(
    sprite_sheet, row=0, num_frames_to_extract=100, skip_last=2
)  # Row 0 (idle)
forward_frames = extract_row_frames(
    sprite_sheet, row=1, num_frames_to_extract=6, skip_last=0
)  # Row 1 (forward, 6 frames)
# Create left animation by flipping the forward frames
left_frames = [pygame.transform.flip(frame, True, False) for frame in forward_frames]

# Current animation state
current_frame = 0
current_animation = "idle"
player_frames = idle_frames
animation_speed = 10  # Change frames every N ticks
animation_counter = 0

# Player position and dimensions
player_x = SCREEN_WIDTH // 2
player_speed = 5
player_width = idle_frames[0].get_width()
player_height = idle_frames[0].get_height()
# Position player on the ground (will be updated after grass height is known)
player_y = SCREEN_HEIGHT - grass_height - player_height // 2.5

# Parallax offsets for each layer
parallax_offset_2 = 0
parallax_offset_3 = 0
parallax_speed_2 = 0.4  # Layer 2 moves slower (background)
parallax_speed_3 = 0.8  # Layer 3 moves faster (foreground)

# Grass offset for ground scrolling
grass_offset = 0
grass_speed = 1.0  # Grass moves at same speed as player input

# Load enemy sprite sheet
enemy_sprite_sheet = pygame.image.load(
    "assets/Monster_Creatures_Fantasy(Version 1.3)/Mushroom/Attack3.png"
)

# Enemy sprite dimensions
enemy_sprite_width = 150  # Each frame is 150x150
enemy_sprite_height = 150  # Each frame is 150x150
enemy_scale = 1.0  # Already large, minimal scaling needed


# Function to extract enemy frames (reuse from player)
def extract_enemy_frames(sprite_sheet, row, num_frames):
    frames = []
    for i in range(num_frames):
        frame = sprite_sheet.subsurface(
            pygame.Rect(
                i * enemy_sprite_width,
                row * enemy_sprite_height,
                enemy_sprite_width,
                enemy_sprite_height,
            )
        )
        # Scale to reasonable display size
        frame = pygame.transform.scale(frame, (240, 240))
        frame = pygame.transform.scale(
            frame, (frame.get_width() * enemy_scale, frame.get_height() * enemy_scale)
        )
        frames.append(frame)
    return frames


# Load enemy attack animation (row 0, 11 frames)
enemy_frames = extract_enemy_frames(enemy_sprite_sheet, row=0, num_frames=11)

# Enemy position and animation
enemy_x = SCREEN_WIDTH + 200  # Start off-screen to the right
enemy_y = SCREEN_HEIGHT - grass_height - 20
enemy_width = enemy_frames[0].get_width()
enemy_height = enemy_frames[0].get_height()
enemy_current_frame = 0
enemy_animation_counter = 0
enemy_animation_speed = 10
enemy_fixed_x = SCREEN_WIDTH - 200  # Fixed position where enemy appears after intro

# Game state
game_state = "intro"  # States: "intro", "battle", "choice"
intro_timer = 0
intro_duration = 180  # 3 seconds at 60 FPS

# Health reveal animation
hearts_revealed = 0
heart_reveal_timer = 0
heart_reveal_delay = 30  # Frames between each heart reveal (0.5 seconds)

# Game loop
running = True
while running:
    clock.tick(FPS)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Game state logic
    new_animation = "idle"

    if game_state == "intro":
        # Auto-run to the right for 3 seconds
        parallax_offset_2 -= player_speed * parallax_speed_2
        parallax_offset_3 -= player_speed * parallax_speed_3
        grass_offset += player_speed * grass_speed
        new_animation = "forward"

        intro_timer += 1
        if intro_timer >= intro_duration:
            game_state = "battle"
            intro_timer = 0
            hearts_revealed = 0  # Reset hearts when battle starts

    elif game_state == "battle":
        # Position enemy at fixed location
        enemy_x = enemy_fixed_x

        # No input, just display the encounter
        # Update heart reveal animation
        heart_reveal_timer += 1
        if heart_reveal_timer >= heart_reveal_delay and hearts_revealed < max_health:
            heart_reveal_timer = 0
            hearts_revealed += 1

    else:  # game_state == "choice"
        # Add choice input handling here later
        pass

    # Switch animation if direction changed
    if new_animation != current_animation:
        current_animation = new_animation
        if new_animation == "idle":
            player_frames = idle_frames
        elif new_animation == "forward":
            player_frames = forward_frames
        elif new_animation == "left":
            player_frames = left_frames
        current_frame = 0
        animation_counter = 0

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

    # Update player animation
    animation_counter += 1
    if animation_counter >= animation_speed:
        animation_counter = 0
        current_frame = (current_frame + 1) % len(player_frames)

    # Update enemy animation
    enemy_animation_counter += 1
    if enemy_animation_counter >= enemy_animation_speed:
        enemy_animation_counter = 0
        enemy_current_frame = (enemy_current_frame + 1) % len(enemy_frames)

    # Draw health hearts in top left (only show during battle state)
    if game_state == "battle":
        for i in range(hearts_revealed):
            heart_x = 10 + i * heart_spacing
            heart_y = 10
            screen.blit(heart_sprite, (heart_x, heart_y))

        # Draw dialogue box below hearts
        dialogue_box_x = 10
        dialogue_box_y = 65  # Below the hearts
        screen.blit(dialogue_box, (dialogue_box_x, dialogue_box_y))

        # Draw dialogue text on the box
        dialogue_surface = dialogue_font.render(dialogue_text, True, dialogue_color)
        text_x = dialogue_box_x + 130  # Padding from left
        text_y = dialogue_box_y + 60  # Padding from top
        screen.blit(dialogue_surface, (text_x, text_y))

    # Draw player sprite in the center
    screen.blit(
        player_frames[current_frame], (player_x - player_width // 2, player_y - player_height // 2)
    )

    # Draw enemy sprite
    screen.blit(
        enemy_frames[enemy_current_frame], (enemy_x - enemy_width // 2, enemy_y - enemy_height // 2)
    )

    # Update display
    pygame.display.flip()

pygame.quit()
sys.exit()
