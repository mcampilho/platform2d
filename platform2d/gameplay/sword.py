"""Directional sword defence; timing and stamina independent of rendering/AI."""
from .combat import Attack,AttackSpec

class Sword:
    def __init__(self,spec=None):
        self.attack=Attack(spec or AttackSpec(.16,.12,.32,48,1))
        self.stamina=100.0
        self.blocking=False
        self.guard_time=0.0
        self.stunned=0.0
        self.result=''

    def update(self,dt,body,facing,guard=False,strike=False):
        self.result=''
        self.stunned=max(0,self.stunned-dt)
        was=self.blocking
        self.blocking=bool(guard and body.on_ground and not self.attack.running and self.stunned<=0 and self.stamina>0)
        self.guard_time=self.guard_time+dt if self.blocking and was else dt if self.blocking else 0
        if self.blocking:
            self.stamina=max(0,self.stamina-18*dt)
            if self.stamina==0:
                self.blocking=False; self.stunned=.65; self.result='break'
        else:
            self.stamina=min(100,self.stamina+22*dt)
        if strike and not guard and self.stunned<=0 and body.on_ground:
            self.attack.start(facing)
        self.attack.update(dt)

    def defend(self,body,facing,source):
        """Return hit/block/parry/break. A rear attack bypasses the guard."""
        if not self.blocking or (source.x+source.w/2-body.x-body.w/2)*facing<0:
            self.result='hit'; return self.result
        if self.guard_time<=.18:
            self.result='parry'
        elif self.stamina>=28:
            self.stamina-=28; self.result='block'
        else:
            self.stamina=0; self.blocking=False; self.stunned=.65; self.result='break'
        return self.result

    def interrupt(self,duration=.3):
        self.attack.cancel(); self.blocking=False
        self.stunned=max(self.stunned,duration)
