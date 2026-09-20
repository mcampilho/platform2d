import json
import os
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import capture,restore,validate
from examples.ranged.scene import RangedScene
from platform2d.tools.editor_model import MapDocument
from platform2d.core.input import Actions
from platform2d.gameplay.inventory import CATALOG


class VariedCampaignTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.name,self.ids,self.docs=load_campaign(Path('examples/campaign/assets/expedition.json'))
        self.settings=json.loads(Path('examples/ranged/settings.json').read_text())

    def tearDown(self): pygame.quit()

    def scene(self,index): return RangedScene(self.docs[index].playable(),self.settings)

    def test_collection_exit_requires_all_crystals(self):
        s=self.scene(1); s.player.respawn((910,482)); s.update(1/60,Actions())
        self.assertFalse(s.won)
        s.collected_items.update(o['id'] for o in s.coins[:-1])
        s.update(1/60,Actions()); self.assertFalse(s.won)
        s.collected_items.add(s.coins[-1]['id']); s.update(1/60,Actions())
        self.assertTrue(s.won)

    def test_full_inventory_never_blocks_mission_crystals(self):
        s=self.scene(1)
        for item in CATALOG.values(): s.inventory.add(item.id,item.limit)
        before=s.inventory.snapshot()
        for coin in s.coins:
            s.player.respawn((coin['x'],coin['y'])); s.collect_items(Actions()); s.collect_items(Actions())
        self.assertEqual(s.inventory.snapshot(),before)
        self.assertEqual(len(s.collected_items),len(s.coins))
        self.assertTrue(s.objectives_ready)

    def test_collection_room_ignores_fire_but_keeps_upgrades(self):
        s=self.scene(1); s.inventory.add('power')
        for _ in range(100): s.update(1/60,Actions(held=frozenset({'shoot'})))
        self.assertEqual(s.shots,0); self.assertFalse(s.projectiles.items)
        self.assertEqual(s.inventory.count('power'),1)

    def test_mixed_room_needs_both_sets(self):
        s=self.scene(3); s.destroyed.update(o['id'] for o in s.objects)
        self.assertFalse(s.objectives_ready)
        s.collected_items.update(o['id'] for o in s.coins)
        self.assertTrue(s.objectives_ready)
        s.destroyed.clear(); self.assertFalse(s.objectives_ready)

    def test_crystals_survive_respawn_but_not_reset(self):
        s=self.scene(2); coin=s.coins[0]
        s.player.respawn((coin['x'],coin['y'])); s.collect_items(Actions())
        s.respawn(); self.assertIn(coin['id'],s.collected_items)
        s.reset(); self.assertFalse(s.collected_items)

    def test_partial_crystal_save_roundtrip_and_invalid_victory(self):
        c=CampaignScene(self.name,self.ids,self.docs,self.settings)
        c.progress.index=1; c.progress.completed=[self.ids[0]]; c.active=self.scene(1)
        c.active.active_checkpoint='checkpoint'; c.active.collected_items.add('crystal-0')
        data=capture(c); restore(data,c)
        self.assertEqual(capture(c),data)
        self.assertEqual(c.active.player.body.y,418)
        bad=deepcopy(data); bad['stage']['won']=True
        with self.assertRaises(ValueError): restore(bad,c)
        self.assertEqual(capture(c),data)

    def test_editor_rules_history_and_file_roundtrip(self):
        doc=MapDocument(deepcopy(self.docs[1].data)); before=doc.snapshot()
        doc.update_mission(theme='ice',weapon_enabled=True)
        after=doc.snapshot(); doc.undo(); self.assertEqual(doc.snapshot(),before)
        doc.redo(); self.assertEqual(doc.snapshot(),after)
        index=doc.place('coin',3,15)
        self.assertEqual(doc.data['objects'][index]['type'],'coin')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'room.json'; doc.save(path)
            self.assertEqual(MapDocument.load(path).snapshot(),doc.snapshot())

    def test_invalid_theme_and_disarmed_targets_are_transactional(self):
        doc=MapDocument(deepcopy(self.docs[0].data)); before=doc.snapshot()
        for changes in ({'theme':'missing'},{'theme':[]},{'weapon_enabled':0},{'weapon_enabled':False}):
            with self.assertRaises(ValueError): doc.update_mission(**changes)
            self.assertEqual(doc.snapshot(),before)
        doc=MapDocument(deepcopy(self.docs[1].data)); before=doc.snapshot()
        with self.assertRaises(ValueError): doc.place('turret',3,15)
        self.assertEqual(doc.snapshot(),before)

    def test_new_campaign_cannot_accept_classic_progress(self):
        old_name,old_ids,old_docs=load_campaign(Path('examples/campaign/assets/campaign.json'))
        old=CampaignScene(old_name,old_ids,old_docs,self.settings)
        new=CampaignScene(self.name,self.ids,self.docs,self.settings)
        with self.assertRaises(ValueError): validate(capture(old),new)
