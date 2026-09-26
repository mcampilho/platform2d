"""Editable classic maps, grouped history, validation and atomic JSON saves."""
from copy import deepcopy
from dataclasses import dataclass
import json
from math import isfinite
import os
from pathlib import Path
import tempfile

from platform2d.physics.body import Box
from platform2d.physics.collision import Collider
from platform2d.world.tilemap import TileMap
from platform2d.gameplay.mechanisms import check_mechanism_structure
from platform2d.gameplay.ranged_config import weapon_spec,validate_target
from platform2d.gameplay.inventory import validate_pickup
from platform2d.gameplay.mission import validate_mission,validate_adventure


OBJECT_SIZES = {"spawn":(24,30),"coin":(24,26),"checkpoint":(24,30),
                "hazard":(32,16),"goal":(32,58),"ladder":(32,96),"beacon":(24,30),
                "entry":(24,30),"door":(32,58),"moving_platform":(96,12),"switch":(24,30),"target":(24,30),"turret":(28,30),"pickup":(24,30),"part":(24,24),"fuel":(20,24),"rocket":(48,88),"guardian":(24,30)}
from platform2d.gameplay.expansion_config import SIZES
OBJECT_SIZES.update(SIZES)
PROFILES = {
    "classic":{"spawn","coin","checkpoint","hazard","goal"},
    "precision":{"spawn","beacon","checkpoint","goal","ladder"},
    "rooms":{"spawn","coin","checkpoint","hazard","goal","entry","door","moving_platform","switch"},
    "ranged":{"spawn","checkpoint","hazard","goal","target","turret","pickup","coin"},
}
PROFILES["adventure"] = PROFILES["ranged"] | {"part","fuel","rocket","guardian"} | SIZES.keys()


def map_profile(data):
    objects = data.get("objects",[])
    if not isinstance(objects,list):
        raise ValueError("Editor: objects deve ser uma lista.")
    return data.get("editor_profile", "precision" if any(o.get("type") in {"ladder","beacon"} for o in objects if isinstance(o,dict)) else "classic")


@dataclass(frozen=True)
class Issue:
    severity: str
    message: str
    position: tuple | None = None
    room_id: str | None = None


def new_map(width=40,height=18):
    if not 8 <= width <= 256 or not 8 <= height <= 128:
        raise ValueError("Usa uma largura de 8–256 e uma altura de 8–128 tiles.")
    return {"version":1,"name":"O meu nível","tile_size":32,
            "tiles":["."*width for _ in range(height-2)]+["#"*width]*2,
            "objects":[{"id":"start","type":"spawn","x":64,"y":(height-2)*32-30},
                       {"id":"exit","type":"goal","x":(width-3)*32,"y":(height-2)*32-58,"w":32,"h":58}]}


def check_structure(data,profile=None):
    """Accept editable semantic errors, reject unsupported or unsafe structures."""
    if not isinstance(data,dict) or data.get("version") != 1:
        raise ValueError("Editor: é necessário um mapa version 1 (não um ficheiro de mundo/salas).")
    profile = profile or map_profile(data)
    if profile not in PROFILES:
        raise ValueError("Perfil do editor desconhecido.")
    size = data.get("tile_size",32)
    if type(size) is not int or not 8 <= size <= 128:
        raise ValueError("Editor: tile_size deve ser um inteiro de 8 a 128.")
    rows = data.get("tiles")
    if (not isinstance(rows,list) or not 1 <= len(rows) <= 128 or
            not all(isinstance(r,str) and 1 <= len(r) <= 256 for r in rows) or
            len({len(r) for r in rows}) != 1 or any(set(r)-set(".#=/\\") for r in rows)):
        raise ValueError("Editor: grelha retangular de até 256×128, com '.', '#', '=' e rampas / ou barra invertida.")
    if not isinstance(data.get("name","Sala"),str):
        raise ValueError("Editor: name deve ser texto.")
    if not isinstance(data.get("properties",{}),dict):
        raise ValueError("Editor: properties deve ser um objeto.")
    if profile in {"ranged","adventure"}:
        weapon_spec(data.get("properties",{}))
    objects = data.get("objects",[])
    if not isinstance(objects,list):
        raise ValueError("Editor: objects deve ser uma lista.")
    if profile in {"ranged","adventure"}:
        validate_mission(data.get("properties",{}),objects)
    if profile == "adventure":
        validate_adventure(data)
    for obj in objects:
        if not isinstance(obj,dict) or obj.get("type") not in PROFILES[profile]:
            raise ValueError(f"Objeto não suportado no perfil {profile}. O ficheiro não foi convertido.")
        if not isinstance(obj.get("id"),str) or not obj["id"]:
            raise ValueError("Todos os objetos precisam de um id de texto não vazio.")
        for field in ("x","y"):
            if type(obj.get(field)) not in (int,float) or not isfinite(obj[field]):
                raise ValueError(f"{obj['id']}: {field} deve ser um número finito.")
        for field in ("w","h"):
            if field in obj and (type(obj[field]) not in (int,float) or not isfinite(obj[field]) or obj[field] <= 0):
                raise ValueError(f"{obj['id']}: {field} deve ser positivo e finito.")
        if obj["type"] in {"target","turret"}:
            validate_target(obj)
        if obj["type"] == "pickup":
            validate_pickup(obj)
        if obj["type"] == "moving_platform":
            end = obj.get("end")
            if not isinstance(end,list) or len(end) != 2 or any(type(v) not in (int,float) or not isfinite(v) for v in end):
                raise ValueError(f"{obj['id']}: destino deve conter duas coordenadas finitas.")
            speed = obj.get("speed",60)
            if type(speed) not in (int,float) or not isfinite(speed) or speed <= 0:
                raise ValueError(f"{obj['id']}: velocidade deve ser positiva e finita.")
        if obj["type"] == "door":
            for field in ("target_room","target_entry","label"):
                if field in obj and not isinstance(obj[field],str):
                    raise ValueError(f"{obj['id']}: {field} deve ser texto.")
        if profile == "rooms":
            check_mechanism_structure(obj)
        elif "requires" in obj:
            raise ValueError("Condições de mecanismos só estão disponíveis no perfil Salas.")


