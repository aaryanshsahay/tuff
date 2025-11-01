import pygame
import sys
import os
from dotenv import load_dotenv
from mystery_master import MurderMysteryMaster

load_dotenv()

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900

# Load and set custom cursor
cursor_sheet = pygame.image.load("assets/dialogue_box/20240711dragonMouseCursorBig-Sheet.png")
# The sheet is 92x23 with 4 cursors, each is roughly 23x23
# Extract the first cursor only
cursor_image = pygame.Surface((23, 23), pygame.SRCALPHA)
cursor_image.blit(cursor_sheet, (0, 0), (0, 0, 23, 23))
# Set the cursor with hotspot at (0, 0)
pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), cursor_image))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
LIGHT_GRAY = (200, 200, 200)
ACCENT_COLOR = (200, 50, 50)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Murder Mystery - The Mansion")

# Clock for FPS
clock = pygame.time.Clock()
FPS = 60

# Load backgrounds
background_layer_1 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_1.png")
background_layer_2 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_2.png")
background_layer_3 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_3.png")

# Scale backgrounds
background_layer_1 = pygame.transform.scale(background_layer_1, (SCREEN_WIDTH, SCREEN_HEIGHT))
background_layer_2 = pygame.transform.scale(background_layer_2, (SCREEN_WIDTH, SCREEN_HEIGHT))
background_layer_3 = pygame.transform.scale(background_layer_3, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Parallax offsets
parallax_offset_2 = 0
parallax_offset_3 = 0
parallax_speed_2 = 0.3
parallax_speed_3 = 0.5

# Character portraits mapping
CHARACTER_PORTRAITS = {
    "James": "assets/potrait/PNG/Transperent/Icon1.png",
    "Emma": "assets/potrait/PNG/Transperent/Icon2.png",
    "Nick": "assets/potrait/PNG/Transperent/Icon5.png",
    "Lisa": "assets/potrait/PNG/Transperent/Icon7.png",
    "Sarah": "assets/potrait/PNG/Transperent/Icon14.png",
    "David": "assets/potrait/PNG/Transperent/Icon39.png",
}

# Card dimensions
CARD_WIDTH = 280
CARD_HEIGHT = 350
CARD_PADDING = 30
CARDS_PER_ROW = 3


# Calculate card positions (3x2 grid)
def get_card_positions():
    positions = []
    left_padding = 150  # Left padding from window edge
    start_x = (
        SCREEN_WIDTH - (CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_PADDING)
    ) // 2
    start_x += left_padding  # Add left padding
    start_y = 150

    for row in range(2):
        for col in range(CARDS_PER_ROW):
            x = start_x + col * (CARD_WIDTH + CARD_PADDING)
            y = start_y + row * (CARD_HEIGHT + CARD_PADDING)
            positions.append((x, y))

    return positions


class InfoModal:
    def __init__(self, title, content, master_data):
        self.title = title
        self.content = content
        self.master_data = master_data
        self.is_open = False

        # Modal dimensions
        self.width = int(SCREEN_WIDTH * 0.75)  # 75% of screen width
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = 100

        # Load background image
        modal_bg = pygame.image.load("assets/dialogue_box/20240707dragon9SlicesA.png")
        self.modal_bg = pygame.transform.scale(modal_bg, (self.width, 900))  # Default height

        # Create font
        self.title_font = pygame.font.Font(None, 32)
        self.text_font = pygame.font.Font(None, 18)

    def generate_facts_content(self):
        """Generate facts content from game state"""
        facts = []
        facts.append(f"🔴 VICTIM: {self.master_data.victim}")
        facts.append(f"📍 CRIME LOCATION: {self.master_data.crime_location}")
        facts.append(f"☠️  CAUSE OF DEATH: {self.master_data.cause_of_death}")
        facts.append(f"⏰ TIME OF DEATH: {self.master_data.time_of_death}")
        facts.append("")
        facts.append("KNOWN CLUES:")
        for i, clue in enumerate(self.master_data.clues, 1):
            facts.append(f"  • {clue.get('clue', 'Unknown')}")
        return facts

    def generate_logs_content(self):
        """Generate investigation logs content"""
        logs = []
        logs.append("No interviews conducted yet.")
        return logs

    def draw(self, surface):
        """Draw the modal"""
        if not self.is_open:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Generate content based on title
        if self.title == "FACTS":
            lines = self.generate_facts_content()
        elif self.title == "LOGS":
            lines = self.generate_logs_content()
        else:
            lines = self.content.split("\n")

        # Calculate height based on content
        line_height = 25
        content_height = len(lines) * line_height + 150  # Increased padding from 80 to 150
        self.height = min(content_height, SCREEN_HEIGHT - 150)

        # Resize modal background
        self.modal_bg = pygame.transform.scale(
            pygame.image.load("assets/dialogue_box/20240707dragon9SlicesA.png"),
            (self.width, self.height),
        )

        # Draw modal background
        surface.blit(self.modal_bg, (self.x, self.y))

        # Draw title
        title_surface = self.title_font.render(self.title, True, WHITE)
        title_x = self.x + 80
        title_y = self.y + 50
        surface.blit(title_surface, (title_x, title_y))

        # Draw content
        content_x = self.x + 120
        content_y = self.y + 100
        for line in lines:
            if line.strip():
                line_surface = self.text_font.render(line, True, LIGHT_GRAY)
                surface.blit(line_surface, (content_x, content_y))
            content_y += line_height

        # Draw close button (X in top right)
        close_button_rect = self.get_close_button_rect()
        pygame.draw.rect(surface, (100, 50, 50), close_button_rect, 2)  # Red border

        # Draw X
        x_font = pygame.font.Font(None, 28)
        x_text = x_font.render("X", True, WHITE)
        x_x = close_button_rect.centerx - x_text.get_width() // 2
        x_y = close_button_rect.centery - x_text.get_height() // 2
        surface.blit(x_text, (x_x, x_y))

        # Draw close instruction
        close_font = pygame.font.Font(None, 16)
        close_text = close_font.render("Press ESC or click to close", True, LIGHT_GRAY)
        close_x = self.x + (self.width - close_text.get_width()) // 2
        close_y = self.y + self.height - 25
        surface.blit(close_text, (close_x, close_y))

    def toggle(self):
        """Toggle modal visibility"""
        self.is_open = not self.is_open

    def get_close_button_rect(self):
        """Get the rectangle for the close button"""
        close_button_size = 30
        close_x = self.x + self.width - close_button_size - 15
        close_y = self.y + 15
        return pygame.Rect(close_x, close_y, close_button_size, close_button_size)

    def is_close_clicked(self, mouse_pos):
        """Check if close button is clicked"""
        return self.get_close_button_rect().collidepoint(mouse_pos)


class MenuButton:
    def __init__(self, label, x, y, width, height):
        self.label = label
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_hovered = False

        # Load the button background image
        button_image = pygame.image.load("assets/dialogue_box/20240707dragon9SlicesB.png")
        self.button_bg = pygame.transform.scale(button_image, (width, height))

        # Create font
        self.font = pygame.font.Font(None, 24)

    def check_hover(self, mouse_pos):
        """Check if mouse is hovering over this button"""
        mouse_x, mouse_y = mouse_pos
        self.is_hovered = (
            self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height
        )

    def draw(self, surface):
        """Draw the button"""
        # Draw background image
        surface.blit(self.button_bg, (self.x, self.y))

        # Draw border on hover
        if self.is_hovered:
            pygame.draw.rect(surface, (100, 200, 255), (self.x, self.y, self.width, self.height), 3)

        # Draw label text
        text_surface = self.font.render(self.label, True, WHITE)
        text_x = self.x + (self.width - text_surface.get_width()) // 2
        text_y = self.y + (self.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))

    def is_clicked(self, mouse_pos):
        """Check if button is clicked"""
        return self.is_hovered


