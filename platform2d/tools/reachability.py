"""Bounded classic-platformer search with replayable positive witnesses.

The optimistic envelope can rule targets out. Discretised search cannot prove
impossibility: exhaustion is explicitly inconclusive, never an error verdict.
"""
from copy import copy, deepcopy
from dataclasses import dataclass, field
import heapq
from math import sqrt
from time import perf_counter

from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController, Movement
from platform2d.core.input import Actions
from platform2d.physics.body import Body, Box
from platform2d.world.tilemap import TileMap
from .editor_model import Issue

DT = 1/60


@dataclass
class ReachabilityResult:
    status: str
    issues: list = field(default_factory=list)
    actions: tuple = ()
    explored: int = 0
    seconds: float = 0


@dataclass
class Node:
    actor: Character
    mask: int
    checkpoint: int
    held: frozenset
    parent: int = -1
    actions: tuple = ()
    cost: int = 0


def object_box(obj):
    return Box(obj["x"],obj["y"],obj.get("w",24),obj.get("h",30))


def covered_by(box, obstacles):
    """Exact rectangle-union coverage, including multiple adjacent tiles."""
    relevant = [r for r in obstacles if box.overlaps(r)]
    xs = sorted({box.x,box.right} | {max(box.x,r.x) for r in relevant} | {min(box.right,r.right) for r in relevant})
    for left,right in zip(xs,xs[1:]):
        middle = (left+right)/2
        intervals = sorted((max(box.y,r.y),min(box.bottom,r.bottom)) for r in relevant if r.x <= middle <= r.right)
        top = box.y
        for start,end in intervals:
            if start > top+1e-9:
                break
            top = max(top,end)
        if top < box.bottom-1e-9:
            return False
    return bool(relevant)


def optimistic_unreachable(level, movement):
    """Necessary reachability with unlimited run-up and no walls/hazards.

    Overestimates jump height, speed and airborne duration. Surface intervals
    include the body's width. Thus a rejected required target really cannot be
    touched under this classic controller, even under more generous conditions.
    """
    # The flat-surface envelope does not model slope walking. Only an exact
    # replay may certify a ramp map; exhausted search stays inconclusive.
    if any(c.slope for c in level.colliders):
        return []
    size = level.tile_size
    surfaces = []
    for y,row in enumerate(level.rows):
        start = None
        for x in range(len(row)+1):
            top = x < len(row) and row[x] != "." and (y == 0 or level.rows[y-1][x] != "#")
            if top and start is None:
                start = x
            if not top and start is not None:
                surfaces.append((start*size-24,x*size,y*size))
                start = None
    # Avoid a quadratic preflight on pathological checkerboard maps.
    if len(surfaces) > 1500:
        return []
    height = movement.jump_speed**2/(2*movement.gravity)+2
    def duration(start_y,end_y):
        drop = end_y-(start_y-height)
        if drop < 0:
            return None
        terminal_distance = movement.terminal_speed**2/(2*movement.gravity)
        fall = (sqrt(2*drop/movement.gravity) if drop <= terminal_distance else
                movement.terminal_speed/movement.gravity+(drop-terminal_distance)/movement.terminal_speed)
        return movement.jump_speed/movement.gravity+fall+movement.coyote_time+2*DT
    def reaches(source,target):
        time = duration(source[2],target[2])
        gap = max(0,target[0]-source[1],source[0]-target[1])
        return time is not None and gap <= movement.speed*time+2
    spawn = (level.spawn[0],level.spawn[0],level.spawn[1]+30)
    reached = [spawn]
    remaining = surfaces[:]
    checkpoints = [object_box(o) for o in level.objects if o["type"] == "checkpoint"]
    cursor = 0
    while cursor < len(reached):
        source = reached[cursor]
        cursor += 1
        next_remaining = []
        for surface in remaining:
            if reaches(source,surface):
                reached.append(surface)
            else:
                next_remaining.append(surface)
        remaining = next_remaining
        next_checkpoints = []
        for box in checkpoints:
            if reaches(source,(box.x-24,box.right,box.bottom+30)):
                reached.append((box.x,box.x,box.y+30))
            else:
                next_checkpoints.append(box)
        checkpoints = next_checkpoints
    impossible = []
    for obj in level.objects:
        if obj["type"] not in {"coin","goal"}:
            continue
        box = object_box(obj)
        target = (box.x-24,box.right,box.bottom+30)
        if not any(reaches(source,target) for source in reached):
            impossible.append(obj)
    return impossible


