import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Estação Aurora — demonstração Platform2D")
    parser.add_argument("--map", type=Path, default=Path(__file__).parent / "assets" / "station.json")
    parser.add_argument("--settings", type=Path, default=Path(__file__).parent / "settings.json")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int)
    parser.add_argument("--screenshot", type=Path)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    from platform2d.audio.service import add_audio_arguments
    add_audio_arguments(parser)
    from platform2d.core.control_settings import add_control_arguments
    add_control_arguments(parser)
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    from platform2d.core.game import Game
    from platform2d.world.tilemap import TileMap
    from .scene import ClassicScene

    try:
        settings = json.loads(args.settings.read_text(encoding="utf-8"))
        level = TileMap.load(args.map)
        pygame.init()
        scene = ClassicScene(level, settings)
        game = Game(scene, settings["bindings"], title="Platform2D • Estação Aurora",volume=args.volume,muted=args.mute or args.headless,controls_profile="classic",controls_path=args.controls_dir/"classic.controls.json")
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        game.run(args.frames, args.screenshot)
    except (ValueError, OSError, KeyError, TypeError) as error:
        pygame.quit()
        parser.exit(1, f"Erro de configuração: {error}\n")


if __name__ == "__main__":
    main()
