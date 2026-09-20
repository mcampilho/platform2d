"""Versioned checkpoint saves. Validate the entire payload before changing state."""
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import tempfile

from platform2d.physics.body import Box
from .mechanisms import requirements

FORMAT = "platform2d.rooms.progress"
VERSION = 1
MAX_BYTES = 2 * 1024 * 1024


def fingerprint(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")).hexdigest()


def rules_fingerprint(movement):
    return fingerprint(dict(controller="arcade-v1",resume="checkpoint",movement=movement))


def fail(message):
    raise ValueError(message)


def fields(value,keys,label):
    if not isinstance(value,dict) or set(value) != set(keys):
        fail(f"Gravação inválida: campos de {label}.")


def finite(value,minimum=0):
    try:
        return type(value) in (int,float) and isfinite(value) and value >= minimum
    except OverflowError:
        return False


def string_list(value):
    return isinstance(value,list) and all(isinstance(v,str) for v in value) and len(value) == len(set(value))


def validate_progress(payload,world,movement):
    fields(payload,{"format","version","world","rules","checkpoint","rooms","switches","stats"},"progresso")
    if payload["format"] != FORMAT or type(payload["version"]) is not int or payload["version"] != VERSION:
        fail("Formato ou versão de gravação não suportados.")
    if payload["world"] != fingerprint(world.definition):
        fail("Gravação incompatível: o mundo foi alterado ou pertence a outro mapa.")
    if payload["rules"] != rules_fingerprint(movement):
        fail("Gravação incompatível: as definições de movimento foram alteradas.")
    cp = payload["checkpoint"]
    fields(cp,{"room","position"},"checkpoint")
    if not isinstance(cp["room"],str) or cp["room"] not in world.rooms:
        fail("Gravação inválida: sala do checkpoint desconhecida.")
    pos = cp["position"]
    if not isinstance(pos,list) or len(pos) != 2 or not all(finite(v) for v in pos):
        fail("Gravação inválida: posição do checkpoint.")
    allowed = {(world.start_room,tuple(world.rooms[world.start_room].entries[world.start_entry]))}
    allowed.update((key,(o["x"],o["y"])) for key,room in world.rooms.items() for o in room.level.objects if o["type"] == "checkpoint")
    if (cp["room"],tuple(pos)) not in allowed:
        fail("Gravação inválida: checkpoint não definido neste mundo.")
    room = world.rooms[cp["room"]]
    body = Box(*pos,24,30)
    if body.right > room.level.width or body.bottom > room.level.height or any(body.overlaps(c.box) for c in room.level.colliders if not c.one_way) or any(body.overlaps(Box(o["x"],o["y"],o.get("w",24),o.get("h",30))) for o in room.level.objects if o["type"] == "hazard"):
        fail("O checkpoint gravado não tem espaço seguro para reaparecer.")
    fields(payload["rooms"],world.rooms.keys(),"salas")
    coins = total = 0
    for key,room in world.rooms.items():
        state = payload["rooms"][key]
        fields(state,{"collected","checkpoint","platforms"},f"sala {key}")
        valid_coins = {o["id"] for o in room.level.objects if o["type"] == "coin"}
        if not string_list(state["collected"]) or not set(state["collected"]) <= valid_coins:
            fail(f"Gravação inválida: cristais na sala {key}.")
        coins += len(state["collected"])
        total += len(valid_coins)
        checkpoint_ids = {o["id"] for o in room.level.objects if o["type"] == "checkpoint"}
        if state["checkpoint"] is not None and (not isinstance(state["checkpoint"],str) or state["checkpoint"] not in checkpoint_ids):
            fail(f"Gravação inválida: checkpoint da sala {key}.")
        fields(state["platforms"],{p.id for p in room.platforms},f"plataformas de {key}")
        for platform in room.platforms:
            phase = state["platforms"][platform.id]
            if not finite(phase) or phase >= 2*platform.length:
                fail(f"Gravação inválida: fase da plataforma {platform.id}.")
    refs = payload["switches"]
    if not isinstance(refs,list) or any(not isinstance(r,list) or len(r) != 2 or not all(isinstance(v,str) for v in r) for r in refs):
        fail("Gravação inválida: interruptores.")
    active = {tuple(r) for r in refs}
    switches = {(key,o["id"]):o for key,room in world.rooms.items() for o in room.level.objects if o["type"] == "switch"}
    if len(active) != len(refs) or not active <= switches.keys():
        fail("Gravação inválida: interruptores desconhecidos/repetidos.")
    # A monotonic activation history must have a valid ordering, not just a cycle.
    justified = set()
    while True:
        additions = {key for key in active-justified if requirements(switches[key]) <= justified}
        if not additions:
            break
        justified.update(additions)
    if justified != active:
        fail("Gravação inválida: condições dos interruptores não satisfeitas.")
    stats = payload["stats"]
    fields(stats,{"deaths","elapsed","won"},"estatísticas")
    if type(stats["deaths"]) is not int or stats["deaths"] < 0 or not finite(stats["elapsed"]) or type(stats["won"]) is not bool:
        fail("Gravação inválida: estatísticas.")
    if stats["won"] and (coins != total or not any(o["type"] == "goal" and requirements(o) <= active for room in world.rooms.values() for o in room.level.objects)):
        fail("Gravação inválida: vitória sem objetivos concluídos.")
    return deepcopy(payload)


def capture_progress(world,movement,stats):
    payload = dict(format=FORMAT,version=VERSION,world=fingerprint(world.definition),rules=rules_fingerprint(movement),
        checkpoint=dict(room=world.checkpoint[0],position=list(world.checkpoint[1])),
        rooms={key:dict(collected=sorted(room.state.removed),checkpoint=room.state.flags.get("checkpoint"),
                       platforms={p.id:p.distance for p in room.platforms}) for key,room in world.rooms.items()},
        switches=[list(key) for key in sorted(world.mechanisms.active)],stats=deepcopy(stats))
    return validate_progress(payload,world,movement)


def restore_progress(payload,world,movement):
    data = validate_progress(payload,world,movement)
    # Everything that can reject input happens above this point.
    for key,state in data["rooms"].items():
        room = world.rooms[key]
        room.state.removed = set(state["collected"])
        room.state.flags = {} if state["checkpoint"] is None else {"checkpoint":state["checkpoint"]}
        for platform in room.platforms:
            platform.distance = state["platforms"][platform.id]
            platform.update(0)
            platform.previous = platform.box
    world.mechanisms.active = {tuple(ref) for ref in data["switches"]}
    world.checkpoint = (data["checkpoint"]["room"],tuple(data["checkpoint"]["position"]))
    world.current_id = world.checkpoint[0]
    return data["stats"]


def unique_object(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            fail("Gravação inválida: chave JSON repetida.")
        result[key] = value
    return result


class ProgressSlot:
    """Disk slot, or isolated memory slot when path is None (editor previews)."""
    def __init__(self,path=None):
        self.path = Path(path).expanduser().resolve() if path is not None else None
        self.memory = None

    def read(self,world,movement):
        if self.path is None:
            if self.memory is None:
                fail("Ainda não existe gravação neste teste. Usa F6 primeiro.")
            payload = self.memory
        else:
            try:
                with self.path.open("rb") as handle:
                    raw = handle.read(MAX_BYTES+1)
                if len(raw) > MAX_BYTES:
                    fail("Gravação demasiado grande.")
                payload = json.loads(raw.decode("utf-8-sig"),object_pairs_hook=unique_object,
                                     parse_constant=lambda value:fail("Gravação inválida: número não finito."))
            except FileNotFoundError as error:
                raise ValueError("Ainda não existe gravação. Usa F6 para guardar.") from error
            except (UnicodeError,json.JSONDecodeError,RecursionError) as error:
                raise ValueError("Não foi possível ler a gravação: JSON inválido.") from error
        return validate_progress(payload,world,movement)

    def save(self,world,movement,stats):
        payload = capture_progress(world,movement,stats)
        if self.path is None:
            self.memory = payload
            return
        if self.path.exists():
            # Never overwrite a world file, an incompatible save or damaged data.
            self.read(world,movement)
        raw = json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
        if len(raw.encode("utf-8")) > MAX_BYTES:
            fail("Progresso demasiado grande para esta versão.")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=self.path.parent,suffix=".tmp",delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary,self.path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def load(self,world,movement):
        return restore_progress(self.read(world,movement),world,movement)


def default_save_path(world_path=None,example="rooms"):
    if world_path is None:
        return Path("saves")/(example+".progress.json")
    canonical = str(Path(world_path).expanduser().resolve())
    identity = sha256((canonical.casefold() if os.name == "nt" else canonical).encode("utf-8")).hexdigest()[:12]
    return Path("saves")/("world-"+identity+".progress.json")
