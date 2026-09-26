"""Validated, data-driven visual themes with a built-in safe fallback."""
from dataclasses import dataclass
import json
from pathlib import Path


DEFAULT_PALETTE = {
    "ink": (8, 15, 28), "panel": (21, 39, 47), "line": (83, 97, 81),
    "accent": (153, 120, 78), "highlight": (215, 178, 106),
    "text": (229, 226, 204), "muted": (164, 188, 185),
}


@dataclass(frozen=True)
class SpriteSpec:
    image: Path
    frame_size: tuple
    clips: dict
    anchor: tuple = (.5,1)
    directional: bool = True


@dataclass(frozen=True)
class VisualTheme:
    id: str
    name: str
    palette: dict
    assets: dict
    parallax: dict
    sprites: dict

    def color(self, key):
        return self.palette.get(key, DEFAULT_PALETTE[key])


class ThemeHandle:
    """Keep the last valid theme while creators edit and reload its manifest."""
    def __init__(self, path=None, asset_root=None):
        self.path = path
        self.asset_root = asset_root
        self.current = load_theme(path, asset_root)
        self.error = ""

    def reload(self):
        try:
            candidate = load_theme(self.path, self.asset_root)
        except (ValueError, OSError) as error:
            self.error = str(error)
            return False
        self.current = candidate
        self.error = ""
        return True


def fallback_theme():
    return VisualTheme("default", "Platform2D", dict(DEFAULT_PALETTE), {}, {}, {})


def _color(value, field):
    if (not isinstance(value, list) or len(value) != 3 or
            any(type(channel) is not int or not 0 <= channel <= 255 for channel in value)):
        raise ValueError(f"Tema visual: {field} deve ser uma cor RGB")
    return tuple(value)


def load_theme(path, asset_root=None):
    """Load one JSON manifest; omitted paths select the dependency-free fallback."""
    if path in (None, "", "default"):
        return fallback_theme()
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Não foi possível ler o tema visual {path}: {error}") from error
    if not isinstance(data, dict) or data.get("format") != "platform2d.theme" or data.get("version") != 1:
        raise ValueError("Tema visual: formato ou versão incompatível")
    identifier, name = data.get("id"), data.get("name")
    if not isinstance(identifier, str) or not identifier or not isinstance(name, str) or not name:
        raise ValueError("Tema visual: id e name são obrigatórios")
    palette = dict(DEFAULT_PALETTE)
    raw_palette = data.get("palette", {})
    if not isinstance(raw_palette, dict) or set(raw_palette) - set(DEFAULT_PALETTE):
        raise ValueError("Tema visual: palette contém campos desconhecidos")
    palette.update({key: _color(value, f"palette.{key}")
                    for key, value in raw_palette.items()})
    assets = data.get("assets", {})
    if not isinstance(assets, dict) or set(assets) - {"background", "foreground", "character"}:
        raise ValueError("Tema visual: assets contém campos desconhecidos")
    root = Path(asset_root) if asset_root is not None else path.parent
    resolved = {}
    for key, name_value in assets.items():
        if not isinstance(name_value, str) or Path(name_value).name != name_value:
            raise ValueError(f"Tema visual: assets.{key} deve ser um nome de ficheiro")
        candidate = root / name_value
        if not candidate.is_file():
            raise ValueError(f"Tema visual: recurso em falta: {name_value}")
        resolved[key] = candidate
    parallax = data.get("parallax", {})
    if (not isinstance(parallax, dict) or set(parallax) - {"background", "foreground"} or
            any(type(value) not in (int, float) or not 0 <= value <= 1
                for value in parallax.values())):
        raise ValueError("Tema visual: fatores de parallax devem estar entre 0 e 1")
    raw_sprites=data.get("sprites",{})
    if not isinstance(raw_sprites,dict):
        raise ValueError("Tema visual: sprites deve ser um objeto")
    sprites={}
    from .sprite_animation import AnimationClip
    for sprite_id,value in raw_sprites.items():
        if (not isinstance(sprite_id,str) or not sprite_id or not isinstance(value,dict) or
                set(value)-{"image","frame_size","clips","anchor","directional"}):
            raise ValueError("Tema visual: definição de sprite inválida")
        image=value.get("image")
        if not isinstance(image,str) or Path(image).name!=image:
            raise ValueError(f"Tema visual: sprites.{sprite_id}.image deve ser um nome de ficheiro")
        candidate=root/image
        if not candidate.is_file():
            raise ValueError(f"Tema visual: recurso em falta: {image}")
        frame_size=value.get("frame_size")
        if (not isinstance(frame_size,list) or len(frame_size)!=2 or
                any(type(channel) is not int or channel<=0 for channel in frame_size)):
            raise ValueError(f"Tema visual: sprites.{sprite_id}.frame_size inválido")
        raw_clips=value.get("clips")
        if not isinstance(raw_clips,dict) or not raw_clips:
            raise ValueError(f"Tema visual: sprites.{sprite_id}.clips é obrigatório")
        clips={}
        for clip_id,clip in raw_clips.items():
            if (not isinstance(clip_id,str) or not clip_id or not isinstance(clip,dict) or
                    set(clip)-{"frames","fps","loop"}):
                raise ValueError(f"Tema visual: clip inválido em {sprite_id}")
            try:
                clips[clip_id]=AnimationClip(tuple(clip.get("frames",())),clip.get("fps",8),clip.get("loop",True))
            except (TypeError,ValueError) as error:
                raise ValueError(f"Tema visual: clip inválido em {sprite_id}.{clip_id}") from error
        anchor=value.get("anchor",[.5,1])
        if (not isinstance(anchor,list) or len(anchor)!=2 or
                any(type(channel) not in (int,float) or not 0<=channel<=1 for channel in anchor)):
            raise ValueError(f"Tema visual: sprites.{sprite_id}.anchor inválido")
        directional=value.get("directional",True)
        if type(directional) is not bool:
            raise ValueError(f"Tema visual: sprites.{sprite_id}.directional deve ser booleano")
        sprites[sprite_id]=SpriteSpec(candidate,tuple(frame_size),clips,tuple(anchor),directional)
    return VisualTheme(identifier,name,palette,resolved,dict(parallax),sprites)
