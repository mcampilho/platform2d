"""Game adapters stay outside the reusable editor package."""
import json
from pathlib import Path

from examples.classic.scene import ClassicScene
from examples.precision.scene import PrecisionScene
from examples.rooms.scene import RoomsScene
from examples.ranged.scene import RangedScene
from examples.campaign.adventure import AdventureScene
from examples.campaign.duel import DuelScene
from examples.campaign.expansion import ExpansionScene,MODES
from platform2d.actors.controller import Movement
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.world_editor import WorldDocument

ROOT = Path(__file__).parents[1]


def editor_profiles():
    profiles = {}
    for name,scene in (("classic",ClassicScene),("precision",PrecisionScene),("rooms",RoomsScene),("ranged",RangedScene)):
        settings = json.loads((ROOT/name/"settings.json").read_text(encoding="utf-8"))
        profiles[name] = dict(factory=lambda data,scene=scene,settings=settings:scene(data,settings),
                              bindings=settings["bindings"],movement=Movement(**settings["movement"]),
                              size=(960,540) if name == "classic" else (960,576))
    settings = json.loads((ROOT/"ranged/settings.json").read_text(encoding="utf-8"))
    settings["bindings"]["interact"]=["e"]
    settings["bindings"].update(attack=["j"],guard=["l"],up=["up","w"])
    profiles["adventure"]=dict(factory=lambda data:(ExpansionScene if data.properties.get("traversal") in MODES else DuelScene if data.properties.get("traversal")=="duel" else AdventureScene)(data,settings),bindings=settings["bindings"],movement=Movement(**settings["movement"]),size=(960,576))
    from examples.campaign.scene import CampaignScene
    campaign_settings=json.loads((ROOT/'ranged/settings.json').read_text(encoding='utf-8'))
    campaign_settings['bindings'].update(interact=['e'],attack=['j'],guard=['l'],up=['up','w'],**{'continue':['return']})
    profiles['campaign']=dict(factory=lambda name,ids,docs:CampaignScene(name,ids,docs,campaign_settings),bindings=campaign_settings['bindings'])
    return profiles


def template_document(profile):
    if profile in MODES:
        return MapDocument(json.loads((ROOT/f"campaign/assets/expansion-{profile}.json").read_text(encoding="utf-8")))
    if profile == "duel":
        return MapDocument(json.loads((ROOT/"campaign/assets/duel-courtyard.json").read_text(encoding="utf-8")))
    if profile == "adventure":
        return MapDocument(json.loads((ROOT/"campaign/assets/odyssey-launch.json").read_text(encoding="utf-8")))
    if profile == "inventory":
        from examples.ranged.inventory_level import definition
        return MapDocument(definition())
    if profile == "ranged":
        from examples.ranged.level import definition
        return MapDocument(definition())
    if profile == "slopes":
        from examples.slopes.level import definition
        return MapDocument(definition())
    if profile == "mechanisms":
        from examples.mechanisms.world import definition
        return WorldDocument(definition())
    paths = {"classic":ROOT/"editor/assets/workshop.json", "precision":ROOT/"precision/assets/ascent.json",
             "rooms":ROOT/"rooms/assets/world.json"}
    data = json.loads(paths[profile].read_text(encoding="utf-8"))
    # Templates are unsaved copies. Opening via --map deliberately edits a file.
    if profile == "rooms":
        return WorldDocument(data)
    if profile == "precision":
        data["editor_profile"] = "precision"
    return MapDocument(data)
