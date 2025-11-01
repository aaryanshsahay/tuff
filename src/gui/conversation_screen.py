"""
Conversation screen for interviewing suspects
"""
import pygame
import threading
import os
from src.config import *


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

    def toggle(self):
        """Toggle the conversation screen open/closed"""
        self.is_open = not self.is_open
        if self.is_open and not self.conversation_started:
            self.conversation_started = True
            # Fetch opening statement asynchronously
            thread = threading.Thread(target=self._fetch_opening_statement)
            thread.daemon = True
            thread.start()

    def _fetch_opening_statement(self):
        """Fetch opening statement from the agent"""
        try:
            statement = self.agent.get_opening_statement()
            self.opening_statement = statement
            if statement:
                self.messages.append((self.suspect["name"], statement))
                # Generate snippet for logs
                if self.logs_modal:
                    thread = threading.Thread(
                        target=self.logs_modal.generate_snippet_for_suspect,
                        args=(self.suspect["name"], self),
                    )
                    thread.daemon = True
                    thread.start()
        except Exception as e:
            print(f"Error getting opening statement: {e}")

    def handle_input(self, event):
        """Handle keyboard input and scroll for conversation"""
        if not self.is_open:
            return

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

            # Calculate dynamic bubble width based on content (tight fit)
            dynamic_width = max_line_width + (bubble_padding * 2)
            # Don't enforce min_bubble_width for dynamic sizing - let it fit content
            bubble_width = min(dynamic_width, max_bubble_width)

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
                    # Right-align player messages with padding on right
                    text_x = bubble_x + bubble_width - bubble_padding - line_text.get_width()
                else:
                    # Left-align suspect messages with dynamic padding
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