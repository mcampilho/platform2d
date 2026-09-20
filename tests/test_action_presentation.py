"""Presentation follows combat timing without advancing simulation."""
import copy
import json
import os
from pathlib import Path
import unittest
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
from platform2d.rendering.action_pose import sword_pose,draw_actor
from platform2d.gameplay.sword import Sword
from platform2d.gameplay.combat import Health
from platform2d.core.input import Actions
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import capture


class ActionPresentationTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.surface=pygame.Surface((960,576))

    def tearDown(self): pygame.quit()

    def scene(self,manifest='duel.json'):
        name,ids,docs=load_campaign(Path('examples/campaign/assets')/manifest)
        settings=json.loads(Path('examples/ranged/settings.json').read_text(encoding='utf-8'))
        campaign=CampaignScene(name,ids,docs,settings)
        return campaign,campaign.active

    def test_pose_follows_real_attack_window(self):
        sword=Sword(); health=Health(); sword.attack.start(1)
        self.assertEqual(sword_pose(sword,health)[0],'windup')
        sword.attack.update(.17)
        self.assertEqual(sword_pose(sword,health)[0],'strike')
        sword.attack.update(.12); sword.attack.update(.01)
        self.assertEqual(sword_pose(sword,health)[0],'recover')
        sword.attack.update(.4)
        self.assertEqual(sword_pose(sword,health)[0],'idle')

    def test_damage_then_vulnerability_then_guard(self):
        sword=Sword(); health=Health(); sword.interrupt(.65); health.hit()
        self.assertEqual(sword_pose(sword,health)[0],'hurt')
        health.update(.2)
        self.assertEqual(sword_pose(sword,health)[0],'stagger')
        sword.stunned=0; sword.blocking=True
        self.assertEqual(sword_pose(sword,health)[0],'guard')

    def test_drawing_does_not_advance_combat_or_save_state(self):
        campaign,s=self.scene(); s.update(1/60,Actions())
        s.sword.attack.start(1); s.impact_fx=[((100,100),.18,'parry')]
        before=(capture(campaign),copy.deepcopy(vars(s.sword.attack)),list(s.impact_fx),s.elapsed)
        for reduced in (False,True):
            s.reduced_effects=reduced
            for alpha in (0,.5,1): s.draw(self.surface,alpha)
        self.assertEqual(before,(capture(campaign),vars(s.sword.attack),s.impact_fx,s.elapsed))

    def test_pause_freezes_impacts_and_reset_clears_them(self):
        _,s=self.scene(); s.impact_fx=[((100,100),.18,'parry')]; s.paused=True
        s.update(.1,Actions()); self.assertEqual(s.impact_fx[0][1],.18)
        s.paused=False; s.update(.2,Actions()); self.assertFalse(s.impact_fx)
        s.impact_fx=[((100,100),.18,'block')]; s.reset(); self.assertFalse(s.impact_fx)

    def test_reduced_effects_retains_distinct_action_poses(self):
        pixels=[]
        for phase in ('carry','windup','strike','recover','guard','hurt','stagger'):
            self.surface.fill('black')
            draw_actor(self.surface,(100,100),phase=phase,progress=.5,reduced=True)
            pixels.append(pygame.image.tobytes(self.surface,'RGB'))
        self.assertEqual(len(set(pixels)),len(pixels))

    def test_carried_piece_render_preserves_mission(self):
        campaign,s=self.scene('odyssey.json')
        s.rocket.carrying=s.rocket.part_order[0]
        before=copy.deepcopy(vars(s.rocket)); body=copy.deepcopy(vars(s.player.body))
        for alpha in (0,.5,1): s.draw(self.surface,alpha)
        self.assertEqual(vars(s.rocket),before)
        self.assertEqual(vars(s.player.body),body)
