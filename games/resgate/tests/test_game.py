import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
from platform2d.core.input import Actions
from resgate.scene import RescueGame
from platform2d.i18n import LANGUAGES


class RescueTests(unittest.TestCase):
    def setUp(self):
        pygame.init(); self.temp=tempfile.TemporaryDirectory(); self.game=RescueGame(self.temp.name)
    def tearDown(self): self.temp.cleanup(); pygame.quit()

    def test_languages_have_full_catalogues_and_compatible_saves(self):
        self.game.index=1;self.game.start_stage()
        self.game.collected={'valve-a'};self.assertTrue(self.game.save())
        saved=self.game.save_path.read_bytes()
        expected=self.game.snapshot()
        for language in LANGUAGES:
            with self.subTest(language=language):
                translated=RescueGame(self.temp.name,language)
                self.assertEqual(translated.language,language)
                self.assertFalse(translated.translator.missing(language))
                self.assertTrue(translated.load())
                self.assertEqual(translated.snapshot(),expected)
                self.assertEqual(translated.save_path.read_bytes(),saved)

    def test_translated_help_uses_rebound_keys(self):
        self.game.language='es';self.game.translator.select('es')
        self.game.control_label=lambda action:'K' if action=='continue' else 'Q'
        self.game.menu='confirm_load'
        with patch.object(self.game,'text',wraps=self.game.text) as rendered:
            self.game.draw(pygame.Surface((960,576)),1)
        labels=[call.args[1] for call in rendered.call_args_list]
        self.assertIn('K: continuar',labels)
        self.assertTrue(any('K: confirmar' in text and 'Q: cancelar' in text for text in labels))

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

    def test_world_labels_and_hud_are_translated_in_every_sector(self):
        surface=pygame.Surface((960,576))
        expected={
            'pt-PT':('SAÍDA','AR','EQUIPAMENTO 0/2','OXIGÉNIO 12.0s','AMEAÇA A '),
            'en':('EXIT','AIR','EQUIPMENT 0/2','OXYGEN 12.0s','THREAT AT '),
            'es':('SALIDA','AIRE','EQUIPO 0/2','OXÍGENO 12.0s','AMENAZA A '),
        }
        for language,(exit_label,air,equipment,oxygen,threat) in expected.items():
            game=RescueGame(self.temp.name,language)
            for index in range(3):
                with self.subTest(language=language,sector=index):
                    game.index=index;game.start_stage();game.menu=None
                    before=game.snapshot()
                    with patch.object(game,'text',wraps=game.text) as rendered:
                        game.draw(surface,1)
                    labels=[call.args[1] for call in rendered.call_args_list]
                    self.assertIn(exit_label,labels)
                    if index==0: self.assertIn(equipment,labels)
                    elif index==1:
                        self.assertIn(air,labels);self.assertIn(oxygen,labels)
                    else: self.assertTrue(any(label.startswith(threat) for label in labels))
                    self.assertEqual(game.snapshot(),before)
