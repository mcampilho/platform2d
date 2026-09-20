"""Render all Resgate screens and shared controls in each advertised language."""
import os
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'games/resgate')]
import pygame
import pygame.freetype
from platform2d.i18n import LANGUAGES,fields,visual_text
from platform2d.core.game import Game
from resgate.scene import RescueGame,BINDINGS


def check_glyphs(translator,folder):
    assert not translator.missing(translator.language)
    font=pygame.freetype.Font(str(folder/translator.metadata['font']),20)
    for key,message in translator.metadata['messages'].items():
        rendered=translator.text(key,**{name:'12' for name in fields(message)})
        visual=visual_text(rendered,translator.metadata['direction'])
        assert all(m is not None for m in font.get_metrics(visual)),(translator.language,key,'missing glyph')


def main():
    pygame.init()
    out=ROOT/'artifacts/resgate-languages';out.mkdir(parents=True,exist_ok=True)
    results={}
    with tempfile.TemporaryDirectory() as folder:
        for language in LANGUAGES:
            scene=RescueGame(folder,language)
            game=Game(scene,BINDINGS,size=(960,576),muted=True,language=language)
            check_glyphs(scene.translator,scene.renderer.folder)
            check_glyphs(game.controls.locale.translator,game.controls.locale.renderer.folder)
            for index in range(3):
                scene.index=index;scene.start_stage()
                for state in (None,'title','briefing','pause','confirm_new','confirm_load','stage','ending'):
                    scene.menu=state
                    scene.draw(game.screen,1)
                    game.controls.draw_hint(game.screen);game.audio_controls.draw(game.screen)
                    if state in ('title','briefing') or state is None:
                        pygame.image.save(game.screen,str(out/f'{language}-{index}-{state or "play"}.png'))
            scene.say(scene.t('load_failed'));scene.draw(game.screen,1)
            game.controls.toggle();game.controls.draw(game.screen)
            pygame.image.save(game.screen,str(out/f'{language}-controls.png'))
            game.controls.row=game.controls.actions.index('jump')
            game.controls.begin_capture();game.controls.assign('left')
            assert game.controls.capture
            assert game.controls.message==game.controls.t('error.used_key')
            game.controls.draw(game.screen)
            pygame.image.save(game.screen,str(out/f'{language}-conflict.png'))
            game.controls.close();game.audio.close()
            results[language]={'screens':24,'catalogues_complete':True,'glyphs_present':True,'conflict_localized':True}
            print(f'{language}: all sectors, menus, controls, validation and font coverage OK')
    (out/'verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    pygame.quit()


if __name__=='__main__': main()
