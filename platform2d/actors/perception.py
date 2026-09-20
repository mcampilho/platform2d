"""Facing, range, field of view and solid-obstacle line of sight."""
from math import cos, hypot, radians


def segment_hits_box(start, end, box):
    low, high = 0.0, 1.0
    for origin, delta, minimum, maximum in (
        (start[0],end[0]-start[0],box.x,box.right),
        (start[1],end[1]-start[1],box.y,box.bottom),
    ):
        if abs(delta) < 1e-10:
            if origin < minimum or origin > maximum:
                return False
        else:
            a,b = (minimum-origin)/delta,(maximum-origin)/delta
            low,high = max(low,min(a,b)),min(high,max(a,b))
            if low > high:
                return False
    return True


def can_see(observer, target, facing, colliders, distance=200, fov=110):
    if distance <= 0 or not 0 < fov <= 180:
        raise ValueError("Perceção: alcance positivo e campo de visão entre 0 e 180 graus.")
    start = (observer.x+observer.w/2,observer.y+observer.h/2)
    end = (target.x+target.w/2,target.y+target.h/2)
    dx,dy = end[0]-start[0],end[1]-start[1]
    length = hypot(dx,dy)
    if length > distance:
        return False
    if length > 1e-8 and dx*facing/length < cos(radians(fov/2)):
        return False
    return not any(segment_hits_box(start,end,c.box) for c in colliders if not c.one_way)
