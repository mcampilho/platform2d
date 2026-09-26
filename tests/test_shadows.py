import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from platform2d.physics.body import Box
from platform2d.rendering.shadows import draw_shadows, shadow_polygon


class ShadowTests(unittest.TestCase):
    def test_shadow_projects_behind_occluder_only(self):
        pygame.init()
        try:
            box = Box(80, 40, 10, 20)
            polygon = shadow_polygon((20, 50), box, 100)
            self.assertGreater(max(x for x, _ in polygon), box.right)
            self.assertEqual(shadow_polygon((85, 50), box), ())
            surface = pygame.Surface((200, 100))
            surface.fill((255, 255, 255))
            draw_shadows(surface, (20, 50), [box], radius=150, length=100)
            self.assertEqual(surface.get_at((60, 50))[:3], (255, 255, 255))
            self.assertLess(surface.get_at((140, 50)).r, 255)
        finally:
            pygame.quit()

    def test_distant_occluders_do_not_change_view(self):
        pygame.init()
        try:
            surface = pygame.Surface((200, 100))
            surface.fill((240, 240, 240))
            draw_shadows(surface, (20, 50), [Box(600, 40, 10, 20)], radius=100)
            self.assertEqual(surface.get_at((100, 50))[:3], (240, 240, 240))
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
