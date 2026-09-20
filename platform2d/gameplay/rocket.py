"""One carried object at a time; assemble before delivering fuel."""
from .progress import fields,string_list


class RocketMission:
    def __init__(self,objects):
        self.part_order=tuple(o['id'] for o in objects if o['type']=='part')
        self.parts=set(self.part_order)
        self.fuel={o['id'] for o in objects if o['type']=='fuel'}
        self.delivered=set(); self.fuelled=set(); self.carrying=None

    @property
    def assembled(self): return self.delivered==self.parts

    @property
    def ready(self): return self.assembled and self.fuelled==self.fuel

    @property
    def next_part(self):
        return next((ident for ident in self.part_order if ident not in self.delivered),None)

    @property
    def fuel_fraction(self):
        return len(self.fuelled)/len(self.fuel) if self.fuel else 0

    def part_name(self,ident):
        index=self.part_order.index(ident)
        return {1:('Foguetão',),2:('Motor','Cockpit'),3:('Motor','Depósito','Cockpit')}.get(len(self.part_order),tuple(f'Peça {i+1}' for i in range(len(self.part_order))))[index]

    def take(self,ident):
        if self.carrying is not None: return False
        if (ident==self.next_part and ident is not None) or (self.assembled and ident in self.fuel-self.fuelled):
            self.carrying=ident; return True
        return False

    def deliver(self):
        if self.carrying is None: return False
        if self.carrying in self.parts and self.carrying!=self.next_part: return False
        (self.delivered if self.carrying in self.parts else self.fuelled).add(self.carrying)
        self.carrying=None; return True

    def snapshot(self):
        return dict(delivered=sorted(self.delivered),fuelled=sorted(self.fuelled),carrying=self.carrying)

    def restore(self,state):
        fields(state,{'delivered','fuelled','carrying'},'foguetão')
        if not string_list(state['delivered']) or not set(state['delivered'])<=self.parts:
            raise ValueError('Peças de foguetão inválidas.')
        if not string_list(state['fuelled']) or not set(state['fuelled'])<=self.fuel:
            raise ValueError('Combustível inválido.')
        delivered,fuelled=set(state['delivered']),set(state['fuelled'])
        carry=state['carrying']
        if carry is not None and (not isinstance(carry,str) or carry not in (self.parts|self.fuel)-delivered-fuelled):
            raise ValueError('Carga inválida.')
        if (fuelled or carry in self.fuel) and delivered!=self.parts:
            raise ValueError('É necessário montar o foguetão antes de abastecer.')
        next_part=next((ident for ident in self.part_order if ident not in delivered),None)
        if carry in self.parts and carry!=next_part: carry=None
        self.delivered,self.fuelled,self.carrying=delivered,fuelled,carry
