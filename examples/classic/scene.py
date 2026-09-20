from platform2d.rendering.terrain import draw_ramp
import math
from pathlib import Path

import pygame

from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController, Movement
from platform2d.physics.body import Body, Box
from platform2d.rendering.animation import Clip, SpriteView, slice_sheet
from platform2d.tools.debug_overlay import draw_debug
from platform2d.world.camera import Camera
from platform2d.audio import SilentAudio


class ClassicScene:
    """Example-specific rules: crystals, hazards, checkpoints and completion."""

    def __init__(self, level, settings):
        self.audio = SilentAudio()
        self.level = level
        self.has_ramps = any(c.slope for c in level.colliders)
        self.player = Character(Body(*level.spawn), ArcadeController(Movement(**settings["movement"])))
        self.camera = Camera((960, 540), (level.width, level.height))
        sheet = pygame.image.load(str(Path(__file__).parent / "assets" / "explorer.png"))
        self.view = SpriteView(slice_sheet(sheet, (32, 40)), {
            "idle": Clip((0, 1), 3), "run": Clip((2, 3, 4, 5), 11),
            "jump": Clip((6,), 1), "fall": Clip((7,), 1),
        })
        self.font = pygame.font.SysFont("consolas", 16)
        self.small = pygame.font.SysFont("consolas", 13)
        self.title_font = pygame.font.SysFont("segoeui", 24, bold=True)
        self.large = pygame.font.SysFont("segoeui", 42, bold=True)
        self.debug = self.paused = False
        self.reset()

    def reset(self):
        self.collected = set()
        self.active_checkpoint = None
        self.respawn_point = self.level.spawn
        self.deaths = 0
        self.won = False
        self.time = 0
        self.message_timer = 0
        self.message = ""
        self.respawn()

    def respawn(self):
        self.player.respawn(self.respawn_point)
        self.camera.follow(self.player.body, 0, snap=True)

    def update(self, dt, actions):
        if "debug" in actions.pressed:
            self.debug = not self.debug
        if "pause" in actions.pressed:
            self.paused = not self.paused
        if "reset" in actions.pressed:
            self.reset()
        if "restart" in actions.pressed:
            self.respawn()
        if self.paused and "step" not in actions.pressed:
            b = self.player.body
            b.previous_x, b.previous_y = b.x, b.y
            self.camera.previous_x, self.camera.previous_y = self.camera.x, self.camera.y
            return
        if self.won:
            b = self.player.body
            b.previous_x, b.previous_y = b.x, b.y
            self.camera.previous_x, self.camera.previous_y = self.camera.x, self.camera.y
            return
        self.time += dt
        self.message_timer = max(0, self.message_timer - dt)
        self.player.update(dt, actions, self.level.colliders)
        for event in set(self.player.controller.motion_events):
            self.audio.play(event)
        body = self.player.body
        # Explicit world edges prevent walking outside the finite demo map.
        body.x = max(0, min(body.x, self.level.width - body.w))
        # Damage wins over pickups/goals regardless of their order in the JSON.
        hazards = [o for o in self.level.objects if o["type"] == "hazard"]
        if any(body.box.overlaps(Box(o["x"],o["y"],o.get("w",24),o.get("h",30))) for o in hazards):
            self.deaths += 1
            self.audio.play("hurt")
            self.respawn()
            self.view.update(self.player.state,dt)
            return
        for obj in self.level.objects:
            box = Box(obj["x"], obj["y"], obj.get("w", 24), obj.get("h", 30))
            if not body.box.overlaps(box):
                continue
            kind = obj["type"]
            if kind == "coin":
                if obj["id"] not in self.collected:
                    self.audio.play("pickup")
                self.collected.add(obj["id"])
            elif kind == "checkpoint" and self.active_checkpoint != obj["id"]:
                self.active_checkpoint = obj["id"]
                self.audio.play("checkpoint")
                self.respawn_point = (obj["x"], obj["y"])
                self.message, self.message_timer = "CHECKPOINT ATIVADO", 2.5
            elif kind == "goal":
                if len(self.collected) == self.coin_count:
                    if not self.won:
                        self.audio.play("victory")
                    self.won = True
                else:
                    self.message, self.message_timer = "Recolhe todos os cristais para abrir o portal", 2
        if body.y > self.level.height + 96:
            self.audio.play("hurt")
            self.deaths += 1
            self.respawn()
        self.camera.follow(body, dt)
        self.view.update(self.player.state, dt)

    @property
    def coin_count(self):
        return sum(obj["type"] == "coin" for obj in self.level.objects)

    def label(self, surface, text, position, color=(198, 218, 231), font=None):
        text = getattr(self,"format_controls",str)(text)
        surface.blit((font or self.font).render(text, True, color), position)

    def draw(self, surface, alpha):
        cx, cy = self.camera.interpolated(alpha)
        # The example owns its art direction; none of this affects physics.
        surface.fill((10, 18, 34))
        for y in range(0, 540, 4):
            shade = y / 540
            pygame.draw.rect(surface, (10+int(9*shade), 18+int(16*shade), 34+int(17*shade)), (0, y, 960, 4))
        for i in range(64):
            x = (i * 137 + 47 - cx * 0.12) % 1000
            y = (i * 73 + 41) % 330
            pygame.draw.circle(surface, (68, 104, 129), (int(x), y), 1)
        pygame.draw.circle(surface, (32, 65, 82), (790-int(cx*.08), 170), 70)
        pygame.draw.circle(surface, (46, 92, 103), (790-int(cx*.08), 170), 53, 1)
        for i in range(-1, 14):
            x = i*110 - int(cx*.23) % 110
            height = 60 + (i*37 % 100)
            pygame.draw.rect(surface, (20, 40, 56), (x, 430-height, 78, height))
            pygame.draw.line(surface, (30, 59, 74), (x+10, 438-height), (x+65, 438-height), 2)
        t = self.level.tile_size
        for collider in self.level.colliders:
            b = collider.box
            x, y = round(b.x-cx), round(b.y-cy)
            if x+t < 0 or x > 960 or y+t < 0 or y > 540:
                continue
            if collider.slope:
                draw_ramp(surface,(x,y,t,t),collider.slope)
            elif collider.one_way:
                pygame.draw.rect(surface, (55, 112, 137), (x, y, t, 8), border_radius=2)
                pygame.draw.line(surface, (119, 208, 216), (x+2, y), (x+t-2, y), 2)
                pygame.draw.line(surface, (37, 67, 85), (x+8, y+8), (x+14, y+17), 2)
            else:
                pygame.draw.rect(surface, (32, 54, 68), (x, y, t, t))
                pygame.draw.rect(surface, (23, 42, 57), (x+2, y+5, t-4, t-7), border_radius=3)
                pygame.draw.line(surface, (49, 89, 100), (x, y), (x+t, y), 2)
        for obj in self.level.objects:
            x, y = round(obj["x"]-cx), round(obj["y"]-cy)
            kind = obj["type"]
            if kind == "coin" and obj["id"] not in self.collected:
                bob = round(math.sin(self.time*3 + obj["x"]) * 3)
                pygame.draw.circle(surface, (49, 72, 77), (x+12, y+13+bob), 16)
                pygame.draw.polygon(surface, (255, 203, 106), [(x+12,y+bob), (x+21,y+12+bob), (x+12,y+25+bob), (x+3,y+12+bob)])
                pygame.draw.line(surface, (255, 242, 196), (x+12,y+4+bob), (x+12,y+19+bob), 2)
            elif kind == "checkpoint":
                active = self.active_checkpoint == obj["id"]
                color = (105, 232, 182) if active else (95, 140, 164)
                pygame.draw.line(surface, color, (x+8,y+30), (x+8,y-17), 3)
                pygame.draw.polygon(surface, color, [(x+10,y-17), (x+35,y-9), (x+10,y)])
                self.label(surface, "CHECKPOINT", (x-30,y+36), color, self.small)
            elif kind == "hazard":
                for dx in range(0, int(obj.get("w",24)), 16):
                    pygame.draw.polygon(surface, (239, 112, 135), [(x+dx,y+obj.get("h",30)), (x+dx+8,y), (x+dx+16,y+obj.get("h",30))])
            elif kind == "goal":
                color = (110, 237, 196) if len(self.collected) == self.coin_count else (100, 132, 163)
                pygame.draw.rect(surface, (21, 52, 66), (x-5,y-8,42,70), border_radius=18)
                pygame.draw.rect(surface, color, (x,y-4,32,62), 3, border_radius=16)
                self.label(surface, "SAÍDA", (x-5,y-26), color, self.small)
        px, py = self.player.body.interpolated(alpha)
        self.view.draw(surface, (px-cx-4, py-cy-10), self.player.controller.facing)
        # HUD and route introduction.
        pygame.draw.rect(surface, (9, 17, 30), (0,0,960,92))
        pygame.draw.line(surface, (42, 69, 87), (24,91), (936,91))
        self.label(surface, "PLATFORM2D  /  LABORATÓRIO 01", (25,14), (95, 203, 194), self.small)
        self.label(surface, self.level.name, (24,35), (233, 242, 248), self.title_font)
        self.label(surface, "Recolhe os cristais. Encontra o portal.", (274,47), (137, 162, 183), self.small)
        self.label(surface, f"CRISTAIS  {len(self.collected):02}/{self.coin_count:02}", (695,24), (255,205,118))
        self.label(surface, f"TENTATIVAS  {self.deaths+1:02}", (695,49), (138,169,191), self.small)
        if cx < 280:
            self.label(surface, "01  /  COLINAS" if self.has_ramps else "01  /  PRIMEIROS PASSOS", (64-cx,250-cy), (105,225,201), self.small)
            self.label(surface, "Sobe e desce sem saltar. Salta o fosso!" if self.has_ramps else "Mantém SALTO para ir mais alto.", (64-cx,274-cy), (177,201,216))
            self.label(surface, "Rampas douradas: atravessáveis por baixo." if self.has_ramps else "Nas plataformas finas: BAIXO + SALTO para descer.", (64-cx,297-cy), (121,155,178), self.small)
        pygame.draw.rect(surface, (9,17,30), (0,508,960,32))
        self.label(surface, "A D / ← →  mover    ESPAÇO  saltar    R  checkpoint    F1  debug    P  pausa    ESC  sair", (23,518), (153,181,199), self.small)
        if self.message_timer:
            text = self.font.render(self.message, True, (140,244,206))
            surface.blit(text, (480-text.get_width()/2,110))
        if self.debug:
            draw_debug(surface, self.small, self.player.body, self.player.state,
                       self.level.colliders, (cx,cy), t)
            self.label(surface, "N: uma atualização em pausa | F2: reiniciar sessão", (25,190), font=self.small)
        if self.paused or self.won:
            panel = pygame.Surface((960,540), pygame.SRCALPHA)
            panel.fill((4,10,22,205))
            surface.blit(panel,(0,0))
            title = "Percurso concluído" if self.won else "Em pausa"
            text = self.large.render(title, True, (219,246,240))
            surface.blit(text,(480-text.get_width()/2,205))
            detail = f"{self.coin_count} cristais · {self.deaths+1} tentativas · F2 para recomeçar" if self.won else "P para continuar · N para avançar uma atualização"
            text = self.font.render(detail, True, (155,196,207))
            surface.blit(text,(480-text.get_width()/2,274))
