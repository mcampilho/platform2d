import os
import unittest

os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame

from platform2d.rendering.guidance import ObjectiveGuide


class ObjectiveGuideTests(unittest.TestCase):
    def test_visible_points_need_no_marker(self):
        guide=ObjectiveGuide()
        self.assertIsNone(guide.marker((100,100),(0,0,200,200)))

    def test_marker_clamps_each_direction_inside_margin(self):
        guide=ObjectiveGuide(margin=20); viewport=pygame.Rect(0,0,200,120)
        for point in ((500,60),(-300,60),(100,-300),(100,400),(500,-300)):
            position,direction=guide.marker(point,viewport)
            inner=viewport.inflate(-40,-40)
            self.assertTrue(inner.left<=position[0]<=inner.right and inner.top<=position[1]<=inner.bottom)
            self.assertAlmostEqual(direction[0]**2+direction[1]**2,1)

    def test_draw_is_visual_only_and_reduced_mode_is_supported(self):
        guide=ObjectiveGuide(); surface=pygame.Surface((200,120))
        before=pygame.image.tostring(surface,'RGB')
        self.assertTrue(guide.draw(surface,(500,60),(0,0,200,120),age=1.2,reduced=True))
        self.assertNotEqual(before,pygame.image.tostring(surface,'RGB'))
