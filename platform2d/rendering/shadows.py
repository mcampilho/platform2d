"""Bounded screen-space shadows from rectangular world occluders."""
from math import hypot, isfinite

import pygame


def _hull(points):
    """Small monotone-chain hull for an occluder and its projected corners."""
    points = sorted(set(points))
    if len(points) < 3:
        return points

    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    lower = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def shadow_polygon(light, box, length=300):
    """Project a box away from a point light; return world-space polygon."""
    if type(length) not in (int, float) or not isfinite(length) or length <= 0:
        raise ValueError("Shadow length must be a finite positive number")
    lx, ly = light
    if box.x <= lx <= box.right and box.y <= ly <= box.bottom:
        return ()
    corners = ((box.x, box.y), (box.right, box.y),
               (box.right, box.bottom), (box.x, box.bottom))
    points = list(corners)
    for x, y in corners:
        dx, dy = x - lx, y - ly
        distance = hypot(dx, dy)
        if distance:
            points.append((x + dx / distance * length,
                           y + dy / distance * length))
    return tuple(_hull(points))


def draw_shadows(surface, light, boxes, offset=(0, 0), *, radius=240, length=310,
                 color=(6, 13, 27, 68), max_occluders=96):
    """Draw nearby solid shadows without changing the game world."""
    lx, ly = light
    nearby = []
    for box in boxes:
        dx = max(box.x - lx, 0, lx - box.right)
        dy = max(box.y - ly, 0, ly - box.bottom)
        distance_sq = dx * dx + dy * dy
        if distance_sq <= radius * radius:
            nearby.append((distance_sq, box))
    if not nearby:
        return
    nearby.sort(key=lambda item: item[0])
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    ox, oy = offset
    bounds = pygame.Rect(-length, -length,
                         surface.get_width() + 2 * length,
                         surface.get_height() + 2 * length)
    for _, box in nearby[:max_occluders]:
        polygon = shadow_polygon(light, box, length)
        if len(polygon) < 3:
            continue
        points = [(round(x - ox), round(y - oy)) for x, y in polygon]
        if any(bounds.collidepoint(point) for point in points):
            pygame.draw.polygon(layer, color, points)
    surface.blit(layer, (0, 0))
