"""Optional precision movement. Static wall/ladder sensors; shared collision solver."""
from dataclasses import dataclass
from math import hypot, isfinite

from .controller import ArcadeController


@dataclass(frozen=True)
class Abilities:
    dash: bool = True
    wall_jump: bool = True
    ladders: bool = True
    double_jump: bool = False
    glide: bool = False
    dash_speed: float = 650
    dash_duration: float = .18
    dash_cooldown: float = .15
    wall_jump_speed: float = 280
    wall_jump_height: float = 430
    wall_lock: float = .12
    wall_slide_speed: float = 85
    climb_speed: float = 125
    glide_fall_speed: float = 110

    def __post_init__(self):
        for name in ("dash","wall_jump","ladders","double_jump","glide"):
            if type(getattr(self,name)) is not bool:
                raise ValueError(f"Capacidade {name}: usa true ou false.")
        for name,value in vars(self).items():
            if name in {"dash","wall_jump","ladders","double_jump","glide"}:
                continue
            if type(value) not in (int,float) or not isfinite(value) or value <= 0:
                raise ValueError(f"Capacidade {name}: valor finito positivo obrigatório.")


class PrecisionController(ArcadeController):
    def __init__(self, config=None, abilities=None):
        self.abilities = abilities or Abilities()
        self.colliders = ()
        self.ladders = ()
        super().__init__(config)

    def reset(self):
        super().reset()
        self.dash_left = self.cooldown_left = self.wall_lock_left = self.ladder_lock = 0.0
        self.dash_ready = True
        self.dash_direction = (1,0)
        self.wall_velocity = 0
        self.ladder = None
        self.extra_jump_used = False

    def interrupt(self):
        ready,cooldown = self.dash_ready,self.cooldown_left
        self.reset()
        self.dash_ready,self.cooldown_left = ready,cooldown

    def prepare(self, colliders, ladders=()):
        self.colliders,self.ladders = colliders,ladders

    def wall_side(self, body):
        for collider in self.colliders:
            r = collider.box
            if collider.one_way or not (body.y < r.bottom and body.y+body.h > r.y):
                continue
            if abs(body.x+body.w-r.x) <= 1:
                return 1
            if abs(body.x-r.right) <= 1:
                return -1
        return 0

    def available_ladder(self, body, vertical):
        center = body.x+body.w/2
        for ladder in self.ladders:
            if (ladder.x <= center <= ladder.right and body.y <= ladder.bottom and
                    body.y+body.h >= ladder.y-1 and
                    not (vertical < 0 and body.y+body.h <= ladder.y+1)):
                return ladder
        return None

    def before_physics(self, body, actions, dt):
        a = self.abilities
        self.motion_state = None
        self.cooldown_left = max(0,self.cooldown_left-dt)
        self.ladder_lock = max(0,self.ladder_lock-dt)
        self.wall_lock_left = max(0,self.wall_lock_left-dt)
        vertical = actions.axis("up","down")
        direction = actions.axis()
        if body.on_ground:
            self.extra_jump_used = False
        # One charge, restored by actual ground contact; ladders and walls don't refill.
        if body.on_ground and self.dash_left <= 0:
            self.dash_ready = True
        if (a.dash and "dash" in actions.pressed and self.dash_ready and
                self.cooldown_left <= 0 and self.dash_left <= 0):
            dx,dy = direction,vertical
            if dx == 0 and dy == 0:
                dx = self.facing
            length = hypot(dx,dy)
            self.dash_direction = (dx/length,dy/length)
            self.dash_left = a.dash_duration
            self.motion_events += ("dash",)
            self.dash_ready = False
            self.ladder = None
            self.ladder_lock = .2
            self.wall_lock_left = self.coyote = self.buffer = self.drop_timer = 0
            if dx:
                self.facing = 1 if dx > 0 else -1
        if self.dash_left > 0:
            fraction = min(1,self.dash_left/dt)
            body.vx = self.dash_direction[0]*a.dash_speed*fraction
            body.vy = self.dash_direction[1]*a.dash_speed*fraction
            self.dash_left = max(0,self.dash_left-dt)
            self.motion_state = "dash"
            body.on_ground = False
            return
        if a.ladders:
            if self.ladder is None and vertical and self.ladder_lock <= 0:
                self.ladder = self.available_ladder(body,vertical)
            if self.ladder is not None:
                r = self.ladder
                center = body.x+body.w/2
                if not (r.x-1 <= center <= r.right+1 and body.y <= r.bottom and body.y+body.h >= r.y-1):
                    self.ladder = None
                elif "jump" in actions.pressed:
                    self.motion_events += ("jump",)
                    self.ladder = None
                    self.ladder_lock = .2
                    self.coyote = self.buffer = 0
                    body.vy = -self.config.jump_speed
                    if "jump" not in actions.held:
                        body.vy = -self.config.jump_cut
                    body.vx = direction*self.config.speed
                    if direction:
                        self.facing = direction
                    body.on_ground = False
                    return
                else:
                    # Align by swept motion, never teleport across geometry.
                    body.vx = max(-a.climb_speed,min(a.climb_speed,(r.x+r.w/2-center)/dt))
                    body.vy = vertical*a.climb_speed
                    if vertical < 0:
                        body.vy = max(body.vy,(r.y-body.h-body.y)/dt)
                    self.drop_timer = dt*2
                    self.coyote = self.buffer = 0
                    self.motion_state = "climb"
                    body.on_ground = False
                    return
        side = self.wall_side(body) if a.wall_jump else 0
        wall_jump = bool(side and not body.on_ground and "jump" in actions.pressed)
        double_jump = bool(a.double_jump and not body.on_ground and self.coyote <= 0
                           and not side and not self.extra_jump_used and "jump" in actions.pressed)
        super().before_physics(body,actions,dt)
        if wall_jump:
            self.motion_events += ("jump",)
            body.vx = -side*a.wall_jump_speed
            body.vy = -a.wall_jump_height if "jump" in actions.held else -self.config.jump_cut
            body.on_ground = False
            self.wall_velocity = body.vx
            self.wall_lock_left = a.wall_lock
            self.facing = -side
            self.coyote = self.buffer = 0
        elif double_jump:
            self.jump(body)
            self.extra_jump_used = True
        elif self.wall_lock_left > 0:
            body.vx = self.wall_velocity
            self.facing = 1 if self.wall_velocity > 0 else -1
        elif side and direction == side and not body.on_ground and body.vy > 0:
            body.vy = min(body.vy,a.wall_slide_speed)
            self.motion_state = "wall_slide"
        if a.glide and "glide" in actions.held and not body.on_ground and body.vy > 0:
            body.vy = min(body.vy,a.glide_fall_speed)
            self.motion_state = "glide"

    def after_physics(self, body):
        landed = body.on_ground
        if self.motion_state == "dash":
            dx,dy = self.dash_direction
            blocked = (dx != 0 and (body.wall_left or body.wall_right) or
                       dy < 0 and body.hit_ceiling or dy > 0 and body.on_ground)
            if blocked:
                self.dash_left = 0
            if self.dash_left <= 0:
                self.cooldown_left = self.abilities.dash_cooldown
                body.vx = max(-self.config.speed,min(body.vx,self.config.speed))
                body.vy = max(-self.config.jump_speed,min(body.vy,self.config.terminal_speed))
        elif self.motion_state == "climb":
            if self.ladder and (landed or body.y+body.h <= self.ladder.y+1e-6 or body.y >= self.ladder.bottom):
                self.ladder = None
                self.ladder_lock = .15
                self.drop_timer = 0
                self.motion_state = None
                body.vy = 0
        else:
            super().after_physics(body)
        if landed and self.dash_left <= 0:
            self.dash_ready = True
