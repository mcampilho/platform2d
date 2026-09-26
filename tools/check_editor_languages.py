"""Smoke-render map and campaign editor screens in every UI language."""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'

import pygame
from examples.campaign.locale import CampaignLocale
from examples.editor.profiles import editor_profiles,template_document
from platform2d.i18n import LANGUAGES
from platform2d.tools.campaign_editor import CampaignEditor
from platform2d.tools.campaign_model import CampaignDocument
from platform2d.tools.level_editor import LevelEditor


PROFILES=('classic','precision','rooms','mechanisms','slopes','ranged','inventory','adventure','duel','cargo','swim','escape','explore')


def main():
    pygame.init()
    profiles=editor_profiles()
    output=ROOT/'artifacts/editor-languages'
    output.mkdir(parents=True,exist_ok=True)
    count=0
    for language in LANGUAGES:
        names=CampaignLocale(language)
        for profile in (*PROFILES,'campaign'):
            if profile=='campaign':
                document=CampaignDocument.load(ROOT/'examples/campaign/assets/odyssey-horizons.json')
                editor=CampaignEditor(document,profiles,language=language)
            else:
                classic=profiles['classic']
                editor=LevelEditor(classic['factory'],classic['bindings'],template_document(profile),
                                   analysis_movement=classic['movement'],profiles=profiles,language=language)
            editor.locale.extra=names.literal
            editor.draw()
            count+=1
            if profile in ('classic','campaign'):
                pygame.image.save(editor.screen,str(output/f'{language}-{profile}.png'))
            editor.show_validation()
            editor.draw()
            count+=1
            if profile=='inventory':
                pickup=next(i for i,obj in enumerate(editor.document.data['objects']) if obj['type']=='pickup')
                editor.pickup_properties(pickup)
                editor.draw()
                count+=1
    pygame.quit()
    print(f'{len(LANGUAGES)} languages, {len(PROFILES)+1} editor profiles, {count} screens rendered')


if __name__=='__main__': main()
