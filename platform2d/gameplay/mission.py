"""Small map-driven objective contract shared by play, editor and saves."""
THEMES = {
    'station': ((12,23,37),(20,36,51),(43,64,79),(25,43,59)),
    'garden': ((13,32,29),(24,49,40),(61,92,66),(36,63,47)),
    'ice': ((15,28,46),(28,49,69),(83,120,144),(46,77,104)),
    'reactor': ((32,19,36),(52,30,52),(96,64,88),(62,37,60)),
    'observatory': ((10,26,34),(20,45,49),(83,116,91),(40,69,62)),
}


def validate_mission(properties,objects):
    theme=properties.get('theme','station')
    if not isinstance(theme,str) or theme not in THEMES:
        raise ValueError('Tema desconhecido: station, garden, ice, reactor ou observatory.')
    armed=properties.get('weapon_enabled',True)
    if type(armed) is not bool:
        raise ValueError('weapon_enabled deve ser true ou false.')
    if not armed and any(o.get('type') in {'target','turret'} for o in objects if isinstance(o,dict)):
        raise ValueError('Uma sala com alvos precisa de permitir disparos.')


def objectives_complete(objects,destroyed,collected):
    return all(o['id'] in destroyed for o in objects if o['type'] in {'target','turret','guardian'}) and all(
        o['id'] in collected for o in objects if o['type']=='coin')


def validate_adventure(data):
    from .expansion_config import validate_expansion
    validate_expansion(data)
    props=data.get('properties',{})
    mode=props.get('traversal','walk'); scroll=props.get('scroll','both')
    if mode not in ('walk','jetpack','ledge','duel','cargo','swim','escape','explore','willy') or scroll not in ('none','horizontal','vertical','both'):
        raise ValueError('Aventura: movimento ou scroll desconhecido.')
    size=data.get('tile_size',32)
    width=len(data['tiles'][0])*size; height=len(data['tiles'])*size
    willy_size=mode=='willy' and (width,height)==(1024,512)
    if not willy_size and not (960<=width<=3840 and 576<=height<=2048):
        raise ValueError('Aventura: dimensões entre 960×576 e 3840×2048.')
    if scroll=='none' and (width,height)!=(960,576):
        raise ValueError('Sem scroll, usa 960×576.')
    if not willy_size and ((scroll=='horizontal' and height!=576) or (scroll=='vertical' and width!=960)):
        raise ValueError('Scroll horizontal: altura 576. Scroll vertical: largura 960. Usa dois eixos para ampliar ambos.')
    objects=data.get('objects',[])
    rocket=[o for o in objects if isinstance(o,dict) and o.get('type')=='rocket']
    cargo=[o for o in objects if isinstance(o,dict) and o.get('type') in {'part','fuel'}]
    if mode=='jetpack':
        if scroll!='none': raise ValueError('A oficina do foguetão usa ecrã fixo, sem scroll.')
        if any(isinstance(o,dict) and o.get('type') in {'spawn','checkpoint','part','fuel','rocket','coin'} and
               isinstance(o.get('y'),(int,float)) and o['y']<264 for o in objects):
            raise ValueError('Na oficina, coloca os objetos jogáveis abaixo do painel: Y mínimo 264.')
        if len(rocket)!=1 or not any(o['type']=='part' for o in cargo) or not any(o['type']=='fuel' for o in cargo):
            raise ValueError('Jetpack: define um foguetão, pelo menos uma peça e um combustível.')
        if sum(o['type']=='part' for o in cargo)>3 or sum(o['type']=='fuel' for o in cargo)>9:
            raise ValueError('Foguetão: máximo de três peças e nove depósitos de combustível.')
    elif rocket or cargo:
        raise ValueError('Peças, combustível e foguetão pertencem ao modo jetpack.')

    guards=[o for o in objects if isinstance(o,dict) and o.get('type')=='guardian']
    if guards and mode!='duel': raise ValueError('O guardião exige o modo Duelo.')
    if mode=='duel':
        if scroll=='none': raise ValueError('Duelo: escolhe uma câmara horizontal, vertical ou de dois eixos.')
        if props.get('weapon_enabled',True): raise ValueError('Duelo: desativa os disparos; usa a espada.')
        if any(o.get('type') in {'turret','target'} for o in objects if isinstance(o,dict)):
            raise ValueError('Duelo: substitui os alvos de tiro por guardiões.')
    for guard in guards:
        if type(guard.get('hp',3)) is not int or not 1<=guard.get('hp',3)<=20:
            raise ValueError('Guardião: vida inteira entre 1 e 20.')
        if guard.get('w',24)!=24 or guard.get('h',30)!=30:
            raise ValueError('Guardião: corpo de 24×30 unidades.')
