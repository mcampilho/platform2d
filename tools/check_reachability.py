"""Check F8, capture its report and replay the certificate in the real scene."""
import json
import os
from pathlib import Path
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.classic.scene import ClassicScene
from platform2d.actors.controller import Movement
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.level_editor import LevelEditor


def main():
    pygame.init()
    settings = json.loads((ROOT/"examples/classic/settings.json").read_text())
    data = json.loads((ROOT/"examples/editor/assets/workshop.json").read_text(encoding="utf-8"))
    editor = LevelEditor(lambda level:ClassicScene(level,settings),settings["bindings"],
                         MapDocument(data),analysis_movement=Movement(**settings["movement"]))
    editor.show_validation()
    while editor.analysis:
        editor.update(0)
    assert editor.analysis_result.status == "solved", editor.analysis_result
    editor.draw()
    output = ROOT/"artifacts"
    output.mkdir(exist_ok=True)
    pygame.image.save(editor.screen,str(output/"editor-solution.png"))
    editor.start_solution()
    for _ in range(len(editor.solution_actions)+1):
        editor.update(1/60)
    assert editor.preview.won and editor.preview.deaths == 0
    editor.draw()
    pygame.image.save(editor.screen,str(output/"editor-solution-completed.png"))
    editor.stop_preview()
    editor.document.data["objects"].append(dict(id="too_high",type="coin",x=320,y=30))
    editor.show_validation()
    while editor.analysis:
        editor.update(0)
    assert editor.analysis_result.status == "impossible"
    editor.draw()
    pygame.image.save(editor.screen,str(output/"editor-unreachable.png"))
    pygame.quit()
    print("F8 verified: complete solution replayed with zero deaths; unreachable crystal identified.")


if __name__ == "__main__":
    main()
