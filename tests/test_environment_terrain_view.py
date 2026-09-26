import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from examples.environment.terrain_view import bridge_plank, stone_tile


class EnvironmentTerrainViewTests(unittest.TestCase):
    def test_tiles_and_bridge_are_cached_with_expected_dimensions(self):
        ground = stone_tile(32, 32, 1, True)
        self.assertIs(ground, stone_tile(32, 32, 1, True))
        self.assertEqual(ground.get_size(), (32, 32))
        self.assertNotEqual(ground.get_at((8, 0)), ground.get_at((8, 15)))
        ledge = stone_tile(32, 32, 1, True, True)
        self.assertEqual(ledge.get_at((16, 20)).a, 0)
        bridge = bridge_plank(96, 12)
        self.assertIs(bridge, bridge_plank(96, 12))
        self.assertEqual(bridge.get_size(), (96, 12))
        self.assertGreater(bridge.get_at((48, 1)).a, 0)


if __name__ == "__main__":
    unittest.main()
