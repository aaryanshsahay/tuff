"""
Cursor utilities for the game
"""
import pygame


# Store cursor images globally
cursor_image = None
map_frame_cursor = None


def init_cursors():
    """Initialize custom cursors"""
    global cursor_image, map_frame_cursor

    # Load and set custom cursor
    cursor_sheet = pygame.image.load("assets/dialogue_box/20240711dragonMouseCursorBig-Sheet.png")
    # The sheet is 92x23 with 4 cursors, each is roughly 23x23
    # Extract the first cursor only
    cursor_image = pygame.Surface((23, 23), pygame.SRCALPHA)
    cursor_image.blit(cursor_sheet, (0, 0), (0, 0, 23, 23))
    # Set the cursor with hotspot at (0, 0)
    pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), cursor_image))

    # Load map frame cursor
    map_frame_cursor = pygame.image.load("assets/dialogue_box/20240713dragonMapFrame.png")
    map_frame_cursor = pygame.transform.scale(map_frame_cursor, (40, 40))  # Adjust size as needed


def set_default_cursor():
    """Set cursor back to default arrow"""
    if cursor_image:
        pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), cursor_image))


def set_map_frame_cursor():
    """Set cursor to map frame"""
    if map_frame_cursor:
        pygame.mouse.set_cursor(pygame.cursors.Cursor((20, 20), map_frame_cursor))