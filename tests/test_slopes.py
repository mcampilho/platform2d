import os
import unittest

os.environ["SDL_VIDEODRIVER"] = os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider,move
from platform2d.physics.platform import MovingPlatform,move_with_platforms
from platform2d.actors.character import Character
from platform2d.actors.abilities import PrecisionController
from platform2d.actors.controller import Movement
from platform2d.actors.enemy import PatrolEnemy
from platform2d.core.input import Actions
from platform2d.world.tilemap import TileMap
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.reachability import ReachabilitySearch,optimistic_unreachable
from examples.slopes.level import definition

DT = 1/60


class SlopesTests(unittest.TestCase):
    def test_rejects_unsupported_ramp_shapes_and_solid_sides(self):
        for box,one_way,slope in ((Box(0,0,32,32),False,-1),(Box(0,0,64,32),True,1),
                                  (Box(0,0,32,32),True,2),(Box(0,0,0,0),True,-1)):
            with self.assertRaises(ValueError):
                Collider(box,one_way,slope)

    def test_patrol_crosses_ramps_without_treating_their_bounds_as_ledges(self):
        level = TileMap(definition())
        enemy = PatrolEnemy("guard",Body(64,482),64,800,facing=1)
        reached = 64
        for _ in range(1300):
            enemy.update(DT,Body(-2000,0),level.colliders)
            reached = max(reached,enemy.body.x)
            self.assertTrue(enemy.body.on_ground)
        self.assertGreater(reached,790)
        self.assertLess(enemy.body.x,300)

    def test_map_symbols_orientation_and_top_only(self):
        level = TileMap(definition())
        ramps = [c for c in level.colliders if c.slope]
        self.assertEqual(len(ramps),16)
        self.assertTrue(all(c.one_way for c in ramps))
        for c in ramps:
            expected = (c.box.bottom,c.box.y) if c.slope == -1 else (c.box.y,c.box.bottom)
            self.assertEqual((c.surface(c.box.x,0),c.surface(c.box.right,0)),expected)

    def test_footprint_uses_highest_point_and_clamps_endpoints(self):
        ramp = Collider(Box(32,64,32,32),True,-1)
        self.assertEqual(ramp.surface(36,24),68)
        self.assertEqual(ramp.surface(60,24),64)
        self.assertEqual(ramp.surface(-30,24),96)

    def test_fall_onto_each_orientation_with_high_speed(self):
        for slope in (-1,1):
            ramp = Collider(Box(0,100,64,64),True,slope)
            body = Body(20,0,vy=1500)
            move(body,[ramp],.2)
            self.assertTrue(body.on_ground)
            self.assertAlmostEqual(body.y+body.h,ramp.surface(body.x,body.w))
            self.assertEqual(body.vy,0)
            self.assertEqual((body.previous_x,body.previous_y),(20,0))

    def test_jump_through_from_below_then_land_on_top(self):
        ramp = Collider(Box(0,100,64,64),True,-1)
        actor = Character(Body(20,150,vy=-440))
        above = False
        for _ in range(90):
            actor.update(DT,Actions(),[ramp])
            above |= actor.body.y+actor.body.h < ramp.surface(20,24)
        self.assertTrue(above)
        self.assertTrue(actor.body.on_ground)
        self.assertAlmostEqual(actor.body.y+actor.body.h,ramp.surface(20,24))
        self.assertFalse(actor.body.hit_ceiling)

    def test_no_side_or_bottom_collision(self):
        ramp = Collider(Box(100,100,32,32),True,-1)
        body = Body(75,125,vx=300)
        move(body,[ramp],.1)
        self.assertAlmostEqual(body.x,105)
        self.assertFalse(body.on_ground or body.wall_right)

    def test_walk_both_directions_across_ramp_seams_and_flat_joins(self):
        level = TileMap(definition())
        for direction,start in (("right",64),("left",800)):
            actor = Character(Body(start,482))
            was_on_ramp = False
            for i in range(200):
                actor.update(DT,Actions(held=frozenset({direction})),level.colliders)
                b = actor.body
                self.assertTrue(b.on_ground,(direction,i,b))
                self.assertFalse(b.wall_left or b.wall_right,(direction,i,b))
                was_on_ramp |= b.y < 400
                self.assertFalse(any(b.box.overlaps(c.box) for c in level.colliders if not c.one_way))
                if (direction == "right" and b.x > 760) or (direction == "left" and b.x < 80):
                    break
            self.assertTrue(was_on_ramp)

    def test_jump_leaves_slope_without_ground_snap(self):
        ramp = Collider(Box(0,100,96,96),True,-1)
        actor = Character(Body(20,ramp.surface(20,24)-30,on_ground=True))
        actor.update(DT,Actions(held=frozenset({"jump","right"}),pressed=frozenset({"jump"})),[ramp])
        self.assertFalse(actor.body.on_ground)
        self.assertLess(actor.body.vy,0)
        self.assertLess(actor.body.y+30,ramp.surface(actor.body.x,24))

    def test_drop_through_disables_ramp_support(self):
        ramp = Collider(Box(0,100,96,96),True,-1)
        actor = Character(Body(20,ramp.surface(20,24)-30,on_ground=True))
        top = actor.body.y
        for i in range(30):
            actor.update(DT,Actions(held=frozenset({"down","jump"}),pressed=frozenset({"jump"}) if i==0 else frozenset()),[ramp])
        self.assertGreater(actor.body.y,top+30)
        self.assertFalse(actor.body.on_ground)

    def test_no_snap_across_large_drop(self):
        ramp = Collider(Box(64,200,32,32),True,-1)
        body = Body(40,70,vx=180,vy=20,on_ground=True)
        move(body,[Collider(Box(0,100,64,32)),ramp],DT)
        self.assertLess(body.y,80)

    def test_low_ceiling_stops_ascent_without_embedding(self):
        ramp = Collider(Box(0,100,128,128),True,-1)
        ceiling = Collider(Box(48,90,160,55))
        actor = Character(Body(0,ramp.surface(0,24)-30,on_ground=True))
        for _ in range(60):
            actor.update(DT,Actions(held=frozenset({"right"})),[ramp,ceiling])
            self.assertFalse(actor.body.box.overlaps(ceiling.box))
        self.assertLess(actor.body.x,48)
        self.assertTrue(actor.body.on_ground)

    def test_horizontal_dash_crosses_join_without_hitting_fill_blocks(self):
        level = TileMap(definition())
        actor = Character(Body(225,490-30,on_ground=True),PrecisionController())
        # Place the feet exactly on the actual ramp before the dash.
        ramp = next(c for c in level.colliders if c.slope == -1 and c.box.x == 224)
        actor.body.y = ramp.surface(actor.body.x,24)-30
        for i in range(9):
            actor.update(DT,Actions(held=frozenset({"right"}),pressed=frozenset({"dash"}) if i==0 else frozenset()),level.colliders)
            self.assertFalse(actor.body.wall_right)
        self.assertGreater(actor.body.x,315)
        self.assertLess(actor.body.y,400)

    def test_ramps_do_not_count_as_wall_jump_surfaces(self):
        controller = PrecisionController()
        controller.prepare([Collider(Box(24,0,32,32),True,-1)])
        self.assertEqual(controller.wall_side(Body(0,0)),0)

    def test_moving_platform_carries_up_through_ramp_without_false_crush(self):
        ramp = Collider(Box(0,100,96,96),True,-1)
        platform = MovingPlatform("lift",(0,190),(0,80),64,speed=60)
        body = Body(12,160,on_ground=True,vy=20)
        for _ in range(70):
            platform.update(DT)
            body.vy = 20
            move_with_platforms(body,[ramp],[platform],DT)
            self.assertFalse(body.crushed)
        self.assertTrue(body.on_ground)
        self.assertLess(body.y,100)

    def test_editor_support_check_uses_inclined_height(self):
        data = definition()
        ramp = next(c for c in TileMap(data).colliders if c.slope == -1)
        spawn = next(o for o in data["objects"] if o["type"] == "spawn")
        spawn.update(x=ramp.box.x,y=ramp.surface(ramp.box.x,24)-30)
        issues = MapDocument(data).validate()
        self.assertFalse([i for i in issues if "start:" in i.message],issues)

    def test_ramp_map_never_uses_flat_impossibility_proof(self):
        data = definition()
        next(o for o in data["objects"] if o["type"] == "coin").update(x=32,y=0)
        self.assertEqual(optimistic_unreachable(TileMap(data),Movement()),[])
        result = ReachabilitySearch(data,max_nodes=0).step()
        self.assertEqual(result.status,"inconclusive")

    def test_positive_solver_witness_replays_with_ramps(self):
        data = dict(version=1,tile_size=32,tiles=["............"]*6+
                    ["..../##\\....",".../####\\...","###......###","############"],
                    objects=[dict(id="start",type="spawn",x=32,y=226),dict(id="coin",type="coin",x=170,y=165),dict(id="goal",type="goal",x=320,y=198,w=32,h=58)])
        search = ReachabilitySearch(data,max_seconds=10)
        while search.result is None:
            search.step(50)
        self.assertEqual(search.result.status,"solved",search.result.issues)
        self.assertTrue(search.result.actions)
