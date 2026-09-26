import json,os,unittest
from pathlib import Path

os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame

from examples.campaign.factory import create_scene
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import _identity,capture,validate
from examples.campaign.willy_solution import solution_actions
from platform2d.core.input import Actions
from platform2d.tools.editor_model import MapDocument


class WillyLevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.document=MapDocument.load(Path('examples/campaign/assets/willy-keys.json'))
        cls.settings=json.loads(Path('examples/ranged/settings.json').read_text(encoding='utf-8'))

    @classmethod
    def tearDownClass(cls): pygame.quit()

    def scene(self): return create_scene(self.document,self.settings)

    def test_exact_grid_and_symbol_counts(self):
        self.assertEqual(self.document.size,(32,16))
        objects=self.document.data['objects']
        self.assertEqual(sum(o['type']=='coin' for o in objects),5)
        self.assertEqual(sum(o['type']=='crumble' for o in objects),13)
        self.assertEqual(sum(o['type']=='conveyor' for o in objects),20)
        self.assertEqual(sum(o['type']=='patrol' for o in objects),1)
        self.assertFalse([i for i in self.document.validate() if i.severity=='error'])

    def test_five_keys_unlock_exit(self):
        scene=self.scene(); self.assertFalse(scene.objectives_ready)
        scene.collected_items={o['id'] for o in scene.coins}
        self.assertTrue(scene.objectives_ready)

    def test_crumbling_floor_disappears_and_resets_after_death(self):
        scene=self.scene(); tile=next(o for o in scene.level.objects if o['id']=='crumb-14')
        scene.player.body.teleport(tile['x'],tile['y']-30); scene.player.body.on_ground=True
        scene.prepare_world(.49,Actions())
        self.assertFalse(any(c.box.x==tile['x'] and c.box.y==tile['y'] for c in scene.level.colliders))
        scene.respawn(); scene.prepare_world(0,Actions())
        self.assertTrue(any(c.box.x==tile['x'] and c.box.y==tile['y'] for c in scene.level.colliders))

    def test_conveyor_moves_player_and_patrol_is_lethal(self):
        scene=self.scene(); scene.player.body.teleport(300,258); scene.player.body.on_ground=True
        scene.update_encounters(.25,Actions()); self.assertGreater(scene.player.body.x,300)
        enemy=next(o for o in scene.level.objects if o['type']=='patrol')
        scene.player.body.teleport(enemy['x'],enemy['y']+20)
        scene.update_encounters(0,Actions()); self.assertTrue(scene.health.dead)

    def test_fixed_jump_is_about_two_tiles_high(self):
        scene=self.scene(); config=scene.player.controller.config
        height=config.jump_speed**2/(2*config.gravity)
        self.assertGreaterEqual(height,64)
        self.assertLess(height,96)
        self.assertEqual(config.jump_cut,config.jump_speed)
        descending_time=(config.jump_speed+(config.jump_speed**2-2*config.gravity*64)**.5)/config.gravity
        self.assertGreaterEqual(config.speed*descending_time,128)

    def test_normal_floor_can_be_crossed_from_below_and_landed_on(self):
        scene=self.scene(); body=scene.player.body
        body.teleport(200,450); body.on_ground=True
        minimum=body.y
        for frame in range(150):
            held=frozenset({'jump'}) if frame<45 else frozenset()
            pressed=frozenset({'jump'}) if frame==0 else frozenset()
            released=frozenset({'jump'}) if frame==45 else frozenset()
            scene.player.update(1/60,Actions(held,pressed,released),scene.level.colliders)
            minimum=min(minimum,body.y)
        self.assertLess(minimum,386)
        self.assertAlmostEqual(body.y,386)

    def test_standalone_manifest_opens_only_this_level(self):
        name,ids,documents=load_campaign(Path('examples/campaign/assets/willy.json'))
        self.assertEqual(ids,['lost-keys'])
        self.assertEqual(documents[0].data['name'],'Mina das Chaves Perdidas')

    def test_recorded_route_solves_level_without_deaths(self):
        scene=self.scene()
        for action in solution_actions(): scene.update(1/60,action)
        self.assertTrue(scene.won)
        self.assertEqual(scene.deaths,0)
        self.assertEqual({o['id'] for o in scene.coins},scene.collected_items)

    def test_previous_twelve_stage_save_is_accepted(self):
        name,ids,documents=load_campaign(Path('examples/campaign/assets/odyssey-horizons.json'))
        campaign=CampaignScene(name,ids,documents,self.settings); data=capture(campaign)
        data['identity']=_identity(campaign,[d.data for d in documents[:-1]],ids[:-1])
        self.assertEqual(validate(data,campaign)['index'],0)