class CharacterCard:
    def __init__(self, suspect_data, x, y):
        self.suspect = suspect_data
        self.x = x
        self.y = y
        self.width = CARD_WIDTH
        self.height = CARD_HEIGHT
        self.is_hovered = False

        # Load portrait
        portrait_path = CHARACTER_PORTRAITS.get(suspect_data["name"])
        if portrait_path and os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path)
            # Scale portrait to fit in card
            self.portrait = pygame.transform.scale(self.portrait, (180, 180))
        else:
            self.portrait = None

        # Create font
        self.title_font = pygame.font.Font(None, 28)
        self.text_font = pygame.font.Font(None, 20)

    def check_hover(self, mouse_pos):
        """Check if mouse is hovering over this card"""
        mouse_x, mouse_y = mouse_pos
        self.is_hovered = (
            self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height
        )

    def draw(self, surface):
        # Create a semi-transparent surface for the card
        card_surface = pygame.Surface((self.width, self.height))
        card_surface.set_alpha(204)  # 80% opaque (204/255 ≈ 0.8)
        card_surface.fill(DARK_GRAY)
        surface.blit(card_surface, (self.x, self.y))

        # Draw card border - changes color on hover
        border_color = (100, 200, 255) if self.is_hovered else ACCENT_COLOR  # Light blue on hover
        border_width = 4 if self.is_hovered else 3
        pygame.draw.rect(
            surface, border_color, (self.x, self.y, self.width, self.height), border_width
        )

        # Draw portrait
        if self.portrait:
            portrait_x = self.x + (self.width - self.portrait.get_width()) // 2
            portrait_y = self.y + 20
            surface.blit(self.portrait, (portrait_x, portrait_y))
        else:
            # Draw placeholder if portrait not found
            placeholder_text = self.text_font.render(
                f"No image: {self.suspect['name']}", True, LIGHT_GRAY
            )
            placeholder_x = self.x + 20
            placeholder_y = self.y + 50
            surface.blit(placeholder_text, (placeholder_x, placeholder_y))

        # Draw name
        name_text = self.title_font.render(self.suspect["name"], True, WHITE)
        name_x = self.x + (self.width - name_text.get_width()) // 2
        name_y = self.y + 210
        surface.blit(name_text, (name_x, name_y))

        # Draw age and occupation
        age_text = self.text_font.render(f"Age: {self.suspect['age']}", True, LIGHT_GRAY)
        age_x = self.x + 20
        age_y = self.y + 250
        surface.blit(age_text, (age_x, age_y))

        occupation_text = self.text_font.render(
            f"Occupation: {self.suspect['occupation']}", True, LIGHT_GRAY
        )
        occupation_x = self.x + 20
        occupation_y = self.y + 280
        surface.blit(occupation_text, (occupation_x, occupation_y))

        # Draw gender
        gender_text = self.text_font.render(f"Gender: {self.suspect['gender']}", True, LIGHT_GRAY)
        gender_x = self.x + 20
        gender_y = self.y + 310
        surface.blit(gender_text, (gender_x, gender_y))


