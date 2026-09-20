"""Four small adventures composed from cargo and exploration capabilities."""
import pygame
from .adventure import AdventureScene
from platform2d.actors.exploration import SwimController,ExploreController
from platform2d.gameplay.cargo import Cargo
from platform2d.physics.body import Box
from platform2d.physics.collision import Collider

MODES={'cargo','swim','escape','explore'}


class ExpansionScene(AdventureScene):
    def __init__(self,level,settings):
        super().__init__(level,settings)
        controller={'swim':SwimController,'explore':ExploreController}.get(self.mode)
        if controller: self.player.controller=controller(self.player.controller.config)
        self.static_colliders=list(level.colliders)

    def respawn(self):
        self.cargo=Cargo(self.level.objects)
        self.open_gates=set(); self.oxygen=12.0; self.escape_time=0
        self.escape_origin=max(0,self.respawn_point[0]-120)
        super().respawn()

    def freeze(self):
        super().freeze()
        self.cargo.freeze()

    @property
    def ability(self):
        return any(o['type']=='ability' and o['id'] in self.collected_items for o in self.level.objects)

    @property
    def objectives_ready(self):
        if self.mode=='cargo' and len(self.cargo.active())!=len(self.cargo.plates): return False
        if self.mode=='explore' and not self.ability: return False
        return super().objectives_ready

    def gate_open(self,obj):
        return self.ability if self.mode=='explore' else bool(self.cargo.plates) and len(self.cargo.active(self.player.body))==len(self.cargo.plates)

    def prepare_world(self,dt,actions):
        gates=[o for o in self.level.objects if o['type']=='gate']
        solids=list(self.static_colliders)
        self.open_gates=set()
        for gate in gates:
            r=self.box(gate)
            # An obstructed closing gate waits; never inserts solid geometry
            # through the player or a crate. Objective checks remain separate.
            obstructed=any(r.overlaps(b.box) for b in [self.player.body,*self.cargo.crates.values()])
            if self.gate_open(gate) or obstructed: self.open_gates.add(gate['id'])
            else: solids.append(Collider(r))
        self.cargo.update(dt,self.player.body,actions.axis(),solids,self.level.width)
        if any(b.box.bottom>self.level.height for b in self.cargo.crates.values()):
            self.respawn()
            self.inventory_notice='Caixa perdida: puzzle reposto. Os cristais recolhidos foram conservados.'
            self.inventory_notice_time=4
        self.level.colliders=solids+self.cargo.colliders()
        c=self.player.controller; b=self.player.body
        if self.mode=='swim':
            water=next((o for o in self.level.objects if o['type']=='water' and self.box(o).overlaps(Box(b.x+8,b.y+8,8,14))),None)
            c.submerged=water is not None; c.current=water.get('current',0) if water else 0
        if self.mode=='explore': c.enabled=self.ability
        if self.mode=='escape': self.escape_time+=dt

    def update(self,dt,actions):
        try: super().update(dt,actions)
        finally:
            if hasattr(self,'static_colliders'): self.level.colliders=self.static_colliders

    def update_camera(self,dt,snap=False):
        super().update_camera(dt,snap)
        if self.mode=='escape':
            previous=self.camera.x if snap else self.camera.previous_x
            self.camera.x=max(0,min(self.level.width-960,max(self.escape_origin+self.escape_time*65,self.player.body.x-650)))
            self.camera.previous_x=self.camera.x if snap else previous

    def update_encounters(self,dt,actions):
        b=self.player.body
        if self.mode=='swim':
            head=Box(b.x+7,b.y,10,10)
            wet=any(o['type']=='water' and head.overlaps(self.box(o)) for o in self.level.objects)
            air=any(o['type']=='air' and head.overlaps(self.box(o)) for o in self.level.objects)
            self.oxygen=max(0,self.oxygen-dt) if wet and not air else min(12,self.oxygen+dt*6)
            if self.oxygen==0: self.health.remaining=0
        if self.mode=='escape':
            frontier=min(self.level.width,self.escape_origin+self.escape_time*65)
            if b.box.right<frontier: self.health.remaining=0

    def collect_items(self,actions):
        super().collect_items(actions)
        for obj in self.level.objects:
            if obj['type']=='ability' and obj['id'] not in self.collected_items and self.player.body.box.overlaps(self.box(obj)):
                self.collected_items.add(obj['id']); self.audio.play('checkpoint')
                self.inventory_notice='SALTO DUPLO adquirido! Solta e volta a premir SALTAR no ar. Regressa ao átrio.'
                self.inventory_notice_time=6

    @property
    def mission_marker(self): return (self.ability,) if self.mode=='explore' else None

    def draw_world(self,surface,alpha,background=True):
        super().draw_world(surface,alpha,background)
        for obj in self.level.objects:
            r=self.box(obj); rect=pygame.Rect(r.x,r.y,r.w,r.h); kind=obj['type']
            if kind=='water':
                tint=pygame.Surface(rect.size,pygame.SRCALPHA); tint.fill((35,137,207,65)); surface.blit(tint,rect)
                pygame.draw.line(surface,(105,222,239),rect.topleft,rect.topright,3)
                for x in range(rect.x+30,rect.right,96):
                    pygame.draw.line(surface,(64,132,166),(x,rect.y+40),(x+22,rect.y+40),2)
            elif kind=='air':
                pygame.draw.ellipse(surface,(177,237,237),rect,2)
                self.text(surface,'AR',r.x+8,r.y+8)
            elif kind=='plate':
                active=obj['id'] in self.cargo.active(self.player.body)
                pygame.draw.rect(surface,(119,239,192) if active else (245,192,101),rect)
                self.text(surface,str(obj.get('weight',2))+' t · '+('ATIVA' if active else 'LIVRE'),r.x-8,r.y-65,(119,239,192) if active else (245,192,101))
            elif kind=='gate':
                opened=self.gate_open(obj) or obj['id'] in self.open_gates
                pygame.draw.rect(surface,(120,225,202) if opened else (230,131,114),rect,2 if opened else 0)
                self.text(surface,'ABERTA' if opened else 'SELADA',r.x-10,r.y-20)
            elif kind=='ability' and obj['id'] not in self.collected_items:
                pygame.draw.rect(surface,(194,147,244),rect,3,border_radius=8)
                self.text(surface,'2x',r.x+3,r.y+6)
        for b in self.cargo.crates.values():
            x,y=b.interpolated(alpha); rect=pygame.Rect(x,y,b.w,b.h)
            pygame.draw.rect(surface,(144,96,58),rect)
            pygame.draw.rect(surface,(241,194,120),rect,3)
            pygame.draw.line(surface,(241,194,120),rect.topleft,rect.bottomright,3)
            pygame.draw.line(surface,(241,194,120),rect.topright,rect.bottomleft,3)

    def draw(self,surface,alpha):
        super().draw(surface,alpha)
        if self.won or self.paused: return
        labels={
            'cargo':f'CAIXAS · empurra e usa como degraus · placas {len(self.cargo.active())}/{len(self.cargo.plates)} · R: repor caixas',
            'swim':f'OXIGÉNIO {self.oxygen:04.1f}s · SALTAR / cima: subir · baixo: mergulhar · procura bolsas de AR',
            'escape':'FUGA · mantém-te à frente da faixa vermelha · checkpoints permitem retomar o percurso',
            'explore':'SALTO DUPLO · salta, solta e prime SALTAR no ar · regressa à esquerda' if self.ability else 'EXPLORAÇÃO · encontra a capacidade no laboratório e regressa ao átrio'}
        pygame.draw.rect(surface,(9,17,29),(0,34,960,62))
        self.text(surface,self.level.name,24,38,(137,233,213))
        self.text(surface,labels[self.mode],24,65)
        if self.mode!='escape':
            got=sum(o['id'] in self.collected_items for o in self.coins)
            self.text(surface,f'CRISTAIS {got}/{len(self.coins)} · VIDA {self.health.remaining}/5',680,38)
        if self.inventory_notice_time:
            pygame.draw.rect(surface,(12,23,37),(12,520,936,28),border_radius=5)
            self.text(surface,self.inventory_notice,24,527,(249,215,145))
        if self.mode=='escape':
            frontier=min(self.level.width,self.escape_origin+self.escape_time*65)
            edge=round(frontier-self.camera.x)
            if edge>=0: pygame.draw.rect(surface,(224,100,114),(edge,96,12,480))
            self.text(surface,f'AMEAÇA A {max(0,round(self.player.body.x-frontier))} m',740,38,(255,180,149))
