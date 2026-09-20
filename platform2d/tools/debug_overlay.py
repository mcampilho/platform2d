import pygame


def draw_debug(surface, font, body, state, colliders, camera, tile_size):
    cx, cy = camera
    for x in range(-round(cx) % tile_size, surface.get_width(), tile_size):
        pygame.draw.line(surface, (41, 58, 78), (x, 0), (x, surface.get_height()))
    for y in range(-round(cy) % tile_size, surface.get_height(), tile_size):
        pygame.draw.line(surface, (41, 58, 78), (0, y), (surface.get_width(), y))
    for collider in colliders:
        b = collider.box
        if collider.slope:
            left = collider.surface(b.x,0)
            right = collider.surface(b.right,0)
            pygame.draw.line(surface,(255,192,84),(b.x-cx,left-cy),(b.right-cx,right-cy),2)
        else:
            pygame.draw.rect(surface, (255, 192, 84), (b.x-cx, b.y-cy, b.w, b.h), 1)
    pygame.draw.rect(surface, (255, 100, 157), (body.x-cx, body.y-cy, body.w, body.h), 1)
    lines = [f"STATE {state.upper()} | POS {body.x:.1f}, {body.y:.1f}",
             f"VEL {body.vx:.1f}, {body.vy:.1f} | GROUND {body.on_ground}",
             f"LEFT {body.wall_left} | RIGHT {body.wall_right} | CEILING {body.hit_ceiling}"]
    panel = pygame.Surface((570, 80), pygame.SRCALPHA)
    panel.fill((6, 13, 25, 235))
    surface.blit(panel, (18, 105))
    for index, line in enumerate(lines):
        surface.blit(font.render(line, True, (191, 225, 239)), (28, 114 + index*22))
