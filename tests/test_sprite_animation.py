import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
import pygame

from platform2d.rendering.sprite_animation import AnimationClip,SpriteAtlas


class SpriteAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): pygame.init()
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def atlas(self,folder):
        image=pygame.Surface((20,10),pygame.SRCALPHA)
        pygame.draw.rect(image,(255,0,0),(0,0,10,10))
        pygame.draw.rect(image,(0,0,255),(10,0,10,10))
        path=Path(folder)/'atlas.png'; pygame.image.save(image,str(path)); return path

    def test_clip_timing_loop_and_non_looping_end(self):
        with tempfile.TemporaryDirectory() as folder:
            atlas=SpriteAtlas(self.atlas(folder),(10,10),{
                'walk':AnimationClip((0,1),2),
                'once':AnimationClip((0,1),2,False)})
            self.assertEqual(atlas.frame('walk',0).get_at((5,5))[:3],(255,0,0))
            self.assertEqual(atlas.frame('walk',.5).get_at((5,5))[:3],(0,0,255))
            self.assertEqual(atlas.frame('walk',1).get_at((5,5))[:3],(255,0,0))
            self.assertEqual(atlas.frame('once',9).get_at((5,5))[:3],(0,0,255))

    def test_direction_and_anchor_change_rendered_pixels(self):
        with tempfile.TemporaryDirectory() as folder:
            image=pygame.Surface((10,10),pygame.SRCALPHA); image.set_at((1,4),(255,255,255,255))
            path=Path(folder)/'asymmetric.png'; pygame.image.save(image,str(path))
            atlas=SpriteAtlas(path,(10,10),{'idle':AnimationClip((0,))},(.25,1),True)
            right=pygame.Surface((30,20),pygame.SRCALPHA); left=right.copy()
            self.assertEqual(atlas.draw(right,(15,15),'idle',facing=1).bottom,15)
            self.assertEqual(atlas.draw(left,(15,15),'idle',facing=-1).bottom,15)
            self.assertNotEqual(pygame.image.tostring(right,'RGBA'),pygame.image.tostring(left,'RGBA'))

    def test_bad_dimensions_and_missing_frames_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=self.atlas(folder)
            with self.assertRaises(ValueError): SpriteAtlas(path,(6,10),{'idle':AnimationClip((0,))})
            with self.assertRaises(ValueError): SpriteAtlas(path,(10,10),{'idle':AnimationClip((2,))})


if __name__=='__main__': unittest.main()
