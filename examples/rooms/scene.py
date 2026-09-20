from platform2d.rendering.terrain import draw_ramp
"""Game-specific presentation and rules, without copying player physics."""
from pathlib import Path
import math
import pygame

from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController, Movement
from platform2d.physics.body import Body, Box
from platform2d.rendering.animation import Clip, SpriteView, slice_sheet
from platform2d.rendering.transition import FadeTransition
from platform2d.tools.debug_overlay import draw_debug
from platform2d.gameplay.mechanisms import requirements
from platform2d.gameplay.progress import ProgressSlot
from platform2d.audio import SilentAudio


class RoomsScene:
    def __init__(self, world, settings, progress_slot=None):
        self.audio = SilentAudio()
        self.world = world
        self.progress_slot = progress_slot or ProgressSlot()
        self.movement_settings = vars(Movement(**settings["movement"])).copy()
        self.progress_message = ""
        self.progress_message_time = 0
        self.has_mechanisms = any(r.objects("switch") for r in world.rooms.values())
        if any(r.level.width != 960 or r.level.height != 576 for r in world.rooms.values()):
            raise ValueError("Arquivo Lunar: as salas devem medir 960×576 unidades.")
        self.player = Character(Body(0,0), ArcadeController(Movement(**settings["movement"])))
        sheet = pygame.image.load(str(Path(__file__).parents[1] / "classic/assets/explorer.png"))
        self.view = SpriteView(slice_sheet(sheet,(32,40)), {
            "idle":Clip((0,1),3), "run":Clip((2,3,4,5),11),
            "jump":Clip((6,),1), "fall":Clip((7,),1)})
        self.small = pygame.font.SysFont("consolas",13)
        self.font = pygame.font.SysFont("segoeui",18)
        self.title = pygame.font.SysFont("segoeui",27,bold=True)
        self.large = pygame.font.SysFont("segoeui",40,bold=True)
        self.paused = self.debug = False
        self.reset()

    def reset(self):
        self.world.reset()
        self.transition = FadeTransition()
        self.player.respawn(self.world.respawn())
        self.deaths = 0
        self.won = False
        self.elapsed = 0
        self.notice = ""
        self.notice_time = 0

    @property
    def total(self):
        return sum(sum(o["type"] == "coin" for o in r.level.objects) for r in self.world.rooms.values())

    @property
    def collected(self):
        return sum(sum(o["type"] == "coin" and o["id"] in r.state.removed
                       for o in r.level.objects) for r in self.world.rooms.values())

    def freeze_interpolation(self):
        b = self.player.body
        b.previous_x, b.previous_y = b.x,b.y
        for p in self.world.current.platforms:
            p.previous = p.box

    def enter(self, room_id, entry_id):
        self.player.respawn(self.world.enter(room_id,entry_id))
        self.freeze_interpolation()

    def die(self):
        self.audio.play("hurt")
        self.deaths += 1
        self.player.respawn(self.world.respawn())
        self.freeze_interpolation()

    def nearby_door(self):
        body = self.player.body.box
        for door in self.world.current.objects("door"):
            if body.overlaps(Box(door["x"]-14,door["y"]-8,door.get("w",32)+28,door.get("h",58)+16)):
                return door
        return None

    def nearby_interaction(self):
        body = self.player.body.box
        choices = []
        for obj in self.world.current.objects():
            if obj["type"] not in {"door","switch"}:
                continue
            if obj["type"] == "switch" and (obj.get("activation","interact") != "interact" or
                    (self.world.current_id,obj["id"]) in self.world.mechanisms.active):
                continue
            w,h = obj.get("w",32 if obj["type"] == "door" else 24),obj.get("h",58 if obj["type"] == "door" else 30)
            if body.overlaps(Box(obj["x"]-14,obj["y"]-8,w+28,h+16)):
                distance = (body.x+body.w/2-obj["x"]-w/2)**2+(body.y+body.h/2-obj["y"]-h/2)**2
                choices.append((distance,obj["id"],obj))
        return min(choices,key=lambda item:(item[0],item[1]))[2] if choices else None

    def blocked_notice(self,obj):
        names = []
        for room_id,switch_id in sorted(requirements(obj)-self.world.mechanisms.active):
            switch = next(o for o in self.world.rooms[room_id].objects("switch") if o["id"] == switch_id)
            names.append(switch.get("label",switch_id))
        self.notice,self.notice_time = "Falta ativar: "+", ".join(names)[:78],2.5

    def activate_switch(self,obj):
        if self.world.mechanisms.activate(self.world.current_id,obj):
            self.audio.play("switch")
            self.notice,self.notice_time = obj.get("label","Interruptor")[:65]+" · ATIVADO",2.5

    def progress_action(self,load=False):
        if self.transition.active:
            self.progress_message = "Espera pelo fim da passagem entre salas."
            self.audio.play("blocked")
        else:
            try:
                if load:
                    stats = self.progress_slot.load(self.world,self.movement_settings)
                    self.player.respawn(self.world.respawn())
                    self.transition = FadeTransition()
                    self.deaths,self.elapsed,self.won = stats["deaths"],stats["elapsed"],stats["won"]
                    self.paused = False
                    self.notice,self.notice_time = "",0
                    self.freeze_interpolation()
                    self.view.update(self.player.state,0)
                    self.progress_message = "Progresso carregado · retomado no checkpoint."
                    self.audio.stop()
                    self.audio.play("load")
                else:
                    self.progress_slot.save(self.world,self.movement_settings,dict(deaths=self.deaths,elapsed=self.elapsed,won=self.won))
                    self.progress_message = "Progresso guardado · F9 retoma no checkpoint."
                    self.audio.play("save")
                if self.progress_slot.path is None:
                    self.progress_message += " [Só neste teste]"
            except (OSError,ValueError) as error:
                self.audio.play("error")
                self.progress_message = str(error)
        self.progress_message_time = 5

    def update(self, dt, actions):
        self.progress_message_time = max(0,self.progress_message_time-dt)
        if "load_progress" in actions.pressed or "save_progress" in actions.pressed:
            self.progress_action("load_progress" in actions.pressed)
            self.freeze_interpolation()
            return
        if "debug" in actions.pressed:
            self.debug = not self.debug
        if "pause" in actions.pressed:
            self.paused = not self.paused
        if "reset" in actions.pressed:
            self.reset()
            self.progress_message = "Partida reiniciada. A gravação anterior continua disponível com F9."
            self.progress_message_time = 5
        if self.paused and "step" not in actions.pressed:
            self.freeze_interpolation()
            return
        if self.transition.active:
            self.freeze_interpolation()
            self.transition.update(dt)
            return
        if "restart" in actions.pressed:
            self.player.respawn(self.world.respawn())
            self.freeze_interpolation()
        if self.won:
            self.freeze_interpolation()
            return
        self.elapsed += dt
        self.notice_time = max(0,self.notice_time-dt)
        room = self.world.current
        room.update(dt)
        self.player.update(dt,actions,room.level.colliders,room.platforms)
        for event in set(self.player.controller.motion_events):
            self.audio.play(event)
        b = self.player.body
        b.x = max(0,min(b.x,room.level.width-b.w))
        if b.crushed or b.y > room.level.height+64:
            self.die()
            return
        if any(b.box.overlaps(Box(o["x"],o["y"],o.get("w",24),o.get("h",30))) for o in room.objects("hazard")):
            self.die()
            return
        for obj in room.objects("switch"):
            if obj.get("activation","interact") == "touch" and b.box.overlaps(Box(obj["x"],obj["y"],obj.get("w",24),obj.get("h",30))):
                self.activate_switch(obj)
        for obj in room.objects():
            if not b.box.overlaps(Box(obj["x"],obj["y"],obj.get("w",24),obj.get("h",30))):
                continue
            kind = obj["type"]
            if kind == "coin":
                self.audio.play("pickup")
                room.state.removed.add(obj["id"])
            elif kind == "checkpoint":
                if self.world.checkpoint != (room.id,(obj["x"],obj["y"])):
                    self.audio.play("checkpoint")
                    self.world.set_checkpoint((obj["x"],obj["y"]))
                    room.state.flags["checkpoint"] = obj["id"]
                    self.notice, self.notice_time = "Sinal guardado · checkpoint ativo nesta sala",2.5
            elif kind == "hazard":
                self.die()
                return
            elif kind == "goal":
                if not self.world.mechanisms.enabled(obj):
                    self.blocked_notice(obj)
                elif self.collected == self.total:
                    if not self.won:
                        self.audio.play("victory")
                    self.won = True
                else:
                    self.notice, self.notice_time = "Faltam cristais. Podes regressar à outra sala pela porta.",2
        interaction = self.nearby_interaction()
        if interaction and "interact" in actions.pressed and not self.won:
            if not self.world.mechanisms.enabled(interaction):
                self.audio.play("blocked")
                self.blocked_notice(interaction)
            elif interaction["type"] == "switch":
                self.activate_switch(interaction)
            else:
                destination = (interaction["target_room"],interaction["target_entry"])
                self.audio.play("door")
                self.transition.start(lambda: self.enter(*destination))
        self.view.update(self.player.state,dt)

    def text(self,surface,text,x,y,color=(186,201,216),font=None):
        text = getattr(self,"format_controls",str)(text)
        surface.blit((font or self.small).render(text,True,color),(round(x),round(y)))

    def draw(self,surface,alpha):
        room = self.world.current
        archive = room.id == "archive"
        accent = (180,156,244) if archive else (99,224,193)
        surface.fill((15,18,34))
        for x in range(32,960,64):
            pygame.draw.line(surface,(24,30,49),(x,96),(x,544))
        for y in range(96,544,64):
            pygame.draw.line(surface,(24,30,49),(0,y),(960,y))
        # Architectural silhouette and a subtle room-specific focal shape.
        pygame.draw.circle(surface,(25,30,50),(750,210),95,1)
        pygame.draw.circle(surface,(32,37,60),(750,210),73,1)
        for x in (48,224,704,880):
            pygame.draw.rect(surface,(21,27,44),(x,160,25,352))
            pygame.draw.rect(surface,(34,42,62),(x,160,25,5))
        self.text(surface,"02" if archive else "01",731,185,(53,58,86),self.large)
        for c in room.level.colliders:
            r = c.box
            if c.slope:
                draw_ramp(surface,(r.x,r.y,r.w,r.h),c.slope)
            elif c.one_way:
                pygame.draw.rect(surface,(72,71,103),(r.x,r.y,r.w,8),border_radius=2)
                pygame.draw.line(surface,accent,(r.x+1,r.y),(r.right-1,r.y),2)
            else:
                pygame.draw.rect(surface,(40,46,65),(r.x,r.y,r.w,r.h))
                pygame.draw.rect(surface,(25,31,47),(r.x+2,r.y+4,r.w-4,r.h-6),border_radius=3)
                pygame.draw.line(surface,(68,76,98),(r.x,r.y),(r.right,r.y))
        for p in room.platforms:
            pygame.draw.line(surface,(58,66,86),(p.start[0]+p.w/2,p.start[1]+6),
                             (p.end[0]+p.w/2,p.end[1]+6),2)
            r = p.interpolated(alpha)
            pygame.draw.rect(surface,(37,93,100),(r.x,r.y,r.w,r.h),border_radius=4)
            pygame.draw.rect(surface,accent,(r.x,r.y,r.w,3),border_radius=1)
            for dx in range(10,int(r.w)-8,18):
                pygame.draw.line(surface,(123,208,196),(r.x+dx,r.y+5),(r.x+dx+5,r.y+9),2)
        for obj in room.objects():
            x,y,kind = obj["x"],obj["y"],obj["type"]
            if kind == "coin":
                bob = math.sin(self.elapsed*3+x)*2
                pygame.draw.circle(surface,(64,53,64),(int(x+12),int(y+13+bob)),18)
                pygame.draw.polygon(surface,(255,206,118),[(x+12,y+bob),(x+21,y+13+bob),(x+12,y+26+bob),(x+3,y+13+bob)])
                pygame.draw.line(surface,(255,239,189),(x+12,y+5+bob),(x+12,y+21+bob),2)
            elif kind == "door":
                door_color = accent if self.world.mechanisms.enabled(obj) else (244,160,107)
                pygame.draw.rect(surface,(33,37,57),(x-5,y-6,42,64),border_radius=7)
                pygame.draw.rect(surface,door_color,(x,y,32,58),2,border_radius=5)
                pygame.draw.circle(surface,accent,(int(x+24),int(y+32)),2)
                self.text(surface,obj.get("label","PORTA"),x-16,y-25,door_color)
                if not self.world.mechanisms.enabled(obj):
                    pygame.draw.rect(surface,door_color,(x+10,y+21,12,14),2)
            elif kind == "switch":
                active = (room.id,obj["id"]) in self.world.mechanisms.active
                color = (112,242,191) if active else (249,190,102)
                w,h = obj.get("w",24),obj.get("h",30)
                pygame.draw.rect(surface,(37,50,66),(x,y,w,h),border_radius=3)
                pygame.draw.rect(surface,color,(x,y,w,h),2,border_radius=3)
                pygame.draw.line(surface,color,(x+w/2,y+h*.7),(x+w*(.8 if active else .2),y+h*.25),3)
                self.text(surface,obj.get("label","Interruptor")[:30],max(4,min(x-30,730)),y-24,color)
                self.text(surface,"ATIVO" if active else "TOCAR" if obj.get("activation") == "touch" else "[E]",x,y+h+5,color)
            elif kind == "checkpoint":
                active = self.world.checkpoint == (room.id,(x,y))
                color = (111,239,196) if active else (118,134,159)
                pygame.draw.line(surface,color,(x+10,y+30),(x+10,y-16),3)
                pygame.draw.polygon(surface,color,[(x+12,y-16),(x+35,y-9),(x+12,y)])
            elif kind == "goal":
                color = (117,241,197) if self.collected == self.total and self.world.mechanisms.enabled(obj) else (121,125,158)
                pygame.draw.rect(surface,(29,39,59),(x-7,y-10,48,68),border_radius=19)
                pygame.draw.ellipse(surface,color,(x,y-5,34,63),3)
                self.text(surface,"NÚCLEO",x-7,y-29,color)
            elif kind == "hazard":
                for dx in range(0,int(obj.get("w",24)),16):
                    pygame.draw.polygon(surface,(232,109,132),[(x+dx,y+16),(x+dx+8,y),(x+dx+16,y+16)])
        x,y = self.player.body.interpolated(alpha)
        self.view.draw(surface,(x-4,y-10),self.player.controller.facing)
        pygame.draw.rect(surface,(9,13,25),(0,0,960,88))
        self.text(surface,"PLATFORM2D  /  "+("LABORATÓRIO 07" if self.has_mechanisms else "LABORATÓRIO 02"),25,12,accent)
        self.text(surface,self.world.name[:20],24,32,(235,238,249),self.title)
        self.text(surface,room.level.name,300,46,(156,170,197),self.font)
        self.text(surface,f"CRISTAIS {self.collected:02}/{self.total:02}",757,24,(255,206,118))
        self.text(surface,f"TENTATIVAS {self.deaths+1:02}",757,47)
        pygame.draw.line(surface,(46,52,77),(24,87),(936,87))
        if archive:
            self.text(surface,"A TRAVESSIA",330,136,accent)
            self.text(surface,"Salta para a plataforma e deixa-te transportar.",330,160)
            self.text(surface,"A porta guarda o progresso de cada sala.",330,181,(122,137,165))
        elif room.id == "atrium":
            self.text(surface,"O ELEVADOR",70,134,accent)
            self.text(surface,"Sobe a bordo. O cristal está no piso superior.",70,158)
            self.text(surface,"Explora as duas salas e recupera os quatro cristais.",70,180,(122,137,165))
        else:
            self.text(surface,"MECANISMOS",70,134,accent)
            self.text(surface,"Ativa interruptores para libertar portas e a saída.",70,158)
            self.text(surface,"E: interagir · R: checkpoint · F2: reiniciar mecanismos",70,180,(122,137,165))
        interaction = self.nearby_interaction()
        if interaction:
            label = "BLOQUEADO" if not self.world.mechanisms.enabled(interaction) else "ATIVAR" if interaction["type"] == "switch" else "ATRAVESSAR"
            self.text(surface,"[E] "+label,max(10,min(interaction["x"]-40,810)),interaction["y"]-47,accent)
        if self.notice_time:
            self.text(surface,self.notice,170,105,(134,235,194))
        if self.debug:
            draw_debug(surface,self.small,self.player.body,self.player.state,room.level.colliders,(0,0),32)
            self.text(surface,f"ROOM {room.id} | PLATFORMS {len(room.platforms)} | N: avançar em pausa",28,193)
            self.text(surface,f"INTERRUPTORES ATIVOS: {len(self.world.mechanisms.active)}",28,214)
        pygame.draw.rect(surface,(9,13,25),(0,544,960,32))
        self.text(surface,"A/D: mover  ESPAÇO: salto  E: usar  R: checkpoint  F6: guardar  F9: carregar  F2: reiniciar  P: pausa",20,555)
        if self.paused or self.won:
            cover = pygame.Surface((960,576),pygame.SRCALPHA)
            cover.fill((5,9,23,220))
            surface.blit(cover,(0,0))
            title = ("Percurso concluído" if self.has_mechanisms else "Arquivo recuperado") if self.won else "Em pausa"
            image = self.large.render(title,True,(231,236,249))
            surface.blit(image,(480-image.get_width()/2,219))
            detail = f"{self.total} cristais · {len(self.world.rooms)} salas · F2 para recomeçar" if self.won else "P para continuar · N para uma atualização"
            image = self.font.render(detail,True,accent)
            surface.blit(image,(480-image.get_width()/2,286))
        if self.transition.active:
            cover = pygame.Surface((960,576))
            cover.fill((5,9,23))
            cover.set_alpha(self.transition.opacity)
            surface.blit(cover,(0,0))
        if self.progress_message_time:
            pygame.draw.rect(surface,(13,31,43),(18,91,924,64),border_radius=7)
            words = self.progress_message.split()
            lines,line = [],""
            for word in words:
                candidate = (line+" "+word).strip()
                if self.small.size(candidate)[0] > 888 and line:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
            for index,line in enumerate(lines[:3]):
                self.text(surface,line,30,101+index*17,(159,244,217))
