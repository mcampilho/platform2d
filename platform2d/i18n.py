"""Per-game UTF-8 catalogues and rendering, without process-global locale state."""
import json
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from string import Formatter


def fields(text):
    result = set()
    for _, name, spec, conversion in Formatter().parse(text):
        if name is not None:
            if not name.isidentifier() or spec or conversion:
                raise ValueError('Use simple named placeholders, e.g. {count}')
            result.add(name)
    return result


class Translator:
    def __init__(self, folder, language='pt-PT', fallback='pt-PT'):
        self.catalogues = {}
        for path in sorted(Path(folder).glob('*.json')):
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or not isinstance(data.get('messages'), dict):
                raise ValueError(f'Invalid catalogue: {path.name}')
            if data.get('direction') not in ('ltr', 'rtl'):
                raise ValueError(f'Invalid direction: {path.name}')
            if not isinstance(data.get('name'), str) or not isinstance(data.get('font'), str):
                raise ValueError(f'Missing language name or font: {path.name}')
            if Path(data['font']).name != data['font'] or '/' in data['font'] or '\\' in data['font']:
                raise ValueError('Font must be a filename')
            for key, value in data['messages'].items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError(f'Messages must be strings: {path.name}')
                fields(value)
            self.catalogues[path.stem] = data
        if fallback not in self.catalogues:
            raise ValueError('Missing fallback catalogue')
        self.fallback = fallback
        source = self.catalogues[fallback]['messages']
        for code, data in self.catalogues.items():
            for key, value in data['messages'].items():
                if key not in source or fields(value) != fields(source[key]):
                    raise ValueError(f'Unknown key or mismatched placeholders: {code}/{key}')
        self.select(language)

    def select(self, language):
        requested = str(language).replace('_', '-').lower()
        exact = next((code for code in self.catalogues if code.lower() == requested), None)
        # Prefer an explicit regional match; otherwise use an available base language.
        base = requested.split('-')[0]
        candidates = [code for code in self.catalogues if code.lower().split('-')[0] == base]
        self.language = exact or (candidates[0] if len(candidates) == 1 else self.fallback)
        return self.language

    @property
    def metadata(self):
        return self.catalogues[self.language]

    def missing(self, language):
        return set(self.catalogues[self.fallback]['messages']) - set(self.catalogues[language]['messages'])

    def text(self, key, **values):
        template = self.metadata['messages'].get(key, self.catalogues[self.fallback]['messages'].get(key))
        if template is None:
            raise KeyError(f'Unknown translation key: {key}')
        return template.format_map(values)


@lru_cache(maxsize=1024)
def visual_text(text, direction='ltr'):
    if direction == 'ltr':
        return text
    if direction != 'rtl':
        raise ValueError('Direction must be ltr or rtl')
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError as error:
        raise RuntimeError('Arabic requires: pip install "platform2d[i18n]"') from error
    # Shape logical Arabic before the Unicode bidirectional algorithm. Do not
    # reverse strings by hand: numbers and Latin key names must retain their order.
    return get_display(arabic_reshaper.reshape(text), base_dir='R')


class TextRenderer:
    MAX_RENDER_CACHE_BYTES = 8 * 1024 * 1024

    def __init__(self, translator, font_folder):
        self.translator = translator
        self.folder = Path(font_folder)
        self.cache = {}
        self._render_cache = OrderedDict()
        self._render_cache_bytes = 0

    def font(self, size):
        import pygame
        path = self.folder / self.translator.metadata['font']
        key = (str(path), size)
        if key not in self.cache:
            self.cache[key] = pygame.font.Font(str(path), size)
        return self.cache[key]

    def render(self, text, color, size=24, max_width=None):
        metadata = self.translator.metadata
        key = (metadata['font'], metadata['direction'], text, tuple(color), size, max_width)
        cached = self._render_cache.get(key)
        if cached is not None:
            self._render_cache.move_to_end(key)
            return cached
        text = visual_text(text, metadata['direction'])
        # Fit complete messages without cutting translations or stretching glyphs.
        while True:
            font = self.font(size)
            if max_width is None or font.size(text)[0] <= max_width:
                image = font.render(text, True, color)
                image_bytes = image.get_width() * image.get_height() * image.get_bytesize()
                if image_bytes <= self.MAX_RENDER_CACHE_BYTES:
                    while self._render_cache and self._render_cache_bytes + image_bytes > self.MAX_RENDER_CACHE_BYTES:
                        _, old = self._render_cache.popitem(last=False)
                        self._render_cache_bytes -= old.get_width() * old.get_height() * old.get_bytesize()
                    self._render_cache[key] = image
                    self._render_cache_bytes += image_bytes
                return image
            if size <= 12:
                raise ValueError('Translated text does not fit; wrap it or enlarge its area')
            size -= 1

    def draw(self, surface, text, y, color=(226,238,244), size=24, margin=28):
        image = self.render(text, color, size, surface.get_width()-2*margin)
        x = surface.get_width()-margin-image.get_width() if self.translator.metadata['direction']=='rtl' else margin
        surface.blit(image, (x,y))
        return image.get_rect(topleft=(x,y))


LANGUAGES=('pt-PT','en','es','fr','de','zh-Hans','ar','ja')
FONT_FOLDER=Path(__file__).parent/'fonts'


class InterfaceText:
    """Packaged common UI translations; each host owns its selected language."""
    def __init__(self,language='pt-PT'):
        self.translator=Translator(Path(__file__).parent/'locales',language)
        self.renderer=TextRenderer(self.translator,FONT_FOLDER)

    @property
    def language(self): return self.translator.language

    @property
    def rtl(self): return self.translator.metadata['direction']=='rtl'

    def t(self,key,**values): return self.translator.text(key,**values)

    def legacy_error(self,error):
        # Preserve the existing settings API while localizing its validation errors.
        source=self.translator.catalogues['pt-PT']['messages']
        key=next((key for key,value in source.items() if key.startswith('error.') and value==str(error)),None)
        return self.t(key or 'io_error')

    def render(self,text,size=16,color=(216,233,240),width=None):
        return self.renderer.render(text,color,size,width)

    def box(self,surface,text,rect,size=16,color=(216,233,240)):
        import pygame
        rect=pygame.Rect(rect)
        image=self.render(text,size,color,rect.width)
        x=rect.right-image.get_width() if self.rtl else rect.x
        surface.blit(image,(x,rect.y))
        return image.get_rect(topleft=(x,rect.y))
