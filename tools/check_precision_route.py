"""Complete the precision course through input, including all three abilities."""
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
from examples.precision.scene import PrecisionScene
from platform2d.core.input import Actions
from platform2d.world.tilemap import TileMap


def check_route(scene=None,step=None):
    pygame.init()
    owns_scene = scene is None
    if owns_scene:
        level = TileMap(json.loads((ROOT/"examples/precision/assets/ascent.json").read_text(encoding="utf-8")),{"ladder","beacon"})
        scene = PrecisionScene(level,json.loads((ROOT/"examples/precision/settings.json").read_text()))
    step = step or (lambda action:scene.update(1/60,action))
    previous = set()
    ticks = 0
    trace = []

    def tick(held):
        nonlocal previous,ticks
        held = set(held)
        step(Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
        previous = held
        ticks += 1
        b = scene.player.body
        trace.append((ticks,round(b.x,1),round(b.y,1),scene.wall_jumps,sorted(held)))
        if scene.deaths:
            raise AssertionError(f"Death at {ticks}; signals={scene.collected}; trace={trace[-15:]}")

    def until(label,condition,policy,limit=1800):
        for _ in range(limit):
            if condition():
                return
            tick(policy())
        b = scene.player.body
        raise AssertionError(f"{label} stalled at {b.x:.1f}, {b.y:.1f}; jumps={scene.wall_jumps}")

    def steer(x):
        b = scene.player.body
        delta = x-(b.x+b.w/2)-b.vx*abs(b.vx)/2400
        return {"right"} if delta > 3 else {"left"} if delta < -3 else set()

    until("ladder approach",lambda:abs(scene.player.body.x+12-248)<5,lambda:steer(248))
    until("ladder top",lambda:scene.player.body.y <= 290.01,lambda:{"up"})
    until("takeoff",lambda:scene.player.body.x > 416,lambda:{"right"})
    tick({"right","jump"})
    for _ in range(17):
        tick({"right","jump"})
    tick({"right","dash","jump"})
    until("second signal",lambda:"dash_beacon" in scene.collected,lambda:{"right","jump"})
    until("shaft entry",lambda:scene.player.body.x > 985 and scene.player.body.on_ground,lambda:{"right"})
    tick({"right"})
    tick({"right","jump"})
    heading = 1

    def wall_policy():
        nonlocal heading
        c,b = scene.player.controller,scene.player.body
        if b.y+b.h <= 224.001:
            if b.on_ground and "jump" in previous:
                return {"right"}
            return {"right","jump"}
        side = c.wall_side(b)
        if side and c.wall_lock_left <= 0:
            if "jump" in previous:
                return {"right" if side > 0 else "left"}
            heading = -side
            return {"right" if heading > 0 else "left","jump"}
        return {"right" if heading > 0 else "left","jump"}

    until("wall ascent",lambda:scene.player.body.x >= 1090 and scene.player.body.y < 224,wall_policy)
    until("summit",lambda:scene.won,lambda:{"right"})
    assert len(scene.collected) == 3 and scene.wall_jumps >= 2 and scene.dashes >= 1 and scene.climb_time > .5
    surface = pygame.Surface((960,576))
    scene.draw(surface,1)
    (ROOT/"artifacts").mkdir(exist_ok=True)
    pygame.image.save(surface,str(ROOT/"artifacts/precision-completed.png"))
    print(f"Completed precision: {ticks} steps, 3 signals, {scene.dashes} dash, {scene.wall_jumps} wall jumps, {scene.climb_time:.2f}s climbing, 0 deaths.")
    if owns_scene:
        pygame.quit()


if __name__ == "__main__":
    check_route()
