"""Reusable world objects around the existing precision movement and solver."""
from dataclasses import replace
from math import isfinite
from pathlib import Path

import pygame

from examples.precision.scene import PrecisionScene
from platform2d.actors.abilities import Abilities, PrecisionController
from platform2d.actors.controller import Movement, approach
from platform2d.physics.body import Box
from platform2d.physics.collision import Collider
from platform2d.physics.platform import MovingPlatform
from platform2d.rendering.feedback import Feedback
from platform2d.rendering.ambient import draw_ambient
from platform2d.rendering.camera_effects import CameraEffects
from platform2d.rendering.lighting import draw_glow
from platform2d.rendering.shadows import draw_shadows
from platform2d.rendering.panorama import Panorama
from platform2d.rendering.theme import load_theme
from .character_view import AstronomerView
from .terrain_view import bridge_plank, stone_tile
from .object_view import draw_checkpoint, draw_goal, draw_gate, draw_switch


class EnvironmentController(PrecisionController):
    def __init__(self, movement, abilities):
        super().__init__(movement, abilities)
        self.submerged = False
        self.current = 0
        self.gravity_scale = 1

    def before_physics(self, body, actions, dt):
        if self.submerged:
            direction = actions.axis()
            if direction:
                self.facing = direction
            vertical = int("down" in actions.held) - int("jump" in actions.held or "up" in actions.held)
            body.vx = approach(body.vx, direction * 135 + self.current, 650 * dt)
            body.vy = approach(body.vy, vertical * 145 - 15, 550 * dt)
            self.motion_state = "fly"
            self.buffer = self.coyote = self.drop_timer = 0
            self.dash_left = 0
            self.ladder = None
            return
        original = self.config
        try:
            self.config = replace(original, gravity=original.gravity * self.gravity_scale)
            super().before_physics(body, actions, dt)
        finally:
            self.config = original


