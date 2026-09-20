import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from platform2d.core.input import Actions
from platform2d.gameplay.campaign import CampaignProgress
from examples.campaign.scene import CampaignScene,load_campaign

MANIFEST=Path('examples/campaign/assets/campaign.json')


class ProgressTests(unittest.TestCase):
    def test_order_completion_and_reset(self):
        p=CampaignProgress(['a','b'])
        self.assertFalse(p.advance())
        self.assertTrue(p.complete()); self.assertFalse(p.complete())
        self.assertTrue(p.advance()); self.assertEqual(p.current,'b')
        self.assertTrue(p.complete()); self.assertTrue(p.finished)
        self.assertFalse(p.advance()); p.reset()
        self.assertEqual(p.current,'a'); self.assertFalse(p.finished)

    def test_invalid_ids(self):
        for ids in ([],['a','a'],[''],[None]):
            with self.assertRaises(ValueError): CampaignProgress(ids)


class CampaignTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.name,self.ids,self.docs=load_campaign(MANIFEST)
        self.settings=json.loads(Path('examples/ranged/settings.json').read_text())
        self.scene=CampaignScene(self.name,self.ids,self.docs,self.settings)

    def tearDown(self):
        pygame.quit()

    def finish(self):
        s=self.scene.active
        s.destroyed.update(o['id'] for o in s.objects)
        s.player.respawn((910,482))
        self.scene.update(1/60,Actions())

    def test_carry_inventory_restore_life_and_reset_local_ids(self):
        s=self.scene.active
        s.inventory.add('power',2); s.inventory.add('medkit')
        s.collected_items.add('power-a'); s.health.hit(2)
        self.finish()
        self.scene.update(1/60,Actions(pressed=frozenset({'continue'})))
        n=self.scene.active
        self.assertEqual(self.scene.progress.index,1)
        self.assertEqual(n.inventory.snapshot(),{'power':2,'medkit':1})
        self.assertEqual(n.weapon.spec.damage,3)
        self.assertEqual(n.health.remaining,5)
        self.assertFalse(n.collected_items); self.assertFalse(n.destroyed)
        self.assertFalse(n.projectiles.items)

    def test_continue_requires_fresh_press_after_victory(self):
        self.scene.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.assertEqual(self.scene.progress.index,0)
        self.finish()
        self.scene.update(1/60,Actions(held=frozenset({'continue'})))
        self.assertEqual(self.scene.progress.index,0)

    def test_totals_record_once_and_final_does_not_advance(self):
        for index in range(3):
            self.scene.active.shots=3; self.scene.active.deaths=1
            self.finish()
            for _ in range(4): self.scene.update(1/60,Actions())
            self.scene.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.assertTrue(self.scene.progress.finished)
        self.assertEqual(self.scene.totals['shots'],9)
        self.assertEqual(self.scene.totals['deaths'],3)
        self.assertEqual(self.scene.progress.index,2)

    def test_reset_resets_entire_campaign(self):
        self.finish(); self.scene.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.scene.active.inventory.add('power')
        self.scene.update(1/60,Actions(pressed=frozenset({'reset'})))
        self.assertEqual(self.scene.progress.index,0)
        self.assertEqual(self.scene.totals,dict(shots=0,deaths=0,elapsed=0))
        self.assertFalse(self.scene.active.inventory.snapshot())

    def test_pause_prevents_finishing_and_restart_stays_on_stage(self):
        self.finish(); self.scene.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.scene.active.inventory.add('power')
        self.scene.update(1/60,Actions(pressed=frozenset({'pause'})))
        elapsed=self.scene.active.elapsed
        self.scene.update(1/60,Actions(held=frozenset({'right','shoot'})))
        self.assertEqual(self.scene.active.elapsed,elapsed)
        self.scene.update(1/60,Actions(pressed=frozenset({'pause','restart'})))
        self.assertEqual(self.scene.progress.index,1)
        self.assertEqual(self.scene.active.inventory.count('power'),1)

    def test_document_isolation(self):
        before=[doc.snapshot() for doc in self.docs]
        self.scene.active.inventory.add('power'); self.finish()
        self.scene.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.assertEqual(before,[doc.snapshot() for doc in self.docs])

    def test_manifest_rejects_invalid_and_missing_later_map(self):
        data=json.loads(MANIFEST.read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'campaign.json'
            for field,value in [('version',True),('stages',[]),('name','')]:
                changed={**data,field:value}; path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError): load_campaign(path)
            data['stages'][0]['map']=str((MANIFEST.parent/'stage-1.json').resolve())
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError): load_campaign(path)
