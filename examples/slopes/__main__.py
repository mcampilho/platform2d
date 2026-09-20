import argparse
import json
import os
from pathlib import Path


def main():
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
    parser = argparse.ArgumentParser(description="Colinas — rampas e superfícies inclinadas")
    parser.add_argument("--map",type=Path)
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
    from platform2d.world.tilemap import TileMap
    from examples.classic.scene import ClassicScene
    from .level import definition
    try:
        settings = json.loads((Path(__file__).parents[1]/"classic/settings.json").read_text(encoding="utf-8"))
        level = TileMap.load(args.map) if args.map else TileMap(definition())
        pygame.init()
        scene = ClassicScene(level,settings)
        game = Game(scene,settings["bindings"],title="Platform2D 0.11 - Colinas",volume=args.volume,
                    muted=args.mute or args.headless,controls_profile="classic",controls_path=args.controls_dir/"classic.controls.json")
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True,exist_ok=True)
        game.run(args.frames,args.screenshot)
    except (ValueError,OSError,KeyError,TypeError) as error:
        pygame.quit()
        parser.exit(1,f"Não foi possível abrir Colinas: {error}\n")


if __name__ == "__main__":
    main()
