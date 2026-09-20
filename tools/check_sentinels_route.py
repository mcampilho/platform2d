"""Complete briefing, combat, terminal and exit using only player Actions."""
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
from examples.sentinels.scene import SentinelsScene
from platform2d.core.input import Actions
from platform2d.world.tilemap import TileMap


def check_route():
    pygame.init()
    level = TileMap(json.loads((ROOT/"examples/sentinels/assets/outpost.json").read_text(encoding="utf-8")),
                    {"enemy","npc","switch","gate"})
    scene = SentinelsScene(level,json.loads((ROOT/"examples/sentinels/settings.json").read_text()))
    previous = set()
    ticks = 0

    def tick(held):
        nonlocal previous,ticks
        held = set(held)
        scene.update(1/60,Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
        previous = held
        ticks += 1
        if scene.deaths:
            raise AssertionError(f"Player died at tick {ticks}; defeated {scene.defeated}")

    def until(label,condition,policy,limit=1800):
        for _ in range(limit):
            if condition():
                return
            tick(policy())
        raise AssertionError(f"{label} stalled at x={scene.player.body.x:.1f}, health={scene.health.remaining}, guards={scene.defeated}")

    until("approach NPC",lambda:scene.player.body.x > 110,lambda:{"right"})
    tick({"interact"})
    for _ in range(3):
        tick(set())
        tick({"interact"})
    assert scene.briefed

    def fight():
        enemy = next(e for e in scene.enemies if not e.health.dead)
        b = scene.player.body
        delta = enemy.body.x-b.x
        gap = abs(delta)-b.w
        held = set()
        if gap > 30:
            held.add("right" if delta > 0 else "left")
        if gap < 36 and not scene.attack.running and scene.player.stun_left <= 0:
            if scene.player.controller.facing == (1 if delta >= 0 else -1):
                held.add("attack")
            else:
                held.add("right" if delta > 0 else "left")
        return held

    until("first guard",lambda:len(scene.defeated) == 1,fight)
    until("approach cover",lambda:scene.player.body.x > 500,lambda:{"right"})
    tick({"right","jump"})
    until("jump over cover",lambda:scene.player.body.x > 592,lambda:{"right","jump"})
    until("second guard",lambda:len(scene.defeated) == 2,fight)
    until("terminal",lambda:scene.player.body.x > 816,lambda:{"right"})
    tick({"interact"})
    assert scene.gate_open
    until("exit",lambda:scene.won,lambda:{"right"})
    surface = pygame.Surface((960,576))
    scene.draw(surface,1)
    (ROOT/"artifacts").mkdir(exist_ok=True)
    pygame.image.save(surface,str(ROOT/"artifacts/sentinels-completed.png"))
    print(f"Completed Sentinels: {ticks} steps, briefing, 2 guards defeated, gate opened, 0 deaths, health {scene.health.remaining}/3.")
    pygame.quit()


if __name__ == "__main__":
    check_route()