class ReachabilitySearch:
    """Call step() incrementally to keep the editor responsive; cancel discards it."""
    def __init__(self, data, movement=None, max_nodes=16000, max_seconds=8):
        self.data = deepcopy(data)
        self.level = TileMap(self.data)
        self.movement = deepcopy(movement or Movement())
        self.max_nodes,self.max_seconds = max_nodes,max_seconds
        self.started = perf_counter()
        self.compute_seconds = 0.0
        self.result = None
        self.nodes = []
        self.queue = []
        self.best = {}
        self.explored = 0
        self.observed = 0
        self.coins = [object_box(o) for o in self.level.objects if o["type"] == "coin"]
        self.coin_objects = [o for o in self.level.objects if o["type"] == "coin"]
        self.goals = [object_box(o) for o in self.level.objects if o["type"] == "goal"]
        self.hazards = [object_box(o) for o in self.level.objects if o["type"] == "hazard"]
        self.checkpoints = [object_box(o) for o in self.level.objects if o["type"] == "checkpoint"]
        self.full_mask = (1 << len(self.coins))-1
        self.grid = {(int(c.box.x/self.level.tile_size),int(c.box.y/self.level.tile_size)):c for c in self.level.colliders}
        self.preflight_done = False
        self._add(Node(Character(Body(*self.level.spawn),ArcadeController(self.movement)),0,-1,frozenset()))

    def _key(self,node):
        b,c = node.actor.body,node.actor.controller
        return (round(b.x/4),round(b.y/4),round(b.vx/30),round(b.vy/30),b.on_ground,
                b.wall_left,b.wall_right,round(c.coyote/DT),round(c.buffer/DT),round(c.drop_timer/DT),
                node.mask,node.checkpoint,node.held)

    def _heuristic(self,node):
        b = node.actor.body
        targets = [box for i,box in enumerate(self.coins) if not node.mask & (1 << i)]
        count = len(targets)
        if not targets:
            targets = self.goals
        distance = min((abs(box.x-b.x)+max(0,b.y-box.y)*1.7 for box in targets),default=0)
        return count*900+distance+node.cost*.55

    def _add(self,node):
        key = self._key(node)
        if self.best.get(key,float("inf")) <= node.cost:
            return
        self.best[key] = node.cost
        index = len(self.nodes)
        self.nodes.append(node)
        heapq.heappush(self.queue,(self._heuristic(node),index))

    def _nearby(self,body):
        size = self.level.tile_size
        dx = (max(abs(body.vx),self.movement.speed)*DT)+2
        dy = max(self.movement.jump_speed,self.movement.terminal_speed,abs(body.vy))*DT+2
        return [self.grid[x,y]
                for y in range(max(0,int((body.y-dy)//size)),min(len(self.level.rows),int((body.y+body.h+dy)//size)+1))
                for x in range(max(0,int((body.x-dx)//size)),min(len(self.level.rows[0]),int((body.x+body.w+dx)//size)+1))
                if (x,y) in self.grid]

    def _advance(self,node,action,full_geometry=False):
        if "restart" in action.pressed:
            position = self.level.spawn if node.checkpoint < 0 else (self.checkpoints[node.checkpoint].x,self.checkpoints[node.checkpoint].y)
            node.actor.respawn(position)
        node.actor.update(DT,action,self.level.colliders if full_geometry else self._nearby(node.actor.body))
        body = node.actor.body
        body.x = max(0,min(body.x,self.level.width-body.w))
        if body.y > self.level.height+96 or any(body.box.overlaps(h) for h in self.hazards):
            return "dead"
        coin_index = checkpoint_index = 0
        status = "alive"
        # Preserve the scene's JSON order, including a goal before the last coin.
        for obj in self.level.objects:
            kind = obj["type"]
            touches = body.box.overlaps(object_box(obj))
            if kind == "coin":
                if touches:
                    node.mask |= 1 << coin_index
                coin_index += 1
            elif kind == "checkpoint":
                if touches:
                    node.checkpoint = checkpoint_index
                checkpoint_index += 1
            elif kind == "goal" and touches and node.mask == self.full_mask:
                status = "won"
        return status

    def _branch(self,parent_index,held,frames=6):
        parent = self.nodes[parent_index]
        actor = copy(parent.actor)
        actor.body = copy(parent.actor.body)
        actor.controller = copy(parent.actor.controller)
        node = Node(actor,parent.mask,parent.checkpoint,parent.held,parent_index,cost=parent.cost)
        commands = []
        for _ in range(frames):
            action = Actions(held,frozenset(held-node.held),frozenset(node.held-held))
            node.held = held
            status = self._advance(node,action)
            commands.append(action)
            node.cost += 1
            if status == "dead":
                return
            self.observed |= node.mask
            if status == "won":
                node.actions = tuple(commands)
                self._success(node)
                return
        node.actions = tuple(commands)
        self._add(node)

    def _success(self,node):
        segments = [node.actions]
        while node.parent >= 0:
            node = self.nodes[node.parent]
            segments.append(node.actions)
        actions = tuple(action for segment in reversed(segments) for action in segment)
        replay = Node(Character(Body(*self.level.spawn),ArcadeController(deepcopy(self.movement))),0,-1,frozenset())
        status = "alive"
        for action in actions:
            status = self._advance(replay,action,full_geometry=True)
            if status == "dead":
                break
        if status != "won":
            self._finish("inconclusive",[Issue("warning","A rota candidata não passou na repetição exata. Resultado inconclusivo.")])
            return
        resets = sum("restart" in a.pressed for a in actions)
        message = f"Solução confirmada: {len(self.coins)} cristais e saída na mesma rota, {len(actions)/60:.1f}s, sem mortes."
        if resets:
            message += f" Usa R {resets} vez(es) para voltar ao ponto de reaparecimento."
        self._finish("solved",[Issue("ok",message)],actions)

    def _finish(self,status,issues,actions=()):
        self.result = ReachabilityResult(status,issues,actions,self.explored,perf_counter()-self.started)

    def step(self,expansions=1):
        if self.result:
            return self.result
        started = perf_counter()
        if not self.preflight_done:
            self.preflight_done = True
            impossible = optimistic_unreachable(self.level,self.movement)
            goals = [o for o in self.level.objects if o["type"] == "goal"]
            required = [o for o in impossible if o["type"] == "coin"]
            if goals and all(o in impossible for o in goals):
                required.extend(o for o in impossible if o["type"] == "goal")
            if required:
                self._finish("impossible",[Issue("error",f"{o['id']}: fora do alcance máximo de salto/deslocação, mesmo ignorando obstáculos.",(o["x"],o["y"])) for o in required])
                return self.result
        for _ in range(expansions):
            if not self.queue or self.explored >= self.max_nodes or self.compute_seconds+perf_counter()-started >= self.max_seconds:
                missing = [o for i,o in enumerate(self.coin_objects) if not self.observed & (1 << i)]
                issues = [Issue("warning","Não foi possível confirmar uma solução dentro dos limites de pesquisa. Isto não prova que o nível é impossível.")]
                issues.extend(Issue("warning",f"{o['id']}: não alcançado nas rotas exploradas.",(o["x"],o["y"])) for o in missing)
                if not missing:
                    issues.append(Issue("warning","A saída com todos os cristais ainda não foi confirmada numa única rota."))
                self._finish("inconclusive",issues)
                break
            _,index = heapq.heappop(self.queue)
            parent = self.nodes[index]
            if parent.cost != self.best[self._key(parent)]:
                continue
            self.explored += 1
            for direction in (-1,0,1):
                base = {"left"} if direction < 0 else {"right"} if direction > 0 else set()
                for jump in (False,True):
                    self._branch(index,frozenset(base | ({"jump"} if jump else set())))
                    if self.result:
                        break
                if self.result:
                    break
            if self.result:
                break
            if parent.actor.body.on_ground:
                self._branch(index,frozenset({"down","jump"}))
            if self.result:
                break
            position = self.level.spawn if parent.checkpoint < 0 else (self.checkpoints[parent.checkpoint].x,self.checkpoints[parent.checkpoint].y)
            if abs(parent.actor.body.x-position[0])+abs(parent.actor.body.y-position[1]) > 32:
                self._branch(index,frozenset({"restart"}),1)
        self.compute_seconds += perf_counter()-started
        return self.result

    def run(self):
        while self.result is None:
            self.step(10)
        return self.result
