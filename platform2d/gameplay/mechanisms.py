"""Monotonic switches and AND conditions; no executable scripts in map data."""
from platform2d.core.events import Event, EventBus


def requirements(obj):
    return {(ref["room"], ref["switch"]) for ref in obj.get("requires", [])}


def check_mechanism_structure(obj):
    if "requires" in obj:
        if obj["type"] not in {"switch", "door", "goal"}:
            raise ValueError("Condições só são suportadas em interruptores, portas e saídas.")
        refs = obj["requires"]
        if not isinstance(refs, list) or any(not isinstance(r,dict) or set(r) != {"room","switch"} or
                any(not isinstance(r[k],str) or not r[k].strip() for k in ("room","switch")) for r in refs):
            raise ValueError("requires deve ser uma lista de referências {room, switch} não vazias.")
        if len(requirements(obj)) != len(refs):
            raise ValueError("Condição repetida no mesmo objeto.")
    if obj["type"] == "switch":
        if obj.get("activation","interact") not in ("interact","touch"):
            raise ValueError("Ativação de interruptor: interact ou touch.")
        if not isinstance(obj.get("label","Interruptor"),str):
            raise ValueError("O nome do interruptor deve ser texto.")


def reference_errors(rooms):
    switches = {(key,o["id"]) for key,room in rooms.items() for o in room["objects"] if o["type"] == "switch"}
    for key,room in rooms.items():
        for obj in room["objects"]:
            for ref in requirements(obj)-switches:
                yield key,obj,f"interruptor de condição inexistente: {ref[0]}/{ref[1]}."


def optimistic_access(rooms,start):
    """Overestimate access, ignoring geometry and one-way trips. Not a solution."""
    reached,signals = {start},set()
    changed = True
    while changed:
        before = (len(reached),len(signals))
        for key in tuple(reached):
            for obj in rooms[key]["objects"]:
                if not requirements(obj) <= signals:
                    continue
                if obj["type"] == "switch":
                    signals.add((key,obj["id"]))
                elif obj["type"] == "door" and obj.get("target_room") in rooms:
                    reached.add(obj["target_room"])
        changed = before != (len(reached),len(signals))
    return reached,signals


class Mechanisms:
    def __init__(self, events=None):
        self.events = events or EventBus()
        self.active = set()

    def reset(self):
        self.active.clear()

    def enabled(self, obj):
        return requirements(obj) <= self.active

    def activate(self, room_id, obj):
        key = (room_id,obj["id"])
        if obj["type"] != "switch" or key in self.active or not self.enabled(obj):
            return False
        self.active.add(key)
        self.events.publish(Event("switch_activated",key))
        return True
