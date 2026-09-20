"""Validate every catalogue, glyph, UI state and lesson; write review screenshots."""
import os
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
import pygame.freetype
from platform2d.i18n import visual_text
from tutorials.first_game.scene import LessonScene


def main():
    pygame.init()
    out=ROOT/'artifacts/i18n'; out.mkdir(parents=True,exist_ok=True)
    surface=pygame.Surface((960,576))
    scene=LessonScene()
    for source in json.loads((scene.text_renderer.folder/'sources.json').read_text(encoding='utf-8')):
        data=(scene.text_renderer.folder/source['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==source['sha256'], source['file']
    for code in scene.LANGUAGES:
        scene.translator.select(code)
        assert not scene.translator.missing(code), code
        coverage=pygame.freetype.Font(str(scene.text_renderer.folder/scene.translator.metadata['font']),24)
        # Include every message, even notices not reached by the success route.
        for key in scene.translator.metadata['messages']:
            text=scene.translator.text(key,lesson='06',title=scene.translator.text('lesson.6'),
                                       current=3,maximum=3,name=scene.translator.metadata['name'],volume=100)
            visual=visual_text(text,scene.translator.metadata['direction'])
            # SDL_ttf may report the replacement box's metrics for missing glyphs.
            # FreeType returns None for characters absent from the actual font.
            metrics=coverage.get_metrics(visual)
            assert all(m is not None for m in metrics), (code,key,'missing glyph')
            scene.text_renderer.render(text,(255,255,255),24,904)
        for lesson in range(1,7):
            scene.lesson=lesson
            for state in ('menu','playing','paused','won'):
                scene.menu=state=='menu'; scene.paused=state=='paused'; scene.won=state=='won'
                scene.draw(surface,1)
            scene.menu=True; scene.paused=scene.won=False
        scene.draw(surface,1)
        pygame.image.save(surface,str(out/f'{code}.png'))
        print(f'{code}: catalogue, placeholders, glyphs and 24 lesson states OK')
    pygame.quit()


if __name__=='__main__': main()
