"""Ground patrol with sight, last-seen pursuit, search and damage states."""
from platform2d.core.input import Actions
from platform2d.gameplay.combat import Health
from .character import Character
from .controller import ArcadeController, Movement
from .perception import can_see
from .state_machine import State, StateMachine


class PatrolEnemy:
    def __init__(self, enemy_id, body, left, right, facing=-1):
        if left >= right or not left <= body.x <= right:
            raise ValueError("Patrulha: limites inválidos ou posição fora do percurso.")
        self.id = enemy_id
        self.character = Character(body,ArcadeController(Movement(speed=70)))
        self.direction = 1 if facing >= 0 else -1
        self.character.controller.facing = self.direction
        self.left,self.right = left,right
        self.health = Health(2,0.25)
        self.visible = False
        self.last_seen = None
        self.memory = 0
        self.intent = 0
        self.machine = StateMachine(self,{
            "patrol":State(update=lambda e,dt:e.patrol()),
            "chase":State(update=lambda e,dt:e.chase()),
            "search":State(update=lambda e,dt:e.search()),
            "hurt":State(update=lambda e,dt:e.recover()),
            "dead":State(enter=lambda e:e.stop()),
        },"patrol")

    @property
    def body(self):
        return self.character.body

    def stop(self):
        self.intent = 0
        self.body.vx = self.body.vy = 0

    def patrol(self):
        if self.visible:
            self.machine.change("chase")
            self.chase()
            return
        if self.body.x <= self.left:
            self.direction = 1
        elif self.body.x >= self.right:
            self.direction = -1
        self.intent = self.direction

    def chase(self):
        if not self.visible and self.memory <= 0:
            self.machine.change("search")
            return
        dx = self.last_seen-(self.body.x+self.body.w/2)
        self.intent = 1 if dx > 8 else -1 if dx < -8 else 0
        if self.intent:
            self.direction = self.intent

    def search(self):
        self.intent = 0
        if self.visible:
            self.machine.change("chase")
        elif self.machine.elapsed >= .7:
            self.machine.change("patrol")

    def recover(self):
        self.intent = 0
        if self.character.stun_left <= 0:
            self.machine.change("patrol")

    def hit(self, damage, direction):
        if not self.health.hit(damage):
            return False
        if self.health.dead:
            self.machine.change("dead")
        else:
            self.character.knockback(direction*155)
            self.machine.change("hurt")
        return True

    def update(self, dt, target, colliders):
        self.health.update(dt)
        if self.health.dead:
            self.visible = False
            return
        self.visible = can_see(self.body,target,self.character.controller.facing,colliders)
        self.memory = max(0,self.memory-dt)
        if self.visible:
            self.last_seen = target.x+target.w/2
            self.memory = .55
        self.intent = 0
        self.machine.update(dt)
        self.character.controller.config.speed = 110 if self.machine.current == "chase" else 70
        # Avoid a ledge in the intended direction, even during pursuit.
        if self.intent and self.body.on_ground:
            probe = self.body.x+self.body.w+8 if self.intent > 0 else self.body.x-8
            on_ramp = any(c.slope and self.body.x < c.box.right and self.body.box.right > c.box.x
                          and abs(self.body.box.bottom-c.surface(self.body.x,self.body.w)) < 1e-5 for c in colliders)
            supported = any(c.box.x <= probe <= c.box.right and
                            (abs((c.surface(probe,0) if c.slope else c.box.y)-self.body.box.bottom) <= self.body.w+8
                             if c.slope or on_ramp else 0 <= c.box.y-self.body.box.bottom <= 8) for c in colliders)
            if not supported or self.body.wall_left or self.body.wall_right:
                self.direction = -self.intent
                self.intent = 0
                self.body.vx = 0
        held = frozenset({"right" if self.intent > 0 else "left"}) if self.intent else frozenset()
        self.character.update(dt,Actions(held),colliders)
