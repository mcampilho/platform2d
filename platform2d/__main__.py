"""Small SDK entry point: python -m platform2d new DIRECTORY."""
import argparse
from importlib.resources import files
from pathlib import Path
from . import __version__


def create_project(destination,name='O meu jogo'):
    target=Path(destination)
    if target.exists(): raise ValueError('A pasta de destino já existe; escolhe uma pasta nova.')
    if not isinstance(name,str) or not name.strip(): raise ValueError('O jogo precisa de nome.')
    import json
    sources=files('platform2d').joinpath('starter')
    planned={}
    for source in sources.iterdir():
        if source.name.endswith('.tmpl'):
            relative=source.name[:-5].replace('__','/',1)
            planned[relative]=source.read_text(encoding='utf-8').replace('@TITLE@',json.dumps(name,ensure_ascii=False))
    target.mkdir(parents=True)
    for relative,content in planned.items():
        path=target/relative; path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content,encoding='utf-8')
    return target.resolve()


def main():
    parser=argparse.ArgumentParser(description='Platform2D — ferramentas para criar jogos')
    parser.add_argument('--version',action='version',version=__version__)
    commands=parser.add_subparsers(dest='command',required=True)
    new=commands.add_parser('new',help='Criar um projeto independente, sem substituir ficheiros')
    new.add_argument('directory',type=Path); new.add_argument('--name',default='O meu jogo')
    commands.add_parser('doctor',help='Mostrar versões e localização da instalação')
    theme=commands.add_parser('theme',help='Criar ou validar um tema visual')
    theme_commands=theme.add_subparsers(dest='theme_command',required=True)
    theme_new=theme_commands.add_parser('new',help='Criar um tema modelo')
    theme_new.add_argument('directory',type=Path)
    theme_new.add_argument('--id',default='my-theme'); theme_new.add_argument('--name',default='O meu tema')
    theme_check=theme_commands.add_parser('check',help='Validar recursos e criar uma pré-visualização')
    theme_check.add_argument('manifest',type=Path)
    theme_check.add_argument('--assets',type=Path)
    theme_check.add_argument('--preview',type=Path)
    args=parser.parse_args()
    if args.command=='doctor':
        import pygame,sys,platform2d
        print(f'Platform2D {__version__}\nPython {sys.version.split()[0]}\nPygame {pygame.version.ver}\nMotor: {Path(platform2d.__file__).parent}')
    elif args.command=='new':
        try: print(f'Projeto criado em {create_project(args.directory,args.name)}\nEntra nessa pasta e executa: python -m mygame')
        except (ValueError,OSError) as error: parser.exit(1,str(error)+'\n')
    else:
        from platform2d.tools.theme_tool import create_theme,inspect_theme,render_preview
        try:
            if args.theme_command=='new':
                print(f'Tema modelo criado em {create_theme(args.directory,args.id,args.name)}')
            else:
                visual,assets=inspect_theme(args.manifest,args.assets)
                print(f'Tema válido: {visual.name} ({visual.id})')
                for role,name,width,height,alpha in assets:
                    print(f'  {role}: {name} — {width}×{height}' + (' — transparência' if alpha else ''))
                if args.preview:
                    print(f'Pré-visualização: {render_preview(visual,args.preview)}')
        except (ValueError,OSError) as error: parser.exit(1,str(error)+'\n')


if __name__=='__main__': main()
