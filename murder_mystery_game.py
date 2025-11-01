import pygame
import sys
import os
import threading
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


class ConversationScreen:
    def __init__(self, suspect_data, agent, screen_width, screen_height, logs_modal=None):
        self.suspect = suspect_data
        self.agent = agent
        self.is_open = False
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.logs_modal = logs_modal

        # Conversation history
        self.messages = []
        self.user_input = ""
        self.is_typing = False

        # Loading animation
        self.is_loading = False
        self.loading_dots_frame = 0
        self.loading_timer = 0
        self.loading_message = None
        self.pending_response = None

        # Cache for opening statement
        self.opening_statement = None

        # Cache for responses (question -> response mapping)
        self.response_cache = {}

        # Track if conversation has been started
        self.conversation_started = False

        # Track conversation sessions for multiple observations
        self.session_snippets = []  # List of snippets from different conversation sessions

        # Track personality changes for animation
        self.last_personality_state = agent.get_personality_state().copy()
        self.personality_changes = {}  # Maps trait -> (change_value, frame_count)
        self.change_animation_frames = 180  # 180 frames = 3 seconds at 60 FPS

        # Scroll tracking for conversation
        self.scroll_offset = 0  # How many messages to skip from the top

        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 18)
        self.input_font = pygame.font.Font(None, 20)

        # Load portrait
        portrait_path = CHARACTER_PORTRAITS.get(suspect_data["name"])
        if portrait_path and os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path)
            self.portrait = pygame.transform.scale(self.portrait, (150, 150))
        else:
            self.portrait = None

        # Load progress bar image
        progress_bar_path = "assets/progress/PNG/GUI-Kit-Pack-Free_04.png"
        if os.path.exists(progress_bar_path):
            self.progress_bar = pygame.image.load(progress_bar_path)
            self.progress_bar = pygame.transform.scale(self.progress_bar, (15, 20))
        else:
            self.progress_bar = None

        # Load level 0 icon (slim version)
        level_zero_icon_path = "assets/progress/PNG/GUI-Kit-Pack-Free_01.png"
        if os.path.exists(level_zero_icon_path):
            self.level_zero_icon = pygame.image.load(level_zero_icon_path)
            self.level_zero_icon = pygame.transform.scale(self.level_zero_icon, (6, 20))
        else:
            self.level_zero_icon = None


    def handle_input(self, event):
        """Handle keyboard input and scroll for conversation"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Send message
                if self.user_input.strip() and not self.is_loading:
                    self.messages.append(("You", self.user_input))
                    self.loading_message = self.user_input
                    self.user_input = ""
                    self.is_loading = True
                    self.loading_timer = 0
                    self.loading_dots_frame = 0
                    # Reset scroll to bottom when new message sent
                    self.scroll_offset = 0

                    # Start API call in background thread
                    thread = threading.Thread(target=self._fetch_response_async)
                    thread.daemon = True
                    thread.start()
            elif event.key == pygame.K_BACKSPACE:
                self.user_input = self.user_input[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.is_open = False
        elif event.type == pygame.TEXTINPUT:
            if len(self.user_input) < 100 and not self.is_loading:  # Limit input length
                self.user_input += event.text
        elif event.type == pygame.MOUSEWHEEL:
            # Handle scroll wheel - scroll up to see older messages
            self.scroll_offset += event.y  # Positive y = scroll up (show older), negative = scroll down (show newer)
            max_scroll = len(self.messages) - 1
            self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def _fetch_response_async(self):
        """Fetch response from agent in background thread"""
        try:
            # Check if response is cached
            if self.loading_message in self.response_cache:
                self.pending_response = self.response_cache[self.loading_message]
            else:
                # Get response from agent and cache it
                response, personality_changes = self.agent.respond(self.loading_message)
                self.pending_response = response
                self.response_cache[self.loading_message] = response
        except Exception as e:
            self.pending_response = f"Error getting response: {str(e)}"
        finally:
            self.is_loading = False

    def get_window_rect(self):
        """Get the rectangle of the conversation window"""
        window_width = int(self.screen_width * 0.85)
        window_height = int(self.screen_height * 0.90)
        window_x = (self.screen_width - window_width) // 2
        window_y = (self.screen_height - window_height) // 2
        return pygame.Rect(window_x, window_y, window_width, window_height)

    def draw(self, surface):
        """Draw the conversation screen"""
        if not self.is_open:
            return

        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(50)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Draw main conversation window
        window_width = int(self.screen_width * 0.85)
        window_height = int(self.screen_height * 0.90)
        window_x = (self.screen_width - window_width) // 2
        window_y = (self.screen_height - window_height) // 2

        # Draw window background
        pygame.draw.rect(surface, DARK_GRAY, (window_x, window_y, window_width, window_height))
        pygame.draw.rect(surface, ACCENT_COLOR, (window_x, window_y, window_width, window_height), 3)

        # Draw suspect info section (left side)
        info_width = 250
        info_x = window_x + 20
        info_y = window_y + 20

        # Draw portrait
        if self.portrait:
            portrait_x = info_x + (info_width - 150) // 2
            portrait_y = info_y
            surface.blit(self.portrait, (portrait_x, portrait_y))

        # Draw suspect name and info
        name_text = self.title_font.render(self.suspect["name"], True, WHITE)
        name_x = info_x + (info_width - name_text.get_width()) // 2
        name_y = info_y + 170
        surface.blit(name_text, (name_x, name_y))

        # Draw personality traits
        personality_y = name_y + 40
        traits_title = self.text_font.render("Personality Traits:", True, LIGHT_GRAY)
        surface.blit(traits_title, (info_x, personality_y))

        personality_y += 25
        for trait, level in self.agent.get_personality_state().items():
            # Draw trait name
            trait_text = self.text_font.render(f"{trait}:", True, LIGHT_GRAY)
            surface.blit(trait_text, (info_x, personality_y))

            # Draw visual progress bars (level number of bars) or icon for level 0
            bar_x = info_x + 140

            # Check if this trait is animating
            is_animating = trait in self.personality_changes
            if is_animating:
                change_value, frames_left = self.personality_changes[trait]
                # Blinking effect - blink every 15 frames (shows/hides for 0.25 seconds)
                should_show = (frames_left % 30) < 15
                self.personality_changes[trait] = (change_value, frames_left - 1)
                if frames_left <= 0:
                    del self.personality_changes[trait]
            else:
                should_show = True

            if should_show:
                if level == 0:
                    # Draw level 0 icon (slim)
                    if self.level_zero_icon:
                        surface.blit(self.level_zero_icon, (bar_x, personality_y))
                else:
                    # Draw visual progress bars (level number of bars)
                    for i in range(level):
                        if self.progress_bar:
                            surface.blit(self.progress_bar, (bar_x + i * 18, personality_y))

            # Draw +1 or -1 indicator if animating
            if is_animating and trait in self.personality_changes:
                change_value, _ = self.personality_changes[trait]
                change_text = f"{change_value:+d}"

                # Color logic: Trust +1 is good (green), others +1 is bad (red)
                if trait == "Trust":
                    change_color = (100, 255, 100) if change_value > 0 else (255, 100, 100)
                else:  # Anxious and Moody: +1 is bad (red), -1 is good (green)
                    change_color = (255, 100, 100) if change_value > 0 else (100, 255, 100)

                indicator_surface = self.text_font.render(change_text, True, change_color)
                indicator_x = bar_x + (level * 18) + 5
                surface.blit(indicator_surface, (indicator_x, personality_y - 5))

            personality_y += 25

        # Draw conversation section (right side)
        conv_x = window_x + info_width + 40
        conv_y = window_y + 20
        conv_width = window_width - info_width - 60
        conv_height = window_height - 120

        # Draw conversation box background
        pygame.draw.rect(surface, (40, 40, 40), (conv_x, conv_y, conv_width, conv_height))
        pygame.draw.rect(surface, LIGHT_GRAY, (conv_x, conv_y, conv_width, conv_height), 2)

        # Draw messages as bubbles with scroll support
        message_y = conv_y + 10
        max_visible_messages = 10
        # Calculate which messages to show based on scroll offset
        start_index = max(0, len(self.messages) - max_visible_messages - self.scroll_offset)
        messages_to_show = self.messages[start_index:start_index + max_visible_messages]

        # Add pending response if available
        if self.pending_response:
            self.messages.append((self.suspect["name"], self.pending_response))
            self.pending_response = None
            messages_to_show = self.messages[-max_visible_messages:]

            # Detect personality changes and track them for animation
            current_state = self.agent.get_personality_state()
            for trait, new_level in current_state.items():
                old_level = self.last_personality_state.get(trait, new_level)
                change = new_level - old_level
                if change != 0:
                    self.personality_changes[trait] = (change, self.change_animation_frames)
                self.last_personality_state[trait] = new_level

            # Generate snippet for logs in background thread
            if self.logs_modal:
                thread = threading.Thread(
                    target=self.logs_modal.generate_snippet_for_suspect,
                    args=(self.suspect["name"], self)
                )
                thread.daemon = True
                thread.start()

        for speaker, message in messages_to_show:
            is_player = speaker == "You"

            # Determine bubble position and color first
            if is_player:
                # Player message - right side, blue
                bubble_color = (100, 150, 255)
                text_color = BLACK
                left_margin = 100  # Player messages on right, so large left margin
                right_margin = 5  # Minimal right padding for player messages
            else:
                # Suspect message - left side, gray with padding on right
                bubble_color = (80, 80, 80)
                text_color = WHITE
                left_margin = 20
                right_margin = 100  # Received messages have padding on right

            # Wrap text based on actual rendered width with dynamic bubble width
            bubble_padding = 10
            line_height = 20
            max_bubble_width = conv_width - left_margin - right_margin
            min_bubble_width = 100  # Minimum width for bubble

            # First pass: try to fit text with max width
            words = message.split()
            lines = []
            current_line = ""
            max_line_width = 0

            for word in words:
                test_line = current_line + word + " " if current_line else word + " "
                test_surface = self.text_font.render(test_line.rstrip(), True, text_color)
                if test_surface.get_width() > max_bubble_width - (bubble_padding * 2) and current_line:
                    line_surface = self.text_font.render(current_line.rstrip(), True, text_color)
                    max_line_width = max(max_line_width, line_surface.get_width())
                    lines.append(current_line.rstrip())
                    current_line = word + " "
                else:
                    current_line = test_line

            if current_line:
                line_surface = self.text_font.render(current_line.rstrip(), True, text_color)
                max_line_width = max(max_line_width, line_surface.get_width())
                lines.append(current_line.rstrip())

            # Calculate dynamic bubble width based on content
            dynamic_width = max_line_width + (bubble_padding * 2)
            bubble_width = max(min_bubble_width, min(dynamic_width, max_bubble_width))

            # Calculate bubble size
            bubble_height = len(lines) * line_height + bubble_padding * 2

            # Determine bubble x position
            if is_player:
                # Player messages on right side - close to the right edge
                bubble_x = conv_x + conv_width - bubble_width - 20
            else:
                # Suspect messages on left side
                bubble_x = conv_x + left_margin

            # Draw bubble background
            pygame.draw.rect(surface, bubble_color, (bubble_x, message_y, bubble_width, bubble_height), border_radius=10)
            pygame.draw.rect(surface, LIGHT_GRAY, (bubble_x, message_y, bubble_width, bubble_height), 2, border_radius=10)

            # Draw message text inside bubble
            text_y = message_y + bubble_padding
            for line in lines:
                line_text = self.text_font.render(line, True, text_color)
                if is_player:
                    # Right-align player messages
                    text_x = bubble_x + bubble_width - bubble_padding - line_text.get_width()
                else:
                    # Left-align suspect messages
                    text_x = bubble_x + bubble_padding
                surface.blit(line_text, (text_x, text_y))
                text_y += line_height

            message_y += bubble_height + 10

        # Draw loading bubble if currently loading
        if self.is_loading:
            self.loading_timer += 1
            if self.loading_timer >= 8:  # Change dots every 8 frames
                self.loading_timer = 0
                self.loading_dots_frame = (self.loading_dots_frame + 1) % 3

            # Create loading bubble
            dots = [".", "..", "..."]
            loading_text = dots[self.loading_dots_frame]

            # Calculate bubble size for loading message
            bubble_padding = 10
            line_height = 20
            loading_surface = self.text_font.render(loading_text, True, WHITE)
            bubble_height = line_height + bubble_padding * 2
            bubble_width = loading_surface.get_width() + bubble_padding * 2

            # Position loading bubble on left (suspect side)
            left_margin = 20
            bubble_x = conv_x + left_margin
            bubble_color = (80, 80, 80)

            # Draw loading bubble background
            pygame.draw.rect(surface, bubble_color, (bubble_x, message_y, bubble_width, bubble_height), border_radius=10)
            pygame.draw.rect(surface, LIGHT_GRAY, (bubble_x, message_y, bubble_width, bubble_height), 2, border_radius=10)

            # Draw loading dots inside bubble
            text_y = message_y + bubble_padding
            surface.blit(loading_surface, (bubble_x + bubble_padding, text_y))

        # Draw input box
        input_y = window_y + window_height - 60
        pygame.draw.rect(surface, (60, 60, 60), (conv_x, input_y, conv_width, 40))
        pygame.draw.rect(surface, LIGHT_GRAY, (conv_x, input_y, conv_width, 40), 2)

        # Draw input text (disabled while loading)
        if not self.is_loading:
            input_text = self.input_font.render(self.user_input, True, WHITE)
            surface.blit(input_text, (conv_x + 10, input_y + 8))
        else:
            # Show placeholder while loading
            placeholder_text = self.input_font.render("(waiting for response...)", True, (100, 100, 100))
            surface.blit(placeholder_text, (conv_x + 10, input_y + 8))

        # Draw close instruction
        close_text = self.text_font.render("Press ESC to close", True, LIGHT_GRAY)
        close_x = window_x + (window_width - close_text.get_width()) // 2
        close_y = window_y + window_height - 25
        surface.blit(close_text, (close_x, close_y))

    def toggle(self):
        """Toggle conversation screen"""
        self.is_open = not self.is_open
        if self.is_open:
            self.user_input = ""
            # Only initialize conversation on first opening
            if not self.conversation_started:
                self.messages = []
                self.conversation_started = True
                # Send first message asynchronously if not cached
                if self.opening_statement is None:
                    self.is_loading = True
                    self.loading_timer = 0
                    self.loading_dots_frame = 0
                    thread = threading.Thread(target=self._fetch_opening_statement_async)
                    thread.daemon = True
                    thread.start()
                else:
                    # Use cached opening statement
                    self.messages.append((self.suspect["name"], self.opening_statement))
            # If reopening, conversation history persists (no clearing)

    def _fetch_opening_statement_async(self):
        """Fetch opening statement from agent in background thread"""
        try:
            self.opening_statement = self.agent.get_opening_statement()
            self.pending_response = self.opening_statement
        except Exception as e:
            self.pending_response = f"Error: {str(e)}"
        finally:
            self.is_loading = False

    def _send_first_message(self):
        """Send the first greeting message from the suspect"""
        # Use cached opening statement, or generate and cache if not available
        if self.opening_statement is None:
            self.opening_statement = self.agent.get_opening_statement()
        self.messages.append((self.suspect["name"], self.opening_statement))


class InfoModal:
    def __init__(self, title, content, master_data, conversation_screens=None):
        self.title = title
        self.content = content
        self.master_data = master_data
        self.conversation_screens = conversation_screens or {}
        self.is_open = False

        # Cache for generated snippets (maps suspect_name -> list of snippets)
        self.snippet_cache = {}

        # Scroll tracking for logs
        self.scroll_offset = 0

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
        """Generate investigation logs content with cached AI-generated snippets (unique only)"""
        logs = []

        # Check if there are any messages across all conversation screens
        has_messages = False
        for suspect_name, conv_screen in self.conversation_screens.items():
            if conv_screen.messages:
                has_messages = True
                logs.append(f"\n--- Interview with {suspect_name} ---")

                # Use cached snippets (can be multiple from different sessions), removing duplicates
                if suspect_name in self.snippet_cache:
                    # Use set to track unique snippets, but preserve order
                    seen_snippets = set()
                    for snippet in self.snippet_cache[suspect_name]:
                        # Only add if we haven't seen this exact snippet before
                        if snippet not in seen_snippets:
                            logs.append(f"  • {snippet}")
                            seen_snippets.add(snippet)
                else:
                    logs.append(f"  • (generating...)")

        if not has_messages:
            logs.append("No interviews conducted yet.")

        return logs

    def generate_snippet_for_suspect(self, suspect_name, conv_screen):
        """Generate a single sentence snippet asynchronously"""
        from openai import OpenAI
        import os

        conversation_text = "\n".join([f"{speaker}: {msg}" for speaker, msg in conv_screen.messages])

        snippet_prompt = f"""Analyze this interview with {suspect_name} and write ONE short suspicious or notable observation (5-7 words max).
