from dataclasses import dataclass
from math import isfinite


@dataclass
class Movement:
    speed: float = 230
    acceleration: float = 1500
    friction: float = 1900
    air_control: float = 0.7
    gravity: float = 1200
    jump_speed: float = 440
    jump_cut: float = 170
    terminal_speed: float = 800
    coyote_time: float = 0.10
    jump_buffer: float = 0.12

    def __post_init__(self):
        for name, value in vars(self).items():
            if type(value) not in (int, float) or not isfinite(value) or value < 0:
                raise ValueError(f"Movimento: {name} deve ser um número finito não negativo.")
        if not 0 <= self.air_control <= 1:
            raise ValueError("Movimento: air_control deve estar entre 0 e 1.")
        if self.gravity == 0 or self.jump_speed == 0 or self.terminal_speed == 0:
            raise ValueError("Movimento: gravity, jump_speed e terminal_speed devem ser positivos.")
        if self.jump_cut > self.jump_speed:
            raise ValueError("Movimento: jump_cut não pode exceder jump_speed.")


def approach(value, target, amount):
    return min(value + amount, target) if value < target else max(value - amount, target)


class ArcadeController:
    def __init__(self, config=None):
        self.config = config or Movement()
        self.reset()

    def reset(self):
        self.motion_events = ()
        self.coyote = self.buffer = self.drop_timer = 0.0
        self.facing = 1
        self.jump_held = False
        self.motion_state = None

    def prepare(self, colliders, ladders=()):
        """Optional environment hook. The arcade controller needs no sensors."""

    def interrupt(self):
        self.reset()

    def jump(self, body):
        self.motion_events += ("jump",)
        body.vy = -self.config.jump_speed
        if not self.jump_held:
            body.vy = max(body.vy, -self.config.jump_cut)
        body.on_ground = False
        self.coyote = self.buffer = 0

    def before_physics(self, body, actions, dt):
        c = self.config
        self.coyote = c.coyote_time if body.on_ground else max(0, self.coyote - dt)
        self.buffer = max(0, self.buffer - dt)
        self.drop_timer = max(0, self.drop_timer - dt)
        self.jump_held = "jump" in actions.held
        if "jump" in actions.pressed:
            if "down" in actions.held:
                self.drop_timer = 0.22
                self.buffer = self.coyote = 0
            else:
                self.buffer = c.jump_buffer
        direction = actions.axis()
        if direction:
            self.facing = direction
        rate = c.acceleration if direction else c.friction
        rate *= 1 if body.on_ground else c.air_control
        body.vx = approach(body.vx, direction * c.speed, rate * dt)
        if self.buffer > 0 and self.coyote > 0:
            self.jump(body)
        if "jump" in actions.released and body.vy < -c.jump_cut:
            body.vy = -c.jump_cut
        body.vy = min(body.vy + c.gravity * dt, c.terminal_speed)

    def after_physics(self, body):
        if body.on_ground and self.buffer > 0:
            self.jump(body)
