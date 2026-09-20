"""One editable world, with global history and an active room view."""
from copy import deepcopy
from pathlib import Path

from .editor_model import MapDocument, Issue, check_structure, new_map
from platform2d.world.room import RoomWorld
from platform2d.gameplay.mechanisms import reference_errors, optimistic_access, requirements


def new_world():
    first,second = new_map(30,18),new_map(30,18)
    first["name"],second["name"] = "Átrio","Galeria"
    first["objects"] = [first["objects"][0],
        dict(id="to_gallery",type="door",x=864,y=454,w=32,h=58,target_room="gallery",target_entry="start")]
    second["objects"].append(dict(id="to_atrium",type="door",x=128,y=454,w=32,h=58,target_room="atrium",target_entry="start"))
    return dict(version=1,name="O meu mundo",start_room="atrium",start_entry="start",rooms={"atrium":first,"gallery":second})


class WorldDocument(MapDocument):
    profile = "rooms"

    def __init__(self,data=None,path=None):
        data = new_world() if data is None else data
        if not isinstance(data,dict) or data.get("version") != 1 or not isinstance(data.get("rooms"),dict) or not data["rooms"]:
            raise ValueError("Mundo: é necessária uma lista de salas não vazia em rooms, version 1.")
        if not isinstance(data.get("name","Mundo"),str):
            raise ValueError("O nome do mundo deve ser texto.")
        for key,room in data["rooms"].items():
            if not isinstance(key,str) or not key.strip():
                raise ValueError("Cada sala precisa de um ID não vazio.")
            check_structure(room,"rooms")
        for field in ("start_room","start_entry"):
            if field in data and not isinstance(data[field],str):
                raise ValueError(f"{field} deve ser texto.")
        self.world = deepcopy(data)
        for room in self.world["rooms"].values():
            room.setdefault("tile_size",32)
            room.setdefault("objects",[])
        self.active_room = data.get("start_room") if data.get("start_room") in data["rooms"] else next(iter(data["rooms"]))
        self.path = Path(path).resolve() if path else None
        self.saved = self.snapshot() if path else None
        self.undo_stack,self.redo_stack = [],[]
        self.transaction = None

    @property
    def data(self):
        return self.world["rooms"][self.active_room]

    def snapshot(self):
        return deepcopy(self.world)

    def restore(self,data):
        self.world = data
        if self.active_room not in data["rooms"]:
            self.active_room = next(iter(data["rooms"]))

    def switch_room(self,room_id):
        if room_id not in self.world["rooms"]:
            raise ValueError("Sala desconhecida.")
        self.commit()
        self.active_room = room_id

    def add_room(self,room_id):
        room_id = room_id.strip()
        if not room_id or room_id in self.world["rooms"]:
            raise ValueError("Escolhe um ID de sala não vazio e ainda não utilizado.")
        self.begin()
        room = new_map(30,18)
        room["name"] = room_id
        room["objects"] = room["objects"][:1]
        self.world["rooms"][room_id] = room
        self.active_room = room_id
        self.commit()

    def rename_room(self,new_id):
        new_id = new_id.strip()
        old = self.active_room
        if new_id == old:
            return
        if not new_id or new_id in self.world["rooms"]:
            raise ValueError("Escolhe um ID de sala não vazio e ainda não utilizado.")
        self.begin()
        self.world["rooms"] = {new_id if key == old else key:room for key,room in self.world["rooms"].items()}
        for room in self.world["rooms"].values():
            for obj in room["objects"]:
                if obj["type"] == "door" and obj.get("target_room") == old:
                    obj["target_room"] = new_id
                for ref in obj.get("requires",[]):
                    if ref["room"] == old:
                        ref["room"] = new_id
        if self.world.get("start_room") == old:
            self.world["start_room"] = new_id
        self.active_room = new_id
        self.commit()

    def delete_room(self):
        if len(self.world["rooms"]) == 1:
            raise ValueError("Não é possível eliminar a última sala.")
        self.begin()
        del self.world["rooms"][self.active_room]
        self.active_room = next(iter(self.world["rooms"]))
        self.commit()  # Broken references remain visible and must be repaired.

    def update_object(self,index,**changes):
        if not 0 <= index < len(self.data["objects"]):
            return
        old = self.data["objects"][index]
        old_id,kind = old["id"],old["type"]
        new_id = changes.get("id",old_id)
        if new_id != old_id and any(o["id"] == new_id for o in self.data["objects"]):
            raise ValueError("ID já utilizado nesta sala.")
        super().update_object(index,**changes)
        if kind == "switch" and new_id != old_id:
            for room in self.world["rooms"].values():
                for obj in room["objects"]:
                    for ref in obj.get("requires",[]):
                        if (ref["room"],ref["switch"]) == (self.active_room,old_id):
                            ref["switch"] = new_id
        if kind in {"spawn","entry"} and new_id != old_id:
            for room in self.world["rooms"].values():
                for obj in room["objects"]:
                    if obj["type"] == "door" and (obj.get("target_room"),obj.get("target_entry")) == (self.active_room,old_id):
                        obj["target_entry"] = new_id
            if (self.world.get("start_room"),self.world.get("start_entry")) == (self.active_room,old_id):
                self.world["start_entry"] = new_id

    def set_start(self,room_id,entry_id):
        if entry_id not in self.entries(room_id):
            raise ValueError("Escolhe uma entrada existente.")
        self.begin()
        self.world.update(start_room=room_id,start_entry=entry_id)
        self.commit()

    def entries(self,room_id):
        return [o["id"] for o in self.world["rooms"].get(room_id,{}).get("objects",[]) if o["type"] in {"spawn","entry"}]

    def link_door(self,index,room_id,entry_id):
        if self.data["objects"][index]["type"] != "door" or entry_id not in self.entries(room_id):
            raise ValueError("Escolhe uma porta e uma entrada existente.")
        self.update_object(index,target_room=room_id,target_entry=entry_id)
        self.commit()

    def validate(self):
        issues = []
        rooms = self.world["rooms"]
        for room_id,obj,message in reference_errors(rooms):
            issues.append(Issue("error",f"{room_id}/{obj['id']}: {message}",(obj["x"],obj["y"]),room_id))
        goals = []
        for room_id,room in rooms.items():
            for issue in MapDocument(room,profile="rooms").validate():
                issues.append(Issue(issue.severity,f"{room_id}: {issue.message}",issue.position,room_id))
            for obj in room["objects"]:
                if obj["type"] == "goal":
                    goals.append(room_id)
                if obj["type"] == "door":
                    target,entry = obj.get("target_room"),obj.get("target_entry")
                    if not isinstance(target,str) or target not in rooms or entry not in self.entries(target):
                        issues.append(Issue("error",f"{room_id}/{obj['id']}: destino de porta inexistente ou por ligar.",(obj["x"],obj["y"]),room_id))
        if not goals:
            issues.append(Issue("error","O mundo precisa de pelo menos uma saída final (goal)."))
        start,entry = self.world.get("start_room"),self.world.get("start_entry")
        if start not in rooms or entry not in self.entries(start):
            issues.append(Issue("error","A sala/entrada inicial do mundo não existe."))
        else:
            reached,signals = optimistic_access(rooms,start)
            for room_id,room in rooms.items():
                for obj in room["objects"]:
                    if obj.get("requires") and not requirements(obj) <= signals:
                        issues.append(Issue("warning",f"{room_id}/{obj['id']}: condições bloqueadas; dependência circular ou interruptor atrás de uma porta fechada.",(obj["x"],obj["y"]),room_id))
            for room_id in rooms.keys()-reached:
                required = any(o["type"] == "coin" for o in rooms[room_id]["objects"])
                issues.append(Issue("error" if required else "warning",f"{room_id}: sem ligação desde o início"+("; contém cristais obrigatórios." if required else "."),None,room_id))
            if goals and not reached.intersection(goals):
                issues.append(Issue("error","Nenhuma saída final tem ligação desde a sala inicial."))
            elif goals and not any(o["type"] == "goal" and requirements(o) <= signals for key in reached for o in rooms[key]["objects"]):
                issues.append(Issue("error","Todas as saídas finais dependem de interruptores que não podem ser ativados, mesmo ignorando a geometria."))
        issues.append(Issue("warning","Verificados geometria e destinos. As ligações não provam um percurso jogável: testa portas, saltos e plataformas com F5."))
        return issues

    def playable(self):
        errors = [i.message for i in self.validate() if i.severity == "error"]
        if errors:
            raise ValueError("\n".join(errors))
        return RoomWorld(self.snapshot())
