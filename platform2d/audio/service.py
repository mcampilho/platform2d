"""Owned mixer channels, bounded polyphony and graceful device failure."""
from importlib import resources
from math import isfinite

import pygame

EFFECTS = ("jump","land","pickup","checkpoint","hurt","attack","hit","dash",
           "door","switch","blocked","victory","save","load","error","shoot")


class SilentAudio:
    available = False
    volume = 0.0
    muted = True

    def play(self,name):
        return False

    def update(self,dt,paused=False):
        pass

    def stop(self):
        pass

    def close(self):
        pass


class Audio:
    """No sounds queue: muted/paused/busy requests are dropped immediately."""
    def __init__(self,volume=.45,muted=False,asset_dir=None):
        if type(volume) not in (float,int) or not isfinite(volume) or not 0 <= volume <= 1:
            raise ValueError("Volume deve estar entre 0 e 1.")
        self.volume = float(volume)
        self.muted = bool(muted)
        self.available = False
        self.paused = False
        self.time = 0.0
        self.last = {}
        self.sounds = {}
        self.channels = []
        self.errors = []
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050,size=-16,channels=1,buffer=512)
            count = pygame.mixer.get_num_channels()
            pygame.mixer.set_num_channels(count+6)
            self.channels = [pygame.mixer.Channel(i) for i in range(count,count+6)]
            folder = asset_dir if asset_dir is not None else resources.files("platform2d.audio").joinpath("assets")
            for name in EFFECTS:
                try:
                    with resources.as_file(folder.joinpath(name+".wav")) as path:
                        self.sounds[name] = pygame.mixer.Sound(str(path))
                except (pygame.error,OSError) as error:
                    self.errors.append(f"{name}: {error}")
            self.available = bool(self.sounds)
        except pygame.error as error:
            self.errors.append(str(error))

    def update(self,dt,paused=False):
        self.time += max(0,dt)
        if paused and not self.paused:
            self.stop()
        self.paused = paused

    def play(self,name):
        if not self.available or self.muted or self.paused or self.volume <= 0 or name not in self.sounds:
            return False
        cooldown = .35 if name in {"blocked","error"} else .05
        if self.time-self.last.get(name,-100) < cooldown:
            return False
        try:
            channel = next((c for c in self.channels if not c.get_busy()),None)
            if channel is None:
                # Completion and damage must remain audible in a busy frame.
                if name not in {"victory","hurt","error"}:
                    return False
                channel = self.channels[0]
            channel.set_volume(self.volume)
            channel.play(self.sounds[name])
            self.last[name] = self.time
            return True
        except pygame.error as error:
            self.available = False
            self.errors.append(str(error))
            return False

    def set_volume(self,value):
        if type(value) not in (int,float) or not isfinite(value):
            raise ValueError("Volume inválido.")
        self.volume = max(0.,min(1.,float(value)))
        try:
            for channel in self.channels:
                channel.set_volume(0 if self.muted else self.volume)
        except pygame.error:
            self.available = False

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop()

    def stop(self):
        try:
            for channel in self.channels:
                channel.stop()
        except pygame.error:
            self.available = False
        self.last.clear()

    def close(self):
        self.stop()
        self.sounds.clear()
        self.available = False


class AudioControls:
    """Reusable host-level shortcuts and a short visual status message."""
    def __init__(self,audio):
        self.audio = audio
        self.remaining = 4.0
        self.keys = set()
        self.focused = True

    def handle_event(self,event):
        keys = {pygame.K_F10,pygame.K_F11,pygame.K_F12}
        if event.type == pygame.WINDOWFOCUSLOST:
            self.focused = False
            self.keys.clear()
            self.audio.stop()
        if event.type == pygame.WINDOWFOCUSGAINED:
            self.focused = True
        if event.type == pygame.KEYUP and event.key in keys:
            self.keys.discard(event.key)
            return True
        if event.type == pygame.KEYDOWN and event.key in keys:
            if event.key not in self.keys:
                self.keys.add(event.key)
                if event.key == pygame.K_F10:
                    self.audio.toggle_mute()
                else:
                    self.audio.set_volume(round(self.audio.volume+(-.1 if event.key == pygame.K_F11 else .1),2))
                self.remaining = 3
            return True
        return False

    def update(self,dt):
        self.remaining = max(0,self.remaining-dt)

    def draw(self,surface):
        if self.remaining <= 0:
            return
        status = "SOM INDISPONÍVEL" if not self.audio.available else "SOM DESLIGADO" if self.audio.muted else f"SOM {self.audio.volume:.0%}"
        font = pygame.font.SysFont("consolas",13)
        text = font.render(status+"  |  F10: silêncio  F11/F12: volume",True,(179,233,219))
        rect = text.get_rect(bottomright=(surface.get_width()-16,surface.get_height()-43)).inflate(16,14)
        pygame.draw.rect(surface,(12,28,40),rect,border_radius=5)
        surface.blit(text,(rect.x+8,rect.y+7))


def add_audio_arguments(parser):
    parser.add_argument("--mute",action="store_true",help="Começar sem som; F10 permite ativar")
    parser.add_argument("--volume",type=float,default=.45,help="Volume dos efeitos entre 0 e 1 (predefinição: 0.45)")
