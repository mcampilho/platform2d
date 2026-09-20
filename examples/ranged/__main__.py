import argparse
import json
import os
from pathlib import Path


def main():
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
    parser = argparse.ArgumentParser(description="Linha de Defesa — projéteis e combate à distância")
    parser.add_argument("--map",type=Path)
    parser.add_argument("--template",choices=("ranged","inventory"),default="ranged")
    parser.add_argument("--settings",type=Path,default=Path(__file__).parent/"settings.json")
    parser.add_argument("--headless",action="store_true")
    parser.add_argument("--frames",type=int)
    parser.add_argument("--screenshot",type=Path)
    from platform2d.audio.service import add_audio_arguments
    from platform2d.core.control_settings import add_control_arguments
    add_audio_arguments(parser)
    add_control_arguments(parser)
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = os.environ["SDL_AUDIODRIVER"] = "dummy"
    import pygame
    from platform2d.core.game import Game
    from platform2d.tools.editor_model import MapDocument
    from .level import definition
    if args.template == "inventory":
        from .inventory_level import definition
    from .scene import RangedScene
    try:
        document = MapDocument.load(args.map) if args.map else MapDocument(definition())
        if document.profile != "ranged":
            raise ValueError("Escolhe um mapa do perfil Combate.")
        level = document.playable()
        settings = json.loads(args.settings.read_text(encoding="utf-8"))
        pygame.init()
        scene = RangedScene(level,settings)
        game = Game(scene,settings["bindings"],size=(960,576),title=f"Platform2D 0.13 - {level.name}",volume=args.volume,
                    muted=args.mute or args.headless,controls_profile="ranged",controls_path=args.controls_dir/"ranged.controls.json")
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True,exist_ok=True)
        game.run(args.frames,args.screenshot)
    except (ValueError,OSError,KeyError,TypeError) as error:
        pygame.quit()
        parser.exit(1,f"Não foi possível abrir Linha de Defesa: {error}\n")


if __name__ == "__main__":
    main()
