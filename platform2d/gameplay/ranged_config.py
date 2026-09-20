"""Data contracts shared by the ranged demo and its editor profile."""
from .projectiles import WeaponSpec,number

WEAPON_FIELDS = {"speed","cooldown","lifetime","damage"}
TARGET_DEFAULTS = dict(hp=2,interval=1.2,projectile_speed=240,range=420)


def weapon_spec(properties):
    if not isinstance(properties,dict):
        raise ValueError("properties deve ser um objeto.")
    config = properties.get("weapon",{})
    if not isinstance(config,dict) or set(config)-WEAPON_FIELDS:
        raise ValueError("Arma: usa speed, cooldown, lifetime e damage.")
    return WeaponSpec(**config)


def validate_target(obj):
    hp = obj.get("hp",2)
    if type(hp) is not int or not 1 <= hp <= 20:
        raise ValueError("Resistência: inteiro entre 1 e 20 obrigatório.")
    if obj["type"] == "turret":
        for field,low,high in (("interval",.3,10),("projectile_speed",60,1800),("range",32,1400)):
            number(obj.get(field,TARGET_DEFAULTS[field]),low,high,field)
