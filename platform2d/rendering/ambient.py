"""Small, deterministic ambient animations clipped to a world-space region."""
from math import sin

import pygame


def draw_ambient(surface, region, camera, time, kind):
    """Draw quiet water bubbles or gravity motes without changing game state."""
    if kind not in {"water", "gravity_zone"}:
        raise ValueError(f"Unknown ambient region: {kind}")
    cx, cy = camera
    rect = pygame.Rect(round(region.x - cx), round(region.y - cy),
                       round(region.w), round(region.h))
    visible = rect.clip(surface.get_rect())
    if visible.width == 0 or visible.height == 0:
        return
    old_clip = surface.get_clip()
    surface.set_clip(old_clip.clip(visible))
    try:
        spacing = 46 if kind == "water" else 74
        first = max(0, int((cx - region.x) // spacing) - 1)
        last = min(int(region.w // spacing) + 2,
                   int((cx + surface.get_width() - region.x) // spacing) + 2)
        for index in range(first, last):
            phase = index * 2.39996
            if kind == "water":
                travel = (time * (17 + index % 4 * 3) + index * 31) % max(1, region.h)
                x = region.x + index * spacing + 11 + sin(time * 1.5 + phase) * 6 - cx
                y = region.y + region.h - travel - cy
                radius = 2 + index % 3
                pygame.draw.circle(surface, (110, 178, 185),
                                   (round(x), round(y)), radius, 1)
                if radius > 2:
                    pygame.draw.circle(surface, (168, 211, 199),
                                       (round(x - 1), round(y - 1)), 1)
            else:
                x = region.x + index * spacing + 19 + sin(time * .55 + phase) * 9 - cx
                y = region.y + 24 + (index * 53) % max(1, region.h - 24)
                y += sin(time * .9 + phase) * 8 - cy
                pygame.draw.circle(surface, (138, 117, 167),
                                   (round(x), round(y)), 2 if index % 3 else 3)
    finally:
        surface.set_clip(old_clip)
