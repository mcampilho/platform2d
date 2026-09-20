import os,unittest
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from platform2d.gameplay.rocket import RocketMission
from platform2d.rendering.rocket import vehicle,component,FUEL,METAL

class RocketOrderTests(unittest.TestCase):
    def setUp(self):
        self.objects=[dict(type='part',id=k) for k in ('motor','tank','cockpit')]+[dict(type='fuel',id='f'+str(i)) for i in range(3)]
        self.rocket=RocketMission(self.objects)

    def test_order_is_map_order_not_alphabetic_and_no_cargo_deadlock(self):
        r=self.rocket
        self.assertFalse(r.take('cockpit')); self.assertIsNone(r.carrying)
        for ident in ('motor','tank','cockpit'):
            self.assertEqual(r.next_part,ident); self.assertTrue(r.take(ident)); self.assertTrue(r.deliver())
        self.assertTrue(r.assembled); self.assertIsNone(r.next_part)

    def test_legacy_installed_parts_preserved_and_carried_later_part_returned(self):
        r=self.rocket
        r.restore(dict(delivered=['tank'],fuelled=[],carrying='cockpit'))
        self.assertEqual(r.delivered,{'tank'}); self.assertIsNone(r.carrying)
        self.assertTrue(r.take('motor')); r.deliver()
        self.assertTrue(r.take('cockpit')); r.deliver(); self.assertTrue(r.assembled)

    def test_rendered_components_are_distinct(self):
        pictures=[]
        for kind in ('Motor','Depósito','Cockpit'):
            surface=pygame.Surface((24,24)); component(surface,(0,0,24,24),kind,METAL)
            pictures.append(pygame.image.tostring(surface,'RGB'))
        self.assertEqual(len(set(pictures)),3)

    def test_fuel_colour_rises_from_bottom_and_survives_save(self):
        r=self.rocket
        for ident in r.part_order: r.take(ident); r.deliver()
        counts=[]
        for step in range(4):
            surface=pygame.Surface((48,90)); vehicle(surface,(0,0,48,86),r)
            pixels=[(x,y) for y in range(86) for x in range(48) if surface.get_at((x,y))[:3]==FUEL]
            counts.append(len(pixels))
            if step==1: self.assertGreaterEqual(min(y for x,y in pixels),57)
            if step<3: r.take('f'+str(step)); r.deliver()
            state=r.snapshot(); r.restore(state); self.assertEqual(r.snapshot(),state)
        self.assertEqual(counts[0],0); self.assertEqual(counts,sorted(set(counts)))
        self.assertEqual(r.fuel_fraction,1)
