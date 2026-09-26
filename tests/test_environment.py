import json
import os
import unittest
from unittest.mock import patch
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from examples.environment.scene import EnvironmentScene
from platform2d.core.input import Actions
from platform2d.world.tilemap import TileMap
from platform2d.rendering.lighting import glow_sprite


ROOT = Path(__file__).resolve().parents[1] / "examples/environment"
DT = 1 / 60


def actions(*held, pressed=()):
    return Actions(frozenset(held), frozenset(pressed), frozenset())


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        data = json.loads((ROOT / "assets/laboratory.json").read_text(encoding="utf-8"))
        settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
        self.scene = EnvironmentScene(TileMap(data, {"moving_platform", "switch", "gate",
                                               "water", "gravity_zone"}), settings)

    def tearDown(self):
        pygame.quit()

    def test_platform_advances_and_carries_rider(self):
        scene = self.scene
        platform = scene.platforms[0]
        scene.player.body.teleport(platform.box.x + 15, platform.box.y - 30)
        scene.player.body.on_ground = True
        before = scene.player.body.x
        scene.update(DT, actions())
        self.assertGreater(scene.player.body.x, before)
        self.assertAlmostEqual(scene.player.body.box.bottom, platform.box.y)

    def test_switch_opens_solid_gate_and_reset_closes_it(self):
        scene = self.scene
        gate = next(o for o in scene.level.objects if o["type"] == "gate")
        scene.player.body.teleport(gate["x"] - 24, 480)
        scene.update(DT, actions("right"))
        self.assertLessEqual(scene.player.body.box.right, gate["x"])
        switch = next(o for o in scene.level.objects if o["type"] == "switch")
        scene.player.body.teleport(switch["x"], 480)
        scene.update(DT, actions(pressed=("interact",)))
        self.assertIn(gate["id"], scene.gates_open)
        self.assertGreater(scene.camera_effects.trauma,0)
        scene.player.body.teleport(gate["x"] - 24, 480)
        for _ in range(20): scene.update(DT, actions("right"))
        self.assertGreater(scene.player.body.x, gate["x"])
        scene.update(DT, actions(pressed=("reset",)))
        self.assertNotIn(gate["id"], scene.gates_open)

    def test_water_and_low_gravity_are_local(self):
        scene = self.scene
        controller = scene.player.controller
        scene.player.body.teleport(1250, 400)
        scene.update(DT, actions("jump"))
        self.assertTrue(controller.submerged)
        self.assertEqual(controller.motion_state, "fly")
        self.assertGreater(len(scene.feedback.particles), 0)
        scene.draw(pygame.Surface((960, 576)), 0)
        scene.player.body.teleport(1700, 400)
        scene.update(DT, actions())
        self.assertFalse(controller.submerged)
        self.assertEqual(controller.gravity_scale, .38)
        scene.player.body.teleport(2100, 400)
        scene.update(DT, actions())
        self.assertEqual(controller.gravity_scale, 1)
        scene.draw(pygame.Surface((960, 576)), 0)

    def test_effects_can_be_disabled_without_changing_world_rules(self):
        scene = self.scene
        self.assertIs(glow_sprite(64, (247, 190, 96)), glow_sprite(64, (247, 190, 96)))
        scene.update(DT, actions(pressed=("effects",)))
        self.assertFalse(scene.feedback.enabled)
        scene.player.body.teleport(1250, 400)
        scene.update(DT, actions("jump"))
        self.assertTrue(scene.player.controller.submerged)
        self.assertEqual(scene.feedback.particles, [])
        scene.draw(pygame.Surface((960, 576)), 0)
        scene.update(DT, actions(pressed=("effects",)))
        self.assertTrue(scene.feedback.enabled)

    def test_theme_reload_is_safe_and_keeps_world_state(self):
        scene=self.scene
        scene.paused=True
        player_before=(scene.player.body.x,scene.player.body.y)
        scene.update(DT,actions(pressed=("reload_theme",)))
        self.assertEqual(scene.theme.id,"observatory")
        self.assertIn("recarregado",scene.theme_notice)
        valid_theme=scene.theme
        with patch("examples.environment.scene.load_theme",side_effect=ValueError("cor inválida")):
            scene.update(DT,actions(pressed=("reload_theme",)))
        self.assertIs(scene.theme,valid_theme)
        self.assertIn("preservado",scene.theme_notice)
        self.assertEqual((scene.player.body.x,scene.player.body.y),player_before)

    def test_invalid_environment_references_and_gravity_are_rejected(self):
        settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
        for kind, change in (("switch", {"gate": "missing"}),
                             ("gravity_zone", {"scale": 0}),
                             ("water", {"current": 999})):
            with self.subTest(kind=kind):
                data = json.loads((ROOT / "assets/laboratory.json").read_text(encoding="utf-8"))
                next(obj for obj in data["objects"] if obj["type"] == kind).update(change)
                with self.assertRaises(ValueError):
                    EnvironmentScene(TileMap(data, {"moving_platform", "switch", "gate",
                                                    "water", "gravity_zone"}), settings)


if __name__ == "__main__":
    unittest.main()
