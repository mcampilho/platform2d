"""Campaign-specific checkpoint contract. No live state changes during validation."""
from copy import deepcopy
from platform2d.gameplay.progress import fields,finite,string_list,fingerprint
from platform2d.gameplay.inventory import CATALOG,Inventory,upgraded_weapon
from .factory import create_scene
from platform2d.gameplay.rocket import RocketMission
from platform2d.gameplay.mission import objectives_complete

FORMAT = 'platform2d.campaign.progress'


def identity(campaign):
    return fingerprint(dict(ids=campaign.progress.stages,maps=[d.data for d in campaign.documents],
                            movement=campaign.settings['movement'],rules='combat-checkpoint-v1',
                            catalog=[(i.id,i.limit) for i in CATALOG.values()]))


def stats(data):
    fields(data,{'shots','deaths','elapsed'},'estatísticas')
    if any(type(data[k]) is not int or not 0 <= data[k] <= 10**12 for k in ('shots','deaths')) or not finite(data['elapsed']) or data['elapsed']>10**12:
        raise ValueError('Estatísticas inválidas.')


def capture(campaign):
    s=campaign.active
    payload = dict(format=FORMAT,version=1,identity=identity(campaign),index=campaign.progress.index,
                totals=deepcopy(campaign.totals),inventory=s.inventory.snapshot(),
                stage=dict(checkpoint=s.active_checkpoint,destroyed=sorted(s.destroyed),
                           collected=sorted(s.collected_items),won=s.won,
                           stats={k:getattr(s,k) for k in ('shots','deaths','elapsed')}))
    if getattr(s,'rocket',None) is not None:
        payload['stage']['rocket']=s.rocket.snapshot()
    if getattr(s,'mode',None)=='cargo': payload['stage']['cargo']=s.cargo.snapshot()
    return payload


def validate(data,campaign):
    fields(data,{'format','version','identity','index','totals','inventory','stage'},'campanha')
    if data['format']!=FORMAT or type(data['version']) is not int or data['version']!=1:
        raise ValueError('Formato de gravação de campanha incompatível.')
    if data['identity']!=identity(campaign):
        raise ValueError('Gravação incompatível: campanha ou regras alteradas.')
    index=data['index']
    if type(index) is not int or not 0<=index<len(campaign.documents):
        raise ValueError('Nível gravado inválido.')
    inv=data['inventory']
    if not isinstance(inv,dict) or not inv.keys()<=CATALOG.keys():
        raise ValueError('Inventário inválido.')
    for key,value in inv.items():
        if type(value) is not int or not 1<=value<=CATALOG[key].limit:
            raise ValueError('Quantidade de inventário inválida.')
    stats(data['totals'])
    state=data['stage']
    jetpack=campaign.documents[index].profile=='adventure' and campaign.documents[index].data.get('properties',{}).get('traversal')=='jetpack'
    mode=campaign.documents[index].data.get('properties',{}).get('traversal')
    fields(state,{'checkpoint','destroyed','collected','won','stats'} | ({'rocket'} if jetpack else set()) | ({'cargo'} if mode=='cargo' else set()),'nível')
    stats(state['stats'])
    objects=campaign.documents[index].data['objects']
    for key,types in [('destroyed',{'target','turret','guardian'}),('collected',{'pickup','coin','ability'})]:
        allowed={o['id'] for o in objects if o['type'] in types}
        if not string_list(state[key]) or not set(state[key])<=allowed:
            raise ValueError('Objetos de progresso inválidos.')
    if jetpack:
        rocket=RocketMission(objects); rocket.restore(state['rocket'])
        if state['won'] and not rocket.ready: raise ValueError('Vitória sem foguetão abastecido.')
    if mode=='cargo':
        from platform2d.gameplay.cargo import Cargo
        level=campaign.documents[index].playable(); cargo=Cargo(objects)
        cargo.restore(state['cargo'],level.colliders,level.width,level.height)
        if state['won'] and len(cargo.active())!=len(cargo.plates): raise ValueError('Vitória sem placas de carga ativas.')
    if mode=='explore' and state['won'] and not any(o['type']=='ability' and o['id'] in state['collected'] for o in objects):
        raise ValueError('Vitória sem a capacidade de exploração.')
    checkpoints={o['id'] for o in objects if o['type']=='checkpoint'}
    if state['checkpoint'] is not None and (not isinstance(state['checkpoint'],str) or state['checkpoint'] not in checkpoints):
        raise ValueError('Checkpoint inválido.')
    if type(state['won']) is not bool or (state['won'] and not objectives_complete(objects,set(state['destroyed']),set(state['collected']))):
        raise ValueError('Vitória inválida.')
    if state['won'] and any(data['totals'][k]<state['stats'][k] for k in data['totals']):
        raise ValueError('Totais incompatíveis com o nível concluído.')
    if index==0 and data['totals']!=(state['stats'] if state['won'] else dict(shots=0,deaths=0,elapsed=0)):
        raise ValueError('Totais inválidos no primeiro nível.')
    return deepcopy(data)


def restore(data,campaign):
    data=validate(data,campaign)
    state=data['stage']
    # Build a complete candidate before replacing live gameplay.
    candidate=create_scene(campaign.documents[data['index']],campaign.settings)
    candidate.inventory=Inventory()
    for item,quantity in data['inventory'].items(): candidate.inventory.add(item,quantity)
    candidate.weapon.spec=upgraded_weapon(candidate.spec,candidate.inventory)
    candidate.destroyed=set(state['destroyed']); candidate.collected_items=set(state['collected'])
    candidate.active_checkpoint=state['checkpoint']
    if state['checkpoint'] is not None:
        cp=next(o for o in candidate.level.objects if o['id']==state['checkpoint'])
        candidate.respawn_point=(cp['x'],cp['y'])
    candidate.respawn()
    if 'cargo' in state:
        candidate.cargo.restore(state['cargo'],candidate.static_colliders,candidate.level.width,candidate.level.height)
        b=candidate.player.body
        if any(b.box.overlaps(c.box) for c in candidate.cargo.crates.values()):
            from platform2d.physics.body import Box
            # A crate may have been pushed onto the checkpoint. Find a nearby
            # supported free position before installing the candidate scene.
            blockers=[*candidate.static_colliders,*candidate.cargo.colliders()]
            for x in sorted(range(0,candidate.level.width-int(b.w)+1,8),key=lambda x:abs(x-b.x)):
                r=Box(x,b.y,b.w,b.h)
                if not any(r.overlaps(c.box) for c in blockers if not c.one_way) and any(abs(r.bottom-c.box.y)<1 and r.x<c.box.right and r.right>c.box.x for c in blockers):
                    b.teleport(x,b.y); break
            else: raise ValueError('Checkpoint sem espaço livre junto às caixas gravadas.')
        candidate.update_camera(0,True)
    candidate.won=state['won']
    if 'rocket' in state:
        candidate.rocket.restore(state['rocket'])
        candidate.launch_time=2.5 if state['won'] else None
        candidate.hide_player=state['won']
    for key,value in state['stats'].items(): setattr(candidate,key,value)
    candidate.audio=campaign.audio; candidate.format_controls=campaign.format_controls
    campaign.active=candidate
    campaign.progress.index=data['index']
    campaign.progress.completed=list(campaign.progress.stages[:data['index']+int(state['won'])])
    campaign.totals=data['totals']
