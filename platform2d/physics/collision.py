from dataclasses import dataclass
from math import ceil

from .body import Box


@dataclass(frozen=True)
class Collider:
    box: Box
    one_way: bool = False
    slope: int = 0  # -1 rises right (/), +1 descends right (\\); top-only.

    def __post_init__(self):
        if type(self.slope) is not int or self.slope not in (-1,0,1):
            raise ValueError("Inclinação deve ser -1, 0 ou 1.")
        if self.slope and (not self.one_way or self.box.w != self.box.h or self.box.w <= 0):
            raise ValueError("Rampas requerem um tile quadrado positivo e superfície atravessável por baixo.")

    def surface(self, x, width):
        """Highest support under a rectangular body's feet, clamped to endpoints."""
        r = self.box
        sample = x+width if self.slope < 0 else x
        fraction = max(0.,min(1.,(sample-r.x)/r.w))
        return r.y+r.h*(1-fraction if self.slope < 0 else fraction)


def move(body, colliders, dt, ignore_one_way=False):
    ramps = [c for c in colliders if c.slope]
    if not ramps:
        return _move_flat(body,colliders,dt,ignore_one_way)
    # Small steps keep slope joins continuous, including fast horizontal dashes.
    original = body.x,body.y
    flats = [c for c in colliders if not c.slope]
    steps = max(1,ceil(max(abs(body.vx*dt),abs(body.vy*dt))/4))
    contacts = [False,False,False]
    for _ in range(steps):
        _move_inclined(body,flats,ramps,dt/steps,ignore_one_way)
        contacts = [a or b for a,b in zip(contacts,(body.wall_left,body.wall_right,body.hit_ceiling))]
    body.wall_left,body.wall_right,body.hit_ceiling = contacts
    body.previous_x,body.previous_y = original


def _move_inclined(body, flats, ramps, dt, ignore):
    x,y = body.x,body.y
    feet = y+body.h
    descending = body.vy >= 0
    dx = body.vx*dt
    def overlaps(c,position):
        return position < c.box.right and position+body.w > c.box.x
    def blocked(position,top):
        candidate = Box(position,top-body.h,body.w,body.h)
        return any(candidate.overlaps(c.box) for c in flats if not c.one_way)
    grounded = body.on_ground or (descending and any(
        overlaps(c,x) and abs(feet-(c.surface(x,body.w) if c.slope else c.box.y)) < 1e-6
        for c in (*flats,*ramps) if not (c.one_way and ignore)))
    # Lift before the horizontal sweep so the adjoining high floor is not a wall.
    rising = [] if ignore or not grounded or not descending else [
        c.surface(x+dx,body.w) for c in ramps if overlaps(c,x+dx)
        and feet <= c.surface(x,body.w)+abs(dx)+1e-6
        and feet-abs(dx)-1e-6 <= c.surface(x+dx,body.w) < feet]
    ceiling_blocked = False
    if rising:
        top = min(rising)
        if blocked(x+dx,top):
            body.vx = 0
            ceiling_blocked = True
        else:
            body.y = top-body.h
    _move_flat(body,flats,dt,ignore)
    if descending and not ignore:
        candidates = []
        for c in ramps:
            if not overlaps(c,body.x) or feet > c.surface(x,body.w)+(abs(body.x-x) if grounded else 0)+1e-6:
                continue
            top = c.surface(body.x,body.w)
            crossed = body.y+body.h >= top-1e-6
            follows = grounded and top <= feet+abs(body.x-x)+1e-6
            if crossed or follows:
                candidates.append(top)
        # At the low endpoint the last corner leaves the ramp before reaching
        # the flat floor. Follow that small remaining descent without a hop.
        if grounded and any(overlaps(c,x) and abs(feet-c.surface(x,body.w)) < 1e-6 for c in ramps):
            candidates.extend(c.box.y for c in flats if overlaps(c,body.x)
                              and feet-1e-6 <= c.box.y <= feet+abs(body.x-x)+1e-6)
        if candidates:
            top = min(candidates)
            if not blocked(body.x,top) and (not body.on_ground or top <= body.y+body.h+1e-6):
                body.y = top-body.h
                body.vy = 0
                body.on_ground = True
    # Zero vertical speed after a substep must retain an actual flat support.
    if descending and not body.on_ground:
        body.on_ground = any(overlaps(c,body.x) and abs(body.y+body.h-c.box.y) < 1e-6
                             for c in flats if not (c.one_way and ignore))
    if ceiling_blocked:
        body.hit_ceiling = True
        body.wall_right |= dx > 0
        body.wall_left |= dx < 0


def _move_flat(body, colliders, dt, ignore_one_way=False):
    """Sweep each axis against static surfaces; the nearest crossing wins.

    Assumes a non-overlapping initial position. World geometry is static.
    """
    body.previous_x, body.previous_y = body.x, body.y
    body.on_ground = body.wall_left = body.wall_right = body.hit_ceiling = False
    dx = body.vx * dt
    for collider in colliders:
        r = collider.box
        if collider.one_way or not (body.y < r.bottom and body.y + body.h > r.y):
            continue
        if dx > 0 and body.x + body.w <= r.x and body.x + body.w + dx >= r.x:
            dx = min(dx, r.x - body.x - body.w)
            body.wall_right = True
        elif dx < 0 and body.x >= r.right and body.x + dx <= r.right:
            dx = max(dx, r.right - body.x)
            body.wall_left = True
    body.x += dx
    if body.wall_left or body.wall_right:
        body.vx = 0
    dy = body.vy * dt
    for collider in colliders:
        r = collider.box
        if not (body.x < r.right and body.x + body.w > r.x):
            continue
        if collider.one_way and ignore_one_way:
            continue
        if dy > 0 and body.y + body.h <= r.y + 1e-7 and body.y + body.h + dy >= r.y:
            dy = min(dy, r.y - body.y - body.h)
            body.on_ground = True
        elif not collider.one_way and dy < 0 and body.y >= r.bottom and body.y + dy <= r.bottom:
            dy = max(dy, r.bottom - body.y)
            body.hit_ceiling = True
    body.y += dy
    if body.on_ground or body.hit_ceiling:
        body.vy = 0
