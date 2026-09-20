"""Cumulative features make the responsibility of each lesson visible."""
import pygame
from pathlib import Path
from platform2d.i18n import Translator, TextRenderer
from platform2d.actors.character import Character
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider
from platform2d.gameplay.combat import Health


class LessonScene:
    LANGUAGES=('pt-PT','en','es','fr','de','zh-Hans','ar','ja')
    show_controls_hint=False

    def __init__(self,lesson=6,language='pt-PT',on_language_changed=None):
        self.lesson=lesson
        folder=Path(__file__).resolve().parent
        self.translator=Translator(folder/'locales',language)
        self.text_renderer=TextRenderer(self.translator,folder/'fonts')
        self.on_language_changed=on_language_changed
        self.language_warning=False
        self.reset()

    def handle_event(self,event):
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F3:
            # Introductory lessons use fixed bindings in their own instructions.
            return True
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F4:
            if not getattr(event,'repeat',False):
                index=self.LANGUAGES.index(self.translator.language)
                self.translator.select(self.LANGUAGES[(index+1)%len(self.LANGUAGES)])
                if hasattr(self,'set_host_language'): self.set_host_language(self.translator.language)
                pygame.display.set_caption(self.translator.text('window',lesson=self.lesson))
                self.language_warning=False
                if self.on_language_changed:
                    try: self.on_language_changed(self.translator.language)
                    except OSError: self.language_warning=True
            return True
        return False

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
        t=self.translator.text; draw=self.text_renderer.draw
        title=t('title',lesson=f'{self.lesson:02d}',title=t(f'lesson.{self.lesson}'))
        message=t('start' if self.menu else 'won' if self.won else 'paused' if self.paused else 'controls')
        draw(surface,title,18,size=25)
        draw(surface,message,59,size=22)
        if self.lesson>=5: draw(surface,t('health',current=self.health.remaining,maximum=3),100,(245,193,130),22)
        draw(surface,t('language',name=self.translator.metadata['name']),143,(128,231,199),20)
        if self.language_warning: draw(surface,t('language.unsaved'),182,(245,193,130),18)
        # Persistent localized hints also explain controls before the game starts.
        pygame.draw.rect(surface,(12,23,37),(0,516,surface.get_width(),60))
        draw(surface,t('controls'),517,size=17)
        if hasattr(self,'audio'):
            status=t('audio.unavailable') if not self.audio.available else t('audio.off') if self.audio.muted else t('audio.volume',volume=round(self.audio.volume*100))
            draw(surface,status+' · '+t('audio.keys'),546,(179,233,219),16)
