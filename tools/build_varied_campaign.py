"""Rebuild only the four bundled Expedition maps and their manifest."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'examples/campaign/assets'


def base(name,theme,armed):
    return dict(version=1,name=name,editor_profile='ranged',tile_size=32,
                properties=dict(theme=theme,weapon_enabled=armed),
                tiles=['.'*30 for _ in range(16)]+['#'*30]*2,
                objects=[dict(id='start',type='spawn',x=64,y=482),
                         dict(id='exit',type='goal',x=910,y=454,w=32,h=58)])


def tiles(data,row,start,end,char):
    cells=list(data['tiles'][row]); cells[start:end]=[char]*(end-start)
    data['tiles'][row]=''.join(cells)


def add(data,ident,kind,x,y,**props):
    data['objects'].append(dict(id=ident,type=kind,x=x,y=y,**props))


def definitions():
    a=base('Bastião de Entrada','station',True)
    tiles(a,15,10,11,'#'); tiles(a,14,20,21,'#'); tiles(a,15,20,21,'#')
    add(a,'power','pickup',140,482,item='power',quantity=1)
    add(a,'guard-a','target',210,482,hp=2)
    add(a,'guard-b','turret',450,482,hp=3,interval=1.4,projectile_speed=220,range=380)
    add(a,'guard-c','target',810,482,hp=3)
    add(a,'checkpoint','checkpoint',535,482)
    add(a,'kit','pickup',560,482,item='medkit',quantity=1)

    b=base('Jardins Suspensos','garden',False)
    for row,start,end in [(14,5,10),(12,11,16),(10,17,22),(12,24,28)]: tiles(b,row,start,end,'=')
    for i,(x,y) in enumerate([(220,422),(425,358),(610,294),(820,358)]):
        add(b,f'crystal-{i}','coin',x,y,w=24,h=26)
    add(b,'checkpoint','checkpoint',280,418)
    add(b,'cadence','pickup',860,354,item='rapid',quantity=1)

    c=base('Conduta Glacial','ice',False)
    for i,x in enumerate([288,640]): add(c,f'cold-{i}','hazard',x,496,w=64,h=16)
    for i,(x,y) in enumerate([(320,410),(490,482),(672,410)]):
        add(c,f'crystal-{i}','coin',x,y,w=24,h=26)
    add(c,'checkpoint','checkpoint',480,482)
    add(c,'kit','pickup',790,482,item='medkit',quantity=1)

    d=base('Laboratório do Reator','reactor',True)
    tiles(d,14,5,10,'='); tiles(d,14,16,20,'='); tiles(d,12,22,27,'=')
    add(d,'guard-a','target',390,482,hp=4)
    add(d,'guard-b','turret',820,482,hp=4,interval=1.3,projectile_speed=230,range=450)
    for i,(x,y) in enumerate([(230,422),(560,422),(780,358)]):
        add(d,f'crystal-{i}','coin',x,y,w=24,h=26)
    add(d,'checkpoint','checkpoint',470,482)
    add(d,'power','pickup',735,354,item='power',quantity=1)
    return [a,b,c,d]


def main():
    stages=[]
    for index,data in enumerate(definitions(),1):
        filename=f'expedition-{index}.json'
        (ROOT/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        stages.append(dict(id=f'expedition-{index}',map=filename))
    manifest=dict(format='platform2d.campaign',version=1,name='Expedição Aurora',stages=stages)
    (ROOT/'expedition.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()
