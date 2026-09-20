"""Flight, ledges and scrolling reuse the combat scene's ordinary world rules."""
import pygame
from examples.ranged.scene import RangedScene
from platform2d.actors.traversal import JetpackController,LedgeController
from platform2d.gameplay.rocket import RocketMission
from platform2d.rendering.animation import Clip
from platform2d.rendering.parallax import draw_parallax
from platform2d.rendering.rocket import component,vehicle,METAL,FUEL
from platform2d.rendering.action_pose import draw_actor
from platform2d.world.camera import Camera


class AdventureScene(RangedScene):
    FIXED_SIZE=False

    def __init__(self,level,settings):
        self.mode=level.properties.get('traversal','walk')
        self.scroll=level.properties.get('scroll','both')
        self.REQUIRES_GOAL=self.mode!='jetpack'
        super().__init__(level,settings)
        controller={'jetpack':JetpackController,'ledge':LedgeController}.get(self.mode)
        if controller: self.player.controller=controller(self.player.controller.config)
        self.player.controller.bounds=(level.width,level.height)
        self.view.clips.update(fly=Clip((6,7),10),hang=Clip((7,),1),climb=Clip((6,0),7))
        self.camera=Camera((960,480),(level.width,level.height))
        self.world_surface=pygame.Surface((level.width,level.height),pygame.SRCALPHA)
        self.viewport=pygame.Surface((960,480))
        self.update_camera(0,True)

    def reset(self):
        self.rocket=RocketMission(self.level.objects) if self.mode=='jetpack' else None
        self.launch_time=None
        self.hide_player=False
        super().reset()

    def respawn(self):
        super().respawn()
        if hasattr(self,'camera'): self.update_camera(0,True)

    def update_camera(self,dt,snap=False):
        self.camera.follow(self.player.body,dt,snap)
        if self.scroll=='horizontal': self.camera.y=self.camera.previous_y=max(0,self.level.height-480)
        if self.scroll=='vertical': self.camera.x=self.camera.previous_x=0

    def world_to_screen(self,point):
        if self.scroll=='none': return point
        return point[0]-self.camera.x,point[1]-self.camera.y+96

    def freeze(self):
        super().freeze()
        if hasattr(self,'camera'):
            self.camera.previous_x,self.camera.previous_y=self.camera.x,self.camera.y

    @property
    def objectives_ready(self):
        return False if self.rocket is not None else super().objectives_ready

    @property
    def mission_marker(self):
        return (len(self.rocket.delivered),len(self.rocket.fuelled)) if self.rocket else None

    def collect_items(self,actions):
        super().collect_items(actions)
        if self.rocket is None: return
        state=self.rocket
        for obj in self.level.objects:
            if obj['type'] in {'part','fuel'} and self.player.body.box.overlaps(self.box(obj)):
                if state.take(obj['id']):
                    self.audio.play('pickup')
                    self.inventory_notice='Carga recolhida. Leva-a ao foguetão e prime [E].'
                    self.inventory_notice_time=3
        rocket=next(o for o in self.level.objects if o['type']=='rocket')
        if self.player.body.box.overlaps(self.box(rocket)) and 'interact' in actions.pressed:
            if state.deliver():
                self.audio.play('checkpoint')
                self.inventory_notice='Peça instalada.' if not state.assembled else 'Montagem concluída. Recolhe o combustível.' if not state.fuelled else 'Combustível entregue.'
                self.inventory_notice_time=3
            elif state.ready and super().objectives_ready:
                self.launch_time=0
                self.hide_player=True
                self.projectiles.clear()
                self.audio.play('door')
            else:
                self.inventory_notice='Procura as peças.' if not state.assembled else 'Ainda falta combustível.' if not state.ready else 'Ainda faltam cristais ou alvos da missão.'
                self.inventory_notice_time=3

    def update(self,dt,actions):
        if self.launch_time is not None and not self.won and 'reset' not in actions.pressed:
            if 'pause' in actions.pressed: self.paused=not self.paused
            self.freeze()
            if self.paused and 'step' not in actions.pressed: return
            self.elapsed+=dt; self.launch_time+=dt
            if self.launch_time>=2.5:
                self.won=True; self.audio.play('victory')
            return
        super().update(dt,actions)
        if (self.paused and 'step' not in actions.pressed) or self.won: return
        if self.mode=='jetpack' and self.player.body.y<264:
            self.player.body.y=264; self.player.body.vy=max(0,self.player.body.vy)
        elif self.player.body.y<0:
            self.player.body.y=0; self.player.body.vy=max(0,self.player.body.vy)
        self.update_camera(dt)

    def draw_player(self,surface,alpha):
        if self.rocket and self.rocket.carrying:
            if not self.hide_player:
                draw_actor(surface,self.player.body.interpolated(alpha),self.player.controller.facing,
                           phase='carry',clock=self.elapsed,reduced=getattr(self,'reduced_effects',False))
        else: super().draw_player(surface,alpha)

    def rocket_draw(self,surface,alpha=1):
        state=self.rocket
        if state is None: return
        for obj in self.level.objects:
            if obj['type'] in {'part','fuel'} and obj['id'] not in state.delivered|state.fuelled and obj['id']!=state.carrying:
                r=pygame.Rect(obj['x'],obj['y'],obj.get('w',24),obj.get('h',24))
                if obj['type']=='part':
                    component(surface,r,state.part_name(obj['id']),METAL)
                    number=state.part_order.index(obj['id'])+1
                    self.text(surface,str(number),r.right+3,r.y,(132,229,214))
                    if obj['id']==state.next_part:
                        pygame.draw.rect(surface,(132,229,214),r.inflate(8,8),1,border_radius=4)
                else:
                    pygame.draw.rect(surface,FUEL,r,2,border_radius=4)
                    self.text(surface,'F',r.x+6,r.y+5,FUEL)
        obj=next(o for o in self.level.objects if o['type']=='rocket')
        x,y=obj['x'],obj['y']-(self.launch_time or 0)**2*110
        pygame.draw.rect(surface,(85,115,132),(x-12,obj['y']+86,72,5))
        vehicle(surface,(x,y,48,86),state)
        if self.launch_time is not None:
            pygame.draw.polygon(surface,(255,206,103),[(x+8,y+87),(x+24,y+135),(x+40,y+87)])
        self.text(surface,f'COMB. {len(state.fuelled)}/{len(state.fuel)}',x-17,obj['y']+95)
        b=self.player.body
        px,py=b.interpolated(alpha)
        if state.carrying:
            if state.carrying in state.parts:
                component(surface,(px,py-32,24,24),state.part_name(state.carrying),METAL)
            else:
                pygame.draw.rect(surface,FUEL,(px+2,py-28,20,20),border_radius=3)
        if self.player.controller.motion_state=='fly':
            pygame.draw.polygon(surface,(255,170,92),[(px+6,py+28),(px+12,py+43),(px+18,py+28)])

    def draw(self,surface,alpha):
        if self.scroll=='none':
            self.draw_world(surface,alpha)
            self.rocket_draw(surface,alpha)
            self.draw_hud(surface)
            pygame.draw.rect(surface,(12,23,37),(0,96,960,157))
            self.text(surface,'BASE ORBITAL · MONTA O FOGUETÃO, ABASTECE E PARTE',24,110,(132,229,214))
            self.text(surface,'Mantém SALTAR para voar. Transporta uma carga de cada vez. [E] entregar / partir.',24,137)
            self.text(surface,f'PEÇAS {len(self.rocket.delivered)}/{len(self.rocket.parts)}   COMBUSTÍVEL {len(self.rocket.fuelled)}/{len(self.rocket.fuel)}',24,167)
            self.text(surface,self.inventory_notice if self.inventory_notice_time else (f'Seguinte: {self.rocket.part_name(self.rocket.next_part)} · recolhe a peça assinalada.' if self.rocket.next_part else 'Recolhe combustível: a cor âmbar sobe no foguetão.'),24,199)
            if self.launch_time is not None:
                self.text(surface,'RUMO AO PLANETA AURORA…',290,238,(250,217,146),self.title)
        else:
            self.world_surface.fill((0,0,0,0))
            self.draw_world(self.world_surface,alpha,background=False)
            anchor=getattr(self.player.controller,'anchor',None)
            if anchor:
                b=self.player.body; edge,top,direction=anchor
                pygame.draw.line(self.world_surface,(178,241,219),(b.x+b.w/2,b.y+15),(edge,top+2),3)
                pygame.draw.circle(self.world_surface,(250,217,148),(round(edge),round(top+2)),3)
            x,y=self.camera.interpolated(alpha)
            draw_parallax(self.viewport,(0,0) if getattr(self,'reduced_effects',False) else (x,y),self.level.properties.get('theme','station'))
            self.viewport.blit(self.world_surface,(-round(x),-round(y)))
            surface.fill((9,17,29)); surface.blit(self.viewport,(0,96))
            self.text(surface,self.level.name,24,35,(232,241,247),self.title)
            got=sum(o['id'] in self.collected_items for o in self.coins)
            self.text(surface,f'CRISTAIS {got}/{len(self.coins)}   VIDA {self.health.remaining}/5',665,43)
            hint='Aproxima-te de uma borda no ar para agarrar. SALTAR / [E]: subir. BAIXO: largar.' if self.mode=='ledge' else 'Explora o vale e recolhe todos os cristais. A câmara acompanha-te.'
            self.text(surface,hint,24,77)
            self.text(surface,'F3: comandos · R: checkpoint · F2: recomeçar',24,555)
        pygame.draw.rect(surface,(9,17,29),(0,0,625,33))
        self.text(surface,'PLATFORM2D / AVENTURA',24,15,(118,220,205))
        self.draw_overlay(surface)
