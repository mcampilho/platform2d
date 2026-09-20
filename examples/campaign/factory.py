from examples.ranged.scene import RangedScene
from .adventure import AdventureScene
from .duel import DuelScene
from .expansion import ExpansionScene,MODES


def create_scene(document,settings):
    cls=AdventureScene if document.profile=='adventure' else RangedScene
    if document.profile=='adventure' and document.data.get('properties',{}).get('traversal')=='duel': cls=DuelScene
    if document.profile=='adventure' and document.data.get('properties',{}).get('traversal') in MODES: cls=ExpansionScene
    return cls(document.playable(),settings)
