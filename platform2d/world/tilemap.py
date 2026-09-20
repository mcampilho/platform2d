import json
from copy import deepcopy
from math import isfinite
from pathlib import Path

from platform2d.physics.body import Box
from platform2d.physics.collision import Collider


class TileMap:
    def __init__(self, data, object_types=None):
        if not isinstance(data, dict):
            raise ValueError("Mapa: a raiz deve ser um objeto JSON.")
        allowed = {"spawn", "checkpoint", "coin", "hazard", "goal"}
        allowed.update(object_types or ())
        if data.get("version") != 1:
            raise ValueError("Mapa: 'version' deve ser 1.")
        self.tile_size = data.get("tile_size", 32)
        if type(self.tile_size) is not int or self.tile_size <= 0:
            raise ValueError("Mapa: tile_size deve ser um inteiro positivo.")
        self.rows = data.get("tiles")
        if (not isinstance(self.rows, list) or not self.rows or
                not all(isinstance(row, str) and row for row in self.rows) or
                len({len(row) for row in self.rows}) != 1):
            raise ValueError("Mapa: tiles deve conter linhas de texto com largura igual.")
        if any(set(row) - set(".#=/\\") for row in self.rows):
            raise ValueError("Mapa: tiles aceita '.', '#', '=', '/' e a barra invertida.")
        self.width = len(self.rows[0]) * self.tile_size
        self.height = len(self.rows) * self.tile_size
        self.colliders = []
        for y, row in enumerate(self.rows):
            for x, tile in enumerate(row):
                if tile != ".":
                    self.colliders.append(Collider(Box(x * self.tile_size, y * self.tile_size,
                                                       self.tile_size, self.tile_size), tile in "=/\\",
                                                   -1 if tile == "/" else 1 if tile == "\\" else 0))
        self.objects = data.get("objects", [])
        if not isinstance(self.objects, list):
            raise ValueError("Mapa: objects deve ser uma lista.")
        ids = set()
        for obj in self.objects:
            if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not obj["id"]:
                raise ValueError("Mapa: cada objeto precisa de um id de texto.")
            if obj["id"] in ids:
                raise ValueError(f"Mapa: id repetido: {obj['id']}")
            ids.add(obj["id"])
            if obj.get("type") not in allowed:
                raise ValueError(f"Mapa: tipo desconhecido no objeto {obj['id']}.")
            for key in ("x", "y"):
                if type(obj.get(key)) not in (int, float) or not 0 <= obj[key] < getattr(self, "width" if key == "x" else "height"):
                    raise ValueError(f"Mapa: coordenada {key} inválida em {obj['id']}.")
            for key in ("w", "h"):
                if key in obj and (type(obj[key]) not in (int, float) or not isfinite(obj[key]) or obj[key] <= 0):
                    raise ValueError(f"Mapa: dimensão {key} inválida em {obj['id']}.")
        spawns = [o for o in self.objects if o["type"] == "spawn"]
        if len(spawns) != 1:
            raise ValueError("Mapa: deve existir exatamente um spawn.")
        self.spawn = (spawns[0]["x"], spawns[0]["y"])
        self.name = data.get("name", "Sala")
        self.properties = deepcopy(data.get("properties",{}))
        if not isinstance(self.properties,dict):
            raise ValueError("Mapa: properties deve ser um objeto.")

    @classmethod
    def load(cls, path):
        try:
            return cls(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Não foi possível ler o mapa {path}: {error}") from error
