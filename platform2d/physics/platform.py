"""Kinematic top-only platforms. Advance once per world step, before actors."""
from dataclasses import dataclass
from math import hypot, isfinite

from .body import Box
from .collision import Collider, move


@dataclass
class MovingPlatform:
    id: str
    start: tuple[float, float]
    end: tuple[float, float]
    w: float
    h: float = 12
    speed: float = 60

    def __post_init__(self):
        values = (*self.start, *self.end, self.w, self.h, self.speed)
        if not all(type(v) in (int, float) and isfinite(v) for v in values):
            raise ValueError("Plataforma: coordenadas, dimensões e velocidade devem ser finitas.")
        self.length = hypot(self.end[0]-self.start[0], self.end[1]-self.start[1])
        if self.w <= 0 or self.h <= 0 or self.speed <= 0 or self.length == 0:
            raise ValueError("Plataforma: dimensões e velocidade positivas e percurso não vazio são obrigatórios.")
        self.distance = 0.0
        self.box = Box(*self.start, self.w, self.h)
        self.previous = self.box

    def update(self, dt):
        self.previous = self.box
        self.distance = (self.distance + self.speed*dt) % (2*self.length)
        fraction = min(self.distance, 2*self.length-self.distance)/self.length
        self.box = Box(self.start[0]+(self.end[0]-self.start[0])*fraction,
                       self.start[1]+(self.end[1]-self.start[1])*fraction, self.w, self.h)

    def interpolated(self, alpha):
        return Box(self.previous.x+(self.box.x-self.previous.x)*alpha,
                   self.previous.y+(self.box.y-self.previous.y)*alpha, self.w, self.h)


def move_with_platforms(body, colliders, platforms, dt, ignore_one_way=False):
    """Carry riders, resolve static geometry, then test relative top crossings.

    Platforms have no solid sides or undersides. Upward crushing against static
    ceilings is reported on the body; the game decides the consequence.
    """
    original_x, original_y = body.x, body.y
    old_bottom = body.y + body.h
    body.crushed = False
    if not ignore_one_way and body.on_ground and body.vy >= 0:
        for platform in platforms:
            old, new = platform.previous, platform.box
            if (abs(old_bottom-old.y) < 1e-5 and body.x < old.right and body.x+body.w > old.x):
                vx, vy = body.vx, body.vy
                dx, dy = new.x-old.x, new.y-old.y
                body.vx, body.vy = dx/dt, dy/dt
                move(body, colliders, dt)
                body.crushed = dy < 0 and body.y > original_y+dy+1e-5
                body.vx, body.vy = vx, vy
                break
    # Final top surfaces also support riders on descending platforms.
    surfaces = list(colliders) + [Collider(p.box, True) for p in platforms]
    move(body, surfaces, dt, ignore_one_way)
    if not ignore_one_way and not body.crushed:
        for platform in sorted(platforms, key=lambda p: p.box.y):
            old, new = platform.previous, platform.box
            if (old_bottom <= old.y+1e-7 and body.y+body.h >= new.y and
                    body.x < new.right and body.x+body.w > new.x):
                target_y = new.y-body.h
                candidate = Box(body.x, target_y, body.w, body.h)
                if any(candidate.overlaps(c.box) for c in colliders if not c.one_way):
                    body.crushed = True
                else:
                    body.y = target_y
                    body.vy = 0
                    body.on_ground = True
                break
    body.previous_x, body.previous_y = original_x, original_y
