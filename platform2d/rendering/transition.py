"""Reusable transitions which never change simulation state."""

import math

import pygame


class FadeTransition:
    def __init__(self, half_duration=0.18):
        if half_duration <= 0:
            raise ValueError("A duração da transição deve ser positiva.")
        self.half_duration = half_duration
        self.elapsed = 0
        self.active = False
        self.callback = None

    def start(self, callback):
        if self.active:
            return False
        self.elapsed = 0
        self.callback = callback
        self.active = True
        return True

    def update(self, dt):
        if not self.active:
            return
        self.elapsed += dt
        if self.elapsed >= self.half_duration and self.callback is not None:
            callback, self.callback = self.callback, None
            callback()
        if self.elapsed >= 2*self.half_duration:
            self.active = False

    @property
    def opacity(self):
        if not self.active:
            return 0
        return round(255*max(0, 1-abs(self.elapsed/self.half_duration-1)))


class MomentTransitions:
    """Short presentation cues for scene entry, checkpoints and completion."""

    def __init__(self,enabled=True):
        self.enabled=enabled
        self.kind=None
        self.elapsed=0.0
        self.duration=0.0
        self.origin=None

    @property
    def active(self):
        return self.kind is not None

    @property
    def progress(self):
        return min(1.0,self.elapsed/self.duration) if self.active and self.duration else 1.0

    def clear(self):
        self.kind=None; self.elapsed=0.0; self.duration=0.0; self.origin=None

    def _start(self,kind,duration,origin=None):
        if not self.enabled:
            self.clear(); return False
        self.kind=kind; self.elapsed=0.0; self.duration=duration; self.origin=origin
        return True

    def enter(self,duration=.42):
        return self._start('enter',duration)

    def checkpoint(self,origin,duration=.6):
        return self._start('checkpoint',duration,origin)

    def complete(self,duration=.85):
        return self._start('complete',duration)

    def update(self,dt):
        if not self.active: return
        self.elapsed+=max(0,dt)
        if self.elapsed>=self.duration: self.clear()

    def draw(self,surface):
        if not self.enabled or not self.active: return
        width,height=surface.get_size(); p=self.progress
        layer=pygame.Surface((width,height),pygame.SRCALPHA)
        if self.kind=='enter':
            # A quick curtain reveal. The world is already fully drawn beneath it.
            alpha=round(255*(1-p)**2)
            layer.fill((6,15,27,alpha)); surface.blit(layer,(0,0))
        elif self.kind=='checkpoint':
            x,y=self.origin or (width//2,height//2)
            # Keep checkpoint feedback local. A full-screen alpha layer here
            # caused a visible hitch on integrated/older graphics hardware.
            radius=round(18+142*p); padding=8
            alpha=round(190*(1-p)**1.5)
            diameter=2*(radius+padding)
            ring=pygame.Surface((diameter,diameter),pygame.SRCALPHA)
            center=radius+padding
            pygame.draw.circle(ring,(127,235,222,alpha),(center,center),radius,max(2,round(7*(1-p))))
            inner=max(2,radius-round(12+8*math.sin(math.pi*p)))
            pygame.draw.circle(ring,(80,220,196,alpha//3),(center,center),inner,2)
            surface.blit(ring,(round(x)-center,round(y)-center))
        elif self.kind=='complete':
            # The bars settle behind the existing results panel.
            eased=1-(1-p)**3; bar=round(height*.075*eased)
            pygame.draw.rect(layer,(5,13,24,210),(0,0,width,bar))
            pygame.draw.rect(layer,(5,13,24,210),(0,height-bar,width,bar))
            layer.fill((112,239,207,round(20*math.sin(math.pi*p))),special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(layer,(0,0))
