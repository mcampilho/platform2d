from math import exp


class Camera:
    def __init__(self, viewport, bounds):
        self.width, self.height = viewport
        self.bounds = bounds
        self.x = self.y = self.previous_x = self.previous_y = 0.0

    def follow(self, body, dt, snap=False):
        target_x = body.x + body.w / 2 - self.width / 2 + body.vx * 0.18
        target_y = body.y + body.h / 2 - self.height * 0.58
        target_x = max(0, min(target_x, max(0, self.bounds[0] - self.width)))
        target_y = max(0, min(target_y, max(0, self.bounds[1] - self.height)))
        self.previous_x, self.previous_y = self.x, self.y
        factor = 1 if snap else 1 - exp(-7 * dt)
        self.x += (target_x - self.x) * factor
        self.y += (target_y - self.y) * factor
        if snap:
            self.previous_x, self.previous_y = self.x, self.y

    def interpolated(self, alpha):
        return (self.previous_x + (self.x - self.previous_x) * alpha,
                self.previous_y + (self.y - self.previous_y) * alpha)
