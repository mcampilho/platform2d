"""Regenerate only the editor's bundled starter template."""
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from platform2d.tools.editor_model import new_map

data = new_map()
data["name"] = "O meu primeiro nível"
rows = [list(r) for r in data["tiles"]]
for x in range(8,13):
    rows[14][x] = "="
for x in range(16,20):
    rows[12][x] = "="
data["tiles"] = ["".join(r) for r in rows]
data["objects"] += [
    {"id":"crystal_1","type":"coin","x":320,"y":418,"w":24,"h":26},
    {"id":"crystal_2","type":"coin","x":548,"y":354,"w":24,"h":26},
    {"id":"checkpoint_1","type":"checkpoint","x":730,"y":482,"w":24,"h":30},
    {"id":"spikes_1","type":"hazard","x":864,"y":496,"w":64,"h":16},
]
path = root/"examples/editor/assets/workshop.json"
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(path)
