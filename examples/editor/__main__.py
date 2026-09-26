import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Atelier — editor visual Platform2D")
    parser.add_argument("--map",type=Path,help="Mapa ou mundo existente para abrir")
    parser.add_argument("--profile",choices=("classic","precision","rooms","mechanisms","slopes","ranged","inventory","adventure","duel","cargo","swim","escape","explore","campaign"),default="classic",help="Modelo inicial (ignorado com --map)")
    parser.add_argument("--output",type=Path,default=Path("levels/meu-nivel.json"))
    parser.add_argument("--headless",action="store_true")
    parser.add_argument("--frames",type=int)
    parser.add_argument("--screenshot",type=Path)
    from platform2d.i18n import LANGUAGES
    parser.add_argument("--language",choices=LANGUAGES,default='pt-PT')
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
    from platform2d.tools.editor_model import MapDocument
    from platform2d.tools.level_editor import LevelEditor
    from .profiles import editor_profiles, template_document
    from platform2d.audio import Audio
    try:
        pygame.init()
        profiles = editor_profiles()
        from platform2d.tools.campaign_model import CampaignDocument,FORMAT
        from platform2d.tools.campaign_editor import CampaignEditor
        is_campaign=args.profile=='campaign' and not args.map
        if args.map:
            raw=json.loads(args.map.read_text(encoding='utf-8-sig'))
            is_campaign=isinstance(raw,dict) and raw.get('format')==FORMAT
        if is_campaign:
            if args.map: document=CampaignDocument.load(args.map)
            else:
                document=CampaignDocument.load(Path(__file__).parents[1]/'campaign/assets/odyssey-horizons.json')
                document.path=None; document.saved=None
            editor=CampaignEditor(document,profiles,args.output,audio=Audio(args.volume,args.mute or args.headless),controls_dir=args.controls_dir,language=args.language)
        else:
            document=MapDocument.load(args.map) if args.map else template_document(args.profile)
            classic = profiles['classic']
            editor = LevelEditor(classic['factory'],classic['bindings'],document,args.output,
                                 analysis_movement=classic['movement'],profiles=profiles,audio=Audio(args.volume,args.mute or args.headless),controls_dir=args.controls_dir,language=args.language)
        from examples.campaign.locale import CampaignLocale
        editor.locale.extra=CampaignLocale(args.language).literal
        editor.run(args.frames,args.screenshot)
    except (ValueError,OSError,KeyError,TypeError) as error:
        pygame.quit()
        parser.exit(1,f"Não foi possível abrir o editor: {error}\n")


if __name__ == "__main__":
    main()
