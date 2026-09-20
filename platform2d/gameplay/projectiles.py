"""Straight projectiles and cooldowns; no Pygame, rendering or game rules."""
from dataclasses import dataclass
from math import hypot,isfinite

from platform2d.physics.body import Box


def number(value,low,high,label):
    if type(value) not in (int,float) or not low <= value <= high or not isfinite(value):
        raise ValueError(f"{label}: valor entre {low:g} e {high:g} obrigatório.")


@dataclass(frozen=True)
class WeaponSpec:
    speed: float = 620
    cooldown: float = .24
    lifetime: float = 1.5
    damage: int = 1
    width: float = 10
    height: float = 4

    def __post_init__(self):
        for key,low,high in (("speed",1,10000),("cooldown",.02,30),("lifetime",.001,30),
                             ("width",1,128),("height",1,128)):
            number(getattr(self,key),low,high,key)
        if type(self.damage) is not int or not 1 <= self.damage <= 100:
            raise ValueError("Dano: inteiro entre 1 e 100 obrigatório.")


@dataclass(frozen=True)
class Target:
    id: str
    team: str
    box: Box
    previous: Box | None = None


@dataclass(frozen=True)
class Impact:
    projectile_id: int
    owner: str
    team: str
    target_id: str | None  # None means solid terrain.
    point: tuple[float,float]
    damage: int
    direction: tuple[float,float]


@dataclass
class Projectile:
    id: int
    owner: str
    team: str
    x: float
    y: float
    vx: float
    vy: float
    spec: WeaponSpec
    remaining: float

    def __post_init__(self):
        self.previous_x,self.previous_y = self.x,self.y

    def interpolated(self,alpha):
        return (self.previous_x+(self.x-self.previous_x)*alpha,
                self.previous_y+(self.y-self.previous_y)*alpha)


def crossing(origin,delta,box):
    """First segment/rectangle contact, expressed as a fraction in [0, 1]."""
    enter,leave = 0.,1.
    for value,change,low,high in ((origin[0],delta[0],box.x,box.right),
                                  (origin[1],delta[1],box.y,box.bottom)):
        if abs(change) < 1e-12:
            if not low <= value <= high:
                return None
        else:
            a,b = (low-value)/change,(high-value)/change
            enter,leave = max(enter,min(a,b)),min(leave,max(a,b))
            if enter > leave:
                return None
    return enter


class ProjectileSystem:
    def __init__(self,capacity=128):
        if type(capacity) is not int or not 1 <= capacity <= 4096:
            raise ValueError("Capacidade de projéteis: inteiro entre 1 e 4096.")
        self.capacity = capacity
        self.items = []
        self.next_id = 1

    def spawn(self,origin,direction,owner,team,spec):
        if not isinstance(spec,WeaponSpec):
            raise ValueError("É necessária uma WeaponSpec.")
        if not isinstance(owner,str) or not owner or not isinstance(team,str) or not team:
            raise ValueError("Autor e equipa devem ser textos não vazios.")
        if len(origin) != 2 or len(direction) != 2:
            raise ValueError("Origem e direção precisam de duas coordenadas.")
        for value in (*origin,*direction):
            number(value,-1e9,1e9,"Coordenada")
        length = hypot(*direction)
        if length == 0:
            raise ValueError("A direção do disparo não pode ser nula.")
        if len(self.items) >= self.capacity:
            return None
        projectile = Projectile(self.next_id,owner,team,*origin,
                                direction[0]/length*spec.speed,direction[1]/length*spec.speed,spec,spec.lifetime)
        self.next_id += 1
        self.items.append(projectile)
        return projectile

    def clear(self):
        self.items.clear()

    def freeze(self):
        for p in self.items:
            p.previous_x,p.previous_y = p.x,p.y

    def update(self,dt,colliders=(),targets=()):
        number(dt,0,30,"Passo de simulação")
        if dt == 0:
            return []
        impacts,survivors = [],[]
        targets = tuple(targets)
        solids = [c.box for c in colliders if not c.one_way]
        for p in self.items:
            p.previous_x,p.previous_y = p.x,p.y
            travel = min(dt,p.remaining)
            delta = p.vx*travel,p.vy*travel
            first,target_id = None,None
            def expanded(box):
                return Box(box.x-p.spec.width/2,box.y-p.spec.height/2,
                           box.w+p.spec.width,box.h+p.spec.height)
            # Test terrain first; a wall wins a tie with an overlapping target.
            for box in solids:
                contact = crossing((p.x,p.y),delta,expanded(box))
                if contact is not None and (first is None or contact < first):
                    first = contact
            for target in targets:
                if target.id == p.owner or target.team == p.team:
                    continue
                old = target.previous or target.box
                fraction = travel/dt
                relative = (delta[0]-(target.box.x-old.x)*fraction,
                            delta[1]-(target.box.y-old.y)*fraction)
                contact = crossing((p.x,p.y),relative,expanded(old))
                if contact is not None and (first is None or contact < first-1e-10):
                    first,target_id = contact,target.id
            if first is not None:
                point = p.x+delta[0]*first,p.y+delta[1]*first
                impacts.append(Impact(p.id,p.owner,p.team,target_id,point,p.spec.damage,(p.vx/p.spec.speed,p.vy/p.spec.speed)))
                continue
            p.x,p.y = p.x+delta[0],p.y+delta[1]
            p.remaining -= dt
            if p.remaining > 1e-10:
                survivors.append(p)
        self.items = survivors
        return impacts


class Weapon:
    def __init__(self,spec=None):
        self.spec = spec or WeaponSpec()
        self.remaining = 0.

    def update(self,dt):
        number(dt,0,30,"Passo da arma")
        self.remaining = max(0.,self.remaining-dt)

    def reset(self):
        self.remaining = 0.

    def fire(self,system,origin,direction,owner,team):
        if self.remaining > 1e-10:
            return None
        projectile = system.spawn(origin,direction,owner,team,self.spec)
        if projectile is not None:
            self.remaining = self.spec.cooldown
        return projectile
