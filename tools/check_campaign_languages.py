"""Render every built-in Odyssey stage and menu in all supported languages."""
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'

import pygame
from examples.campaign.app import CampaignApp
from examples.campaign.factory import create_scene
from examples.campaign.scene import CampaignScene,load_campaign
from platform2d.i18n import LANGUAGES


def main():
    pygame.init()
    output=ROOT/'artifacts/campaign-languages'
    output.mkdir(parents=True,exist_ok=True)
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text(encoding='utf-8'))
    name,ids,documents=load_campaign(ROOT/'examples/campaign/assets/odyssey-horizons.json')
    screens=0
    for language in LANGUAGES:
        campaign=CampaignScene(name,ids,documents,settings)
        app=CampaignApp(campaign,language=language)
        surface=pygame.Surface((960,576))
        for mode in ('title','pause','options','quit'):
            app.mode=mode
            app.draw(surface,0)
            if mode=='title': pygame.image.save(surface,str(output/f'{language}-title.png'))
            screens+=1
        app.mode=None
        for index,document in enumerate(documents):
            campaign.progress.index=index
            campaign.active=create_scene(document,settings)
            campaign.active.locale=app.locale
            app.draw(surface,0)
            pygame.image.save(surface,str(output/f'{language}-{index+1:02}.png'))
            screens+=1
    pygame.quit()
    print(f'{len(LANGUAGES)} languages, {len(documents)} stages, {screens} screens rendered')


if __name__=='__main__': main()
