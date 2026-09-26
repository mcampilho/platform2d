import json
import os
from pathlib import Path
import unittest

os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from examples.campaign.app import CampaignApp
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import capture
from examples.campaign.locale import CampaignLocale
from platform2d.i18n import LANGUAGES
from platform2d.tools.editor_i18n import EditorLocale


ROOT=Path(__file__).resolve().parents[1]


class CampaignEditorLanguageTests(unittest.TestCase):
    def test_complete_catalogues_and_built_in_map_names(self):
        for cls in (CampaignLocale,EditorLocale):
            for language in LANGUAGES:
                locale=cls(language)
                self.assertFalse(locale.translator.missing(language))
                self.assertEqual(locale.translator.language,language)
        self.assertEqual(CampaignLocale('en').literal('Oficina Orbital'),'Orbital Workshop')
        self.assertEqual(EditorLocale('ja').literal('Guardar'),'保存')

    def test_language_does_not_change_campaign_progress(self):
        pygame.init()
        try:
            name,ids,docs=load_campaign(ROOT/'examples/campaign/assets/odyssey-horizons.json')
            settings=json.loads((ROOT/'examples/ranged/settings.json').read_text(encoding='utf-8'))
            campaign=CampaignScene(name,ids,docs,settings)
            before=capture(campaign)
            for language in LANGUAGES:
                CampaignApp(campaign,language=language)
                self.assertEqual(capture(campaign),before)
        finally:
            pygame.quit()

    def test_editor_diagnostic_preserves_map_identifier(self):
        locale=EditorLocale('ar')
        source='door-a: área de interação da porta bloqueada.'
        result=locale.literal(source)
        self.assertIn('door-a',result)
        self.assertNotIn('área de interação',result)
        self.assertEqual(locale.literal('obj-x: um erro personalizado'),
                         'obj-x: um erro personalizado')


if __name__=='__main__': unittest.main()
