import unittest

from platform2d.physics.body import Box
from platform2d.physics.collision import Collider
from platform2d.gameplay.projectiles import ProjectileSystem,Weapon,WeaponSpec,Target


class ProjectileTests(unittest.TestCase):
    def shot(self,system=None,**spec):
        system = system or ProjectileSystem()
        projectile = system.spawn((0,0),(1,0),"player","blue",WeaponSpec(**spec))
        return system,projectile

    def test_fast_shot_hits_one_pixel_wall_and_never_reaches_target(self):
        system,p = self.shot(speed=10000)
        impacts = system.update(.1,[Collider(Box(100,-10,1,20))],[Target("foe","red",Box(120,-10,20,20))])
        self.assertEqual(len(impacts),1)
        self.assertIsNone(impacts[0].target_id)
        self.assertAlmostEqual(impacts[0].point[0],95)
        self.assertFalse(system.items)

    def test_nearest_target_wins_independent_of_target_order(self):
        for reversed_order in (False,True):
            system,p = self.shot(speed=1000)
            targets = [Target("near","red",Box(30,-10,10,20)),Target("far","red",Box(60,-10,10,20))]
            impacts = system.update(.1,targets=targets[::-1] if reversed_order else targets)
            self.assertEqual([i.target_id for i in impacts],["near"])
            self.assertFalse(system.update(.1,targets=targets))

    def test_wall_wins_exact_tie_with_target(self):
        system,p = self.shot(speed=1000)
        box = Box(30,-10,10,20)
        self.assertIsNone(system.update(.1,[Collider(box)],[Target("foe","red",box)])[0].target_id)

    def test_owner_and_same_team_are_ignored(self):
        system,p = self.shot(speed=1000)
        targets = [Target("player","red",Box(5,-10,10,20)),Target("ally","blue",Box(20,-10,10,20)),Target("foe","red",Box(60,-10,10,20))]
        self.assertEqual(system.update(.1,targets=targets)[0].target_id,"foe")

    def test_lifetime_clips_travel_before_testing_impacts(self):
        system,p = self.shot(speed=100,lifetime=.1)
        impacts = system.update(1,targets=[Target("far","red",Box(20,-10,10,20))])
        self.assertFalse(impacts)
        self.assertFalse(system.items)
        self.assertEqual(p.x,10)

    def test_contact_at_lifetime_endpoint_counts(self):
        system,p = self.shot(speed=100,lifetime=.1)
        self.assertEqual(system.update(1,targets=[Target("edge","red",Box(15,-10,10,20))])[0].target_id,"edge")

    def test_swept_relative_motion_catches_target_crossing_between_frames(self):
        system,p = self.shot(speed=100)
        target = Target("crossing","red",Box(40,80,10,10),Box(40,-100,10,10))
        impacts = system.update(1,targets=[target])
        self.assertEqual(impacts[0].target_id,"crossing")
        self.assertGreater(impacts[0].point[0],35)
        self.assertLess(impacts[0].point[0],55)

    def test_moving_target_cannot_hit_after_projectile_expired(self):
        system,p = self.shot(speed=1,lifetime=.1)
        target = Target("late","red",Box(0,-1,10,2),Box(0,99,10,2))
        self.assertFalse(system.update(1,targets=[target]))

    def test_projectiles_pass_through_top_only_platforms_and_ramps(self):
        system,p = self.shot(speed=1000)
        colliders = [Collider(Box(20,-10,10,20),True),Collider(Box(40,-10,32,32),True,-1)]
        self.assertFalse(system.update(.1,colliders))
        self.assertEqual(p.x,100)

    def test_diagonal_direction_normalized(self):
        system = ProjectileSystem()
        p = system.spawn((0,0),(3,4),"p","team",WeaponSpec(speed=100))
        system.update(.1)
        self.assertEqual((p.x,p.y),(6,8))

    def test_projectile_size_included_in_sweep(self):
        system,p = self.shot(speed=1000,height=8)
        self.assertEqual(system.update(.1,targets=[Target("edge","red",Box(50,3,10,20))])[0].target_id,"edge")

    def test_zero_step_and_freeze_do_not_advance_simulation(self):
        system,p = self.shot(speed=100)
        system.update(.1)
        remaining = p.remaining
        system.freeze()
        self.assertEqual(p.interpolated(0),p.interpolated(1))
        self.assertFalse(system.update(0))
        self.assertEqual(p.remaining,remaining)

    def test_weapon_cooldown_and_capacity_do_not_queue_shots(self):
        system = ProjectileSystem(1)
        weapon = Weapon(WeaponSpec(cooldown=.25))
        self.assertIsNotNone(weapon.fire(system,(0,0),(1,0),"p","team"))
        self.assertIsNone(weapon.fire(system,(0,0),(1,0),"p","team"))
        weapon.update(.3)
        self.assertIsNone(weapon.fire(system,(0,0),(1,0),"p","team"))
        self.assertEqual(weapon.remaining,0)
        system.clear()
        self.assertIsNotNone(weapon.fire(system,(0,0),(1,0),"p","team"))
        weapon.reset()
        self.assertEqual(weapon.remaining,0)

    def test_target_generator_can_be_used_by_more_than_one_projectile(self):
        system,p = self.shot(speed=1000)
        self.shot(system,speed=1000)
        hits = system.update(.1,targets=(t for t in [Target("foe","red",Box(50,-10,10,20))]))
        self.assertEqual(len(hits),2)
        self.assertNotEqual(hits[0].projectile_id,hits[1].projectile_id)

    def test_damage_reported_not_applied_by_the_projectile_system(self):
        system,p = self.shot(speed=1000,damage=3)
        target = Target("foe","red",Box(50,-10,10,20))
        impact = system.update(.1,targets=[target])[0]
        self.assertEqual((impact.damage,impact.owner,impact.team),(3,"player","blue"))
        self.assertEqual(target.box,Box(50,-10,10,20))

    def test_invalid_specs_steps_and_directions_rejected(self):
        for config in ({"speed":float("nan")},{"speed":10**1000},{"speed":True},{"damage":1.5},{"damage":0},
                       {"lifetime":0},{"cooldown":0},{"width":-1},{"height":float("inf")}):
            with self.subTest(config=config),self.assertRaises(ValueError):
                WeaponSpec(**config)
        system = ProjectileSystem()
        for dt in (-1,float("nan"),True):
            with self.assertRaises(ValueError): system.update(dt)
        with self.assertRaises(ValueError): system.spawn((0,0),(0,0),"p","team",WeaponSpec())
        with self.assertRaises(ValueError): ProjectileSystem(0)
