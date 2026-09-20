from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from platform2d.tools.editor_model import MapDocument, new_map

ROOT = Path(__file__).resolve().parents[1]


class DocumentTests(unittest.TestCase):
    def test_paint_drag_is_single_undo_and_redo(self):
        document = MapDocument()
        original = deepcopy(document.data)
        document.paint_line((2,8),(10,8),"=")
        document.paint_line((10,8),(10,11),"=")
        document.commit()
        self.assertEqual(len(document.undo_stack),1)
        self.assertEqual(document.data["tiles"][8][2:11],"="*9)
        painted = deepcopy(document.data)
        document.undo()
        self.assertEqual(document.data,original)
        document.redo()
        self.assertEqual(document.data,painted)

    def test_undo_new_branch_clears_redo_noop_does_not_add_history(self):
        document = MapDocument()
        document.paint(2,2,".")
        document.commit()
        self.assertFalse(document.undo_stack)
        document.paint(2,2,"#")
        document.commit()
        document.undo()
        document.paint(3,2,"=")
        document.commit()
        self.assertFalse(document.redo_stack)

    def test_place_spawn_moves_existing_and_ids_are_unique(self):
        document = MapDocument()
        document.place("spawn",4,15)
        self.assertEqual(sum(o["type"] == "spawn" for o in document.data["objects"]),1)
        first = document.place("coin",7,14)
        second = document.place("coin",8,14)
        self.assertNotEqual(document.data["objects"][first]["id"],document.data["objects"][second]["id"])
        self.assertEqual(document.data["objects"][0]["y"],482)

    def test_move_resize_object_delete_and_restore(self):
        document = MapDocument()
        index = document.place("hazard",8,15)
        document.update_object(index,x=300,w=64)
        document.commit()
        self.assertEqual(document.object_box(document.data["objects"][index]).w,64)
        document.delete_object(index)
        document.undo()
        self.assertEqual(document.data["objects"][index]["x"],300)
        document.undo()
        self.assertEqual(document.data["objects"][index]["w"],32)

    def test_missing_spawn_goal_and_embedded_spawn_are_errors(self):
        document = MapDocument()
        document.delete_object(0)
        self.assertTrue(any("spawn" in i.message for i in document.validate() if i.severity == "error"))
        document.undo()
        document.paint(2,15,"#")
        document.commit()
        with self.assertRaises(ValueError):
            document.playable()
        self.assertTrue(any("espaço livre" in i.message for i in document.validate()))
        document = MapDocument()
        document.delete_object(1)
        self.assertTrue(any("saída" in i.message for i in document.validate()))

    def test_hazard_spawn_and_duplicate_id_validation(self):
        document = MapDocument()
        hazard = document.place("hazard",2,15)
        document.update_object(hazard,id="start")
        document.commit()
        errors = [i.message for i in document.validate() if i.severity == "error"]
        self.assertTrue(any("repetido" in e for e in errors))
        self.assertTrue(any("zona de dano" in e for e in errors))

    def test_resize_retains_objects_reports_bounds_and_can_undo(self):
        document = MapDocument()
        document.resize(12,18)
        self.assertEqual(len(document.data["objects"]),2)
        self.assertTrue(any("limites" in i.message for i in document.validate()))
        document.undo()
        self.assertEqual(document.size,(40,18))

    def test_airborne_spawn_is_warning_not_error(self):
        document = MapDocument()
        document.update_object(0,y=450)
        document.commit()
        issues = document.validate()
        self.assertTrue(any(i.severity == "warning" for i in issues))
        self.assertFalse(any(i.severity == "error" for i in issues))
        document.playable()

    def test_atomic_roundtrip_and_dirty_history(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"nível.json"
            document = MapDocument()
            document.rename("Teste português")
            self.assertTrue(document.dirty)
            document.save(path)
            self.assertFalse(document.dirty)
            loaded = MapDocument.load(path)
            self.assertEqual(document.data,loaded.data)
            document.paint(1,2,"#")
            document.commit()
            self.assertTrue(document.dirty)
            document.undo()
            self.assertFalse(document.dirty)
            self.assertEqual(list(Path(folder).glob("*.tmp")),[])

    def test_failed_atomic_replace_preserves_existing_file_and_dirty_state(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"level.json"
            document = MapDocument()
            document.save(path)
            old = path.read_bytes()
            document.rename("Alterado")
            with patch("platform2d.tools.editor_model.os.replace",side_effect=OSError("simulated write failure")):
                with self.assertRaises(OSError):
                    document.save()
            self.assertEqual(path.read_bytes(),old)
            self.assertTrue(document.dirty)
            self.assertEqual(list(Path(folder).glob("*.tmp")),[])

    def test_invalid_map_cannot_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"level.json"
            document = MapDocument()
            document.save(path)
            old = path.read_bytes()
            document.delete_object(0)
            with self.assertRaises(ValueError):
                document.save()
            self.assertEqual(path.read_bytes(),old)

    def test_advanced_map_rejected_and_missing_spawn_draft_can_open(self):
        data = new_map()
        data["objects"].append({"id":"guard","type":"enemy","x":100,"y":100})
        with self.assertRaises(ValueError):
            MapDocument(data)
        data["objects"] = []
        document = MapDocument(data)
        self.assertEqual(len([i for i in document.validate() if i.severity == "error"]),2)

    def test_preview_is_detached_from_document(self):
        document = MapDocument()
        preview = document.playable()
        preview.objects[0]["x"] = 999
        self.assertEqual(document.data["objects"][0]["x"],64)


class EditorTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        from examples.classic.scene import ClassicScene
        from platform2d.tools.level_editor import LevelEditor
        settings = json.loads((ROOT/"examples/classic/settings.json").read_text())
        self.editor = LevelEditor(lambda level:ClassicScene(level,settings),settings["bindings"])
        self.editor.draw()

    def tearDown(self):
        pygame.quit()

    def event(self,kind,**kwargs):
        self.editor.handle_event(pygame.event.Event(kind,**kwargs))

    def key(self,key,mod=0):
        self.event(pygame.KEYDOWN,key=key,mod=mod)

    def test_mouse_drag_paints_whole_line_and_undo(self):
        e = self.editor
        self.event(pygame.MOUSEBUTTONDOWN,button=1,pos=(280,380))
        self.event(pygame.MOUSEMOTION,pos=(536,380),rel=(256,0),buttons=(1,0,0))
        self.event(pygame.MOUSEBUTTONUP,button=1,pos=(536,380))
        self.assertEqual(e.document.data["tiles"][8][2:11],"#"*9)
        self.key(pygame.K_z,pygame.KMOD_CTRL)
        self.assertEqual(e.document.data["tiles"][8][2:11],"."*9)

    def test_object_selection_drag_and_numeric_edit(self):
        e = self.editor
        e.choose_tool("select")
        # Spawn at world (64,482), canvas origin (200,112).
        self.event(pygame.MOUSEBUTTONDOWN,button=1,pos=(273,602))
        self.event(pygame.MOUSEMOTION,pos=(305,602),rel=(32,0),buttons=(1,0,0))
        self.event(pygame.MOUSEBUTTONUP,button=1,pos=(305,602))
        self.assertEqual(e.document.data["objects"][0]["x"],96)
        e.edit_property("x")
        self.event(pygame.TEXTINPUT,text="100")
        self.key(pygame.K_RETURN)
        self.assertEqual(e.document.data["objects"][0]["x"],100)

    def test_preview_return_preserves_unsaved_data_and_history(self):
        e = self.editor
        e.document.paint(3,9,"=")
        e.finish_edit()
        before = deepcopy(e.document.data)
        history = len(e.document.undo_stack)
        self.key(pygame.K_F5)
        self.assertIsNotNone(e.preview)
        self.key(pygame.K_d)
        e.update(.1)
        self.assertGreater(e.preview.player.body.x,64)
        e.draw()
        self.key(pygame.K_ESCAPE)
        self.assertIsNone(e.preview)
        self.assertEqual(e.document.data,before)
        self.assertEqual(len(e.document.undo_stack),history)
        self.assertTrue(e.document.dirty)

    def test_errors_block_preview_and_modal_esc_does_not_close_editor(self):
        e = self.editor
        e.document.delete_object(0)
        self.key(pygame.K_F5)
        self.assertIsNone(e.preview)
        self.assertEqual(e.modal["kind"],"validation")
        e.draw()
        self.key(pygame.K_ESCAPE)
        self.assertTrue(e.running)
        self.assertIsNone(e.modal)

    def test_unsaved_quit_cancel_and_discard(self):
        e = self.editor
        self.event(pygame.QUIT)
        self.assertTrue(e.running)
        self.assertEqual(e.modal["kind"],"confirm")
        self.key(pygame.K_ESCAPE)
        self.assertTrue(e.running)
        self.event(pygame.QUIT)
        discard = e.modal["buttons"][1][1]
        e.close_modal_action(discard)
        self.assertFalse(e.running)

    def test_save_as_and_existing_target_confirmation(self):
        e = self.editor
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"map.json"
            path.write_text("keep",encoding="utf-8")
            e.save(True)
            e.modal["text"] = str(path)
            e.submit_modal()
            self.assertEqual(e.modal["kind"],"confirm")
            self.assertEqual(path.read_text(),"keep")
            e.close_modal_action(e.modal["buttons"][0][1])
            self.assertFalse(e.document.dirty)
            self.assertEqual(MapDocument.load(path).data,e.document.data)

    def test_zoom_keeps_world_point_under_cursor(self):
        e = self.editor
        e.camera = [200,0]
        point = (610,370)
        before = e.world_position(point)
        e.set_zoom(1.3,point)
        after = e.world_position(point)
        self.assertAlmostEqual(before[0],after[0])
        self.assertAlmostEqual(before[1],after[1])
