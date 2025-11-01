"""
Background and parallax utilities
"""
import pygame
from src.config import *


class ParallaxBackground:
    def __init__(self):
        # Load backgrounds
        self.background_layer_1 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_1.png")
        self.background_layer_2 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_2.png")
        self.background_layer_3 = pygame.image.load("assets/oak_woods_v1.0/background/background_layer_3.png")

        # Scale backgrounds
        self.background_layer_1 = pygame.transform.scale(self.background_layer_1, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background_layer_2 = pygame.transform.scale(self.background_layer_2, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background_layer_3 = pygame.transform.scale(self.background_layer_3, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # Parallax offsets
        self.parallax_offset_2 = 0
        self.parallax_offset_3 = 0

    def update(self, scroll_speed_2=PARALLAX_SPEED_2, scroll_speed_3=PARALLAX_SPEED_3):
        """Update parallax offsets"""
        self.parallax_offset_2 += scroll_speed_2
        self.parallax_offset_3 += scroll_speed_3

        # Reset offsets to prevent overflow
        if self.parallax_offset_2 >= SCREEN_WIDTH:
            self.parallax_offset_2 = 0
        if self.parallax_offset_3 >= SCREEN_WIDTH:
            self.parallax_offset_3 = 0

    def draw(self, surface):
        """Draw parallax background"""
        # Draw static layer 1
        surface.blit(self.background_layer_1, (0, 0))

        # Draw parallax layer 2
        surface.blit(self.background_layer_2, (-self.parallax_offset_2, 0))
        if self.parallax_offset_2 > 0:
            surface.blit(self.background_layer_2, (SCREEN_WIDTH - self.parallax_offset_2, 0))

        # Draw parallax layer 3
        surface.blit(self.background_layer_3, (-self.parallax_offset_3, 0))
        if self.parallax_offset_3 > 0:
            surface.blit(self.background_layer_3, (SCREEN_WIDTH - self.parallax_offset_3, 0))