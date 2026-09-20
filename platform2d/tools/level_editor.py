"""Pygame map editor. A preview factory is injected by the host game."""
from pathlib import Path
from copy import deepcopy
from time import perf_counter
import pygame

from platform2d.actors.controller import Movement
from .editor_model import Issue, MapDocument, OBJECT_SIZES, PROFILES, new_map
from .world_editor import WorldDocument
from platform2d.audio.service import SilentAudio,AudioControls
from .reachability import ReachabilitySearch
from .adventure_reachability import AdventureSearch
from .controls_panel import ControlsPanel
from platform2d.rendering.terrain import draw_ramp
from platform2d.gameplay.ranged_config import weapon_spec,TARGET_DEFAULTS
from platform2d.gameplay.inventory import ITEMS,CATALOG


TOOLS = [("select","V  Selecionar"),("#","1  Chão sólido"),("=","2  Plataforma"),
         (".","3  Borracha"),("spawn","4  Ponto inicial"),("coin","5  Cristal"),
         ("checkpoint","6  Checkpoint"),("hazard","7  Perigo"),("goal","8  Saída")]
COLORS = {"spawn":(114,232,200),"coin":(255,205,113),"checkpoint":(146,188,244),
          "hazard":(243,120,145),"goal":(190,158,248),"ladder":(130,194,226),
          "beacon":(255,205,113),"entry":(114,232,200),"door":(194,166,248),"moving_platform":(100,220,204),"switch":(249,190,102)}
COLORS.update(guardian=(192,101,126),part=(122,211,245),fuel=(249,188,95),rocket=(190,223,231),pickup=(128,234,182),target=(221,192,116),turret=(245,156,105))
COLORS.update(crate=(220,170,103),plate=(240,202,114),gate=(232,137,122),water=(84,172,227),air=(179,234,239),ability=(192,150,246))
PROFILE_NAMES = {"classic":"Clássico","precision":"Precisão","rooms":"Salas","ranged":"Combate","adventure":"Aventura"}


