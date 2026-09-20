import json
import os
from pathlib import Path
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from platform2d.actors.character import Character
from platform2d.actors.enemy import PatrolEnemy
from platform2d.actors.perception import can_see, segment_hits_box
from platform2d.actors.state_machine import State, StateMachine
from platform2d.core.input import Actions
from platform2d.gameplay.combat import Attack, AttackSpec, Health
from platform2d.gameplay.interaction import Interaction, choose_interaction
from platform2d.physics.body import Body, Box
from platform2d.physics.collision import Collider
from platform2d.world.tilemap import TileMap

ROOT = Path(__file__).resolve().parents[1]
DT = 1/60


class StateTests(unittest.TestCase):
    def test_hooks_order_elapsed_and_same_state_noop(self):
        log = []
        machine = StateMachine(log,{
            "a":State(enter=lambda o:o.append("enter a"),exit=lambda o:o.append("exit a")),
            "b":State(enter=lambda o:o.append("enter b"),update=lambda o,dt:o.append("update b")),
        },"a")
        machine.update(.2)
        machine.change("b")
        self.assertEqual(machine.elapsed,0)
        self.assertFalse(machine.change("b"))
        machine.update(.3)
        self.assertEqual(log,["enter a","exit a","enter b","update b"])
        self.assertEqual(machine.elapsed,.3)

    def test_unknown_state_does_not_change_current(self):
        machine = StateMachine(None,{"idle":State()},"idle")
        with self.assertRaises(ValueError):
            machine.change("missing")
        self.assertEqual(machine.current,"idle")


class PerceptionTests(unittest.TestCase):
    def test_range_facing_and_height(self):
        b = Body(0,70)
        self.assertTrue(can_see(b,Body(100,70),1,[]))
        self.assertFalse(can_see(b,Body(100,70),-1,[]))
        self.assertFalse(can_see(b,Body(300,70),1,[]))
        self.assertFalse(can_see(b,Body(0,-80),1,[]))

    def test_wall_blocks_but_one_way_does_not(self):
        wall = Box(50,0,10,200)
        self.assertFalse(can_see(Body(0,70),Body(100,70),1,[Collider(wall)]))
        self.assertTrue(can_see(Body(0,70),Body(100,70),1,[Collider(wall,True)]))

    def test_segment_vertical_and_parallel(self):
        self.assertTrue(segment_hits_box((5,-10),(5,20),Box(0,0,10,10)))
        self.assertFalse(segment_hits_box((15,-10),(15,20),Box(0,0,10,10)))


class CombatTests(unittest.TestCase):
    def test_health_immunity_death_and_restore(self):
        hp = Health(2,.5)
        self.assertTrue(hp.hit())
        self.assertFalse(hp.hit())
        hp.update(.5)
        self.assertTrue(hp.hit())
        self.assertTrue(hp.dead)
        hp.update(1)
        self.assertFalse(hp.hit())
        hp.restore()
        self.assertEqual(hp.remaining,2)

    def test_attack_windows_and_once_per_target(self):
        attack = Attack(AttackSpec(.1,.1,.2,40))
        attacker = Body(0,0)
        target = Box(30,0,24,30)
        self.assertTrue(attack.start(1))
        self.assertFalse(attack.start(1))
        attack.update(.05)
        self.assertFalse(attack.connects("a",attacker,target))
        attack.update(.07)
        self.assertTrue(attack.connects("a",attacker,target))
        self.assertFalse(attack.connects("a",attacker,target))
        self.assertTrue(attack.connects("b",attacker,target))
        attack.update(.1)
        attack.update(.02)
        self.assertFalse(attack.active)
        self.assertTrue(attack.running)
        attack.update(.2)
        self.assertFalse(attack.running)

    def test_short_window_not_skipped_and_attack_cannot_cross_wall(self):
        attack = Attack(AttackSpec(.001,.002,.2))
        attack.start(1)
        attack.update(DT)
        self.assertTrue(attack.active)
        self.assertFalse(attack.connects("a",Body(0,0),Box(40,0,24,30),[Collider(Box(28,-10,5,50))]))
        self.assertTrue(attack.connects("a",Body(0,0),Box(40,0,24,30)))

    def test_direction_and_outside_hitbox(self):
        attack = Attack()
        attack.start(-1)
        attack.update(.1)
        self.assertFalse(attack.connects("right",Body(100,0),Box(130,0,24,30)))
        self.assertTrue(attack.connects("left",Body(100,0),Box(70,0,24,30)))

    def test_knockback_is_not_overwritten_by_input(self):
        character = Character(Body(0,0))
        character.knockback(-160)
        character.update(DT,Actions(frozenset({"right"})),[])
        self.assertEqual(character.body.vx,-160)
        self.assertLess(character.body.x,0)
        character.respawn((0,0))
        self.assertEqual(character.stun_left,0)


