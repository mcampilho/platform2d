"""Screen-edge guidance for important world points outside the viewport."""

import math

import pygame


class ObjectiveGuide:
    """Draw one unobtrusive direction marker without changing game state."""

    def __init__(self,color=(132,229,214),margin=18):
        self.color=tuple(color)
        self.margin=margin

    def marker(self,point,viewport):
        """Return marker centre and direction, or ``None`` when already visible."""
        viewport=pygame.Rect(viewport)
        inner=viewport.inflate(-2*self.margin,-2*self.margin)
        if inner.collidepoint(point): return None
        cx,cy=viewport.center; dx,dy=point[0]-cx,point[1]-cy
        if dx==0 and dy==0: return None
        limit_x=inner.w/2/abs(dx) if dx else float('inf')
        limit_y=inner.h/2/abs(dy) if dy else float('inf')
        scale=min(limit_x,limit_y)
        length=math.hypot(dx,dy); direction=(dx/length,dy/length)
        return (cx+dx*scale,cy+dy*scale),direction

    def draw(self,surface,point,viewport,age=0,reduced=False):
        marker=self.marker(point,viewport)
        if marker is None: return False
        (x,y),(dx,dy)=marker; px,py=-dy,dx
        pulse=0 if reduced else math.sin(age*5)*2
        tip=(x+dx*(8+pulse),y+dy*(8+pulse))
        back=(x-dx*7,y-dy*7)
        points=[tip,(back[0]+px*6,back[1]+py*6),(back[0]-px*6,back[1]-py*6)]
        pygame.draw.circle(surface,(10,25,36),(round(x),round(y)),13)
        pygame.draw.circle(surface,self.color,(round(x),round(y)),13,2)
        pygame.draw.polygon(surface,self.color,points)
        return True
