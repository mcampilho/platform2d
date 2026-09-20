from copy import deepcopy
import json
from pathlib import Path
import pygame

from .factory import create_scene
from platform2d.audio import SilentAudio
from platform2d.gameplay.campaign import CampaignProgress
from platform2d.gameplay.inventory import upgraded_weapon
from platform2d.tools.editor_model import MapDocument


def load_campaign(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict) or data.get("format") != "platform2d.campaign" or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("Formato de campanha incompatível.")
    if not isinstance(data.get("name"),str) or not data["name"].strip():
        raise ValueError("A campanha precisa de nome.")
    stages = data.get("stages")
    if not isinstance(stages,list) or not 1 <= len(stages) <= 32:
        raise ValueError("A campanha precisa de 1 a 32 níveis.")
    documents,ids = [],[]
    for stage in stages:
        if not isinstance(stage,dict) or not isinstance(stage.get("map"),str) or not stage["map"]:
            raise ValueError("Cada nível precisa de um caminho de mapa.")
        ids.append(stage.get("id"))
        document = MapDocument.load(path.parent/stage["map"])
        if document.profile not in {"ranged","adventure"}:
            raise ValueError("Esta campanha usa mapas dos perfis Combate e Aventura.")
        errors = [i.message for i in document.validate() if i.severity == "error"]
        if errors:
            raise ValueError(stage["map"]+": "+errors[0])
        documents.append(document)
    CampaignProgress(ids)
    return data["name"],ids,documents


class CampaignScene:
    def __init__(self,name,ids,documents,settings):
        if len(ids) != len(documents):
            raise ValueError("Os níveis e os mapas não correspondem.")
        self.name = name
        self.progress = CampaignProgress(ids)
        self.documents = [MapDocument(deepcopy(doc.data)) for doc in documents]
        self.settings = deepcopy(settings)
        self.audio = SilentAudio()
        self.format_controls = str
        self.reset()

    @property
    def paused(self):
        return self.active.paused

    def reset(self):
        self.progress.reset()
        self.totals = dict(shots=0,deaths=0,elapsed=0)
        self.active = create_scene(self.documents[0],self.settings)

    def update(self,dt,actions):
        if "reset" in actions.pressed:
            self.reset()
            return
        self.active.audio = self.audio
        self.active.format_controls = self.format_controls
        if self.active.won:
            self.active.freeze()
            if "continue" in actions.pressed and not self.progress.finished:
                # Construct before changing progress: a failed scene leaves the old one intact.
                next_scene = create_scene(self.documents[self.progress.index+1],self.settings)
                next_scene.inventory = self.active.inventory
                next_scene.weapon.spec = upgraded_weapon(next_scene.spec,next_scene.inventory)
                next_scene.debug = self.active.debug
                next_scene.audio = self.audio
                next_scene.format_controls = self.format_controls
                self.progress.advance()
                self.active = next_scene
            return
        self.active.update(dt,actions)
        if self.active.won and self.progress.complete():
            for key in self.totals:
                self.totals[key] += getattr(self.active,key)

    def draw(self,surface,alpha):
        self.active.format_controls = self.format_controls
        self.active.draw(surface,alpha)
        label = f"CAMPANHA / {self.progress.index+1} DE {len(self.documents)} / {self.name}"
        pygame.draw.rect(surface,(9,17,29),(0,0,625,33))
        self.active.text(surface,label,24,15,(118,220,205))
        if self.active.won:
            pygame.draw.rect(surface,(9,17,29),(120,195,720,230),border_radius=12)
            title = "Campanha concluída!" if self.progress.finished else "Nível concluído!"
            self.active.text(surface,title,245,217,(220,245,237),self.active.large)
            self.active.text(surface,f"TOTAL: {self.totals['shots']} tiros · {self.totals['deaths']} mortes · {self.totals['elapsed']:.1f}s",250,285)
            message = "F2: recomeçar a campanha" if self.progress.finished else "[Enter] próximo nível · melhorias e kits conservados"
            self.active.text(surface,message,220,330,(146,225,205))
            if not self.progress.finished:
                self.active.text(surface,"Próximo: "+self.documents[self.progress.index+1].data['name'],220,365)
