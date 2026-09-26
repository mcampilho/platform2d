"""Presentation and menus around the campaign, without duplicating combat rules."""
import math
import pygame
from platform2d.audio import SilentAudio
from platform2d.gameplay.json_slot import JsonSlot
from platform2d.rendering.feedback import Feedback
from platform2d.rendering.transition import MomentTransitions
from .progress import accepted_identities,capture,identity,validate,restore
from .locale import CampaignLocale


class CampaignApp:
    def __init__(self,campaign,save_path=None,language='pt-PT'):
        self.campaign=campaign
        # Campaign documents are immutable while playing. Preparing their
        # signatures here keeps checkpoint autosaves out of the frame budget.
        self.save_identity=identity(campaign)
        self.save_identities=accepted_identities(campaign,self.save_identity)
        self.locale=campaign.locale=CampaignLocale(language)
        campaign.active.locale=self.locale
        self.slot=JsonSlot(save_path)
        self.audio=SilentAudio()
        self.format_controls=str
        self.open_controls=lambda:None
        self.mode='title'
        self.return_mode='title'
        self.selected=0
        self.started=False
        self.quit_requested=False
        self.notice=''
        self.notice_time=0
        self.feedback=Feedback()
        self.transitions=MomentTransitions()
        self.buttons=[]
        self.pending=lambda:None
        self.confirm_text=''
        self.save_label=''
        self.refresh_save()

    def validate_save(self,data):
        return validate(data,self.campaign,self.save_identities)

    @property
    def paused(self):
        return self.mode is not None or self.campaign.paused

    @property
    def show_controls_hint(self):
        return self.mode is None

    def refresh_save(self):
        try:
            data=self.slot.read(self.validate_save)
            self.save_label=self.locale.t('save.present',current=data['index']+1,total=len(self.campaign.documents))
        except (ValueError,OSError):
            self.save_label=self.locale.t('save.invalid' if self.slot.exists else 'save.missing')

    def message(self,text):
        self.notice=text
        self.notice_time=5

    def menu(self,mode):
        self.mode=mode; self.selected=0; self.buttons=[]
        self.audio.stop()

    def confirm(self,text,callback):
        self.return_mode=self.mode
        self.confirm_text=text; self.pending=callback
        self.menu('confirm')

    def request_new(self):
        if self.started or self.slot.exists:
            self.confirm(self.locale.t('confirm.new'),self.new_game)
        else:
            self.new_game()

    def new_game(self):
        self.campaign.reset(); self.started=True
        self.menu(None); self.feedback.clear(); self.feedback.fade=.35
        self.transitions.enter()
        self.save()

    def save(self):
        if not self.started: return False
        try:
            self.slot.write(capture(self.campaign,self.save_identity),self.validate_save)
            self.message(self.locale.t('save.done'))
            self.refresh_save()
            return True
        except (ValueError,OSError):
            self.message(self.locale.t('save.failed'))
            return False

    def load(self):
        try:
            data=self.slot.read(self.validate_save)
            restore(data,self.campaign)
        except (ValueError,OSError):
            self.message(self.locale.t('load.failed'))
            return False
        self.started=True; self.menu(None)
        self.feedback.clear(); self.feedback.fade=.35
        self.transitions.enter()
        self.message(self.locale.t('load.done'))
        return True

    def request_load(self):
        if self.started:
            self.confirm(self.locale.t('confirm.load'),self.load)
        else: self.load()

    def options(self):
        self.return_mode=self.mode
        self.menu('options')

    def volume(self,delta):
        setter=getattr(self.audio,'set_volume',None)
        if setter: setter(round(self.audio.volume+delta,2))

    def mute(self):
        toggle=getattr(self.audio,'toggle_mute',None)
        if toggle: toggle()

    def effects(self):
        self.feedback.enabled=not self.feedback.enabled
        self.transitions.enabled=self.feedback.enabled
        self.feedback.clear()
        self.transitions.clear()

    def save_quit(self):
        if self.save(): self.quit_requested=True

    def quit(self):
        if self.started:
            self.menu('quit')
        else: self.quit_requested=True

    def choices(self):
        t=self.locale.t
        if self.mode=='title':
            return [(t('menu.new'),self.request_new),(t('menu.continue'),self.request_load),
                    (t('menu.options'),self.options),(t('menu.leave'),self.quit)]
        if self.mode=='pause':
            return [(t('menu.resume'),lambda:self.menu(None)),(t('menu.save'),self.save),
                    (t('menu.load'),self.request_load),(t('menu.new'),self.request_new),
                    (t('menu.options'),self.options),(t('menu.leave'),self.quit)]
        if self.mode=='options':
            return [(t('menu.volume_down',value=f'{self.audio.volume:.0%}'),lambda:self.volume(-.1)),
                    (t('menu.volume_up'),lambda:self.volume(.1)),
                    (t('menu.sound',value=t('menu.sound_off' if self.audio.muted else 'menu.sound_on')),self.mute),
                    (t('menu.effects',value=t('menu.effects_on' if self.feedback.enabled else 'menu.effects_low')),self.effects),
                    (t('menu.controls'),self.open_controls),(t('menu.back'),lambda:self.menu(self.return_mode))]
        if self.mode=='confirm':
            return [(t('menu.confirm'),self.pending),(t('menu.cancel'),lambda:self.menu(self.return_mode))]
        if self.mode=='quit':
            return [(t('menu.save_quit'),self.save_quit),(t('menu.quit_unsaved'),lambda:setattr(self,'quit_requested',True)),
                    (t('menu.cancel'),lambda:self.menu('pause'))]
        return []

    def handle_event(self,event):
        if event.type==pygame.WINDOWFOCUSLOST and self.started and self.mode is None:
            self.menu('pause')
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            if getattr(event,'repeat',False): return True
            if self.mode is None: self.menu('pause')
            elif self.mode=='pause': self.menu(None)
            elif self.mode in {'options','confirm'}: self.menu(self.return_mode)
            elif self.mode=='quit': self.menu('pause')
            else: self.quit()
            return True
        if self.mode is None: return False
        choices=self.choices()
        if event.type==pygame.KEYDOWN and event.key in (pygame.K_UP,pygame.K_DOWN,pygame.K_RETURN,pygame.K_SPACE):
            if getattr(event,'repeat',False): return True
            if event.key in (pygame.K_UP,pygame.K_DOWN):
                self.selected=(self.selected+(-1 if event.key==pygame.K_UP else 1))%len(choices)
            else: choices[self.selected][1]()
            return True
        if event.type==pygame.MOUSEMOTION:
            for index,rect in enumerate(self.buttons):
                if rect.collidepoint(event.pos): self.selected=index
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for index,rect in enumerate(self.buttons):
                if rect.collidepoint(event.pos):
                    choices[index][1](); break
            return True
        return False

    def update(self,dt,actions):
        self.campaign.audio=self.audio
        self.campaign.format_controls=self.format_controls
        self.notice_time=max(0,self.notice_time-dt)
        if self.started and self.mode in (None,'pause'):
            if 'load_progress' in actions.pressed:
                self.request_load(); return
            if 'save_progress' in actions.pressed:
                self.save()
            if 'pause' in actions.pressed:
                self.menu('pause' if self.mode is None else None); return
        if self.mode is not None and not (self.mode=='pause' and 'step' in actions.pressed):
            # Cosmetic title motion does not advance game time or projectiles.
            self.feedback.age+=dt
            return
        if 'reset' in actions.pressed:
            self.request_new(); return
        old=self.campaign.active
        marker=getattr(old,"mission_marker",None)
        checkpoint=old.active_checkpoint; won=old.won
        collected=set(old.collected_items); destroyed=set(old.destroyed)
        health=old.health.remaining; deaths=old.deaths
        self.campaign.update(dt,actions)
        current=self.campaign.active
        screen_point=getattr(current,"world_to_screen",lambda point:point)
        self.feedback.update(dt)
        self.transitions.update(dt)
        if current is not old:
            self.feedback.clear(); self.feedback.fade=.35
            self.transitions.enter()
        else:
            for obj in current.level.objects:
                if obj['id'] in current.collected_items-collected:
                    self.feedback.burst(screen_point((obj['x']+12,obj['y']+15)),(118,240,200))
                if obj['id'] in current.destroyed-destroyed:
                    self.feedback.burst(screen_point((obj['x']+12,obj['y']+15)),(255,194,108))
            if current.health.remaining<health or current.deaths>deaths:
                self.feedback.flash=.2
            if current.deaths>deaths:
                self.feedback.clear(); self.feedback.fade=.35
                self.transitions.enter()
            if current.active_checkpoint!=checkpoint:
                point=screen_point((current.player.body.x+12,current.player.body.y))
                self.feedback.burst(point,(125,224,255))
                self.transitions.checkpoint(point)
            if current.won and not won:
                self.feedback.burst((480,215),(125,242,200))
                self.transitions.complete()
        if current is not old or current.active_checkpoint!=checkpoint or (current.won and not won) or getattr(current,"mission_marker",None)!=marker:
            self.save()

    def draw(self,surface,alpha):
        self.campaign.format_controls=self.format_controls
        self.campaign.active.reduced_effects=not self.feedback.enabled
        self.campaign.draw(surface,alpha)
        if self.mode is None:
            self.feedback.draw(surface)
            self.transitions.draw(surface)
        else:
            shade=pygame.Surface(surface.get_size(),pygame.SRCALPHA); shade.fill((5,13,25,235)); surface.blit(shade,(0,0))
            if self.feedback.enabled:
                for i in range(24):
                    x=(i*173+math.sin(self.feedback.age*.3+i)*12)%960
                    y=(i*91+self.feedback.age*5)%576
                    pygame.draw.circle(surface,(39,88,107),(round(x),round(y)),2)
            t=self.locale.t
            title=self.locale.literal(self.campaign.name) if self.mode=='title' else t('menu.'+self.mode)
            self.locale.draw(surface,title,(50,45,860,55),40,(219,244,238),'center')
            subtitle=self.confirm_text if self.mode=='confirm' else self.save_label if self.mode=='title' else t('menu.suspended')
            self.locale.draw(surface,subtitle,(120,114,720,33),18,(150,188,201),'center')
            self.buttons=[]
            for i,(label,callback) in enumerate(self.choices()):
                rect=pygame.Rect(240,157+i*46,480,39); self.buttons.append(rect)
                pygame.draw.rect(surface,(34,85,85) if i==self.selected else (20,38,54),rect,border_radius=7)
                pygame.draw.rect(surface,(116,226,200) if i==self.selected else (42,67,82),rect,1,border_radius=7)
                self.locale.draw(surface,label,rect.inflate(-44,0).move(0,10),20)
            self.locale.draw(surface,t('menu.help'),(120,476,720,31),16,align='center')
            if self.mode=='options': self.locale.draw(surface,t('menu.options_help'),(120,449,720,26),16,(139,170,188),'center')
        if self.notice_time:
            active=self.campaign.active
            if self.mode is not None or active.won or getattr(active,'launch_time',None) is not None:
                y=507
            elif getattr(active,'scroll','none')!='none':
                y=98
            else:
                y=218 if getattr(active,'mode',None)=='jetpack' else 244
            pygame.draw.rect(surface,(12,32,43),(16,y,928,39),border_radius=6)
            self.locale.draw(surface,self.notice,(28,y+6,904,30),18,(242,209,143))
