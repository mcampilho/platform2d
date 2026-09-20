"""Shared visual convention for top-only ramps in games and the editor."""
import pygame


def draw_ramp(surface, rect, slope):
    x,y,w,h = rect
    start,end = ((x,y+h),(x+w,y)) if slope < 0 else ((x,y),(x+w,y+h))
    pygame.draw.polygon(surface,(33,65,75),[start,end,(x+w,y+h) if slope < 0 else (x,y+h)])
    pygame.draw.line(surface,(245,198,111),start,end,max(2,round(w/12)))
