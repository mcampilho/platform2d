from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class Actions:
    held: frozenset[str] = frozenset()
    pressed: frozenset[str] = frozenset()
    released: frozenset[str] = frozenset()

    def axis(self, negative="left", positive="right"):
        return int(positive in self.held) - int(negative in self.held)


class Input:
    """Latch edges until a simulation step consumes them, exactly once."""

    def __init__(self, bindings, buttons=None, deadzone=.35):
        self.buttons = buttons or {}
        self.deadzone = deadzone
        self.device = None
        self.pad_buttons = set()
        self.axes = {0:0,1:0}
        self.blocked_keys = set()
        self.blocked_buttons = set()
        self.blocked_axes = set()
        self.focused = True
        self.bindings = {
            action: {pygame.key.key_code(name) for name in keys}
            for action, keys in bindings.items()
        }
        self.keys = set()
        self.pressed = set()
        self.released = set()

    def held(self):
        result = {action for action, keys in self.bindings.items() if keys & (self.keys-self.blocked_keys)}
        result.update(action for action, button in self.buttons.items()
                      if button in self.pad_buttons-self.blocked_buttons)
        for axis, negative, positive in ((0,"left","right"),(1,"up","down")):
            direction = self.axes[axis] if axis not in self.blocked_axes else 0
            action = negative if direction < 0 else positive if direction > 0 else None
            if action in self.bindings:
                result.add(action)
        return result

    def clear(self):
        """Discard pending actions; require held controls to be released first."""
        self.blocked_keys.update(self.keys)
        self.blocked_buttons.update(self.pad_buttons)
        self.blocked_axes.update(a for a,v in self.axes.items() if v)
        self.pressed.clear()
        self.released.clear()

    def attach(self, instance_id):
        before = self.held()
        self.device = instance_id
        self.pad_buttons.clear()
        self.blocked_buttons.clear()
        self.axes = {0:0,1:0}
        self.blocked_axes = set()
        removed = before-self.held()
        self.pressed.difference_update(removed)
        self.released.update(removed)

    def configure(self, bindings, buttons, deadzone):
        self.clear()
        self.bindings = {a:{pygame.key.key_code(k) for k in keys} for a,keys in bindings.items()}
        self.buttons = buttons.copy()
        self.deadzone = deadzone

    def feed(self, events):
        for event in events:
            before = self.held()
            if event.type == pygame.WINDOWFOCUSLOST:
                self.keys.clear()
                self.pad_buttons.clear()
                self.axes = {0:0,1:0}
                self.blocked_axes = {0,1}
                self.pressed.clear()
                self.focused = False
            elif event.type == pygame.WINDOWFOCUSGAINED:
                self.focused = True
            elif not self.focused:
                continue
            elif event.type == pygame.KEYDOWN and not getattr(event,"repeat",False):
                self.keys.add(event.key)
            elif event.type == pygame.KEYUP:
                self.keys.discard(event.key)
                self.blocked_keys.discard(event.key)
            elif self.device is not None and getattr(event,"instance_id",None) == self.device:
                if event.type == pygame.CONTROLLERBUTTONDOWN:
                    self.pad_buttons.add(event.button)
                elif event.type == pygame.CONTROLLERBUTTONUP:
                    self.pad_buttons.discard(event.button)
                    self.blocked_buttons.discard(event.button)
                elif event.type == pygame.CONTROLLERAXISMOTION and event.axis in self.axes:
                    value = event.value/32768
                    same_direction = value*self.axes[event.axis] > 0
                    threshold = self.deadzone-.1 if same_direction else self.deadzone
                    self.axes[event.axis] = (-1 if value < 0 else 1) if abs(value) >= threshold else 0
                    if abs(value) < self.deadzone-.1:
                        self.blocked_axes.discard(event.axis)
            after = self.held()
            self.pressed.update(after - before)
            self.released.update(before - after)

    def consume(self):
        result = Actions(frozenset(self.held()), frozenset(self.pressed), frozenset(self.released))
        self.pressed.clear()
        self.released.clear()
        return result
