from copy import deepcopy
import json
from pathlib import Path
import pygame

from .factory import create_scene
from platform2d.audio import SilentAudio
from platform2d.gameplay.campaign import CampaignProgress
from platform2d.gameplay.inventory import upgraded_weapon
from platform2d.tools.editor_model import MapDocument
from .locale import CampaignLocale


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
        self.locale = CampaignLocale()
        self.reset()

    def set_language(self,language):
        self.locale=CampaignLocale(language)
        self.active.locale=self.locale

    @property
    def paused(self):
        return self.active.paused

    def reset(self):
        self.progress.reset()
        self.totals = dict(shots=0,deaths=0,elapsed=0)
        self.active = create_scene(self.documents[0],self.settings)
        self.active.locale=self.locale

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
                self.active.locale=self.locale
            return
        self.active.update(dt,actions)
        if self.active.won and self.progress.complete():
            for key in self.totals:
                self.totals[key] += getattr(self.active,key)

    def draw(self,surface,alpha):
        self.active.format_controls = self.format_controls
        self.active.draw(surface,alpha)
        t=self.locale.t
        label = t('campaign.counter',current=self.progress.index+1,total=len(self.documents),name=self.locale.literal(self.name))
        pygame.draw.rect(surface,(9,17,29),(0,0,625,33))
        self.locale.draw(surface,label,(24,7,590,26),18,(118,220,205))
        if self.active.won:
            pygame.draw.rect(surface,(9,17,29),(120,195,720,230),border_radius=12)
            title = t('campaign.complete' if self.progress.finished else 'level.complete')
            self.locale.draw(surface,title,(150,211,660,56),38,(220,245,237),'center')
            self.locale.draw(surface,t('campaign.totals',shots=self.totals['shots'],deaths=self.totals['deaths'],elapsed=f"{self.totals['elapsed']:.1f}"),(160,285,640,32),20,align='center')
            message = t('campaign.restart' if self.progress.finished else 'campaign.next_hint')
            self.locale.draw(surface,message,(155,330,650,30),18,(146,225,205),'center')
            if not self.progress.finished:
                self.locale.draw(surface,t('campaign.next',name=self.locale.literal(self.documents[self.progress.index+1].data['name'])),(160,365,640,30),18,align='center')
