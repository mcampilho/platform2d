"""Counted items with atomic stack limits; independent of maps and Pygame."""
from dataclasses import dataclass,replace
from types import MappingProxyType


@dataclass(frozen=True)
class ItemDefinition:
    id: str
    label: str
    limit: int

    def __post_init__(self):
        if not isinstance(self.id,str) or not self.id or not isinstance(self.label,str) or not self.label:
            raise ValueError("Um item precisa de ID e nome não vazios.")
        if type(self.limit) is not int or self.limit <= 0:
            raise ValueError("O limite do item deve ser um inteiro positivo.")


ITEMS = (ItemDefinition("power","Potência",3),ItemDefinition("rapid","Cadência",2),
         ItemDefinition("medkit","Kit médico",3))
CATALOG = MappingProxyType({item.id:item for item in ITEMS})


class Inventory:
    def __init__(self,definitions=ITEMS):
        definitions = tuple(definitions)
        if any(not isinstance(item,ItemDefinition) for item in definitions):
            raise ValueError("O catálogo precisa de ItemDefinition.")
        catalog = {item.id:item for item in definitions}
        if len(catalog) != len(definitions):
            raise ValueError("IDs repetidos no catálogo de itens.")
        self.catalog = MappingProxyType(catalog)
        self._counts = {}

    def _validate(self,item,quantity):
        if not isinstance(item,str) or item not in self.catalog:
            raise ValueError("Item desconhecido.")
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("A quantidade deve ser um inteiro positivo.")

    def count(self,item):
        self._validate(item,1)
        return self._counts.get(item,0)

    def add(self,item,quantity=1):
        self._validate(item,quantity)
        value = self.count(item)+quantity
        if value > self.catalog[item].limit:
            return False
        self._counts[item] = value
        return True

    def take(self,item,quantity=1):
        self._validate(item,quantity)
        value = self.count(item)-quantity
        if value < 0:
            return False
        if value:
            self._counts[item] = value
        else:
            self._counts.pop(item,None)
        return True

    def snapshot(self):
        return self._counts.copy()


def validate_pickup(obj):
    item = obj.get("item","medkit")
    if not isinstance(item,str) or item not in CATALOG:
        raise ValueError("Recolhível: escolhe power, rapid ou medkit.")
    quantity = obj.get("quantity",1)
    if type(quantity) is not int or not 1 <= quantity <= CATALOG[item].limit:
        raise ValueError(f"Quantidade de {CATALOG[item].label}: inteiro entre 1 e {CATALOG[item].limit}.")


def upgraded_weapon(base,inventory):
    """Derive from the original spec every time; never accumulate modifiers."""
    return replace(base,damage=min(100,base.damage+inventory.count("power")),
                   cooldown=max(.02,base.cooldown*.8**inventory.count("rapid")))
