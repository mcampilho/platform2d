from dataclasses import dataclass

import pygame


def slice_sheet(sheet, frame_size):
    w, h = frame_size
    if w <= 0 or h <= 0 or sheet.get_width() % w or sheet.get_height() % h:
        raise ValueError("A spritesheet deve ser divisível pelo tamanho dos frames.")
    return [sheet.subsurface((x, y, w, h)).copy()
            for y in range(0, sheet.get_height(), h)
            for x in range(0, sheet.get_width(), w)]


@dataclass(frozen=True)
class Clip:
    frames: tuple[int, ...]
    fps: float = 8
    loop: bool = True

    def __post_init__(self):
        if not self.frames or self.fps <= 0:
            raise ValueError("Uma animação precisa de frames e fps positivo.")


class SpriteView:
    def __init__(self, frames, clips):
        self.frames, self.clips = frames, clips
        self.current = next(iter(clips))
        self.elapsed = 0

    def update(self, state, dt):
        if state != self.current:
            self.current, self.elapsed = state, 0
        else:
            self.elapsed += dt

    def draw(self, surface, position, facing=1):
        clip = self.clips[self.current]
        index = int(self.elapsed * clip.fps)
        index = index % len(clip.frames) if clip.loop else min(index, len(clip.frames) - 1)
        image = self.frames[clip.frames[index]]
        if facing < 0:
            image = pygame.transform.flip(image, True, False)
        surface.blit(image, (round(position[0]), round(position[1])))
