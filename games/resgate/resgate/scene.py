"""Game-specific rules. Imports only the standard library, Pygame and Platform2D."""
import json,os,tempfile
from pathlib import Path
import pygame
from platform2d.i18n import Translator, TextRenderer, FONT_FOLDER
from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController,Movement
from platform2d.actors.exploration import SwimController
from platform2d.audio import SilentAudio
from platform2d.gameplay.progress import fingerprint
from platform2d.physics.body import Body,Box
from platform2d.world.tilemap import TileMap
from platform2d.world.camera import Camera
from platform2d.rendering.parallax import draw_parallax

BINDINGS={'left':['left','a'],'right':['right','d'],'up':['up','w'],'down':['down','s'],
          'jump':['space','z'],'continue':['return'],'pause':['p'],'restart':['r'],
          'save_progress':['f6'],'load_progress':['f9']}
ASSETS=Path(__file__).parent/'assets'


class RescueGame:
    def __init__(self,data_dir,language='pt-PT'):
        self.translator=Translator(Path(__file__).parent/'locales',language)
        self.language=self.translator.language
        self.renderer=TextRenderer(self.translator,FONT_FOLDER)
        self.data_dir=Path(data_dir); self.save_path=self.data_dir/'progress.json'
        self.maps=[json.loads((ASSETS/name).read_text(encoding='utf-8')) for name in ('dock.json','reservoir.json','escape.json')]
        self.signature=fingerprint(dict(maps=self.maps,rules='rescue-1'))
        self.audio=SilentAudio(); self.menu='title'; self.selected=0; self.notice=''; self.notice_time=0
        self.font=20; self.small=15; self.title=40
        self.world=pygame.Surface((1920,960),pygame.SRCALPHA); self.viewport=pygame.Surface((960,480))
        self.new_game(); self.menu='title'

    def t(self,key,**values):
        return self.translator.text(key,**values)

    @property
    def paused(self): return self.menu is not None

    def new_game(self):
        self.index=0; self.deaths=0; self.elapsed=0; self.finished=False; self.stage_won=False
        self.start_stage(); self.menu='briefing'

    def start_stage(self):
        self.level=TileMap(self.maps[self.index],{'water','air'})
        self.collected=set(); self.checkpoint=None; self.stage_won=False
        self.camera=Camera((960,480),(self.level.width,self.level.height))
        self.respawn()

    @staticmethod
    def box(obj): return Box(obj['x'],obj['y'],obj.get('w',24),obj.get('h',30))

    def respawn(self):
        point=next(((o['x'],o['y']) for o in self.level.objects if o['id']==self.checkpoint),self.level.spawn)
        controller=SwimController if self.index==1 else ArcadeController
        self.player=Character(Body(*point),controller(Movement(speed=210)))
        self.oxygen=12.; self.chase=0.; self.frontier=max(0,point[0]-140)
        self.camera.follow(self.player.body,0,True)

    def say(self,message): self.notice=message; self.notice_time=4

    def snapshot(self):
        return dict(format='resgate.progress',version=1,signature=self.signature,index=self.index,
                    collected=sorted(self.collected),checkpoint=self.checkpoint,stage_won=self.stage_won,
                    finished=self.finished,deaths=self.deaths,elapsed=self.elapsed)

    def save(self):
        temporary=None
        try:
            self.data_dir.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.data_dir,delete=False,suffix='.tmp') as f:
                temporary=Path(f.name); json.dump(self.snapshot(),f,ensure_ascii=False,allow_nan=False); f.flush(); os.fsync(f.fileno())
            os.replace(temporary,self.save_path); self.say(self.t('saved'))
            return True
        except OSError as error: self.last_error=str(error); self.say(self.t('save_failed')); return False
        finally:
            if temporary and temporary.exists(): temporary.unlink()

    def load(self):
        import math
        try:
            if self.save_path.stat().st_size>65536: raise ValueError('ficheiro demasiado grande')
            d=json.loads(self.save_path.read_text(encoding='utf-8'))
            if not isinstance(d,dict) or set(d)!=set(self.snapshot()) or d['format']!='resgate.progress' or type(d['version']) is not int or d['version']!=1 or d['signature']!=self.signature: raise ValueError('gravação incompatível')
            if type(d['index']) is not int or not 0<=d['index']<3: raise ValueError('nível inválido')
            objects=self.maps[d['index']]['objects']; coins={o['id'] for o in objects if o['type']=='coin'}
            if not isinstance(d['collected'],list) or any(not isinstance(v,str) for v in d['collected']) or len(d['collected'])!=len(set(d['collected'])) or not set(d['collected'])<=coins: raise ValueError('recolhas inválidas')
            if d['checkpoint'] is not None and (not isinstance(d['checkpoint'],str) or d['checkpoint'] not in {o['id'] for o in objects if o['type']=='checkpoint'}): raise ValueError('checkpoint inválido')
            if type(d['deaths']) is not int or not 0<=d['deaths']<=10**9 or type(d['elapsed']) not in (float,int) or not math.isfinite(d['elapsed']) or not 0<=d['elapsed']<=10**9: raise ValueError('estatísticas inválidas')
            if type(d['stage_won']) is not bool or type(d['finished']) is not bool or d['stage_won'] and set(d['collected'])!=coins or d['finished']!=(d['index']==2 and d['stage_won']): raise ValueError('conclusão inválida')
            self.index=d['index']; self.start_stage(); self.checkpoint=d['checkpoint']; self.collected=set(d['collected'])
            self.deaths=d['deaths']; self.elapsed=d['elapsed']; self.stage_won=d['stage_won']; self.finished=d['finished']; self.respawn()
            self.menu='ending' if self.finished else 'stage' if self.stage_won else None
            self.say(self.t('resumed')); return True
        except (OSError,ValueError,TypeError,KeyError,OverflowError) as error:
            self.last_error=str(error); self.say(self.t('load_failed')); return False

    def freeze(self):
        b=self.player.body; b.previous_x,b.previous_y=b.x,b.y
        self.camera.previous_x,self.camera.previous_y=self.camera.x,self.camera.y

    def update(self,dt,actions):
        self.notice_time=max(0,self.notice_time-dt)
        if self.menu:
            self.freeze()
            if self.menu=='title':
                if 'up' in actions.pressed: self.selected=(self.selected-1)%4
                if 'down' in actions.pressed: self.selected=(self.selected+1)%4
                if 'continue' in actions.pressed:
                    if self.selected==0:
                        self.menu='confirm_new' if self.save_path.exists() else 'briefing'
                        if self.menu=='briefing': self.new_game()
                    elif self.selected==1: self.load()
                    elif self.selected==2: getattr(self,'open_controls',lambda:None)()
                    else: pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif self.menu=='confirm_new':
                if 'continue' in actions.pressed: self.new_game(); self.save()
                elif 'pause' in actions.pressed: self.menu='title'
            elif self.menu=='pause':
                if 'save_progress' in actions.pressed: self.save()
                if 'load_progress' in actions.pressed: self.menu='confirm_load'
                if 'pause' in actions.pressed or 'continue' in actions.pressed: self.menu=None
            elif self.menu=='confirm_load':
                if 'continue' in actions.pressed: self.load()
                elif 'pause' in actions.pressed: self.menu=None
            elif 'continue' in actions.pressed:
                if self.menu=='briefing': self.menu=None
                elif self.menu=='stage':
                    self.index+=1; self.start_stage(); self.menu='briefing'; self.save()
                elif self.menu=='ending': self.menu='title'
            return
        if 'pause' in actions.pressed: self.menu='pause'; self.freeze(); return
        if 'load_progress' in actions.pressed: self.menu='confirm_load'; self.freeze(); return
        if 'restart' in actions.pressed: self.respawn(); return
        if 'save_progress' in actions.pressed: self.save()
        self.elapsed+=dt; b=self.player.body
        if self.index==1:
            self.player.controller.submerged=any(o['type']=='water' and self.box(o).overlaps(Box(b.x+8,b.y+8,8,14)) for o in self.level.objects)
            self.player.controller.current=12
        self.player.update(dt,actions,self.level.colliders); b.x=max(0,min(b.x,self.level.width-b.w))
        for event in self.player.controller.motion_events: self.audio.play(event)
        dead=b.y>self.level.height+64 or any(o['type']=='hazard' and self.box(o).overlaps(b.box) for o in self.level.objects)
        if self.index==1:
            head=Box(b.x+7,b.y,10,10)
            wet=any(o['type']=='water' and self.box(o).overlaps(head) for o in self.level.objects)
            air=any(o['type']=='air' and self.box(o).overlaps(head) for o in self.level.objects)
            self.oxygen=max(0,self.oxygen-dt) if wet and not air else min(12,self.oxygen+6*dt)
            dead|=self.oxygen==0
        if self.index==2:
            self.chase+=dt; dead|=b.box.right<self.frontier+self.chase*65
        if dead:
            self.deaths+=1; self.audio.play('hurt'); self.respawn(); return
        for o in self.level.objects:
            if not self.box(o).overlaps(b.box): continue
            if o['type']=='coin' and o['id'] not in self.collected:
                self.collected.add(o['id']); self.audio.play('pickup'); self.say(self.t('equipment') if self.index==0 else self.t('valve'))
            if o['type']=='checkpoint' and o['id']!=self.checkpoint:
                self.checkpoint=o['id']; self.audio.play('checkpoint'); self.save()
            if o['type']=='goal' and all(c['id'] in self.collected for c in self.level.objects if c['type']=='coin'):
                self.stage_won=True; self.finished=self.index==2; self.menu='ending' if self.finished else 'stage'; self.audio.play('victory'); self.save(); break
        self.camera.follow(b,dt)
        if self.index==2: self.camera.x=min(self.level.width-960,max(self.camera.x,self.frontier+self.chase*65))

    def key(self,action):
        return getattr(self,'control_label',lambda action:BINDINGS[action][0].upper())(action)

    def text(self,surface,text,x,y,color=(216,233,240),font=None,width=None):
        width=width or max(80,surface.get_width()-int(x)-28)
        image=self.renderer.render(text,color,font or self.font,width)
        if surface is not self.world and self.translator.metadata['direction']=='rtl':
            x=surface.get_width()-x-image.get_width()
        surface.blit(image,(x,y))

    def draw(self,surface,alpha):
        x,y=self.camera.interpolated(alpha); self.world.fill((0,0,0,0))
        theme=('station','ice','reactor')[self.index]; draw_parallax(self.viewport,(x,y),theme)
        for c in self.level.colliders:
            r=c.box; pygame.draw.rect(self.world,(57,94,111),(r.x,r.y,r.w,r.h))
            pygame.draw.line(self.world,(105,171,176),(r.x,r.y),(r.right,r.y),3)
        for o in self.level.objects:
            r=self.box(o); rect=pygame.Rect(r.x,r.y,r.w,r.h)
            if o['type']=='water':
                tint=pygame.Surface(rect.size,pygame.SRCALPHA); tint.fill((37,137,194,80)); self.world.blit(tint,rect)
            elif o['type']=='air': pygame.draw.ellipse(self.world,(169,236,244),rect,2); self.text(self.world,self.t('air'),r.x+8,r.y+8,font=self.small)
            elif o['type']=='coin' and o['id'] not in self.collected:
                pygame.draw.rect(self.world,(255,193,95),rect,3,border_radius=4); self.text(self.world,'+',r.x+5,r.y,font=self.font)
            elif o['type']=='goal':
                pygame.draw.rect(self.world,(125,231,195),rect,3,border_radius=8); self.text(self.world,self.t('exit'),r.x-5,r.y-24,font=self.small)
            elif o['type']=='checkpoint':
                pygame.draw.line(self.world,(159,231,236),rect.bottomleft,rect.topleft,3); pygame.draw.polygon(self.world,(159,231,236),[rect.topleft,(r.x+24,r.y+7),(r.x,r.y+14)])
        px,py=self.player.body.interpolated(alpha)
        pygame.draw.rect(self.world,(240,170,90),(px+3,py+10,18,18),border_radius=4)
        pygame.draw.rect(self.world,(217,241,238),(px,py-3,24,19),border_radius=7)
        pygame.draw.rect(self.world,(36,86,106),(px+4,py+3,18,7),border_radius=3)
        pygame.draw.line(self.world,(230,241,235),(px+5,py+26),(px+3,py+30),4)
        pygame.draw.line(self.world,(230,241,235),(px+19,py+26),(px+21,py+30),4)
        self.viewport.blit(self.world,(-round(x),-round(y)))
        surface.fill((9,18,29)); surface.blit(self.viewport,(0,96))
        self.text(surface,f'{self.t("game_title")} / {self.index+1:02d}',26,12,(147,231,211),self.font,width=650)
        hint=self.t('hint'+str(self.index),jump=self.key('jump'),up=self.key('up'),down=self.key('down'))
        self.text(surface,hint,26,45,font=self.small)
        status=self.t('oxygen',value=f'{self.oxygen:04.1f}') if self.index==1 else self.t('threat',distance=max(0,int(self.player.body.x-self.frontier-self.chase*65))) if self.index==2 else self.t('equipment_status',count=len(self.collected))
        self.text(surface,status,710,15,(255,206,139),self.small)
        self.text(surface,self.t('shortcuts',pause=self.key('pause'),save=self.key('save_progress'),load=self.key('load_progress'),restart=self.key('restart')),26,73,font=self.small)
        if self.index==2:
            edge=round(self.frontier+self.chase*65-x)
            if 0<=edge<960: pygame.draw.rect(surface,(235,113,124),(edge,96,8,480))
        if self.menu:
            shade=pygame.Surface((960,576),pygame.SRCALPHA); shade.fill((3,12,23,225)); surface.blit(shade,(0,0))
            if self.menu=='title':
                self.text(surface,self.t('game_title'),80,90,(236,243,235),self.title)
                self.text(surface,self.t('tagline'),82,155)
                for i,label in enumerate((self.t('new_game'),self.t('continue'),self.t('controls'),self.t('quit'))):
                    pygame.draw.rect(surface,(30,87,88) if i==self.selected else (20,35,50),(360 if self.translator.metadata['direction']=='rtl' else 80,224+i*52,520,43),border_radius=8)
                    self.text(surface,label,100,231+i*52,width=480)
                footer=self.t('footer',confirm=self.key('continue'))
                self.text(surface,footer,82,464,font=self.small)
            else:
                titles={'briefing':self.t('level'+str(self.index)),'stage':self.t('sector'),'ending':self.t('ending'),'pause':self.t('pause'),'confirm_new':self.t('new'),'confirm_load':self.t('load')}
                self.text(surface,titles[self.menu],64,160,(236,243,235),self.title)
                briefing=self.t('briefing'+str(self.index))
                message=briefing if self.menu=='briefing' else self.t('summary',time=f'{self.elapsed:.1f}',deaths=self.deaths) if self.menu=='ending' else self.t('next_sector') if self.menu=='stage' else self.t('pause_help',save=self.key('save_progress'),load=self.key('load_progress'),pause=self.key('pause'),confirm=self.key('continue')) if self.menu=='pause' else self.t('confirm_help',confirm=self.key('continue'),pause=self.key('pause'))
                self.text(surface,message,64,250)
                self.text(surface,self.t('continue_help',confirm=self.key('continue')),64,328,(148,230,210))
                if self.menu=='ending': self.text(surface,self.t('credits'),64,405,font=self.small)
        if self.notice_time:
            pygame.draw.rect(surface,(17,37,50),(16,526,928,34),border_radius=5)
            self.text(surface,self.notice,28,533,(255,212,143),self.small)
