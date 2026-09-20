"""Author the four demonstration maps. Only replaces expansion assets."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'examples/campaign/assets'


def level(name,mode,w=50,h=18,scroll='horizontal',theme='station'):
    return dict(version=1,name=name,editor_profile='adventure',tile_size=32,
                properties=dict(traversal=mode,scroll=scroll,theme=theme,weapon_enabled=False),
                tiles=['.'*w for _ in range(h-2)]+['#'*w]*2,objects=[])


def tile(d,x,y,w=1,h=1,kind='#'):
    for row in range(y,y+h):
        s=d['tiles'][row]; d['tiles'][row]=s[:x]+kind*w+s[x+w:]


def obj(d,kind,id,x,y,w,h,**extra): d['objects'].append(dict(type=kind,id=id,x=x,y=y,w=w,h=h,**extra))


def main():
    cargo=level('Fábrica de Carga','cargo',theme='reactor')
    obj(cargo,'spawn','spawn',64,482,24,30)
    for id,x in [('a',192),('b',560)]: obj(cargo,'crate','crate-'+id,x,464,48,48)
    for id,x in [('a',320),('b',704)]: obj(cargo,'plate','plate-'+id,x,506,64,6,weight=2)
    tile(cargo,10,13,3,kind='=')
    obj(cargo,'coin','upper-crystal',352,382,24,26)
    obj(cargo,'gate','cargo-gate',1024,96,32,416)
    obj(cargo,'coin','exit-crystal',1280,482,24,26)
    obj(cargo,'goal','exit',1504,454,32,58)

    swim=level('Torre Inundada','swim',30,36,'vertical','ice')
    obj(swim,'spawn','spawn',96,1058,24,30)
    obj(swim,'water','reservoir',0,288,960,800,current=18)
    tile(swim,0,27,21); tile(swim,10,20,20)
    for id,x,y in [('start',64,992),('east',752,880),('west',96,672),('top',752,352)]:
        obj(swim,'air','air-'+id,x,y,112,96)
    obj(swim,'coin','deep-crystal',784,928,24,26)
    obj(swim,'coin','middle-crystal',128,720,24,26)
    obj(swim,'goal','exit',816,352,32,58)

    escape=level('Fuga da Estação','escape',80,theme='reactor')
    obj(escape,'spawn','spawn',128,482,24,30)
    for x in (16,30,43,58): tile(escape,x,14,1,2)
    for x in (24,52): tile(escape,x,16,3,2,kind='.')
    for id,x in [('mid',1088),('last',1984)]: obj(escape,'checkpoint',id,x,482,24,30)
    obj(escape,'goal','exit',2464,454,32,58)

    explore=level('Laboratório Esquecido','explore',60,theme='garden')
    obj(explore,'spawn','spawn',384,482,24,30)
    obj(explore,'gate','atrium-seal',288,96,32,416)
    tile(explore,3,12,5,kind='=')
    obj(explore,'goal','atrium-exit',128,326,32,58)
    for x in (24,38): tile(explore,x,15,2,1)
    obj(explore,'coin','lab-crystal',1520,482,24,26)
    obj(explore,'ability','double-jump',1744,480,32,32)
    obj(explore,'checkpoint','lab',1664,482,24,30)

    stages=[]
    for mode,d in [('cargo',cargo),('swim',swim),('escape',escape),('explore',explore)]:
        path=ROOT/f'expansion-{mode}.json'; path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        stage=dict(id=mode,map=path.name); stages.append(stage)
        (ROOT/f'{mode}.json').write_text(json.dumps(dict(format='platform2d.campaign',version=1,name=d['name'],stages=[stage]),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    original=json.loads((ROOT/'odyssey-duel.json').read_text(encoding='utf-8'))
    for filename,name,items in [('expansion.json','Novos Horizontes',stages),('odyssey-horizons.json','Odisseia Aurora — Novos Horizontes',original['stages']+stages)]:
        (ROOT/filename).write_text(json.dumps(dict(format='platform2d.campaign',version=1,name=name,stages=items),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()
