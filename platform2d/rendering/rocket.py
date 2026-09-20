"""Rocket silhouettes shared by loose cargo and the assembled vehicle."""
import pygame

METAL=(178,222,231)
FUEL=(249,187,95)
GHOST=(49,68,85)

def component(surface,rect,kind,color,details=True):
    r=pygame.Rect(rect); x,y,w,h=r
    if kind=='Foguetão':
        for i,name in enumerate(('Cockpit','Depósito','Motor')):
            component(surface,(x,y+i*h/3,w,h/3),name,color,details)
    elif kind=='Motor':
        pygame.draw.polygon(surface,color,[(x+w*.25,y),(x+w*.75,y),(x+w*.78,y+h*.5),(x+w,y+h),(x+w*.65,y+h*.85),(x+w*.35,y+h*.85),(x,y+h),(x+w*.22,y+h*.5)])
        if details: pygame.draw.line(surface,(55,89,110),(x+w*.3,y+h*.6),(x+w*.7,y+h*.6),2)
    elif kind=='Cockpit':
        pygame.draw.polygon(surface,color,[(x,y+h),(x+w*.12,y+h*.45),(x+w*.5,y),(x+w*.88,y+h*.45),(x+w,y+h)])
        if details: pygame.draw.circle(surface,(43,87,115),(round(x+w*.5),round(y+h*.65)),max(2,round(w*.16)))
    else:
        pygame.draw.rect(surface,color,r,border_radius=max(2,w//6))
        if details:
            for f in (.2,.8): pygame.draw.line(surface,(55,89,110),(x+2,y+h*f),(x+w-3,y+h*f),2)

def vehicle(surface,rect,state):
    r=pygame.Rect(rect)
    layer=pygame.Surface(r.size,pygame.SRCALPHA)
    n=len(state.part_order)
    for i,ident in enumerate(state.part_order):
        segment=pygame.Rect(0,round(r.h*(n-i-1)/n),r.w,round(r.h/n))
        installed=ident in state.delivered
        kind=state.part_name(ident)
        component(layer,segment,kind,METAL if installed else GHOST,installed)
    # Clip the fuel colour to the exact silhouette, rising from the bottom.
    height=round(r.h*state.fuel_fraction)
    if height:
        tint=pygame.mask.from_surface(layer).to_surface(setcolor=(*FUEL,255),unsetcolor=(0,0,0,0))
        layer.blit(tint,(0,r.h-height),(0,r.h-height,r.w,height))
        # Keep the cockpit window readable even with a full tank.
        if n==3:
            pygame.draw.circle(layer,(43,87,115),(r.w//2,round(r.h/3*.65)),max(2,round(r.w*.16)))
    surface.blit(layer,r)