class InteractionTests(unittest.TestCase):
    def test_priority_distance_disabled_and_stable_ties(self):
        body = Body(0,0)
        near = Interaction("near","Falar",(12,15),lambda:None)
        far = Interaction("far","Abrir",(40,15),lambda:None,priority=1)
        self.assertIs(choose_interaction(body,[near,far]),far)
        far.enabled = False
        self.assertIs(choose_interaction(body,[near,far]),near)
        near.radius = 1
        self.assertIsNone(choose_interaction(Body(100,0),[near,far]))
        other = Interaction("a","Falar",(12,15),lambda:None)
        self.assertIs(choose_interaction(body,[near,other]),other)


class EnemyTests(unittest.TestCase):
    def setUp(self):
        self.floor = [Collider(Box(-100,100,1000,32))]
        self.enemy = PatrolEnemy("guard",Body(100,70),80,200,1)

    def test_patrol_chase_last_seen_search(self):
        e = self.enemy
        e.update(DT,Body(200,70),self.floor)
        self.assertEqual(e.machine.current,"chase")
        remembered = e.last_seen
        for _ in range(40):
            e.update(DT,Body(-1000,70),self.floor)
        self.assertEqual(e.last_seen,remembered)
        self.assertEqual(e.machine.current,"search")
        for _ in range(50):
            e.update(DT,Body(-1000,70),self.floor)
        self.assertEqual(e.machine.current,"patrol")

    def test_patrol_turns_and_avoids_ledge(self):
        floor = [Collider(Box(0,100,160,32))]
        for _ in range(300):
            self.enemy.update(DT,Body(-1000,0),floor)
        self.assertLessEqual(self.enemy.body.box.right,160)
        self.assertAlmostEqual(self.enemy.body.y,70)

    def test_hurt_dead_and_no_resurrection(self):
        e = self.enemy
        self.assertTrue(e.hit(1,-1))
        self.assertEqual(e.machine.current,"hurt")
        self.assertFalse(e.hit(1,-1))
        for _ in range(20):
            e.update(DT,Body(1000,0),self.floor)
        self.assertTrue(e.hit(1,1))
        self.assertEqual(e.machine.current,"dead")
        x = e.body.x
        e.update(1,Body(150,70),self.floor)
        self.assertEqual(e.body.x,x)
        self.assertFalse(e.visible)


class SentinelSceneTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        from examples.sentinels.scene import SentinelsScene
        level = TileMap(json.loads((ROOT/"examples/sentinels/assets/outpost.json").read_text(encoding="utf-8")),{"enemy","npc","switch","gate"})
        self.scene = SentinelsScene(level,json.loads((ROOT/"examples/sentinels/settings.json").read_text()))

    def tearDown(self):
        pygame.quit()

    def test_dialogue_freezes_world_and_requires_new_presses(self):
        s = self.scene
        s.player.respawn((128,482))
        s.update(DT,Actions(pressed=frozenset({"interact"})))
        self.assertTrue(s.dialogue)
        x = s.enemies[0].body.x
        for _ in range(30):
            s.update(DT,Actions(frozenset({"interact"})))
        self.assertEqual(s.enemies[0].body.x,x)
        self.assertEqual(s.dialogue_index,0)
        for _ in range(3):
            s.update(DT,Actions(pressed=frozenset({"interact"})))
        self.assertTrue(s.briefed)
        self.assertFalse(s.dialogue)

    def test_switch_requires_briefing_and_defeated_guards(self):
        s = self.scene
        s.activate()
        self.assertFalse(s.gate_open)
        s.briefed = True
        s.activate()
        self.assertFalse(s.gate_open)
        s.defeated = {e.id for e in s.enemies}
        count = len(s.colliders)
        s.activate()
        self.assertTrue(s.gate_open)
        self.assertEqual(len(s.colliders),count-1)

    def test_respawn_retains_progress_but_full_reset_clears(self):
        s = self.scene
        s.defeated.add(s.enemies[0].id)
        s.briefed = True
        s.health.hit(3)
        s.update(DT,Actions())
        self.assertEqual(s.deaths,1)
        self.assertEqual(len(s.enemies),1)
        self.assertTrue(s.briefed)
        self.assertEqual(s.health.remaining,3)
        s.reset()
        self.assertEqual(len(s.enemies),2)
        self.assertFalse(s.briefed)

    def test_pause_and_debug_render(self):
        s = self.scene
        s.update(DT,Actions(pressed=frozenset({"pause","debug"})))
        position = s.enemies[0].body.x
        s.update(DT,Actions())
        self.assertEqual(s.enemies[0].body.x,position)
        s.draw(pygame.Surface((960,576)),.5)
