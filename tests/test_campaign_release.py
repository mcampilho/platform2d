import json
import os
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.app import CampaignApp
from examples.campaign.progress import _identity,capture,restore,validate
from platform2d.gameplay.json_slot import JsonSlot
from platform2d.core.input import Actions
from platform2d.core.game import Game
from platform2d.core.control_settings import ControlSettings
from platform2d.rendering.feedback import Feedback


def campaign():
    name,ids,docs=load_campaign(Path('examples/campaign/assets/campaign.json'))
    settings=json.loads(Path('examples/ranged/settings.json').read_text())
    settings['bindings'].update(continue_=['return'])
    settings['bindings']['continue']=settings['bindings'].pop('continue_')
    settings['bindings'].update(save_progress=['f6'],load_progress=['f9'])
    return CampaignScene(name,ids,docs,settings)


class CampaignReleaseTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.c=campaign()
        self.app=CampaignApp(self.c)

    def tearDown(self):
        pygame.quit()

    def test_checkpoint_roundtrip_keeps_progress_and_clears_transient_combat(self):
        s=self.c.active
        s.inventory.add('power'); s.inventory.add('medkit',2)
        s.destroyed.add('training'); s.collected_items.add('power-a')
        s.active_checkpoint='safe-point'; s.shots=6; s.deaths=2; s.elapsed=22.5
        payload=capture(self.c)
        other=campaign(); restore(payload,other)
        n=other.active
        self.assertEqual((n.player.body.x,n.player.body.y),(490,482))
        self.assertEqual(n.inventory.snapshot(),{'power':1,'medkit':2})
        self.assertEqual(n.weapon.spec.damage,2)
        self.assertEqual(n.health.remaining,5)
        self.assertFalse(n.projectiles.items)
        self.assertNotIn('training',n.targets)
        self.assertEqual(capture(other),payload)

    def test_won_save_resumes_summary_without_double_counting(self):
        s=self.c.active; s.destroyed.update(o['id'] for o in s.objects)
        s.player.respawn((910,482)); self.c.update(1/60,Actions())
        data=capture(self.c); restore(data,self.c)
        for _ in range(4): self.c.update(1/60,Actions())
        self.assertEqual(capture(self.c),data)
        self.c.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.assertEqual(self.c.progress.index,1)

    def test_final_save_keeps_campaign_complete(self):
        for _ in range(3):
            s=self.c.active; s.destroyed.update(o['id'] for o in s.objects)
            s.player.respawn((910,482)); self.c.update(1/60,Actions())
            self.c.update(1/60,Actions(pressed=frozenset({'continue'})))
        other=campaign(); restore(capture(self.c),other)
        self.assertTrue(other.progress.finished)
        self.assertTrue(other.active.won)

    def test_invalid_loads_preserve_live_state(self):
        original=capture(self.c)
        bad=[]
        for key,value in [('version',True),('identity','x'),('index',-1),('index',True),('inventory',{'power':4}),('inventory',{'medkit':True})]:
            data=deepcopy(original); data[key]=value; bad.append(data)
        for key,value in [('checkpoint','missing'),('destroyed',['missing']),('collected',['power-a','power-a']),('won',True),('stats',{'shots':0,'deaths':0,'elapsed':float('nan')})]:
            data=deepcopy(original); data['stage'][key]=value; bad.append(data)
        for data in bad:
            with self.assertRaises(ValueError): restore(data,self.c)
            self.assertEqual(capture(self.c),original)

    def test_changed_map_or_rules_reject_save_but_controls_do_not(self):
        data=capture(self.c)
        self.c.settings['bindings']['shoot']=['q']
        validate(data,self.c)
        self.c.documents[0].data.setdefault('properties',{})['theme']='garden'
        validate(data,self.c)
        self.c.settings['movement']['speed']+=1
        with self.assertRaises(ValueError): validate(data,self.c)
        self.c.settings['movement']['speed']-=1
        self.c.documents[0].data['name']='changed'
        with self.assertRaises(ValueError): validate(data,self.c)

    def test_legacy_save_survives_one_visual_theme_change(self):
        data=capture(self.c)
        maps=deepcopy([document.data for document in self.c.documents])
        data['identity']=_identity(self.c,maps)
        props=self.c.documents[0].data.setdefault('properties',{})
        props['theme']='garden' if props.get('theme')!='garden' else 'observatory'
        validate(data,self.c)

    def test_disk_roundtrip_and_invalid_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'save.json'; slot=JsonSlot(path)
            validator=lambda data:validate(data,self.c)
            slot.write(capture(self.c),validator)
            self.assertEqual(slot.read(validator),capture(self.c))
            path.write_text('{"format":"another-file"}')
            before=path.read_bytes()
            with self.assertRaises(ValueError): slot.write(capture(self.c),validator)
            self.assertEqual(path.read_bytes(),before)

    def test_replace_failure_keeps_previous_file_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'save.json'; slot=JsonSlot(path); validator=lambda d:validate(d,self.c)
            slot.write(capture(self.c),validator); before=path.read_bytes()
            self.c.active.shots=1
            with patch('platform2d.gameplay.json_slot.os.replace',side_effect=OSError('locked')):
                with self.assertRaises(OSError): slot.write(capture(self.c),validator)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(list(Path(folder).iterdir()),[path])

    def test_duplicate_nonfinite_oversized_and_bad_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'save.json'; slot=JsonSlot(path)
            for raw in ('{"a":1,"a":2}','{"n":NaN}','not json',' '* (slot.MAX_BYTES+1)):
                path.write_text(raw)
                with self.assertRaises(ValueError): slot.read(lambda d:validate(d,self.c))

    def test_title_and_pause_do_not_simulate_and_escape_resumes(self):
        before=capture(self.c)
        self.app.update(1,Actions(held=frozenset({'shoot','right'})))
        self.assertEqual(before,capture(self.c))
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))
        self.assertIsNone(self.app.mode)
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertEqual(self.app.mode,'pause')
        before=capture(self.c); self.app.update(1,Actions(held=frozenset({'shoot','right'})))
        self.assertEqual(before,capture(self.c))
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
        self.assertIsNone(self.app.mode)

    def test_new_game_confirmation_cancel_preserves_save(self):
        self.app.new_game(); self.c.active.inventory.add('power'); self.app.save()
        before=deepcopy(self.app.slot.memory)
        self.app.request_new()
        self.assertEqual(self.app.mode,'confirm')
        self.app.choices()[1][1]()
        self.assertEqual(self.app.slot.memory,before)
        self.assertEqual(self.c.active.inventory.count('power'),1)

    def test_focus_loss_pauses_without_restarting(self):
        self.app.new_game()
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(self.app.mode,'pause')
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        self.assertEqual(self.app.mode,'pause')

    def test_pause_action_resumes_and_debug_step_advances_once(self):
        self.app.new_game()
        toggle=Actions(pressed=frozenset({'pause'}))
        self.app.update(1/60,toggle)
        self.assertEqual(self.app.mode,'pause')
        elapsed=self.c.active.elapsed
        self.app.update(1/60,Actions(pressed=frozenset({'step'})))
        self.assertAlmostEqual(self.c.active.elapsed,elapsed+1/60)
        self.assertEqual(self.app.mode,'pause')
        self.app.update(1/60,toggle)
        self.assertIsNone(self.app.mode)

    def test_autosave_checkpoint_and_manual_save_from_pause(self):
        self.app.new_game(); s=self.c.active
        s.inventory.add('medkit'); s.player.respawn((490,482))
        self.app.update(1/60,Actions())
        self.assertEqual(self.app.slot.memory['stage']['checkpoint'],'safe-point')
        self.app.menu('pause'); s.inventory.take('medkit')
        self.app.update(1/60,Actions(pressed=frozenset({'save_progress'})))
        self.assertEqual(self.app.slot.memory['inventory'],{})

    def test_checkpoint_autosave_reuses_prepared_campaign_identity(self):
        self.app.new_game(); self.app.slot.memory=None
        with patch('examples.campaign.progress.accepted_identities',side_effect=AssertionError('slow identity rebuild')):
            self.c.active.player.respawn((490,482))
            self.app.update(1/60,Actions())
        self.assertEqual(self.app.slot.memory['stage']['checkpoint'],'safe-point')

    def test_failed_load_keeps_current_scene_and_failed_save_does_not_quit(self):
        self.app.new_game(); original=self.c.active
        self.app.slot.memory={'invalid':True}
        self.assertFalse(self.app.load()); self.assertIs(self.c.active,original)
        self.app.save_quit(); self.assertFalse(self.app.quit_requested)

    def test_mouse_options_and_reduced_effects(self):
        surface=pygame.Surface((960,576)); self.app.draw(surface,1)
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.app.buttons[2].center))
        self.assertEqual(self.app.mode,'options')
        self.app.draw(surface,1)
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.app.buttons[3].center))
        self.assertFalse(self.app.feedback.enabled)
        self.assertFalse(self.app.transitions.enabled)

    def test_campaign_moments_start_presentation_transitions(self):
        self.app.new_game(); self.assertEqual(self.app.transitions.kind,'enter')
        self.app.transitions.clear(); s=self.c.active
        s.player.respawn((490,482)); self.app.update(1/60,Actions())
        self.assertEqual(self.app.transitions.kind,'checkpoint')
        self.app.transitions.clear(); s.destroyed.update(o['id'] for o in s.objects)
        s.player.respawn((910,482)); self.app.update(1/60,Actions())
        self.assertEqual(self.app.transitions.kind,'complete')

    def test_visuals_are_bounded_and_do_not_change_game_state(self):
        feedback=Feedback()
        for _ in range(100): feedback.burst((10,10),(255,255,255))
        self.assertLessEqual(len(feedback.particles),120)
        feedback.update(1); self.assertFalse(feedback.particles)
        before=capture(self.c); self.app.new_game()
        self.app.feedback.burst((10,10),(255,255,255))
        self.app.draw(pygame.Surface((960,576)),1)
        self.assertEqual(capture(self.c),before)

    def test_game_host_routes_menu_events_and_closes(self):
        game=Game(self.app,self.c.settings['bindings'],size=(960,576),muted=True)
        events=[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN),pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)]
        with patch('pygame.event.get',return_value=events): game.run(max_frames=1)
        self.assertTrue(self.app.started)
        self.assertEqual(self.app.mode,'pause')
        self.assertFalse(self.app.quit_requested)

    def test_new_actions_preserve_old_campaign_preferences(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'controls.json'
            old_bindings={k:v for k,v in self.c.settings['bindings'].items() if k not in {'save_progress','load_progress'}}
            old=ControlSettings(old_bindings,'campaign',path)
            old.data['keys']['jump']=['g']; old.save(old.data)
            before=path.read_bytes()
            settings=ControlSettings(self.c.settings['bindings'],'campaign',path)
            self.assertFalse(settings.warning)
            self.assertEqual(settings.data['keys']['jump'],['g'])
            self.assertEqual(settings.data['keys']['save_progress'],['f6'])
            self.assertEqual(settings.data['keys']['load_progress'],['f9'])
            self.assertEqual(path.read_bytes(),before)
            buttons=[b for b in settings.data['buttons'].values() if b is not None]
            self.assertEqual(len(buttons),len(set(buttons)))
