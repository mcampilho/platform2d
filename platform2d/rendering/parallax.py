"""Three procedural depth layers, driven only by camera position."""
import pygame
from math import floor


def draw_parallax(surface,camera,theme='station'):
    x,y=camera
    surface.fill((12,20,37) if theme!='reactor' else (29,18,33))
    width,height=surface.get_size()
    for i in range(65):
        px=(i*173-x*.12)%(width+40)-20
        py=(i*97-y*.12)%(height+40)-20
        pygame.draw.circle(surface,(74,102,135),(round(px),round(py)),1)
    for i,(mx,my,radius) in enumerate([(175,75,24),(680,150,38),(450,255,15)]):
        px=(mx-x*.12+100)%(width+200)-100
        py=my-y*.12
        pygame.draw.circle(surface,(45+i*9,64+i*7,89+i*6),(round(px),round(py)),radius)
    for factor,spacing,color,base in [(.3,280,(26,45,64),190),(.6,180,(41,64,80),310)]:
        offset=x*factor%spacing
        vertical=y*factor
        start=floor(x*factor/spacing)
        for i in range(-1,width//spacing+2):
            px=i*spacing-offset
            top=base-vertical+((i+start)%3)*29
            if theme=='reactor':
                pygame.draw.rect(surface,color,(px+spacing*.2,top,spacing*.6,height-top))
                pygame.draw.rect(surface,tuple(c+12 for c in color),(px+spacing*.15,top,spacing*.7,12))
                pygame.draw.rect(surface,(18,25,41),(px+spacing*.35,top+35,spacing*.3,100),border_radius=24)
            else:
                pygame.draw.polygon(surface,color,[(px-100,height),(px+spacing/2,top),(px+spacing+100,height)])
                pygame.draw.line(surface,tuple(min(255,c+12) for c in color),(px+spacing/2,top),(px+spacing/2+35,top+75),2)
