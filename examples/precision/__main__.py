import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Ascensão — laboratório de movimento")
    root = Path(__file__).parent
    parser.add_argument("--map",type=Path,default=root/"assets/ascent.json")
    parser.add_argument("--settings",type=Path,default=root/"settings.json")
    parser.add_argument("--headless",action="store_true")
    parser.add_argument("--frames",type=int)
    parser.add_argument("--screenshot",type=Path)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    from platform2d.audio.service import add_audio_arguments
    add_audio_arguments(parser)
    from platform2d.core.control_settings import add_control_arguments
    add_control_arguments(parser)
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
    import pygame
    from platform2d.core.game import Game
    from platform2d.world.tilemap import TileMap
    from .scene import PrecisionScene
    try:
        level = TileMap(json.loads(args.map.read_text(encoding="utf-8")),{"ladder","beacon"})
        settings = json.loads(args.settings.read_text(encoding="utf-8"))
        pygame.init()
        scene = PrecisionScene(level,settings)
        game = Game(scene,settings["bindings"],size=(960,576),title="Platform2D 0.4 - Parte 4 - Ascensao",volume=args.volume,muted=args.mute or args.headless,controls_profile="precision",controls_path=args.controls_dir/"precision.controls.json")
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True,exist_ok=True)
        game.run(args.frames,args.screenshot)
    except (ValueError,OSError,KeyError,TypeError) as error:
        pygame.quit()
        parser.exit(1,f"Erro de configuração: {error}\n")


if __name__ == "__main__":
    main()
