"""Small procedural character rig. Reads action phases; never advances gameplay."""
from math import sin,cos,pi
import pygame


def sword_pose(sword,health):
    if health.immune_left>max(0,health.invulnerability-.18): return 'hurt',0
    if sword.stunned>0: return 'stagger',0
    if sword.blocking: return 'guard',0
    attack=sword.attack; spec=attack.spec
    if attack.running or attack.active:
        if attack.elapsed<spec.startup: return 'windup',attack.elapsed/max(.001,spec.startup)
        if attack.active: return 'strike',min(1,max(0,(attack.elapsed-spec.startup)/spec.active))
        return 'recover',min(1,max(0,(attack.elapsed-spec.startup-spec.active)/max(.001,spec.recovery)))
    return 'idle',0


def draw_actor(surface,position,facing=1,phase='idle',progress=0,clock=0,guardian=False,reach=48,reduced=False):
    x,y=position; direction=1 if facing>=0 else -1
    suit=(177,89,118) if guardian else (103,221,196)
    light=(235,172,162) if guardian else (179,246,224)
    dark=(75,43,73) if guardian else (34,84,91)
    if phase=='hurt': suit=(234,137,127); light=(255,218,174)
    stride=sin(clock*13)*5 if phase=='run' else 0
    bob=0 if reduced else sin(clock*4)*.6 if phase=='idle' else abs(stride)*.15
    lean={'carry':0,'windup':-3*progress,'strike':4,'recover':4*(1-progress),'guard':-2,'hurt':-5,'stagger':-3}.get(phase,0)
    crouch=3 if phase in {'guard','stagger'} else 0
    def point(px,py): return round(x+12+(px-12)*direction),round(y+py+bob)
    def line(color,a,b,width=3): pygame.draw.line(surface,color,point(*a),point(*b),width)
    def poly(color,points): pygame.draw.polygon(surface,color,[point(*p) for p in points])
    # Feet stay near the collision body's base while the upper body articulates.
    for hip,knee,foot in [((9,18),(8-stride*.5,24),(6-stride,29)),((15,18),(16+stride*.5,24),(19+stride,29))]:
        line(dark,hip,knee,4); line(suit,knee,foot,4); line(dark,(foot[0]-2,29),(foot[0]+3,29),3)
    if guardian:
        poly(dark,[(5+lean,6+crouch),(3,25),(16,24),(16+lean,7+crouch)])
    else:
        poly(dark,[(3+lean,5+crouch),(7+lean,5+crouch),(7+lean,18+crouch),(2+lean,18+crouch)])
    poly(suit,[(6+lean,5+crouch),(18+lean,5+crouch),(19,19),(7,19)])
    line(light,(7+lean,7+crouch),(17+lean,7+crouch),2)
    line(dark,(7,19),(18,19),3)
    # Helmet and visor retain the explorer palette; the guardian has a crest.
    poly(light,[(6+lean,-5+crouch),(17+lean,-5+crouch),(21+lean,0+crouch),(20+lean,7+crouch),(5+lean,7+crouch),(3+lean,1+crouch)])
    line(dark,(10+lean,1+crouch),(21+lean,1+crouch),4)
    line((239,251,242),(16+lean,0+crouch),(20+lean,0+crouch),1)
    if guardian: poly((217,117,106),[(7+lean,-5+crouch),(10+lean,-13+crouch),(18+lean,-11+crouch),(15+lean,-5+crouch)])
    shoulder=(17+lean,10+crouch)
    if phase=='carry':
        for start,elbow,hand in [((7,10),(1,4),(0,-8)),((18,10),(24,4),(24,-8))]:
            line(suit,start,elbow,3); line(light,elbow,hand,3)
        return
    if phase=='guard': elbow=(22,17); hand=(28,9); tip=(28,-15)
    elif phase=='windup': elbow=(13,11); hand=(12,-1); tip=(3-8*progress,-23)
    elif phase=='strike': elbow=(26,12); hand=(32,12); tip=(24+reach,12)
    elif phase=='recover': elbow=(25-5*progress,15); hand=(30-6*progress,14+3*progress); tip=(24+reach*(1-progress),15+12*progress)
    elif phase in {'hurt','stagger'}: elbow=(13,19); hand=(19,24); tip=(35,29)
    else: elbow=(21,17); hand=(24,19); tip=(36,28)
    line(dark,(7+lean,10+crouch),(5-stride*.3,19),3)
    line(suit,shoulder,elbow,4); line(light,elbow,hand,3)
    if phase=='strike' and not reduced:
        for offset in (-6,-3): line((120,108,80),(hand[0],hand[1]+offset),(tip[0]-4,tip[1]+offset),1)
    blade=(255,194,102) if phase=='windup' else (255,239,184) if phase=='strike' else (167,210,225)
    line(blade,hand,tip,3)
    line((233,181,110),(hand[0]-3,hand[1]-3),(hand[0]+3,hand[1]+3),2)


def draw_impact(surface,position,life,kind):
    """Short non-flashing radial marks; lifetime is owned by the scene."""
    x,y=position; t=1-life/.18
    color=(137,241,215) if kind=='parry' else (255,204,125) if kind=='block' else (245,141,133)
    for i in range(6):
        angle=i*pi/3; inner=3+t*5; outer=inner+5*(1-t)
        pygame.draw.line(surface,color,(round(x+cos(angle)*inner),round(y+sin(angle)*inner)),(round(x+cos(angle)*outer),round(y+sin(angle)*outer)),2)
