import copy
import json
import os
from pathlib import Path
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from platform2d.actors.character import Character
from platform2d.core.input import Actions
from platform2d.physics.body import Body, Box
from platform2d.physics.collision import Collider
from platform2d.physics.platform import MovingPlatform, move_with_platforms
from platform2d.world.room import RoomWorld
from platform2d.rendering.transition import FadeTransition

ROOT = Path(__file__).resolve().parents[1]
DT = 1/60


class PlatformTests(unittest.TestCase):
    def test_horizontal_rider_transport_and_interpolation(self):
        p = MovingPlatform("p",(0,100),(200,100),100,speed=60)
        b = Body(30,70,on_ground=True,vy=20)
        p.update(DT)
        move_with_platforms(b,[],[p],DT)
        self.assertAlmostEqual(b.x,31)
        self.assertEqual(b.y,70)
        self.assertTrue(b.on_ground)
        self.assertEqual(b.interpolated(.5),(30.5,70))

    def test_rider_stays_attached_up_down_and_reversal(self):
        p = MovingPlatform("p",(0,100),(0,200),100,speed=120)
        a = Character(Body(30,70,on_ground=True))
        for _ in range(140):
            p.update(DT)
            a.update(DT,Actions(),[],[p])
            self.assertAlmostEqual(a.body.y+a.body.h,p.box.y)
            self.assertTrue(a.body.on_ground)

    def test_jump_detaches_without_horizontal_drag(self):
        p = MovingPlatform("p",(0,100),(200,100),100,speed=60)
        a = Character(Body(30,70,on_ground=True))
        p.update(DT)
        a.update(DT,Actions(frozenset({"jump"}),frozenset({"jump"})),[],[p])
        self.assertEqual(a.body.x,30)
        self.assertLess(a.body.y,70)

    def test_drop_through_detaches(self):
        p = MovingPlatform("p",(0,100),(200,100),100,speed=60)
        a = Character(Body(30,70,on_ground=True))
        for i in range(6):
            p.update(DT)
            a.update(DT,Actions(frozenset({"jump","down"}),frozenset({"jump"}) if i == 0 else frozenset()),[],[p])
        self.assertEqual(a.body.x,30)
        self.assertGreater(a.body.y,70)
        self.assertFalse(a.body.on_ground)

    def test_fast_rising_platform_catches_actor_by_relative_crossing(self):
        p = MovingPlatform("p",(0,200),(0,100),100,speed=6000)
        b = Body(30,130,vy=20)
        p.update(DT)
        move_with_platforms(b,[],[p],DT)
        self.assertEqual(b.y,70)
        self.assertTrue(b.on_ground)

    def test_descending_platform_landing(self):
        p = MovingPlatform("p",(0,100),(0,200),100,speed=60)
        b = Body(30,65,vy=600)
        p.update(DT)
        move_with_platforms(b,[],[p],DT)
        self.assertEqual(b.y,71)
        self.assertTrue(b.on_ground)

    def test_platform_underside_is_not_solid(self):
        p = MovingPlatform("p",(0,100),(100,100),100)
        b = Body(30,120,vy=-600)
        p.update(DT)
        move_with_platforms(b,[],[p],.1)
        self.assertEqual(b.y,60)
        self.assertFalse(b.on_ground)

    def test_ceiling_crush_is_reported(self):
        p = MovingPlatform("p",(0,100),(0,50),100,speed=600)
        b = Body(30,70,on_ground=True,vy=20)
        ceiling = Collider(Box(0,40,100,25))
        p.update(DT)
        move_with_platforms(b,[ceiling],[p],DT)
        self.assertTrue(b.crushed)
        self.assertGreaterEqual(b.y,ceiling.box.bottom)

    def test_carried_actor_cannot_cross_static_wall(self):
        p = MovingPlatform("p",(0,100),(200,100),100,speed=600)
        b = Body(30,70,on_ground=True,vy=20)
        p.update(DT)
        move_with_platforms(b,[Collider(Box(60,0,10,100))],[p],DT)
        self.assertEqual(b.x,36)

    def test_arbitrary_time_and_invalid_path(self):
        p = MovingPlatform("p",(0,100),(100,100),100,speed=100)
        p.update(4.5)
        self.assertEqual(p.box.x,50)
        with self.assertRaises(ValueError):
            MovingPlatform("p",(0,0),(0,0),100)


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/"examples/rooms/assets/world.json").read_text(encoding="utf-8"))
        self.world = RoomWorld(copy.deepcopy(self.data))

    def test_return_preserves_objects_flags_and_platform_phase(self):
        room = self.world.current
        room.state.removed.add("low_crystal")
        room.state.flags["opened"] = True
        room.update(1)
        before = room.platforms[0].box
        self.world.enter("archive","from_atrium")
        self.world.current.update(2)
        self.world.enter("atrium","return")
        self.assertEqual(room.platforms[0].box,before)
        self.assertNotIn("low_crystal",[o["id"] for o in room.objects("coin")])
        self.assertTrue(room.state.flags["opened"])

    def test_checkpoint_can_restore_a_different_room_and_reset_clears(self):
        self.world.enter("archive","from_atrium")
        self.world.set_checkpoint((146,482))
        self.world.current.state.removed.add("far_crystal")
        self.world.enter("atrium","return")
        self.assertEqual(self.world.respawn(),(146,482))
        self.assertEqual(self.world.current_id,"archive")
        self.world.reset()
        self.assertEqual(self.world.current_id,"atrium")
        self.assertFalse(self.world.rooms["archive"].state.removed)

    def test_unknown_door_destination_rejected(self):
        door = self.data["rooms"]["atrium"]["objects"][-1]
        for field,value in (("target_room","missing"),("target_entry","missing")):
            data = copy.deepcopy(self.data)
            data["rooms"]["atrium"]["objects"][-1][field] = value
            with self.subTest(field=field),self.assertRaises(ValueError):
                RoomWorld(data)

    def test_invalid_entry_and_platform_rejected(self):
        data = copy.deepcopy(self.data)
        data["rooms"]["atrium"]["objects"][0]["y"] = 520
        with self.assertRaises(ValueError):
            RoomWorld(data)
        data = copy.deepcopy(self.data)
        platform = next(o for o in data["rooms"]["atrium"]["objects"] if o["type"] == "moving_platform")
        platform["end"] = [950,0]
        with self.assertRaises(ValueError):
            RoomWorld(data)


