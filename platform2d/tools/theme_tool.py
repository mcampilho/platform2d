"""Create, inspect and render portable Platform2D visual themes."""
import json
import os
from pathlib import Path

from platform2d.rendering.theme import DEFAULT_PALETTE, load_theme
from platform2d.rendering.sprite_animation import SpriteAtlas


def create_theme(destination, identifier="my-theme", name="O meu tema"):
    target = Path(destination)
    if target.exists():
        raise ValueError("A pasta do tema já existe; escolhe uma pasta nova.")
    if (not isinstance(identifier, str) or not identifier or
            not all(char.islower() or char.isdigit() or char == "-" for char in identifier)):
        raise ValueError("O id do tema aceita letras minúsculas, números e hífenes.")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("O tema precisa de nome.")
    target.mkdir(parents=True)
    manifest = {
        "format": "platform2d.theme", "version": 1, "id": identifier, "name": name,
        "palette": {key: list(value) for key, value in DEFAULT_PALETTE.items()},
        "assets": {}, "parallax": {"background": .25, "foreground": .55}, "sprites": {},
    }
    path = target / f"{identifier}.theme.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "README.txt").write_text(
        "Coloca as imagens nesta pasta e acrescenta-as a assets no manifesto.\n"
        "Valida com: python -m platform2d theme check " + path.name + " --preview preview.png\n",
        encoding="utf-8")
    return path.resolve()


def inspect_theme(path, asset_root=None):
    theme = load_theme(path, asset_root)
    report = []
    if theme.assets or theme.sprites:
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame
        for role, asset in theme.assets.items():
            try:
                image = pygame.image.load(str(asset))
            except pygame.error as error:
                raise ValueError(f"Tema visual: não foi possível abrir {asset.name}: {error}") from error
            width, height = image.get_size()
            if width <= 0 or height <= 0:
                raise ValueError(f"Tema visual: dimensões inválidas em {asset.name}")
            report.append((role, asset.name, width, height,
                           bool(image.get_flags() & pygame.SRCALPHA or image.get_masks()[3])))
        for sprite_id,spec in theme.sprites.items():
            atlas=SpriteAtlas.from_spec(spec)
            image=pygame.image.load(str(spec.image))
            report.append((f"sprite.{sprite_id}",spec.image.name,image.get_width(),image.get_height(),
                           bool(image.get_flags() & pygame.SRCALPHA or image.get_masks()[3])))
    return theme, report


def render_preview(theme, destination, size=(960, 540)):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    pygame.init()
    surface = pygame.Surface(size)
    ink, panel = theme.color("ink"), theme.color("panel")
    surface.fill(ink)
    background = theme.assets.get("background")
    if background:
        image = pygame.image.load(str(background))
        scaled_width = round(image.get_width() * size[1] / image.get_height())
        image = pygame.transform.smoothscale(image, (scaled_width, size[1]))
        surface.blit(image, ((size[0] - scaled_width) // 2, 0))
        veil = pygame.Surface(size, pygame.SRCALPHA); veil.fill((*ink, 55)); surface.blit(veil, (0, 0))
    foreground = theme.assets.get("foreground")
    if foreground:
        image = pygame.image.load(str(foreground))
        scaled_width = round(image.get_width() * size[1] / image.get_height())
        surface.blit(pygame.transform.smoothscale(image, (scaled_width, size[1])),
                     ((size[0] - scaled_width) // 2, 0))
    pygame.draw.rect(surface, panel, (28, 28, 360, 172), border_radius=12)
    pygame.draw.rect(surface, theme.color("accent"), (28, 28, 360, 172), 2, border_radius=12)
    font = pygame.font.SysFont("segoeui", 28, bold=True)
    small = pygame.font.SysFont("segoeui", 16)
    surface.blit(font.render(theme.name, True, theme.color("text")), (48, 46))
    surface.blit(small.render(theme.id, True, theme.color("muted")), (49, 83))
    for index, key in enumerate(DEFAULT_PALETTE):
        x, y = 49 + index % 4 * 78, 121 + index // 4 * 38
        pygame.draw.rect(surface, theme.color(key), (x, y, 62, 24), border_radius=4)
        pygame.draw.rect(surface, theme.color("text"), (x, y, 62, 24), 1, border_radius=4)
    character = theme.assets.get("character")
    if character:
        sheet = pygame.image.load(str(character))
        cell = sheet.subsurface((0, 0, sheet.get_width() // 4, sheet.get_height() // 2))
        height = 190; width = round(cell.get_width() * height / cell.get_height())
        surface.blit(pygame.transform.smoothscale(cell, (width, height)),
                     (size[0] - width - 70, size[1] - height - 35))
    if theme.sprites:
        entries=list(theme.sprites.items())[:6]
        bar=pygame.Surface((size[0]-56,118),pygame.SRCALPHA)
        bar.fill((*panel,220))
        pygame.draw.rect(bar,theme.color("line"),bar.get_rect(),1,border_radius=9)
        column=bar.get_width()/len(entries)
        for index,(sprite_id,spec) in enumerate(entries):
            atlas=SpriteAtlas.from_spec(spec)
            clip=next(iter(spec.clips))
            frame=atlas.frame(clip,.25)
            scale=min(1.8,72/frame.get_height(),column*.7/frame.get_width())
            image=pygame.transform.smoothscale(frame,(max(1,round(frame.get_width()*scale)),
                                                       max(1,round(frame.get_height()*scale))))
            x=round(index*column+(column-image.get_width())/2)
            bar.blit(image,(x,76-image.get_height()))
            label=small.render(sprite_id,True,theme.color("text"))
            bar.blit(label,(round(index*column+(column-label.get_width())/2),88))
        surface.blit(bar,(28,size[1]-136))
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(destination))
    pygame.quit()
    return destination.resolve()
