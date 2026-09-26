import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from examples.environment.object_view import draw_gate, draw_switch


class EnvironmentObjectViewTests(unittest.TestCase):
    def test_open_gate_has_clear_passage(self):
        closed = pygame.Surface((64, 180))
        opened = pygame.Surface((64, 180))
        closed.fill((9, 21, 34))
        opened.fill((9, 21, 34))
        rect = pygame.Rect(16, 10, 32, 160)
        draw_gate(closed, rect, False)
        draw_gate(opened, rect, True)
        self.assertNotEqual(closed.get_at((32, 60))[:3], (9, 21, 34))
        self.assertEqual(opened.get_at((32, 60))[:3], (9, 21, 34))

    def test_switch_changes_color_when_active(self):
        inactive = pygame.Surface((40, 46))
        active = pygame.Surface((40, 46))
        rect = pygame.Rect(4, 4, 32, 38)
        draw_switch(inactive, rect, False)
        draw_switch(active, rect, True)
        self.assertNotEqual(pygame.image.tostring(inactive, "RGBA"),
                            pygame.image.tostring(active, "RGBA"))


if __name__ == "__main__":
    unittest.main()
