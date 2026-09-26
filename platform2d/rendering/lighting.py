"""Small cached translucent glows for game objects; purely visual."""
from functools import lru_cache

import pygame


@lru_cache(maxsize=32)
def glow_sprite(radius, color):
    if type(radius) is not int or not 8 <= radius <= 256:
        raise ValueError("Light radius must be an integer from 8 to 256")
    if len(color) != 3 or any(type(channel) is not int or not 0 <= channel <= 255
                              for channel in color):
        raise ValueError("Light color must contain three RGB bytes")
    image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for fraction, alpha in ((1, 5), (.75, 9), (.5, 16), (.25, 26)):
        pygame.draw.circle(image, (*color, alpha), (radius, radius), round(radius * fraction))
    return image


def draw_glow(surface, point, color, radius=96):
    image = glow_sprite(radius, tuple(color))
    surface.blit(image, (round(point[0] - radius), round(point[1] - radius)))
