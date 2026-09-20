import json
import os
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from platform2d.gameplay.rocket import RocketMission
from platform2d.actors.traversal import JetpackController,LedgeController
from platform2d.actors.character import Character
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider
from platform2d.core.input import Actions
from platform2d.rendering.parallax import draw_parallax
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.factory import create_scene
from examples.campaign.progress import capture,restore
from examples.campaign.app import CampaignApp
from platform2d.tools.editor_model import MapDocument
from platform2d.core.control_settings import ControlSettings


class RocketTests(unittest.TestCase):
    def setUp(self): self.objects=[dict(id='a',type='part'),dict(id='b',type='part'),dict(id='f',type='fuel')]

    def test_assembly_precedes_fuel_and_one_cargo(self):
        r=RocketMission(self.objects)
        self.assertFalse(r.take('f')); self.assertTrue(r.take('a'))
        self.assertFalse(r.take('b')); self.assertTrue(r.deliver())
        self.assertFalse(r.take('a')); self.assertTrue(r.take('b')); r.deliver()
        self.assertTrue(r.assembled); self.assertFalse(r.ready)
        self.assertTrue(r.take('f')); r.deliver(); self.assertTrue(r.ready)
        self.assertFalse(r.deliver())

    def test_invalid_restore_is_atomic(self):
        r=RocketMission(self.objects); r.take('a'); before=r.snapshot()
        for state in [dict(delivered=[],fuelled=['f'],carrying=None),dict(delivered=['a'],fuelled=[],carrying='a'),
                      dict(delivered=['missing'],fuelled=[],carrying=None),dict(delivered=[],fuelled=[],carrying=['a'])]:
            with self.assertRaises(ValueError): r.restore(state)
            self.assertEqual(r.snapshot(),before)


class TraversalTests(unittest.TestCase):
    def test_flight_rises_while_held_then_falls(self):
        c=Character(Body(10,400),JetpackController())
        for _ in range(30): c.update(1/60,Actions(held=frozenset({'jump'})),[])
        self.assertLess(c.body.y,350)
        for _ in range(90): c.update(1/60,Actions(),[])
        self.assertGreater(c.body.y,400)

    def test_grab_climb_and_bounds_preserved_by_respawn(self):
        controller=LedgeController(); controller.bounds=(960,576)
        c=Character(Body(136,294,vy=20),controller)
        wall=[Collider(Box(160,300,96,32))]
        c.update(1/60,Actions(),wall)
        self.assertIsNotNone(controller.anchor)
        c.update(1/60,Actions(pressed=frozenset({'interact'})),wall)
        for _ in range(20): c.update(1/60,Actions(),wall)
        self.assertIsNone(controller.anchor); self.assertAlmostEqual(c.body.y,270)
        self.assertTrue(c.body.on_ground)
        c.respawn((64,480)); self.assertEqual(controller.bounds,(960,576))

    def test_drop_does_not_immediately_regrab(self):
        controller=LedgeController(); c=Character(Body(136,294,vy=20),controller)
        wall=[Collider(Box(160,300,96,32))]
        c.update(1/60,Actions(),wall)
        c.update(1/60,Actions(held=frozenset({'down'})),wall)
        self.assertIsNone(controller.anchor); self.assertGreater(c.body.vy,0)
        for _ in range(8): c.update(1/60,Actions(),wall)
        self.assertIsNone(controller.anchor)

    def test_one_way_and_blocked_headroom_are_not_grabbable(self):
        for walls in ([Collider(Box(160,300,96,32),True)],
                      [Collider(Box(160,300,96,32)),Collider(Box(160,260,96,20))]):
            c=Character(Body(136,294,vy=20),LedgeController())
            c.update(1/60,Actions(),walls)
            self.assertIsNone(c.controller.anchor)


class OdysseyTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.name,self.ids,self.docs=load_campaign(Path('examples/campaign/assets/odyssey.json'))
        self.settings=json.loads(Path('examples/ranged/settings.json').read_text())
        self.campaign=CampaignScene(self.name,self.ids,self.docs,self.settings)

    def tearDown(self): pygame.quit()

    def test_existing_four_maps_are_reused_unchanged(self):
        _,_,previous=load_campaign(Path('examples/campaign/assets/expedition.json'))
        self.assertEqual([d.snapshot() for d in self.docs[1:5]],[d.snapshot() for d in previous])

    def test_carried_and_delivered_objects_roundtrip(self):
        r=self.campaign.active.rocket
        r.take('part-0'); r.deliver(); r.take('part-1')
        data=capture(self.campaign)
        restore(data,self.campaign)
        self.assertEqual(capture(self.campaign),data)
        self.assertEqual(self.campaign.active.rocket.carrying,'part-1')
        self.assertFalse(self.campaign.active.rocket.take('part-0'))

    def test_invalid_rocket_win_does_not_replace_live_scene(self):
        data=capture(self.campaign); data['stage']['won']=True
        before=self.campaign.active
        with self.assertRaises(ValueError): restore(data,self.campaign)
        self.assertIs(self.campaign.active,before)

    def test_launch_requires_complete_rocket_and_is_pausable(self):
        s=self.campaign.active; s.player.respawn((466,455))
        s.update(1/60,Actions(pressed=frozenset({'interact'})))
        self.assertIsNone(s.launch_time)
        for ident in list(s.rocket.part_order)+list(s.rocket.fuel): s.rocket.take(ident); s.rocket.deliver()
        s.update(1/60,Actions(pressed=frozenset({'interact'})))
        self.assertEqual(s.launch_time,0)
        s.update(1/60,Actions(pressed=frozenset({'pause'})))
        for _ in range(10): s.update(1/60,Actions())
        self.assertEqual(s.launch_time,0)
        s.update(1/60,Actions(pressed=frozenset({'pause'})))
        for _ in range(151): self.campaign.update(1/60,Actions())
        self.assertTrue(s.won)
        self.campaign.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.assertEqual(self.campaign.active.level.name,'Bastião de Entrada')

    def test_delivery_triggers_autosave(self):
        app=CampaignApp(self.campaign); app.new_game()
        s=self.campaign.active; s.rocket.take('part-0'); s.player.respawn((466,455))
        app.update(1/60,Actions(pressed=frozenset({'interact'})))
        self.assertEqual(app.slot.memory['stage']['rocket']['delivered'],['part-0'])

    def test_scroll_camera_and_world_coordinates_roundtrip(self):
        self.campaign.progress.index=6; self.campaign.progress.completed=list(self.ids[:6])
        self.campaign.active=create_scene(self.docs[6],self.settings)
        s=self.campaign.active; s.active_checkpoint='checkpoint-5'
        data=capture(self.campaign); restore(data,self.campaign)
        s=self.campaign.active
        cp=next(o for o in s.level.objects if o['id']=='checkpoint-5')
        self.assertEqual(s.player.body.y,cp['y'])
        point=s.world_to_screen((s.player.body.x,s.player.body.y))
        self.assertGreaterEqual(point[1],96); self.assertLess(point[1],576)
        self.assertGreater(s.camera.y,0)

    def test_editor_extended_map_roundtrip_and_limits(self):
        doc=MapDocument(deepcopy(self.docs[5].data))
        doc.update_mission(scroll='both',traversal='ledge')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'large.json'; doc.save(path)
            self.assertEqual(MapDocument.load(path).snapshot(),doc.snapshot())
        with self.assertRaises(ValueError): doc.resize(200,36)
        with self.assertRaises(ValueError): doc.update_mission(scroll='none')

    def test_parallax_is_deterministic_and_moves_with_camera(self):
        surface=pygame.Surface((960,480))
        draw_parallax(surface,(0,0)); first=pygame.image.tostring(surface,'RGB')
        draw_parallax(surface,(0,0)); self.assertEqual(first,pygame.image.tostring(surface,'RGB'))
        draw_parallax(surface,(250,120)); self.assertNotEqual(first,pygame.image.tostring(surface,'RGB'))

    def test_campaign_interaction_has_free_gamepad_button(self):
        bindings=dict(self.settings['bindings'],interact=['e'])
        controls=ControlSettings(bindings)
        self.assertEqual(controls.data['buttons']['interact'],'B')
        self.assertEqual(controls.data['buttons']['use_item'],'Y')
