import json
import os
from pathlib import Path
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from platform2d.actors.abilities import Abilities, PrecisionController
from platform2d.actors.character import Character
from platform2d.core.input import Actions
from platform2d.physics.body import Body, Box
from platform2d.physics.collision import Collider
from platform2d.physics.platform import MovingPlatform
from platform2d.world.tilemap import TileMap

ROOT = Path(__file__).resolve().parents[1]
DT = 1/60


def inputs(*held, pressed=(), released=()):
    return Actions(frozenset(held),frozenset(pressed),frozenset(released))


def actor(x=0,y=0,**abilities):
    return Character(Body(x,y),PrecisionController(abilities=Abilities(**abilities)))


class DashTests(unittest.TestCase):
    def test_dash_distance_and_gravity_suspension(self):
        a = actor()
        for i in range(11):
            a.update(DT,inputs("right",pressed=("dash",) if i == 0 else ()),[])
        self.assertAlmostEqual(a.body.x,650*.18)
        self.assertEqual(a.body.y,0)
        self.assertFalse(a.controller.dash_ready)
        self.assertEqual(a.controller.dash_left,0)

    def test_double_jump_refills_only_after_ground_contact(self):
        a = actor(0,0,double_jump=True)
        a.update(DT,inputs(),[])
        a.controller.coyote=0
        a.update(DT,inputs('jump',pressed=('jump',)),[])
        self.assertTrue(a.controller.extra_jump_used)
        self.assertLess(a.body.vy,0)
        first=a.body.vy
        a.update(DT,inputs('jump',pressed=('jump',)),[])
        self.assertGreater(a.body.vy,first)
        floor=[Collider(Box(-100,150,400,32))]
        for _ in range(100): a.update(DT,inputs(),floor)
        self.assertTrue(a.body.on_ground)
        a.update(DT,inputs(),floor)
        self.assertFalse(a.controller.extra_jump_used)

    def test_glide_limits_fall_only_while_held(self):
        a=actor(0,0,glide=True,glide_fall_speed=90)
        a.body.vy=400
        a.update(DT,inputs('glide'),[])
        self.assertEqual(a.state,'glide')
        self.assertLessEqual(a.body.vy,90)
        a.update(DT,inputs(),[])
        self.assertNotEqual(a.state,'glide')
        self.assertGreater(a.body.vy,90)

    def test_diagonal_has_same_speed_as_horizontal(self):
        straight,diagonal = actor(),actor()
        straight.update(DT,inputs("right",pressed=("dash",)),[])
        diagonal.update(DT,inputs("right","up",pressed=("dash",)),[])
        self.assertAlmostEqual(diagonal.body.x**2+diagonal.body.y**2,straight.body.x**2)

    def test_dash_cannot_cross_thin_wall_or_ceiling(self):
        for direction,wall in (("right",Box(40,-100,1,300)),("up",Box(-100,-20,300,1))):
            a = actor()
            for i in range(11):
                a.update(DT,inputs(direction,pressed=("dash",) if i == 0 else ()),[Collider(wall)])
            if direction == "right":
                self.assertLessEqual(a.body.box.right,wall.x)
            else:
                self.assertGreaterEqual(a.body.y,wall.bottom)

    def test_no_second_air_dash_then_landing_refills(self):
        a = actor(0,0)
        floor = [Collider(Box(-500,150,1000,32))]
        for i in range(20):
            a.update(DT,inputs("right",pressed=("dash",) if i in (0,19) else ()),floor)
        self.assertFalse(a.controller.dash_ready)
        self.assertNotEqual(a.state,"dash")
        for _ in range(90):
            a.update(DT,inputs(),floor)
        self.assertTrue(a.body.on_ground)
        self.assertTrue(a.controller.dash_ready)

    def test_buffered_jump_on_landing_still_refills_dash(self):
        a = actor(0,65)
        a.body.vy = 300
        a.controller.dash_ready = False
        a.update(DT,inputs("jump",pressed=("jump",)),[Collider(Box(-100,100,500,32))])
        self.assertLess(a.body.vy,0)
        self.assertFalse(a.body.on_ground)
        self.assertTrue(a.controller.dash_ready)

    def test_damage_cancels_dash_without_free_charge_respawn_refills(self):
        a = actor()
        a.update(DT,inputs("right",pressed=("dash",)),[])
        a.knockback(-100)
        self.assertEqual(a.controller.dash_left,0)
        self.assertFalse(a.controller.dash_ready)
        a.respawn((0,0))
        self.assertTrue(a.controller.dash_ready)


class WallTests(unittest.TestCase):
    def setUp(self):
        self.wall = [Collider(Box(100,-400,32,800))]

    def test_wall_jump_points_away_and_locks_input_briefly(self):
        a = actor(76,0)
        a.update(DT,inputs("right","jump",pressed=("jump",)),self.wall)
        self.assertEqual(a.body.vx,-280)
        self.assertEqual(a.body.vy,-430)
        self.assertLess(a.body.x,76)
        a.update(DT,inputs("right","jump"),self.wall)
        self.assertEqual(a.body.vx,-280)

    def test_wall_slide_requires_pressing_into_solid_wall(self):
        a = actor(76,0)
        a.body.vy = 500
        a.update(DT,inputs("right"),self.wall)
        self.assertEqual(a.body.vy,85)
        self.assertEqual(a.state,"wall_slide")
        a.update(DT,inputs(),self.wall)
        self.assertGreater(a.body.vy,85)

    def test_one_way_side_does_not_allow_wall_jump(self):
        a = actor(76,0)
        a.update(DT,inputs("right","jump",pressed=("jump",)),[Collider(self.wall[0].box,True)])
        self.assertGreater(a.body.vy,0)
        self.assertGreater(a.body.vx,0)

    def test_wall_touch_does_not_refill_dash(self):
        a = actor(76,0)
        a.controller.dash_ready = False
        a.update(DT,inputs("right","jump",pressed=("jump",)),self.wall)
        self.assertFalse(a.controller.dash_ready)


