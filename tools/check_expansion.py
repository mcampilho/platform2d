"""Play all four new levels through real inputs, then verify save roundtrips."""
import os,json,sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import pygame
from platform2d.core.input import Actions
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import capture,restore


def run(mode):
    name,ids,docs=load_campaign(ROOT/f'examples/campaign/assets/{mode}.json')
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text(encoding='utf-8'))
    campaign=CampaignScene(name,ids,docs,settings); s=campaign.active
    previous=set(); phase=0; timer=0; jump=0; waypoint=0; visits=[]; featured=False
    water=[(780,932),(780,800),(128,724),(128,570),(800,380)]
    for frame in range(7200):
        b=s.player.body; held=set(); timer+=1
        if mode=='cargo':
            if phase==0:
                held={'right'}
                if s.cargo.crates['crate-a'].x>=328: phase=1; timer=0
            elif phase==1:
                held={'jump'} | ({'right'} if b.x<346 else set())
                if timer>40 and b.on_ground: phase=2; timer=0
            elif phase==2:
                if timer>3: phase=3; timer=0
            elif phase==3:
                held={'jump'}
                if timer>40: phase=4
            elif phase==4:
                held={'right'}
                if s.cargo.crates['crate-b'].x>=712: phase=5; timer=0
            elif phase==5:
                held={'right','jump'}
                if timer>45: phase=6
            else: held={'right'}
        elif mode=='swim':
            x,y=water[waypoint]
            if abs(b.x-x)<16 and abs(b.y-y)<18:
                visits.append(waypoint); waypoint=min(len(water)-1,waypoint+1)
            if b.x<x-5: held.add('right')
            if b.x>x+5: held.add('left')
            if b.y>y+5: held.add('jump')
            if b.y<y-5: held.add('down')
        else:
            direction=-1 if mode=='explore' and s.ability else 1
            if mode=='explore' and s.ability and b.x<200:
                # Reach the exit shelf with two distinct jump presses.
                held={'left'} if b.x>138 else {'right'} if b.x<125 else set()
                if b.on_ground: phase=1; timer=0
                if phase==1 and timer<18: held.add('jump')
                if phase==1 and 22<=timer<44: held.add('jump')
            else:
                held={'right' if direction>0 else 'left'}
                ahead=b.x+b.w+38 if direction>0 else b.x-38
                obstacle=any(not c.one_way and c.box.x<ahead+4 and c.box.right>ahead and c.box.y<b.box.bottom-2 and c.box.bottom>b.y for c in s.static_colliders)
                floor=any(c.box.x<ahead+4 and c.box.right>ahead and abs(c.box.y-b.box.bottom)<4 for c in s.static_colliders)
                if b.on_ground and (obstacle or not floor) and not jump: jump=27
                if jump: held.add('jump'); jump-=1
        actions=Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held))
        before=(b.x,b.y,b.vx,b.vy,s.camera.x,held)
        campaign.update(1/60,actions); previous=held
        assert s.deaths==0,(mode,frame,phase,waypoint,b,before)
        if frame%120==0:
            screen=pygame.Surface((960,576)); s.draw(screen,1)
            pygame.image.save(screen,str(ROOT/f'artifacts/expansion-{mode}-playing.png'))
        feature=(mode=='cargo' and phase==3 and timer==12 or mode=='swim' and waypoint==2 or mode=='escape' and frame==250 or mode=='explore' and s.ability)
        if feature and not featured:
            screen=pygame.Surface((960,576)); s.draw(screen,1)
            pygame.image.save(screen,str(ROOT/f'artifacts/expansion-{mode}-feature.png')); featured=True
        if s.won: break
    assert s.won,(mode,frame,phase,waypoint,b,s.collected_items,getattr(s,'oxygen',None),s.cargo.snapshot())
    payload=capture(campaign); restore(payload,campaign)
    assert campaign.active.won
    print(f'{mode}: {frame+1} real input steps, zero deaths; victory save restored.')
    return frame+1


def main():
    pygame.init(); pygame.display.set_mode((960,576)); (ROOT/'artifacts').mkdir(exist_ok=True)
    for mode in sys.argv[1:] or ('cargo','swim','escape','explore'): run(mode)
    pygame.quit()


if __name__=='__main__': main()
