"""Art-only atlas animation for the Mundo Vivo explorer."""
from pathlib import Path
from math import sin

import pygame


class AstronomerView:
    # Cell, horizontal anchor, vertical anchor, and whether it stands on a surface.
    POSES = {
        "idle": (0, .49, .93, True),
        "run_a": (1, .55, .93, True),
        "run_b": (2, .62, .93, True),
        "jump": (3, .62, .51, False),
        "fall": (4, .49, .53, False),
        "dash": (5, .64, .52, False),
        "fly": (6, .65, .54, False),
        "land": (7, .58, .92, True),
    }

    def __init__(self, path, cell_height=112):
        sheet = pygame.image.load(str(Path(path)))
        width, height = sheet.get_size()
        if width % 4 or height % 2:
            raise ValueError("Character atlas must have 4 columns and 2 rows")
        cell_width, cell_source_height = width // 4, height // 2
        target = (round(cell_width * cell_height / cell_source_height), cell_height)
        self.frames = []
        self.mirrored = []
        for index in range(8):
            cell = sheet.subsurface((index % 4 * cell_width,
                                     index // 4 * cell_source_height,
                                     cell_width, cell_source_height))
            frame = pygame.transform.smoothscale(cell, target)
            self.frames.append(frame)
            self.mirrored.append(pygame.transform.flip(frame, True, False))
        self.state = "idle"
        self.elapsed = 0
        self.landing_left = 0

    def update(self, state, dt):
        if state != self.state:
            if self.state in {"jump", "fall", "fly", "glide"} and state in {"idle", "run"}:
                self.landing_left = .12
            self.state = state
            self.elapsed = 0
        else:
            self.elapsed += dt
        self.landing_left = max(0, self.landing_left - dt)

    def draw(self, surface, body, facing=1, offset=(0, 0), alpha=1):
        if self.landing_left and self.state in {"idle", "run"}:
            pose = "land"
        elif self.state == "run":
            pose = "run_a" if int(self.elapsed * 9) % 2 == 0 else "run_b"
        elif self.state in {"dash", "fly", "jump", "fall", "idle"}:
            pose = self.state
        else:
            pose = "fall" if self.state in {"glide", "wall_slide"} else "idle"
        index, anchor_x, anchor_y, grounded = self.POSES[pose]
        frame = self.frames[index] if facing >= 0 else self.mirrored[index]
        if facing < 0:
            anchor_x = 1 - anchor_x
        x, y = body.interpolated(alpha)
        target_x = x + body.w / 2 - offset[0]
        target_y = y + (body.h if grounded else body.h / 2) - offset[1]
        if pose == "idle":
            target_y += sin(self.elapsed * 3.2) * .8
        left = round(target_x - anchor_x * frame.get_width())
        top = round(target_y - anchor_y * frame.get_height())
        surface.blit(frame, (left, top))
        return pygame.Rect(left, top, *frame.get_size())
