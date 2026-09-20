"""Save a played session, restore in another process, then complete the game."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.mechanisms.world import definition
from examples.rooms.scene import RoomsScene
from platform2d.core.input import Actions,Input
from platform2d.gameplay.progress import ProgressSlot
from platform2d.world.room import RoomWorld

SETTINGS = json.loads((ROOT/"examples/rooms/settings.json").read_text())


def scene_for(path):
    return RoomsScene(RoomWorld(definition()),SETTINGS,ProgressSlot(path))


class Driver:
    def __init__(self,scene):
        self.scene = scene
        self.previous = set()
        self.input = Input(SETTINGS["bindings"])

    def tick(self,held=()):
        held = set(held)
        for kind,names in ((pygame.KEYDOWN,held-self.previous),(pygame.KEYUP,self.previous-held)):
            self.input.feed([pygame.event.Event(kind,key=pygame.key.key_code(SETTINGS["bindings"][name][0])) for name in names])
        self.previous = held
        self.scene.update(1/60,self.input.consume())
        assert self.scene.deaths == 0

    def press(self,action):
        self.tick()
        self.tick({action})
        self.tick()

    def until(self,predicate,policy):
        for _ in range(2400):
            if predicate():
                return
            self.tick(policy())
        raise AssertionError("Route stalled")

    def walk(self,x):
        def steer():
            b = self.scene.player.body
            delta = x-b.x-12-b.vx*abs(b.vx)/2400
            return {"right"} if delta > 3 else {"left"} if delta < -3 else set()
        self.until(lambda:abs(self.scene.player.body.x+12-x)<6 and abs(self.scene.player.body.vx)<35,steer)


def screenshot(scene,name):
    output = ROOT/"artifacts"
    output.mkdir(exist_ok=True)
    surface = pygame.Surface((960,576))
    scene.draw(surface,1)
    pygame.image.save(surface,str(output/name))


def resumed(path):
    pygame.init()
    scene = scene_for(path)
    driver = Driver(scene)
    driver.press("load_progress")
    assert scene.world.current_id == "reactor"
    assert scene.world.checkpoint == ("reactor",(188,482))
    assert scene.collected == 1
    assert scene.world.mechanisms.active == {("control","power"),("reactor","sensor")}
    screenshot(scene,"progress-loaded.png")
    driver.walk(552)
    driver.press("interact")
    driver.until(lambda:scene.won,lambda:{"right"})
    assert scene.collected == 2 and len(scene.world.mechanisms.active) == 3
    driver.press("save_progress")
    screenshot(scene,"progress-completed.png")
    old = path.read_bytes()
    driver.press("reset")
    assert not scene.won and scene.collected == 0
    driver.press("load_progress")
    assert scene.won and scene.collected == 2
    assert path.read_bytes() == old
    pygame.quit()
    print("Fresh process: checkpoint restored; mechanisms, crystals and victory verified; zero deaths.")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--resume":
        resumed(Path(sys.argv[2]))
        return
    pygame.init()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)/"central.progress.json"
        scene = scene_for(path)
        driver = Driver(scene)
        driver.walk(262)
        driver.press("interact")
        driver.walk(880)
        driver.press("interact")
        driver.until(lambda:scene.world.current_id == "reactor" and not scene.transition.active,lambda:set())
        driver.walk(330)
        driver.press("save_progress")
        assert path.exists() and scene.world.checkpoint == ("reactor",(188,482))
        screenshot(scene,"progress-saved.png")
        pygame.quit()
        subprocess.run([sys.executable,str(Path(__file__).resolve()),"--resume",str(path)],check=True,cwd=ROOT)
        pygame.init()
        changed = definition()
        changed["rooms"]["control"]["name"] = "Mapa alterado"
        scene = RoomsScene(RoomWorld(changed),SETTINGS,ProgressSlot(path))
        scene.update(1/60,Actions(pressed=frozenset({"load_progress"})))
        assert "incompatível" in scene.progress_message and not scene.collected
        screenshot(scene,"progress-incompatible.png")
        pygame.quit()
    print("Save workflow passed: keyboard controls, disk write, new process, finish, reset, reload and incompatibility rejection.")


if __name__ == "__main__":
    main()
