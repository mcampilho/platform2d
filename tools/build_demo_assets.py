"""Regenerate the demo's original pixel-art sheet and editable map."""
import json
import os
from pathlib import Path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

ROOT = Path(__file__).resolve().parents[1] / "examples" / "classic" / "assets"
ROOT.mkdir(parents=True, exist_ok=True)
sheet = pygame.Surface((256, 40), pygame.SRCALPHA)
for frame in range(8):
    x = frame * 32
    bob = 1 if frame in (1, 3, 5) else 0
    # Helmet, visor, suit, backpack and animated boots.
    pygame.draw.rect(sheet, (34,75,95), (x+3,19+bob,8,12), border_radius=2)
    pygame.draw.rect(sheet, (116,231,205), (x+8,8+bob,19,16), border_radius=5)
    pygame.draw.rect(sheet, (222,255,236), (x+10,9+bob,13,3), border_radius=1)
    pygame.draw.rect(sheet, (20,50,71), (x+16,14+bob,12,6), border_radius=2)
    pygame.draw.rect(sheet, (88,169,188), (x+22,15+bob,4,2))
    pygame.draw.rect(sheet, (62,153,153), (x+8,23+bob,16,10), border_radius=3)
    pygame.draw.rect(sheet, (240,193,105), (x+14,24+bob,5,4))
    stride = (-3, 0, 3, 0)[frame % 4] if frame in (2,3,4,5) else 0
    for dx, offset in ((9,stride), (20,-stride)):
        pygame.draw.rect(sheet, (45,102,123), (x+dx,31,6,6+offset//2))
        pygame.draw.rect(sheet, (188,233,218), (x+dx,35+offset//2,7,3))
pygame.image.save(sheet, str(ROOT / "explorer.png"))

width, height = 76, 17
rows = [["."]*width for _ in range(height)]
for y in (14,15,16):
    for x in range(width):
        if x not in range(25,29) and x not in range(48,52):
            rows[y][x] = "#"
for x,y,length,tile in [(8,12,5,"="), (15,10,4,"="), (21,12,4,"#"),
                        (26,11,3,"="), (32,12,5,"="), (39,10,4,"="),
                        (46,12,3,"="), (50,11,3,"="), (56,12,4,"#"), (63,10,4,"=")]:
    for dx in range(length):
        rows[y][x+dx] = tile
objects = [{"id":"start","type":"spawn","x":80,"y":418},
           {"id":"beacon","type":"checkpoint","x":1100,"y":418},
           {"id":"exit","type":"goal","x":2330,"y":390,"w":32,"h":58},
           {"id":"spikes","type":"hazard","x":1376,"y":432,"w":64,"h":16}]
for i,(x,y) in enumerate([(320,350),(530,285),(850,316),(1140,350),(1310,285),(1630,316),(1840,350),(2070,285)]):
    objects.append({"id":f"crystal_{i+1}","type":"coin","x":x,"y":y,"w":24,"h":26})
(ROOT / "station.json").write_text(json.dumps({"version":1,"name":"Estação Aurora","tile_size":32,
    "tiles":["".join(row) for row in rows],"objects":objects}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(f"Assets written to {ROOT}")
