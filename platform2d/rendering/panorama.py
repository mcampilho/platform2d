"""A still painted panorama that scrolls more slowly than the game world."""
from pathlib import Path

import pygame


class Panorama:
    def __init__(self, path, height=576, parallax=.27):
        if not 0 <= parallax <= 1:
            raise ValueError("Panorama parallax must be between 0 and 1")
        source = pygame.image.load(str(Path(path)))
        if source.get_height() <= 0 or source.get_width() <= 0:
            raise ValueError("Panorama image must have positive dimensions")
        width = round(source.get_width() * height / source.get_height())
        self.image = pygame.transform.smoothscale(source, (width, height))
        self.parallax = parallax
        self._format = None

    def draw(self, surface, camera_x):
        target_format = (surface.get_bitsize(), surface.get_masks())
        if target_format != self._format and pygame.display.get_surface() is not None:
            self.image = (self.image.convert_alpha(surface) if self.image.get_flags() & pygame.SRCALPHA
                          else self.image.convert(surface))
            self._format = target_format
        overflow = max(0, self.image.get_width() - surface.get_width())
        x = min(overflow, max(0, round(camera_x * self.parallax)))
        surface.blit(self.image, (-x, 0))
        if self.image.get_width() < surface.get_width():
            pygame.draw.rect(surface, (11, 23, 40),
                             (self.image.get_width(), 0,
                              surface.get_width() - self.image.get_width(), surface.get_height()))
