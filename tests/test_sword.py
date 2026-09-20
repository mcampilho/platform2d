import os,json,unittest
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from platform2d.gameplay.sword import Sword
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider
from platform2d.core.input import Actions
from platform2d.core.control_settings import ControlSettings
from platform2d.tools.editor_model import MapDocument
from examples.campaign.scene import load_campaign,CampaignScene
from examples.campaign.progress import capture,restore
from examples.campaign.app import CampaignApp

class SwordTests(unittest.TestCase):
    def setUp(self): self.body=Body(0,100,on_ground=True); self.front=Body(50,100); self.sword=Sword()

    def test_early_guard_parries_and_late_guard_costs_stamina(self):
        self.sword.update(.1,self.body,1,guard=True)
        self.assertEqual(self.sword.defend(self.body,1,self.front),'parry')
        self.sword.update(.2,self.body,1,guard=True); before=self.sword.stamina
        self.assertEqual(self.sword.defend(self.body,1,self.front),'block')
        self.assertAlmostEqual(self.sword.stamina,before-28)

    def test_guard_does_not_stop_rear_or_airborne_attack(self):
        self.sword.update(.1,self.body,1,guard=True)
        self.assertEqual(self.sword.defend(self.body,1,Body(-50,100)),'hit')
        self.body.on_ground=False; self.sword.update(.1,self.body,1,guard=True)
        self.assertFalse(self.sword.blocking)

    def test_insufficient_stamina_breaks_guard_and_recovers(self):
        self.sword.stamina=20; self.sword.update(.2,self.body,1,guard=True)
        self.assertEqual(self.sword.defend(self.body,1,self.front),'break')
        self.assertFalse(self.sword.blocking); self.assertGreater(self.sword.stunned,0)
        for _ in range(120): self.sword.update(1/60,self.body,1)
        self.assertGreater(self.sword.stamina,40); self.assertEqual(self.sword.stunned,0)

    def test_held_defence_eventually_exhausts(self):
        for _ in range(334): self.sword.update(1/60,self.body,1,guard=True)
        self.assertFalse(self.sword.blocking); self.assertGreater(self.sword.stunned,0)

    def test_attack_cannot_be_cancelled_into_guard(self):
        self.sword.update(.05,self.body,1,strike=True)
        self.sword.update(.05,self.body,1,guard=True)
        self.assertTrue(self.sword.attack.running); self.assertFalse(self.sword.blocking)
        self.assertFalse(self.sword.attack.active)
        self.sword.update(.1,self.body,1)
        self.assertTrue(self.sword.attack.active)
        self.assertTrue(self.sword.attack.connects('e',self.body,self.front.box))
        self.assertFalse(self.sword.attack.connects('e',self.body,self.front.box))
        self.sword.update(.15,self.body,1)
        self.sword.update(.01,self.body,1)
        self.assertFalse(self.sword.attack.active)

    def test_wall_blocks_blade_and_interruption_cancels_hit(self):
        self.sword.update(.2,self.body,1,strike=True)
        self.assertFalse(self.sword.attack.connects('e',self.body,self.front.box,[Collider(Box(30,90,8,50))]))
        self.sword.interrupt()
        self.assertFalse(self.sword.attack.connects('e',self.body,self.front.box))

class DuelTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        name,ids,docs=load_campaign(Path('examples/campaign/assets/duel.json'))
        self.settings=json.loads(Path('examples/ranged/settings.json').read_text())
        self.settings['bindings'].update(interact=['e'],attack=['j'],guard=['l'])
        self.campaign=CampaignScene(name,ids,docs,self.settings); self.scene=self.campaign.active

    def tearDown(self): pygame.quit()

    def test_no_victory_while_guardian_alive(self):
        s=self.scene; s.collected_items.add('crystal'); s.player.respawn((1200,482))
        s.update(1/60,Actions()); self.assertFalse(s.won)
        data=capture(self.campaign); data['stage']['won']=True
        with self.assertRaises(ValueError): restore(data,self.campaign)

    def test_defeat_persists_but_partial_health_resets(self):
        s=self.scene; s.guardians[0].health.hit()
        data=capture(self.campaign); restore(data,self.campaign)
        self.assertEqual(self.campaign.active.guardians[0].health.remaining,3)
        self.campaign.active.destroyed.add('guardian')
        data=capture(self.campaign); restore(data,self.campaign)
        self.assertFalse(self.campaign.active.guardians)
        self.campaign.active.reset(); self.assertEqual(len(self.campaign.active.guardians),1)

    def test_pause_freezes_enemy_player_guard_and_clock(self):
        s=self.scene; s.update(1/60,Actions()); s.paused=True
        before=(s.elapsed,s.player.body.x,s.sword.stamina,s.guardians[0].body.x,s.guardians[0].wait)
        for _ in range(60): s.update(1/60,Actions(held=frozenset({'right','guard'}),pressed=frozenset({'attack'})))
        self.assertEqual(before,(s.elapsed,s.player.body.x,s.sword.stamina,s.guardians[0].body.x,s.guardians[0].wait))

    def test_guardian_requires_duel_and_valid_health(self):
        doc=MapDocument.load('examples/campaign/assets/duel-courtyard.json')
        for change in (dict(traversal='walk'),dict(weapon_enabled=True),dict(scroll='none')):
            with self.assertRaises(ValueError): doc.update_mission(**change)
        index=next(i for i,o in enumerate(doc.data['objects']) if o['type']=='guardian')
        for hp in (0,21,True,1.5):
            with self.assertRaises(ValueError): doc.update_object(index,hp=hp)

    def test_campaign_preserves_previous_seven_maps(self):
        _,_,old=load_campaign(Path('examples/campaign/assets/odyssey.json'))
        _,_,new=load_campaign(Path('examples/campaign/assets/odyssey-duel.json'))
        self.assertEqual([d.snapshot() for d in old],[d.snapshot() for d in new[:-1]])
        self.assertEqual(len(new),8)

    def test_controls_have_distinct_keyboard_and_gamepad_bindings(self):
        controls=ControlSettings(self.settings['bindings'])
        self.assertEqual(controls.data['buttons']['attack'],'L3')
        self.assertEqual(controls.data['buttons']['guard'],'R3')

    def test_defeat_triggers_autosave(self):
        app=CampaignApp(self.campaign); app.new_game()
        s=self.campaign.active; e=s.guardians[0]
        e.health.remaining=1; e.sword.interrupt(1)
        s.player.respawn((e.body.x-55,482)); s.player.body.on_ground=True
        app.update(1/60,Actions(pressed=frozenset({'attack'})))
        for _ in range(30): app.update(1/60,Actions())
        self.assertIn('guardian',app.slot.memory['stage']['destroyed'])
