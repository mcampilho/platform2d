from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from examples.editor.profiles import editor_profiles,template_document
from examples.mechanisms.world import definition
from examples.rooms.scene import RoomsScene
from platform2d.actors.controller import Movement
from platform2d.core.input import Actions
from platform2d.gameplay.progress import ProgressSlot,capture_progress,restore_progress,default_save_path
from platform2d.tools.level_editor import LevelEditor
from platform2d.world.room import RoomWorld

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT/"examples/rooms/settings.json").read_text())
MOVEMENT = vars(Movement(**SETTINGS["movement"]))
STATS = dict(deaths=2,elapsed=32.5,won=False)


def progressed_world():
    world = RoomWorld(definition())
    world.rooms["control"].state.removed.add("crystal_a")
    world.mechanisms.activate("control",world.rooms["control"].objects("switch")[0])
    world.enter("reactor","start")
    world.set_checkpoint((188,482))
    world.current.state.flags["checkpoint"] = "safe"
    world.mechanisms.activate("reactor",world.current.objects("switch")[0])
    return world


class ProgressTests(unittest.TestCase):
    def test_disk_roundtrip_to_fresh_world_and_no_activation_events(self):
        world = progressed_world()
        with tempfile.TemporaryDirectory() as folder:
            slot = ProgressSlot(Path(folder)/"save.json")
            slot.save(world,MOVEMENT,STATS)
            fresh = RoomWorld(definition())
            events = []
            fresh.mechanisms.events.subscribe("switch_activated",events.append)
            self.assertEqual(slot.load(fresh,MOVEMENT),STATS)
            self.assertEqual(fresh.current_id,"reactor")
            self.assertEqual(fresh.checkpoint,("reactor",(188,482)))
            self.assertEqual(capture_progress(fresh,MOVEMENT,STATS),capture_progress(world,MOVEMENT,STATS))
            self.assertFalse(events)

    def test_platform_phase_and_interpolation_roundtrip(self):
        world = RoomWorld.load(ROOT/"examples/rooms/assets/world.json")
        for room in world.rooms.values():
            room.update(2.37)
        data = capture_progress(world,MOVEMENT,STATS)
        positions = {key:[(p.distance,p.box) for p in room.platforms] for key,room in world.rooms.items()}
        world.reset()
        restore_progress(data,world,MOVEMENT)
        self.assertEqual(positions,{key:[(p.distance,p.box) for p in room.platforms] for key,room in world.rooms.items()})
        self.assertTrue(all(p.previous == p.box for room in world.rooms.values() for p in room.platforms))

    def test_incompatible_world_and_rules_do_not_mutate_session(self):
        world = progressed_world()
        slot = ProgressSlot()
        slot.save(world,MOVEMENT,STATS)
        changed = definition()
        changed["rooms"]["reactor"]["tiles"][4] = "#"+"."*29
        fresh = RoomWorld(changed)
        before = capture_progress(fresh,MOVEMENT,STATS)
        with self.assertRaisesRegex(ValueError,"mundo"):
            slot.load(fresh,MOVEMENT)
        self.assertEqual(capture_progress(fresh,MOVEMENT,STATS),before)
        with self.assertRaisesRegex(ValueError,"movimento"):
            slot.load(world,{**MOVEMENT,"speed":999})

    def test_invalid_payloads_are_rejected_before_any_mutation(self):
        world = progressed_world()
        valid = capture_progress(world,MOVEMENT,STATS)
        mutations = [lambda p:p.update(version=True),lambda p:p.update(version=99),
            lambda p:p["stats"].update(elapsed=float("inf")),lambda p:p["stats"].update(deaths=True),
            lambda p:p["stats"].update(elapsed=10**400),lambda p:p["stats"].update(won=True),
            lambda p:p["checkpoint"].update(position=[1,1]),
            lambda p:p["rooms"]["control"].update(collected=["to_reactor"]),
            lambda p:p["rooms"]["control"].update(collected=["crystal_a","crystal_a"]),
            lambda p:p["rooms"]["reactor"].update(checkpoint="absent"),
            lambda p:p.update(switches=[["reactor","console"]]),
            lambda p:p.update(switches=[["control","power"]]*2),
            lambda p:p["rooms"].pop("control")]
        for mutate in mutations:
            invalid = deepcopy(valid)
            mutate(invalid)
            with self.subTest(mutation=mutate),self.assertRaises(ValueError):
                restore_progress(invalid,world,MOVEMENT)
            self.assertEqual(capture_progress(world,MOVEMENT,STATS),valid)

    def test_failed_replace_preserves_previous_save_and_cleans_temp(self):
        world = progressed_world()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"save.json"
            slot = ProgressSlot(path)
            slot.save(world,MOVEMENT,STATS)
            old = path.read_bytes()
            with patch("platform2d.gameplay.progress.os.replace",side_effect=OSError("simulated")):
                with self.assertRaises(OSError):
                    slot.save(world,MOVEMENT,{**STATS,"elapsed":55})
            self.assertEqual(path.read_bytes(),old)
            self.assertFalse(list(Path(folder).glob("*.tmp")))

    def test_corrupt_wrong_version_and_foreign_files_are_not_overwritten(self):
        world = progressed_world()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"save.json"
            slot = ProgressSlot(path)
            for raw in ('{bad','{"version":1,"version":1}','{"x":NaN}',json.dumps(definition())):
                path.write_text(raw,encoding="utf-8")
                with self.subTest(raw=raw),self.assertRaises(ValueError):
                    slot.save(world,MOVEMENT,STATS)
                self.assertEqual(path.read_text(encoding="utf-8"),raw)

    def test_missing_save_has_clear_error_and_distinct_world_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,"F6"):
                ProgressSlot(Path(folder)/"missing.json").load(progressed_world(),MOVEMENT)
        self.assertNotEqual(default_save_path("levels/a.json"),default_save_path("levels/b.json"))

    def test_won_state_is_retained_when_requirements_are_complete(self):
        world = progressed_world()
        world.current.state.removed.add("crystal_b")
        console = next(o for o in world.current.objects("switch") if o["id"] == "console")
        world.mechanisms.activate("reactor",console)
        slot = ProgressSlot()
        slot.save(world,MOVEMENT,{**STATS,"won":True})
        world.reset()
        self.assertTrue(slot.load(world,MOVEMENT)["won"])


