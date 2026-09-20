"""Map schema for the four optional exploration modes."""
from math import isfinite

MODES={'cargo','swim','escape','explore'}
OBJECT_MODES={'crate':{'cargo'},'plate':{'cargo'},'gate':{'cargo','explore'},
              'water':{'swim'},'air':{'swim'},'ability':{'explore'}}
SIZES={'crate':(48,48),'plate':(64,6),'gate':(32,160),'water':(256,192),'air':(80,64),'ability':(32,32)}


def validate_expansion(data):
    mode=data.get('properties',{}).get('traversal','walk')
    if mode in MODES:
        if data.get('properties',{}).get('scroll','both')=='none':
            raise ValueError('Estes modos usam uma câmara com scroll.')
        if mode=='escape' and data.get('properties',{}).get('scroll')!='horizontal':
            raise ValueError('Fuga: escolhe scroll horizontal.')
    for o in data.get('objects',[]):
        if not isinstance(o,dict): continue
        kind=o.get('type')
        if kind in OBJECT_MODES and mode not in OBJECT_MODES[kind]:
            raise ValueError(f'{kind}: objeto incompatível com o modo {mode}.')
        if kind=='plate' and (type(o.get('weight',2)) is not int or not 1<=o.get('weight',2)<=8):
            raise ValueError('Placa: peso mínimo inteiro entre 1 e 8.')
        if kind=='water':
            current=o.get('current',0)
            if type(current) not in (int,float) or not isfinite(current) or abs(current)>80:
                raise ValueError('Água: corrente entre -80 e 80 unidades/s.')
        if kind=='crate' and (o.get('w',48)!=48 or o.get('h',48)!=48):
            raise ValueError('Caixa: tamanho de 48×48 unidades.')
