"""Cumulative features make the responsibility of each lesson visible."""
import pygame
from platform2d.actors.character import Character
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider
from platform2d.gameplay.combat import Health


class LessonScene:
    def __init__(self,lesson=6):
        self.lesson=lesson; self.font=pygame.font.Font(None,28)
        self.reset()

    def reset(self):
        self.player=Character(Body(80,482)); self.health=Health(3,.8)
        self.floor=[Collider(Box(0,512,960,64))]
        if self.lesson>=3: self.floor.append(Collider(Box(300,448,128,16),True))
        self.enemy=Body(660,482); self.direction=1
        self.collected=self.won=self.paused=False; self.menu=self.lesson>=6

    def update(self,dt,actions):
        if 'restart' in actions.pressed: self.reset(); return
        if 'pause' in actions.pressed: self.paused=not self.paused
        if self.menu and 'continue' in actions.pressed: self.menu=False
        if self.lesson==1 or self.menu or self.paused or self.won:
            b=self.player.body; b.previous_x,b.previous_y=b.x,b.y
            return
        self.health.update(dt); self.player.update(dt,actions,self.floor)
        b=self.player.body; b.x=max(0,min(936,b.x))
        if self.lesson>=4 and b.box.overlaps(Box(344,410,24,32)): self.collected=True
        if self.lesson>=5:
            self.enemy.x+=self.direction*70*dt
            if self.enemy.x>=748: self.enemy.x=748; self.direction=-1
            elif self.enemy.x<=620: self.enemy.x=620; self.direction=1
            if b.box.overlaps(self.enemy.box) and self.health.hit():
                self.player.respawn((80,482))
                if self.health.dead: self.reset()
        if self.lesson>=4 and self.collected and b.box.overlaps(Box(880,452,40,60)): self.won=True

    def draw(self,surface,alpha):
        surface.fill((12,23,37))
        if self.lesson>=2:
            for c in self.floor: pygame.draw.rect(surface,(53,103,117),(c.box.x,c.box.y,c.box.w,c.box.h))
            x,y=self.player.body.interpolated(alpha); pygame.draw.rect(surface,(118,232,213),(x,y,24,30),border_radius=6)
        if self.lesson>=4:
            if not self.collected: pygame.draw.circle(surface,(249,206,116),(356,426),12)
            pygame.draw.rect(surface,(119,227,190) if self.collected else (110,110,130),(880,452,40,60),3)
        if self.lesson>=5: pygame.draw.rect(surface,(235,128,144),(self.enemy.x,self.enemy.y,24,30),border_radius=5)
        title=('Janela e desenho','Personagem e chão','Plataforma e salto','Recolha e saída','Adversário e vida','Pequeno jogo completo')[self.lesson-1]
        message='Enter: começar' if self.menu else 'Concluído! R: recomeçar' if self.won else 'Pausa · P: retomar' if self.paused else 'Setas: mover · Espaço: saltar · P: pausa · R: recomeçar'
        surface.blit(self.font.render(f'{self.lesson:02d} / {title}',True,(226,238,244)),(28,28))
        surface.blit(self.font.render(message,True,(226,238,244)),(28,65))
        if self.lesson>=5: surface.blit(self.font.render(f'Vida: {self.health.remaining}/3',True,(245,193,130)),(28,103))
