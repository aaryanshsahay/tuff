"""
Main game logic and event handling
"""
import pygame
import sys
import json
import os
from src.config import *
from src.gui import CharacterCard, MenuButton, InfoModal, AccusationResultsModal, ConversationScreen
from src.agents import MurderMysteryMaster, SuspectAgent, AgentOrchestrator
from src.utils import init_cursors, set_default_cursor, set_map_frame_cursor, ParallaxBackground


def get_card_positions():
    """Calculate card positions (3x2 grid)"""
    positions = []
    left_padding = 150
    start_x = (
        SCREEN_WIDTH - (CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_PADDING)
    ) // 2
    start_x += left_padding
    start_y = 150

    for row in range(2):
        for col in range(CARDS_PER_ROW):
            x = start_x + col * (CARD_WIDTH + CARD_PADDING)
            y = start_y + row * (CARD_HEIGHT + CARD_PADDING)
            positions.append((x, y))

    return positions


class MurderMysteryGame:
    def __init__(self, test_mode=False):
        # Initialize pygame
        pygame.init()

        # Create screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Murder Mystery - The Mansion")

        # Clock for FPS
        self.clock = pygame.time.Clock()

        # Initialize cursors
        init_cursors()

        # Game state
        self.test_mode = test_mode
        self.master = None
        self.orchestrator = None
        self.cards = []
        self.conversation_screens = {}
        self.menu_buttons = []
        self.facts_modal = None
        self.logs_modal = None
        self.accusation_modal = None
        self.background = ParallaxBackground()
        self.active_conversation = None
        self.in_accusation_mode = False

    def setup_game(self):
        """Initialize the game with a new case"""
        print("🔍 Setting up murder mystery case...\n")

        # Generate case or load test case
        self.master = MurderMysteryMaster()

        if self.test_mode:
            # Load test case from cache
            if not self._load_test_case():
                print("❌ Failed to load test case")
                return False
        else:
            # Generate new case
            if not self.master.generate_case_state():
                print("❌ Failed to generate case")
                return False

        # Build world state
        self.master.build_world_state()

        # Create orchestrator for narrative coherence
        self.orchestrator = AgentOrchestrator(
            self.master.case_state,
            self.master.suspects,
            self.master.relationships,
            self.master.clues
        )

        # Create modals
        self.facts_modal = InfoModal("FACTS", "", self.master)
        self.logs_modal = InfoModal("LOGS", "", self.master)
        self.facts_modal.scroll_offset = 0
        self.logs_modal.scroll_offset = 0

        # Create menu buttons (left side)
        button_width = 240
        button_height = 200
        button_x = 20
        button_y_start = 200
        button_spacing = 200

        self.menu_buttons = [
            MenuButton(
                "FACTS", button_x, button_y_start, button_width, button_height
            ),
            MenuButton(
                "LOGS", button_x, button_y_start + button_spacing, button_width, button_height
            ),
            MenuButton(
                "ACCUSE", button_x, button_y_start + button_spacing * 2, button_width, button_height
            ),
        ]

        # Create character cards and conversation screens
        card_positions = get_card_positions()
        card_index = 0

        for suspect_name in sorted(self.master.suspects.keys()):
            suspect = self.master.suspects[suspect_name]
            if not suspect["is_victim"] and card_index < len(card_positions):
                x, y = card_positions[card_index]
                card = CharacterCard(suspect, x, y)
                self.cards.append(card)

                # Create conversation screen and agent for this suspect
                if not suspect["is_victim"]:
                    # Get relationships for this suspect
                    relationships = {}
                    for pair, rel_type in self.master.relationships.items():
                        names = pair.split("_")
                        if suspect_name in names:
                            other_name = names[0] if names[1] == suspect_name else names[1]
                            relationships[other_name] = rel_type

                    # Create agent with orchestrator for narrative coherence
                    agent = SuspectAgent(
                        suspect, relationships, self.master.case_state, self.master.clues, self.orchestrator
                    )

                    # Create conversation screen
                    conv_screen = ConversationScreen(suspect, agent, SCREEN_WIDTH, SCREEN_HEIGHT, self.logs_modal)
                    self.conversation_screens[suspect_name] = conv_screen

                card_index += 1

        # Update logs modal with conversation screens
        self.logs_modal.conversation_screens = self.conversation_screens

        # Print case info to terminal
        print("=" * 80)
        print("MURDER MYSTERY - CASE BRIEFING")
        print("=" * 80)
        print(f"🔴 VICTIM: {self.master.victim}")
        print(f"🔪 MURDERER: {self.master.murderer}")
        print(f"📍 CRIME LOCATION: {self.master.crime_location}")
        print(f"☠️  CAUSE OF DEATH: {self.master.cause_of_death}")
        print(f"⏰ TIME OF DEATH: {self.master.time_of_death}\n")

        print("✅ Game setup complete!\n")
        return True

    def _load_test_case(self):
        """Load test case from JSON cache file"""
        test_case_path = os.path.join(os.path.dirname(__file__), "test_case.json")

        try:
            with open(test_case_path, 'r') as f:
                test_data = json.load(f)

            # Set the case state directly
            self.master.case_state = test_data

            # Build world state from the loaded test case
            self.master.build_world_state()
            return True
        except Exception as e:
            print(f"❌ Error loading test case: {e}")
            return False

    def handle_events(self):
        """Handle all game events"""
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                # Pass input to active conversation screen if one is open
                if self.active_conversation:
                    self.conversation_screens[self.active_conversation].handle_input(event)
                    # Check if conversation was closed
                    if not self.conversation_screens[self.active_conversation].is_open:
                        self.active_conversation = None
                else:
                    # Handle general keyboard input
                    if event.key == pygame.K_ESCAPE:
                        # Cancel accusation mode if active
                        if self.in_accusation_mode:
                            self.in_accusation_mode = False
                            set_default_cursor()
                        # Close accusation modal if open
                        elif self.accusation_modal and self.accusation_modal.is_open:
                            self.accusation_modal.toggle()
                        # Close other modals if open, otherwise exit
                        elif self.facts_modal.is_open:
                            self.facts_modal.toggle()
                        elif self.logs_modal.is_open:
                            self.logs_modal.toggle()
                        else:
                            return False

            elif event.type == pygame.TEXTINPUT:
                # Pass text input to active conversation screen
                if self.active_conversation:
                    self.conversation_screens[self.active_conversation].handle_input(event)

            elif event.type == pygame.MOUSEWHEEL:
                # Handle scroll wheel for conversation or modals
                if self.active_conversation:
                    self.conversation_screens[self.active_conversation].handle_input(event)
                elif self.accusation_modal and self.accusation_modal.is_open:
                    # Scroll accusation results
                    self.accusation_modal.scroll_offset += event.y
                    self.accusation_modal.scroll_offset = max(0, self.accusation_modal.scroll_offset)
                elif self.logs_modal.is_open:
                    # Scroll logs
                    self.logs_modal.scroll_offset += event.y
                    self.logs_modal.scroll_offset = max(0, self.logs_modal.scroll_offset)
                elif self.facts_modal.is_open:
                    # Scroll facts
                    self.facts_modal.scroll_offset += event.y
                    self.facts_modal.scroll_offset = max(0, self.facts_modal.scroll_offset)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check for menu button clicks first (always takes priority)
                button_clicked = False
                for button in self.menu_buttons:
                    if button.is_clicked(mouse_pos):
                        if button.label == "FACTS":
                            self.facts_modal.toggle()
                        elif button.label == "LOGS":
                            self.logs_modal.toggle()
                        elif button.label == "ACCUSE":
                            set_map_frame_cursor()
                            self.in_accusation_mode = True
                        button_clicked = True
                        break

                # If no button was clicked, handle other interactions
                if not button_clicked:
                    # Handle close buttons on modals
                    if self.facts_modal.is_open and self.facts_modal.is_close_clicked(mouse_pos):
                        self.facts_modal.toggle()
                    elif self.logs_modal.is_open and self.logs_modal.is_close_clicked(mouse_pos):
                        self.logs_modal.toggle()
                    elif self.accusation_modal and self.accusation_modal.is_open and self.accusation_modal.is_close_clicked(mouse_pos):
                        self.accusation_modal.toggle()
                    # Handle conversation screen
                    elif self.active_conversation:
                        window_rect = self.conversation_screens[self.active_conversation].get_window_rect()
                        if not window_rect.collidepoint(mouse_pos):
                            self.conversation_screens[self.active_conversation].toggle()
                            self.active_conversation = None
                    # Handle character card clicks
                    else:
                        for i, card in enumerate(self.cards):
                            if card.is_clicked(mouse_pos):
                                if self.in_accusation_mode:
                                    # Handle accusation
                                    accused_name = card.suspect["name"]
                                    is_correct = accused_name == self.master.case_state["murderer"]

                                    # Reset cursor
                                    set_default_cursor()
                                    self.in_accusation_mode = False

                                    # Create and show accusation results modal
                                    self.accusation_modal = AccusationResultsModal(
                                        accused_name,
                                        is_correct,
                                        self.master,
                                        self.orchestrator,
                                        self.conversation_screens
                                    )
                                    self.accusation_modal.toggle()
                                else:
                                    # Open conversation screen for this suspect
                                    suspect_name = card.suspect["name"]
                                    if suspect_name in self.conversation_screens:
                                        self.active_conversation = suspect_name
                                        self.conversation_screens[suspect_name].toggle()
                                break

        # Update hover states
        for card in self.cards:
            card.check_hover(mouse_pos)
        for button in self.menu_buttons:
            button.check_hover(mouse_pos)

        return True

    def update(self):
        """Update game state"""
        self.background.update()

    def draw(self):
        """Draw all game elements"""
        # Draw background
        self.background.draw(self.screen)

        # Draw title
        title_font = pygame.font.Font(None, 48)
        title_text = title_font.render("THE MANSION - SELECT A SUSPECT TO INTERVIEW", True, WHITE)
        title_x = (SCREEN_WIDTH - title_text.get_width()) // 2
        self.screen.blit(title_text, (title_x, 30))

        # Draw menu buttons
        for button in self.menu_buttons:
            button.draw(self.screen)

        # Draw character cards
        for card in self.cards:
            card.draw(self.screen)

        # Draw modals on top
        self.facts_modal.draw(self.screen)
        self.logs_modal.draw(self.screen)
        if self.accusation_modal:
            self.accusation_modal.draw(self.screen)

        # Draw active conversation screen
        if self.active_conversation:
            self.conversation_screens[self.active_conversation].draw(self.screen)

        # Update display
        pygame.display.flip()

    def run(self):
        """Main game loop"""
        print("🔍 " * 20)
        print("WELCOME TO MURDER MYSTERY DETECTIVE GAME")
        print("🔍 " * 20 + "\n")

        # Setup game
        if not self.setup_game():
            return

        # Main game loop
        running = True
        while running:
            self.clock.tick(FPS)
            running = self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()