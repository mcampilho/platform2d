"""Translations owned by the campaign example, separate from game data."""
from pathlib import Path

from platform2d.i18n import FONT_FOLDER, TextRenderer, Translator


class CampaignLocale:
    def __init__(self, language='pt-PT'):
        self.translator=Translator(Path(__file__).parent/'locales',language)
        self.renderer=TextRenderer(self.translator,FONT_FOLDER)

    @property
    def language(self): return self.translator.language

    @property
    def rtl(self): return self.translator.metadata['direction']=='rtl'

    def t(self,key,**values): return self.translator.text(key,**values)

    def literal(self,text):
        """Translate built-in map names and fixed legacy notices; leave user text intact."""
        source=self.translator.catalogues['pt-PT']['messages']
        key=next((key for key,value in source.items() if key.startswith(('map.','literal.')) and value==text),None)
        return self.t(key) if key else text

    def draw(self,surface,message,rect,size=18,color=(223,239,236),align=None):
        import pygame
        rect=pygame.Rect(rect)
        image=self.renderer.render(message,color,size,rect.width)
        align=align or ('right' if self.rtl else 'left')
        x=rect.right-image.get_width() if align=='right' else rect.centerx-image.get_width()//2 if align=='center' else rect.x
        surface.blit(image,(x,rect.y))
        return image.get_rect(topleft=(x,rect.y))
