"""Rebuild the original fourth demo map; overwrites ascent.json."""
import json
from pathlib import Path

rows = [["."]*48 for _ in range(18)]
for y in (16,17):
    for x in range(48):
        if not 14 <= x < 21:
            rows[y][x] = "#"
for start,end in ((7,14),(21,28)):
    for x in range(start,end):
        rows[10][x] = "="
for y in range(7,14):
    rows[y][29] = "#"
for y in range(7,16):
    rows[y][33] = "#"
for x in range(34,45):
    rows[7][x] = "="
objects = [
    {"id":"start","type":"spawn","x":64,"y":482},
    {"id":"training_ladder","type":"ladder","x":232,"y":320,"w":32,"h":192},
    {"id":"climb_beacon","type":"beacon","x":340,"y":288,"w":24,"h":32},
    {"id":"before_gap","type":"checkpoint","x":396,"y":290},
    {"id":"dash_beacon","type":"beacon","x":750,"y":288,"w":24,"h":32},
    {"id":"before_walls","type":"checkpoint","x":820,"y":290},
    {"id":"wall_beacon","type":"beacon","x":1200,"y":192,"w":24,"h":32},
    {"id":"summit","type":"checkpoint","x":1296,"y":194},
    {"id":"exit","type":"goal","x":1400,"y":166,"w":32,"h":58}
]
path = Path(__file__).resolve().parents[1]/"examples/precision/assets/ascent.json"
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps({"version":1,"name":"Ascensão","tile_size":32,
                            "tiles":["".join(row) for row in rows],"objects":objects},
                           indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(path)
