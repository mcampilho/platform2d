"""Game rules consume projectile impacts; the projectile system never applies damage."""
from pathlib import Path
import pygame

from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController,Movement
from platform2d.actors.perception import segment_hits_box
from platform2d.audio import SilentAudio
from platform2d.gameplay.combat import Health
from platform2d.gameplay.projectiles import ProjectileSystem,Target,Weapon,WeaponSpec
from platform2d.gameplay.ranged_config import weapon_spec,validate_target
from platform2d.gameplay.inventory import Inventory,CATALOG,validate_pickup,upgraded_weapon
from platform2d.gameplay.mission import THEMES,validate_mission,objectives_complete
from platform2d.physics.body import Body,Box
from platform2d.rendering.animation import Clip,SpriteView,slice_sheet
from platform2d.rendering.terrain import draw_ramp
from platform2d.tools.debug_overlay import draw_debug


class RangedScene:
    FIXED_SIZE = True
    REQUIRES_GOAL = True

    def set_language(self,language):
        from examples.campaign.locale import CampaignLocale
        self.locale=CampaignLocale(language)
    def __init__(self,level,settings):
        self.level = level
        if self.FIXED_SIZE and (level.width,level.height) != (960,576):
            raise ValueError("Combate: o mapa deve medir 960×576.")
        if self.REQUIRES_GOAL and not any(o["type"] == "goal" for o in level.objects):
            raise ValueError("Combate: falta uma saída.")
        if any(o["id"] == "player" for o in level.objects):
            raise ValueError("O ID player está reservado ao jogador.")
        self.objects = [o for o in level.objects if o["type"] in {"turret","target"}]
        for obj in self.objects:
            validate_target(obj)
        validate_mission(level.properties,level.objects)
        self.armed = level.properties.get("weapon_enabled",True)
        self.coins = [o for o in level.objects if o["type"] == "coin"]
        self.palette = THEMES[level.properties.get("theme","station")]
        self.spec = weapon_spec(level.properties)
        self.pickups = [o for o in level.objects if o["type"] == "pickup"]
        for obj in self.pickups:
            validate_pickup(obj)
        self.audio = SilentAudio()
        self.player = Character(Body(*level.spawn),ArcadeController(Movement(**settings["movement"])))
        sheet = pygame.image.load(str(Path(__file__).parents[1]/"classic/assets/explorer.png"))
        self.view = SpriteView(slice_sheet(sheet,(32,40)),{
            "idle":Clip((0,1),3),"run":Clip((2,3,4,5),11),"jump":Clip((6,),1),"fall":Clip((7,),1)})
        self.small = pygame.font.SysFont("consolas",13)
        self.title = pygame.font.SysFont("segoeui",27,bold=True)
        self.large = pygame.font.SysFont("segoeui",40,bold=True)
        self.projectiles = ProjectileSystem()
        self.weapon = Weapon(self.spec)
        self.health = Health(5,.8)
        self.debug = self.paused = False
        self.reset()

    @staticmethod
    def box(obj):
        return Box(obj["x"],obj["y"],obj.get("w",24),obj.get("h",30))

    def reset(self):
        self.inventory = Inventory()
        self.collected_items = set()
        self.pickup_contacts = set()
        self.inventory_notice = ""
        self.inventory_notice_time = 0
        self.weapon.spec = upgraded_weapon(self.spec,self.inventory)
        self.destroyed = set()
        self.respawn_point = self.level.spawn
        self.active_checkpoint = None
        self.deaths = self.shots = self.elapsed = 0
        self.won = False
        self.respawn()

    def respawn(self):
        self.pickup_contacts.clear()
        self.player.respawn(self.respawn_point)
        self.health.restore()
        self.weapon.reset()
        self.projectiles.clear()
        self.sparks = []
        self.targets = {o["id"]:Health(o.get("hp",2),0) for o in self.objects if o["id"] not in self.destroyed}
        self.turrets = {}
        for obj in self.objects:
            if obj["type"] == "turret" and obj["id"] not in self.destroyed:
                speed = obj.get("projectile_speed",240)
                weapon = Weapon(WeaponSpec(speed=speed,cooldown=obj.get("interval",1.2),
                                           lifetime=obj.get("range",420)/speed,width=8,height=6))
                weapon.remaining = weapon.spec.cooldown
                self.turrets[obj["id"]] = weapon

    def freeze(self):
        b = self.player.body
        b.previous_x,b.previous_y = b.x,b.y
        self.projectiles.freeze()

    @property
    def objectives_ready(self):
        return objectives_complete(self.level.objects,self.destroyed,self.collected_items)

    def collect_items(self,actions):
        for obj in self.coins:
            if obj["id"] not in self.collected_items and self.player.body.box.overlaps(self.box(obj)):
                self.collected_items.add(obj["id"])
                self.inventory_notice = "Cristal de missão recolhido."
                self.inventory_notice_time = 2.5
                self.audio.play("pickup")
        if "use_item" in actions.pressed:
            if not self.health.dead and self.health.remaining < self.health.maximum and self.inventory.take("medkit"):
                self.health.heal(2)
                self.inventory_notice = "Kit usado: até 2 pontos de vida recuperados."
                self.audio.play("pickup")
            else:
                self.inventory_notice = "Vida completa: kit conservado." if self.health.remaining == self.health.maximum else "Não tens kits médicos."
                self.audio.play("blocked")
            self.inventory_notice_time = 2.5
        contacts = set()
        for obj in self.pickups:
            if obj["id"] in self.collected_items or not self.player.body.box.overlaps(self.box(obj)):
                continue
            contacts.add(obj["id"])
            item,quantity = obj.get("item","medkit"),obj.get("quantity",1)
            if self.inventory.add(item,quantity):
                self.collected_items.add(obj["id"])
                self.weapon.spec = upgraded_weapon(self.spec,self.inventory)
                self.inventory_notice = self.tr('notice.picked','Recolhido: {item} ×{quantity}',item=self.tr('item.'+item,CATALOG[item].label),quantity=quantity)
                self.inventory_notice_time = 2.5
                self.audio.play("pickup")
            elif obj["id"] not in self.pickup_contacts:
                self.inventory_notice = self.tr('notice.full','Sem espaço para esta quantidade de {item}.',item=self.tr('item.'+item,CATALOG[item].label))
                self.inventory_notice_time = 2.5
                self.audio.play("blocked")
        self.pickup_contacts = contacts

    def update_encounters(self,dt,actions):
        """Optional close-combat encounters resolve before death and goal checks."""

    def prepare_world(self,dt,actions):
        """Optional dynamic geometry and environmental sensors before movement."""

    def update(self,dt,actions):
        if "debug" in actions.pressed:
            self.debug = not self.debug
        if "pause" in actions.pressed:
            self.paused = not self.paused
        if "reset" in actions.pressed:
            self.reset()
        if self.paused and "step" not in actions.pressed or self.won:
            self.freeze()
            return
        if "restart" in actions.pressed:
            self.respawn()
            return
        self.elapsed += dt
        self.inventory_notice_time = max(0,self.inventory_notice_time-dt)
        self.health.update(dt)
        self.weapon.update(dt)
        self.sparks = [(point,life-dt,team) for point,life,team in self.sparks if life > dt]
        self.prepare_world(dt,actions)
        self.player.update(dt,actions,self.level.colliders)
        for event in set(self.player.controller.motion_events):
            self.audio.play(event)
        b = self.player.body
        b.x = max(0,min(b.x,self.level.width-b.w))
        # Resolve existing shots before spawning new ones: a shot is born at
        # the end of this step and travels from that position on the next step.
        targets = [Target("player","player",b.box,Box(b.previous_x,b.previous_y,b.w,b.h))]
        targets.extend(Target(o["id"],"enemy",self.box(o)) for o in self.objects if o["id"] not in self.destroyed)
        for impact in self.projectiles.update(dt,self.level.colliders,targets):
            self.sparks.append((impact.point,.16,impact.team))
            if impact.target_id == "player":
                if self.health.hit(impact.damage):
                    self.audio.play("hurt")
                    self.player.knockback(impact.direction[0]*130,-90,.12)
            elif impact.target_id in self.targets:
                health = self.targets[impact.target_id]
                if health.hit(impact.damage):
                    self.audio.play("hit")
                    if health.dead:
                        self.destroyed.add(impact.target_id)
        self.update_encounters(dt,actions)
        if self.health.dead or b.y > self.level.height+64:
            self.deaths += 1
            self.audio.play("hurt")
            self.respawn()
            return
        if any(o["type"] == "hazard" and b.box.overlaps(self.box(o)) for o in self.level.objects):
            self.deaths += 1
            self.audio.play("hurt")
            self.respawn()
            return
        self.collect_items(actions)
        for obj in self.level.objects:
            if not b.box.overlaps(self.box(obj)):
                continue
            if obj["type"] == "checkpoint" and self.active_checkpoint != obj["id"]:
                self.active_checkpoint = obj["id"]
                self.respawn_point = obj["x"],obj["y"]
                self.audio.play("checkpoint")
            if obj["type"] == "goal" and self.objectives_ready:
                self.won = True
                self.projectiles.clear()
                self.audio.play("victory")
                return
        if self.armed and "shoot" in actions.held and self.player.stun_left <= 0:
            facing = self.player.controller.facing
            # Start just inside the body edge: a nearby wall cannot be skipped
            # by placing a muzzle beyond it.
            origin = (b.x+b.w if facing > 0 else b.x,b.y+b.h/2)
            if self.weapon.fire(self.projectiles,origin,(facing,0),"player","player"):
                self.shots += 1
                self.audio.play("shoot")
        for obj in self.objects:
            if obj["id"] in self.destroyed or obj["type"] != "turret":
                continue
            weapon = self.turrets[obj["id"]]
            weapon.update(dt)
            r = self.box(obj)
            origin = r.x+r.w/2,r.y+r.h/2
            destination = b.x+b.w/2,b.y+b.h/2
            dx,dy = destination[0]-origin[0],destination[1]-origin[1]
            visible = abs(dx) <= obj.get("range",420) and abs(dy) <= 12
            if visible and not any(segment_hits_box(origin,destination,c.box) for c in self.level.colliders if not c.one_way):
                if weapon.fire(self.projectiles,origin,(1 if dx >= 0 else -1,0),obj["id"],"enemy"):
                    self.audio.play("shoot")
        self.view.update(self.player.state,dt)

    def text(self,surface,text,x,y,color=(179,203,217),font=None):
        locale=getattr(self,'locale',None)
        if locale is not None:
            text=locale.literal(text)
        text = getattr(self,"format_controls",str)(text)
        if locale is not None:
            size=40 if font is self.large else 27 if font is self.title else 13
            image=locale.renderer.render(text,color,size,max(12,surface.get_width()-16))
        else:
            image=(font or self.small).render(text,True,color)
        x=round(x)
        if locale is not None: x=max(0,min(x,surface.get_width()-image.get_width()-4))
        surface.blit(image,(x,round(y)))

    def tr(self,key,default,**values):
        locale=getattr(self,'locale',None)
        return locale.t(key,**values) if locale is not None else default.format_map(values)

    def draw_world(self,surface,alpha,background=True):
        if background:
            surface.fill(self.palette[0])
            for x in range(0,self.level.width,48):
                pygame.draw.line(surface,self.palette[1],(x,96),(x,self.level.height))
            for y in range(96,self.level.height,48):
                pygame.draw.line(surface,self.palette[1],(0,y),(self.level.width,y))
        for c in self.level.colliders:
            r = c.box
            if c.slope:
                draw_ramp(surface,(r.x,r.y,r.w,r.h),c.slope)
            elif c.one_way:
                pygame.draw.rect(surface,(105,196,197),(r.x,r.y,r.w,5))
            else:
                pygame.draw.rect(surface,self.palette[2],(r.x,r.y,r.w,r.h))
                pygame.draw.rect(surface,self.palette[3],(r.x+2,r.y+4,r.w-4,r.h-6),border_radius=3)
        for obj in self.level.objects:
            r = self.box(obj)
            if obj["type"] == "coin":
                if obj["id"] not in self.collected_items and obj.get("style") != "key":
                    pygame.draw.polygon(surface,(255,218,116),[(r.x+r.w/2,r.y),(r.right,r.y+r.h/2),(r.x+r.w/2,r.bottom),(r.x,r.y+r.h/2)])
                    pygame.draw.circle(surface,(255,249,212),(round(r.x+r.w/2),round(r.y+r.h/2)),3)
            elif obj["type"] == "pickup":
                if obj["id"] in self.collected_items:
                    continue
                item = obj.get("item","medkit")
                color = {"power":(205,153,249),"rapid":(108,216,240),"medkit":(128,234,182)}[item]
                pygame.draw.rect(surface,(23,45,59),(r.x,r.y,r.w,r.h),border_radius=5)
                pygame.draw.rect(surface,color,(r.x,r.y,r.w,r.h),2,border_radius=5)
                self.text(surface,{"power":"D","rapid":"C","medkit":"+"}[item],r.x+7,r.y+6,color)
            elif obj["type"] in {"target","turret"}:
                if obj["id"] in self.destroyed:
                    pygame.draw.rect(surface,(58,70,78),(r.x,r.bottom-5,r.w,5))
                    continue
                color = (245,156,105) if obj["type"] == "turret" else (221,192,116)
                pygame.draw.rect(surface,(64,56,62),(r.x,r.y,r.w,r.h),border_radius=4)
                pygame.draw.rect(surface,color,(r.x,r.y,r.w,r.h),2,border_radius=4)
                center = round(r.x+r.w/2),round(r.y+r.h/2)
                if obj["type"] == "target":
                    pygame.draw.circle(surface,color,center,7,2)
                    pygame.draw.circle(surface,color,center,2)
                else:
                    facing = 1 if self.player.body.x > r.x else -1
                    pygame.draw.line(surface,color,center,(center[0]+facing*20,center[1]),5)
                    weapon = self.turrets[obj["id"]]
                    charge = 1-min(1,weapon.remaining/weapon.spec.cooldown)
                    pygame.draw.rect(surface,color,(r.x,r.bottom+4,r.w*charge,2))
                health = self.targets[obj["id"]]
                pygame.draw.rect(surface,(66,71,80),(r.x,r.y-8,r.w,3))
                pygame.draw.rect(surface,color,(r.x,r.y-8,r.w*health.remaining/health.maximum,3))
            elif obj["type"] == "checkpoint":
                color = (125,244,208) if obj["id"] == self.active_checkpoint else (100,156,171)
                pygame.draw.line(surface,color,(r.x+6,r.y),(r.x+6,r.bottom),2)
                pygame.draw.polygon(surface,color,[(r.x+6,r.y),(r.x+24,r.y+6),(r.x+6,r.y+13)])
            elif obj["type"] == "goal":
                color = (116,239,210) if self.objectives_ready else (113,100,143)
                pygame.draw.rect(surface,color,(r.x,r.y,r.w,r.h),3,border_radius=12)
                self.text(surface,"SAÍDA" if self.objectives_ready else "BLOQUEADA",r.x-25,r.y-23,color)
            elif obj["type"] == "hazard":
                if obj.get("style") not in {"bush","stalactite"}:
                    pygame.draw.rect(surface,(236,110,137),(r.x,r.y,r.w,r.h))
        self.draw_player(surface,alpha)
        for p in self.projectiles.items:
            x,y = p.interpolated(alpha)
            color = (119,244,221) if p.team == "player" else (255,139,103)
            pygame.draw.line(surface,(49,91,100) if p.team=="player" else (110,61,55),(x-p.vx/p.spec.speed*15,y),(x,y),3)
            pygame.draw.rect(surface,color,(x-p.spec.width/2,y-p.spec.height/2,p.spec.width,p.spec.height),border_radius=2)
        for point,life,team in self.sparks:
            pygame.draw.circle(surface,(249,220,155),tuple(round(v) for v in point),max(1,round(12*(1-life/.16))),1)

    def draw_player(self,surface,alpha):
        b = self.player.body
        px,py = b.interpolated(alpha)
        if not getattr(self,"hide_player",False) and (self.health.immune_left <= 0 or int(self.elapsed*16)%2 == 0):
            self.view.draw(surface,(px-4,py-10),self.player.controller.facing)
            facing = self.player.controller.facing
            gun = (px+b.w-2 if facing > 0 else px-11,py+12,13,5)
            if self.armed:
                pygame.draw.rect(surface,(113,234,215),gun,border_radius=2)

    def draw_hud(self,surface):
        pygame.draw.rect(surface,(9,17,29),(0,0,960,94))
        self.text(surface,self.tr('hud.lab','PLATFORM2D  /  LABORATÓRIO {number}',number='13' if self.pickups else '12'),24,15,(118,220,205))
        self.text(surface,self.level.name,24,36,(232,241,247),self.title)
        crystals = sum(o["id"] in self.collected_items for o in self.coins)
        status = self.tr('hud.targets_crystals','ALVOS {targets}/{target_total}  CRISTAIS {crystals}/{crystal_total}',targets=len(self.destroyed),target_total=len(self.objects),crystals=crystals,crystal_total=len(self.coins)) if self.coins else self.tr('hud.targets_shots','ALVOS {targets}/{target_total}   TIROS {shots}',targets=f'{len(self.destroyed):02}',target_total=f'{len(self.objects):02}',shots=f'{self.shots:03}')
        self.text(surface,status,637,23,(241,199,130))
        for i in range(self.health.maximum):
            pygame.draw.circle(surface,(115,229,197) if i < self.health.remaining else (44,62,75),(652+i*24,58),7)
        mission = "MISTA: destrói os alvos e recolhe todos os cristais." if self.objects and self.coins else "RECOLHA: apanha todos os cristais para abrir a saída." if self.coins else "COMBATE: destrói todos os alvos para abrir a saída." if self.objects else "TRAVESSIA: chega à saída em segurança."
        self.text(surface,mission,26,111)
        self.text(surface,"Explora as plataformas. Os cristais não ocupam espaço no inventário." if self.coins else "Usa as coberturas, controla os disparos e procura a saída.",26,132,(115,151,174))
        if self.pickups or self.inventory.snapshot():
            stats = self.tr('hud.inventory','INVENTÁRIO  Dano +{power}/3   Cadência {rapid}/2   Kits {kits}/3',power=self.inventory.count('power'),rapid=self.inventory.count('rapid'),kits=self.inventory.count('medkit'))
            self.text(surface,stats,26,166,(146,225,205))
            info = self.tr('hud.weapon','Arma: dano {damage} · intervalo {interval}s   [H] usar kit (+2 vida)',damage=self.weapon.spec.damage,interval=f'{self.weapon.spec.cooldown:.2f}') if self.armed else self.tr('hud.unarmed','Disparos desativados nesta sala   [H] usar kit (+2 vida)')
            self.text(surface,info,26,188)
        if self.inventory_notice_time:
            self.text(surface,self.inventory_notice,26,217,(248,209,132))
        self.text(surface,"F3: comandos  |  R: checkpoint  |  F2: recomeçar",25,555)
        if self.debug:
            draw_debug(surface,self.small,self.player.body,self.player.state,self.level.colliders,(0,0),self.level.tile_size)

    def draw_overlay(self,surface):
        if self.paused or self.won:
            shade = pygame.Surface(surface.get_size(),pygame.SRCALPHA)
            shade.fill((3,10,21,215))
            surface.blit(shade,(0,0))
            self.text(surface,"Setor seguro" if self.won else "Em pausa",320,222,(220,245,237),self.large)
            self.text(surface,self.tr('hud.win_stats','{shots} disparos · {deaths} mortes · F2 para recomeçar',shots=self.shots,deaths=self.deaths) if self.won else "P para continuar · N para avançar",300,284)

    def draw(self,surface,alpha):
        self.draw_world(surface,alpha)
        self.draw_hud(surface)
        self.draw_overlay(surface)
