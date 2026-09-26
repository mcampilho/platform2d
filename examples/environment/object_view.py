"""Observatory props. Appearance is separate from collision and interaction."""
import pygame


COPPER = (166, 132, 85)
BRIGHT_COPPER = (223, 181, 111)
TEAL = (108, 193, 162)
MUTED = (87, 121, 126)
STONE = (25, 45, 52)


def draw_checkpoint(surface, x, y, active):
    x, y = round(x), round(y)
    pygame.draw.ellipse(surface, (16, 33, 39), (x - 3, y + 27, 29, 7))
    pygame.draw.rect(surface, STONE, (x + 6, y - 6, 10, 36), border_radius=3)
    pygame.draw.line(surface, COPPER, (x + 7, y - 4), (x + 7, y + 27), 2)
    color = TEAL if active else MUTED
    pygame.draw.polygon(surface, color,
                        ((x + 11, y - 18), (x + 20, y - 9),
                         (x + 11, y), (x + 2, y - 9)))
    pygame.draw.polygon(surface, BRIGHT_COPPER,
                        ((x + 11, y - 18), (x + 20, y - 9),
                         (x + 11, y), (x + 2, y - 9)), 2)
    if active:
        pygame.draw.circle(surface, (222, 244, 198), (x + 11, y - 9), 2)


def draw_goal(surface, x, y, width, height, unlocked):
    rect = pygame.Rect(round(x), round(y), round(width), round(height))
    inner = rect.inflate(-10, -10)
    pygame.draw.rect(surface, STONE, rect, border_radius=rect.width // 2)
    pygame.draw.rect(surface, COPPER, rect, 3, border_radius=rect.width // 2)
    pygame.draw.rect(surface, (11, 29, 36), inner, border_radius=inner.width // 2)
    pygame.draw.rect(surface, TEAL if unlocked else MUTED, inner, 2,
                     border_radius=inner.width // 2)
    if unlocked:
        pygame.draw.line(surface, (130, 203, 176),
                         (inner.centerx, inner.y + 8),
                         (inner.centerx, inner.bottom - 6), 2)
        pygame.draw.circle(surface, (217, 223, 164), (inner.centerx, inner.centery), 3)
    else:
        pygame.draw.circle(surface, (133, 112, 89), inner.center, 3)
    for side in (rect.left + 4, rect.right - 5):
        pygame.draw.circle(surface, BRIGHT_COPPER, (side, rect.y + 22), 1)


def draw_gate(surface, rect, opened):
    rect = pygame.Rect(rect)
    inner = rect.inflate(-10, -10)
    if opened:
        pygame.draw.rect(surface, (25, 48, 50), (rect.x, rect.y, 5, rect.height))
        pygame.draw.rect(surface, (25, 48, 50), (rect.right - 5, rect.y, 5, rect.height))
        pygame.draw.rect(surface, (25, 48, 50), (rect.x, rect.y, rect.width, 5))
        pygame.draw.rect(surface, (25, 48, 50), (rect.x, rect.bottom - 5, rect.width, 5))
        pygame.draw.rect(surface, TEAL, rect, 2, border_radius=5)
        pygame.draw.line(surface, (112, 186, 155),
                         (inner.left, inner.y + 6), (inner.left, inner.bottom - 6), 1)
        pygame.draw.circle(surface, (174, 228, 180), (rect.centerx, rect.y + 12), 3)
    else:
        pygame.draw.rect(surface, STONE, rect, border_radius=5)
        pygame.draw.rect(surface, COPPER, rect, 3, border_radius=5)
        pygame.draw.rect(surface, (46, 60, 61), inner)
        for bar in range(inner.left + 3, inner.right, 7):
            pygame.draw.line(surface, (111, 88, 72),
                             (bar, inner.top), (bar, inner.bottom), 2)
        pygame.draw.circle(surface, BRIGHT_COPPER, rect.center, 5)
        pygame.draw.circle(surface, (53, 56, 53), rect.center, 2)
    for top in (rect.y + 18, rect.bottom - 18):
        pygame.draw.circle(surface, BRIGHT_COPPER, (rect.centerx, top), 2)


def draw_switch(surface, rect, active):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, STONE, rect, border_radius=6)
    pygame.draw.rect(surface, COPPER, rect, 2, border_radius=6)
    center = (rect.centerx, rect.y + 14)
    pygame.draw.circle(surface, (77, 88, 78), center, 11)
    pygame.draw.circle(surface, BRIGHT_COPPER, center, 10, 2)
    pygame.draw.circle(surface, TEAL if active else (234, 179, 89), center, 6)
    pygame.draw.line(surface, (22, 45, 47), center,
                     (center[0] + (4 if active else -4), center[1] - 4), 2)
    for x in (rect.left + 5, rect.right - 6):
        pygame.draw.circle(surface, BRIGHT_COPPER, (x, rect.bottom - 6), 1)
