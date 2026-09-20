from platform2d.rendering.terrain import draw_ramp
"""Demo rules: briefing, two guards, terminal and an exit gate."""
from math import cos, sin, radians
from pathlib import Path
import pygame

from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController, Movement
from platform2d.actors.enemy import PatrolEnemy
from platform2d.gameplay.combat import Attack, Health
from platform2d.gameplay.interaction import Interaction, choose_interaction
from platform2d.physics.body import Body, Box
from platform2d.physics.collision import Collider
from platform2d.rendering.animation import Clip, SpriteView, slice_sheet
from platform2d.tools.debug_overlay import draw_debug
from platform2d.audio import SilentAudio


class SentinelsScene:
    def __init__(self,level,settings):
        self.audio = SilentAudio()
        self.level = level
        if (level.width,level.height) != (960,576):
            raise ValueError("Sentinelas: o mapa deve medir 960×576.")
        for kind in ("npc","switch","gate","goal"):
            if len(self.objects(kind)) != 1:
                raise ValueError(f"Sentinelas: é necessário exatamente um objeto {kind}.")
        self.player = Character(Body(*level.spawn),ArcadeController(Movement(**settings["movement"])))
        sheet = pygame.image.load(str(Path(__file__).parents[1]/"classic/assets/explorer.png"))
        self.view = SpriteView(slice_sheet(sheet,(32,40)),{
            "idle":Clip((0,1),3),"run":Clip((2,3,4,5),11),"jump":Clip((6,),1),"fall":Clip((7,),1)})
        self.font = pygame.font.SysFont("segoeui",18)
        self.small = pygame.font.SysFont("consolas",13)
        self.title = pygame.font.SysFont("segoeui",28,bold=True)
        self.large = pygame.font.SysFont("segoeui",40,bold=True)
        self.debug = self.paused = False
        self.reset()

    def objects(self,kind):
        return [o for o in self.level.objects if o["type"] == kind]

    def reset(self):
        self.defeated = set()
        self.briefed = self.gate_open = self.won = False
        self.deaths = 0
        self.elapsed = 0
        self.notice = ""
        self.notice_time = 0
        self.dialogue = []
        self.dialogue_index = 0
        self.health = Health(3,.9)
        self.attack = Attack()
        self.respawn()

    def respawn(self):
        self.player.respawn(self.level.spawn)
        self.health.restore()
        self.attack.cancel()
        self.enemies = [PatrolEnemy(o["id"],Body(o["x"],o["y"]),o["left"],o["right"],o.get("facing",-1))
                        for o in self.objects("enemy") if o["id"] not in self.defeated]

    @property
    def colliders(self):
        result = list(self.level.colliders)
        if not self.gate_open:
            o = self.objects("gate")[0]
            result.append(Collider(Box(o["x"],o["y"],o["w"],o["h"])))
        return result

    def talk(self):
        self.attack.cancel()
        self.dialogue = [
            "Sou a Íris. Os dois guardas bloquearam a saída do posto.",
            "J lança um golpe curto. Aproxima-te e ataca antes de te tocarem.",
            "Derrota os guardas e usa E no terminal à direita para abrir a saída."]
        self.dialogue_index = 0

    def activate(self):
        if not self.briefed:
            self.notice = "Fala primeiro com a Íris, junto à entrada."
        elif len(self.defeated) < len(self.objects("enemy")):
            self.notice = "Terminal bloqueado: derrota os dois guardas."
        else:
            self.gate_open = True
            self.audio.play("switch")
            self.notice = "Acesso autorizado. A saída está aberta."
        self.notice_time = 2.5

    def interaction(self):
        npc,terminal = self.objects("npc")[0],self.objects("switch")[0]
        return choose_interaction(self.player.body,[
            Interaction(npc["id"],"Falar com Íris",(npc["x"]+12,npc["y"]+15),self.talk,60),
            Interaction(terminal["id"],"Ativar terminal",(terminal["x"]+14,terminal["y"]+17),self.activate,55,
                        enabled=not self.gate_open)])

    def freeze(self):
        for character in [self.player]+[e.character for e in self.enemies]:
            b = character.body
            b.previous_x,b.previous_y = b.x,b.y

    def update(self,dt,actions):
        if "debug" in actions.pressed:
            self.debug = not self.debug
        if "pause" in actions.pressed:
            self.paused = not self.paused
        if "reset" in actions.pressed:
            self.reset()
        if self.paused and "step" not in actions.pressed:
            self.freeze()
            return
        if self.dialogue:
            self.freeze()
            if "interact" in actions.pressed:
                self.dialogue_index += 1
                if self.dialogue_index >= len(self.dialogue):
                    self.dialogue = []
                    self.briefed = True
            return
        if self.won:
            self.freeze()
            return
        if "restart" in actions.pressed:
            self.respawn()
        self.elapsed += dt
        self.notice_time = max(0,self.notice_time-dt)
        self.health.update(dt)
        solids = self.colliders
        if "attack" in actions.pressed and self.player.stun_left <= 0:
            if self.attack.start(self.player.controller.facing):
                self.audio.play("attack")
        self.player.update(dt,actions,solids)
        for event in set(self.player.controller.motion_events):
            self.audio.play(event)
        b = self.player.body
        b.x = max(0,min(b.x,960-b.w))
        self.attack.update(dt)
        for enemy in self.enemies:
            enemy.update(dt,b,solids)
            if enemy.health.dead:
                continue
            if self.attack.connects(enemy.id,b,enemy.body.box,solids):
                self.audio.play("hit")
                enemy.hit(self.attack.spec.damage,self.attack.facing)
                if enemy.health.dead:
                    self.defeated.add(enemy.id)
            if not enemy.health.dead and enemy.machine.current != "hurt" and b.box.overlaps(enemy.body.box):
                if self.health.hit():
                    self.audio.play("hurt")
                    self.attack.cancel()
                    self.player.knockback(-210 if b.x < enemy.body.x else 210)
        if self.health.dead or b.y > self.level.height+64:
            self.audio.play("hurt")
            self.deaths += 1
            self.respawn()
            return
        if "interact" in actions.pressed:
            action = self.interaction()
            if action:
                action.callback()
        goal = self.objects("goal")[0]
        if self.gate_open and b.box.overlaps(Box(goal["x"],goal["y"],goal["w"],goal["h"])):
            self.audio.play("victory")
            self.won = True
        self.view.update(self.player.state,dt)

    def text(self,surface,text,x,y,color=(185,199,219),font=None):
        text = getattr(self,"format_controls",str)(text)
        surface.blit((font or self.small).render(text,True,color),(round(x),round(y)))

    def draw(self,surface,alpha):
        surface.fill((16,20,34))
        for x in range(32,960,64):
            pygame.draw.line(surface,(25,32,49),(x,88),(x,544))
        for y in range(96,544,64):
            pygame.draw.line(surface,(25,32,49),(0,y),(960,y))
        for x in (280,608,832):
            pygame.draw.rect(surface,(25,34,51),(x,224,56,288))
            for y in (240,304,368):
                pygame.draw.rect(surface,(39,56,74),(x+8,y,40,4))
        pygame.draw.circle(surface,(51,61,82),(496,230),64,1)
        self.text(surface,"VIGIA / 03",456,222,(76,92,118))
        if self.debug:
            vision = pygame.Surface((960,576),pygame.SRCALPHA)
            for e in self.enemies:
                if e.health.dead:
                    continue
                b = e.body
                center = (b.x+b.w/2,b.y+b.h/2)
                facing = e.character.controller.facing
                points = [center]+[(center[0]+cos(radians(angle))*200*facing,center[1]+sin(radians(angle))*200)
                                   for angle in range(-55,56,5)]
                pygame.draw.polygon(vision,(238,145,85,35),points)
            surface.blit(vision,(0,0))
        for collider in self.level.colliders:
            b = collider.box
            if collider.slope:
                draw_ramp(surface,(b.x,b.y,b.w,b.h),collider.slope)
            elif collider.one_way:
                pygame.draw.rect(surface,(81,101,125),(b.x,b.y,b.w,8),border_radius=2)
                pygame.draw.line(surface,(145,189,208),(b.x,b.y),(b.right,b.y),2)
            else:
                pygame.draw.rect(surface,(43,55,72),(b.x,b.y,b.w,b.h))
                pygame.draw.rect(surface,(26,35,50),(b.x+2,b.y+4,b.w-4,b.h-6),border_radius=3)
        npc = self.objects("npc")[0]
        x,y = npc["x"],npc["y"]
        pygame.draw.rect(surface,(146,125,225),(x+3,y+12,19,18),border_radius=4)
        pygame.draw.rect(surface,(217,202,240),(x+5,y-1,16,15),border_radius=5)
        pygame.draw.rect(surface,(51,48,83),(x+12,y+4,11,5),border_radius=2)
        self.text(surface,"ÍRIS",x-1,y-24,(195,177,247))
        for enemy in self.enemies:
            if enemy.health.dead:
                continue
            x,y = enemy.body.interpolated(alpha)
            alert = enemy.machine.current == "chase"
            color = (255,146,113) if alert else (205,121,116)
            if enemy.machine.current == "hurt":
                color = (248,219,181)
            pygame.draw.rect(surface,color,(x+2,y+11,20,18),border_radius=3)
            pygame.draw.rect(surface,(105,69,86),(x,y,24,16),border_radius=4)
            dx = 3 if enemy.character.controller.facing < 0 else 14
            pygame.draw.rect(surface,(255,215,127),(x+dx,y+5,8,4))
            for i in range(enemy.health.maximum):
                pygame.draw.rect(surface,color if i < enemy.health.remaining else (55,45,60),(x+i*14,y-9,10,3))
            labels = {"patrol":"PATRULHA","chase":"ALERTA!","search":"PROCURAR","hurt":"ATINGIDO"}
            self.text(surface,labels.get(enemy.machine.current,""),x-19,y-29,color)
            if self.debug and enemy.visible:
                b = self.player.body
                pygame.draw.line(surface,(255,112,114),(x+12,y+15),(b.x+12,b.y+15),1)
        terminal = self.objects("switch")[0]
        x,y = terminal["x"],terminal["y"]
        pygame.draw.rect(surface,(55,70,87),(x,y,28,34),border_radius=4)
        pygame.draw.rect(surface,(112,235,177) if self.gate_open else (244,190,104),(x+5,y+5,18,12),border_radius=2)
        gate = self.objects("gate")[0]
        if not self.gate_open:
            pygame.draw.rect(surface,(76,55,67),(gate["x"],gate["y"],gate["w"],gate["h"]))
            for y in range(int(gate["y"]),512,16):
                pygame.draw.line(surface,(239,150,119),(gate["x"]+2,y),(gate["x"]+14,y+8),3)
        pygame.draw.rect(surface,(96,180,177),(930,454,24,58),2,border_radius=8)
        x,y = self.player.body.interpolated(alpha)
        if self.health.immune_left <= 0 or int(self.elapsed*18)%2:
            self.view.draw(surface,(x-4,y-10),self.player.controller.facing)
        if self.attack.active:
            hit = self.attack.box(Box(x,y,self.player.body.w,self.player.body.h))
            glow = pygame.Surface((int(hit.w),int(hit.h)),pygame.SRCALPHA)
            glow.fill((127,244,219,110))
            surface.blit(glow,(hit.x,hit.y))
            pygame.draw.rect(surface,(194,255,231),(hit.x,hit.y,hit.w,hit.h),2,border_radius=5)
        if self.debug:
            draw_debug(surface,self.small,self.player.body,self.player.state,self.colliders,(0,0),32)
        pygame.draw.rect(surface,(9,14,25),(0,0,960,88))
        self.text(surface,"PLATFORM2D / LABORATÓRIO 03",25,12,(249,181,116))
        self.text(surface,"Sentinelas",24,33,(238,239,247),self.title)
        self.text(surface,"VIDA",635,23)
        for i in range(3):
            pygame.draw.rect(surface,(124,229,190) if i < self.health.remaining else (48,61,74),(680+i*20,24,14,12),border_radius=3)
        self.text(surface,f"GUARDAS {len(self.defeated)}/{len(self.objects('enemy'))}",787,23,(249,181,116))
        self.text(surface,f"TENTATIVAS {self.deaths+1:02}",787,47)
        objective = "1. Fala com Íris" if not self.briefed else "2. Derrota os guardas [J]" if len(self.defeated)<len(self.objects('enemy')) else "3. Ativa o terminal [E]" if not self.gate_open else "4. Atravessa a saída"
        self.text(surface,objective,265,47,(161,191,207))
        if not self.debug:
            self.text(surface,"OBSERVAR · APROXIMAR · ATACAR",34,123,(249,181,116))
            self.text(surface,"Os guardas só perseguem o que conseguem ver.",34,147)
            self.text(surface,"J / X: ataque curto     E: falar ou usar o terminal",34,169,(134,158,183))
        if self.notice_time:
            self.text(surface,self.notice,70,207,(130,235,194))
        action = self.interaction()
        if action and not self.dialogue:
            self.text(surface,"[E] "+action.label,max(16,min(self.player.body.x-20,735)),self.player.body.y-47,(175,244,213))
        pygame.draw.rect(surface,(9,14,25),(0,544,960,32))
        self.text(surface,"A D  mover   ESPAÇO  saltar   J  atacar   E  interagir   R  voltar   F1  debug   P  pausa   F2  reiniciar",17,555)
        if self.dialogue:
            pygame.draw.rect(surface,(13,20,37),(36,278,888,146),border_radius=10)
            pygame.draw.rect(surface,(141,126,203),(36,278,888,146),2,border_radius=10)
            self.text(surface,"ÍRIS / COMUNICAÇÕES",58,297,(195,177,247))
            self.text(surface,self.dialogue[self.dialogue_index],58,333,(233,235,244),self.font)
            self.text(surface,f"[E] Continuar   {self.dialogue_index+1}/{len(self.dialogue)}",58,391,(159,179,205))
        if self.paused or self.won:
            cover = pygame.Surface((960,576),pygame.SRCALPHA)
            cover.fill((5,10,22,215))
            surface.blit(cover,(0,0))
            message = "Posto libertado" if self.won else "Em pausa"
            image = self.large.render(message,True,(227,245,234))
            surface.blit(image,(480-image.get_width()/2,215))
            self.text(surface,"F2 para recomeçar" if self.won else "P para continuar · N para avançar",350,284)
