"""Exercise editor input, save/open and a complete playable preview."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.classic.scene import ClassicScene
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.level_editor import LevelEditor


def check_workflow():
    pygame.init()
    settings = json.loads((ROOT/"examples/classic/settings.json").read_text())
    data = json.loads((ROOT/"examples/editor/assets/workshop.json").read_text(encoding="utf-8"))
    editor = LevelEditor(lambda level:ClassicScene(level,settings),settings["bindings"],MapDocument(data))
    output = ROOT/"artifacts/editor-workflow.json"
    output.parent.mkdir(exist_ok=True)

    def event(kind,**kwargs):
        editor.handle_event(pygame.event.Event(kind,**kwargs))
        editor.draw()

    def key(value,mod=0):
        event(pygame.KEYDOWN,key=value,mod=mod)

    def enter_text(text):
        event(pygame.TEXTINPUT,text=str(text))
        key(pygame.K_RETURN)

    editor.draw()
    original = deepcopy(editor.document.data)
    event(pygame.MOUSEBUTTONDOWN,button=1,pos=(600,320))
    event(pygame.MOUSEMOTION,pos=(664,320),rel=(64,0),buttons=(1,0,0))
    event(pygame.MOUSEBUTTONUP,button=1,pos=(664,320))
    key(pygame.K_z,pygame.KMOD_CTRL)
    assert editor.document.data == original
    key(pygame.K_y,pygame.KMOD_CTRL)
    assert editor.document.data != original
    key(pygame.K_5)
    event(pygame.MOUSEBUTTONDOWN,button=1,pos=(376,609))
    event(pygame.MOUSEBUTTONUP,button=1,pos=(376,609))
    key(pygame.K_RIGHT,pygame.KMOD_SHIFT)
    assert len(editor.document.data["objects"]) == 7
    expected = deepcopy(editor.document.data)
    key(pygame.K_s,pygame.KMOD_CTRL)
    enter_text(output)
    if editor.modal and editor.modal["kind"] == "confirm":
        editor.close_modal_action(editor.modal["buttons"][0][1])
    assert not editor.document.dirty and output.exists()
    key(pygame.K_o,pygame.KMOD_CTRL)
    enter_text(output)
    assert editor.document.data == expected
    editor.draw()
    pygame.image.save(editor.screen,str(ROOT/"artifacts/editor-workflow.png"))
    key(pygame.K_F5)
    assert editor.preview is not None
    scene = editor.preview
    route = [(182,482),(332,418),(396,418),(560,354),(730,482),(820,482),(962,482),(1196,482)]
    index = 0
    previous = set()
    keys = {"left":pygame.K_a,"right":pygame.K_d,"jump":pygame.K_SPACE}
    for tick in range(3600):
        b = scene.player.body
        tx,ty = route[index]
        error = tx-(b.x+b.w/2)
        steering = error-b.vx*abs(b.vx)/2400
        held = {"right"} if steering > 4 else {"left"} if steering < -4 else set()
        if (not b.on_ground and "jump" in previous) or (b.on_ground and (
                ty < b.y-5 and abs(error) < 180 or index == 6 and b.x < 900)):
            held.add("jump")
        for name in held-previous:
            editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=keys[name],mod=0))
        for name in previous-held:
            editor.handle_event(pygame.event.Event(pygame.KEYUP,key=keys[name],mod=0))
        previous = held
        editor.update(1/60)
        if scene.deaths:
            raise AssertionError(f"Preview death at waypoint {index}, tick {tick}")
        if abs(b.x+b.w/2-tx) < 14 and abs(b.y-ty) < 3 and b.on_ground:
            index = min(index+1,len(route)-1)
        if scene.won:
            break
    else:
        raise AssertionError(f"Preview stalled at {index}: x={b.x}, y={b.y}, crystals={scene.collected}")
    editor.draw()
    pygame.image.save(editor.screen,str(ROOT/"artifacts/editor-preview-completed.png"))
    key(pygame.K_F5)
    assert editor.preview is None and editor.document.data == expected and not editor.document.dirty
    print(f"Editor workflow passed: painted, undo/redo, placed/moved object, saved/reopened JSON, preview completed in {tick+1} steps, 3 crystals, 0 deaths; document unchanged after preview.")
    pygame.quit()


if __name__ == "__main__":
    check_workflow()
