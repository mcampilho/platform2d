"""Sword encounter adapter: ordinary platform physics, explicit combat timing."""
import pygame
from .adventure import AdventureScene
from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController,Movement
from platform2d.actors.perception import segment_hits_box
from platform2d.core.input import Actions
from platform2d.gameplay.combat import AttackSpec,Health
from platform2d.gameplay.sword import Sword
from platform2d.physics.body import Body,Box
from platform2d.rendering.action_pose import draw_actor,draw_impact,sword_pose


class Guardian:
    def __init__(self,obj):
        self.id=obj['id']
        self.character=Character(Body(obj['x'],obj['y']),ArcadeController(Movement(speed=65)))
        self.character.controller.facing=-1
        self.health=Health(obj.get('hp',3),.25)
        self.sword=Sword(AttackSpec(.55,.14,.85,48,1))
        self.wait=0

    @property
    def body(self): return self.character.body

    def update(self,dt,player,colliders):
        self.health.update(dt)
        b=self.body; dx=player.x+player.w/2-b.x-b.w/2
        visible=abs(player.y-b.y)<48 and not any(segment_hits_box((b.x+12,b.y+15),(player.x+12,player.y+15),c.box) for c in colliders if not c.one_way)
        held=set(); strike=False; guard=False
        if not self.sword.attack.running and self.sword.stunned<=0:
            self.character.controller.facing=1 if dx>=0 else -1
            if visible and abs(dx)>62:
                direction=1 if dx>0 else -1
                # Stay on a supported ledge rather than blindly walking into a pit.
                foot=Box(b.x+12+direction*28,b.box.bottom,4,12)
                if any(foot.overlaps(c.box) for c in colliders): held.add('right' if dx>0 else 'left')
                self.wait=0
            elif visible:
                self.wait+=dt; guard=True
                if self.wait>=.85:
                    strike=True; guard=False; self.wait=0
        if not held: b.vx=0
        self.character.update(dt,Actions(held=frozenset(held)),colliders)
        self.sword.update(dt,b,self.character.controller.facing,guard,strike)


