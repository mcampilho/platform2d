"""Integration route shipped with the game so the frozen build is testable too."""
import json,tempfile
from pathlib import Path
import pygame
from platform2d.core.input import Actions
from .scene import RescueGame


def verify(output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    report=[]
    with tempfile.TemporaryDirectory(prefix='route-',dir=output) as folder:
        game=RescueGame(folder); game.new_game(); game.menu=None
        previous=set(); phase=0; timer=0; jump=0; waypoint=0
        for frame in range(6000):
            b=game.player.body; held=set(); stage=game.index; timer+=1
            if game.menu=='stage':
                game.update(1/60,Actions(pressed=frozenset({'continue'})))
                game.update(1/60,Actions(pressed=frozenset({'continue'})))
                previous=set(); waypoint=0; jump=0; continue
            if stage==1:
                targets=[(780,732),(780,572),(128,492),(128,340),(800,265)]
                x,y=targets[waypoint]
                if abs(b.x-x)<14 and abs(b.y-y)<15: waypoint=min(waypoint+1,len(targets)-1)
                if b.x<x-5: held.add('right')
                if b.x>x+5: held.add('left')
                if b.y>y+5: held.add('jump')
                if b.y<y-5: held.add('down')
            else:
                held={'right'}
                if stage==0:
                    if 244<b.x<380 and 'kit' not in game.collected: held.add('jump')
                else:
                    ahead=b.box.right+38
                    obstacle=any(not c.one_way and c.box.x<ahead+4 and c.box.right>ahead and c.box.y<b.box.bottom-2 and c.box.bottom>b.y for c in game.level.colliders)
                    floor=any(c.box.x<ahead+4 and c.box.right>ahead and abs(c.box.y-b.box.bottom)<4 for c in game.level.colliders)
                    if b.on_ground and (obstacle or not floor) and not jump and 'jump' not in previous: jump=27
                    if jump: held.add('jump'); jump-=1
            before=(b.x,b.y,b.vx,b.vy,jump,held)
            game.update(1/60,Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held))); previous=held
            assert game.deaths==0,(stage,frame,waypoint,game.player.body,before)
            if frame%120==0:
                screen=pygame.Surface((960,576)); game.draw(screen,1); pygame.image.save(screen,str(output/f'stage-{stage+1}.png'))
            if game.stage_won:
                report.append(dict(stage=stage+1,frames=frame+1,collected=len(game.collected)))
                restored=RescueGame(folder); assert restored.load(); assert restored.snapshot()==game.snapshot()
            if game.finished: break
        assert game.finished,(frame,game.index,game.player.body,game.collected)
        assert len(report)==3,report
        screen=pygame.Surface((960,576));game.draw(screen,1);pygame.image.save(screen,str(output/'ending.png'))
        (output/'verification.json').write_text(json.dumps(dict(stages=report,deaths=game.deaths,seconds=game.elapsed),indent=2),encoding='utf-8')
        print('Resgate: three stages completed with real input, zero deaths, all victory saves restored.')