class TransitionTests(unittest.TestCase):
    def test_midpoint_runs_once_even_with_large_delta(self):
        fade = FadeTransition(.2)
        calls = []
        self.assertTrue(fade.start(lambda:calls.append("entered")))
        self.assertFalse(fade.start(lambda:calls.append("wrong")))
        fade.update(.1)
        self.assertEqual(calls,[])
        fade.update(.1)
        self.assertEqual(fade.opacity,255)
        self.assertEqual(calls,["entered"])
        fade.update(1)
        self.assertFalse(fade.active)
        self.assertEqual(calls,["entered"])


class SceneTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        from examples.rooms.scene import RoomsScene
        self.scene = RoomsScene(RoomWorld.load(ROOT/"examples/rooms/assets/world.json"),
                                json.loads((ROOT/"examples/rooms/settings.json").read_text()))

    def tearDown(self):
        pygame.quit()

    def test_door_requires_press_and_transition_finishes_without_bounce(self):
        scene = self.scene
        scene.player.respawn((880,482))
        scene.update(DT,Actions())
        self.assertFalse(scene.transition.active)
        scene.update(DT,Actions(frozenset({"interact"}),frozenset({"interact"})))
        for _ in range(60):
            scene.update(DT,Actions(frozenset({"interact"})))
        self.assertEqual(scene.world.current_id,"archive")
        self.assertFalse(scene.transition.active)

    def test_pause_freezes_platform_and_step_advances_once(self):
        scene = self.scene
        scene.update(DT,Actions(pressed=frozenset({"pause"})))
        p = scene.world.current.platforms[0]
        before = p.box
        scene.update(DT,Actions())
        self.assertEqual(p.box,before)
        scene.update(DT,Actions(pressed=frozenset({"step"})))
        self.assertNotEqual(p.box,before)
        after = p.box
        scene.update(DT,Actions())
        self.assertEqual(p.box,after)

    def test_both_rooms_draw_and_goal_requires_all_rooms(self):
        scene = self.scene
        scene.debug = True
        scene.draw(pygame.Surface((960,576)),.5)
        scene.enter("archive","from_atrium")
        scene.player.respawn((890,482))
        scene.update(DT,Actions())
        self.assertFalse(scene.won)
        for room in scene.world.rooms.values():
            room.state.removed.update(o["id"] for o in room.objects("coin"))
        scene.update(DT,Actions())
        self.assertTrue(scene.won)
        scene.draw(pygame.Surface((960,576)),.5)