class LadderTests(unittest.TestCase):
    def setUp(self):
        self.ladder = Box(0,100,32,200)
        self.floor = [Collider(Box(-100,300,500,32)),Collider(Box(0,100,160,32),True)]

    def test_climb_pause_exit_at_top_and_descend_through_platform(self):
        a = actor(4,270)
        a.update(DT,inputs("up"),self.floor,ladders=[self.ladder])
        self.assertEqual(a.state,"climb")
        y = a.body.y
        a.update(DT,inputs(),self.floor,ladders=[self.ladder])
        self.assertEqual(a.body.y,y)
        for _ in range(110):
            a.update(DT,inputs("up"),self.floor,ladders=[self.ladder])
        self.assertAlmostEqual(a.body.y,70)
        self.assertTrue(a.body.on_ground)
        for _ in range(5):
            a.update(DT,inputs("down"),self.floor,ladders=[self.ladder])
        self.assertGreater(a.body.y,70)
        self.assertEqual(a.state,"climb")

    def test_jump_and_dash_detach_from_ladder(self):
        for command in ("jump","dash"):
            a = actor(4,180)
            a.update(DT,inputs("up"),[],ladders=[self.ladder])
            a.update(DT,inputs("up","right",command,pressed=(command,)),[],ladders=[self.ladder])
            self.assertIsNone(a.controller.ladder)
            self.assertLess(a.body.vy,0)
            self.assertGreater(a.body.vx,0)

    def test_ladder_cannot_pass_solid_ceiling(self):
        a = actor(4,180)
        ceiling = Collider(Box(-20,140,100,20))
        for _ in range(40):
            a.update(DT,inputs("up"),[ceiling],ladders=[self.ladder])
        self.assertGreaterEqual(a.body.y,160)

    def test_ladder_does_not_refill_air_dash(self):
        a = actor(4,180)
        a.controller.dash_ready = False
        a.update(DT,inputs("up"),[],ladders=[self.ladder])
        self.assertFalse(a.controller.dash_ready)

    def test_reaching_bottom_releases_ladder_for_walking(self):
        a = actor(4,250)
        for _ in range(12):
            a.update(DT,inputs("down"),self.floor,ladders=[self.ladder])
        self.assertIsNone(a.controller.ladder)
        self.assertTrue(a.body.on_ground)
        x = a.body.x
        a.update(DT,inputs("right"),self.floor,ladders=[self.ladder])
        self.assertGreater(a.body.x,x)


class IntegrationTests(unittest.TestCase):
    def test_disabled_capabilities_match_arcade_controller(self):
        classic = Character(Body(0,70))
        precision = actor(0,70,dash=False,wall_jump=False,ladders=False)
        floor = [Collider(Box(-100,100,1000,32))]
        for i in range(120):
            action = inputs("right","jump","up",pressed=("jump","dash") if i == 4 else ())
            for a in (classic,precision):
                a.update(DT,action,floor,ladders=[Box(0,0,100,100)])
            self.assertEqual((classic.body.x,classic.body.y),(precision.body.x,precision.body.y))

    def test_moving_platform_landing_refills_and_dash_detaches(self):
        a = actor(10,65)
        a.body.vy = 300
        a.controller.dash_ready = False
        p = MovingPlatform("p",(0,100),(100,100),100,speed=60)
        p.update(DT)
        a.update(DT,inputs(),[],[p])
        self.assertTrue(a.controller.dash_ready)
        old = a.body.x
        p.update(DT)
        a.update(DT,inputs("right",pressed=("dash",)),[],[p])
        self.assertAlmostEqual(a.body.x-old,650*DT)
        self.assertGreater(a.controller.dash_left,0)
        for _ in range(3):
            p.update(DT)
            a.update(DT,inputs("right"),[],[p])
        self.assertAlmostEqual(a.body.x-old,650*DT*4)

    def test_invalid_capability_values(self):
        for config in ({"dash":"yes"},{"dash_speed":0},{"wall_lock":float("nan")}):
            with self.subTest(config=config),self.assertRaises(ValueError):
                Abilities(**config)

    def test_demo_pause_restart_and_render(self):
        pygame.init()
        try:
            from examples.precision.scene import PrecisionScene
            level = TileMap(json.loads((ROOT/"examples/precision/assets/ascent.json").read_text(encoding="utf-8")),{"ladder","beacon"})
            settings = json.loads((ROOT/"examples/precision/settings.json").read_text())
            scene = PrecisionScene(level,settings)
            scene.update(DT,inputs(pressed=("pause","debug")))
            x = scene.player.body.x
            scene.update(DT,inputs("right",pressed=("dash",)))
            self.assertEqual(scene.player.body.x,x)
            scene.update(DT,inputs("right",pressed=("step",)))
            self.assertGreater(scene.player.body.x,x)
            scene.draw(pygame.Surface((960,576)),.5)
            scene.collected.add("climb_beacon")
            scene.update(DT,inputs(pressed=("restart",)))
            self.assertIn("climb_beacon",scene.collected)
            scene.update(DT,inputs(pressed=("reset",)))
            self.assertFalse(scene.collected)
        finally:
            pygame.quit()
