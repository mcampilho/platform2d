from typing import Protocol

from .input import Actions


class Scene(Protocol):
    def update(self, dt: float, actions: Actions) -> None: ...

    def draw(self, surface, alpha: float) -> None: ...
