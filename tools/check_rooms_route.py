"""Exercise both rooms using only Actions: lift, doors, return trip and ferry."""
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
from examples.rooms.scene import RoomsScene
from platform2d.core.input import Actions
from platform2d.world.room import RoomWorld


def check_route(scene=None,step=None):
    pygame.init()
    owns_scene = scene is None
    if owns_scene:
        scene = RoomsScene(RoomWorld.load(ROOT/"examples/rooms/assets/world.json"),
                           json.loads((ROOT/"examples/rooms/settings.json").read_text()))
    step = step or (lambda action:scene.update(1/60,action))
    previous = set()
    ticks = 0

    def tick(held):
        nonlocal previous,ticks
        held = set(held)
        step(Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
        previous = held
        ticks += 1
        if scene.deaths:
            raise AssertionError(f"Death in {scene.world.current_id} at tick {ticks}")

    def until(label, condition, policy, limit=2400):
        for _ in range(limit):
            if condition():
                return
            tick(policy())
        b = scene.player.body
        raise AssertionError(f"{label} stalled: {b.x:.1f}, {b.y:.1f}; {scene.collected} crystals")

    def steer(x):
        b = scene.player.body
        delta = x-(b.x+b.w/2)-b.vx*abs(b.vx)/2400
        return {"right"} if delta > 3 else {"left"} if delta < -3 else set()

    def walk(x):
        until(f"walk {x}",lambda:abs(scene.player.body.x+12-x)<8,
              lambda:steer(x))

    def door(room_id):
        tick({"interact"})
        until("door",lambda:scene.world.current_id == room_id and not scene.transition.active,lambda:set())

    walk(184)
    walk(334)
    lift = scene.world.current.platforms[0]

    def board_lift():
        held = steer(334)
        b = scene.player.body
        if (b.on_ground and b.y > 460 and lift.box.y > 445) or (
                "jump" in previous and not b.on_ground):
            held.add("jump")
        return held

    until("board lift",lambda:scene.player.body.on_ground and scene.player.body.y < 440,board_lift)
    until("ride lift",lambda:scene.player.body.y < 288,lambda:set())
    until("upper crystal",lambda:scene.collected == 2,lambda:steer(473))
    walk(895)
    door("archive")
    walk(162)
    # Return to demonstrate persistence and a checkpoint belonging to another room.
    walk(60)
    door("atrium")
    assert scene.collected == 2
    assert scene.world.checkpoint[0] == "archive"
    walk(895)
    door("archive")
    walk(193)
    ferry = scene.world.current.platforms[0]

    def board_ferry():
        b = scene.player.body
        if b.on_ground and b.y > 460:
            if ferry.box.x < 270:
                return {"right","jump"}
            return steer(193)
        return steer(ferry.box.x+45) | {"jump"}

    until("board ferry",lambda:scene.player.body.on_ground and scene.player.body.y < 450,board_ferry)
    until("ride ferry",lambda:scene.player.body.x > 665,lambda:set())
    walk(794)
    until("goal",lambda:scene.won,lambda:{"right"})
    assert scene.collected == 4
    surface = pygame.Surface((960,576))
    scene.draw(surface,1)
    (ROOT/"artifacts").mkdir(exist_ok=True)
    pygame.image.save(surface,str(ROOT/"artifacts/rooms-completed.png"))
    print(f"Completed rooms: {ticks} steps, 4 crystals, 3 door crossings, 0 deaths.")
    if owns_scene:
        pygame.quit()


if __name__ == "__main__":
    check_route()
