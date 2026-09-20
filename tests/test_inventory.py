import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ['SDL_VIDEODRIVER'] = os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from platform2d.gameplay.inventory import Inventory,ItemDefinition,upgraded_weapon
from platform2d.gameplay.combat import Health
from platform2d.gameplay.projectiles import WeaponSpec
from platform2d.core.control_settings import ControlSettings,defaults,expand_actions
from platform2d.core.input import Actions
from platform2d.tools.editor_model import MapDocument
from examples.ranged.inventory_level import definition
from examples.ranged.scene import RangedScene


class InventoryTests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_capacity_and_take_are_atomic(self):
        inv=Inventory()
        self.assertTrue(inv.add('medkit',2))
        self.assertFalse(inv.add('medkit',2))
        self.assertFalse(inv.take('medkit',3))
        self.assertEqual(inv.count('medkit'),2)
        self.assertTrue(inv.take('medkit',2))
        self.assertEqual(inv.snapshot(),{})

    def test_invalid_requests_do_not_mutate(self):
        inv=Inventory()
        for item,qty in [('unknown',1),('power',True),('power',0),('power',-1),('power',1.5)]:
            for method in (inv.add,inv.take):
                with self.assertRaises(ValueError): method(item,qty)
        self.assertEqual(inv.snapshot(),{})

    def test_catalog_and_snapshot_are_protected(self):
        with self.assertRaises(ValueError): Inventory([ItemDefinition('x','X',1)]*2)
        with self.assertRaises(ValueError): ItemDefinition('x','X',True)
        inv=Inventory(); inv.add('power')
        inv.snapshot()['power']=99
        self.assertEqual(inv.count('power'),1)
        with self.assertRaises(TypeError): inv.catalog['x']=ItemDefinition('x','X',1)

    def test_modifiers_derive_from_original_without_accumulating(self):
        inv=Inventory(); inv.add('power',3); inv.add('rapid',2)
        base=WeaponSpec()
        first=upgraded_weapon(base,inv)
        self.assertEqual(first,upgraded_weapon(base,inv))
        self.assertEqual(first.damage,4)
        self.assertAlmostEqual(first.cooldown,.24*.64)
        self.assertEqual(base.damage,1)
        capped=upgraded_weapon(WeaponSpec(damage=100,cooldown=.02),inv)
        self.assertEqual((capped.damage,capped.cooldown),(100,.02))

    def test_healing_clamps_and_preserves_immunity(self):
        hp=Health(5,.8)
        self.assertFalse(hp.heal(2))
        hp.hit(1); self.assertTrue(hp.heal(2))
        self.assertEqual((hp.remaining,hp.immune_left),(5,.8))
        hp.update(1); hp.hit(5)
        self.assertFalse(hp.heal(2))
        for amount in (0,-1,True,1.5):
            with self.assertRaises(ValueError): hp.heal(amount)

    def test_additive_control_migration_preserves_remaps_and_file(self):
        bindings={'shoot':['k','x'],'use_item':['h']}
        old=defaults({'shoot':['h']}); old['buttons']['shoot']='Y'
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'keys.json'
            path.write_text(json.dumps(dict(format='platform2d.controls',version=1,profile='ranged',controls=old)))
            before=path.read_bytes()
            settings=ControlSettings(bindings,'ranged',path)
            self.assertFalse(settings.warning)
            self.assertEqual(settings.data['keys'],{'shoot':['h'],'use_item':['f4']})
            self.assertIsNone(settings.data['buttons']['use_item'])
            self.assertEqual(path.read_bytes(),before)
            settings.save(settings.data)
            self.assertEqual(ControlSettings(bindings,'ranged',path).data,settings.data)

    def test_invalid_old_preferences_are_not_migrated(self):
        old=defaults({'shoot':['h']}); old['buttons']={}
        with self.assertRaises(ValueError): expand_actions(old,{'shoot':['k'],'use_item':['h']})


class InventorySceneTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        settings=json.loads(Path('examples/ranged/settings.json').read_text())
        self.scene=RangedScene(MapDocument(definition()).playable(),settings)

    def tearDown(self):
        pygame.quit()

    def collect(self,item):
        obj=next(o for o in self.scene.pickups if o['item']==item)
        self.scene.player.respawn((obj['x'],obj['y']))
        self.scene.collect_items(Actions())
        return obj

    def test_pickup_once_and_respawn_retains_but_reset_clears(self):
        s=self.scene; obj=self.collect('power')
        s.collect_items(Actions())
        s.respawn()
        self.assertEqual(s.inventory.count('power'),1)
        self.assertIn(obj['id'],s.collected_items)
        self.assertEqual(s.weapon.spec.damage,2)
        s.reset()
        self.assertFalse(s.collected_items)
        self.assertEqual(s.inventory.snapshot(),{})
        self.assertEqual(s.weapon.spec,s.spec)

    def test_full_stack_stays_in_world_then_can_be_collected(self):
        s=self.scene; s.inventory.add('medkit',3)
        obj=self.collect('medkit')
        self.assertNotIn(obj['id'],s.collected_items)
        s.inventory.take('medkit')
        s.collect_items(Actions())
        self.assertIn(obj['id'],s.collected_items)
        self.assertEqual(s.inventory.count('medkit'),3)

    def test_medkit_is_not_wasted_and_requires_press(self):
        s=self.scene; self.collect('medkit')
        use=Actions(pressed=frozenset({'use_item'}))
        s.collect_items(use)
        self.assertEqual(s.inventory.count('medkit'),1)
        s.health.hit(3)
        s.collect_items(Actions(held=frozenset({'use_item'})))
        self.assertEqual(s.health.remaining,2)
        s.collect_items(use)
        self.assertEqual((s.health.remaining,s.inventory.count('medkit')),(4,0))
        s.collect_items(use)
        self.assertEqual(s.health.remaining,4)

    def test_pause_prevents_collection_and_consumption(self):
        s=self.scene; s.player.respawn((144,482)); s.inventory.add('medkit'); s.health.hit(2)
        s.update(1/60,Actions(pressed=frozenset({'pause','use_item'})))
        self.assertEqual(s.inventory.snapshot(),{'medkit':1})
        self.assertEqual(s.health.remaining,3)

    def test_old_shots_keep_damage_new_shots_use_upgrade(self):
        s=self.scene
        s.weapon.fire(s.projectiles,(70,490),(1,0),'player','player')
        old=s.projectiles.items[0]; remaining=s.weapon.remaining
        self.collect('power')
        self.assertEqual(old.spec.damage,1)
        self.assertEqual(s.weapon.remaining,remaining)
        s.weapon.reset()
        s.weapon.fire(s.projectiles,(70,490),(1,0),'player','player')
        self.assertEqual(s.projectiles.items[-1].spec.damage,2)

    def test_hazard_death_precedes_pickup(self):
        s=self.scene
        s.level.objects.append(dict(id='danger',type='hazard',x=144,y=482,w=24,h=30))
        s.player.respawn((144,482)); s.update(1/60,Actions())
        self.assertEqual(s.deaths,1)
        self.assertFalse(s.collected_items)

    def test_pickup_edit_history_and_roundtrip(self):
        doc=MapDocument(definition()); index=len(doc.data['objects'])-1
        before=doc.snapshot()
        doc.update_object(index,item='medkit',quantity=3); doc.commit()
        after=doc.snapshot(); doc.undo(); self.assertEqual(doc.snapshot(),before)
        doc.redo(); self.assertEqual(doc.snapshot(),after)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'items.json'; doc.save(path)
            self.assertEqual(MapDocument.load(path).snapshot(),after)

    def test_invalid_pickup_edits_are_transactional(self):
        doc=MapDocument(definition()); index=len(doc.data['objects'])-1; before=doc.snapshot()
        for change in ({'item':'missing'},{'quantity':True},{'quantity':0},{'quantity':4},{'quantity':1.5}):
            with self.assertRaises(ValueError): doc.update_object(index,**change)
            self.assertEqual(doc.snapshot(),before)

    def test_blocked_pickup_is_reported(self):
        doc=MapDocument(definition()); doc.data['objects'][-1].update(x=416,y=480)
        self.assertTrue(any(i.severity=='error' and 'bloqueado' in i.message for i in doc.validate()))
