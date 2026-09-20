import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ["SDL_VIDEODRIVER"] = os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from examples.ranged.scene import RangedScene
from examples.ranged.level import definition
from platform2d.tools.editor_model import MapDocument
from platform2d.core.input import Actions
from platform2d.core.control_settings import ControlSettings,button_codes
from platform2d.gameplay.projectiles import WeaponSpec

DT = 1/60


class RangedTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.settings = json.loads((Path(__file__).resolve().parents[1]/"examples/ranged/settings.json").read_text())
        self.scene = RangedScene(MapDocument(definition()).playable(),self.settings)

    def tearDown(self):
        pygame.quit()

    def test_held_fire_has_cadence_and_hits_targets(self):
        scene = self.scene
        for _ in range(120):
            scene.update(DT,Actions(held=frozenset({"shoot"})))
        self.assertEqual(scene.shots,8)
        self.assertTrue({"training","sentry-a"} <= scene.destroyed)
        self.assertLess(len(scene.projectiles.items),10)

    def test_pause_freezes_projectiles_and_weapon_then_single_step_advances(self):
        s = self.scene
        s.update(DT,Actions(held=frozenset({"shoot"})))
        s.update(DT,Actions(pressed=frozenset({"pause"})))
        p = s.projectiles.items[0]
        state = (p.x,p.y,p.remaining,s.weapon.remaining,s.elapsed)
        for _ in range(30): s.update(DT,Actions(held=frozenset({"shoot"})))
        self.assertEqual((p.x,p.y,p.remaining,s.weapon.remaining,s.elapsed),state)
        s.update(DT,Actions(pressed=frozenset({"step"})))
        self.assertGreater(p.x,state[0])
        self.assertTrue(s.paused)

    def test_respawn_clears_shots_restores_health_and_keeps_completed_targets(self):
        s = self.scene
        s.destroyed.add("training")
        s.respawn_point = (490,482)
        s.health.hit()
        s.projectiles.spawn((1,1),(1,0),"foe","enemy",WeaponSpec())
        s.update(DT,Actions(pressed=frozenset({"restart"})))
        self.assertEqual((s.player.body.x,s.player.body.y),(490,482))
        self.assertFalse(s.projectiles.items)
        self.assertEqual(s.health.remaining,5)
        self.assertIn("training",s.destroyed)
        self.assertNotIn("training",s.targets)

    def test_reset_restores_all_targets_and_initial_spawn(self):
        s = self.scene
        s.destroyed.add("training")
        s.respawn_point = (490,482)
        s.reset()
        self.assertFalse(s.destroyed)
        self.assertEqual(s.respawn_point,s.level.spawn)
        self.assertEqual(len(s.targets),4)

    def test_exit_is_locked_until_every_target_is_destroyed(self):
        s = self.scene
        s.player.respawn((910,482))
        s.update(DT,Actions())
        self.assertFalse(s.won)
        s.destroyed.update(o["id"] for o in s.objects)
        s.update(DT,Actions())
        self.assertTrue(s.won)
        self.assertFalse(s.projectiles.items)

    def test_muzzle_cannot_spawn_past_adjacent_wall(self):
        s = self.scene
        s.player.respawn((392,482))
        s.update(DT,Actions(held=frozenset({"shoot"})))
        s.update(DT,Actions())
        self.assertFalse([p for p in s.projectiles.items if p.team == "player"])
        self.assertFalse(s.destroyed)

    def test_multiple_enemy_hits_respect_player_invulnerability(self):
        s = self.scene
        for i in range(2):
            s.projectiles.spawn((60,497),(1,0),str(i),"enemy",WeaponSpec(speed=600))
        s.update(DT,Actions())
        self.assertEqual(s.health.remaining,4)

    def test_cover_blocks_turret_line_of_sight(self):
        s = self.scene
        s.player.respawn((500,482))
        for weapon in s.turrets.values(): weapon.remaining = 0
        s.update(DT,Actions())
        owners = {p.owner for p in s.projectiles.items}
        self.assertNotIn("sentry-a",owners)
        self.assertIn("sentry-b",owners)

    def test_weapon_history_and_file_round_trip(self):
        document = MapDocument(definition())
        before = document.snapshot()
        document.update_weapon(speed=800,damage=2)
        document.undo()
        self.assertEqual(document.snapshot(),before)
        document.redo()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"arena.json"
            document.save(path)
            loaded = MapDocument.load(path)
            self.assertEqual(loaded.profile,"ranged")
            self.assertEqual(loaded.snapshot(),document.snapshot())
            self.assertEqual(RangedScene(loaded.playable(),self.settings).spec.damage,2)

    def test_invalid_weapon_or_target_edits_are_transactional(self):
        document = MapDocument(definition())
        before = document.snapshot()
        for change in ({"speed":0},{"damage":True},{"lifetime":float("nan")},{"unknown":3}):
            with self.assertRaises(ValueError): document.update_weapon(**change)
            self.assertEqual(document.snapshot(),before)
        index = next(i for i,o in enumerate(document.data["objects"]) if o["type"] == "turret")
        for change in ({"hp":0},{"hp":1.5},{"interval":0},{"range":-1},{"projectile_speed":True}):
            with self.assertRaises(ValueError): document.update_object(index,**change)
            self.assertEqual(document.snapshot(),before)

    def test_structure_rejects_blocked_target_reserved_id_and_wrong_size(self):
        document = MapDocument(definition())
        target = next(o for o in document.data["objects"] if o["type"] == "target")
        target.update(x=416,y=480,id="player")
        errors = [i.message for i in document.validate() if i.severity == "error"]
        self.assertTrue(any("bloqueado" in m for m in errors))
        self.assertTrue(any("reservado" in m for m in errors))
        with self.assertRaises(ValueError): document.resize(40,18)
        self.assertTrue(any("Não existe pesquisa" in i.message for i in document.validate()))

    def test_shoot_action_uses_gamepad_x_and_can_coexist_with_melee(self):
        settings = ControlSettings(self.settings["bindings"],"ranged")
        self.assertEqual(button_codes(settings.data)["shoot"],pygame.CONTROLLER_BUTTON_X)
        both = ControlSettings({"attack":["j"],"shoot":["k"]})
        self.assertNotEqual(both.data["buttons"]["attack"],both.data["buttons"]["shoot"])

    def test_target_in_hazard_can_still_be_shot_from_a_safe_distance(self):
        data = definition()
        data["objects"].append(dict(id="danger",type="hazard",x=215,y=482,w=24,h=30))
        errors = [i for i in MapDocument(data).validate() if i.severity == "error"]
        self.assertFalse(errors)
