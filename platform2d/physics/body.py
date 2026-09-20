from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self):
        return self.x + self.w

    @property
    def bottom(self):
        return self.y + self.h

    def overlaps(self, other):
        return (self.x < other.right and self.right > other.x and
                self.y < other.bottom and self.bottom > other.y)


@dataclass
class Body:
    x: float
    y: float
    w: float = 24
    h: float = 30
    vx: float = 0
    vy: float = 0
    on_ground: bool = False
    wall_left: bool = False
    wall_right: bool = False
    hit_ceiling: bool = False
    crushed: bool = False

    def __post_init__(self):
        self.previous_x, self.previous_y = self.x, self.y

    @property
    def box(self):
        return Box(self.x, self.y, self.w, self.h)

    def teleport(self, x, y):
        self.x = self.previous_x = float(x)
        self.y = self.previous_y = float(y)
        self.vx = self.vy = 0
        self.on_ground = self.wall_left = self.wall_right = self.hit_ceiling = False
        self.crushed = False

    def interpolated(self, alpha):
        return (self.previous_x + (self.x - self.previous_x) * alpha,
                self.previous_y + (self.y - self.previous_y) * alpha)
