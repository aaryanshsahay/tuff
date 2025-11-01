"""
Menu button component
"""
import pygame
from src.config import WHITE


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
        """Check if button was clicked"""
        mouse_x, mouse_y = mouse_pos
        return (
            self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height
        )