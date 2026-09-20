"""Pushable rigid crates and weight plates; independent of campaign rules."""
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider,move


def object_box(obj): return Box(obj['x'],obj['y'],obj.get('w',48),obj.get('h',48))


class Cargo:
    def __init__(self,objects):
        self.crates={o['id']:Body(o['x'],o['y'],o.get('w',48),o.get('h',48)) for o in objects if o['type']=='crate'}
        self.plates=[o for o in objects if o['type']=='plate']

    def active(self,player=None):
        active=set()
        for plate in self.plates:
            r=object_box(plate); weight=0
            for b,mass in [(b,2) for b in self.crates.values()]+([(player,1)] if player else []):
                if abs(b.box.bottom-r.bottom)<=2 and r.x<=b.x+b.w/2<=r.right:
                    weight+=mass
            if weight>=plate.get('weight',2): active.add(plate['id'])
        return active

    def colliders(self): return [Collider(b.box) for b in self.crates.values()]

    def update(self,dt,player,direction,solids,width):
        # No chain pushing. Falling crates collide with the player rather than
        # embedding them; gates use the same safe obstruction rule in the host.
        for b in sorted(self.crates.values(),key=lambda b:b.y,reverse=True):
            others=[Collider(o.box) for o in self.crates.values() if o is not b]
            support=any(b.x<c.box.right and b.box.right>c.box.x and abs(b.box.bottom-c.box.y)<.01 for c in [*solids,*others])
            touching=(0<=b.x-player.box.right<=3 if direction>0 else 0<=player.x-b.box.right<=3)
            side=player.y<b.box.bottom-2 and player.box.bottom>b.y+2
            b.vx=direction*90 if direction and touching and side and support and player.on_ground else 0
            b.vy=min(600,b.vy+1200*dt)
            move(b,[*solids,*others,Collider(player.box)],dt)
            b.x=max(0,min(width-b.w,b.x))

    def freeze(self):
        for b in self.crates.values(): b.previous_x,b.previous_y=b.x,b.y

    def snapshot(self): return {key:[b.x,b.y] for key,b in self.crates.items()}

    def restore(self,state,solids,width,height):
        from math import isfinite
        if not isinstance(state,dict) or state.keys()!=self.crates.keys(): raise ValueError('Gravação: caixas incompatíveis.')
        candidate={}
        for key,pos in state.items():
            if not isinstance(pos,list) or len(pos)!=2 or any(type(v) not in (int,float) or not isfinite(v) for v in pos):
                raise ValueError('Gravação: posição de caixa inválida.')
            original=self.crates[key]; b=Body(*pos,original.w,original.h)
            if b.x<0 or b.y<0 or b.box.right>width or b.box.bottom>height:
                raise ValueError('Gravação: caixa fora do mapa.')
            if any(b.box.overlaps(c.box) for c in solids if not c.one_way) or any(b.box.overlaps(o.box) for o in candidate.values()):
                raise ValueError('Gravação: caixas sobrepostas a sólidos ou entre si.')
            candidate[key]=b
        self.crates=candidate
