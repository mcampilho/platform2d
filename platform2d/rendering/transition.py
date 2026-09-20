"""A timed fade; the destination changes exactly once at full opacity."""


class FadeTransition:
    def __init__(self, half_duration=0.18):
        if half_duration <= 0:
            raise ValueError("A duração da transição deve ser positiva.")
        self.half_duration = half_duration
        self.elapsed = 0
        self.active = False
        self.callback = None

    def start(self, callback):
        if self.active:
            return False
        self.elapsed = 0
        self.callback = callback
        self.active = True
        return True

    def update(self, dt):
        if not self.active:
            return
        self.elapsed += dt
        if self.elapsed >= self.half_duration and self.callback is not None:
            callback, self.callback = self.callback, None
            callback()
        if self.elapsed >= 2*self.half_duration:
            self.active = False

    @property
    def opacity(self):
        if not self.active:
            return 0
        return round(255*max(0, 1-abs(self.elapsed/self.half_duration-1)))
