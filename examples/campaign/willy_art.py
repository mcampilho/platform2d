"""Cached, hand-drawn mine art for the lost-keys level."""
from math import pi,sin

import pygame


STONE=(38,34,55)
STONE_LIGHT=(81,76,103)
STONE_DARK=(22,20,36)
MOSS=(71,104,77)
GOLD=(250,202,91)


def _surface(size=(32,32)):
    return pygame.Surface(size,pygame.SRCALPHA)


def stone_tile(size,variant=0,platform=False):
    image=_surface((size,size))
    pygame.draw.rect(image,STONE,(0,0,size,size))
    pygame.draw.rect(image,STONE_DARK,(2,5,size-4,size-7),border_radius=4)
    pygame.draw.polygon(image,(52,48,72),[(3,6),(size-3,4),(size-6,size-5),(5,size-3)])
    pygame.draw.line(image,STONE_LIGHT,(2,3),(size-3,3),2)
    if platform:
        pygame.draw.rect(image,MOSS,(1,1,size-2,5),border_radius=2)
        pygame.draw.line(image,(116,143,92),(3,2),(size-5,2),1)
        pygame.draw.polygon(image,(45,41,61),[(0,9),(size,7),(size,size),(0,size)])
    crack_x=(9,17,23,13)[variant%4]
    pygame.draw.lines(image,(28,26,43),False,[(crack_x,8),(crack_x-3,15),(crack_x+2,21)],1)
    pygame.draw.circle(image,(99,93,117),((variant*7+6)%25+3,(variant*11+15)%24+4),1)
    return image


def crumble_tile(size,variant=0):
    image=_surface((size,size))
    pygame.draw.rect(image,(111,78,61),(1,2,size-2,size-4),border_radius=3)
    pygame.draw.rect(image,(171,122,77),(2,2,size-4,5),border_radius=2)
    pygame.draw.lines(image,(53,40,43),False,[(5,7),(13,14),(10,23),(17,size-2)],2)
    pygame.draw.lines(image,(62,43,43),False,[(26,5),(20,13),(24,19),(19,27)],2)
    pygame.draw.circle(image,(222,169,96),(7+variant*5%20,12+variant*3%13),2)
    return image


def conveyor_tile(size):
    image=_surface((size,size))
    pygame.draw.rect(image,(26,42,52),(0,2,size,size-4),border_radius=4)
    pygame.draw.rect(image,(72,115,119),(1,3,size-2,size-6),2,border_radius=4)
    pygame.draw.rect(image,(41,67,76),(2,7,size-4,15),border_radius=3)
    for x in (7,16,25):
        pygame.draw.circle(image,(17,29,38),(x,25),4)
        pygame.draw.circle(image,(112,160,153),(x,25),2)
    pygame.draw.line(image,(119,218,198),(2,6),(size-3,6),2)
    return image


def guardian_walk_frames(sprite):
    """Build two facing directions with a small alternating stone stride."""
    frames={-1:[],1:[]}
    width,height=sprite.get_size()
    split=round(height*.62)
    half=width//2
    for facing in (1,-1):
        source=sprite if facing>0 else pygame.transform.flip(sprite,True,False)
        torso=source.subsurface((0,0,width,split+5)).copy()
        rear=source.subsurface((0,split,half,height-split)).copy()
        front=source.subsurface((half,split,width-half,height-split)).copy()
        for index in range(8):
            wave=sin(index*pi/4)
            bob=round(abs(wave))
            stride=round(wave*3)
            rear_lift=round(max(0,wave)*3)
            front_lift=round(max(0,-wave)*3)
            # Keep the canvas flush with the original feet. Extra transparent
            # pixels below it would make the guardian appear to float even
            # though its collision box is standing on the conveyor.
            image=_surface((width+8,height))
            # Separate feet make the walking direction visible even at the
            # compact gameplay scale; the torso hides the cut between parts.
            image.blit(rear,(4-stride,split-rear_lift))
            image.blit(front,(4+half+stride,split-front_lift))
            image.blit(torso,(4,bob))
            frames[facing].append(image)
    return frames


def bush_sway_frames(sprite):
    """Pre-render a gentle bottom-anchored sway; no transforms during play."""
    frames=[]
    for angle in (-2,-1,0,1,2,1,0,-1):
        turned=pygame.transform.rotozoom(sprite,angle,1)
        image=_surface((sprite.get_width()+6,sprite.get_height()+5))
        image.blit(turned,((image.get_width()-turned.get_width())//2,
                           image.get_height()-turned.get_height()))
        frames.append(image)
    return frames


def draw_key(surface,rect,time,sprite):
    center=(round(rect.x+rect.w/2),round(rect.y+rect.h/2))
    pulse=round((1+__import__('math').sin(time*4+rect.x))*.7)
    glow=_surface((44,44))
    pygame.draw.circle(glow,(255,197,70,22),(22,22),16+pulse)
    pygame.draw.circle(glow,(255,220,112,35),(22,22),10+pulse)
    surface.blit(glow,(center[0]-22,center[1]-22))
    surface.blit(sprite,(round(rect.x+(rect.w-sprite.get_width())/2),
                         round(rect.y+(rect.h-sprite.get_height())/2)))
    # A brief travelling glint draws the eye without making the key flash
    # continuously. Position offsets keep multiple keys out of sync.
    cycle=(time+rect.x*.013+rect.y*.007)%2.8
    if cycle<.48:
        progress=cycle/.48
        strength=sin(progress*pi)
        x=round(rect.x-3+progress*(rect.w+6))
        y=round(rect.y+rect.h*.28-progress*4)
        radius=max(1,round(5*strength))
        color=(255,244,183)
        pygame.draw.line(surface,color,(x-radius,y),(x+radius,y),1)
        pygame.draw.line(surface,color,(x,y-radius),(x,y+radius),1)
        pygame.draw.circle(surface,(255,255,226),(x,y),1)


def draw_bush(surface,rect,sprite):
    surface.blit(sprite,(round(rect.x+(rect.w-sprite.get_width())/2),
                         round(rect.bottom-sprite.get_height())))


def draw_stalactite(surface,rect):
    pygame.draw.polygon(surface,(34,30,49),[(rect.x,rect.y),(rect.right,rect.y),(rect.x+19,rect.bottom),(rect.x+14,rect.y+22)])
    pygame.draw.polygon(surface,(106,91,126),[(rect.x+5,rect.y),(rect.x+21,rect.y),(rect.x+17,rect.bottom-4)])
    pygame.draw.line(surface,(179,134,153),(rect.x+8,rect.y+3),(rect.x+17,rect.bottom-7),2)


def draw_exit(surface,rect,ready):
    frame=(179,143,78) if ready else (83,72,98)
    pygame.draw.rect(surface,(25,22,38),(rect.x,rect.y,rect.w,rect.h),border_radius=10)
    pygame.draw.rect(surface,frame,(rect.x,rect.y,rect.w,rect.h),4,border_radius=10)
    pygame.draw.rect(surface,(48,42,62),(rect.x+10,rect.y+10,rect.w-20,rect.h-10),border_radius=7)
    for y in range(round(rect.y+16),round(rect.bottom-6),12):
        pygame.draw.line(surface,(74,62,79),(rect.x+13,y),(rect.right-13,y),2)
    pygame.draw.circle(surface,GOLD if ready else (91,75,90),(round(rect.right-16),round(rect.y+rect.h/2)),3)


def draw_patrol(surface,rect,sprite):
    surface.blit(sprite,(round(rect.x+(rect.w-sprite.get_width())/2),
                         round(rect.bottom-sprite.get_height()+3)))
