"""
Character card display component
"""
import pygame
from src.config import *


class CharacterCard:
    def __init__(self, suspect_data, x, y):
        self.suspect = suspect_data
        self.x = x
        self.y = y
        self.width = CARD_WIDTH
        self.height = CARD_HEIGHT
        self.is_hovered = False

        # Load portrait
        portrait_path = CHARACTER_PORTRAITS.get(
            self.suspect["name"], "assets/potrait/PNG/Transperent/Icon1.png"
        )
        try:
            self.portrait = pygame.image.load(portrait_path)
            self.portrait = pygame.transform.scale(self.portrait, (150, 150))
        except:
            self.portrait = None

        # Create fonts
        self.name_font = pygame.font.Font(None, 28)
        self.info_font = pygame.font.Font(None, 20)

    def check_hover(self, mouse_pos):
        """Check if mouse is hovering over this card"""
        mouse_x, mouse_y = mouse_pos
        self.is_hovered = (
            self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height
        )

    def is_clicked(self, mouse_pos):
        """Check if this card was clicked"""
        mouse_x, mouse_y = mouse_pos
        return (
            self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height
        )

    def draw(self, surface):
        """Draw the character card"""
        # Create semi-transparent background
        card_surface = pygame.Surface((self.width, self.height))
        card_surface.set_alpha(240 if not self.is_hovered else 255)
        card_surface.fill((40, 40, 50))

        # Draw card border - changes color on hover
        border_color = (100, 150, 200) if self.is_hovered else (70, 70, 80)
        pygame.draw.rect(card_surface, border_color, (0, 0, self.width, self.height), 3)

        # Blit the card surface to the main surface
        surface.blit(card_surface, (self.x, self.y))

        # Draw portrait
        if self.portrait:
            portrait_x = self.x + (self.width - 150) // 2
            portrait_y = self.y + 20
            surface.blit(self.portrait, (portrait_x, portrait_y))
        else:
            # Draw placeholder if portrait not found
            placeholder_rect = pygame.Rect(
                self.x + (self.width - 150) // 2, self.y + 20, 150, 150
            )
            pygame.draw.rect(surface, DARK_GRAY, placeholder_rect)
            pygame.draw.rect(surface, LIGHT_GRAY, placeholder_rect, 2)

        # Draw name
        name_surface = self.name_font.render(self.suspect["name"], True, WHITE)
        name_x = self.x + (self.width - name_surface.get_width()) // 2
        name_y = self.y + 180
        surface.blit(name_surface, (name_x, name_y))

        # Draw age and occupation
        info_text = f"{self.suspect['age']} years old"
        info_surface = self.info_font.render(info_text, True, LIGHT_GRAY)
        info_x = self.x + (self.width - info_surface.get_width()) // 2
        info_y = self.y + 220
        surface.blit(info_surface, (info_x, info_y))

        occupation_surface = self.info_font.render(
            self.suspect["occupation"], True, LIGHT_GRAY
        )
        occupation_x = self.x + (self.width - occupation_surface.get_width()) // 2
        occupation_y = self.y + 245
        surface.blit(occupation_surface, (occupation_x, occupation_y))

        # Draw gender
        gender_surface = self.info_font.render(self.suspect["gender"], True, (150, 150, 160))
        gender_x = self.x + (self.width - gender_surface.get_width()) // 2
        gender_y = self.y + 270
        surface.blit(gender_surface, (gender_x, gender_y))