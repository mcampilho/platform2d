"""Validated preferences, separate from game settings, maps and saves."""
from copy import deepcopy
import json
from math import isfinite
import os
from pathlib import Path
import tempfile
import pygame

BUTTONS = {"A":pygame.CONTROLLER_BUTTON_A,"B":pygame.CONTROLLER_BUTTON_B,
           "X":pygame.CONTROLLER_BUTTON_X,"Y":pygame.CONTROLLER_BUTTON_Y,
           "LB":pygame.CONTROLLER_BUTTON_LEFTSHOULDER,"RB":pygame.CONTROLLER_BUTTON_RIGHTSHOULDER,
           "Back":pygame.CONTROLLER_BUTTON_BACK,"Start":pygame.CONTROLLER_BUTTON_START,
           "L3":pygame.CONTROLLER_BUTTON_LEFTSTICK,"R3":pygame.CONTROLLER_BUTTON_RIGHTSTICK}
DIRECTIONS = {"left":pygame.CONTROLLER_BUTTON_DPAD_LEFT,"right":pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
              "up":pygame.CONTROLLER_BUTTON_DPAD_UP,"down":pygame.CONTROLLER_BUTTON_DPAD_DOWN}
DEFAULT_BUTTONS = {"guard":"R3","jump":"A","dash":"B","attack":"X","shoot":"X","interact":"Y","use_item":"Y","continue":"RB","pause":"Start",
                   "restart":"Back","save_progress":"LB","load_progress":"RB"}
RESERVED = {pygame.K_ESCAPE,pygame.K_F3,pygame.K_F5,pygame.K_F10,pygame.K_F11,pygame.K_F12}


def defaults(bindings):
    used,buttons = set(),{}
    for action in bindings:
        if action in DIRECTIONS:
            continue
        button = DEFAULT_BUTTONS.get(action)
        if action == "attack" and button in used and "L3" not in used:
            button = "L3"
        if action == "interact" and button in used and "B" not in used:
            button = "B"
        buttons[action] = button if button not in used else None
        used.add(button)
    return {"keys":deepcopy(bindings),"buttons":buttons,"deadzone":.35}


def validate(data, bindings):
    if not isinstance(data,dict) or set(data) != {"keys","buttons","deadzone"}:
        raise ValueError("Formato de comandos inválido.")
    if not isinstance(data["keys"],dict) or set(data["keys"]) != set(bindings):
        raise ValueError("Ações incompatíveis com este jogo.")
    used = set()
    for keys in data["keys"].values():
        if not isinstance(keys,list) or not 1 <= len(keys) <= 2 or not all(isinstance(k,str) for k in keys):
            raise ValueError("Cada ação precisa de uma ou duas teclas.")
        for key in keys:
            try:
                code = pygame.key.key_code(key)
            except (ValueError,TypeError):
                raise ValueError("Tecla desconhecida.") from None
            if code in RESERVED or code == pygame.K_UNKNOWN:
                raise ValueError("Tecla reservada pela aplicação.")
            if code in used:
                raise ValueError("Esta tecla já pertence a outra ação.")
            used.add(code)
    buttons = data["buttons"]
    if not isinstance(buttons,dict) or set(buttons) != set(bindings)-DIRECTIONS.keys():
        raise ValueError("Botões incompatíveis com este jogo.")
    used = set()
    for button in buttons.values():
        if button is None:
            continue
        if not isinstance(button,str) or button not in BUTTONS:
            raise ValueError("Botão desconhecido ou reservado ao movimento.")
        if button in used:
            raise ValueError("Este botão já pertence a outra ação.")
        used.add(button)
    dz = data["deadzone"]
    if type(dz) not in (float,int) or not isfinite(dz) or not .2 <= dz <= .7:
        raise ValueError("Zona morta deve estar entre 20% e 70%.")
    return deepcopy(data)


def expand_actions(data, bindings):
    """Add new actions without overwriting valid existing user choices."""
    if not isinstance(data,dict) or not isinstance(data.get("keys"),dict):
        return validate(data,bindings)
    old = data["keys"]
    if not old or not set(old) <= set(bindings):
        return validate(data,bindings)
    result = validate(data,{key:bindings[key] for key in old})
    used = {pygame.key.key_code(k) for keys in old.values() for k in keys}
    preferred = defaults(bindings)
    for action in bindings:
        if action in old:
            continue
        keys = [k for k in bindings[action] if pygame.key.key_code(k) not in used]
        if not keys:
            keys = next(([k] for k in ["f4","f7","f8",*"abcdefghijklmnopqrstuvwxyz0123456789"]
                         if pygame.key.key_code(k) not in used),None)
        if not keys:
            raise ValueError("Sem teclas disponíveis para a nova ação.")
        result["keys"][action] = keys
        used.update(pygame.key.key_code(k) for k in keys)
        if action not in DIRECTIONS:
            button = preferred["buttons"][action]
            result["buttons"][action] = button if button not in result["buttons"].values() else None
    return validate(result,bindings)


def button_codes(data):
    return {**{a:b for a,b in DIRECTIONS.items() if a in data["keys"]},
            **{a:BUTTONS[b] for a,b in data["buttons"].items() if b is not None}}


class ControlSettings:
    def __init__(self, bindings, profile="custom", path=None):
        self.defaults = validate(defaults(bindings),bindings)
        self.profile = profile
        self.path = Path(path) if path is not None else None
        self.data = deepcopy(self.defaults)
        self.warning = ""
        if self.path is not None and self.path.exists():
            try:
                if self.path.stat().st_size > 65536:
                    raise ValueError("Ficheiro de comandos demasiado grande.")
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(payload,dict) or set(payload) != {"format","version","profile","controls"} or payload["format"] != "platform2d.controls" or type(payload["version"]) is not int or payload["version"] != 1 or payload["profile"] != profile:
                    raise ValueError("Formato ou perfil incompatível.")
                self.data = expand_actions(payload["controls"],bindings)
            except (OSError,ValueError,TypeError):
                self.warning = "Preferências inválidas: usados os comandos de origem."

    def save(self, data):
        candidate = validate(data,self.defaults["keys"])
        if self.path is not None:
            # Refuse to replace a map, save or unrelated existing file.
            if self.path.exists():
                try:
                    old = json.loads(self.path.read_text(encoding="utf-8"))
                except (ValueError,OSError):
                    raise ValueError("Ficheiro inválido preservado. Renomeia-o antes de guardar.") from None
                if not isinstance(old,dict) or old.get("format") != "platform2d.controls" or old.get("profile") != self.profile or type(old.get("version")) is not int or old["version"] != 1:
                    raise ValueError("O destino pertence a outro ficheiro ou perfil.")
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=self.path.parent,suffix=".tmp",delete=False) as file:
                    temporary = Path(file.name)
                    json.dump(dict(format="platform2d.controls",version=1,profile=self.profile,controls=candidate),file,ensure_ascii=False,indent=2,allow_nan=False)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temporary,self.path)
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
        self.data = candidate
        self.warning = ""


def add_control_arguments(parser):
    parser.add_argument("--controls-dir",type=Path,default=Path("preferences"),help="Pasta de preferências de comandos")