class MapDocument:
    def __init__(self,data=None,path=None,profile=None):
        data = new_map() if data is None else data
        check_structure(data,profile)
        self.profile = profile or map_profile(data)
        if self.profile == "rooms" and profile is None:
            raise ValueError("As salas devem ser abertas através do ficheiro de mundo com rooms.")
        self.data = deepcopy(data)
        if self.profile in {"precision","ranged"}:
            self.data["editor_profile"] = self.profile
        self.data.setdefault("tile_size",32)
        self.data.setdefault("objects",[])
        self.path = Path(path).resolve() if path else None
        self.saved = deepcopy(self.data) if path else None
        self.undo_stack = []
        self.redo_stack = []
        self.transaction = None

    @classmethod
    def load(cls,path):
        path = Path(path).expanduser().resolve()
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError,json.JSONDecodeError) as error:
            raise ValueError(f"Não foi possível abrir: {error}") from error
        if isinstance(data,dict) and "rooms" in data:
            from .world_editor import WorldDocument
            return WorldDocument(data,path)
        return cls(data,path)

    def snapshot(self):
        return deepcopy(self.data)

    def restore(self,data):
        self.data = data

    @property
    def dirty(self):
        return self.snapshot() != self.saved

    @property
    def size(self):
        return len(self.data["tiles"][0]),len(self.data["tiles"])

    @property
    def tile_size(self):
        return self.data["tile_size"]

    def begin(self):
        if self.transaction is None:
            self.transaction = self.snapshot()

    def commit(self):
        if self.transaction is not None and self.transaction != self.snapshot():
            self.undo_stack.append(self.transaction)
            self.undo_stack = self.undo_stack[-100:]
            self.redo_stack.clear()
        self.transaction = None

    def undo(self):
        self.commit()
        if self.undo_stack:
            self.redo_stack.append(self.snapshot())
            self.restore(self.undo_stack.pop())

    def redo(self):
        self.commit()
        if self.redo_stack:
            self.undo_stack.append(self.snapshot())
            self.restore(self.redo_stack.pop())

    def paint(self,column,row,tile):
        width,height = self.size
        if not 0 <= column < width or not 0 <= row < height:
            return
        if tile not in {".","#","=","/","\\"}:
            raise ValueError("Tile desconhecido.")
        self.begin()
        line = self.data["tiles"][row]
        self.data["tiles"][row] = line[:column]+tile+line[column+1:]

    def paint_line(self,start,end,tile):
        x,y = start
        target_x,target_y = end
        dx,dy = abs(target_x-x),abs(target_y-y)
        sx,sy = (1 if x < target_x else -1),(1 if y < target_y else -1)
        error = dx-dy
        while True:
            self.paint(x,y,tile)
            if (x,y) == (target_x,target_y):
                break
            twice = error*2
            if twice > -dy:
                error -= dy
                x += sx
            if twice < dx:
                error += dx
                y += sy

    def object_box(self,obj):
        # Match the classic scene's defaults, including legacy maps.
        defaults = {"ladder":(32,96),"door":(32,58),"moving_platform":(96,12)}.get(obj["type"],(24,30))
        return Box(obj["x"],obj["y"],obj.get("w",defaults[0]),obj.get("h",defaults[1]))

    def pick(self,x,y):
        for index in range(len(self.data["objects"])-1,-1,-1):
            box = self.object_box(self.data["objects"][index])
            if box.x <= x < box.right and box.y <= y < box.bottom:
                return index
        return None

    def place(self,kind,column,row):
        if kind not in PROFILES[self.profile]:
            raise ValueError("Objeto desconhecido.")
        if self.profile in {"ranged","adventure"} and kind in {"target","turret"} and not self.data.get("properties",{}).get("weapon_enabled",True):
            raise ValueError("Ativa os disparos em Missão / ambiente antes de colocar alvos.")
        if not (0 <= column < self.size[0] and 0 <= row < self.size[1]):
            return None
        self.begin()
        w,h = OBJECT_SIZES[kind]
        size = self.tile_size
        x,y = column*size+(size-w)/2,(row+1)*size-h
        if kind == "spawn":
            existing = next((i for i,o in enumerate(self.data["objects"]) if o["type"] == "spawn"),None)
            if existing is not None:
                self.data["objects"][existing].update(x=x,y=y)
                self.commit()
                return existing
        ids = {o["id"] for o in self.data["objects"]}
        number = 1
        while f"{kind}_{number}" in ids:
            number += 1
        self.data["objects"].append({"id":f"{kind}_{number}","type":kind,"x":x,"y":y,"w":w,"h":h})
        obj = self.data["objects"][-1]
        if kind == "moving_platform":
            obj.update(end=[x,max(0,y-128)],speed=60)
        elif kind == "door":
            obj.update(target_room="",target_entry="",label="PORTA")
        elif kind == "switch":
            obj.update(activation="interact",label="Interruptor",requires=[])
        elif kind == "pickup":
            obj.update(item="medkit",quantity=1)
        elif kind in {"target","turret"}:
            obj["hp"] = 2
            if kind == "turret":
                obj.update(interval=1.2,projectile_speed=240,range=420)
        self.commit()
        return len(self.data["objects"])-1

    def update_object(self,index,**changes):
        if not 0 <= index < len(self.data["objects"]):
            return
        changed = deepcopy(self.data["objects"][index])
        changed.update(changes)
        sample = deepcopy(self.data)
        sample["objects"][index] = changed
        check_structure(sample,self.profile)
        self.begin()
        self.data["objects"][index] = changed

    def delete_object(self,index):
        if 0 <= index < len(self.data["objects"]):
            self.begin()
            self.data["objects"].pop(index)
            self.commit()

    def update_mission(self,**changes):
        allowed={"theme","weapon_enabled"} | ({"traversal","scroll"} if self.profile=="adventure" else set())
        if self.profile not in {"ranged","adventure"} or not set(changes) <= allowed:
            raise ValueError("Configuração de missão desconhecida.")
        candidate = deepcopy(self.data)
        candidate.setdefault("properties",{}).update(changes)
        check_structure(candidate,self.profile)
        self.begin()
        self.data = candidate
        self.commit()

    def update_weapon(self,**changes):
        if self.profile not in {"ranged","adventure"}:
            raise ValueError("A configuração da arma pertence ao perfil Combate.")
        properties = deepcopy(self.data.get("properties",{}))
        properties.setdefault("weapon",{}).update(changes)
        weapon_spec(properties)
        self.begin()
        self.data["properties"] = properties
        self.commit()

    def resize(self,width,height):
        mode=self.data.get('properties',{}).get('traversal')
        willy_size=mode=='willy' and (width*self.tile_size,height*self.tile_size)==(1024,512)
        if self.profile == "adventure" and not willy_size and not (960 <= width*self.tile_size <= 3840 and 576 <= height*self.tile_size <= 2048):
            raise ValueError("Aventura: dimensões entre 960×576 e 3840×2048.")
        if self.profile in {"rooms","ranged"} and (width*self.tile_size,height*self.tile_size) != (960,576):
            raise ValueError("Os perfis Salas e Combate usam ecrãs fixos de 960×576 unidades.")
        if not 8 <= width <= 256 or not 8 <= height <= 128:
            raise ValueError("Dimensões: largura 8–256, altura 8–128.")
        self.begin()
        rows = self.data["tiles"]
        self.data["tiles"] = [(rows[y][:width].ljust(width,".") if y < len(rows) else "."*width) for y in range(height)]
        self.commit()

    def rename(self,name):
        name = name.strip()
        if not name:
            raise ValueError("O nome não pode ficar vazio.")
        self.begin()
        self.data["name"] = name
        self.commit()

    def validate(self):
        from .reachability import covered_by
        issues = []
        if self.profile == "adventure":
            try:
                validate_adventure(self.data)
            except ValueError as error:
                issues.append(Issue("error",str(error)))
        width,height = (n*self.tile_size for n in self.size)
        objects = self.data["objects"]
        solids = [Box(x*self.tile_size,y*self.tile_size,self.tile_size,self.tile_size)
                  for y,row in enumerate(self.data["tiles"]) for x,t in enumerate(row) if t == "#"]
        supports = solids+[Box(x*self.tile_size,y*self.tile_size,self.tile_size,self.tile_size)
                           for y,row in enumerate(self.data["tiles"]) for x,t in enumerate(row) if t == "="]
        ramps = [Collider(Box(x*self.tile_size,y*self.tile_size,self.tile_size,self.tile_size),True,-1 if t == "/" else 1)
                 for y,row in enumerate(self.data["tiles"]) for x,t in enumerate(row) if t in "/\\"]
        spawns = [o for o in objects if o["type"] == "spawn"]
        if len(spawns) != 1:
            issues.append(Issue("error","É necessário exatamente um ponto inicial (spawn)."))
        if self.profile != "rooms" and not (self.profile == "adventure" and self.data.get("properties",{}).get("traversal") == "jetpack") and not any(o["type"] == "goal" for o in objects):
            issues.append(Issue("error","Falta uma saída (goal) para concluir o nível."))
        if self.profile in {"rooms","ranged"} and (width,height) != (960,576):
            issues.append(Issue("error","As salas deste perfil devem medir 960×576 unidades."))
        ids = set()
        hazards = [self.object_box(o) for o in objects if o["type"] == "hazard"]
        for obj in objects:
            pos = (obj["x"],obj["y"])
            box = self.object_box(obj)
            if obj["id"] in ids:
                issues.append(Issue("error",f"ID repetido: {obj['id']}",pos))
            ids.add(obj["id"])
            if self.profile in {"ranged","adventure"} and obj["id"] == "player":
                issues.append(Issue("error","O ID player está reservado ao jogador.",pos))
            if box.x < 0 or box.y < 0 or box.right > width or box.bottom > height:
                issues.append(Issue("error",f"{obj['id']}: objeto fora dos limites.",pos))
            if obj["type"] in {"spawn","checkpoint","entry","guardian"}:
                body = Box(obj["x"],obj["y"],24,30)
                if body.right > width or body.bottom > height or any(body.overlaps(s) for s in solids):
                    issues.append(Issue("error",f"{obj['id']}: corpo 24×30 sem espaço livre.",pos))
                if any(body.overlaps(h) for h in hazards):
                    issues.append(Issue("error",f"{obj['id']}: reaparecimento numa zona de dano.",pos))
                ramp_support = any(body.x < c.box.right and body.right > c.box.x and abs(body.bottom-c.surface(body.x,body.w)) <= 1 for c in ramps)
                if not ramp_support and not any(abs(body.bottom-s.y) <= 1 and body.x < s.right and body.right > s.x for s in supports):
                    issues.append(Issue("warning",f"{obj['id']}: começa no ar, sem apoio imediato.",pos))
            elif obj["type"] in {"target","turret","guardian"} and covered_by(box,solids):
                issues.append(Issue("error",f"{obj['id']}: totalmente bloqueado por sólidos; os projéteis não conseguem atingir este alvo.",pos))
            elif obj["type"] in {"coin","beacon","goal","ladder","pickup","part","fuel","rocket","ability"} and covered_by(box,solids+hazards):
                issues.append(Issue("error",f"{obj['id']}: totalmente bloqueado por sólidos ou perigos; não pode ser recolhido/ativado em segurança.",pos))
            elif obj["type"] not in {"water","air"} and any(box.overlaps(s) for s in solids):
                issues.append(Issue("warning",f"{obj['id']}: sobrepõe parcialmente um tile sólido.",pos))
            elif obj["type"] in {"coin","beacon","goal","door","pickup"} and any(box.overlaps(h) for h in hazards):
                issues.append(Issue("warning",f"{obj['id']}: sobrepõe parcialmente uma zona de dano.",pos))
            if obj["type"] == "moving_platform":
                end = Box(*obj["end"],box.w,box.h)
                if end.x < 0 or end.y < 0 or end.right > width or end.bottom > height:
                    issues.append(Issue("error",f"{obj['id']}: destino da plataforma fora da sala.",pos))
                if obj["end"] == [obj["x"],obj["y"]]:
                    issues.append(Issue("error",f"{obj['id']}: percurso da plataforma vazio.",pos))
                sweep = Box(min(box.x,end.x),min(box.y,end.y),abs(box.x-end.x)+box.w,abs(box.y-end.y)+box.h)
                if any(sweep.overlaps(s) for s in solids):
                    issues.append(Issue("warning",f"{obj['id']}: área do percurso cruza sólidos; testa o transporte e esmagamento.",pos))
            if obj["type"] == "door":
                interaction = Box(box.x-14,box.y-8,box.w+28,box.h+16)
                if covered_by(interaction,solids+hazards):
                    issues.append(Issue("error",f"{obj['id']}: área de interação da porta bloqueada.",pos))
            if obj["type"] == "switch":
                interaction = box if obj.get("activation","interact") == "touch" else Box(box.x-14,box.y-8,box.w+28,box.h+16)
                if covered_by(interaction,solids+hazards):
                    issues.append(Issue("error",f"{obj['id']}: área de ativação do interruptor bloqueada.",pos))
        mode=self.data.get('properties',{}).get('traversal')
        required={'cargo':{'crate','plate','gate'},'swim':{'water','air'},'explore':{'ability','gate'}}
        for kind in required.get(mode,set()):
            if not any(o['type']==kind for o in objects): issues.append(Issue('error',f'Este modo precisa de pelo menos um objeto {kind}.'))
        crates=[o for o in objects if o['type']=='crate']
        for obj in crates:
            r=self.object_box(obj)
            if any(r.overlaps(s) for s in solids) or any(r.overlaps(self.object_box(o)) for o in objects if o is not obj and o['type'] in {'crate','spawn','checkpoint','gate'}):
                issues.append(Issue('error',f"{obj['id']}: caixa sobreposta a um corpo ou sólido.",(r.x,r.y)))
            if not any(abs(r.bottom-s.y)<1 and r.x<s.right and r.right>s.x for s in supports):
                issues.append(Issue('warning',f"{obj['id']}: caixa sem apoio inicial; testa a queda.",(r.x,r.y)))
        for obj in (o for o in objects if o['type']=='plate'):
            r=self.object_box(obj)
            if not any(abs(r.bottom-s.y)<1 and r.x<s.right and r.right>s.x for s in supports):
                issues.append(Issue('warning',f"{obj['id']}: coloca a base da placa ao nível do chão.",(r.x,r.y)))
            if obj.get('weight',2)>len(crates)*2+1:
                issues.append(Issue('error',f"{obj['id']}: não há peso suficiente no mapa.",(r.x,r.y)))
        if mode in {'cargo','swim','escape','explore','willy'}:
            issues.append(Issue('warning','Este modo tem regras dinâmicas: F8 é inconclusivo; testa o percurso com F5.'))
        goals = [o for o in objects if o["type"] in {"goal","door"}]
        for i,goal in enumerate(goals):
            if any(self.object_box(goal).overlaps(self.object_box(other)) for other in goals[:i]):
                issues.append(Issue("warning",f"{goal['id']}: porta/saída sobreposta a outra porta/saída.",(goal["x"],goal["y"])))
        if self.profile == "precision":
            issues.append(Issue("warning","Perfil de precisão: geometria verificada; confirma saltos, dash, paredes e escadas com F5. A solução automática só está disponível no perfil clássico."))
        if self.profile == "adventure":
            issues.append(Issue("warning","Aventura: F8 procura uma rota de voo, plataformas ou bordas. O combate continua a exigir teste manual; uma pesquisa inconclusiva não prova impossibilidade."))
        if self.profile == "ranged":
            issues.append(Issue("warning","Perfil Combate: confirma com F5 os saltos, a recolha dos cristais, o alcance dos tiros e a destruição dos alvos. Não existe pesquisa automática de solução para combate."))
        return issues

    def playable(self):
        errors = [i.message for i in self.validate() if i.severity == "error"]
        if errors:
            raise ValueError("\n".join(errors))
        return TileMap(deepcopy(self.data),PROFILES[self.profile])

    def save(self,path=None):
        target = Path(path).expanduser().resolve() if path else self.path
        if target is None:
            raise ValueError("Escolhe um caminho para guardar.")
        if target.suffix.lower() != ".json":
            raise ValueError("O ficheiro deve ter extensão .json.")
        self.commit()
        self.playable()
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=target.parent,suffix=".tmp",delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(self.snapshot(),handle,ensure_ascii=False,indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary,target)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
        self.path = target
        self.saved = self.snapshot()
        return target
