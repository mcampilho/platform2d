"""Build new Odyssey maps; existing Expedition rooms remain untouched."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'examples/campaign/assets'


def base(name,width,height,mode,scroll,theme='station'):
    return dict(version=1,name=name,editor_profile='adventure',tile_size=32,
                properties=dict(traversal=mode,scroll=scroll,theme=theme,weapon_enabled=False),
                tiles=['.'*width for _ in range(height-2)]+['#'*width]*2,objects=[])


def tile(data,row,start,end,kind='#'):
    cells=list(data['tiles'][row]); cells[start:end]=[kind]*(end-start); data['tiles'][row]=''.join(cells)


def obj(data,ident,kind,x,y,**props):
    data['objects'].append(dict(id=ident,type=kind,x=x,y=y,**props))


def definitions():
    launch=base('Oficina Orbital',30,18,'jetpack','none')
    obj(launch,'start','spawn',64,482)
    obj(launch,'rocket','rocket',456,424,w=48,h=88)
    for row,start,end in [(12,3,9),(10,11,15),(11,21,28)]: tile(launch,row,start,end,'=')
    for i,(x,y) in enumerate([(160,360),(370,296),(790,328)]): obj(launch,f'part-{i}','part',x,y,w=24,h=24)
    for i,(x,y) in enumerate([(260,488),(660,488),(850,328)]): obj(launch,f'fuel-{i}','fuel',x,y,w=20,h=24)

    valley=base('Vale das Três Luas',75,18,'walk','horizontal','garden')
    obj(valley,'start','spawn',64,482)
    obj(valley,'exit','goal',2300,454,w=32,h=58)
    for i,x in enumerate([330,850,1450,2020]): obj(valley,f'crystal-{i}','coin',x,482,w=24,h=26)
    for i,x in enumerate([540,1120,1720]): obj(valley,f'pit-{i}','hazard',x,496,w=64,h=16)
    for i,x in enumerate([760,1520]): obj(valley,f'checkpoint-{i}','checkpoint',x,482)
    for row,start,end in [(13,9,14),(11,24,31),(12,40,47),(10,59,64)]: tile(valley,row,start,end,'=')

    palace=base('Palácio das Falésias',30,36,'ledge','vertical','reactor')
    obj(palace,'start','spawn',64,1058)
    # Each 96-unit rise is just beyond an ordinary jump; hands can reach the lip.
    for i in range(8):
        column=5+i*3; row=31-i*3
        tile(palace,row,column,column+3)
        obj(palace,f'crystal-{i}','coin',column*32+40,row*32-26,w=24,h=26)
        if i in (2,5): obj(palace,f'checkpoint-{i}','checkpoint',column*32+8,row*32-30)
    obj(palace,'exit','goal',858,262,w=32,h=58)
    return launch,valley,palace


def main():
    files=['odyssey-launch.json','odyssey-valley.json','odyssey-palace.json']
    for filename,data in zip(files,definitions()):
        (ROOT/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stages=[dict(id='launch',map=files[0])]+[dict(id=f'expedition-{i}',map=f'expedition-{i}.json') for i in range(1,5)]+[
        dict(id='valley',map=files[1]),dict(id='palace',map=files[2])]
    (ROOT/'odyssey.json').write_text(json.dumps(dict(format='platform2d.campaign',version=1,name='Odisseia Aurora',stages=stages),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()
