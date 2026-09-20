"""Check interactions which the tutorial's success-only route cannot exercise."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import pygame
from platform2d.core.input import Actions
from tutorials.first_game.scene import LessonScene


class TutorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def test_menu_and_pause_freeze_motion(self):
        scene = LessonScene()
        right = Actions(held=frozenset({'right'}))
        scene.update(1/60, right)
        self.assertEqual(scene.player.body.x, 80)
        scene.update(1/60, Actions(pressed=frozenset({'continue', 'pause'})))
        scene.update(1/60, right)
        self.assertEqual(scene.player.body.x, 80)
        scene.update(1/60, Actions(pressed=frozenset({'pause'})))
        scene.update(1/60, right)
        self.assertGreater(scene.player.body.x, 80)

    def test_exit_requires_collectible(self):
        scene = LessonScene(4)
        scene.player.body.x = 884
        scene.update(1/60, Actions())
        self.assertFalse(scene.won)
        scene.collected = True
        scene.update(1/60, Actions())
        self.assertTrue(scene.won)

    def test_enemy_damage_respawn_and_restart(self):
        scene = LessonScene(5)
        scene.player.body.x = scene.enemy.x
        scene.update(1/60, Actions())
        self.assertEqual(scene.health.remaining, 2)
        self.assertEqual(scene.player.body.x, 80)
        scene.update(1/60, Actions(pressed=frozenset({'restart'})))
        self.assertEqual(scene.health.remaining, 3)


if __name__ == '__main__':
    unittest.main()
