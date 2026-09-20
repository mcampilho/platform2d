"""Bounded traversal search. Positive results require replay in the host scene."""
from collections import deque
from copy import copy,deepcopy
from dataclasses import dataclass
import heapq
from math import sqrt
from time import perf_counter
from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController
from platform2d.actors.traversal import JetpackController,LedgeController
from platform2d.core.input import Actions
from platform2d.physics.body import Body,Box
from platform2d.gameplay.rocket import RocketMission
from platform2d.world.tilemap import TileMap
from .editor_model import PROFILES,Issue
from .reachability import ReachabilitySearch,Node,DT,object_box,optimistic_unreachable


@dataclass
class AdventureNode(Node):
    rocket: object=None


def sealed_targets(level):
    """Optimistic point flood: ignores body size, gravity, hazards and one-ways.

    Diagonals and an exterior border deliberately overestimate connectivity.
    Only fully enclosed mandatory regions can be rejected; no jump verdict.
    Small tiles/checkpoints disable this proof because traversal snaps/respawns
    need a more elaborate connectivity model.
    """
    rows=level.rows; h=len(rows); w=len(rows[0]); size=level.tile_size
    if size<32 or w*h>20000 or any(o['type']=='checkpoint' for o in level.objects): return []
    start=(int((level.spawn[0]+12)//size),int((level.spawn[1]+15)//size))
    seen={start}; queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)):
            nx,ny=x+dx,y+dy
            if (nx,ny) in seen or not -1<=nx<=w or not -1<=ny<=h: continue
            if 0<=nx<w and 0<=ny<h and rows[ny][nx]=='#': continue
            seen.add((nx,ny)); queue.append((nx,ny))
    missing=[]
    for obj in level.objects:
        if obj['type'] not in {'coin','goal','part','fuel','rocket'}: continue
        if obj['type']=='goal' and level.properties.get('traversal')=='jetpack': continue
        r=object_box(obj)
        # Extra margin also admits the controller's small ledge alignment snap.
        envelope=Box(r.x-32,r.y-40,r.w+64,r.h+80)
        if not any(envelope.overlaps(Box(x*size,y*size,size,size)) for x,y in seen): missing.append(obj)
    goals=[o for o in level.objects if o['type']=='goal']
    return [o for o in missing if o['type']!='goal' or all(g in missing for g in goals)]


