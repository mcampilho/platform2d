"""Rebuild the original third-demo map; overwrites outpost.json."""
import json
from pathlib import Path

rows = [["."]*30 for _ in range(18)]
for y in (16,17):
    rows[y] = ["#"]*30
for start,end in ((8,15),(20,25)):
    for x in range(start,end):
        rows[14][x] = "="
rows[15][17] = "#"
objects = [
    {"id":"start","type":"spawn","x":56,"y":482},
    {"id":"iris","type":"npc","x":142,"y":482,"w":24,"h":30},
    {"id":"guard_1","type":"enemy","x":400,"y":482,"left":300,"right":478,"facing":-1},
    {"id":"guard_2","type":"enemy","x":744,"y":482,"left":640,"right":798,"facing":-1},
    {"id":"console","type":"switch","x":836,"y":478,"w":28,"h":34},
    {"id":"exit_gate","type":"gate","x":896,"y":384,"w":16,"h":128},
    {"id":"exit","type":"goal","x":930,"y":454,"w":24,"h":58}
]
target = Path(__file__).resolve().parents[1]/"examples/sentinels/assets/outpost.json"
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps({"version":1,"name":"Posto de vigia","tile_size":32,
                              "tiles":["".join(row) for row in rows],"objects":objects},
                             ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(target)
