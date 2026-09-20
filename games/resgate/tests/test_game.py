import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
from platform2d.core.input import Actions
from resgate.scene import RescueGame


class RescueTests(unittest.TestCase):
    def setUp(self):
        pygame.init(); self.temp=tempfile.TemporaryDirectory(); self.game=RescueGame(self.temp.name)
    def tearDown(self): self.temp.cleanup(); pygame.quit()

    def test_pause_and_title_do_not_advance_physics(self):
        s=self.game
        for menu in ('title','pause','briefing'):
            s.menu=menu; before=(s.elapsed,s.oxygen,s.player.body.x)
            s.update(1,Actions(held=frozenset({'right','jump'})))
            self.assertEqual(before,(s.elapsed,s.oxygen,s.player.body.x))

    def test_invalid_save_preserves_live_game(self):
        s=self.game; before=s.snapshot()
        for changes in ({'index':True},{'checkpoint':[]},{'elapsed':float('inf')},{'collected':['unknown']},{'index':2,'stage_won':True,'finished':False}):
            data=dict(before,**changes);s.save_path.write_text(json.dumps(data))
            self.assertFalse(s.load()); self.assertEqual(before,s.snapshot())

    def test_failed_replace_preserves_last_good_save(self):
        s=self.game; s.save(); before=s.save_path.read_bytes(); s.deaths=3
        with patch('resgate.scene.os.replace',side_effect=OSError('blocked')): self.assertFalse(s.save())
        self.assertEqual(s.save_path.read_bytes(),before)

    def test_new_game_confirmation_can_be_cancelled(self):
        s=self.game; s.collected={'kit'}; s.save(); previous=s.save_path.read_bytes();s.menu='title'
        s.update(1/60,Actions(pressed=frozenset({'continue'})))
        self.assertEqual(s.menu,'confirm_new')
        s.update(1/60,Actions(pressed=frozenset({'pause'})))
        self.assertEqual(s.menu,'title');self.assertEqual(s.save_path.read_bytes(),previous)

    def test_save_resumes_at_checkpoint_with_recovered_oxygen(self):
        s=self.game;s.index=1;s.start_stage();s.oxygen=2;s.collected={'valve-a'};s.save()
        self.assertTrue(s.load());self.assertEqual(s.oxygen,12);self.assertEqual(s.collected,{'valve-a'})

    def test_collectible_is_required_for_exit(self):
        s=self.game;s.menu=None;s.player.respawn((1184,482))
        s.update(1/60,Actions());self.assertFalse(s.stage_won)
        s.collected={'kit','radio'};s.update(1/60,Actions());self.assertTrue(s.stage_won)

    def test_respawn_keeps_collectibles_and_resets_chase(self):
        s=self.game;s.index=2;s.start_stage();s.checkpoint='evac-cp';s.chase=100
        s.respawn();self.assertEqual(s.chase,0);self.assertEqual(s.player.body.x,1120)
