import json
import os
from pathlib import Path
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from platform2d.core.input import Actions, Input
from platform2d.actors.character import Character
from platform2d.actors.controller import Movement
from platform2d.physics.body import Body, Box
from platform2d.physics.collision import Collider, move
from platform2d.world.camera import Camera
from platform2d.world.tilemap import TileMap
from platform2d.rendering.animation import Clip, SpriteView, slice_sheet

DT = 1/60
ROOT = Path(__file__).resolve().parents[1]


def actions(*held, pressed=(), released=()):
    return Actions(frozenset(held), frozenset(pressed), frozenset(released))


class PhysicsTests(unittest.TestCase):
    def test_fast_horizontal_motion_hits_nearest_wall(self):
        b = Body(0,0,10,10,vx=30000)
        walls = [Collider(Box(200,0,2,100)), Collider(Box(60,0,2,100))]
        move(b,walls,DT)
        self.assertEqual(b.x,50)
        self.assertTrue(b.wall_right)
        self.assertEqual(b.vx,0)

    def test_fast_fall_cannot_cross_thin_floor(self):
        b = Body(0,0,10,10,vy=30000)
        move(b,[Collider(Box(-10,100,100,2))],DT)
        self.assertEqual(b.y,90)
        self.assertTrue(b.on_ground)

    def test_ceiling_and_left_wall(self):
        b = Body(30,30,10,10,vx=-1000,vy=-1000)
        move(b,[Collider(Box(0,0,20,100)),Collider(Box(20,0,100,20))],DT)
        self.assertEqual((b.x,b.y),(20,20))
        self.assertTrue(b.wall_left and b.hit_ceiling)

    def test_one_way_passes_up_and_lands_down(self):
        platform = [Collider(Box(0,100,100,8),True)]
        b = Body(10,120,10,10,vy=-300)
        move(b,platform,.2)
        self.assertEqual(b.y,60)
        b.vy = 300
        move(b,platform,.2)
        self.assertEqual(b.y,90)
        self.assertTrue(b.on_ground)

    def test_drop_does_not_ignore_solid_floor(self):
        b = Body(10,90,10,10,vy=300)
        move(b,[Collider(Box(0,100,100,8),True),Collider(Box(0,130,100,10))],.2,True)
        self.assertEqual(b.y,120)

    def test_subpixel_coordinates_and_teleport(self):
        b = Body(.1,.2,vx=1)
        move(b,[],DT)
        self.assertAlmostEqual(b.x,.1+DT)
        b.teleport(400,200)
        self.assertEqual(b.interpolated(.3),(400,200))


class MovementTests(unittest.TestCase):
    def setUp(self):
        self.floor = [Collider(Box(-1000,100,2000,32))]
        self.actor = Character(Body(0,70))
        self.actor.update(DT,actions(),self.floor)

    def test_coyote_jump_after_leaving_floor(self):
        self.actor.update(DT,actions(),[])
        self.actor.update(DT,actions("jump",pressed=("jump",)),[])
        self.assertLess(self.actor.body.vy,-300)

    def test_coyote_expires_and_no_double_jump(self):
        for _ in range(10):
            self.actor.update(DT,actions(),[])
        self.actor.update(DT,actions("jump",pressed=("jump",)),[])
        self.assertGreater(self.actor.body.vy,0)
        self.actor.respawn((0,70))
        self.actor.update(DT,actions(),self.floor)
        self.actor.update(DT,actions("jump",pressed=("jump",)),self.floor)
        previous = self.actor.body.vy
        self.actor.update(DT,actions("jump",pressed=("jump",)),self.floor)
        self.assertGreater(self.actor.body.vy,previous)

    def test_buffered_jump_fires_on_landing(self):
        self.actor.respawn((0,65))
        self.actor.body.vy = 200
        self.actor.update(DT,actions("jump",pressed=("jump",)),self.floor)
        self.actor.update(DT,actions("jump"),self.floor)
        self.assertLess(self.actor.body.vy,-300)

    def test_short_jump_is_lower_than_held_jump(self):
        def apex(release):
            a = Character(Body(0,70))
            a.update(DT,actions(),self.floor)
            a.update(DT,actions("jump",pressed=("jump",)),self.floor)
            top = a.body.y
            for i in range(40):
                a.update(DT,actions(released=("jump",)) if release and i == 0 else actions(*(() if release else ("jump",))),self.floor)
                top = min(top,a.body.y)
            return top
        self.assertGreater(apex(True),apex(False)+40)

    def test_friction_stops_and_speed_is_capped(self):
        for _ in range(120):
            self.actor.update(DT,actions("right"),self.floor)
        self.assertEqual(self.actor.body.vx,230)
        for _ in range(30):
            self.actor.update(DT,actions(),self.floor)
        self.assertEqual(self.actor.body.vx,0)

    def test_invalid_movement_settings_have_clear_errors(self):
        for settings in ({"gravity":0},{"speed":-1},{"air_control":2},
                         {"jump_cut":900},{"acceleration":float("nan")}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                Movement(**settings)

    def test_expired_buffer_does_not_jump_on_landing(self):
        self.actor.respawn((0,-200))
        self.actor.update(DT,actions("jump",pressed=("jump",)),self.floor)
        for _ in range(70):
            self.actor.update(DT,actions("jump"),self.floor)
        self.assertTrue(self.actor.body.on_ground)
        self.assertEqual(self.actor.body.vy,0)

    def test_render_rates_produce_same_simulation(self):
        positions = []
        for fps in (30,60,120):
            actor = Character(Body(0,70))
            accumulator = 0
            for _ in range(fps):
                accumulator += 1/fps
                while accumulator >= DT:
                    actor.update(DT,actions("right"),self.floor)
                    accumulator -= DT
            positions.append((actor.body.x,actor.body.y,actor.body.vx))
        self.assertEqual(positions[0],positions[1])
        self.assertEqual(positions[1],positions[2])


class InputTests(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def tearDown(self):
        pygame.quit()

    def test_short_tap_survives_until_simulation_and_is_consumed_once(self):
        state = Input({"jump":["space"]})
        state.feed([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE),
                    pygame.event.Event(pygame.KEYUP,key=pygame.K_SPACE)])
        state.feed([])
        first,second = state.consume(),state.consume()
        self.assertIn("jump",first.pressed)
        self.assertIn("jump",first.released)
        self.assertNotIn("jump",second.pressed)

    def test_multiple_bindings_and_focus_loss(self):
        state = Input({"jump":["space","z"]})
        state.feed([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE),pygame.event.Event(pygame.KEYDOWN,key=pygame.K_z)])
        state.consume()
        state.feed([pygame.event.Event(pygame.KEYUP,key=pygame.K_SPACE)])
        self.assertIn("jump",state.consume().held)
        state.feed([pygame.event.Event(pygame.WINDOWFOCUSLOST)])
        self.assertIn("jump",state.consume().released)


