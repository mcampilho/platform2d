"""Complete Colinas through input, then save/reopen/test its editor template."""
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
    document = template_document("slopes")
    assert not [i for i in document.validate() if i.severity == "error"]
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)/"colinas.json"
        document.save(path)
        editor = LevelEditor(classic["factory"],classic["bindings"],MapDocument.load(path),profiles=profiles)
        # Exercise actual keyboard tools, grouped paint and undo/redo.
        for code,tile,column in ((pygame.K_u,"/",2),(pygame.K_b,"\\",3)):
            editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=code,mod=0))
            assert editor.tool == tile
            editor.document.paint(column,2,tile)
            editor.document.commit()
            editor.document.undo()
            assert editor.document.data["tiles"][2][column] == "."
            editor.document.redo()
            assert editor.document.data["tiles"][2][column] == tile
            editor.document.undo()
        snapshot = editor.document.snapshot()
        editor.draw()
        (ROOT/"artifacts").mkdir(exist_ok=True)
        pygame.image.save(editor.screen,str(ROOT/"artifacts/editor-slopes.png"))
        editor.start_preview()
        scene = editor.preview
        previous = set()
        grounded_up = grounded_down = 0
        for tick in range(1200):
            b = scene.player.body
            held = {"right"}
            if 870 < b.x < 1035:
                held.add("jump")
            for action in held-previous:
                editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.key.key_code(classic["bindings"][action][0])))
            for action in previous-held:
                editor.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.key.key_code(classic["bindings"][action][0])))
            old_y = b.y
            editor.update(1/60)
            previous = held
            if b.on_ground and b.y < old_y-.01:
                grounded_up += 1
            if b.on_ground and b.y > old_y+.01:
                grounded_down += 1
            assert scene.deaths == 0, (tick,b.x,b.y)
            if tick == 110:
                surface = pygame.Surface((960,540))
                scene.draw(surface,1)
                pygame.image.save(surface,str(ROOT/"artifacts/slopes-game.png"))
            if scene.won:
                break
        assert scene.won,(scene.player.body,len(scene.collected))
        assert len(scene.collected) == 7
        assert grounded_up > 40 and grounded_down > 40,(grounded_up,grounded_down)
        assert editor.document.snapshot() == snapshot
        editor.draw()
        pygame.image.save(editor.screen,str(ROOT/"artifacts/slopes-completed.png"))
        editor.stop_preview()
        print(f"Colinas: {tick+1} steps, 7 crystals, ascent {grounded_up}, descent {grounded_down}, gap jumped, zero deaths; editor round-trip and history preserved.")
    pygame.quit()


if __name__ == "__main__":
    main()
