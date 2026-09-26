import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from platform2d.physics.body import Box
from platform2d.rendering.ambient import draw_ambient


class AmbientTests(unittest.TestCase):
    def test_animated_region_is_clipped_and_deterministic(self):
        for kind in ("water", "gravity_zone"):
            with self.subTest(kind=kind):
                region = Box(20, 20, 120, 100)
                first = pygame.Surface((180, 140))
                second = pygame.Surface((180, 140))
                first.fill((0, 0, 0))
                second.fill((0, 0, 0))
                draw_ambient(first, region, (0, 0), 1.5, kind)
                draw_ambient(second, region, (0, 0), 1.5, kind)
                self.assertEqual(pygame.image.tostring(first, "RGB"),
                                 pygame.image.tostring(second, "RGB"))
                self.assertEqual(first.get_at((0, 0))[:3], (0, 0, 0))
                self.assertTrue(any(first.get_at((x, y))[:3] != (0, 0, 0)
                                    for x in range(20, 140) for y in range(20, 120)))

    def test_offscreen_region_does_not_draw(self):
        surface = pygame.Surface((100, 100))
        surface.fill((17, 23, 31))
        before = pygame.image.tostring(surface, "RGB")
        draw_ambient(surface, Box(1000, 1000, 120, 100), (0, 0), 2, "water")
        self.assertEqual(pygame.image.tostring(surface, "RGB"), before)


if __name__ == "__main__":
    unittest.main()
