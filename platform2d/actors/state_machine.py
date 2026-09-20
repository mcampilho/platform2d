"""Small explicit state machine, independent of physics and rendering."""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class State:
    enter: Callable = lambda owner: None
    update: Callable = lambda owner, dt: None
    exit: Callable = lambda owner: None


class StateMachine:
    def __init__(self, owner, states, initial):
        if initial not in states:
            raise ValueError(f"Estado inicial desconhecido: {initial}")
        self.owner, self.states = owner, dict(states)
        self.current = initial
        self.elapsed = 0.0
        self.changing = False
        self.states[initial].enter(owner)

    def change(self, name):
        if name not in self.states:
            raise ValueError(f"Estado desconhecido: {name}")
        if name == self.current:
            return False
        if self.changing:
            raise RuntimeError("Transições dentro de enter/exit não são permitidas.")
        self.changing = True
        try:
            self.states[self.current].exit(self.owner)
            self.current, self.elapsed = name, 0.0
            self.states[name].enter(self.owner)
        finally:
            self.changing = False
        return True

    def update(self, dt):
        self.elapsed += dt
        self.states[self.current].update(self.owner, dt)
