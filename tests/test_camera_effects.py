import unittest

from platform2d.rendering.camera_effects import CameraEffects


class CameraEffectsTests(unittest.TestCase):
    def test_impulse_is_bounded_interpolated_and_decays(self):
        effects=CameraEffects(amplitude=8,decay=2)
        effects.impulse(.7)
        values=[]
        for _ in range(40):
            effects.update(1/60)
            values.append(effects.interpolated(.5))
        self.assertTrue(any(abs(x)+abs(y)>0 for x,y in values))
        self.assertTrue(all(abs(x)<=8 and abs(y)<=8 for x,y in values))
        for _ in range(60): effects.update(1/60)
        self.assertEqual(effects.trauma,0)
        self.assertEqual(effects.current,(0.0,0.0))

    def test_disabled_and_clear_have_no_offset(self):
        effects=CameraEffects(enabled=False)
        effects.impulse(1); effects.update(.1)
        self.assertEqual(effects.interpolated(.5),(0.0,0.0))
        effects.enabled=True; effects.impulse(.5); effects.update(.01); effects.clear()
        self.assertEqual(effects.interpolated(.5),(0.0,0.0))

    def test_invalid_configuration_and_impulse_are_rejected(self):
        for factory in (lambda:CameraEffects(amplitude=-1),lambda:CameraEffects(decay=0)):
            with self.assertRaises(ValueError): factory()
        for value in (-.1,1.1,True):
            with self.assertRaises(ValueError): CameraEffects().impulse(value)


if __name__=='__main__': unittest.main()