class DuelScene(AdventureScene):
    def respawn(self):
        super().respawn()
        self.sword=Sword()
        self.impact_fx=[]
        self.guardians=[Guardian(o) for o in self.level.objects if o['type']=='guardian' and o['id'] not in self.destroyed]

    @property
    def mission_marker(self): return tuple(sorted(self.destroyed))

    def freeze(self):
        super().freeze()
        for enemy in getattr(self,'guardians',[]):
            enemy.body.previous_x,enemy.body.previous_y=enemy.body.x,enemy.body.y

    def update(self,dt,actions):
        paused_after=self.paused ^ ('pause' in actions.pressed)
        if self.won or paused_after and 'step' not in actions.pressed:
            super().update(dt,actions)
            return
        if not self.sword.attack.running and self.sword.stunned<=0 and actions.axis():
            self.player.controller.facing=1 if actions.axis()>0 else -1
        if self.sword.attack.running or self.sword.stunned>0 or ('guard' in actions.held or 'attack' in actions.pressed) and self.player.body.on_ground:
            remove={'left','right','jump'}
            actions=Actions(actions.held-remove,actions.pressed-remove,actions.released)
            self.player.body.vx=0
        super().update(dt,actions)

    def announce(self,text,sound):
        self.inventory_notice=text; self.inventory_notice_time=1.4
        self.audio.play(sound)

    def update_encounters(self,dt,actions):
        self.impact_fx=[(p,t-dt,k) for p,t,k in self.impact_fx if t>dt]
        b=self.player.body
        was_attacking=self.sword.attack.running
        self.sword.update(dt,b,self.player.controller.facing,'guard' in actions.held,'attack' in actions.pressed and self.player.stun_left<=0)
        if self.sword.attack.running and not was_attacking: self.audio.play('attack')
        for enemy in self.guardians:
            if enemy.health.dead: continue
            enemy.update(dt,b,self.level.colliders)
            eb=enemy.body
            # Characters cannot walk through one another; jumping over is allowed.
            if b.box.overlaps(eb.box):
                left=b.previous_x+b.w/2<eb.previous_x+eb.w/2
                target=eb.x-b.w if left else eb.box.right
                candidate=Box(target,b.y,b.w,b.h)
                if 0<=target<=self.level.width-b.w and not any(candidate.overlaps(c.box) for c in self.level.colliders if not c.one_way):
                    b.x=target; b.vx=0
            if self.sword.attack.connects(enemy.id,b,eb.box,self.level.colliders):
                outcome=enemy.sword.defend(eb,enemy.character.controller.facing,b)
                if outcome not in {'hit','break'}: self.impact_fx.append(((eb.x+12,eb.y+12),.18,outcome))
                if outcome in {'hit','break'}:
                    if enemy.health.hit():
                        self.impact_fx.append(((eb.x+12,eb.y+12),.18,outcome))
                        enemy.sword.interrupt(.45); self.announce('Golpe certeiro!','hit')
                        if enemy.health.dead: self.destroyed.add(enemy.id)
                elif outcome=='parry':
                    self.sword.interrupt(.65); self.announce('O guardião desviou a tua espada.','blocked')
                else: self.announce('Defesa do guardião: espera pela recuperação.','blocked')
            if not enemy.health.dead and enemy.sword.attack.connects('player',eb,b.box,self.level.colliders):
                outcome=self.sword.defend(b,self.player.controller.facing,eb)
                if outcome not in {'hit','break'}: self.impact_fx.append(((b.x+12,b.y+12),.18,outcome))
                if outcome in {'hit','break'}:
                    if self.health.hit():
                        self.impact_fx.append(((b.x+12,b.y+12),.18,outcome))
                        self.sword.interrupt(.35)
                        self.announce('Defesa quebrada!' if outcome=='break' else 'Foste atingido.','hurt')
                elif outcome=='parry':
                    enemy.sword.interrupt(.9); self.announce('Desvio perfeito! Contra-ataca com [J].','checkpoint')
                else: self.announce('Golpe bloqueado. Gere a resistência.','blocked')

    def draw_player(self,surface,alpha):
        phase,progress=sword_pose(self.sword,self.health)
        if phase=='idle' and abs(self.player.body.vx)>8: phase='run'
        draw_actor(surface,self.player.body.interpolated(alpha),self.player.controller.facing,
                   phase,progress,self.elapsed,reach=self.sword.attack.spec.reach,reduced=getattr(self,'reduced_effects',False))

    def draw_world(self,surface,alpha,background=True):
        super().draw_world(surface,alpha,background)
        for enemy in self.guardians:
            if enemy.health.dead: continue
            px,py=enemy.body.interpolated(alpha)
            phase,progress=sword_pose(enemy.sword,enemy.health)
            if phase=='idle' and abs(enemy.body.vx)>8: phase='run'
            draw_actor(surface,(px,py),enemy.character.controller.facing,phase,progress,self.elapsed,
                       guardian=True,reach=enemy.sword.attack.spec.reach,reduced=getattr(self,'reduced_effects',False))
            pygame.draw.rect(surface,(51,29,47),(px-9,py-18,42,5))
            pygame.draw.rect(surface,(232,134,154),(px-9,py-18,42*enemy.health.remaining/enemy.health.maximum,5))
            label={'hurt':'ATINGIDO','stagger':'VULNERÁVEL','guard':'DEFESA','windup':'PREPARA','strike':'GOLPE','recover':'RECUPERA'}.get(phase,'GUARDIÃO')
            self.text(surface,label,px-25,py-37,(255,207,137))
        if not getattr(self,'reduced_effects',False):
            for position,life,kind in self.impact_fx[-32:]: draw_impact(surface,position,life,kind)

    def draw(self,surface,alpha):
        super().draw(surface,alpha)
        if self.won or self.paused: return
        pygame.draw.rect(surface,(9,17,29),(0,0,960,96))
        self.text(surface,'PÁTIO DO GUARDIÃO · ESPADA E DEFESA',24,10,(132,229,214))
        self.text(surface,'[J] golpe · manter [L] defesa frontal · bloquear no último instante permite contra-atacar.',24,35)
        count=sum(o['type']=='guardian' for o in self.level.objects)
        self.text(surface,self.tr('duel.status','GUARDIÕES {current}/{total}   VIDA {health}/5   RESISTÊNCIA',current=len(self.destroyed),total=count,health=self.health.remaining),24,62)
        pygame.draw.rect(surface,(43,54,71),(570,65,180,10))
        pygame.draw.rect(surface,(132,229,214),(570,65,round(self.sword.stamina*1.8),10))
        if self.inventory_notice_time:
            pygame.draw.rect(surface,(12,23,37),(170,514,660,30))
            self.text(surface,self.inventory_notice,186,521,(255,219,150))
