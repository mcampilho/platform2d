"""Flight deliveries, full scrolling traversal and ledge climbs through actions."""
import os
import json
from pathlib import Path
import sys
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.campaign.scene import load_campaign,CampaignScene
from examples.campaign.factory import create_scene
from examples.campaign.progress import capture,restore
from platform2d.core.input import Actions


def main():
    pygame.init(); screen=pygame.display.set_mode((960,576))
    name,ids,docs=load_campaign(ROOT/'examples/campaign/assets/odyssey.json')
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text())
    campaign=CampaignScene(name,ids,docs,settings); scene=campaign.active
    previous=set(); ticks=0
    def tick(held=()):
        nonlocal previous,ticks
        held=set(held)
        scene.update(1/60,Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
        previous=held; ticks+=1
        assert scene.deaths==0,(ticks,scene.player.body)
    def until(label,condition,policy,limit=1500):
        for _ in range(limit):
            if condition(): return
            tick(policy())
        raise AssertionError((label,scene.player.body,getattr(scene.player.controller,'anchor',None)))
    def fly(x,y,condition):
        def policy():
            b=scene.player.body; keys={'down'}
            dx=x-(b.x+b.vx*.12)
            if abs(dx)>5: keys.add('right' if dx>0 else 'left')
            if b.y+b.vy*.24>y: keys.add('jump')
            return keys
        until('fly',condition,policy)
    scene.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts/odyssey-rocket.png'))
    for kind in ('part','fuel'):
        for obj in [o for o in scene.level.objects if o['type']==kind]:
            fly(obj['x'],obj['y'],lambda:scene.rocket.carrying==obj['id'])
            # Return high above the launch pad, then descend to its interaction box.
            fly(466,340,lambda:abs(scene.player.body.x-466)<12)
            fly(466,455,lambda:scene.player.body.box.overlaps(scene.box(next(o for o in scene.level.objects if o['type']=='rocket'))))
            tick({'interact'}); tick()
            assert scene.rocket.carrying is None
            if kind=='fuel':
                scene.draw(screen,1); pygame.image.save(screen,str(ROOT/f'artifacts/rocket-fuel-{len(scene.rocket.fuelled)}.png'))
            data=capture(campaign); restore(data,campaign); scene=campaign.active
    assert scene.rocket.ready
    fly(466,455,lambda:scene.player.body.box.overlaps(scene.box(next(o for o in scene.level.objects if o['type']=='rocket'))))
    tick({'interact'})
    for _ in range(60): tick()
    scene.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts/odyssey-launch.png'))
    until('launch',lambda:scene.won,lambda:set())
    print('Rocket assembled and fuelled; six deliveries restored from saves; launch completed.')
    # Existing four rooms have their own complete route verification.
    scene=create_scene(docs[5],settings); previous=set()
    for hazard in [540,1120,1720]:
        until('approach',lambda:scene.player.body.x>=hazard-58,lambda:{'right'})
        tick({'right'})
        until('jump hazard',lambda:scene.player.body.x>=hazard+90,lambda:{'right','jump'})
        until('land',lambda:scene.player.body.on_ground,lambda:set())
    until('valley exit',lambda:scene.won,lambda:{'right'})
    assert scene.camera.x>1000
    scene.won=False; scene.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts/odyssey-parallax.png')); scene.won=True
    print('Horizontal level complete; camera travelled',round(scene.camera.x))
    scene=create_scene(docs[6],settings); previous=set()
    for index in range(8):
        edge=(5+index*3)*32
        until('approach ledge',lambda:scene.player.body.x>=edge-60,lambda:{'right'})
        tick({'right'})
        until('grab',lambda:scene.player.controller.anchor is not None,lambda:{'right','jump'},180)
        if index==3:
            scene.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts/odyssey-hang.png'))
        tick(); tick({'interact'})
        until('climb',lambda:scene.player.controller.anchor is None,lambda:set(),120)
        until('crystal',lambda:f'crystal-{index}' in scene.collected_items,lambda:{'right'})
    until('palace exit',lambda:scene.won,lambda:{'right'})
    assert scene.player.controller.grabs==8
    print('Vertical palace complete: eight ledge grabs and climbs, zero deaths.',ticks,'steps total.')
    pygame.quit()


if __name__=='__main__': main()