class WorldTests(unittest.TestCase):
    def test_map_validation(self):
        valid = {"version":1,"tiles":["...","###"],"objects":[{"id":"s","type":"spawn","x":0,"y":0}]}
        self.assertEqual(TileMap(valid).width,96)
        for changes in ({"version":2},{"tiles":["..","..."]},{"tiles":["?##"]},
                        {"objects":[]},{"tile_size":0},{"objects":valid["objects"]*2}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                TileMap({**valid,**changes})

    def test_camera_bounds_and_small_world(self):
        camera = Camera((960,540),(2400,800))
        camera.follow(Body(2400,800),DT,snap=True)
        self.assertEqual((camera.x,camera.y),(1440,260))
        small = Camera((960,540),(100,100))
        small.follow(Body(100,100),DT,snap=True)
        self.assertEqual((small.x,small.y),(0,0))

    def test_sheet_animation_does_not_change_body(self):
        frames = slice_sheet(pygame.Surface((64,40)),(32,40))
        view = SpriteView(frames,{"idle":Clip((0,1),10)})
        view.update("idle",.15)
        view.draw(pygame.Surface((100,100)),(0,0),-1)
        self.assertEqual(len(frames),2)


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def scene(self):
        from examples.classic.scene import ClassicScene
        level = TileMap.load(ROOT / "examples/classic/assets/station.json")
        settings = json.loads((ROOT / "examples/classic/settings.json").read_text())
        return ClassicScene(level,settings)

    def test_checkpoint_death_retains_crystals_and_reset_clears(self):
        scene = self.scene()
        coin = next(o for o in scene.level.objects if o["type"] == "coin")
        scene.player.respawn((coin["x"],coin["y"]))
        scene.update(DT,actions())
        self.assertEqual(len(scene.collected),1)
        cp = next(o for o in scene.level.objects if o["type"] == "checkpoint")
        scene.player.respawn((cp["x"],cp["y"]))
        scene.update(DT,actions())
        scene.player.body.y = scene.level.height+200
        scene.update(DT,actions())
        self.assertEqual(scene.deaths,1)
        self.assertEqual(scene.respawn_point,(cp["x"],cp["y"]))
        self.assertEqual(len(scene.collected),1)
        scene.update(DT,actions(pressed=("reset",)))
        self.assertEqual(scene.collected,set())
        self.assertIsNone(scene.active_checkpoint)

    def test_pause_step_and_goal(self):
        scene = self.scene()
        scene.update(DT,actions(pressed=("pause",)))
        scene.update(DT,actions("right"))
        self.assertEqual(scene.player.body.x,80)
        scene.update(DT,actions("right",pressed=("step",)))
        self.assertGreater(scene.player.body.x,80)
        scene.update(DT,actions(pressed=("pause",)))
        goal = next(o for o in scene.level.objects if o["type"] == "goal")
        scene.player.respawn((goal["x"],goal["y"]))
        scene.update(DT,actions())
        self.assertFalse(scene.won)
        scene.collected = {o["id"] for o in scene.level.objects if o["type"] == "coin"}
        scene.update(DT,actions())
        self.assertTrue(scene.won)

    def test_render_with_debug(self):
        scene = self.scene()
        scene.debug = True
        scene.update(DT,actions())
        scene.draw(pygame.Surface((960,540)),.5)


if __name__ == "__main__":
    unittest.main()
