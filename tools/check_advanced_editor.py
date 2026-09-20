"""Round-trip both advanced profiles and complete their previews through input."""
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
from tools.check_rooms_route import check_route as rooms_route
from tools.check_precision_route import check_route as precision_route


def main():
    pygame.init()
    profiles = editor_profiles()
    classic = profiles["classic"]
    output = ROOT/"artifacts"
    output.mkdir(exist_ok=True)
    for profile,route in (("rooms",rooms_route),("precision",precision_route)):
        editor = LevelEditor(classic["factory"],classic["bindings"],template_document(profile),profiles=profiles)
        doc = editor.document
        if profile == "rooms":
            index = next(i for i,o in enumerate(doc.data["objects"]) if o["type"] == "moving_platform")
            doc.update_object(index,speed=52)
        else:
            index = next(i for i,o in enumerate(doc.data["objects"]) if o["type"] == "ladder")
            doc.update_object(index,w=36)
        editor.finish_edit()
        editor.select_object(index)
        editor.draw()
        pygame.image.save(editor.screen,str(output/f"editor-{profile}-properties.png"))
        if profile == "rooms":
            editor.special_properties()
            editor.draw()
            pygame.image.save(editor.screen,str(output/"editor-platform-properties.png"))
            editor.modal = None
            editor.room_dialog()
            editor.draw()
            pygame.image.save(editor.screen,str(output/"editor-room-list.png"))
            editor.modal = None
            door_index = next(i for i,o in enumerate(doc.data["objects"]) if o["type"] == "door")
            editor.select_object(door_index)
            editor.door_destination()
            editor.draw()
            pygame.image.save(editor.screen,str(output/"editor-door-destination.png"))
            editor.modal = None
        expected = doc.snapshot()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/f"{profile}.json"
            doc.save(path)
            editor.replace_document(MapDocument.load(path))
            assert editor.document.snapshot() == expected
            editor.show_validation()
            assert editor.analysis is None
            assert not any(i.severity == "error" for i in editor.issues)
            editor.draw()
            pygame.image.save(editor.screen,str(output/f"editor-{profile}-validation.png"))
            editor.close_validation()
            editor.start_preview()
            def step(action):
                # Drive the editor's own fixed-step loop, including input bindings.
                for name in action.pressed:
                    key = pygame.key.key_code(profiles[profile]["bindings"][name][0])
                    editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=key,mod=0))
                for name in action.released:
                    key = pygame.key.key_code(profiles[profile]["bindings"][name][0])
                    editor.handle_event(pygame.event.Event(pygame.KEYUP,key=key,mod=0))
                editor.update(1/60)
            route(editor.preview,step)
            editor.draw()
            pygame.image.save(editor.screen,str(output/f"editor-{profile}-completed.png"))
            editor.stop_preview()
            assert editor.document.snapshot() == expected and not editor.document.dirty
        print(f"Editor {profile}: modified, saved, reopened and completed; document preserved.")
    pygame.quit()


if __name__ == "__main__":
    main()
