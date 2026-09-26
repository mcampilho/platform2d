import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from examples.environment.character_view import AstronomerView
from platform2d.physics.body import Body


ASSET = Path(__file__).resolve().parents[1] / "examples/environment/assets/astronomer-atlas.png"


class CharacterViewTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.view = AstronomerView(ASSET)

    def tearDown(self):
        pygame.quit()

    def test_all_poses_draw_without_changing_physics(self):
        body = Body(60, 70)
        before = (body.x, body.y, body.vx, body.vy, body.on_ground)
        for state in ("idle", "run", "jump", "fall", "dash", "fly", "glide", "wall_slide"):
            with self.subTest(state=state):
                surface = pygame.Surface((160, 160), pygame.SRCALPHA)
                self.view.update(state, 1 / 60)
                rect = self.view.draw(surface, body, facing=1)
                self.assertTrue(rect.colliderect(pygame.Rect(body.x, body.y, body.w, body.h)))
                self.assertGreater(pygame.mask.from_surface(surface).count(), 0)
        self.assertEqual((body.x, body.y, body.vx, body.vy, body.on_ground), before)

    def test_run_alternates_and_left_facing_is_mirrored(self):
        body = Body(60, 70)
        first = pygame.Surface((160, 160), pygame.SRCALPHA)
        second = pygame.Surface((160, 160), pygame.SRCALPHA)
        left = pygame.Surface((160, 160), pygame.SRCALPHA)
        self.view.update("run", 0)
        self.view.draw(first, body, facing=1)
        self.view.update("run", .12)
        self.view.draw(second, body, facing=1)
        self.view.draw(left, body, facing=-1)
        self.assertNotEqual(pygame.image.tostring(first, "RGBA"), pygame.image.tostring(second, "RGBA"))
        self.assertNotEqual(pygame.image.tostring(second, "RGBA"), pygame.image.tostring(left, "RGBA"))
        self.view.update("fall", .02)
        self.view.update("idle", .02)
        self.assertGreater(self.view.landing_left, 0)
        self.view.update("idle", .2)
        self.assertEqual(self.view.landing_left, 0)

    def test_atlas_grid_is_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.png"
            pygame.image.save(pygame.Surface((11, 13)), str(path))
            with self.assertRaises(ValueError):
                AstronomerView(path)


if __name__ == "__main__":
    unittest.main()
