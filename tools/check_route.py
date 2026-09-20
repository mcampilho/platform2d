"""Deterministic demo playthrough using the same actions as a human player."""
import os
from pathlib import Path
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import pygame
from platform2d.core.input import Actions
from platform2d.world.tilemap import TileMap
from examples.classic.scene import ClassicScene


def check_route():
    pygame.init()
    root = Path(__file__).resolve().parents[1]
    scene = ClassicScene(TileMap.load(root / "examples/classic/assets/station.json"),
                         json.loads((root / "examples/classic/settings.json").read_text()))
    # Support positions along the route. No teleporting or direct state changes.
    waypoints = [(330,354),(395,354),(540,290),(710,354),(765,354),
                 (860,322),(990,418),(1110,418),(1150,354),(1190,354),
                 (1320,290),(1515,354),(1640,322),(1750,418),
                 (1850,354),(1895,354),(2080,290),(2340,418)]
    index = 0
    previous = set()
    for tick in range(18000):
        body = scene.player.body
        target_x, target_y = waypoints[index]
        center = body.x + body.w/2
        error = target_x-center
        stopping = body.vx*abs(body.vx)/(2*1000)
        direction = 1 if error-stopping > 4 else -1 if error-stopping < -4 else 0
        held = {"right"} if direction > 0 else {"left"} if direction < 0 else set()
        # Hold jump during flight. Start within a safe horizontal reach.
        if (not body.on_ground and "jump" in previous) or (
                body.on_ground and target_y < body.y-5 and abs(error) < 180):
            held.add("jump")
        scene.update(1/60, Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
        previous = held
        if scene.deaths:
            raise AssertionError(f"Route died at waypoint {index}, tick {tick}")
        if abs(body.x+body.w/2-target_x) < 14 and abs(body.y-target_y) < 3 and body.on_ground:
            index = min(index+1,len(waypoints)-1)
        if scene.won:
            output = root / "artifacts" / "completed.png"
            output.parent.mkdir(exist_ok=True)
            surface = pygame.Surface((960,540))
            scene.draw(surface,1)
            pygame.image.save(surface,str(output))
            print(f"Completed route: {tick+1} simulation steps, {len(scene.collected)} crystals, {scene.deaths} deaths.")
            pygame.quit()
            return
    pygame.quit()
    raise AssertionError(f"Route stalled at waypoint {index}: {body.x:.1f}, {body.y:.1f}, crystals {scene.collected}")


if __name__ == "__main__":
    check_route()