class ProgressSceneTests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def press(self,scene,action):
        scene.update(1/60,Actions(pressed=frozenset({action})))

    def test_save_load_while_paused_and_f2_keeps_save(self):
        scene = RoomsScene(progressed_world(),SETTINGS)
        scene.world = progressed_world()
        scene.player.respawn((420,482))
        scene.deaths,scene.elapsed = 2,32.5
        scene.paused = True
        self.press(scene,"save_progress")
        self.assertIsNotNone(scene.progress_slot.memory)
        self.press(scene,"reset")
        self.assertFalse(scene.world.mechanisms.active)
        self.press(scene,"load_progress")
        self.assertFalse(scene.paused)
        self.assertEqual((scene.player.body.x,scene.player.body.y),(188,482))
        self.assertEqual(scene.player.body.vx,0)
        self.assertEqual(scene.deaths,2)
        self.assertEqual(scene.elapsed,32.5)
        self.assertEqual(len(scene.world.mechanisms.active),2)

    def test_transition_refuses_save_and_load(self):
        scene = RoomsScene(RoomWorld(definition()),SETTINGS)
        scene.transition.start(lambda:None)
        self.press(scene,"save_progress")
        self.assertIsNone(scene.progress_slot.memory)
        self.assertIn("passagem",scene.progress_message)

    def test_editor_save_is_memory_only_and_discarded_with_preview(self):
        profiles = editor_profiles()
        classic = profiles["classic"]
        e = LevelEditor(classic["factory"],classic["bindings"],template_document("mechanisms"),profiles=profiles)
        before = e.document.snapshot()
        e.start_preview()
        self.assertIsNone(e.preview.progress_slot.path)
        e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F6,mod=0))
        e.update(1/60)
        self.assertIsNotNone(e.preview.progress_slot.memory)
        e.draw()
        e.stop_preview()
        e.start_preview()
        self.assertIsNone(e.preview.progress_slot.memory)
        self.assertEqual(e.document.snapshot(),before)
