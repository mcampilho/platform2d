import json
import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from examples.precision.scene import PrecisionScene
from platform2d.actors.abilities import Abilities
from platform2d.actors.controller import Movement
from platform2d.world.tilemap import TileMap


ROOT = Path(__file__).resolve().parents[1] / "examples/mobility"


class MobilityLaboratoryTests(unittest.TestCase):
    def test_five_zones_load_and_render(self):
        pygame.init()
        try:
            data = json.loads((ROOT / "assets/laboratory.json").read_text(encoding="utf-8"))
            settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
            level = TileMap(data)
            Movement(**settings["movement"])
            Abilities(**settings["abilities"])
            self.assertEqual(len(level.properties["lessons"]), 5)
            scene = PrecisionScene(level, settings)
            screen = pygame.Surface((960, 576))
            for lesson in level.properties["lessons"]:
                scene.player.body.teleport(lesson["x"], 400)
                scene.draw(screen, 0)
            self.assertEqual(scene.total, 0)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
