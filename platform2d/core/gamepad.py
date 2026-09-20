"""SDL standardized controllers; device indices are never instance IDs."""
import pygame
from pygame._sdl2 import controller


class Gamepads:
    def __init__(self, state, backend=controller):
        self.state = state
        self.backend = backend
        self.devices = {}
        self.error = ""
        try:
            backend.init()
            backend.set_eventstate(True)
            for index in range(backend.get_count()):
                self.add(index)
        except pygame.error:
            self.error = "Gamepad indisponível; usa o teclado."

    @property
    def name(self):
        device = self.devices.get(self.state.device)
        return device.name if device else self.error or "Sem gamepad — podes ligá-lo durante o jogo"

    def add(self, index):
        try:
            if not self.backend.is_controller(index):
                return
            device = self.backend.Controller(index)
            instance = device.as_joystick().get_instance_id()
            if instance in self.devices:
                return
            self.devices[instance] = device
            if self.state.device is None:
                self.state.attach(instance)
        except pygame.error:
            self.error = "Não foi possível abrir o gamepad."

    def feed(self, event):
        if event.type == pygame.CONTROLLERDEVICEADDED:
            self.add(event.device_index)
        elif event.type == pygame.CONTROLLERDEVICEREMOVED:
            device = self.devices.pop(event.instance_id,None)
            if device:
                device.quit()
            if event.instance_id == self.state.device:
                self.state.attach(next(iter(self.devices),None))
        elif event.type == pygame.CONTROLLERDEVICEREMAPPED and event.instance_id == self.state.device:
            self.state.attach(self.state.device)

    def close(self):
        for device in self.devices.values():
            device.quit()
        self.devices.clear()
        self.state.attach(None)
