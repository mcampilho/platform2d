"""F8 certification and visible solution replay for all three passive adventures."""
import os,sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import pygame
from examples.editor.profiles import editor_profiles
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.level_editor import LevelEditor


def main():
    pygame.init(); profiles=editor_profiles(); classic=profiles['classic']
    for name in ('launch','valley','palace'):
        doc=MapDocument.load(ROOT/f'examples/campaign/assets/odyssey-{name}.json')
        before=doc.snapshot(); source=doc.path.read_bytes()
        editor=LevelEditor(classic['factory'],classic['bindings'],doc,profiles=profiles)
        editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F8,mod=0))
        for _ in range(4000):
            editor.update(1/60)
            if editor.analysis is None: break
        result=editor.analysis_result
        assert result is not None and result.status=='solved',(name,result)
        editor.draw(); pygame.image.save(editor.screen,str(ROOT/f'artifacts/validation-{name}.png'))
        editor.start_solution()
        for _ in range(len(result.actions)+1): editor.update(1/60)
        assert editor.preview.won and editor.preview.deaths==0
        editor.draw(); pygame.image.save(editor.screen,str(ROOT/f'artifacts/solution-{name}.png'))
        editor.stop_preview(); assert doc.snapshot()==before and doc.path.read_bytes()==source
        print(name,': certified and replayed',len(result.actions),'frames;',result.explored,'states; zero deaths; map unchanged.')
    pygame.quit()

if __name__=='__main__': main()
