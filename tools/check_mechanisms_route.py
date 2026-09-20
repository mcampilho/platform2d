"""Complete the mechanism template through the editor's keyboard input."""
import os
from pathlib import Path
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.editor.profiles import editor_profiles,template_document
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.level_editor import LevelEditor


def main():
    pygame.init()
    profiles = editor_profiles()
    classic = profiles["classic"]
    editor = LevelEditor(classic["factory"],classic["bindings"],template_document("mechanisms"),profiles=profiles)
    output = ROOT/"artifacts"
    output.mkdir(exist_ok=True)
    editor.selected = 3
    editor.conditions_dialog()
    editor.draw()
    pygame.image.save(editor.screen,str(output/"editor-mechanisms-conditions.png"))
    editor.modal = None
    expected = editor.document.snapshot()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)/"central.json"
        editor.document.save(path)
        editor.replace_document(MapDocument.load(path))
        editor.start_preview()
        scene = editor.preview
        events = []
        scene.world.mechanisms.events.subscribe("switch_activated",events.append)
        previous = set()
        ticks = 0
        def tick(held):
            nonlocal previous,ticks
            held = set(held)
            for name in held-previous:
                key = pygame.key.key_code(profiles["rooms"]["bindings"][name][0])
                editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=key,mod=0))
            for name in previous-held:
                key = pygame.key.key_code(profiles["rooms"]["bindings"][name][0])
                editor.handle_event(pygame.event.Event(pygame.KEYUP,key=key,mod=0))
            editor.update(1/60)
            ticks += 1
            previous = held
            assert scene.deaths == 0
        def until(condition,policy):
            for _ in range(2400):
                if condition():
                    return
                tick(policy())
            raise AssertionError(f"Stalled: {scene.world.current_id}, {scene.player.body.x}, {scene.world.mechanisms.active}")
        def walk(x):
            def steer():
                b = scene.player.body
                delta = x-b.x-12-b.vx*abs(b.vx)/2400
                return {"right"} if delta > 3 else {"left"} if delta < -3 else set()
            until(lambda:abs(scene.player.body.x+12-x)<6 and abs(scene.player.body.vx)<35,steer)
        def press(action):
            tick(set())
            tick({action})
            tick(set())
        def door(destination):
            press("interact")
            until(lambda:scene.world.current_id == destination and not scene.transition.active,lambda:set())

        walk(880)
        press("interact")
        assert not scene.transition.active and scene.world.current_id == "control"
        editor.draw()
        pygame.image.save(editor.screen,str(output/"mechanisms-locked.png"))
        walk(262)
        press("interact")
        assert ("control","power") in scene.world.mechanisms.active
        press("interact")
        assert len(events) == 1
        press("restart")
        assert ("control","power") in scene.world.mechanisms.active
        walk(880)
        door("reactor")
        walk(880)
        assert ("reactor","sensor") in scene.world.mechanisms.active and not scene.won
        assert scene.collected == 2
        walk(552)
        press("interact")
        assert ("reactor","console") in scene.world.mechanisms.active
        walk(140)
        door("control")
        assert len(scene.world.mechanisms.active) == 3
        walk(880)
        door("reactor")
        press("restart")
        assert scene.world.current_id == "reactor" and len(scene.world.mechanisms.active) == 3
        until(lambda:scene.won,lambda:{"right"})
        assert len(events) == 3
        editor.draw()
        pygame.image.save(editor.screen,str(output/"mechanisms-completed.png"))
        press("reset")
        assert not scene.world.mechanisms.active and scene.collected == 0 and not scene.won
        editor.stop_preview()
        assert editor.document.snapshot() == expected and not editor.document.dirty
        print(f"Mechanisms: {ticks} steps, blocked door and goal, 3 activations, 3 crossings, reset and round-trip verified; zero deaths.")
    pygame.quit()


if __name__ == "__main__":
    main()
