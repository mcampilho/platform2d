"""Edit a pickup, then complete the upgraded arena using real input events."""
import os
from pathlib import Path
import sys
import tempfile

os.environ['SDL_VIDEODRIVER'] = os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.editor.profiles import editor_profiles,template_document
from platform2d.tools.level_editor import LevelEditor
from platform2d.tools.editor_model import MapDocument


def main():
    pygame.init()
    profiles=editor_profiles(); classic=profiles['classic']
    editor=LevelEditor(classic['factory'],classic['bindings'],template_document('inventory'),profiles=profiles)
    index=next(i for i,o in enumerate(editor.document.data['objects']) if o['id']=='medical-a')
    editor.selected=index
    editor.special_properties()
    editor.close_modal_action(editor.modal['items'][1][1])
    editor.handle_event(pygame.event.Event(pygame.TEXTINPUT,text='2'))
    editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN,mod=0))
    assert editor.document.data['objects'][index]['quantity']==2
    editor.draw()
    pygame.image.save(editor.screen,str(ROOT/'artifacts/editor-inventory.png'))
    editor.modal=None
    editor.document.undo()
    assert editor.document.data['objects'][index]['quantity']==1
    editor.document.redo()
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'inventory.json'; editor.document.save(path)
        editor.replace_document(MapDocument.load(path))
        snapshot=editor.document.snapshot()
        editor.start_preview(); scene=editor.preview
        previous=set(); ticks=0
        def tick(held):
            nonlocal previous,ticks
            held=set(held)
            for pressed,names in ((False,previous-held),(True,held-previous)):
                for name in names:
                    key=pygame.key.key_code(profiles['ranged']['bindings'][name][0])
                    editor.handle_event(pygame.event.Event(pygame.KEYDOWN if pressed else pygame.KEYUP,key=key))
            editor.update(1/60); previous=held; ticks+=1
            assert scene.deaths==0,(ticks,scene.health.remaining)
        def until(label,condition,held,limit=1200):
            for _ in range(limit):
                if condition(): return
                tick(held)
            raise AssertionError((label,scene.player.body,scene.destroyed,scene.health.remaining))
        until('first upgrade',lambda:scene.inventory.count('power')==1,{'right','shoot'})
        until('first sector',lambda:{'training','sentry-a'} <= scene.destroyed,{'shoot'})
        until('cover',lambda:scene.player.body.x>=356,{'right'})
        assert scene.inventory.count('rapid')==1
        until('jump',lambda:scene.player.body.x>469,{'right','jump'})
        until('land',lambda:scene.player.body.on_ground and scene.player.body.y>475,set())
        until('medkit',lambda:scene.inventory.count('medkit')==2,{'right'})
        # Let the remaining turret hit us; use a kit through the configured key.
        until('injury',lambda:scene.health.remaining<5,set())
        before=scene.health.remaining
        tick({'use_item'})
        assert scene.health.remaining==min(5,before+2)
        assert scene.inventory.count('medkit')==1
        editor.draw()
        pygame.image.save(editor.screen,str(ROOT/'artifacts/inventory-battle.png'))
        until('second sector',lambda:len(scene.destroyed)==4,{'shoot'})
        until('exit',lambda:scene.won,{'right'})
        assert scene.inventory.snapshot()==dict(power=2,rapid=1,medkit=1)
        assert scene.weapon.spec.damage==3
        assert abs(scene.weapon.spec.cooldown-.192)<1e-9
        assert editor.document.snapshot()==snapshot
        editor.draw()
        pygame.image.save(editor.screen,str(ROOT/'artifacts/inventory-completed.png'))
        print(f'Inventory route: {ticks} steps, 4 targets, {scene.shots} shots, zero deaths; all pickups collected, kit used, weapon upgraded. Editor undo/redo/save/reopen and preview isolation OK.')
        editor.stop_preview()
    pygame.quit()


if __name__=='__main__':
    main()