class AdventureSearch(ReachabilitySearch):
    def __init__(self,data,movement=None,scene_factory=None,max_nodes=18000,max_seconds=12):
        self.mode=data.get('properties',{}).get('traversal','walk')
        self.scene_factory=scene_factory; self.replay=None; self.replay_actions=(); self.replay_index=0
        filtered=deepcopy(data); filtered['objects']=[o for o in filtered['objects'] if o['type'] in {'spawn','coin','checkpoint','hazard','goal'}]
        super().__init__(filtered,movement,max_nodes,max_seconds)
        self.data=deepcopy(data); self.level=TileMap(self.data,PROFILES['adventure'])
        self.by_id={o['id']:o for o in self.level.objects}
        self.rocket_object=next((o for o in self.level.objects if o['type']=='rocket'),None)
        self.nodes=[]; self.queue=[]; self.best={}; self.preflight_done=True; self.adventure_preflight=False
        controller={'walk':ArcadeController,'jetpack':JetpackController,'ledge':LedgeController}.get(self.mode,ArcadeController)(self.movement)
        controller.bounds=(self.level.width,self.level.height)
        node=AdventureNode(Character(Body(*self.level.spawn),controller),0,-1,frozenset(),rocket=RocketMission(self.level.objects) if self.mode=='jetpack' else None)
        self._add(node)

    def _key(self,node):
        key=super()._key(node); c=node.actor.controller; r=getattr(node,'rocket',None)
        return key+(c.facing,getattr(c,'anchor',None),round(getattr(c,'climb',0)/DT),round(getattr(c,'cooldown',0)/DT),
                    tuple(sorted(r.delivered)) if r else (),tuple(sorted(r.fuelled)) if r else (),r.carrying if r else None)

    def _heuristic(self,node):
        r=getattr(node,'rocket',None)
        if not r: return super()._heuristic(node)
        if r.carrying: targets=[self.rocket_object]
        elif r.next_part: targets=[self.by_id[r.next_part]]
        elif not r.ready: targets=[self.by_id[i] for i in sorted(r.fuel-r.fuelled)]
        else:
            targets=[o for i,o in enumerate(self.coin_objects) if not node.mask&(1<<i)] or [self.rocket_object]
        b=node.actor.body
        distance=min(abs(o['x']-b.x)+abs(o['y']-b.y) for o in targets)
        remaining=2*(len(r.parts)-len(r.delivered)+len(r.fuel)-len(r.fuelled))-bool(r.carrying)
        return remaining*1600+distance+node.cost*.12

    def _advance(self,node,action,full_geometry=False):
        if 'restart' in action.pressed:
            cp=None if node.checkpoint<0 else self.checkpoints[node.checkpoint]
            node.actor.respawn(self.level.spawn if cp is None else (cp.x,cp.y))
        node.actor.update(DT,action,self.level.colliders if self.mode=='ledge' or full_geometry else self._nearby(node.actor.body))
        b=node.actor.body; b.x=max(0,min(b.x,self.level.width-b.w))
        if b.y>self.level.height+64 or any(b.box.overlaps(h) for h in self.hazards): return 'dead'
        for i,box in enumerate(self.coins):
            if b.box.overlaps(box): node.mask|=1<<i
        r=getattr(node,'rocket',None)
        if r:
            for obj in self.level.objects:
                if obj['type'] in {'part','fuel'} and b.box.overlaps(object_box(obj)): r.take(obj['id'])
            if b.box.overlaps(object_box(self.rocket_object)) and 'interact' in action.pressed:
                if not r.deliver() and r.ready and node.mask==self.full_mask: return 'won'
        for i,box in enumerate(self.checkpoints):
            if b.box.overlaps(box): node.checkpoint=i
        if not r and node.mask==self.full_mask and any(b.box.overlaps(g) for g in self.goals): return 'won'
        minimum=264 if self.mode=='jetpack' else 0
        if b.y<minimum: b.y=minimum; b.vy=max(0,b.vy)
        return 'alive'

    def _branch(self,parent_index,held,frames=8):
        parent=self.nodes[parent_index]; actor=copy(parent.actor)
        actor.body=copy(parent.actor.body); actor.controller=copy(parent.actor.controller)
        r=copy(parent.rocket) if parent.rocket else None
        if r: r.delivered=set(r.delivered); r.fuelled=set(r.fuelled)
        node=AdventureNode(actor,parent.mask,parent.checkpoint,parent.held,parent_index,cost=parent.cost,rocket=r)
        commands=[]
        for _ in range(frames):
            action=Actions(held,held-node.held,node.held-held); node.held=held
            status=self._advance(node,action); commands.append(action); node.cost+=1
            if status=='dead': return
            self.observed|=node.mask
            if status=='won':
                node.actions=tuple(commands); self._success(node); return
        node.actions=tuple(commands); self._add(node)

    def _success(self,node):
        segments=[node.actions]
        while node.parent>=0:
            node=self.nodes[node.parent]; segments.append(node.actions)
        actions=tuple(a for segment in reversed(segments) for a in segment)
        if self.mode=='jetpack': actions+=tuple(Actions() for _ in range(155))
        if self.scene_factory is None:
            self._finish('inconclusive',[Issue('warning','Rota candidata encontrada, mas o anfitrião não fornece repetição nas regras reais.')]); return
        self.replay=self.scene_factory(TileMap(deepcopy(self.data),PROFILES['adventure']))
        self.replay_actions=actions; self.replay_index=0

    def step(self,expansions=1):
        if self.result: return self.result
        started=perf_counter()
        try:
            if not self.adventure_preflight:
                self.adventure_preflight=True
                if self.mode not in {'walk','jetpack','ledge'} or any(o['type'] in {'target','turret','guardian'} for o in self.level.objects):
                    self._finish('inconclusive',[Issue('warning','Combate, caixas, água, fuga e capacidades adquiridas exigem teste manual (F5). A pesquisa cobre voo, plataformas e bordas sem adversários.')]); return self.result
                missing=sealed_targets(self.level)
                if missing:
                    self._finish('impossible',[Issue('error',f"{o['id']}: região fechada por sólidos, mesmo ignorando tamanho do corpo e limites do movimento.",(o['x'],o['y'])) for o in missing]); return self.result
                if self.mode in {'walk','ledge'}:
                    generous=deepcopy(self.movement)
                    if self.mode=='ledge':
                        # More height than hand alignment + pull-up can add, and
                        # virtually unlimited horizontal travel. Only reject
                        # targets still unreachable under this relaxed model.
                        generous.jump_speed=sqrt(generous.jump_speed**2+2*generous.gravity*64)
                        generous.speed=max(generous.speed,self.level.width/DT)
                    unreachable=optimistic_unreachable(self.level,generous)
                    goals=[o for o in self.level.objects if o['type']=='goal']
                    missing=[o for o in unreachable if o['type']=='coin' or all(g in unreachable for g in goals)]
                    if missing:
                        self._finish('impossible',[Issue('error',f"{o['id']}: acima/fora do alcance mesmo num modelo mais permissivo de salto e bordas.",(o['x'],o['y'])) for o in missing]); return self.result
            if self.compute_seconds>=self.max_seconds:
                self._finish('inconclusive',[Issue('warning','Limite de pesquisa atingido. Não encontrar uma rota não prova impossibilidade.')]); return self.result
            if self.replay is not None:
                for _ in range(24):
                    if self.replay_index>=len(self.replay_actions):
                        if self.replay.won and self.replay.deaths==0:
                            self._finish('solved',[Issue('ok',f'Rota confirmada nas regras do jogo: {len(self.replay_actions)/60:.1f}s, todos os objetivos, sem mortes. Usa Ver solução para acompanhar o percurso.')],self.replay_actions)
                        else: self._finish('inconclusive',[Issue('warning','A rota candidata não venceu na repetição real. Testa manualmente; não é uma prova de impossibilidade.')])
                        break
                    self.replay.update(DT,self.replay_actions[self.replay_index]); self.replay_index+=1
                    if self.replay.deaths:
                        self._finish('inconclusive',[Issue('warning','A repetição real detetou uma morte; a rota não foi certificada.')]); break
                return self.result
            for _ in range(expansions):
                if not self.queue or self.explored>=self.max_nodes or len(self.nodes)>=self.max_nodes:
                    self._finish('inconclusive',[Issue('warning','Pesquisa limitada sem rota confirmada. Revê os acessos e testa com F5.')]); break
                _,index=heapq.heappop(self.queue); parent=self.nodes[index]
                if parent.cost!=self.best[self._key(parent)]: continue
                self.explored+=1
                anchor=getattr(parent.actor.controller,'anchor',None)
                if anchor:
                    choices=[frozenset(),frozenset({'interact'}),frozenset({'down'})]
                else:
                    choices=[]
                    for direction in (-1,0,1):
                        base={'left'} if direction<0 else {'right'} if direction>0 else set()
                        for jump in (False,True):
                            keys=base|({'jump'} if jump else set())
                            if self.mode=='jetpack': keys|={'down'}
                            choices.append(frozenset(keys))
                    if self.mode=='jetpack': choices.append(frozenset({'interact'}))
                    elif parent.actor.body.on_ground: choices.append(frozenset({'down','jump'}))
                for held in choices:
                    self._branch(index,held)
                    if self.result or self.replay is not None: break
                if self.result or self.replay is not None: break
            return self.result
        finally: self.compute_seconds+=perf_counter()-started
