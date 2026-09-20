import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import wave

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from platform2d.audio.service import Audio,AudioControls,EFFECTS,SilentAudio
from platform2d.core.input import Actions
from platform2d.actors.character import Character
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider
from examples.editor.profiles import editor_profiles,template_document
from platform2d.tools.level_editor import LevelEditor

ROOT = Path(__file__).resolve().parents[1]


class Recorder(SilentAudio):
    def __init__(self):
        self.events = []

    def play(self,name):
        self.events.append(name)
        return True


class AudioTests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_assets_are_pcm_bounded_and_not_silent(self):
        for name in EFFECTS:
            with self.subTest(effect=name),wave.open(str(ROOT/"platform2d/audio/assets"/(name+".wav")),"rb") as clip:
                self.assertEqual((clip.getnchannels(),clip.getsampwidth(),clip.getframerate()),(1,2,22050))
                data = clip.readframes(clip.getnframes())
                values = struct.unpack("<"+"h"*(len(data)//2),data)
                self.assertGreater(max(values),1000)
                self.assertLess(max(abs(v) for v in values),5000)
                self.assertEqual(values[0],0)
                self.assertLess(len(values)/22050,1)

    def test_real_dummy_mixer_play_volume_mute_and_owned_channels(self):
        external = pygame.mixer.Channel(0)
        sound = pygame.mixer.Sound(str(ROOT/"platform2d/audio/assets/victory.wav"))
        external.play(sound,loops=-1)
        audio = Audio()
        self.assertTrue(audio.available)
        self.assertEqual(set(audio.sounds),set(EFFECTS))
        self.assertTrue(audio.play("jump"))
        self.assertFalse(audio.play("jump"))
        self.assertTrue(any(c.get_sound() == audio.sounds["jump"] for c in audio.channels))
        audio.set_volume(5)
        self.assertEqual(audio.volume,1)
        audio.set_volume(-1)
        self.assertEqual(audio.volume,0)
        audio.toggle_mute()
        self.assertFalse(audio.play("pickup"))
        self.assertFalse(any(c.get_busy() for c in audio.channels))
        self.assertTrue(external.get_busy())
        audio.close()
        self.assertTrue(external.get_busy())

    def test_pause_discards_effects_no_queue_after_unpause(self):
        audio = Audio()
        audio.play("victory")
        audio.update(.1,paused=True)
        self.assertFalse(audio.play("pickup"))
        self.assertFalse(any(c.get_busy() for c in audio.channels))
        audio.update(.1,paused=False)
        self.assertFalse(any(c.get_busy() for c in audio.channels))
        self.assertTrue(audio.play("pickup"))
        audio.close()

    def test_device_failure_and_missing_files_are_nonfatal(self):
        with patch("pygame.mixer.get_init",return_value=None),patch("pygame.mixer.init",side_effect=pygame.error("no device")):
            audio = Audio()
            self.assertFalse(audio.available)
            self.assertFalse(audio.play("jump"))
            audio.close()
        with tempfile.TemporaryDirectory() as folder:
            audio = Audio(asset_dir=Path(folder))
            self.assertFalse(audio.available)
            self.assertEqual(len(audio.errors),len(EFFECTS))
            audio.close()

    def test_controls_are_edge_triggered_and_clear_on_focus_loss(self):
        audio = Audio()
        controls = AudioControls(audio)
        for _ in range(3):
            controls.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F10))
        self.assertTrue(audio.muted)
        controls.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_F10))
        controls.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F10))
        self.assertFalse(audio.muted)
        controls.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F11))
        self.assertAlmostEqual(audio.volume,.35)
        controls.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertFalse(controls.focused)
        self.assertFalse(controls.keys)
        audio.close()

    def test_invalid_volume_and_unknown_effect(self):
        for value in (float("nan"),2,-1,True):
            with self.assertRaises(ValueError):
                Audio(value)
        audio = Audio(muted=True)
        self.assertFalse(audio.play("absent"))
        audio.close()

    def test_accepted_jump_event_not_emitted_for_failed_air_jump(self):
        actor = Character(Body(0,70))
        floor = [Collider(Box(-100,100,500,32))]
        actor.update(1/60,Actions(),floor)
        actor.update(1/60,Actions(held=frozenset({"jump"}),pressed=frozenset({"jump"})),floor)
        self.assertIn("jump",actor.controller.motion_events)
        for _ in range(12):
            actor.update(1/60,Actions(held=frozenset({"jump"})),floor)
        actor.update(1/60,Actions(held=frozenset({"jump"}),pressed=frozenset({"jump"})),floor)
        self.assertNotIn("jump",actor.controller.motion_events)

    def test_pickup_once_and_preview_exit_stops_audio(self):
        profiles = editor_profiles()
        classic = profiles["classic"]
        audio = Audio()
        e = LevelEditor(classic["factory"],classic["bindings"],template_document("classic"),profiles=profiles,audio=audio)
        e.start_preview()
        recorder = Recorder()
        e.preview.audio = recorder
        coin = next(o for o in e.preview.level.objects if o["type"] == "coin")
        e.preview.player.body.teleport(coin["x"],coin["y"])
        e.update(1/60)
        e.update(1/60)
        self.assertEqual(recorder.events.count("pickup"),1)
        audio.play("victory")
        e.stop_preview()
        self.assertFalse(any(c.get_busy() for c in audio.channels))
        audio.close()
