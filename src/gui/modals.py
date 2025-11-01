"""
Modal dialogs for the game
"""

import pygame
import threading
from openai import OpenAI
import os
from src.config import *


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
        facts.append(f"VICTIM: {self.master_data.victim}")
        facts.append(f"CRIME LOCATION: {self.master_data.crime_location}")
        facts.append(f"CAUSE OF DEATH: {self.master_data.cause_of_death}")
        facts.append(f"TIME OF DEATH: {self.master_data.time_of_death}")
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

        conversation_text = "\n".join(
            [f"{speaker}: {msg}" for speaker, msg in conv_screen.messages]
        )

        snippet_prompt = f"""Analyze this interview with {suspect_name} and write ONE short suspicious or notable observation (5-7 words max).
Example: "David seemed nervous about Emma"

Transcript:
{conversation_text}

Observation:"""

        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": snippet_prompt}],
                temperature=0.7,
                max_tokens=50,
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
        for i, line in enumerate(lines[start_line : start_line + max_visible_lines]):
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


class AccusationResultsModal:
    def __init__(self, accused_name, is_correct, master_data, orchestrator, conversation_screens):
        self.accused_name = accused_name
        self.is_correct = is_correct
        self.master_data = master_data
        self.orchestrator = orchestrator
        self.conversation_screens = conversation_screens
        self.is_open = False
        self.scroll_offset = 0

        # Modal dimensions
        self.width = int(SCREEN_WIDTH * 0.75)
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = 100

        # Load background image
        modal_bg = pygame.image.load("assets/dialogue_box/20240707dragon9SlicesA.png")
        self.modal_bg = pygame.transform.scale(modal_bg, (self.width, 900))

        # Load result images
        if is_correct:
            self.result_image = pygame.image.load("assets/progress/PNG/GUI-Kit-Pack-Free_37.png")
        else:
            self.result_image = pygame.image.load("assets/progress/PNG/GUI-Kit-Pack-Free_36.png")

        # Scale result image
        self.result_image = pygame.transform.scale(self.result_image, (200, 200))

        # Create fonts
        self.title_font = pygame.font.Font(None, 36)
        self.subtitle_font = pygame.font.Font(None, 24)
        self.text_font = pygame.font.Font(None, 18)

        # Cache for generated content (to avoid recalculating every frame)
        self.cached_content = None
        self.is_loading_content = False

    def generate_results_content(self):
        """Generate detailed results content"""
        lines = []
        accused = self.master_data.suspects[self.accused_name]

        if self.is_correct:
            # Correct accusation
            murderer = self.master_data.suspects[self.accused_name]
            murderer_briefing = self.orchestrator.get_suspect_briefing(self.accused_name)

            lines.append("═" * 70)
            lines.append(f"✓ CORRECT - {self.accused_name.upper()} IS THE MURDERER")
            lines.append("═" * 70)
            lines.append("")
            lines.append(f"Age: {murderer['age']} | Occupation: {murderer['occupation']}")
            lines.append(f"Gender: {murderer['gender']}")
            lines.append("")
            lines.append("MOTIVE:")
            lines.append(f"  {self.master_data.case_state['murderer_motive']}")
            lines.append("")
            lines.append("METHOD:")
            lines.append(f"  {self.master_data.cause_of_death}")
            lines.append(f"  Location: {self.master_data.crime_location}")
            lines.append(f"  Time: {self.master_data.time_of_death}")
            lines.append("")
            lines.append("KEY EVIDENCE:")

            # Extract secrets they should hide
            secrets = murderer_briefing.get("what_they_should_hide", [])
            if secrets:
                for secret in secrets[:3]:
                    lines.append(f"  • {secret}")
            else:
                lines.append(f"  • False alibi that couldn't hold under scrutiny")
                lines.append(f"  • Suspicious behavior and nervousness")
                lines.append(f"  • Motive connected to the victim")

            lines.append("")
            lines.append("CONFESSION:")
            lines.append(f"  When confronted with the evidence, {self.accused_name}")
            lines.append(f"  admitted to the crime. They have been arrested.")
            lines.append("")
            lines.append("CASE STATUS: SOLVED ✓")

        else:
            # Incorrect accusation
            real_murderer = self.master_data.suspects[self.master_data.case_state["murderer"]]
            accused_briefing = self.orchestrator.get_suspect_briefing(self.accused_name)

            lines.append("═" * 70)
            lines.append(f"✗ INCORRECT - {self.accused_name.upper()} IS INNOCENT")
            lines.append("═" * 70)
            lines.append("")
            lines.append(f"Age: {accused['age']} | Occupation: {accused['occupation']}")
            lines.append(f"Gender: {accused['gender']}")
            lines.append("")
            lines.append(f"THE REAL MURDERER: {self.master_data.case_state['murderer'].upper()}")
            lines.append("")
            lines.append("WHY YOU WERE MISLED:")
            lines.append(f"  {self.accused_name} seemed suspicious because:")

            # Extract what they should hide (innocent reasons)
            secrets = accused_briefing.get("what_they_should_hide", [])
            if secrets:
                for secret in secrets[:2]:
                    lines.append(f"    - {secret}")
            else:
                lines.append(f"    - Had conflicts with the victim")
                lines.append(f"    - Nervous about unrelated secrets")

            lines.append("")
            lines.append("WHAT YOU MISSED:")
            lines.append(f"  The true motive: {self.master_data.case_state['murderer_motive']}")
            lines.append(f"  This motive pointed to {self.master_data.case_state['murderer']}")
            lines.append(f"  Look for connections between the murderer and victim")
            lines.append("")
            lines.append("CASE STATUS: UNSOLVED - Investigation continues...")

        return lines

    def draw(self, surface):
        """Draw the accusation results modal"""
        if not self.is_open:
            return

        # Generate content asynchronously on first draw
        if self.cached_content is None and not self.is_loading_content:
            self.is_loading_content = True
            thread = threading.Thread(target=self._generate_content_async)
            thread.daemon = True
            thread.start()

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # Use cached content or show loading message
        if self.cached_content is not None:
            lines = self.cached_content
        else:
            lines = ["Loading accusation results..."]

        # Calculate height based on content
        line_height = 22
        content_height = len(lines) * line_height + 300  # Extra space for image and padding
        max_height = int(SCREEN_HEIGHT * 0.85)
        self.height = min(content_height, max_height)

        # Resize modal background
        self.modal_bg = pygame.transform.scale(
            pygame.image.load("assets/dialogue_box/20240707dragon9SlicesA.png"),
            (self.width, self.height),
        )

        # Draw modal background
        surface.blit(self.modal_bg, (self.x, self.y))

        # Draw result image at top center
        image_x = self.x + (self.width - self.result_image.get_width()) // 2
        image_y = self.y + 30
        surface.blit(self.result_image, (image_x, image_y))

        # Draw content with scroll support
        content_x = self.x + 80
        content_y = self.y + 260  # Below the image
        max_visible_lines = int((self.height - 310) / line_height)

        # Calculate which lines to show based on scroll offset
        start_line = min(self.scroll_offset, max(0, len(lines) - max_visible_lines))
        for i, line in enumerate(lines[start_line : start_line + max_visible_lines]):
            if line.strip():
                line_surface = self.text_font.render(line, True, LIGHT_GRAY)
                surface.blit(line_surface, (content_x, content_y))
            content_y += line_height

        # Draw close button
        close_button_rect = self.get_close_button_rect()
        pygame.draw.rect(surface, (100, 50, 50), close_button_rect, 2)

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

    def get_close_button_rect(self):
        """Get the rectangle for the close button"""
        close_button_size = 30
        close_x = self.x + self.width - close_button_size - 15
        close_y = self.y + 15
        return pygame.Rect(close_x, close_y, close_button_size, close_button_size)

    def is_close_clicked(self, mouse_pos):
        """Check if close button is clicked"""
        return self.get_close_button_rect().collidepoint(mouse_pos)

    def _generate_content_async(self):
        """Generate results content asynchronously"""
        try:
            self.cached_content = self.generate_results_content()
        except Exception as e:
            print(f"Error generating accusation results: {e}")
            self.cached_content = [f"Error generating results: {str(e)}"]
        finally:
            self.is_loading_content = False

    def toggle(self):
        """Toggle modal visibility"""
        self.is_open = not self.is_open