class EnvironmentScene(PrecisionScene):
    def __init__(self, level, settings):
        super().__init__(level, settings)
        assets_root = Path(__file__).parent / "assets"
        theme_name = level.properties.get("visual_theme", "default")
        if not isinstance(theme_name, str) or (theme_name != "default" and Path(theme_name).name != theme_name):
            raise ValueError("visual_theme deve ser um nome de ficheiro")
        self.theme_assets_root = assets_root
        self.theme_path = None if theme_name == "default" else assets_root / theme_name
        self.reload_visual_theme()
        self.theme_notice = ""
        self.theme_notice_time = 0
        self.static_colliders = level.colliders
        self.solid_tiles = {(int(c.box.x), int(c.box.y)) for c in level.colliders if not c.one_way}
        self.platforms = []
        gates = {obj["id"] for obj in level.objects if obj["type"] == "gate"}
        for obj in level.objects:
            if obj["type"] == "moving_platform":
                end = obj.get("end")
                if not isinstance(end, list) or len(end) != 2:
                    raise ValueError(f"Plataforma {obj['id']}: end deve ter duas coordenadas")
                platform = MovingPlatform(obj["id"], (obj["x"], obj["y"]), tuple(end),
                                          obj.get("w", 96), obj.get("h", 12), obj.get("speed", 60))
                if any(x < 0 or y < 0 or x + platform.w > level.width or y + platform.h > level.height
                       for x, y in (platform.start, platform.end)):
                    raise ValueError(f"Plataforma {obj['id']}: percurso fora do mapa")
                self.platforms.append(platform)
            elif obj["type"] == "gravity_zone":
                scale = obj.get("scale", .4)
                if type(scale) not in (int, float) or not isfinite(scale) or not 0 < scale <= 2:
                    raise ValueError(f"Zona {obj['id']}: scale deve estar entre 0 e 2")
            elif obj["type"] == "water":
                current = obj.get("current", 0)
                if type(current) not in (int, float) or not isfinite(current) or abs(current) > 150:
                    raise ValueError(f"Água {obj['id']}: corrente inválida")
            elif obj["type"] == "switch" and obj.get("gate") not in gates:
                raise ValueError(f"Interruptor {obj['id']}: porta desconhecida")
            if obj["type"] in {"water", "gravity_zone", "gate", "switch"}:
                box = self.box(obj)
                if box.right > level.width or box.bottom > level.height:
                    raise ValueError(f"Objeto {obj['id']}: área fora do mapa")
        self.gates_open = set()
        effects = settings.get("effects", {})
        if (not isinstance(effects, dict) or type(effects.get("enabled", True)) is not bool or
                type(effects.get("shadows", True)) is not bool):
            raise ValueError("effects.enabled e effects.shadows devem ser true ou false")
        self.feedback = Feedback()
        self.ambient_time = 0
        self.feedback.enabled = effects.get("enabled", True)
        self.shadows_enabled = effects.get("shadows", True)
        if type(effects.get("camera", True)) is not bool:
            raise ValueError("effects.camera deve ser true ou false")
        self.camera.look_ahead = .24
        self.camera_effects = CameraEffects(effects.get("camera", True))
        self.player.controller = EnvironmentController(Movement(**settings["movement"]),
                                                       Abilities(**settings["abilities"]))
        self.player.respawn(self.spawn)

    @staticmethod
    def box(obj):
        return Box(obj["x"], obj["y"], obj.get("w", 32), obj.get("h", 32))

    def reload_visual_theme(self):
        """Build all visual resources before replacing the currently valid set."""
        theme = load_theme(self.theme_path, self.theme_assets_root)
        background = theme.assets.get("background", self.theme_assets_root / "astral-greenhouse-bg.png")
        foreground = theme.assets.get("foreground", self.theme_assets_root / "observatory-foreground.png")
        character = theme.assets.get("character", self.theme_assets_root / "astronomer-atlas.png")
        panorama = Panorama(background, parallax=theme.parallax.get("background", .27))
        foreground_panorama = Panorama(foreground, parallax=theme.parallax.get("foreground", .55))
        view = AstronomerView(character)
        self.theme, self.panorama = theme, panorama
        self.foreground_panorama, self.view = foreground_panorama, view

    def draw_background(self, surface, cx, cy):
        self.panorama.draw(surface, cx)
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((5, 14, 25, 46))
        surface.blit(shade, (0, 0))

    def camera_offset(self, alpha):
        return self.camera_effects.interpolated(alpha) if self.feedback.enabled else (0, 0)

    def draw_terrain(self, surface, collider, x, y):
        box = collider.box
        tile = pygame.Rect(round(x), round(y), round(box.w), round(box.h))
        variant = (int(box.x / 32) * 13 + int(box.y / 32) * 7) % 4
        exposed = (int(box.x), int(box.y - 32)) not in self.solid_tiles
        surface.blit(stone_tile(tile.w, tile.h, variant, exposed, collider.one_way),
                     tile.topleft)

    def draw_foreground(self, surface, cx, cy):
        self.foreground_panorama.draw(surface, cx)

    def draw_player(self, surface, alpha, cx, cy):
        self.view.draw(surface, self.player.body, self.player.controller.facing, (cx, cy), alpha)

    def draw_world_object(self, surface, obj, x, y):
        if obj["type"] == "checkpoint":
            draw_checkpoint(surface, x, y, self.checkpoint == obj["id"])
            return True
        if obj["type"] == "goal":
            draw_goal(surface, x, y, obj.get("w", 32), obj.get("h", 58),
                      len(self.collected) == self.total)
            self.text(surface, "SAÍDA", x - 4, y - 22, (185, 215, 183))
            return True
        return False

    def draw_hud(self, surface, lessons):
        self.draw_observatory_hud(surface)

    def draw_observatory_hud(self, surface):
        """Replace the laboratory's generic bars with the observatory's panels."""
        ink = self.theme.color("ink")
        copper = self.theme.color("accent")
        pale = self.theme.color("text")
        muted = self.theme.color("muted")
        pygame.draw.rect(surface, ink, (0, 0, 960, 88))
        pygame.draw.line(surface, copper, (0, 87), (960, 87), 2)
        for rect in ((14, 12, 214, 64), (238, 12, 496, 64), (744, 12, 202, 64)):
            pygame.draw.rect(surface, self.theme.color("panel"), rect, border_radius=8)
            pygame.draw.rect(surface, self.theme.color("line"), rect, 1, border_radius=8)
            pygame.draw.circle(surface, copper, (rect[0] + 11, rect[1] + 11), 2)
            pygame.draw.circle(surface, copper,
                               (rect[0] + rect[2] - 11, rect[1] + 11), 2)
        self.text(surface, "OBSERVATÓRIO / MUNDO VIVO", 29, 19, copper)
        self.text(surface, self.level.name, 28, 38, pale, self.title)
        lessons = self.level.properties.get("lessons", [])
        if lessons:
            lesson = max((item for item in lessons if self.player.body.x >= item["x"]),
                         key=lambda item: item["x"], default=lessons[0])
            stage = lessons.index(lesson)
            self.text(surface, lesson["title"], 254, 20, (171, 212, 188), self.font)
            self.text(surface, lesson["help"], 254, 47, pale)
            for index in range(len(lessons)):
                color = (199, 166, 105) if index <= stage else (75, 91, 92)
                pygame.draw.circle(surface, color, (765 + index * 18, 31), 5)
            self.text(surface, f"SECTOR {stage + 1}/{len(lessons)}", 756, 47, pale)
        ready = self.player.controller.dash_ready
        self.text(surface, "DASH", 840, 19, muted)
        pygame.draw.circle(surface, self.theme.color("highlight") if ready else (75, 91, 92),
                           (890, 34), 5)
        self.text(surface, f"{self.deaths + 1:02}", 913, 19, muted, self.font)
        pygame.draw.rect(surface, ink, (0, 544, 960, 32))
        pygame.draw.line(surface, copper, (0, 544), (960, 544), 1)
        self.text(surface, self.level.properties.get("footer", ""), 18, 554, muted)
        if self.theme_notice_time:
            pygame.draw.rect(surface, self.theme.color("panel"), (180, 496, 600, 36),
                             border_radius=6)
            message = self.theme_notice[:82]
            label = self.small.render(message, True, self.theme.color("highlight"))
            surface.blit(label, (480 - label.get_width() // 2, 507))

    def draw_status_overlay(self, surface, lessons):
        veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        veil.fill((6, 15, 25, 208))
        surface.blit(veil, (0, 0))
        card = pygame.Rect(212, 142, 536, 292)
        pygame.draw.rect(surface, (18, 36, 45), card, border_radius=16)
        pygame.draw.rect(surface, (154, 124, 81), card, 2, border_radius=16)
        pygame.draw.rect(surface, (66, 91, 83), card.inflate(-16, -16), 1,
                         border_radius=10)
        pygame.draw.circle(surface, (209, 166, 101), (480, 168), 7, 2)
        pygame.draw.line(surface, (117, 104, 75), (306, 183), (450, 183), 1)
        pygame.draw.line(surface, (117, 104, 75), (510, 183), (654, 183), 1)
        if self.won:
            heading = "PERCURSO CONCLUÍDO"
            detail = "Exploraste os quatro sectores do Mundo Vivo."
            command = "F2  recomeçar o percurso"
        else:
            heading = "OBSERVATÓRIO EM PAUSA"
            detail = "A expedição fica à tua espera."
            command = "P  continuar     N  avançar um passo"
        title = self.title.render(heading, True, (231, 226, 198))
        surface.blit(title, (480 - title.get_width() // 2, 202))
        caption = self.font.render(detail, True, (171, 203, 193))
        surface.blit(caption, (480 - caption.get_width() // 2, 254))
        if lessons:
            reached = sum(self.player.body.x >= item["x"] for item in lessons)
            if self.won:
                reached = len(lessons)
            for index in range(len(lessons)):
                pygame.draw.circle(surface,
                                   (211, 169, 101) if index < reached else (77, 97, 96),
                                   (453 + index * 18, 312), 5)
            progress = f"{reached} / {len(lessons)} sectores"
            label = self.small.render(progress, True, (168, 190, 180))
            surface.blit(label, (480 - label.get_width() // 2, 330))
        instruction = self.font.render(command, True, (226, 213, 177))
        surface.blit(instruction, (480 - instruction.get_width() // 2, 374))

    def update(self, dt, actions):
        self.theme_notice_time = max(0, self.theme_notice_time - dt)
        if "reload_theme" in actions.pressed:
            try:
                self.reload_visual_theme()
                self.theme_notice = "Tema visual recarregado."
            except (ValueError, OSError, pygame.error) as error:
                self.theme_notice = "Tema anterior preservado: " + str(error)
            self.theme_notice_time = 5
        if "effects" in actions.pressed:
            self.feedback.enabled = not self.feedback.enabled
            if not self.feedback.enabled:
                self.feedback.clear()
                self.camera_effects.clear()
        if "reset" in actions.pressed:
            self.gates_open.clear()
            self.feedback.clear()
            self.camera_effects.clear()
        stepping = not self.won and (not self.paused or "step" in actions.pressed)
        if "pause" in actions.pressed:
            stepping = not self.paused
        if stepping:
            self.ambient_time += dt
            self.camera_effects.update(dt)
            was_submerged = self.player.controller.submerged
            previous_gravity = self.player.controller.gravity_scale
            switch_point = None
            for platform in self.platforms:
                platform.update(dt)
            body = self.player.body
            center = Box(body.x + 6, body.y + 5, 12, 20)
            controller = self.player.controller
            controller.submerged = False
            controller.current = 0
            controller.gravity_scale = 1
            for obj in self.level.objects:
                if obj["type"] == "water" and center.overlaps(self.box(obj)):
                    controller.submerged = True
                    controller.current = obj.get("current", 0)
                elif obj["type"] == "gravity_zone" and center.overlaps(self.box(obj)):
                    controller.gravity_scale = obj.get("scale", .4)
                elif (obj["type"] == "switch" and "interact" in actions.pressed and
                      body.box.overlaps(Box(obj["x"] - 16, obj["y"] - 16,
                                            obj.get("w", 32) + 32, obj.get("h", 32) + 32))):
                    self.gates_open.add(obj["gate"])
                    self.audio.play("switch")
                    switch_point = (obj["x"] + obj.get("w", 32) / 2, obj["y"] + 8)
        self.level.colliders = list(self.static_colliders) + [Collider(self.box(obj)) for obj in self.level.objects
            if obj["type"] == "gate" and obj["id"] not in self.gates_open]
        try:
            super().update(dt, actions)
        finally:
            self.level.colliders = self.static_colliders
        if stepping:
            controller = self.player.controller
            body = self.player.body
            if not was_submerged and controller.submerged:
                self.feedback.burst((body.x + body.w / 2, body.y + body.h / 2), (105, 211, 245))
                if self.feedback.enabled: self.camera_effects.impulse(.12)
            if previous_gravity == 1 and controller.gravity_scale != 1:
                self.feedback.burst((body.x + body.w / 2, body.y + body.h / 2), (192, 149, 244))
                if self.feedback.enabled: self.camera_effects.impulse(.1)
            if switch_point:
                self.feedback.burst(switch_point, (250, 204, 119))
                if self.feedback.enabled: self.camera_effects.impulse(.32)
            if "land" in controller.motion_events:
                self.feedback.burst((body.x + body.w / 2, body.y + body.h), (157, 222, 207))
                if self.feedback.enabled: self.camera_effects.impulse(.08)
            self.feedback.update(dt)

    def draw_environment(self, surface, alpha, cx, cy):
        for obj in self.level.objects:
            kind = obj["type"]
            if kind not in {"water", "gravity_zone", "gate", "switch"}:
                continue
            box = self.box(obj)
            rect = pygame.Rect(box.x - cx, box.y - cy, box.w, box.h)
            if kind in {"water", "gravity_zone"}:
                tint = pygame.Surface(rect.size, pygame.SRCALPHA)
                tint.fill((35, 121, 168, 75) if kind == "water" else (119, 84, 170, 58))
                surface.blit(tint, rect)
                pygame.draw.line(surface, (111, 229, 239) if kind == "water" else (188, 146, 252),
                                 rect.topleft, rect.topright, 3)
                if kind == "water":
                    phase = round(self.feedback.age * 32)
                    for step in range(0, rect.width, 58):
                        ripple_x = rect.x + (step + phase) % rect.width
                        ripple_y = rect.y + 28 + step % 3 * 31
                        pygame.draw.arc(surface, (98, 190, 205),
                                        (ripple_x, ripple_y, 30, 7), 3.3, 5.8, 1)
                else:
                    for step in range(0, rect.width, 75):
                        pygame.draw.circle(surface, (153, 120, 204),
                                           (rect.x + step + 24, rect.y + 42 + step % 4 * 42), 2)
                if self.feedback.enabled:
                    draw_ambient(surface, box, (cx, cy), self.ambient_time, kind)
            elif kind == "gate":
                opened = obj["id"] in self.gates_open
                draw_gate(surface, rect, opened)
            else:
                active = obj["gate"] in self.gates_open
                draw_switch(surface, rect, active)
                if not active:
                    self.text(surface, "E", rect.x + 11, rect.y + 24, (217, 225, 194))
        for platform in self.platforms:
            box = platform.interpolated(alpha)
            plank = pygame.Rect(round(box.x - cx), round(box.y - cy), round(box.w), round(box.h))
            surface.blit(bridge_plank(plank.width, plank.height), plank.topleft)

    def draw_environment_effects(self, surface, alpha, cx, cy):
        if not self.feedback.enabled:
            return
        body = self.player.body
        px, py = body.interpolated(alpha)
        light = (px + body.w / 2 - self.player.controller.facing * 7,
                 py + body.h / 2)
        if self.shadows_enabled:
            boxes = [collider.box for collider in self.static_colliders if not collider.one_way]
            boxes.extend(self.box(obj) for obj in self.level.objects
                         if obj["type"] == "gate" and obj["id"] not in self.gates_open)
            boxes.extend(platform.interpolated(alpha) for platform in self.platforms)
            draw_shadows(surface, light, boxes, (cx, cy))
        draw_glow(surface, (light[0] - cx, light[1] - cy), (232, 167, 92), 76)
        for obj in self.level.objects:
            kind = obj["type"]
            if kind == "switch":
                color, radius = ((87, 217, 165) if obj["gate"] in self.gates_open
                                 else (247, 190, 96)), 64
            elif kind == "gravity_zone":
                color, radius = (139, 99, 210), 130
            elif kind == "water":
                color, radius = (61, 151, 206), 125
            elif kind == "gate" and obj["id"] in self.gates_open:
                color, radius = (87, 217, 165), 70
            else:
                continue
            box = self.box(obj)
            draw_glow(surface, (box.x + box.w / 2 - cx, box.y + box.h / 2 - cy), color, radius)
        self.feedback.draw(surface, (cx, cy))
