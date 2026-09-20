"""Complete all campaign stages through keyboard input, without teleporting."""
import os
from pathlib import Path
import sys
import json
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.campaign.scene import CampaignScene,load_campaign
from platform2d.core.input import Input


def main():
    pygame.init(); surface=pygame.display.set_mode((960,576))
    name,ids,docs=load_campaign(ROOT/'examples/campaign/assets/campaign.json')
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text())
    settings['bindings']['continue']=['return']
    scene=CampaignScene(name,ids,docs,settings)
    inputs=Input(settings['bindings']); previous=set(); ticks=0
    before=[d.snapshot() for d in docs]
    def tick(held):
        nonlocal previous,ticks
        held=set(held)
        for pressed,names in ((False,previous-held),(True,held-previous)):
            for action in names:
                event=pygame.event.Event(pygame.KEYDOWN if pressed else pygame.KEYUP,key=pygame.key.key_code(settings['bindings'][action][0]))
                inputs.feed([event])
        scene.update(1/60,inputs.consume()); previous=held; ticks+=1
        assert scene.active.deaths==0
    def until(label,condition,held):
        for _ in range(1200):
            if condition(): return
            tick(held)
        raise AssertionError((label,scene.active.player.body,scene.active.destroyed))
    for index in range(3):
        s=scene.active
        until('first pickup',lambda:s.player.body.x>=150,{'right','shoot'})
        until('first sector',lambda:{'training','sentry-a'}<=s.destroyed,{'shoot'})
        until('cover',lambda:s.player.body.x>=356,{'right'})
        until('jump',lambda:s.player.body.x>469,{'right','jump'})
        until('land',lambda:s.player.body.on_ground and s.player.body.y>475,set())
        until('second sector',lambda:len(s.destroyed)==4,{'shoot'})
        until('exit',lambda:s.won,{'right'})
        inventory=s.inventory.snapshot()
        scene.draw(surface,1)
        pygame.image.save(surface,str(ROOT/f'artifacts/campaign-stage-{index+1}.png'))
        tick(set()); tick({'continue'})
        if index<2:
            assert scene.progress.index==index+1
            assert scene.active.inventory.snapshot()==inventory
            assert scene.active.health.remaining==5
    assert scene.progress.finished
    assert scene.totals['deaths']==0
    assert before==[d.snapshot() for d in docs]
    print(f'Campaign complete: 3 stages, {ticks} steps, {scene.totals["shots"]} shots, zero deaths; inventory carried and maps preserved.')
    pygame.quit()


if __name__=='__main__': main()
