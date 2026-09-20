"""Run one of six cumulative lessons, or verify the complete playable lesson."""
import argparse,os
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lesson',type=int,choices=range(1,7),default=6)
    parser.add_argument('--headless',action='store_true'); parser.add_argument('--frames',type=int)
    parser.add_argument('--verify',action='store_true'); parser.add_argument('--screenshot',type=Path)
    args=parser.parse_args()
    if args.headless or args.verify: os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from platform2d.core.game import Game
    from platform2d.core.input import Actions
    from platform2d.paths import user_data_dir
    from scene import LessonScene
    pygame.init(); scene=LessonScene(args.lesson)
    if args.verify:
        scene.menu=False; previous=set()
        for frame in range(1800):
            b=scene.player.body; held={'right'}
            if 238<b.x<380 and not scene.collected: held.add('jump')
            if b.on_ground and 0<scene.enemy.x-b.box.right<72: scene.auto_jump=28
            if getattr(scene,'auto_jump',0)>0:
                held.add('jump'); scene.auto_jump-=1
            scene.update(1/60,Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
            previous=held
            if scene.won: break
        assert scene.won and scene.health.remaining==3,(scene.player.body,scene.health.remaining)
        print(f'Tutorial completed: {frame+1} input steps, collectible, enemy avoided, zero damage.')
        pygame.quit(); return
    if args.screenshot: args.screenshot.parent.mkdir(parents=True,exist_ok=True)
    Game(scene,{'left':['left','a'],'right':['right','d'],'jump':['space','z'],'pause':['p'],
                'restart':['r'],'continue':['return']},size=(960,576),title=f'Platform2D — Lição {args.lesson}',
         muted=args.headless,controls_path=user_data_dir('Platform2D-Tutorial')/'controls.json').run(args.frames,args.screenshot)


if __name__=='__main__': main()
