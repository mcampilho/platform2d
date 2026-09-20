"""The same combat rules, with optional collectible upgrades."""
from .level import definition as combat_definition


def definition():
    data = combat_definition()
    data['name'] = 'Arsenal de Campo'
    for ident,item,x in [('power-a','power',144),('rapid-a','rapid',275),
                         ('medical-a','medkit',520),('power-b','power',780)]:
        data['objects'].append(dict(id=ident,type='pickup',item=item,quantity=1,x=x,y=482,w=24,h=30))
    return data
