import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Arquivo Lunar — salas e plataformas móveis")
    parser.add_argument("--world", type=Path, default=Path(__file__).parent / "assets/world.json")
    parser.add_argument("--settings", type=Path, default=Path(__file__).parent / "settings.json")
    parser.add_argument("--save-file",type=Path,help="Ficheiro de progresso (F6/F9)")
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
    from platform2d.world.room import RoomWorld
    from .scene import RoomsScene
    from platform2d.gameplay.progress import ProgressSlot, default_save_path

    try:
        settings = json.loads(args.settings.read_text(encoding="utf-8"))
        world = RoomWorld.load(args.world)
        pygame.init()
        default_world = Path(__file__).parent/"assets/world.json"
        save_path = args.save_file or default_save_path(None if args.world.resolve() == default_world.resolve() else args.world,"arquivo-lunar")
        if save_path.resolve() in {args.world.resolve(),args.settings.resolve()}:
            raise ValueError("O ficheiro de progresso deve ser diferente do mundo e das definições.")
        scene = RoomsScene(world, settings, ProgressSlot(save_path))
        game = Game(scene, settings["bindings"], size=(960,576), title="Platform2D 0.2 - Parte 2 - Arquivo Lunar",volume=args.volume,muted=args.mute or args.headless,controls_profile="rooms",controls_path=args.controls_dir/"rooms.controls.json")
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        game.run(args.frames, args.screenshot)
    except (ValueError, OSError, KeyError, TypeError) as error:
        pygame.quit()
        parser.exit(1, f"Erro de configuração: {error}\n")


if __name__ == "__main__":
    main()
