"""Complete ranged combat via editor input; exercise editable weapon data."""
import os
from pathlib import Path
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.editor.profiles import editor_profiles,template_document
from platform2d.tools.level_editor import LevelEditor
from platform2d.tools.editor_model import MapDocument


def main():
    pygame.init()
    profiles = editor_profiles()
    classic = profiles["classic"]
    document = template_document("ranged")
    editor = LevelEditor(classic["factory"],classic["bindings"],document,profiles=profiles)
    (ROOT/"artifacts").mkdir(exist_ok=True)
    editor.ranged_properties()
    # Use the same modal callbacks as a mouse click, then type a new interval.
    editor.close_modal_action(editor.modal["items"][1][1])
    editor.handle_event(pygame.event.Event(pygame.TEXTINPUT,text="0.25"))
    editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN,mod=0))
    assert editor.document.data["properties"]["weapon"]["cooldown"] == .25
    editor.draw()
    pygame.image.save(editor.screen,str(ROOT/"artifacts/editor-weapon.png"))
    editor.modal = None
    editor.document.undo()
    assert editor.document.data["properties"]["weapon"]["cooldown"] == .24
    editor.document.redo()
    editor.refresh()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)/"combate.json"
        editor.document.save(path)
        editor.replace_document(MapDocument.load(path))
        snapshot = editor.document.snapshot()
        editor.draw()
        pygame.image.save(editor.screen,str(ROOT/"artifacts/editor-ranged.png"))
        editor.start_preview()
        scene = editor.preview
        previous = set()
        ticks = 0
        def tick(held):
            nonlocal previous,ticks
            held = set(held)
            for pressed,names in ((False,previous-held),(True,held-previous)):
                for name in names:
                    code = pygame.key.key_code(profiles["ranged"]["bindings"][name][0])
                    editor.handle_event(pygame.event.Event(pygame.KEYDOWN if pressed else pygame.KEYUP,key=code))
            editor.update(1/60)
            ticks += 1
            previous = held
            assert scene.deaths == 0,(ticks,scene.player.body)
        def until(label,condition,policy,limit=1200):
            for _ in range(limit):
                if condition():
                    return
                tick(policy())
            raise AssertionError((label,scene.player.body,scene.destroyed,scene.health.remaining))
        # Long-range opening volley, then cross the cover once this side is safe.
        until("first sector",lambda:{"training","sentry-a"} <= scene.destroyed,lambda:{"shoot"})
        until("approach cover",lambda:scene.player.body.x >= 356,lambda:{"right"})
        until("clear cover",lambda:scene.player.body.x > 469,lambda:{"right","jump"})
        until("land",lambda:scene.player.body.on_ground and scene.player.body.y > 475,lambda:set())
        for _ in range(5):
            tick(set())
        editor.draw()
        pygame.image.save(editor.screen,str(ROOT/"artifacts/ranged-battle.png"))
        until("second sector",lambda:len(scene.destroyed) == 4,lambda:{"shoot"})
        until("exit",lambda:scene.won,lambda:{"right"})
        assert not scene.projectiles.items
        assert editor.document.snapshot() == snapshot
        editor.draw()
        pygame.image.save(editor.screen,str(ROOT/"artifacts/ranged-completed.png"))
        print(f"Ranged route: {ticks} steps, 4 targets destroyed, {scene.shots} shots, zero deaths, health {scene.health.remaining}/5. Weapon edited/undone/redone/saved/reopened; preview preserved document.")
        editor.stop_preview()
    pygame.quit()


if __name__ == "__main__":
    main()
