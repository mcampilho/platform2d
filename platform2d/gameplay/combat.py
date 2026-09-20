"""Health and one-hit-per-target attack windows, independent of animation."""
from dataclasses import dataclass, field
from math import isfinite

from platform2d.physics.body import Box


@dataclass
class Health:
    maximum: int = 3
    invulnerability: float = 0.8
    remaining: int = field(init=False)
    immune_left: float = field(default=0, init=False)

    def __post_init__(self):
        if type(self.maximum) is not int or self.maximum <= 0 or not isfinite(self.invulnerability) or self.invulnerability < 0:
            raise ValueError("Vida: máximo inteiro positivo e invulnerabilidade não negativa.")
        self.remaining = self.maximum

    @property
    def dead(self):
        return self.remaining == 0

    def update(self, dt):
        self.immune_left = max(0,self.immune_left-dt)

    def hit(self, damage=1):
        if type(damage) is not int or damage <= 0:
            raise ValueError("O dano deve ser um inteiro positivo.")
        if self.dead or self.immune_left > 0:
            return False
        self.remaining = max(0,self.remaining-damage)
        self.immune_left = self.invulnerability
        return True

    def restore(self):
        self.remaining = self.maximum
        self.immune_left = 0

    def heal(self,amount):
        if type(amount) is not int or amount <= 0:
            raise ValueError("A recuperação deve ser um inteiro positivo.")
        if self.dead or self.remaining == self.maximum:
            return False
        self.remaining = min(self.maximum,self.remaining+amount)
        return True


@dataclass(frozen=True)
class AttackSpec:
    startup: float = 0.08
    active: float = 0.10
    recovery: float = 0.22
    reach: float = 42
    damage: int = 1

    def __post_init__(self):
        if any(not isfinite(v) or v < 0 for v in (self.startup,self.active,self.recovery,self.reach)) or self.active == 0 or self.reach == 0:
            raise ValueError("Ataque: durações não negativas; janela ativa e alcance positivos.")
        if type(self.damage) is not int or self.damage <= 0:
            raise ValueError("Ataque: dano inteiro positivo.")


class Attack:
    def __init__(self, spec=None):
        self.spec = spec or AttackSpec()
        self.cancel()

    def cancel(self):
        self.elapsed = 0.0
        self.running = self.active = False
        self.targets = set()
        self.facing = 1

    def start(self, facing):
        if self.running:
            return False
        self.elapsed = 0
        self.running = True
        self.active = False
        self.targets.clear()
        self.facing = 1 if facing >= 0 else -1
        return True

    def update(self, dt):
        self.active = False
        if not self.running:
            return
        before = self.elapsed
        self.elapsed += dt
        # Interval overlap prevents losing short attack windows between steps.
        self.active = self.elapsed > self.spec.startup and before < self.spec.startup+self.spec.active
        if self.elapsed >= self.spec.startup+self.spec.active+self.spec.recovery:
            self.running = False

    def box(self, body):
        x = body.x+body.w if self.facing > 0 else body.x-self.spec.reach
        return Box(x,body.y+3,self.spec.reach,max(1,body.h-6))

    def connects(self, target_id, attacker, hurtbox, blockers=()):
        if not self.active or target_id in self.targets or not self.box(attacker).overlaps(hurtbox):
            return False
        from platform2d.actors.perception import segment_hits_box
        start = (attacker.x+attacker.w/2,attacker.y+attacker.h/2)
        end = (hurtbox.x+hurtbox.w/2,hurtbox.y+hurtbox.h/2)
        if any(segment_hits_box(start,end,c.box) for c in blockers if not c.one_way):
            return False
        self.targets.add(target_id)
        return True
