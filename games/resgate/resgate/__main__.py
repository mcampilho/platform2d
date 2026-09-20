import argparse,os
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description='Resgate na Estação')
    parser.add_argument('--headless',action='store_true'); parser.add_argument('--frames',type=int)
    parser.add_argument('--screenshot',type=Path); parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--self-test',action='store_true',help='Verificar os três percursos com comandos reais')
    parser.add_argument('--language',choices=('pt-PT','en','es','fr','de','zh-Hans','ar','ja'),default='pt-PT')
    args=parser.parse_args()
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
    if args.headless or args.self_test: os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from platform2d.core.game import Game
    from platform2d.paths import user_data_dir
    from .scene import RescueGame,BINDINGS
    folder=args.data_dir or user_data_dir('ResgateNaEstacao')
    pygame.init()
    if args.self_test:
        from .verification import verify
        verify(folder); pygame.quit(); return
    scene=RescueGame(folder,args.language)
    game=Game(scene,BINDINGS,size=(960,576),title=scene.t('game_title'),muted=args.headless,language=args.language,
              controls_profile='custom',controls_path=folder/'controls.json')
    pygame.display.set_icon(pygame.image.load(str(Path(__file__).parent/'assets/icon.png')))
    if args.screenshot: args.screenshot.parent.mkdir(parents=True,exist_ok=True)
    game.run(args.frames,args.screenshot)


if __name__=='__main__':
    main()