class LevelEditor:
    def __init__(self, preview_factory, bindings, document=None, default_path="levels/meu-nivel.json", analysis_movement=None, profiles=None, audio=None, controls_dir=None):
        self.controls_dir = Path(controls_dir) if controls_dir is not None else None
        self.workspace = None
        self.controls = None
        self.audio = audio or SilentAudio()
        self.audio_controls = AudioControls(audio) if audio is not None else None
        self.document = document or MapDocument()
        self.preview_factory,self.bindings = preview_factory,bindings
        self.profiles = profiles or {}
        self.default_path = Path(default_path)
        self.screen = pygame.display.set_mode((1280,800))
        pygame.display.set_caption("Platform2D 0.23 - Atelier - Aventura")
        self.font = pygame.font.SysFont("segoeui",17)
        self.small = pygame.font.SysFont("consolas",13)
        self.title = pygame.font.SysFont("segoeui",26,bold=True)
        self.canvas = pygame.Rect(200,112,824,608)
        self.zoom = 1.0
        self.camera = [0.0,0.0]
        self.tool = "#"
        self.selected = None
        self.show_tiles = self.show_objects = self.show_grid = True
        self.buttons = []
        self.modal = None
        self.preview = None
        self.preview_input = None
        self.solution_actions = None
        self.solution_index = 0
        self.analysis_movement = deepcopy(analysis_movement or Movement())
        self.analysis = self.analysis_result = self.analysis_data = None
        self.analysis_settings = None
        self.accumulator = 0
        self.stroke = self.drag = self.pan = None
        self.object_scroll = 0
        self.mouse = (0,0)
        self.running = True
        self.status = "Começa por desenhar. F5 testa o mapa sem o guardar."
        self.refresh()

    def search_movement(self):
        return self.analysis_movement if self.document.profile=='classic' else self.profiles.get(self.document.profile,{}).get('movement',self.analysis_movement)

    def refresh(self):
        if self.tool not in {"select","#","=",".","/","\\"} | PROFILES[self.document.profile]:
            self.tool = "select"
        if self.document.profile not in {"classic","adventure"} or self.analysis_data != self.document.data or self.analysis_settings != vars(self.search_movement()):
            self.analysis = self.analysis_result = None
        self.structural_issues = self.document.validate()
        self.issues = self.structural_issues[:]
        if self.analysis_result is not None:
            self.issues.extend(self.analysis_result.issues)
        if self.selected is not None and self.selected >= len(self.document.data["objects"]):
            self.selected = None
        self.clamp_camera()

    def clamp_camera(self):
        for i,extent in enumerate((self.canvas.width,self.canvas.height)):
            maximum = self.document.size[i]*self.document.tile_size-extent/self.zoom
            self.camera[i] = max(0,min(self.camera[i],max(0,maximum)))

    def world_position(self,position):
        return ((position[0]-self.canvas.x)/self.zoom+self.camera[0],
                (position[1]-self.canvas.y)/self.zoom+self.camera[1])

    def cell(self,position):
        x,y = self.world_position(position)
        size = self.document.tile_size
        return int(x//size),int(y//size)

    def screen_box(self,box):
        # Keep invalid, very distant object coordinates renderable for correction.
        limit = lambda value:max(-1000000,min(1000000,value))
        return pygame.Rect(round(limit(self.canvas.x+(box.x-self.camera[0])*self.zoom)),
                           round(limit(self.canvas.y+(box.y-self.camera[1])*self.zoom)),
                           max(1,round(limit(box.w*self.zoom))),max(1,round(limit(box.h*self.zoom))))

    def set_zoom(self,factor,anchor=None):
        anchor = anchor or self.canvas.center
        before = self.world_position(anchor)
        self.zoom = max(.25,min(2.5,self.zoom*factor))
        after = self.world_position(anchor)
        self.camera[0] += before[0]-after[0]
        self.camera[1] += before[1]-after[1]
        self.clamp_camera()

    def finish_edit(self):
        self.document.commit()
        self.stroke = self.drag = None
        self.refresh()

    def replace_document(self,document):
        if document.profile != "classic" and document.profile not in self.profiles:
            raise ValueError("O anfitrião deste editor não fornece teste para este perfil.")
        self.document = document
        self.selected = None
        self.camera = [0.0,0.0]
        self.object_scroll = 0
        self.refresh()
        self.status = "Mapa aberto." if document.path else "Novo mapa. Escolhe Guardar para criar um ficheiro."

    def tools(self):
        base = [(kind,label) for kind,label in TOOLS if kind in {"select","#","=",".","/","\\"} | PROFILES[self.document.profile]]
        extras = {"precision":[("beacon","5  Sinal"),("ladder","L  Escada")],
                  "ranged":[("target","5  Alvo"),("turret","T  Torreta"),("pickup","I  Recolhível")],
                  "rooms":[("entry","I  Entrada"),("door","O  Porta"),("moving_platform","M  Plat. móvel"),("switch","T  Interruptor")]}
        extras["adventure"]=extras["ranged"]+[("part","9  Peça"),("fuel","0  Combustível"),("rocket","O  Foguetão"),("guardian","Q  Guardião")]
        mode=self.document.data.get('properties',{}).get('traversal')
        expansion_tools={'cargo': [('crate','Caixa (2 t)'),('plate','Placa de peso'),('gate','Porta de carga')],
                         'swim':[('water','Água / corrente'),('air','Bolsa de ar')],
                         'escape':[], 'explore':[('ability','Salto duplo'),('gate','Porta de capacidade')]}
        if self.document.profile=='adventure' and mode in expansion_tools: extras['adventure']=expansion_tools[mode]
        if self.document.profile in {"ranged","adventure"}:
            base = [(kind,"C  Cristal" if kind == "coin" else label) for kind,label in base]
        return base+[("/","U  Rampa /"),("\\","B  Rampa \\")]+extras.get(self.document.profile,[])

    def open_campaign_workspace(self,path=None):
        from .campaign_model import CampaignDocument
        from .campaign_editor import CampaignEditor
        campaign=CampaignDocument.load(path) if path else CampaignDocument()
        def open_it():
            self.workspace=CampaignEditor(campaign,self.profiles,audio=self.audio,controls_dir=self.controls_dir,
                                          on_close=lambda:setattr(self,'workspace',None))
        self.protect_unsaved(open_it)

    def new_dialog(self):
        def create(profile):
            if profile == "rooms":
                document = WorldDocument()
            else:
                data = new_map(30,18) if profile == "ranged" else new_map()
                if profile == "precision":
                    data["editor_profile"] = "precision"
                    data["name"] = "O meu percurso de precisão"
                elif profile == "ranged":
                    data["editor_profile"] = "ranged"
                    data["name"] = "O meu campo de treino"
                if profile == "adventure":
                    data["editor_profile"]="adventure"
                    data["properties"]={"traversal":"walk","scroll":"both"}
                document = MapDocument(data)
            self.protect_unsaved(lambda:self.replace_document(document))
        available = [p for p in PROFILE_NAMES if p == "classic" or p in self.profiles]
        self.confirm("Novo projeto — escolhe o perfil","Clássico: saltos e cristais. Precisão: dash, paredes e escadas. Salas: portas e elevadores. Combate: projéteis, alvos e torretas.",
                     [(PROFILE_NAMES[p],lambda p=p:create(p)) for p in available]+([("Campanha",self.open_campaign_workspace)] if "campaign" in self.profiles else []))

    def choice(self,title,items,footer=()):
        self.modal = dict(kind="choice",title=title,items=items,footer=footer,scroll=0)

    def switch_room(self,room_id):
        self.finish_edit()
        self.document.switch_room(room_id)
        self.selected = None
        self.camera = [0,0]
        self.object_scroll = 0
        self.refresh()

    def room_dialog(self):
        if not isinstance(self.document,WorldDocument):
            return
        doc = self.document
        def added(value):
            doc.add_room(value)
            self.switch_room(doc.active_room)
        def renamed(value):
            doc.rename_room(value)
            self.refresh()
        def deleted():
            doc.delete_room()
            self.switch_room(doc.active_room)
        self.choice("Salas — "+doc.active_room,
            [(f"{key}  ·  {room.get('name','Sala')}"+("  [INÍCIO]" if key == doc.world.get("start_room") else ""),
              lambda key=key:self.switch_room(key)) for key,room in doc.world["rooms"].items()],
            [("Adicionar",lambda:self.input_dialog("ID da nova sala","sala_nova",added)),
             ("Mudar ID",lambda:self.input_dialog("Novo ID da sala",doc.active_room,renamed)),
             ("Eliminar",lambda:self.confirm("Eliminar sala?","As portas que apontam para esta sala terão de ser corrigidas. Podes desfazer.",[("Eliminar",deleted),("Cancelar",self.room_dialog)]))])

    def door_destination(self):
        index = self.selected
        doc = self.document
        def choose_entry(room_id):
            self.choice("Entrada em "+room_id,[(entry,lambda entry=entry:(doc.link_door(index,room_id,entry),self.refresh())) for entry in doc.entries(room_id)])
        self.choice("Sala de destino da porta",[(key,lambda key=key:choose_entry(key)) for key in doc.world["rooms"]])

    def special_properties(self):
        index = self.selected
        if index is None:
            return
        obj = self.document.data["objects"][index]
        if obj['type'] in {'plate','water'}:
            field='weight' if obj['type']=='plate' else 'current'
            def apply(text):
                value=int(text) if field=='weight' else float(text.replace(',','.'))
                self.document.update_object(index,**{field:value}); self.finish_edit()
            self.input_dialog('Peso mínimo (1–8 t)' if field=='weight' else 'Corrente horizontal (-80 a 80)',obj.get(field,2 if field=='weight' else 0),apply)
            return
        if obj['type']=='gate':
            self.confirm('Condição de abertura','Carga: exige todas as placas do mapa. Exploração: exige recolher a capacidade de salto duplo.', [('Fechar',lambda:None)])
            return
        if obj["type"] == "guardian":
            def apply(text):
                self.document.update_object(index,hp=int(text))
                self.document.commit(); self.refresh()
            self.input_dialog("Vida do guardião (1–20)",obj.get("hp",3),apply)
            return
        if obj["type"] == "pickup":
            self.pickup_properties(index)
            return
        if obj["type"] in {"target","turret"}:
            self.ranged_properties(index)
            return
        if obj["type"] == "door":
            self.choice("Porta — destino e condições",[("Ligar porta…",self.door_destination),("Condições de abertura…",self.conditions_dialog)])
        elif obj["type"] == "goal" and isinstance(self.document,WorldDocument):
            self.conditions_dialog()
        elif obj["type"] == "switch":
            def mode():
                value = "touch" if obj.get("activation","interact") == "interact" else "interact"
                self.document.update_object(index,activation=value)
                self.finish_edit()
                self.special_properties()
            self.choice("Interruptor",[("Nome: "+obj.get("label","Interruptor"),lambda:self.input_dialog("Nome apresentado no jogo",obj.get("label","Interruptor"),lambda text:(self.document.update_object(index,label=text.strip()),self.finish_edit()))),
                ("Ativação: "+("tecla E" if obj.get("activation","interact") == "interact" else "ao tocar")+" — clicar para mudar",mode),
                ("Condições para ativar…",self.conditions_dialog)])
        elif obj["type"] == "moving_platform":
            self.choice("Percurso da plataforma",[
                (f"Destino X: {obj['end'][0]:g}",lambda:self.edit_platform("end_x")),
                (f"Destino Y: {obj['end'][1]:g}",lambda:self.edit_platform("end_y")),
                (f"Velocidade: {obj.get('speed',60):g} unidades/s",lambda:self.edit_platform("speed"))])
        elif obj["type"] in {"entry","spawn"} and isinstance(self.document,WorldDocument):
            self.document.set_start(self.document.active_room,obj["id"])
            self.refresh()
            self.status = "Início do mundo definido nesta entrada."

    def conditions_dialog(self):
        index = self.selected
        obj = self.document.data["objects"][index]
        def remove(ref):
            self.document.update_object(index,requires=[r for r in obj.get("requires",[]) if r != ref])
            self.finish_edit()
            self.conditions_dialog()
        def add():
            choices = []
            for key,room in self.document.world["rooms"].items():
                for switch in room["objects"]:
                    ref = dict(room=key,switch=switch["id"])
                    if switch["type"] != "switch" or ref in obj.get("requires",[]) or (key == self.document.active_room and switch is obj):
                        continue
                    def choose(ref=ref):
                        self.document.update_object(index,requires=obj.get("requires",[])+[ref])
                        self.finish_edit()
                        self.conditions_dialog()
                    choices.append((key+" / "+switch["id"]+" · "+switch.get("label","Interruptor"),choose))
            if choices:
                self.choice("Escolher interruptor",choices)
            else:
                self.confirm("Sem interruptores disponíveis","Coloca um interruptor com T. Cada condição só pode ser adicionada uma vez e o objeto não pode depender de si próprio.",[("Voltar",self.conditions_dialog)])
        refs = obj.get("requires",[])
        self.choice("Exige TODOS os interruptores" if refs else "Sem condições — sempre disponível",
                    [("Remover: "+r["room"]+" / "+r["switch"],lambda r=r:remove(r)) for r in refs],[("Adicionar condição",add)])

    def edit_platform(self,field):
        index = self.selected
        obj = self.document.data["objects"][index]
        value = obj.get("speed",60) if field == "speed" else obj["end"][0 if field == "end_x" else 1]
        def apply(text):
            number = float(text.replace(",","."))
            if field == "speed":
                changes = dict(speed=number)
            else:
                end = obj["end"][:]
                end[0 if field == "end_x" else 1] = number
                changes = dict(end=end)
            self.document.update_object(index,**changes)
            self.finish_edit()
            self.special_properties()
        self.input_dialog({"end_x":"Destino X","end_y":"Destino Y","speed":"Velocidade (unidades/s)"}[field],value,apply)

    def pickup_properties(self,index):
        obj = self.document.data["objects"][index]
        item = obj.get("item","medkit")
        def apply(**changes):
            self.document.update_object(index,**changes)
            self.document.commit()
            self.refresh()
            self.pickup_properties(index)
        def choose_item():
            self.choice("Tipo de recolhível",[(definition.label,lambda definition=definition:
                apply(item=definition.id,quantity=min(obj.get("quantity",1),definition.limit))) for definition in ITEMS])
        def quantity():
            self.input_dialog("Quantidade",obj.get("quantity",1),lambda text:apply(quantity=int(text)))
        self.choice("Configurar recolhível",[("Tipo: "+CATALOG[item].label,choose_item),
                    (f"Quantidade: {obj.get('quantity',1)} (máximo {CATALOG[item].limit})",quantity)])

    def mission_properties(self):
        props = self.document.data.get("properties",{})
        labels = {"station":"Estação","garden":"Jardins","ice":"Glacial","reactor":"Reator"}
        def apply(**changes):
            self.document.update_mission(**changes)
            self.refresh()
            self.mission_properties()
        def themes():
            self.choice("Ambiente da sala",[(label,lambda key=key:apply(theme=key)) for key,label in
                        [("station","Estação"),("garden","Jardins"),("ice","Glacial"),("reactor","Reator")]])
        items=[("Ambiente: "+labels[props.get("theme","station")],themes),
               ("Disparos: "+("ativos" if props.get("weapon_enabled",True) else "desativados"),
                lambda:apply(weapon_enabled=not props.get("weapon_enabled",True)))]
        if self.document.profile=="adventure":
            def modes():
                self.choice("Movimento",[(label,lambda mode=mode:apply(traversal=mode)) for mode,label in
                            [("walk","Plataformas"),("jetpack","Jetpack e foguetão"),("ledge","Agarrar bordas"),("duel","Espada e defesa"),("cargo","Caixas e peso"),("swim","Natação"),("escape","Fuga"),("explore","Exploração e capacidade")]])
            def scrolling():
                self.choice("Câmara",[(label,lambda mode=mode:apply(scroll=mode)) for mode,label in
                            [("none","Ecrã fixo"),("horizontal","Horizontal"),("vertical","Vertical"),("both","Dois eixos")]])
            items += [("Movimento…",modes),("Câmara / scroll…",scrolling)]
        self.choice("Missão / ambiente",items)

    def ranged_properties(self,index=None):
        labels = {"speed":"Velocidade do projétil (unidades/s)","cooldown":"Intervalo entre tiros (segundos)",
                  "lifetime":"Duração do projétil (segundos)","damage":"Dano por impacto", "hp":"Resistência",
                  "interval":"Intervalo entre tiros (segundos)","projectile_speed":"Velocidade do projétil (unidades/s)","range":"Alcance (unidades)"}
        if index is None:
            spec = weapon_spec(self.document.data.get("properties",{}))
            fields = {key:getattr(spec,key) for key in ("speed","cooldown","lifetime","damage")}
        else:
            obj = self.document.data["objects"][index]
            fields = {key:obj.get(key,TARGET_DEFAULTS[key]) for key in (("hp","interval","projectile_speed","range") if obj["type"] == "turret" else ("hp",))}
        def edit(field):
            def apply(text):
                value = int(text) if field in {"hp","damage"} else float(text.replace(",","."))
                if index is None:
                    self.document.update_weapon(**{field:value})
                else:
                    self.document.update_object(index,**{field:value})
                    self.document.commit()
                self.refresh()
                self.ranged_properties(index)
            self.input_dialog(labels[field],fields[field],apply)
        self.choice("Arma do jogador" if index is None else "Configurar alvo / torreta",
                    [(f"{labels[key]}: {value:g}",lambda key=key:edit(key)) for key,value in fields.items()])

    def confirm(self,title,message,buttons):
        self.modal = {"kind":"confirm","title":title,"message":message,"buttons":buttons}

    def protect_unsaved(self,action):
        self.finish_edit()
        if not self.document.dirty:
            action()
            return
        self.confirm("Alterações por guardar", "Queres guardar o mapa antes de continuar?",[
            ("Guardar",lambda:self.save(after=action)),("Descartar",action),("Cancelar",lambda:None)])

    def input_dialog(self,title,text,callback,kind="text"):
        self.modal = {"kind":kind,"title":title,"text":str(text),"cursor":len(str(text)),
                      "select_all":True,"callback":callback,"error":""}

    def open_dialog(self):
        def load(path):
            import json
            raw=json.loads(Path(path).read_text(encoding='utf-8-sig'))
            if 'campaign' in self.profiles and isinstance(raw,dict) and raw.get('format')=='platform2d.campaign':
                self.open_campaign_workspace(path)
                return
            document = MapDocument.load(path)
            self.protect_unsaved(lambda:self.replace_document(document))
        self.input_dialog("Abrir mapa JSON",str(self.document.path or self.default_path),load,"open")

    def save(self,as_new=False,after=None):
        self.finish_edit()
        if any(i.severity == "error" for i in self.structural_issues):
            self.status = "Corrige os erros antes de guardar. O mapa atual continua no editor."
            self.show_validation()
            return
        def write(path):
            target = Path(path).expanduser().resolve()
            def perform():
                saved = self.document.save(target)
                self.status = f"Guardado: {saved.name}"
                if after:
                    after()
            if target.exists() and target != self.document.path:
                self.confirm("Substituir ficheiro?",f"Já existe: {target.name}",[("Substituir",perform),("Cancelar",lambda:None)])
            else:
                perform()
        if as_new or self.document.path is None:
            self.input_dialog("Guardar mapa como",str(self.document.path or self.default_path),write,"save")
        else:
            self.guard(lambda:write(self.document.path))

    def show_validation(self):
        self.finish_edit()
        self.modal = {"kind":"validation","title":"Validação do mapa","scroll":0}
        if self.document.profile in {"classic","adventure"} and not any(i.severity == "error" for i in self.structural_issues) and self.analysis_result is None:
            self.analysis_data = deepcopy(self.document.data)
            self.analysis_settings = vars(self.search_movement()).copy()
            self.analysis = (AdventureSearch(self.analysis_data,self.search_movement(),self.profiles.get('adventure',{}).get('factory'))
                             if self.document.profile=='adventure' else ReachabilitySearch(self.analysis_data,self.search_movement()))

    def close_validation(self):
        if self.analysis is not None:
            self.analysis = None
            self.status = "Pesquisa cancelada. F8 inicia outra verificação."
        self.modal = None

    def start_solution(self):
        self.refresh()
        if self.analysis_result is None or self.analysis_result.status != "solved":
            return
        actions = self.analysis_result.actions
        self.modal = None
        self.start_preview()
        self.solution_actions = actions
        self.solution_index = 0

    def guard(self,callback):
        try:
            callback()
        except (OSError,ValueError,TypeError) as error:
            self.status = str(error).splitlines()[0]
            self.confirm("Não foi possível concluir",str(error),[("Fechar",lambda:None)])

    def start_preview(self):
        self.finish_edit()
        if any(i.severity == "error" for i in self.structural_issues):
            self.status = "Corrige os erros indicados antes de testar."
            self.show_validation()
            return
        profile = self.profiles.get(self.document.profile,{})
        self.preview = profile.get("factory",self.preview_factory)(self.document.playable())
        self.preview.audio = self.audio
        if self.controls:
            self.controls.close()
        path = self.controls_dir/(self.document.profile+".controls.json") if self.controls_dir is not None else None
        self.controls = ControlsPanel(profile.get("bindings",self.bindings),self.document.profile,path)
        self.preview.format_controls = self.controls.format_hint
        self.preview_input = self.controls.input
        self.solution_actions = None
        self.solution_index = 0
        self.accumulator = 0
        self.status = "Teste isolado: F5 ou Escape regressa à edição."

    def stop_preview(self):
        self.audio.stop()
        if self.controls:
            self.controls.close()
            self.controls = None
        self.preview = self.preview_input = None
        self.solution_actions = None
        self.accumulator = 0
        self.status = "De volta ao editor. O teste não alterou o mapa nem o histórico."

    def delete_selection(self):
        if self.selected is not None:
            self.document.delete_object(self.selected)
            self.selected = None
            self.refresh()

    def edit_property(self,field):
        if self.selected is None:
            return
        index = self.selected
        obj = self.document.data["objects"][index]
        value = obj.get(field,24 if field == "w" else 30)
        def apply(text):
            new = text.strip() if field == "id" else float(text.replace(",","."))
            self.document.update_object(index,**{field:new})
            self.finish_edit()
        self.input_dialog("Editar "+field,value,apply)

    def nudge_property(self,field,amount):
        if self.selected is not None:
            obj = self.document.data["objects"][self.selected]
            value = obj.get(field,24 if field == "w" else 30)+amount
            self.document.update_object(self.selected,**{field:value})
            self.finish_edit()

    def resize_dialog(self):
        width,height = self.document.size
        def resize(text):
            parts = text.lower().replace("×","x").split("x")
            if len(parts) != 2:
                raise ValueError("Escreve largura x altura, por exemplo 48 x 18.")
            width,height = (int(p.strip()) for p in parts)
            def apply():
                self.document.resize(width,height)
                self.refresh()
            if width < self.document.size[0] or height < self.document.size[1]:
                self.confirm("Reduzir a grelha?","Tiles fora da nova área serão cortados. Os objetos são mantidos e validados. Podes desfazer.",[("Reduzir",apply),("Cancelar",lambda:None)])
            else:
                apply()
        self.input_dialog("Tamanho em tiles",f"{width} x {height}",resize)

    def handle_modal(self,event):
        modal = self.modal
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if modal["kind"] == "validation":
                self.close_validation()
            else:
                self.modal = None
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect,callback in reversed(self.buttons):
                if rect.collidepoint(event.pos):
                    self.guard(callback)
                    return
        if modal["kind"] in {"validation","choice"}:
            if event.type == pygame.MOUSEWHEEL:
                count = len(self.issues) if modal["kind"] == "validation" else len(modal["items"])
                modal["scroll"] = max(0,min(max(0,count-6),modal["scroll"]-event.y))
            return
        if modal["kind"] == "confirm":
            return
        text = modal["text"]
        if event.type == pygame.TEXTINPUT:
            if modal["select_all"]:
                text = ""
                modal["cursor"] = 0
            cursor = modal["cursor"]
            modal["text"] = (text[:cursor]+event.text+text[cursor:])[:1000]
            modal["cursor"] = min(1000,cursor+len(event.text))
            modal["select_all"] = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.submit_modal()
            elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                modal["select_all"] = True
            elif event.key in (pygame.K_BACKSPACE,pygame.K_DELETE):
                cursor = modal["cursor"]
                if modal["select_all"]:
                    modal["text"],modal["cursor"] = "",0
                elif event.key == pygame.K_BACKSPACE and cursor:
                    modal["text"] = text[:cursor-1]+text[cursor:]
                    modal["cursor"] -= 1
                elif event.key == pygame.K_DELETE:
                    modal["text"] = text[:cursor]+text[cursor+1:]
                modal["select_all"] = False
            elif event.key in (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_HOME,pygame.K_END):
                modal["select_all"] = False
                if event.key == pygame.K_HOME:
                    modal["cursor"] = 0
                elif event.key == pygame.K_END:
                    modal["cursor"] = len(text)
                else:
                    modal["cursor"] = max(0,min(len(text),modal["cursor"]+(1 if event.key == pygame.K_RIGHT else -1)))

    def submit_modal(self):
        modal = self.modal
        self.modal = None
        try:
            modal["callback"](modal["text"])
        except (OSError,ValueError,TypeError) as error:
            modal["error"] = str(error)
            self.modal = modal

    def handle_event(self,event):
        if self.workspace:
            self.workspace.handle_event(event)
            return
        if self.audio_controls and self.audio_controls.handle_event(event):
            return
        if event.type == pygame.QUIT:
            if self.preview:
                self.stop_preview()
            self.protect_unsaved(lambda:setattr(self,"running",False))
            return
        if event.type == pygame.MOUSEMOTION:
            self.mouse = event.pos
        if event.type == pygame.WINDOWFOCUSLOST:
            self.finish_edit()
            self.pan = None
        if self.modal:
            self.handle_modal(event)
            return
        if self.preview:
            if self.controls and self.solution_actions is None and self.controls.handle_event(event):
                self.audio.stop()
                self.accumulator = 0
                return
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_F5,pygame.K_ESCAPE):
                self.stop_preview()
            return
        if event.type == pygame.KEYDOWN:
            self.finish_edit()
            ctrl = event.mod & pygame.KMOD_CTRL
            shift = event.mod & pygame.KMOD_SHIFT
            if ctrl:
                if event.key == pygame.K_s:
                    self.save(bool(shift))
                elif event.key == pygame.K_o:
                    self.open_dialog()
                elif event.key == pygame.K_n:
                    self.new_dialog()
                elif event.key in (pygame.K_y,pygame.K_z):
                    if event.key == pygame.K_y or shift:
                        self.document.redo()
                    else:
                        self.document.undo()
                    self.selected = None
                    self.refresh()
                return
            key_tools = {pygame.K_v:"select",**{pygame.K_1+i:tool for i,(tool,_) in enumerate(TOOLS[1:])}}
            key_tools.update({pygame.K_u:"/",pygame.K_b:"\\"})
            key_tools.update({pygame.K_l:"ladder",pygame.K_i:"entry",pygame.K_o:"door",pygame.K_m:"moving_platform",pygame.K_t:"switch"})
            if self.document.profile == "precision":
                key_tools[pygame.K_5] = "beacon"
            elif self.document.profile in {"ranged","adventure"}:
                key_tools.update({pygame.K_5:"target",pygame.K_t:"turret",pygame.K_i:"pickup",pygame.K_c:"coin",pygame.K_9:"part",pygame.K_0:"fuel",pygame.K_o:"rocket",pygame.K_q:"guardian"})
            if event.key in key_tools:
                candidate = key_tools[event.key]
                if candidate not in {"select","#","=",".","/","\\"} | PROFILES[self.document.profile]:
                    return
                self.tool = candidate
                if self.tool in OBJECT_SIZES or self.tool == "select":
                    self.show_objects = True
                else:
                    self.show_tiles = True
            elif event.key == pygame.K_DELETE:
                self.delete_selection()
            elif event.key == pygame.K_F5:
                self.guard(self.start_preview)
            elif event.key == pygame.K_F8:
                self.show_validation()
            elif event.key == pygame.K_g:
                self.show_grid = not self.show_grid
            elif event.key == pygame.K_ESCAPE:
                self.selected = None
            elif event.key in (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN):
                dx = int(event.key == pygame.K_RIGHT)-int(event.key == pygame.K_LEFT)
                dy = int(event.key == pygame.K_DOWN)-int(event.key == pygame.K_UP)
                if self.selected is not None:
                    obj = self.document.data["objects"][self.selected]
                    scale = 8 if shift else 1
                    self.document.update_object(self.selected,x=obj["x"]+dx*scale,y=obj["y"]+dy*scale)
                    self.finish_edit()
                else:
                    self.camera[0] += dx*64/self.zoom
                    self.camera[1] += dy*64/self.zoom
                    self.clamp_camera()
        elif event.type == pygame.MOUSEWHEEL:
            if self.canvas.collidepoint(self.mouse):
                self.set_zoom(1.15**event.y,self.mouse)
            elif self.mouse[0] > 1040:
                self.object_scroll = max(0,min(max(0,len(self.document.data["objects"])-5),self.object_scroll-event.y))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse = event.pos
            if event.button == 1:
                for rect,callback in reversed(self.buttons):
                    if rect.collidepoint(event.pos):
                        self.finish_edit()
                        self.guard(callback)
                        return
            if not self.canvas.collidepoint(event.pos):
                return
            if event.button == 2:
                self.pan = event.pos
            elif event.button in (1,3):
                x,y = self.world_position(event.pos)
                if self.tool == "select":
                    self.selected = self.document.pick(x,y) if self.show_objects else None
                    if event.button == 3:
                        self.delete_selection()
                    elif self.selected is not None:
                        obj = self.document.data["objects"][self.selected]
                        self.document.begin()
                        self.drag = (x,y,obj["x"],obj["y"])
                elif self.tool in OBJECT_SIZES:
                    if event.button == 3:
                        self.selected = self.document.pick(x,y)
                        self.delete_selection()
                    else:
                        self.selected = self.document.place(self.tool,*self.cell(event.pos))
                        self.refresh()
                else:
                    tile = "." if event.button == 3 else self.tool
                    self.stroke = (self.cell(event.pos),tile)
                    self.document.paint(*self.cell(event.pos),tile)
        elif event.type == pygame.MOUSEMOTION:
            if self.pan is not None:
                self.camera[0] -= (event.pos[0]-self.pan[0])/self.zoom
                self.camera[1] -= (event.pos[1]-self.pan[1])/self.zoom
                self.pan = event.pos
                self.clamp_camera()
            elif self.canvas.collidepoint(event.pos):
                if self.stroke:
                    previous,tile = self.stroke
                    current = self.cell(event.pos)
                    self.document.paint_line(previous,current,tile)
                    self.stroke = (current,tile)
                elif self.drag and self.selected is not None:
                    x,y = self.world_position(event.pos)
                    start_x,start_y,obj_x,obj_y = self.drag
                    snap = 1 if pygame.key.get_mods() & pygame.KMOD_ALT else self.document.tile_size
                    dx,dy = round((x-start_x)/snap)*snap,round((y-start_y)/snap)*snap
                    obj = self.document.data["objects"][self.selected]
                    obj["x"],obj["y"] = obj_x+dx,obj_y+dy
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.pan = None
            else:
                self.finish_edit()

    def update(self,dt):
        if self.workspace:
            self.workspace.update(dt)
            return
        if self.audio_controls:
            self.audio_controls.update(dt)
        self.audio.update(dt,paused=bool(self.modal) or not self.preview or bool(self.controls and self.controls.open) or (self.audio_controls is not None and not self.audio_controls.focused))
        if self.analysis is not None and self.modal and self.modal["kind"] == "validation":
            deadline = perf_counter()+.008
            while self.analysis is not None and perf_counter() < deadline:
                result = self.analysis.step()
                if result is not None:
                    self.analysis_result = result
                    self.analysis = None
                    self.refresh()
                    self.status = {"solved":"Solução confirmada. F8 permite reproduzir a rota.",
                                   "impossible":"Há objetivos comprovadamente fora do alcance.",
                                   "inconclusive":"Pesquisa inconclusiva: não foi encontrada uma rota completa."}[result.status]
        if self.preview and not self.modal and not (self.controls and self.controls.open):
            self.accumulator += min(dt,.25)
            while self.accumulator >= 1/60:
                if self.solution_actions is None:
                    actions = self.preview_input.consume()
                    if "reset" in actions.pressed or "restart" in actions.pressed:
                        self.audio.stop()
                    self.audio.update(0,paused=(self.audio_controls is not None and not self.audio_controls.focused) or (self.preview.paused and "pause" not in actions.pressed))
                    self.preview.update(1/60,actions)
                elif self.solution_index < len(self.solution_actions):
                    self.preview.update(1/60,self.solution_actions[self.solution_index])
                    self.solution_index += 1
                self.accumulator -= 1/60
                self.audio.update(0,paused=(self.audio_controls is not None and not self.audio_controls.focused) or self.preview.paused)

    def text(self,text,x,y,color=(183,200,217),font=None):
        self.screen.blit((font or self.small).render(str(text),True,color),(round(x),round(y)))

    def wrapped(self,text,x,y,width,color=(183,200,217),font=None,line_height=23):
        font = font or self.font
        for paragraph in str(text).splitlines():
            line = ""
            for word in paragraph.split():
                candidate = (line+" "+word).strip()
                if font.size(candidate)[0] > width and line:
                    self.text(line,x,y,color,font)
                    y += line_height
                    line = word
                else:
                    line = candidate
            self.text(line,x,y,color,font)
            y += line_height
        return y

    def button(self,label,rect,callback,selected=False):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.screen,(37,81,85) if selected else (30,42,60),rect,border_radius=5)
        pygame.draw.rect(self.screen,(102,218,190) if selected else (53,70,91),rect,1,border_radius=5)
        font = self.small
        image = font.render(label,True,(225,235,242))
        self.screen.blit(image,image.get_rect(center=rect.center))
        self.buttons.append((rect,callback))

    def choose_tool(self,tool):
        self.tool = tool
        if tool in OBJECT_SIZES or tool == "select":
            self.show_objects = True
        else:
            self.show_tiles = True

    def draw_canvas(self):
        from platform2d.physics.body import Box
        pygame.draw.rect(self.screen,(8,17,30),self.canvas)
        self.screen.set_clip(self.canvas)
        size = self.document.tile_size
        width,height = self.document.size
        x0,y0 = int(self.camera[0]//size),int(self.camera[1]//size)
        x1 = min(width,int((self.camera[0]+self.canvas.width/self.zoom)//size)+1)
        y1 = min(height,int((self.camera[1]+self.canvas.height/self.zoom)//size)+1)
        for y in range(y0,y1):
            for x in range(x0,x1):
                r = self.screen_box(Box(x*size,y*size,size,size))
                tile = self.document.data["tiles"][y][x]
                if self.show_tiles and tile == "#":
                    pygame.draw.rect(self.screen,(47,79,98),r)
                    if r.width > 12:
                        pygame.draw.rect(self.screen,(29,52,73),r.inflate(-4,-5),border_radius=2)
                elif self.show_tiles and tile in "/\\":
                    draw_ramp(self.screen,r,-1 if tile == "/" else 1)
                elif self.show_tiles and tile == "=":
                    pygame.draw.rect(self.screen,(99,203,197),(r.x,r.y,r.w,max(2,int(6*self.zoom))))
                if self.show_grid:
                    pygame.draw.rect(self.screen,(28,43,61),r,1)
        if self.show_objects:
            for i,obj in enumerate(self.document.data["objects"]):
                r = self.screen_box(self.document.object_box(obj))
                color = COLORS[obj["type"]]
                pygame.draw.rect(self.screen,color,r,2,border_radius=3)
                if obj["type"] == "moving_platform":
                    end = self.screen_box(Box(*obj["end"],r.w/self.zoom,r.h/self.zoom))
                    pygame.draw.line(self.screen,color,r.center,end.center,2)
                    pygame.draw.rect(self.screen,color,end,1)
                    self.text("DESTINO",end.x,end.y-17,color)
                elif obj["type"] == "ladder":
                    for y in range(r.y+6,r.bottom, max(4,int(14*self.zoom))):
                        pygame.draw.line(self.screen,color,(r.left,y),(r.right,y),2)
                elif obj["type"] == "switch":
                    pygame.draw.line(self.screen,color,r.midbottom,r.topleft,3)
                if obj.get("requires"):
                    pygame.draw.circle(self.screen,(249,190,102),r.topright,4)
                if obj["type"] in {"coin","beacon"}:
                    pygame.draw.polygon(self.screen,color,[r.midtop,r.midright,r.midbottom,r.midleft])
                elif obj["type"] == "spawn":
                    pygame.draw.circle(self.screen,color,r.center,max(2,int(5*self.zoom)))
                elif obj["type"] == "hazard":
                    pygame.draw.line(self.screen,color,r.bottomleft,r.topright,2)
                    pygame.draw.line(self.screen,color,r.topleft,r.bottomright,2)
                elif obj["type"] == "pickup":
                    self.text({"power":"D","rapid":"C","medkit":"+"}[obj.get("item","medkit")],r.x+4,r.y+2,color)
                elif obj["type"] == "target":
                    pygame.draw.circle(self.screen,color,r.center,max(2,round(7*self.zoom)),2)
                elif obj["type"] == "turret":
                    pygame.draw.line(self.screen,color,r.center,r.midleft,max(2,round(4*self.zoom)))
                if self.zoom >= .75:
                    self.text(obj["id"],r.x,r.y-17,color)
                if i == self.selected:
                    pygame.draw.rect(self.screen,(250,248,206),r.inflate(6,6),2)
        if self.canvas.collidepoint(self.mouse) and not self.modal:
            x,y = self.cell(self.mouse)
            if 0 <= x < width and 0 <= y < height:
                r = self.screen_box(Box(x*size,y*size,size,size))
                pygame.draw.rect(self.screen,(129,181,195),r,2)
        self.screen.set_clip(None)
        pygame.draw.rect(self.screen,(56,79,99),self.canvas,1)

    def draw_inspector(self):
        self.text("PROPRIEDADES",1044,120,(111,223,192))
        if self.selected is not None:
            obj = self.document.data["objects"][self.selected]
            self.text(obj["type"].upper(),1044,151,COLORS[obj["type"]])
            self.button(obj["id"][:24],(1044,177,216,30),lambda:self.edit_property("id"))
            if obj["type"] == "door":
                destination = obj.get("target_room","")+" / "+obj.get("target_entry","")
                self.text(destination[:27],1044,208,(163,177,202))
            for index,field in enumerate(("x","y","w","h")):
                y = 223+index*38
                self.text(field.upper(),1044,y+8)
                value = obj.get(field,24 if field == "w" else 30)
                self.button("-",(1070,y,28,29),lambda field=field:self.nudge_property(field,-1))
                self.button(f"{value:g}",(1104,y,112,29),lambda field=field:self.edit_property(field))
                self.button("+",(1222,y,28,29),lambda field=field:self.nudge_property(field,1))
            self.button("Eliminar [DEL]",(1044,386,216,31),self.delete_selection)
            special = {"plate":"Peso mínimo…","water":"Corrente…","gate":"Condição de abertura…","guardian":"Vida do guardião…","door":"Destino / condições…","moving_platform":"Percurso / velocidade…","switch":"Configurar interruptor…","target":"Configurar alvo…","turret":"Configurar torreta…","pickup":"Configurar recolhível…"}
            if isinstance(self.document,WorldDocument) and obj["type"] == "goal":
                special["goal"] = "Condições da saída…"
            if isinstance(self.document,WorldDocument) and obj["type"] in {"spawn","entry"}:
                special[obj["type"]] = "Definir início do mundo"
            if obj["type"] in special:
                self.button(special[obj["type"]],(1044,423,216,31),self.special_properties)
            else:
                self.text("Setas: 1 unidade; Shift: 8",1044,428)
        else:
            self.wrapped("Seleciona um objeto no mapa ou na lista para ajustar posição e tamanho.",1044,156,210,font=self.font)
            self.wrapped("O corpo do jogador mede 24×30. W/H dos objetos definem a área de interação.",1044,277,210,color=(128,150,174),font=self.font)
        objects = self.document.data["objects"]
        self.text(f"OBJETOS ({len(objects)})",1044,466,(111,223,192))
        self.object_scroll = min(self.object_scroll,max(0,len(objects)-5))
        for offset,obj in enumerate(objects[self.object_scroll:self.object_scroll+5]):
            index = self.object_scroll+offset
            self.button(obj["id"][:25],(1044,488+offset*29,216,25),lambda index=index:self.select_object(index),index == self.selected)
        self.text("Roda sobre a lista: percorrer",1044,638,(128,150,174))
        # A compact overview keeps long levels navigable.
        width,height = self.document.size
        scale = min(212/width,57/height)
        for y,row in enumerate(self.document.data["tiles"]):
            for x,tile in enumerate(row):
                if tile != ".":
                    pygame.draw.rect(self.screen,(66,126,137),(1044+x*scale,660+y*scale,max(1,scale),max(1,scale)))
        size = self.document.tile_size
        pygame.draw.rect(self.screen,(159,219,206),(1044+self.camera[0]/size*scale,660+self.camera[1]/size*scale,
                         min(width,self.canvas.width/self.zoom/size)*scale,min(height,self.canvas.height/self.zoom/size)*scale),1)

    def select_object(self,index):
        self.selected = index
        self.tool = "select"
        self.show_objects = True
        obj = self.document.data["objects"][index]
        self.camera = [obj["x"]-self.canvas.width/self.zoom/2,obj["y"]-self.canvas.height/self.zoom/2]
        self.clamp_camera()

    def close_modal_action(self,callback):
        self.modal = None
        callback()

    def draw_modal(self):
        self.buttons = []
        shade = pygame.Surface((1280,800),pygame.SRCALPHA)
        shade.fill((3,8,18,210))
        self.screen.blit(shade,(0,0))
        pygame.draw.rect(self.screen,(18,29,46),(230,117,820,570),border_radius=10)
        pygame.draw.rect(self.screen,(67,107,124),(230,117,820,570),1,border_radius=10)
        modal = self.modal
        self.text(modal["title"],257,139,(229,243,242),self.title)
        kind = modal["kind"]
        if kind == "confirm":
            self.wrapped(modal["message"],257,201,752)
            for index,(label,callback) in enumerate(modal["buttons"]):
                spacing = min(235,756//max(1,len(modal["buttons"])))
                self.button(label,(257+index*spacing,612,spacing-12,40),lambda callback=callback:self.close_modal_action(callback))
        elif kind == "choice":
            for index,(label,callback) in enumerate(modal["items"][modal["scroll"]:modal["scroll"]+6]):
                self.button(label[:89],(257,201+index*53,756,43),lambda callback=callback:self.close_modal_action(callback))
            self.text("Roda: percorrer · Escape: fechar",257,539)
            for index,(label,callback) in enumerate(modal["footer"]):
                self.button(label,(257+index*250,578,235,34),lambda callback=callback:self.close_modal_action(callback))
            self.button("Fechar",(859,635,153,33),lambda:setattr(self,"modal",None))
        elif kind == "validation":
            if self.analysis is not None:
                self.text("A repetir a rota nas regras reais do jogo…" if getattr(self.analysis,"replay",None) is not None else f"A procurar uma rota completa... {self.analysis.explored} estados. Escape cancela.",257,179,(129,223,196))
            elif self.analysis_result is not None:
                labels = {"solved":"SOLUÇÃO CONFIRMADA", "impossible":"OBJETIVO INACESSÍVEL", "inconclusive":"RESULTADO INCONCLUSIVO"}
                self.text(labels[self.analysis_result.status],257,179,(129,223,196))
            issues = self.issues or [Issue("ok","Geometria validada. A pesquisar a solução jogável…" if self.document.profile == "classic" else "Geometria validada. Confirma o percurso com F5.")]
            for index,issue in enumerate(issues[modal["scroll"]:modal["scroll"]+6]):
                y = 198+index*62
                color = (246,139,157) if issue.severity == "error" else (243,205,134) if issue.severity == "warning" else (128,229,195)
                self.wrapped(issue.message,257,y,650,color,self.font,21)
                if issue.position or issue.room_id:
                    def focus(issue=issue):
                        self.close_validation()
                        if issue.room_id and isinstance(self.document,WorldDocument):
                            self.switch_room(issue.room_id)
                        if issue.position:
                            self.camera = [issue.position[0]-200,issue.position[1]-180]
                            self.clamp_camera()
                            self.selected = self.document.pick(issue.position[0]+1,issue.position[1]+1)
                    self.button("Ver",(948,y,65,29),focus)
            self.text("Uma solução exige todos os cristais e uma saída na mesma rota." if self.document.profile == "classic" else "Aventura: voo e bordas com repetição real; combate exige teste manual." if self.document.profile=="adventure" else "Perfil avançado: validação estrutural; solução automática ainda não disponível.",257,587)
            self.text("Roda para percorrer os resultados.",257,609,(126,152,172))
            if self.analysis_result is not None and self.analysis_result.status == "solved":
                self.button("Ver solução",(691,633,153,33),self.start_solution)
            self.button("Cancelar" if self.analysis is not None else "Fechar",(868,633,145,33),self.close_validation)
        else:
            self.text("Escreve o valor ou caminho e prime Enter. Ctrl+A seleciona tudo.",257,191)
            rect = pygame.Rect(257,222,756,44)
            pygame.draw.rect(self.screen,(9,18,32),rect,border_radius=4)
            pygame.draw.rect(self.screen,(106,205,190),rect,1,border_radius=4)
            self.screen.set_clip(rect.inflate(-12,-6))
            font = self.font
            cursor_width = font.size(modal["text"][:modal["cursor"]])[0]
            offset = max(0,cursor_width-720)
            if modal["select_all"]:
                pygame.draw.rect(self.screen,(43,80,108),(265,230,min(736,font.size(modal["text"])[0]),26))
            self.text(modal["text"],265-offset,231,(231,243,243),font)
            pygame.draw.line(self.screen,(199,244,223),(265+cursor_width-offset,230),(265+cursor_width-offset,257))
            self.screen.set_clip(None)
            if kind == "open":
                self.text("MAPAS LOCAIS — clica para preencher o caminho",257,290,(119,215,193))
                paths = sorted(self.default_path.parent.glob("*.json"))
                examples = [Path(p) for p in ("examples/classic/assets/station.json","examples/precision/assets/ascent.json","examples/rooms/assets/world.json") if Path(p).exists()]
                paths = paths[:4]+examples
                for index,path in enumerate(paths):
                    def choose(path=path):
                        modal["text"] = str(path)
                        modal["cursor"] = len(str(path))
                        modal["select_all"] = True
                    self.button(str(path)[-80:],(257,317+index*32,756,27),choose)
            if modal["error"]:
                self.wrapped(modal["error"],257,551,750,(247,148,160),self.small,18)
            self.button("Confirmar",(691,625,153,38),self.submit_modal)
            self.button("Cancelar",(859,625,153,38),lambda:setattr(self,"modal",None))

    def draw(self):
        if self.workspace:
            self.workspace.draw()
            return
        self.buttons = []
        self.screen.fill((13,22,37))
        if self.preview:
            prefix = "SOLUÇÃO AUTOMÁTICA / " if self.solution_actions is not None else "TESTAR / "
            self.text(prefix+self.document.data.get("name","Sala"),30,23,(130,232,203),self.title)
            if self.solution_actions is not None:
                self.text("F5 ou ESC: voltar ao editor  |  Rota confirmada com a física e os objetivos deste nível",30,68)
            else:
                self.text("F5 ou ESC: voltar ao editor  |  F3: configurar comandos do teste",30,68)
            size = self.profiles.get(self.document.profile,{}).get("size",(960,540))
            surface = pygame.Surface(size)
            self.preview.draw(surface,self.accumulator/(1/60))
            if self.controls and self.solution_actions is None:
                self.controls.draw_hint(surface)
            scale = min(1152/size[0],648/size[1])
            target = (round(size[0]*scale),round(size[1]*scale))
            self.screen.blit(pygame.transform.smoothscale(surface,target),((1280-target[0])//2,111))
        else:
            self.text("ATELIER / 22",18,18,(115,224,196),self.title)
            self.text("PLATFORM2D · EDITOR",18,54,(128,156,182))
            actions = [("Novo",self.new_dialog),
                       ("Abrir",self.open_dialog),("Guardar",self.save),("Guardar como",lambda:self.save(True)),
                       ("Desfazer",lambda:(self.document.undo(),setattr(self,"selected",None),self.refresh())),
                       ("Refazer",lambda:(self.document.redo(),setattr(self,"selected",None),self.refresh())),
                       ("Validar [F8]",self.show_validation),("Testar [F5]",self.start_preview)]
            for i,(label,callback) in enumerate(actions):
                self.button(label,(251+i*126,22,118,37),callback)
            name = self.document.data.get("name","Sala")
            self.text(("● " if self.document.dirty else "✓ ")+name[:40],201,79,(224,236,241))
            self.button("Nome",(561,73,66,27),lambda:self.input_dialog("Nome do nível",name,lambda text:(self.document.rename(text),self.refresh())))
            self.button("Tamanho",(635,73,83,27),self.resize_dialog)
            for label,field,x in (("Tiles","show_tiles",728),("Objetos","show_objects",808),("Grelha","show_grid",901)):
                self.button(label,(x,73,74 if label != "Objetos" else 85,27),lambda field=field:setattr(self,field,not getattr(self,field)),getattr(self,field))
            self.button("-",(1052,73,30,27),lambda:self.set_zoom(1/1.2))
            self.text(f"{self.zoom:.0%}",1093,80)
            self.button("+",(1150,73,30,27),lambda:self.set_zoom(1.2))
            self.button("1:1",(1190,73,70,27),lambda:self.set_zoom(1/self.zoom))
            self.text("FERRAMENTAS",18,113,(111,223,192))
            tool_list=self.tools()
            spacing=min(25,350/max(1,len(tool_list)-1))
            for index,(tool,label) in enumerate(tool_list):
                self.button(label,(16,142+index*spacing,167,spacing-2),lambda tool=tool:self.choose_tool(tool),self.tool == tool)
            self.text("PERFIL: "+PROFILE_NAMES[self.document.profile],18,542,(111,223,192))
            if isinstance(self.document,WorldDocument):
                self.button("Salas…",(16,567,167,32),self.room_dialog)
                self.text(self.document.active_room[:22],18,608)
            elif self.document.profile in {"ranged","adventure"}:
                self.button("Arma do jogador…",(16,567,167,32),self.ranged_properties)
                self.button("Missão / ambiente…",(16,604,167,25),self.mission_properties)
            else:
                self.wrapped("Arrasta para pintar. Botão direito apaga.",18,570,166,font=self.small,line_height=19)
            self.wrapped("Roda: zoom\nBotão central: mover\nAlt: sem grelha",18,632,166,font=self.small,line_height=18)
            self.text(f"{self.document.size[0]} × {self.document.size[1]} tiles",18,692)
            self.draw_canvas()
            self.draw_inspector()
            errors = sum(i.severity == "error" for i in self.issues)
            warnings = sum(i.severity == "warning" for i in self.issues)
            self.text(f"{errors} erros / {warnings} avisos",18,745,(247,153,159) if errors else (128,222,188))
            self.text(self.status[:121],201,745)
            path = str(self.document.path) if self.document.path else "Ainda sem ficheiro · Ctrl+S para guardar"
            self.text(path[-140:],18,776,(112,143,167))
        if self.modal:
            self.draw_modal()
        if self.audio_controls:
            self.audio_controls.draw(self.screen)
        if self.controls and self.solution_actions is None:
            self.controls.draw(self.screen)

    def run(self,max_frames=None,screenshot=None):
        clock = pygame.time.Clock()
        frames = 0
        try:
            self.draw()
            while self.running:
                dt = clock.tick(60)/1000
                for event in pygame.event.get():
                    self.guard(lambda event=event:self.handle_event(event))
                self.update(dt)
                self.draw()
                pygame.display.flip()
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    break
            if screenshot:
                Path(screenshot).parent.mkdir(parents=True,exist_ok=True)
                pygame.image.save(self.screen,str(screenshot))
        finally:
            active=self
            while active is not None:
                if active.controls: active.controls.close()
                active=getattr(active,'workspace',None) or getattr(active,'map_editor',None)
            self.audio.close()
            pygame.quit()
