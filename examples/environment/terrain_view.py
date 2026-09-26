"""Cached observatory stonework; all coordinates and collisions remain unchanged."""
from functools import lru_cache

import pygame


@lru_cache(maxsize=48)
def stone_tile(width, height, variant, exposed, one_way=False):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    if one_way:
        pygame.draw.rect(image, (20, 35, 43), (0, 3, width, 7))
        pygame.draw.rect(image, (53, 79, 77), (0, 2, width, 5))
        pygame.draw.line(image, (158, 163, 113), (0, 1), (width - 1, 1), 2)
        pygame.draw.line(image, (91, 135, 103), (0, 0), (width - 1, 0))
        for x in range(7 + variant % 3, width, 14):
            pygame.draw.circle(image, (177, 145, 94), (x, 5), 1)
        return image

    bases = ((30, 48, 53), (33, 52, 55), (26, 45, 51), (35, 52, 55))
    image.fill(bases[variant % 4])
    pygame.draw.rect(image, (19, 34, 41), (2, 4, width - 4, height - 5), 1)
    pygame.draw.line(image, (53, 74, 76), (2, 5), (width - 3, 5))
    pygame.draw.line(image, (19, 34, 41), (0, height - 2), (width - 1, height - 2), 2)
    if variant % 2:
        pygame.draw.lines(image, (63, 84, 82), False,
                          ((5, 15), (11, 18), (15, 17), (19, 24)), 1)
    else:
        pygame.draw.lines(image, (54, 78, 78), False,
                          ((width - 6, 12), (width - 12, 15), (width - 16, 21)), 1)
    for number in range(3):
        x = (variant * 11 + number * 13 + 5) % max(1, width - 3)
        y = (variant * 7 + number * 9 + 11) % max(1, height - 5)
        pygame.draw.circle(image, (55, 78, 76), (x, y), 1)
    if exposed:
        pygame.draw.rect(image, (50, 79, 71), (0, 0, width, 5))
        pygame.draw.line(image, (112, 154, 107), (0, 0), (width - 1, 0), 2)
        pygame.draw.line(image, (165, 166, 111), (4, 1), (width - 9, 1))
        for x in (6 + variant % 3, 21 + variant % 2):
            pygame.draw.line(image, (82, 131, 95), (x, 0),
                             (x - 1, -2 - variant % 2), 1)
    return image


@lru_cache(maxsize=12)
def bridge_plank(width, height):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(image, (26, 46, 49), (0, 2, width, height - 2), border_radius=3)
    pygame.draw.rect(image, (55, 82, 76), (1, 3, width - 2, height - 7), 1,
                     border_radius=2)
    pygame.draw.line(image, (150, 178, 129), (1, 1), (width - 2, 1), 3)
    pygame.draw.line(image, (91, 128, 101), (6, 4), (width - 7, 4))
    for x in (13, width - 14):
        pygame.draw.circle(image, (181, 145, 94), (x, height - 4), 2)
    return image
