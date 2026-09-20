import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Central de Energia — interruptores e portas condicionais")
    parser.add_argument("--world",type=Path)
    parser.add_argument("--save-file",type=Path,help="Ficheiro de progresso (F6/F9)")
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
    from platform2d.world.room import RoomWorld
    from examples.rooms.scene import RoomsScene
    from .world import definition
    from platform2d.gameplay.progress import ProgressSlot, default_save_path
    try:
        settings = json.loads((Path(__file__).parents[1]/"rooms/settings.json").read_text())
        world = RoomWorld.load(args.world) if args.world else RoomWorld(definition())
        pygame.init()
        save_path = args.save_file or default_save_path(args.world,"central-energia")
        if args.world and save_path.resolve() == args.world.resolve():
            raise ValueError("O ficheiro de progresso deve ser diferente do mundo.")
        scene = RoomsScene(world,settings,ProgressSlot(save_path))
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True,exist_ok=True)
        Game(scene,settings["bindings"],size=(960,576),title="Platform2D 0.12 - Central de Energia",volume=args.volume,muted=args.mute or args.headless,controls_profile="rooms",controls_path=args.controls_dir/"rooms.controls.json").run(args.frames,args.screenshot)
    except (ValueError,OSError,KeyError,TypeError) as error:
        pygame.quit()
        parser.exit(1,f"Erro de configuração: {error}\n")


if __name__ == "__main__":
    main()
