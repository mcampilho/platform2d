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
from platform2d.core.input import Input
from platform2d.core.gamepad import Gamepads
from platform2d.core.control_settings import ControlSettings, defaults, validate, button_codes
from platform2d.tools.controls_panel import ControlsPanel
from platform2d.core.game import Game
from examples.editor.profiles import editor_profiles, template_document
from platform2d.tools.level_editor import LevelEditor

BINDINGS = {"left":["a","left"],"right":["d","right"],"jump":["space","z"],"pause":["p"]}


def key(code, down=True, **kwargs):
    return pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP,key=code,mod=0,**kwargs)


def button(code, down=True, instance=71):
    return pygame.event.Event(pygame.CONTROLLERBUTTONDOWN if down else pygame.CONTROLLERBUTTONUP,button=code,instance_id=instance)


def axis(value, index=0):
    return pygame.event.Event(pygame.CONTROLLERAXISMOTION,axis=index,value=round(value*32767),instance_id=71)


class ControlsTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/"classic.controls.json"

    def tearDown(self):
        pygame.quit()
        self.temp.cleanup()

    def state(self):
        data = defaults(BINDINGS)
        state = Input(data["keys"],button_codes(data))
        state.attach(71)
        return state

    def test_keyboard_and_controller_share_action_edges(self):
        state = self.state()
        state.feed([key(pygame.K_SPACE),button(pygame.CONTROLLER_BUTTON_A)])
        self.assertEqual(state.consume().pressed,{"jump"})
        state.feed([key(pygame.K_SPACE,False)])
        self.assertEqual(state.consume().held,{"jump"})
        state.feed([button(pygame.CONTROLLER_BUTTON_A,False)])
        self.assertEqual(state.consume().released,{"jump"})

    def test_pad_tap_latched_once_and_foreign_or_joystick_events_ignored(self):
        state = self.state()
        state.feed([button(pygame.CONTROLLER_BUTTON_A),button(pygame.CONTROLLER_BUTTON_A,False)])
        action = state.consume()
        self.assertEqual(action.pressed,{"jump"})
        self.assertEqual(action.released,{"jump"})
        state.feed([button(pygame.CONTROLLER_BUTTON_A,instance=99),pygame.event.Event(pygame.JOYBUTTONDOWN,button=0,instance_id=71)])
        self.assertFalse(state.consume().held)
        self.assertFalse(state.consume().pressed)

    def test_axis_deadzone_hysteresis_reversal_and_dpad(self):
        state = self.state()
        state.feed([axis(.34)])
        self.assertFalse(state.consume().held)
        state.feed([axis(.4)])
        self.assertEqual(state.consume().pressed,{"right"})
        state.feed([axis(.28)])
        self.assertEqual(state.consume().held,{"right"})
        state.feed([axis(-.28)])
        self.assertEqual(state.consume().released,{"right"})
        state.feed([axis(-.8),button(pygame.CONTROLLER_BUTTON_DPAD_RIGHT)])
        self.assertEqual(state.consume().axis(),0)
        state.feed([axis(0)])
        self.assertEqual(state.consume().held,{"right"})

    def test_disconnect_releases_only_pad_and_drops_pending_presses(self):
        state = self.state()
        state.feed([button(pygame.CONTROLLER_BUTTON_A),key(pygame.K_d)])
        state.consume()
        state.attach(None)
        action = state.consume()
        self.assertEqual(action.released,{"jump"})
        self.assertEqual(action.held,{"right"})
        state.attach(71)
        state.feed([button(pygame.CONTROLLER_BUTTON_A)])
        state.attach(None)
        self.assertNotIn("jump",state.consume().pressed)

    def test_focus_loss_discards_pending_and_requires_neutral_stick(self):
        state = self.state()
        state.feed([button(pygame.CONTROLLER_BUTTON_A),axis(1),pygame.event.Event(pygame.WINDOWFOCUSLOST)])
        self.assertFalse(state.consume().pressed)
        state.feed([key(pygame.K_SPACE),button(pygame.CONTROLLER_BUTTON_A)])
        self.assertFalse(state.consume().held)
        state.feed([pygame.event.Event(pygame.WINDOWFOCUSGAINED),axis(.9)])
        self.assertFalse(state.consume().held)
        state.feed([axis(0),axis(.9)])
        self.assertEqual(state.consume().pressed,{"right"})

    def test_clear_suppresses_held_until_release(self):
        state = self.state()
        state.feed([key(pygame.K_SPACE),button(pygame.CONTROLLER_BUTTON_A),axis(1)])
        state.clear()
        state.feed([key(pygame.K_SPACE,repeat=True),axis(.9)])
        self.assertFalse(state.consume().held)
        state.feed([key(pygame.K_SPACE,False),button(pygame.CONTROLLER_BUTTON_A,False),axis(0)])
        state.feed([button(pygame.CONTROLLER_BUTTON_A)])
        self.assertEqual(state.consume().pressed,{"jump"})

    def test_round_trip_profiles_and_conflicts(self):
        settings = ControlSettings(BINDINGS,"classic",self.path)
        settings.data["keys"]["jump"] = ["k"]
        settings.data["buttons"]["jump"] = "X"
        settings.save(settings.data)
        loaded = ControlSettings(BINDINGS,"classic",self.path)
        self.assertEqual(loaded.data,settings.data)
        wrong = ControlSettings(BINDINGS,"precision",self.path)
        self.assertTrue(wrong.warning)
        with self.assertRaises(ValueError):
            wrong.save(wrong.data)
        self.assertEqual(ControlSettings(BINDINGS,"classic",self.path).data,loaded.data)

    def test_bad_bindings_reserved_aliases_buttons_and_deadzone(self):
        for field,action,value in (("keys","jump",["f3"]),("keys","jump",["d"]),
                                   ("keys","jump",[]),("keys","jump",["not-a-key"]),
                                   ("buttons","jump","Start"),("buttons","jump","DPAD_UP")):
            data = defaults(BINDINGS)
            data[field][action] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(data,BINDINGS)
        for dz in (float("nan"),True,.19,.71,"0.35"):
            data = defaults(BINDINGS)
            data["deadzone"] = dz
            with self.assertRaises(ValueError):
                validate(data,BINDINGS)

    def test_corrupt_or_unrelated_file_preserved(self):
        for content in ('{bad',json.dumps({"version":1,"tiles":[]}),json.dumps({"format":"platform2d.controls","version":2,"profile":"classic"})):
            self.path.write_text(content)
            settings = ControlSettings(BINDINGS,"classic",self.path)
            self.assertTrue(settings.warning)
            self.assertEqual(settings.data,defaults(BINDINGS))
            with self.assertRaises(ValueError):
                settings.save(settings.data)
            self.assertEqual(self.path.read_text(),content)

    def test_failed_write_preserves_previous_file_and_active_controls(self):
        settings = ControlSettings(BINDINGS,"classic",self.path)
        settings.save(settings.data)
        original = self.path.read_bytes()
        candidate = defaults(BINDINGS)
        candidate["keys"]["jump"] = ["k"]
        with patch("platform2d.core.control_settings.os.replace",side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                settings.save(candidate)
        self.assertEqual(self.path.read_bytes(),original)
        self.assertEqual(settings.data,defaults(BINDINGS))
        self.assertEqual(list(self.path.parent.glob("*.tmp")),[])

    def test_panel_capture_cancel_conflict_save_and_reload(self):
        panel = ControlsPanel(BINDINGS,"classic",self.path)
        panel.handle_event(key(pygame.K_F3))
        panel.row = panel.actions.index("jump")
        panel.handle_event(key(pygame.K_RETURN))
        panel.handle_event(key(pygame.K_d))
        self.assertTrue(panel.capture)
        self.assertIn("já pertence",panel.message)
        panel.handle_event(key(pygame.K_k))
        self.assertFalse(panel.capture)
        self.assertFalse(self.path.exists())
        panel.save()
        self.assertFalse(panel.open)
        self.assertEqual(ControlSettings(BINDINGS,"classic",self.path).data["keys"]["jump"][0],"k")
        self.assertFalse(panel.input.consume().pressed)
        panel.handle_event(key(pygame.K_k,False))
        panel.handle_event(key(pygame.K_k))
        self.assertIn("jump",panel.input.consume().pressed)
        panel.toggle()
        panel.restore()
        panel.handle_event(key(pygame.K_ESCAPE))
        self.assertEqual(panel.settings.data["keys"]["jump"][0],"k")
        panel.close()

    def test_pad_capture_requires_active_device(self):
        panel = ControlsPanel(BINDINGS)
        panel.input.attach(71)
        panel.toggle()
        panel.row,panel.column = panel.actions.index("jump"),2
        panel.begin_capture()
        panel.handle_event(button(pygame.CONTROLLER_BUTTON_X,instance=99))
        self.assertTrue(panel.capture)
        panel.handle_event(button(pygame.CONTROLLER_BUTTON_X))
        self.assertEqual(panel.draft["buttons"]["jump"],"X")
        panel.save()
        self.assertFalse(panel.input.consume().held)
        panel.close()

    def test_game_modal_freezes_world_and_escape_does_not_quit(self):
        class Scene:
            paused = False
            def __init__(self): self.updates = 0
            def update(self,dt,actions): self.updates += 1
            def draw(self,surface,alpha): surface.fill((0,0,0))
        scene = Scene()
        game = Game(scene,BINDINGS,muted=True)
        with patch("pygame.event.get",side_effect=[[key(pygame.K_F3)],[],[],[key(pygame.K_ESCAPE)],[],[],[]]):
            game.run(max_frames=7)
        self.assertFalse(game.controls.open)
        self.assertGreater(scene.updates,0)

    def test_editor_menu_freezes_and_reuses_preferences_without_touching_map(self):
        profiles = editor_profiles()
        classic = profiles["classic"]
        editor = LevelEditor(classic["factory"],classic["bindings"],template_document("classic"),profiles=profiles,controls_dir=self.path.parent)
        before = editor.document.snapshot()
        editor.start_preview()
        position = editor.preview.player.body.x,editor.preview.player.body.y
        editor.handle_event(key(pygame.K_F3))
        editor.handle_event(key(pygame.K_d))
        editor.update(.2)
        self.assertEqual((editor.preview.player.body.x,editor.preview.player.body.y),position)
        editor.controls.draft["keys"]["jump"] = ["k"]
        editor.controls.save()
        editor.stop_preview()
        editor.start_preview()
        self.assertEqual(editor.controls.settings.data["keys"]["jump"],["k"])
        self.assertEqual(editor.document.snapshot(),before)
        editor.stop_preview()


class DeviceTests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_hotplug_uses_instance_ids_and_switches_to_remaining_device(self):
        class Device:
            name = "Virtual test pad"
            def __init__(self,index): self.id,self.closed = 70+index,False
            def as_joystick(self): return self
            def get_instance_id(self): return self.id
            def quit(self): self.closed = True
        class Backend:
            def init(self): pass
            def set_eventstate(self,value): pass
            def get_count(self): return 1
            def is_controller(self,index): return index < 2
            Controller = Device
        state = Input(BINDINGS,{"jump":pygame.CONTROLLER_BUTTON_A})
        pads = Gamepads(state,Backend())
        self.assertEqual(state.device,70)
        pads.feed(pygame.event.Event(pygame.CONTROLLERDEVICEADDED,device_index=1))
        state.feed([button(pygame.CONTROLLER_BUTTON_A,instance=70)])
        state.consume()
        first = pads.devices[70]
        pads.feed(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED,instance_id=70))
        self.assertTrue(first.closed)
        self.assertEqual(state.device,71)
        self.assertEqual(state.consume().released,{"jump"})
        pads.close()
        self.assertIsNone(state.device)

    def test_controller_failure_keeps_keyboard_usable(self):
        class Broken:
            def init(self): raise pygame.error("unavailable")
        state = Input(BINDINGS)
        pads = Gamepads(state,Broken())
        state.feed([key(pygame.K_SPACE)])
        self.assertEqual(state.consume().pressed,{"jump"})
        self.assertIn("indisponível",pads.name)
        pads.close()
