"""Complete game routes through remapped keys and standard controller events."""
import json
import tempfile
from pathlib import Path
from check_rooms_route import ROOT, check_route as rooms_route
from check_precision_route import check_route as precision_route
import pygame
from examples.editor.profiles import editor_profiles,template_document
from platform2d.tools.level_editor import LevelEditor
from platform2d.core.control_settings import ControlSettings


def main():
    pygame.init()
    profiles = editor_profiles()
    classic = profiles["classic"]
    with tempfile.TemporaryDirectory() as folder:
        for profile,route,mode in (("rooms",rooms_route,"keyboard"),("precision",precision_route,"gamepad")):
            editor = LevelEditor(classic["factory"],classic["bindings"],template_document(profile),profiles=profiles,controls_dir=folder)
            snapshot = editor.document.snapshot()
            editor.start_preview()
            panel = editor.controls
            panel.toggle()
            panel.row = panel.actions.index("jump")
            panel.begin_capture()
            panel.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_k))
            assert not panel.capture
            panel.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_k))
            if mode == "gamepad":
                panel.input.attach(71)
                panel.column = 2
                panel.begin_capture()
                panel.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,instance_id=71,button=pygame.CONTROLLER_BUTTON_X))
                panel.handle_event(pygame.event.Event(pygame.CONTROLLERBUTTONUP,instance_id=71,button=pygame.CONTROLLER_BUTTON_X))
            editor.draw()
            pygame.image.save(editor.screen,str(ROOT/f"artifacts/controls-{profile}.png"))
            panel.save()
            path = Path(folder)/(profile+".controls.json")
            assert ControlSettings(profiles[profile]["bindings"],profile,path).data == panel.settings.data
            previous = set()
            def step(actions):
                nonlocal previous
                held = set(actions.held)
                for down,names in ((False,previous-held),(True,held-previous)):
                    for action in names:
                        if mode == "keyboard":
                            event = pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP,key=pygame.key.key_code(panel.settings.data["keys"][action][0]))
                        elif action in ("left","right","up","down"):
                            # Axes are dispatched together below, including diagonals.
                            continue
                        else:
                            event = pygame.event.Event(pygame.CONTROLLERBUTTONDOWN if down else pygame.CONTROLLERBUTTONUP,instance_id=71,button=panel.input.buttons[action])
                        editor.handle_event(event)
                if mode == "gamepad":
                    for index,negative,positive in ((0,"left","right"),(1,"up","down")):
                        value = (int(positive in held)-int(negative in held))*32767
                        editor.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION,instance_id=71,axis=index,value=value))
                previous = held
                editor.update(1/60)
            route(editor.preview,step)
            assert editor.document.snapshot() == snapshot
            assert editor.preview.won and editor.preview.deaths == 0
            print(profile,mode,"completed with remapped jump, document unchanged")
            editor.stop_preview()
        # Compact game-size layout, with the longest action list.
        editor.start_preview()
        editor.controls.toggle()
        surface = pygame.Surface((960,540))
        editor.controls.draw(surface)
        pygame.image.save(surface,str(ROOT/"artifacts/controls-game.png"))
        editor.stop_preview()
    pygame.quit()


if __name__ == "__main__":
    main()
