"""Compile the reviewed translation tables into runtime UTF-8 JSON catalogues."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LANGUAGES=('pt-PT','en','es','fr','de','zh-Hans','ar','ja')


def main():
    for domain,output in [('common',ROOT/'platform2d/locales'),('resgate',ROOT/'games/resgate/resgate/locales'),('campaign',ROOT/'examples/campaign/locales'),('editor',ROOT/'platform2d/tools/locales')]:
        messages={code:{} for code in LANGUAGES}
        for number,line in enumerate((ROOT/'translations'/f'{domain}.tsv').read_text(encoding='utf-8').splitlines(),1):
            if not line or line.startswith('#'): continue
            key,*values=line.split('\t')
            if len(values)!=8: raise ValueError(f'{domain}:{number}: expected eight translations')
            for code,value in zip(LANGUAGES,values):
                if key in messages[code] or not value: raise ValueError(f'{domain}:{number}: duplicate or empty message')
                messages[code][key]=value
        output.mkdir(parents=True,exist_ok=True)
        for code in LANGUAGES:
            meta=json.loads((ROOT/'tutorials/first_game/locales'/f'{code}.json').read_text(encoding='utf-8'))
            meta['messages']=messages[code]
            (output/f'{code}.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'{domain}: {len(messages["en"])} messages x 8 languages')


if __name__=='__main__': main()
