"""Optional visual camera impulses; never modify simulation coordinates."""
from math import sin


class CameraEffects:
    def __init__(self, enabled=True, amplitude=7, decay=2.8):
        if type(enabled) is not bool or amplitude < 0 or decay <= 0:
            raise ValueError("Configuração de efeitos de câmara inválida")
        self.enabled = enabled
        self.amplitude = amplitude
        self.decay = decay
        self.trauma = 0
        self.time = 0
        self.previous = self.current = (0.0, 0.0)

    def impulse(self, strength):
        if type(strength) not in (int, float) or not 0 <= strength <= 1:
            raise ValueError("Impulso de câmara deve estar entre 0 e 1")
        if self.enabled:
            self.trauma = min(1, self.trauma + strength)

    def clear(self):
        self.trauma = 0
        self.previous = self.current = (0.0, 0.0)

    def update(self, dt):
        if dt < 0:
            raise ValueError("dt não pode ser negativo")
        self.previous = self.current
        self.time += dt
        self.trauma = max(0, self.trauma - self.decay * dt)
        power = self.trauma * self.trauma if self.enabled else 0
        self.current = (sin(self.time * 47.3) * self.amplitude * power,
                        sin(self.time * 61.7 + 1.8) * self.amplitude * .65 * power)

    def interpolated(self, alpha):
        return (self.previous[0] + (self.current[0] - self.previous[0]) * alpha,
                self.previous[1] + (self.current[1] - self.previous[1]) * alpha)
