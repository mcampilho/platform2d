"""Text resources for the map and campaign editors."""
from pathlib import Path
import re

from platform2d.i18n import FONT_FOLDER, TextRenderer, Translator


class EditorLocale:
    def __init__(self,language='pt-PT'):
        self.translator=Translator(Path(__file__).parent/'locales',language)
        self.renderer=TextRenderer(self.translator,FONT_FOLDER)
        self.source={value:key for key,value in self.translator.catalogues['pt-PT']['messages'].items() if key.startswith('literal.')}
        self.prefixes=sorted(((value,key) for key,value in self.translator.catalogues['pt-PT']['messages'].items() if key.startswith('prefix.')),reverse=True)
        self.suffixes=sorted(((value,key) for key,value in self.translator.catalogues['pt-PT']['messages'].items() if key.startswith('suffix.')),reverse=True)

    def t(self,key,**values): return self.translator.text(key,**values)

    def literal(self,text):
        text=str(text)
        match=re.fullmatch(r'Solução confirmada: (\d+) cristais e saída na mesma rota, ([\d.]+)s, sem mortes\.(?: Usa R (\d+) vez\(es\) para voltar ao ponto de reaparecimento\.)?',text)
        if match:
            result=self.t('validation.classic_solved',crystals=match[1],seconds=match[2])
            return result+(self.t('validation.classic_reset',count=match[3]) if match[3] else '')
        match=re.fullmatch(r'Rota confirmada nas regras do jogo: ([\d.]+)s, todos os objetivos, sem mortes\. Usa Ver solução para acompanhar o percurso\.',text)
        if match: return self.t('validation.adventure_solved',seconds=match[1])
        key=self.source.get(text)
        if key: return self.t(key)
        for source,key in self.prefixes:
            if text.startswith(source): return self.t(key)+self.literal(text[len(source):])
        for source,key in self.suffixes:
            if text.endswith(source): return self.literal(text[:-len(source)])+self.t(key)
        for prefix in ('ERRO · ','AVISO · '):
            if text.startswith(prefix):
                return self.t('literal.error' if prefix.startswith('ERRO') else 'literal.warning')+' · '+self.literal(text[len(prefix):])
        if ': ' in text:
            prefix,detail=text.split(': ',1)
            prefix_key=self.source.get(prefix)
            if prefix_key: return self.t(prefix_key)+': '+self.literal(detail)
            detail_key=self.source.get(detail)
            if detail_key: return prefix+': '+self.t(detail_key)
        extra=getattr(self,'extra',None)
        return extra(text) if extra else text
