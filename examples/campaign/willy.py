"""A compact 32×16 key hunt with conveyors and fragile floors."""
from dataclasses import replace
from pathlib import Path

import pygame

from platform2d.physics.body import Box
from platform2d.physics.collision import Collider
from platform2d.rendering.sprite_animation import SpriteAtlas
from platform2d.rendering.theme import load_theme
from .adventure import AdventureScene
from .willy_art import (conveyor_tile,crumble_tile,draw_bush,
                        draw_exit,draw_key,draw_patrol,draw_stalactite,
                        stone_tile)


class WillyScene(AdventureScene):
    def __init__(self,level,settings):
        super().__init__(level,settings)
        config=self.player.controller.config
        self.player.controller.config=replace(config,speed=305,acceleration=2600,friction=2800,
                                              air_control=.45,jump_speed=410,jump_cut=410)
        self.base_colliders=list(level.colliders)
        self.dynamic_objects=[o for o in level.objects if o['type'] in {'crumble','conveyor'}]
        assets=Path(__file__).parent/'assets'
        manifest=assets/level.properties.get('visual_theme','willy-mine.theme.json')
        self.visual_theme=load_theme(manifest,assets)
        background=pygame.image.load(str(self.visual_theme.assets['background']))
        self.mine_background=pygame.transform.smoothscale(background,(1120,560))
        size=self.level.tile_size
        self.mine_walls=[stone_tile(size,index) for index in range(4)]
        self.mine_platforms=[stone_tile(size,index,True) for index in range(4)]
        self.mine_crumbles=[crumble_tile(size,index) for index in range(4)]
        self.mine_conveyor=conveyor_tile(size)
        self.mine_key=SpriteAtlas.from_spec(self.visual_theme.sprites['key'])
        self.mine_bush=SpriteAtlas.from_spec(self.visual_theme.sprites['bush'])
        self.mine_guardian=SpriteAtlas.from_spec(self.visual_theme.sprites['guardian'])
        self.respawn()

    def draw_scrolling_background(self,surface,camera):
        x,y=camera
        # The painted layer moves more slowly than the level, leaving enough
        # overscan for both axes of this compact scrolling map.
        bx=-80-round(x*.34)
        by=-38-round(y*.28)
        surface.blit(self.mine_background,(bx,by))
        veil=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        veil.fill((11,8,25,42))
        pygame.draw.polygon(veil,(109,188,216,18),[(515,0),(700,0),(610,480),(430,480)])
        surface.blit(veil,(0,0))
        reduced=getattr(self,'reduced_effects',False)
        clock=0 if reduced else self.elapsed
        for index in range(18):
            px=round((index*157-x*.12)%1000-20)
            py=round((index*83+clock*(5+index%4)-y*.09)%510-15)
            pygame.draw.circle(surface,(112,145,155),(px,py),1+(index%5==0))

    def respawn(self):
        self.crumble={o['id']:None for o in self.level.objects if o['type']=='crumble'}
        self.patrols={o['id']:[float(o['x']),1] for o in self.level.objects if o['type']=='patrol'}
        super().respawn()

    def prepare_world(self,dt,actions):
        b=self.player.body
        for obj in self.level.objects:
            if obj['type']!='crumble': continue
            state=self.crumble[obj['id']]
            tile=self.box(obj)
            standing=abs(b.box.bottom-tile.y)<1 and b.box.right>tile.x and b.x<tile.right
            if state is None and standing: state=0.0; self.audio.play('switch')
            if state is not None: state+=dt
            self.crumble[obj['id']]=state
        active=[]
        for obj in self.dynamic_objects:
            if obj['type']=='crumble' and self.crumble[obj['id']] is not None and self.crumble[obj['id']]>=.48:
                continue
            active.append(Collider(self.box(obj),True))
        self.level.colliders=self.base_colliders+active

    def update_encounters(self,dt,actions):
        b=self.player.body
        for obj in self.level.objects:
            if obj['type']=='conveyor':
                r=self.box(obj)
                if b.on_ground and abs(b.box.bottom-r.y)<1 and b.box.right>r.x and b.x<r.right:
                    b.x=max(0,min(self.level.width-b.w,b.x+obj.get('speed',72)*dt))
            elif obj['type']=='patrol':
                state=self.patrols[obj['id']]; state[0]+=state[1]*obj.get('speed',48)*dt
                if state[0]<=obj['left'] or state[0]>=obj['right']:
                    state[0]=max(obj['left'],min(obj['right'],state[0])); state[1]*=-1
                enemy=Box(state[0],obj['y'],obj.get('w',32),obj.get('h',64))
                if b.box.overlaps(enemy): self.health.remaining=0

    def draw_world(self,surface,alpha,background=True):
        super().draw_world(surface,alpha,background)
        # C looks like a full floor block but remains one-way: Willy crosses
        # it from below and lands only while falling onto its upper face.
        size=self.level.tile_size
        for row,line in enumerate(self.level.rows):
            for column,tile in enumerate(line):
                if tile in {'#','='}:
                    variant=(column*13+row*7)%4
                    image=self.mine_platforms[variant] if tile=='=' else self.mine_walls[variant]
                    surface.blit(image,(column*size,row*size))
        for obj in self.level.objects:
            r=self.box(obj); kind=obj['type']
            if kind=='coin' and obj['id'] not in self.collected_items:
                draw_key(surface,r,self.elapsed,self.mine_key.frame('idle'))
            elif kind=='hazard':
                if obj.get('style')=='stalactite':
                    draw_stalactite(surface,r)
                elif obj.get('style')=='bush':
                    draw_bush(surface,r,self.mine_bush.frame('sway',self.elapsed+r.x*.006))
            elif kind=='crumble':
                state=self.crumble[obj['id']]
                if state is None or state<.48:
                    shake=0 if state is None else (-1 if int(state*30)%2 else 1)
                    variant=(round(r.x/size)+round(r.y/size))%4
                    surface.blit(self.mine_crumbles[variant],(r.x,r.y+shake))
            elif kind=='conveyor':
                surface.blit(self.mine_conveyor,(r.x,r.y))
                shift=int(self.elapsed*38)%12
                for offset in (-12,0,12,24):
                    x=r.x+offset+shift
                    pygame.draw.lines(surface,(149,229,205),False,[(x,r.y+11),(x+5,r.y+15),(x,r.y+19)],2)
            elif kind=='patrol':
                x=self.patrols[obj['id']][0]
                facing=self.patrols[obj['id']][1]
                frame=self.mine_guardian.frame('walk',self.elapsed,facing)
                draw_patrol(surface,pygame.Rect(x,r.y,r.w,r.h),frame)
            elif kind=='goal':
                draw_exit(surface,r,self.objectives_ready)
        self.draw_player(surface,alpha)

    def draw(self,surface,alpha):
        super().draw(surface,alpha)
        if self.scroll!='none':
            keys=sum(o['id'] in self.collected_items for o in self.coins)
            pygame.draw.rect(surface,(9,17,29),(635,33,325,31))
            self.text(surface,self.tr('willy.keys','CHAVES {current}/{total}   VIDA {health}/5',current=keys,total=len(self.coins),health=self.health.remaining),652,43,(241,199,130))
            pygame.draw.rect(surface,(9,17,29),(0,64,960,31))
            self.text(surface,self.tr('willy.hint','CHAVES {current}/{total} · recolhe todas, evita os perigos e alcança a saída',current=keys,total=len(self.coins)),24,73,(245,205,105))
