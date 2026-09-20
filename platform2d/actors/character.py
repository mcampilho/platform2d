from platform2d.physics.collision import move
from platform2d.physics.platform import move_with_platforms
from .controller import ArcadeController


class Character:
    def __init__(self, body, controller=None):
        self.body = body
        self.controller = controller or ArcadeController()
        self.stun_left = 0.0

    @property
    def state(self):
        if self.controller.motion_state:
            return self.controller.motion_state
        if not self.body.on_ground:
            return "jump" if self.body.vy < 0 else "fall"
        return "run" if abs(self.body.vx) > 8 else "idle"

    def update(self, dt, actions, colliders, platforms=(), *, ladders=()):
        was_grounded,fall_speed = self.body.on_ground,self.body.vy
        self.controller.motion_events = ()
        self.controller.prepare(colliders, ladders)
        if self.stun_left > 0:
            self.stun_left = max(0,self.stun_left-dt)
            config = self.controller.config
            self.body.vy = min(self.body.vy+config.gravity*dt,config.terminal_speed)
        else:
            self.controller.before_physics(self.body, actions, dt)
        if platforms:
            move_with_platforms(self.body, colliders, platforms, dt, self.controller.drop_timer > 0)
        else:
            self.body.crushed = False
            move(self.body, colliders, dt, self.controller.drop_timer > 0)
        self.controller.after_physics(self.body)
        if not was_grounded and self.body.on_ground and fall_speed > 30:
            self.controller.motion_events += ("land",)

    def knockback(self, vx, vy=-160, duration=0.18):
        self.controller.interrupt()
        self.body.vx, self.body.vy = vx, vy
        self.body.on_ground = False
        self.stun_left = duration

    def respawn(self, position):
        self.body.teleport(*position)
        self.controller.reset()
        self.stun_left = 0.0
