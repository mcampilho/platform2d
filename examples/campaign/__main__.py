import argparse
import json
import os
from pathlib import Path


def main():
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
    parser = argparse.ArgumentParser(description="Odisseia Aurora — foguetão, exploração e bordas")
    parser.add_argument("--campaign",type=Path,default=Path(__file__).parent/"assets/odyssey-horizons.json")
    parser.add_argument("--headless",action="store_true")
    parser.add_argument("--frames",type=int)
    parser.add_argument("--screenshot",type=Path)
    parser.add_argument("--save",type=Path,help="Ficheiro de progresso da campanha")
    from platform2d.audio.service import add_audio_arguments
    from platform2d.core.control_settings import add_control_arguments
    add_audio_arguments(parser); add_control_arguments(parser)
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = os.environ["SDL_AUDIODRIVER"] = "dummy"
    import pygame
    from platform2d.core.game import Game
    from .scene import CampaignScene,load_campaign
    from .app import CampaignApp
    from platform2d.gameplay.progress import default_save_path
    try:
        name,ids,documents = load_campaign(args.campaign)
        settings = json.loads((Path(__file__).parents[1]/"ranged/settings.json").read_text(encoding="utf-8"))
        settings['bindings']['continue'] = ['return']
        settings['bindings']['interact'] = ['e']
        settings['bindings'].update(attack=['j'],guard=['l'],up=['up','w'])
        settings['bindings']['save_progress'] = ['f6']
        settings['bindings']['load_progress'] = ['f9']
        pygame.init()
        campaign = CampaignScene(name,ids,documents,settings)
        default_path = default_save_path(args.campaign)
        save_path = args.save or default_path.with_name(default_path.name.replace('world-','campaign-',1))
        scene = CampaignApp(campaign,save_path)
        game = Game(scene,settings['bindings'],size=(960,576),title="Platform2D 0.23 - "+name,
                    volume=args.volume,muted=args.mute or args.headless,controls_profile="campaign",
                    controls_path=args.controls_dir/"campaign.controls.json")
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True,exist_ok=True)
        game.run(args.frames,args.screenshot)
    except (OSError,ValueError,KeyError,TypeError) as error:
        pygame.quit()
        parser.exit(1,f"Não foi possível abrir a campanha: {error}\n")


if __name__ == '__main__':
    main()
