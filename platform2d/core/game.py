import pygame

from .scene import Scene
from platform2d.audio.service import Audio,AudioControls
from platform2d.tools.controls_panel import ControlsPanel


class Game:
    FIXED_DT = 1 / 60

    def __init__(self, scene: Scene, bindings, size=(960, 540), title="Platform2D", *, volume=.45, muted=False, controls_profile="custom", controls_path=None, language="pt-PT"):
        pygame.init()
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption(title)
        self.scene = scene
        self.audio = Audio(volume,muted)
        self.audio_controls = AudioControls(self.audio,language)
        self.scene.audio = self.audio
        self.controls = ControlsPanel(bindings,controls_profile,controls_path,language)
        self.scene.format_controls = self.controls.format_hint
        self.scene.open_controls = self.controls.toggle
        self.scene.control_label = self.controls.label
        self.scene.set_host_language = self.set_language
        self.input = self.controls.input

    def set_language(self,language):
        """Update shared overlays; the scene owns its own text catalogue."""
        self.controls.set_language(language)
        self.audio_controls.locale.translator.select(language)

    def run(self, max_frames=None, screenshot=None):
        clock = pygame.time.Clock()
        accumulator = 0.0
        frames = 0
        running = True
        try:
            while running:
                elapsed = min(clock.tick(120) / 1000, 0.25)
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        running = False
                    if self.audio_controls.handle_event(event):
                        continue
                    handler = getattr(self.scene,"handle_event",None)
                    if not self.controls.open and handler is not None and handler(event):
                        self.input.clear()
                        accumulator = 0
                        continue
                    if self.controls.handle_event(event):
                        self.audio.stop()
                        accumulator = 0
                        continue
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False
                self.audio_controls.update(elapsed)
                if getattr(self.scene,"quit_requested",False):
                    running = False
                accumulator = 0 if self.controls.open else accumulator+elapsed
                if self.controls.open:
                    self.audio.update(elapsed,paused=True)
                while accumulator >= self.FIXED_DT:
                    actions = self.input.consume()
                    if "reset" in actions.pressed or "restart" in actions.pressed:
                        self.audio.stop()
                    self.audio.update(self.FIXED_DT,paused=not self.audio_controls.focused or (getattr(self.scene,"paused",False) and "pause" not in actions.pressed))
                    self.scene.update(self.FIXED_DT, actions)
                    self.audio.update(0,paused=not self.audio_controls.focused or getattr(self.scene,"paused",False))
                    accumulator -= self.FIXED_DT
                self.scene.draw(self.screen, accumulator / self.FIXED_DT)
                if getattr(self.scene,"show_controls_hint",True):
                    self.controls.draw_hint(self.screen)
                    self.audio_controls.draw(self.screen)
                self.controls.draw(self.screen)
                pygame.display.flip()
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    running = False
            if screenshot:
                pygame.image.save(self.screen, str(screenshot))
        finally:
            self.controls.close()
            self.audio.close()
            pygame.quit()
