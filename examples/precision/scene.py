from platform2d.rendering.terrain import draw_ramp
"""Precision course. Game-specific checkpoints and presentation."""
from pathlib import Path
import pygame

from platform2d.actors.abilities import Abilities, PrecisionController
from platform2d.actors.character import Character
from platform2d.actors.controller import Movement
from platform2d.physics.body import Body, Box
from platform2d.rendering.animation import Clip, SpriteView, slice_sheet
from platform2d.tools.debug_overlay import draw_debug
from platform2d.world.camera import Camera
from platform2d.audio import SilentAudio


class PrecisionScene:
    def __init__(self,level,settings):
        self.audio = SilentAudio()
        self.level = level
        self.player = Character(Body(*level.spawn),PrecisionController(
            Movement(**settings["movement"]),Abilities(**settings["abilities"])))
        self.ladders = [Box(o["x"],o["y"],o.get("w",32),o.get("h",96)) for o in level.objects if o["type"] == "ladder"]
        self.camera = Camera((960,576),(level.width,level.height))
        sheet = pygame.image.load(str(Path(__file__).parents[1]/"classic/assets/explorer.png"))
        self.view = SpriteView(slice_sheet(sheet,(32,40)),{
            "idle":Clip((0,1),3),"run":Clip((2,3,4,5),11),
            "jump":Clip((6,),1),"fall":Clip((7,),1),
            "dash":Clip((6,),1),"climb":Clip((2,4),6),"wall_slide":Clip((7,),1)})
        self.small = pygame.font.SysFont("consolas",13)
        self.font = pygame.font.SysFont("segoeui",18)
        self.title = pygame.font.SysFont("segoeui",28,bold=True)
        self.large = pygame.font.SysFont("segoeui",40,bold=True)
        self.debug = self.paused = False
        self.reset()

    def reset(self):
        self.collected = set()
        self.checkpoint = None
        self.spawn = self.level.spawn
        self.deaths = self.dashes = self.wall_jumps = 0
        self.climb_time = 0
        self.won = False
        self.trail = []
        self.respawn()

    def respawn(self):
        self.player.respawn(self.spawn)
        self.camera.follow(self.player.body,0,snap=True)
        self.trail = []

    @property
    def total(self):
        return sum(o["type"] == "beacon" for o in self.level.objects)

    def freeze(self):
        b = self.player.body
        b.previous_x,b.previous_y = b.x,b.y
        self.camera.previous_x,self.camera.previous_y = self.camera.x,self.camera.y

    def update(self,dt,actions):
        if "debug" in actions.pressed:
            self.debug = not self.debug
        if "pause" in actions.pressed:
            self.paused = not self.paused
        if "reset" in actions.pressed:
            self.reset()
        if "restart" in actions.pressed:
            self.respawn()
        if self.won or (self.paused and "step" not in actions.pressed):
            self.freeze()
            return
        controller = self.player.controller
        before_dash,before_lock = controller.motion_state == "dash",controller.wall_lock_left
        self.player.update(dt,actions,self.level.colliders,ladders=self.ladders)
        for event in set(controller.motion_events):
            self.audio.play(event)
        b = self.player.body
        b.x = max(0,min(b.x,self.level.width-b.w))
        if controller.motion_state == "dash":
            self.dashes += int(not before_dash)
            self.trail.append((b.x,b.y,.16))
        if controller.wall_lock_left > before_lock:
            self.wall_jumps += 1
        if controller.motion_state == "climb":
            self.climb_time += dt
        self.trail = [(x,y,time-dt) for x,y,time in self.trail if time > dt]
        if b.y > self.level.height+64:
            self.audio.play("hurt")
            self.deaths += 1
            self.respawn()
            return
        for obj in self.level.objects:
            box = Box(obj["x"],obj["y"],obj.get("w",24),obj.get("h",30))
            if not b.box.overlaps(box):
                continue
            if obj["type"] == "beacon":
                if obj["id"] not in self.collected:
                    self.audio.play("pickup")
                self.collected.add(obj["id"])
            elif obj["type"] == "checkpoint":
                if self.checkpoint != obj["id"]:
                    self.audio.play("checkpoint")
                self.checkpoint = obj["id"]
                self.spawn = (obj["x"],obj["y"])
            elif obj["type"] == "goal" and len(self.collected) == self.total:
                if not self.won:
                    self.audio.play("victory")
                self.won = True
        self.camera.follow(b,dt)
        self.view.update(self.player.state,dt)

    def text(self,surface,text,x,y,color=(177,201,220),font=None):
        text = getattr(self,"format_controls",str)(text)
        surface.blit((font or self.small).render(text,True,color),(round(x),round(y)))

    def draw(self,surface,alpha):
        cx,cy = self.camera.interpolated(alpha)
        surface.fill((10,22,37))
        for i in range(22):
            x = i*96-int(cx*.22)%96
            height = 95+(i*29)%130
            pygame.draw.polygon(surface,(18,40,56),[(x-50,544),(x+30,544-height),(x+108,544)])
        for i in range(44):
            pygame.draw.circle(surface,(54,93,116),(int((i*137+33-cx*.1)%960),100+i*37%200),1)
        for ladder in self.ladders:
            x,y = ladder.x-cx,ladder.y-cy
            pygame.draw.rect(surface,(63,94,122),(x,y,4,ladder.h))
            pygame.draw.rect(surface,(63,94,122),(x+ladder.w-4,y,4,ladder.h))
            for dy in range(6,int(ladder.h),14):
                pygame.draw.line(surface,(138,187,206),(x+4,y+dy),(x+ladder.w-4,y+dy),3)
        for c in self.level.colliders:
            r = c.box
            x,y = r.x-cx,r.y-cy
            if x+32 < 0 or x > 960:
                continue
            if c.slope:
                draw_ramp(surface,(x,y,r.w,r.h),c.slope)
            elif c.one_way:
                pygame.draw.rect(surface,(48,88,107),(x,y,32,8),border_radius=2)
                pygame.draw.line(surface,(123,235,215),(x,y),(x+32,y),2)
            else:
                pygame.draw.rect(surface,(35,61,78),(x,y,32,32))
                pygame.draw.rect(surface,(22,43,61),(x+2,y+4,28,26),border_radius=3)
                pygame.draw.line(surface,(67,105,122),(x,y),(x+32,y),1)
        for obj in self.level.objects:
            x,y = obj["x"]-cx,obj["y"]-cy
            if obj["type"] == "beacon":
                color = (88,132,145) if obj["id"] in self.collected else (247,200,111)
                pygame.draw.circle(surface,(31,58,74),(round(x+12),round(y+16)),19)
                pygame.draw.polygon(surface,color,[(x+12,y),(x+23,y+16),(x+12,y+32),(x+1,y+16)],0 if obj["id"] not in self.collected else 2)
            elif obj["type"] == "checkpoint":
                color = (126,242,199) if self.checkpoint == obj["id"] else (92,138,159)
                pygame.draw.line(surface,color,(x+8,y+30),(x+8,y-12),3)
                pygame.draw.polygon(surface,color,[(x+10,y-12),(x+30,y-5),(x+10,y+4)])
            elif obj["type"] == "goal":
                color = (130,241,203) if len(self.collected) == self.total else (106,147,164)
                pygame.draw.rect(surface,color,(x,y,32,58),3,border_radius=14)
                self.text(surface,"CUME",x-1,y-23,color)
        for x,y,time in self.trail:
            echo = pygame.Surface((24,30),pygame.SRCALPHA)
            echo.fill((102,226,222,int(time/.16*100)))
            surface.blit(echo,(x-cx,y-cy))
        x,y = self.player.body.interpolated(alpha)
        self.view.draw(surface,(x-cx-4,y-cy-10),self.player.controller.facing)
        self.text(surface,"01 / ESCALAR",70-cx,215-cy,(126,236,215))
        self.text(surface,"W / ↑ para subir a escada.",70-cx,239-cy)
        self.text(surface,"02 / ATRAVESSAR",469-cx,175-cy,(126,236,215))
        self.text(surface,"Salta e usa SHIFT + → no ar.",469-cx,199-cy)
        self.text(surface,"03 / SUBIR PELAS PAREDES",970-cx,115-cy,(126,236,215))
        self.text(surface,"Entra por baixo da parede esquerda.",970-cx,140-cy)
        self.text(surface,"Encosta e salta. Alterna os lados.",970-cx,160-cy)
        if self.debug:
            draw_debug(surface,self.small,self.player.body,self.player.state,self.level.colliders,(cx,cy),32)
            for ladder in self.ladders:
                pygame.draw.rect(surface,(132,167,255),(ladder.x-cx,ladder.y-cy,ladder.w,ladder.h),1)
            self.text(surface,f"DASHES {self.dashes} | WALL JUMPS {self.wall_jumps} | CLIMB {self.climb_time:.1f}s",28,191)
        pygame.draw.rect(surface,(8,15,28),(0,0,960,88))
        self.text(surface,"PLATFORM2D / LABORATÓRIO 04",25,12,(126,236,215))
        self.text(surface,"Ascensão",24,33,(231,242,249),self.title)
        self.text(surface,"ESCADAS / DASH / WALL JUMP",240,47,(142,177,197))
        ready = self.player.controller.dash_ready
        self.text(surface,"DASH " + ("PRONTO" if ready else "GASTO"),631,23,(126,236,215) if ready else (173,143,161))
        self.text(surface,f"SINAIS {len(self.collected)}/{self.total}",794,23,(247,200,111))
        self.text(surface,f"TENTATIVAS {self.deaths+1:02}",794,47)
        pygame.draw.rect(surface,(8,15,28),(0,544,960,32))
        self.text(surface,"A D  mover   W S  escada   ESPAÇO  salto   SHIFT / C  dash   R  checkpoint   F1  debug   P  pausa",18,555)
        if self.paused or self.won:
            panel = pygame.Surface((960,576),pygame.SRCALPHA)
            panel.fill((5,13,26,220))
            surface.blit(panel,(0,0))
            image = self.large.render("Cume alcançado" if self.won else "Em pausa",True,(219,247,233))
            surface.blit(image,(480-image.get_width()/2,210))
            text = f"{self.dashes} dashes · {self.wall_jumps} saltos na parede · F2 para recomeçar" if self.won else "P para continuar · N para avançar uma atualização"
            image = self.font.render(text,True,(147,205,207))
            surface.blit(image,(480-image.get_width()/2,282))