def draw_background():
    """Draw parallax background"""
    global parallax_offset_2, parallax_offset_3

    # Draw static layer 1
    screen.blit(background_layer_1, (0, 0))

    # Draw parallax layer 2
    tile_offset_2 = parallax_offset_2 % SCREEN_WIDTH
    screen.blit(background_layer_2, (tile_offset_2 - SCREEN_WIDTH, 0))
    screen.blit(background_layer_2, (tile_offset_2, 0))
    if tile_offset_2 + SCREEN_WIDTH < SCREEN_WIDTH:
        screen.blit(background_layer_2, (tile_offset_2 + SCREEN_WIDTH, 0))

    # Draw parallax layer 3
    tile_offset_3 = parallax_offset_3 % SCREEN_WIDTH
    screen.blit(background_layer_3, (tile_offset_3 - SCREEN_WIDTH, 0))
    screen.blit(background_layer_3, (tile_offset_3, 0))
    if tile_offset_3 + SCREEN_WIDTH < SCREEN_WIDTH:
        screen.blit(background_layer_3, (tile_offset_3 + SCREEN_WIDTH, 0))

    # Update parallax offsets
    parallax_offset_2 -= parallax_speed_2
    parallax_offset_3 -= parallax_speed_3


def main():
    # Setup game with master agent
    print("🔍 Setting up murder mystery case...\n")
    master = MurderMysteryMaster()

    if not master.generate_case_state():
        print("❌ Failed to generate case")
        pygame.quit()
        sys.exit()

    master.build_world_state()
    print("✅ Game setup complete!\n")

    # Create menu buttons on the left side
    button_width = 240
    button_height = 200
    button_x = 20
    button_y_start = 200
    button_spacing = 200

    menu_buttons = [
        MenuButton("FACTS", button_x, button_y_start, button_width, button_height),
        MenuButton("LOGS", button_x, button_y_start + button_spacing, button_width, button_height),
        MenuButton(
            "ACCUSE", button_x, button_y_start + button_spacing * 2, button_width, button_height
        ),
    ]

    # Create modals for FACTS and LOGS
    facts_modal = InfoModal("FACTS", "", master)
    logs_modal = InfoModal("LOGS", "", master)

    # Create character cards (excluding victim)
    card_positions = get_card_positions()
    cards = []
    card_index = 0

    for suspect_name in sorted(master.suspects.keys()):
        suspect = master.suspects[suspect_name]
        if not suspect["is_victim"] and card_index < len(card_positions):
            x, y = card_positions[card_index]
            card = CharacterCard(suspect, x, y)
            cards.append(card)
            card_index += 1

    # Print case info to terminal
    print("=" * 80)
    print("MURDER MYSTERY - CASE BRIEFING")
    print("=" * 80)
    print(f"🔴 VICTIM: {master.victim}")
    print(f"🔪 MURDERER: {master.murderer}")
    print(f"📍 CRIME LOCATION: {master.crime_location}")
    print(f"☠️  CAUSE OF DEATH: {master.cause_of_death}")
    print(f"⏰ TIME OF DEATH: {master.time_of_death}\n")

    # Main game loop
    running = True
    while running:
        clock.tick(FPS)

        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Close modals if open, otherwise exit
                    if facts_modal.is_open:
                        facts_modal.toggle()
                    elif logs_modal.is_open:
                        logs_modal.toggle()
                    else:
                        running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle button clicks
                if facts_modal.is_open:
                    # Check if close button is clicked
                    if facts_modal.is_close_clicked(mouse_pos):
                        facts_modal.toggle()
                elif logs_modal.is_open:
                    # Check if close button is clicked
                    if logs_modal.is_close_clicked(mouse_pos):
                        logs_modal.toggle()
                else:
                    # Check menu button clicks
                    for button in menu_buttons:
                        if button.is_clicked(mouse_pos):
                            if button.label == "FACTS":
                                facts_modal.toggle()
                            elif button.label == "LOGS":
                                logs_modal.toggle()
                            elif button.label == "ACCUSE":
                                pass  # TODO: Implement accuse functionality

        # Update hover states
        for card in cards:
            card.check_hover(mouse_pos)
        for button in menu_buttons:
            button.check_hover(mouse_pos)

        # Draw background
        draw_background()

        # Draw title
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("THE MANSION - SELECT A SUSPECT TO INTERVIEW", True, WHITE)
        title_x = (SCREEN_WIDTH - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, 30))

        # Draw menu buttons
        for button in menu_buttons:
            button.draw(screen)

        # Draw character cards
        for card in cards:
            card.draw(screen)

        # Draw modals on top
        facts_modal.draw(screen)
        logs_modal.draw(screen)

        # Update display
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
