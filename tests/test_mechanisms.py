from copy import deepcopy
import os
import tempfile
from pathlib import Path
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from platform2d.core.events import Event, EventBus
from platform2d.core.input import Actions
from platform2d.gameplay.mechanisms import Mechanisms, check_mechanism_structure
from platform2d.world.room import RoomWorld
from platform2d.tools.world_editor import WorldDocument
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.level_editor import LevelEditor
from examples.editor.profiles import editor_profiles,template_document
from examples.mechanisms.world import definition


class MechanismTests(unittest.TestCase):
    def test_notifications_use_snapshot_and_unsubscribe(self):
        bus = EventBus()
        seen = []
        stop = bus.subscribe("switch_activated",lambda e:(seen.append(e.source),stop()))
        bus.publish(Event("switch_activated",("a","s")))
        bus.publish(Event("switch_activated",("a","s")))
        self.assertEqual(seen,[("a","s")])

    def test_activation_is_once_only_and_all_conditions_required(self):
        state = Mechanisms()
        seen = []
        state.events.subscribe("switch_activated",seen.append)
        first = dict(type="switch",id="a")
        second = dict(type="switch",id="b",requires=[dict(room="room",switch="a")])
        gate = dict(requires=[dict(room="room",switch="a"),dict(room="room",switch="b")])
        self.assertFalse(state.activate("room",second))
        self.assertTrue(state.activate("room",first))
        self.assertFalse(state.enabled(gate))
        self.assertFalse(state.activate("room",first))
        self.assertTrue(state.activate("room",second))
        self.assertTrue(state.enabled(gate))
        self.assertEqual(len(seen),2)
        state.reset()
        self.assertFalse(state.active)

    def test_runtime_rejects_dangling_references_but_editor_can_repair(self):
        data = definition()
        data["rooms"]["control"]["objects"][-1]["requires"][0]["switch"] = "absent"
        with self.assertRaises(ValueError):
            RoomWorld(data)
        doc = WorldDocument(data)
        self.assertTrue(any("inexistente" in i.message and i.severity == "error" for i in doc.validate()))

    def test_schema_rejects_invalid_and_duplicate_requirements(self):
        for refs in (None,"a",[dict(room="a")],[dict(room=2,switch="s")],
                     [dict(room="a",switch="s")]*2):
            with self.subTest(refs=refs),self.assertRaises(ValueError):
                check_mechanism_structure(dict(type="door",requires=refs))
        with self.assertRaises(ValueError):
            check_mechanism_structure(dict(type="switch",activation=[]))

    def test_closed_door_with_own_key_behind_it_is_error(self):
        data = definition()
        data["rooms"]["control"]["objects"][-1]["requires"] = [dict(room="reactor",switch="sensor")]
        issues = WorldDocument(data).validate()
        self.assertTrue(any(i.severity == "error" and "saída" in i.message for i in issues))
        self.assertTrue(any("condições bloqueadas" in i.message for i in issues))

    def test_circular_switches_cannot_unlock_final_goal(self):
        data = definition()
        switches = data["rooms"]["reactor"]["objects"]
        sensor = next(o for o in switches if o["id"] == "sensor")
        sensor["requires"] = [dict(room="reactor",switch="console")]
        self.assertTrue(any(i.severity == "error" and "Todas as saídas" in i.message for i in WorldDocument(data).validate()))

    def test_rename_room_and_switch_updates_conditions_and_undo(self):
        doc = WorldDocument(definition())
        original = doc.snapshot()
        doc.rename_room("hall")
        doc.update_object(1,id="generator")
        doc.commit()
        self.assertEqual(doc.data["objects"][-1]["requires"],[dict(room="hall",switch="generator")])
        console = next(o for o in doc.world["rooms"]["reactor"]["objects"] if o["id"] == "console")
        self.assertIn(dict(room="hall",switch="generator"),console["requires"])
        doc.undo()
        doc.undo()
        self.assertEqual(doc.snapshot(),original)

    def test_roundtrip_and_delete_report_conditions(self):
        doc = WorldDocument(definition())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"mechanisms.json"
            doc.save(path)
            self.assertEqual(MapDocument.load(path).snapshot(),doc.snapshot())
        doc.delete_object(1)
        self.assertTrue(any(i.severity == "error" and "inexistente" in i.message for i in doc.validate()))


class MechanismUITests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.profiles = editor_profiles()
        classic = self.profiles["classic"]
        self.editor = LevelEditor(classic["factory"],classic["bindings"],template_document("mechanisms"),profiles=self.profiles)

    def tearDown(self):
        pygame.quit()

    def choose(self,label):
        e = self.editor
        e.draw()
        callback = next(cb for title,cb in e.modal.get("items",[])+list(e.modal.get("footer",[])) if label in title)
        e.close_modal_action(callback)

    def test_editor_condition_picker_remove_add_and_activation_mode(self):
        e = self.editor
        e.selected = 3
        e.special_properties()
        self.choose("Condições")
        self.choose("Remover")
        self.assertEqual(e.document.data["objects"][3]["requires"],[])
        self.choose("Adicionar")
        self.choose("control / power")
        self.assertEqual(e.document.data["objects"][3]["requires"],[dict(room="control",switch="power")])
        e.modal = None
        e.selected = 1
        e.special_properties()
        self.choose("Ativação")
        self.assertEqual(e.document.data["objects"][1]["activation"],"touch")
        e.draw()

    def test_death_preserves_switches_reset_clears_and_preview_is_isolated(self):
        e = self.editor
        before = e.document.snapshot()
        e.start_preview()
        scene = e.preview
        switch = scene.world.current.objects("switch")[0]
        scene.world.mechanisms.activate("control",switch)
        scene.die()
        self.assertIn(("control","power"),scene.world.mechanisms.active)
        scene.reset()
        self.assertFalse(scene.world.mechanisms.active)
        e.stop_preview()
        self.assertEqual(e.document.snapshot(),before)

    def test_touch_once_pause_freezes_and_hazard_has_priority(self):
        e = self.editor
        doc = e.document
        obj = doc.data["objects"][1]
        obj.update(x=64,y=482,activation="touch")
        scene = self.profiles["rooms"]["factory"](doc.playable())
        seen = []
        scene.world.mechanisms.events.subscribe("switch_activated",seen.append)
        empty = Actions(frozenset(),frozenset(),frozenset())
        scene.paused = True
        scene.update(1/60,empty)
        self.assertFalse(seen)
        scene.paused = False
        scene.update(1/60,empty)
        scene.update(1/60,empty)
        self.assertEqual(len(seen),1)
        scene.reset()
        scene.world.current.level.objects.append(dict(id="danger",type="hazard",x=64,y=482))
        scene.update(1/60,empty)
        self.assertEqual(scene.deaths,1)
        self.assertFalse(scene.world.mechanisms.active)
