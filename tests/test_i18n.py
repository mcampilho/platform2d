import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from platform2d.i18n import Translator, visual_text
from tutorials.first_game.scene import LessonScene

FOLDER=Path(__file__).resolve().parents[1]/'tutorials/first_game/locales'


class TranslationTests(unittest.TestCase):
    def test_catalogues_complete_and_independent(self):
        first=Translator(FOLDER,'en-US'); second=Translator(FOLDER,'pt_PT')
        self.assertEqual(first.language,'en')
        self.assertEqual(second.language,'pt-PT')
        for code in LessonScene.LANGUAGES:
            first.select(code)
            self.assertEqual(first.missing(code),set())
            self.assertIn('2',first.text('health',current=2,maximum=3))
        self.assertEqual(second.text('start'),'Enter: começar')
        self.assertEqual(first.select('unknown'),'pt-PT')

    def test_missing_translation_uses_fallback_and_bad_placeholders_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            for code in ('pt-PT','en'):
                data=json.loads((FOLDER/f'{code}.json').read_text(encoding='utf-8'))
                if code=='en': del data['messages']['health']
                Path(folder,f'{code}.json').write_text(json.dumps(data),encoding='utf-8')
            translator=Translator(folder,'en')
            self.assertEqual(translator.text('health',current=2,maximum=3),'Vida: 2/3')
            self.assertEqual(translator.missing('en'),{'health'})
            data['messages']['health']='Health: {wrong}'
            Path(folder,'en.json').write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(ValueError): Translator(folder)

    def test_unknown_key_and_missing_value_are_visible_errors(self):
        translator=Translator(FOLDER)
        with self.assertRaises(KeyError): translator.text('typo')
        with self.assertRaises(KeyError): translator.text('health')

    def test_arabic_shaping_keeps_latin_keys_and_digits_readable(self):
        text=visual_text('الصحة: 12/30 · F11/F12','rtl')
        self.assertIn('12/30',text)
        self.assertIn('F11/F12',text)
        self.assertTrue(any('\ufe70'<=c<='\ufeff' for c in text))
        self.assertEqual(visual_text('English 12/30'),'English 12/30')

    def test_language_change_preserves_game_state_and_ignores_key_repeat(self):
        pygame.init()
        try:
            changed=[]
            scene=LessonScene(on_language_changed=changed.append)
            scene.player.body.x=234; scene.collected=True; scene.paused=True
            event=pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4,repeat=False)
            with patch('pygame.display.set_caption'):
                self.assertTrue(scene.handle_event(event))
                scene.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4,repeat=True))
            self.assertEqual(changed,['en'])
            self.assertEqual(scene.player.body.x,234)
            self.assertTrue(scene.collected and scene.paused)
            scene.text_renderer.draw(pygame.Surface((960,576)),scene.translator.text('start'),10)
        finally: pygame.quit()

    def test_arabic_layout_aligns_text_to_right(self):
        pygame.font.init()
        scene=LessonScene(language='ar')
        rect=scene.text_renderer.draw(pygame.Surface((960,576)),scene.translator.text('start'),10)
        self.assertEqual(rect.right,932)


if __name__=='__main__': unittest.main()