Example: "David seemed nervous about Emma"

Transcript:
{conversation_text}

Observation:"""

        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": snippet_prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )
            snippet = response.choices[0].message.content.strip()

            # Initialize list for this suspect if not already done
            if suspect_name not in self.snippet_cache:
                self.snippet_cache[suspect_name] = []

            # Append snippet to list
            self.snippet_cache[suspect_name].append(snippet)
        except Exception as e:
            if suspect_name not in self.snippet_cache:
                self.snippet_cache[suspect_name] = []
            self.snippet_cache[suspect_name].append("(Unable to generate snippet)")

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

        # Calculate height based on content with max of 75% window height
        line_height = 25
        content_height = len(lines) * line_height + 150  # Padding for title and spacing
        max_height = int(SCREEN_HEIGHT * 0.75)  # Max 75% of window height
        self.height = min(content_height, max_height)

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

        # Draw content with scroll support
        content_x = self.x + 120
        content_y = self.y + 100
        max_visible_lines = int((self.height - 150) / line_height)  # Lines that fit in modal

        # Calculate which lines to show based on scroll offset
        start_line = min(self.scroll_offset, max(0, len(lines) - max_visible_lines))
        for i, line in enumerate(lines[start_line:start_line + max_visible_lines]):
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


    def get_rect(self):
        """Get the rectangle for this button"""
        return pygame.Rect(self.x, self.y, self.width, self.height)


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

    def is_clicked(self, mouse_pos):
        """Check if card is clicked"""
        mouse_x, mouse_y = mouse_pos
        return (
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
    # Initialize scroll offsets
    facts_modal.scroll_offset = 0
    logs_modal.scroll_offset = 0

    # Create character cards and conversation screens (excluding victim)
    from suspect_agent import SuspectAgent

    card_positions = get_card_positions()
    cards = []
    conversation_screens = {}
    card_index = 0

    for suspect_name in sorted(master.suspects.keys()):
        suspect = master.suspects[suspect_name]
        if not suspect["is_victim"] and card_index < len(card_positions):
            x, y = card_positions[card_index]
            card = CharacterCard(suspect, x, y)
            cards.append(card)

            # Create conversation screen and agent for this suspect
            if not suspect["is_victim"]:
                # Get relationships for this suspect
                relationships = {}
                for pair, rel_type in master.relationships.items():
                    names = pair.split("_")
                    if suspect_name in names:
                        other_name = names[0] if names[1] == suspect_name else names[1]
                        relationships[other_name] = rel_type

                # Create agent
                agent = SuspectAgent(suspect, relationships, master.case_state, master.clues)

                # Create conversation screen (logs_modal will be added after)
                conv_screen = ConversationScreen(suspect, agent, SCREEN_WIDTH, SCREEN_HEIGHT, logs_modal)
                conversation_screens[suspect_name] = conv_screen

            card_index += 1

    # Update logs modal with conversation screens
    logs_modal.conversation_screens = conversation_screens

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
    active_conversation = None  # Track which suspect's conversation is open

    while running:
        clock.tick(FPS)

        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Pass input to active conversation screen if one is open
                if active_conversation:
                    conversation_screens[active_conversation].handle_input(event)
                    # Check if conversation was closed
                    if not conversation_screens[active_conversation].is_open:
                        active_conversation = None
                else:
                    # Handle general keyboard input
                    if event.key == pygame.K_ESCAPE:
                        # Close modals if open, otherwise exit
                        if facts_modal.is_open:
                            facts_modal.toggle()
                        elif logs_modal.is_open:
                            logs_modal.toggle()
                        else:
                            running = False
            elif event.type == pygame.TEXTINPUT:
                # Pass text input to active conversation screen
                if active_conversation:
                    conversation_screens[active_conversation].handle_input(event)
            elif event.type == pygame.MOUSEWHEEL:
                # Handle scroll wheel for conversation or modals
                if active_conversation:
                    conversation_screens[active_conversation].handle_input(event)
                elif logs_modal.is_open:
                    # Scroll logs
                    logs_modal.scroll_offset += event.y
                    logs_modal.scroll_offset = max(0, logs_modal.scroll_offset)
                elif facts_modal.is_open:
                    # Scroll facts
                    facts_modal.scroll_offset += event.y
                    facts_modal.scroll_offset = max(0, facts_modal.scroll_offset)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle button clicks - prioritize conversation screen
                if active_conversation:
                    # Check if click is outside the conversation window
                    window_rect = conversation_screens[active_conversation].get_window_rect()
                    if not window_rect.collidepoint(mouse_pos):
                        # Close conversation screen
                        conversation_screens[active_conversation].toggle()
                        active_conversation = None
                elif facts_modal.is_open:
                    # Check if close button is clicked
                    if facts_modal.is_close_clicked(mouse_pos):
                        facts_modal.toggle()
                elif logs_modal.is_open:
                    # Check if close button is clicked
                    if logs_modal.is_close_clicked(mouse_pos):
                        logs_modal.toggle()
                else:
                    # Check menu button clicks
                    button_clicked = False
                    for button in menu_buttons:
                        if button.is_clicked(mouse_pos):
                            if button.label == "FACTS":
                                facts_modal.toggle()
                            elif button.label == "LOGS":
                                logs_modal.toggle()
                            elif button.label == "ACCUSE":
                                pass  # TODO: Implement accuse functionality
                            button_clicked = True
                            break

                    # Check character card clicks if no button was clicked
                    if not button_clicked:
                        for i, card in enumerate(cards):
                            if card.is_clicked(mouse_pos):
                                # Open conversation screen for this suspect
                                suspect_name = card.suspect["name"]
                                if suspect_name in conversation_screens:
                                    active_conversation = suspect_name
                                    conversation_screens[suspect_name].toggle()
                                break

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

        # Draw active conversation screen
        if active_conversation:
            conversation_screens[active_conversation].draw(screen)

        # Update display
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
