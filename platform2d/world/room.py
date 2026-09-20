"""Room definitions, in-session state and validated door connections."""
from dataclasses import dataclass, field
import json
from pathlib import Path
from copy import deepcopy

from platform2d.physics.body import Box
from platform2d.physics.platform import MovingPlatform
from .tilemap import TileMap
from platform2d.gameplay.mechanisms import Mechanisms, check_mechanism_structure, reference_errors


@dataclass
class RoomState:
    removed: set[str] = field(default_factory=set)
    flags: dict = field(default_factory=dict)


class Room:
    def __init__(self, room_id, data):
        self.id = room_id
        self.level = TileMap(data, {"entry", "door", "moving_platform", "switch"})
        for obj in self.level.objects:
            check_mechanism_structure(obj)
        self.entries = {o["id"]: (o["x"], o["y"]) for o in self.level.objects
                        if o["type"] in {"spawn", "entry"}}
        for entry_id, (x, y) in self.entries.items():
            box = Box(x, y, 24, 30)
            if (box.right > self.level.width or box.bottom > self.level.height or
                    any(box.overlaps(c.box) for c in self.level.colliders if not c.one_way)):
                raise ValueError(f"Sala {room_id}: entrada {entry_id} sem espaço livre 24×30.")
        self.reset()

    def reset(self):
        self.state = RoomState()
        self.platforms = []
        for obj in self.level.objects:
            if obj["type"] == "moving_platform":
                end = obj.get("end")
                if not isinstance(end, list) or len(end) != 2:
                    raise ValueError(f"Plataforma {obj['id']}: end deve conter duas coordenadas.")
                p = MovingPlatform(obj["id"], (obj["x"], obj["y"]), tuple(end),
                                   obj.get("w", 96), obj.get("h", 12), obj.get("speed", 60))
                for x,y in (p.start,p.end):
                    if x < 0 or y < 0 or x+p.w > self.level.width or y+p.h > self.level.height:
                        raise ValueError(f"Plataforma {p.id}: percurso fora da sala.")
                self.platforms.append(p)

    def objects(self, kind=None):
        return [obj for obj in self.level.objects if obj["id"] not in self.state.removed
                and (kind is None or obj["type"] == kind)]

    def update(self, dt):
        for platform in self.platforms:
            platform.update(dt)


class RoomWorld:
    """Only the active room advances. Leaving preserves objects and platform phase."""

    def __init__(self, data):
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("Mundo: version deve ser 1.")
        data = deepcopy(data)
        self.definition = deepcopy(data)
        definitions = data.get("rooms")
        if not isinstance(definitions, dict) or not definitions:
            raise ValueError("Mundo: rooms deve conter pelo menos uma sala.")
        self.rooms = {key: Room(key, value) for key,value in definitions.items()}
        errors = list(reference_errors(definitions))
        if errors:
            key,obj,message = errors[0]
            raise ValueError(f"{key}/{obj['id']}: {message}")
        self.mechanisms = Mechanisms()
        self.name = data.get("name","Arquivo Lunar")
        self.start_room = data.get("start_room")
        self.start_entry = data.get("start_entry")
        self.validate_destination(self.start_room, self.start_entry)
        for room in self.rooms.values():
            for door in room.objects("door"):
                self.validate_destination(door.get("target_room"), door.get("target_entry"))
        self.reset()

    @classmethod
    def load(cls, path):
        try:
            return cls(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Não foi possível ler o mundo {path}: {error}") from error

    @property
    def current(self):
        return self.rooms[self.current_id]

    def validate_destination(self, room_id, entry_id):
        if not isinstance(room_id, str) or room_id not in self.rooms:
            raise ValueError(f"Mundo: sala de destino desconhecida: {room_id}.")
        if not isinstance(entry_id, str) or entry_id not in self.rooms[room_id].entries:
            raise ValueError(f"Mundo: entrada {entry_id} desconhecida na sala {room_id}.")

    def enter(self, room_id, entry_id):
        self.validate_destination(room_id, entry_id)
        self.current_id = room_id
        return self.current.entries[entry_id]

    def set_checkpoint(self, position):
        self.checkpoint = (self.current_id, tuple(position))

    def respawn(self):
        self.current_id, position = self.checkpoint
        return position

    def reset(self):
        self.mechanisms.reset()
        for room in self.rooms.values():
            room.reset()
        position = self.enter(self.start_room, self.start_entry)
        self.set_checkpoint(position)
