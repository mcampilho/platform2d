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

from examples.editor.profiles import editor_profiles, template_document
from examples.rooms.scene import RoomsScene
from examples.precision.scene import PrecisionScene
from platform2d.tools.editor_model import MapDocument, new_map
from platform2d.tools.world_editor import WorldDocument
from platform2d.tools.level_editor import LevelEditor


class WorldDocumentTests(unittest.TestCase):
    def errors(self,doc):
        return [i for i in doc.validate() if i.severity == "error"]

    def test_new_world_and_existing_world_are_playable(self):
        for doc in (WorldDocument(),template_document("rooms")):
            self.assertFalse(self.errors(doc))
            world = doc.playable()
            self.assertEqual(len(world.rooms),2)
            world.current.state.removed.add("anything")
            self.assertNotIn("removed",doc.data)

    def test_global_history_across_rooms_and_deletion(self):
        doc = WorldDocument()
        before = doc.snapshot()
        doc.paint(3,8,"=")
        doc.switch_room("gallery")
        doc.paint(4,9,"#")
        doc.commit()
        doc.undo()
        self.assertEqual(doc.data["tiles"][9][4],".")
        doc.undo()
        self.assertEqual(doc.snapshot(),before)
        doc.redo()
        self.assertEqual(doc.world["rooms"]["atrium"]["tiles"][8][3],"=")
        doc.add_room("third")
        doc.delete_room()
        doc.undo()
        self.assertIn("third",doc.world["rooms"])
        doc.undo()
        self.assertNotIn("third",doc.world["rooms"])

    def test_room_and_entry_rename_update_all_references_atomically(self):
        doc = WorldDocument()
        before = doc.snapshot()
        doc.rename_room("hall")
        self.assertEqual(doc.world["start_room"],"hall")
        self.assertEqual(doc.world["rooms"]["gallery"]["objects"][-1]["target_room"],"hall")
        doc.update_object(0,id="arrival")
        doc.commit()
        self.assertEqual(doc.world["start_entry"],"arrival")
        self.assertEqual(doc.world["rooms"]["gallery"]["objects"][-1]["target_entry"],"arrival")
        doc.undo()
        doc.undo()
        self.assertEqual(doc.snapshot(),before)

    def test_invalid_destinations_report_owning_room(self):
        doc = WorldDocument()
        doc.data["objects"][-1]["target_entry"] = "missing"
        issues = self.errors(doc)
        self.assertTrue(any(i.room_id == "atrium" and "destino" in i.message for i in issues))
        with self.assertRaises(ValueError):
            doc.playable()

    def test_deleted_initial_room_does_not_silently_change_start(self):
        doc = WorldDocument()
        doc.delete_room()
        self.assertTrue(any("inicial" in i.message for i in self.errors(doc)))
        self.assertEqual(doc.world["start_room"],"atrium")

    def test_room_with_required_coin_without_link_is_error(self):
        doc = WorldDocument()
        doc.add_room("isolated")
        doc.place("coin",5,15)
        self.assertTrue(any(i.room_id == "isolated" and "ligação" in i.message for i in self.errors(doc)))

    def test_one_way_connection_is_allowed_but_not_claimed_solved(self):
        doc = WorldDocument()
        doc.switch_room("gallery")
        doc.delete_object(2)
        self.assertFalse(self.errors(doc))
        self.assertTrue(any("não provam" in i.message for i in doc.validate()))

    def test_platform_endpoints_speed_and_empty_path(self):
        doc = WorldDocument()
        index = doc.place("moving_platform",8,14)
        with self.assertRaises(ValueError):
            doc.update_object(index,speed=float("nan"))
        obj = doc.data["objects"][index]
        doc.update_object(index,end=[obj["x"],obj["y"]])
        self.assertTrue(any("vazio" in i.message for i in self.errors(doc)))
        doc.update_object(index,end=[2000,300])
        self.assertTrue(any("fora" in i.message for i in self.errors(doc)))

    def test_entry_needs_player_clearance_and_room_size_is_fixed(self):
        doc = WorldDocument()
        index = doc.place("entry",8,15)
        doc.paint(8,15,"#")
        self.assertTrue(any("espaço livre" in i.message for i in self.errors(doc)))
        with self.assertRaises(ValueError):
            doc.resize(40,18)

    def test_world_save_roundtrip_and_failed_replace_preserves_file(self):
        doc = WorldDocument()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"world.json"
            doc.save(path)
            saved = path.read_bytes()
            loaded = MapDocument.load(path)
            self.assertIsInstance(loaded,WorldDocument)
            loaded.switch_room("gallery")
            self.assertFalse(loaded.dirty)
            loaded.rename("New name")
            with patch("platform2d.tools.editor_model.os.replace",side_effect=OSError("failure")):
                with self.assertRaises(OSError):
                    loaded.save()
            self.assertEqual(path.read_bytes(),saved)
            self.assertTrue(loaded.dirty)
            self.assertFalse(list(Path(folder).glob("*.tmp")))
            loaded.save()
            self.assertEqual(MapDocument.load(path).snapshot(),loaded.snapshot())

    def test_precision_profile_persists_without_special_objects(self):
        doc = template_document("precision")
        doc.data["objects"] = [o for o in doc.data["objects"] if o["type"] not in {"ladder","beacon"}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"precision.json"
            doc.save(path)
            self.assertEqual(MapDocument.load(path).profile,"precision")
        with self.assertRaises(ValueError):
            doc.place("door",2,2)


class ProfileUITests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.profiles = editor_profiles()
        classic = self.profiles["classic"]
        self.editor = LevelEditor(classic["factory"],classic["bindings"],WorldDocument(),profiles=self.profiles)

    def tearDown(self):
        pygame.quit()

    def click(self,label):
        e = self.editor
        e.draw()
        # Buttons expose callbacks; text is intentionally tested via modal model.
        modal = e.modal
        entries = modal.get("items",[])+list(modal.get("footer",[]))
        callback = next(callback for text,callback in entries if label in text)
        e.close_modal_action(callback)

    def test_destination_picker_and_special_properties(self):
        e = self.editor
        e.selected = 1
        e.special_properties()
        self.click("Ligar porta")
        self.click("gallery")
        self.click("start")
        self.assertEqual(e.document.data["objects"][1]["target_entry"],"start")
        index = e.document.place("moving_platform",8,14)
        e.selected = index
        e.special_properties()
        self.click("Velocidade")
        e.modal["text"] = "75"
        e.submit_modal()
        self.assertEqual(e.document.data["objects"][index]["speed"],75)
        e.draw()

    def test_new_profile_selection_and_preview_controller(self):
        e = self.editor
        e.new_dialog()
        callback = next(cb for label,cb in e.modal["buttons"] if label == "Precisão")
        e.close_modal_action(callback)
        discard = next(cb for label,cb in e.modal["buttons"] if label == "Descartar")
        e.close_modal_action(discard)
        self.assertEqual(e.document.profile,"precision")
        e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_l,mod=0))
        self.assertEqual(e.tool,"ladder")
        e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F8,mod=0))
        self.assertIsNone(e.analysis)
        self.assertTrue(any("automática" in i.message for i in e.issues))
        e.close_validation()
        e.start_preview()
        self.assertIsInstance(e.preview,PrecisionScene)
        e.draw()
        e.stop_preview()
        e.replace_document(WorldDocument())
        e.start_preview()
        self.assertIsInstance(e.preview,RoomsScene)
        e.draw()

    def test_validation_focus_switches_to_problem_room(self):
        e = self.editor
        e.document.world["rooms"]["gallery"]["objects"][-1]["target_entry"] = "missing"
        e.show_validation()
        e.draw()
        problem = next(i for i in e.issues if i.room_id == "gallery" and i.position)
        issue_index = e.issues.index(problem)
        e.modal["scroll"] = issue_index
        e.draw()
        # Click the first issue's Ver button through the public event path.
        e.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(970,210)))
        self.assertEqual(e.document.active_room,"gallery")
        self.assertIsNotNone(e.selected)
        self.assertIsNone(e.modal)
