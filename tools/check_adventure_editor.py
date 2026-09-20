"""Round-trip large maps and run each new capability in the editor preview."""
import os
from pathlib import Path
import sys
import tempfile
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.editor.profiles import editor_profiles
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.level_editor import LevelEditor


def main():
    pygame.init()
    profiles=editor_profiles(); classic=profiles['classic']
    for filename in ('odyssey-launch','odyssey-valley','odyssey-palace'):
        doc=MapDocument.load(ROOT/f'examples/campaign/assets/{filename}.json')
        editor=LevelEditor(classic['factory'],classic['bindings'],doc,profiles=profiles)
        original=doc.snapshot()
        editor.mission_properties()
        editor.close_modal_action(editor.modal['items'][0][1])
        editor.close_modal_action(editor.modal['items'][2][1])
        assert doc.data['properties']['theme']=='ice'
        doc.undo(); assert doc.snapshot()==original
        doc.redo()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'map.json'; doc.save(path)
            editor.replace_document(MapDocument.load(path))
            before=editor.document.snapshot()
            editor.modal=None; editor.start_preview()
            assert editor.preview is not None
            scene=editor.preview
            if filename=='odyssey-launch':
                editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE))
                for _ in range(40): editor.update(1/60)
                editor.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_SPACE))
                assert scene.player.body.y<scene.level.spawn[1]-90
            editor.draw()
            pygame.image.save(editor.screen,str(ROOT/f'artifacts/editor-{filename}.png'))
            editor.stop_preview()
            assert editor.document.snapshot()==before
    pygame.quit()
    print('Adventure editor: theme history, JSON roundtrips, jetpack flight, scrolling previews and document isolation verified.')


if __name__=='__main__': main()
