"""Rebuild only the original second demo map. Replaces world.json."""
import json
from pathlib import Path


def room(name, gap=False):
    rows = [["."]*30 for _ in range(18)]
    for y in (16,17):
        for x in range(30):
            if not gap or x < 7 or x >= 22:
                rows[y][x] = "#"
    if not gap:
        for x in range(12,21):
            rows[10][x] = "="
    return {"version":1,"name":name,"tile_size":32,"tiles":["".join(r) for r in rows],"objects":[]}


atrium = room("01 · Átrio dos elevadores")
atrium["objects"] = [
    {"id":"start","type":"spawn","x":72,"y":482},
    {"id":"return","type":"entry","x":824,"y":482},
    {"id":"low_crystal","type":"coin","x":172,"y":482},
    {"id":"high_crystal","type":"coin","x":460,"y":290},
    {"id":"lift","type":"moving_platform","x":288,"y":480,"w":96,"h":12,"end":[288,288],"speed":48},
    {"id":"to_archive","type":"door","x":884,"y":454,"w":32,"h":58,"target_room":"archive","target_entry":"from_atrium","label":"ARQUIVO"}
]
archive = room("02 · Galeria suspensa",True)
archive["objects"] = [
    {"id":"start","type":"spawn","x":112,"y":482},
    {"id":"from_atrium","type":"entry","x":112,"y":482},
    {"id":"checkpoint","type":"checkpoint","x":146,"y":482},
    {"id":"to_atrium","type":"door","x":40,"y":454,"w":32,"h":58,"target_room":"atrium","target_entry":"return","label":"ÁTRIO"},
    {"id":"ferry","type":"moving_platform","x":192,"y":448,"w":112,"h":12,"end":[656,448],"speed":80},
    {"id":"crossing_crystal","type":"coin","x":454,"y":418},
    {"id":"far_crystal","type":"coin","x":782,"y":482},
    {"id":"core","type":"goal","x":890,"y":454,"w":34,"h":58}
]
target = Path(__file__).resolve().parents[1]/"examples/rooms/assets/world.json"
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps({"version":1,"start_room":"atrium","start_entry":"start",
                             "rooms":{"atrium":atrium,"archive":archive}},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(target)
