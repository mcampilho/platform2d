"""A modal command editor shared by games and Atelier previews."""
from copy import deepcopy
import re
import pygame
from platform2d.core.input import Input
from platform2d.core.gamepad import Gamepads
from platform2d.core.control_settings import ControlSettings, BUTTONS, DIRECTIONS, button_codes, validate

LABELS = {"left":"Esquerda","right":"Direita","up":"Subir","down":"Descer",
          "jump":"Saltar","dash":"Dash","guard":"Defender","attack":"Atacar","shoot":"Disparar","use_item":"Usar kit","continue":"Próximo nível","interact":"Interagir",
          "restart":"Checkpoint","reset":"Recomeçar","debug":"Diagnóstico","pause":"Pausa",
          "step":"Avançar um passo","save_progress":"Guardar progresso","load_progress":"Carregar progresso"}
KEY_LABELS = {"space":"Espaço","left":"←","right":"→","up":"↑","down":"↓",
              "left shift":"Shift esq.","right shift":"Shift dir.","left ctrl":"Ctrl esq.","right ctrl":"Ctrl dir."}
PROFILE_LABELS = {"campaign_editor":"Teste de campanha","classic":"Clássico","rooms":"Salas","precision":"Precisão","sentinels":"Sentinelas","ranged":"Combate","campaign":"Campanha","adventure":"Aventura","custom":"Personalizado"}


class ControlsPanel:
    def __init__(self, bindings, profile="custom", path=None):
        self.settings = ControlSettings(bindings,profile,path)
        data = self.settings.data
        self.input = Input(data["keys"],button_codes(data),data["deadzone"])
        self.gamepads = Gamepads(self.input)
        self.open = False
        self.capture = False
        self.row = self.column = 0
        self.actions = list(bindings)
        self.message = self.settings.warning
        self.draft = deepcopy(data)
        self.cells = []
        self.buttons = []
        self.last_device = "keyboard"

    def label(self, action):
        data = self.settings.data
        button = data["buttons"].get(action)
        if self.last_device == "gamepad" and button:
            return button
        key = data["keys"].get(action,[action])[0]
        return KEY_LABELS.get(key,key.upper())

    def format_hint(self, text):
        actions = {"F1":"debug","F2":"reset","F6":"save_progress","F9":"load_progress",
                   "P":"pause","N":"step","E":"interact","R":"restart","L":"guard","J":"attack","H":"use_item","Enter":"continue"}
        pattern = r"\[(E|J|L|H|Enter)\]|\b(F1|F2|F6|F9|P(?= para)|N(?=:| para)|E(?=:)|R(?=:))\b"
        def replace(match):
            token = match.group(1) or match.group(2)
            action = actions[token]
            if action not in self.settings.data["keys"]:
                return match.group(0)
            value = self.label(action)
            return "["+value+"]" if match.group(1) else value
        return re.sub(pattern,replace,str(text))

    def toggle(self):
        self.open = not self.open
        self.capture = False
        self.input.clear()
        if self.open:
            self.draft = deepcopy(self.settings.data)
            self.message = self.settings.warning or "Seleciona uma célula e carrega Enter para alterar."

    def save(self):
        try:
            self.settings.save(self.draft)
        except (OSError,ValueError) as error:
            self.message = str(error)
            return
        self.input.configure(self.draft["keys"],button_codes(self.draft),self.draft["deadzone"])
        self.open = self.capture = False

    def restore(self):
        self.draft = deepcopy(self.settings.defaults)
        self.capture = False
        self.message = "Comandos de origem preparados. Guarda para aplicar."

    def begin_capture(self):
        if self.column == 2 and self.actions[self.row] in DIRECTIONS:
            self.message = "Direcional e analógico esquerdo mantêm o movimento."
            return
        self.capture = True
        self.message = "Prime uma tecla." if self.column < 2 else "Prime um botão do gamepad ativo."

    def assign(self, value):
        candidate = deepcopy(self.draft)
        action = self.actions[self.row]
        if self.column == 2:
            candidate["buttons"][action] = value
        else:
            keys = candidate["keys"][action]
            if value is None:
                if self.column == 0:
                    self.message = "A tecla principal é obrigatória."
                    return
                candidate["keys"][action] = keys[:1]
            elif self.column < len(keys):
                keys[self.column] = value
            else:
                keys.append(value)
        try:
            validate(candidate,self.settings.defaults["keys"])
        except ValueError as error:
            self.message = str(error)
            return
        self.draft = candidate
        self.capture = False
        self.message = "Alteração preparada. Guarda para aplicar."

    def handle_event(self, event):
        self.gamepads.feed(event)
        self.input.feed([event])
        if event.type == pygame.KEYDOWN and self.input.focused:
            self.last_device = "keyboard"
        elif getattr(event,"instance_id",None) == self.input.device and self.input.device is not None and self.input.focused:
            if event.type == pygame.CONTROLLERBUTTONDOWN or (event.type == pygame.CONTROLLERAXISMOTION and abs(event.value)/32768 >= self.input.deadzone):
                self.last_device = "gamepad"
        if event.type == pygame.WINDOWFOCUSLOST:
            self.capture = False
        if self.input.focused and event.type == pygame.KEYDOWN and event.key == pygame.K_F3 and not getattr(event,"repeat",False):
            self.toggle()
            return True
        if not self.open:
            return False
        self.input.clear()
        if not self.input.focused:
            return True
        if self.capture:
            if event.type == pygame.KEYDOWN and not getattr(event,"repeat",False):
                if event.key == pygame.K_ESCAPE:
                    self.capture = False
                    self.message = "Alteração cancelada."
                elif self.column < 2:
                    self.assign(pygame.key.name(event.key))
            elif self.column == 2 and event.type == pygame.CONTROLLERBUTTONDOWN and event.instance_id == self.input.device:
                label = next((k for k,v in BUTTONS.items() if v == event.button),None)
                if label is None:
                    self.message = "O direcional está reservado ao movimento."
                else:
                    self.assign(label)
            return True
        if event.type == pygame.KEYDOWN and not getattr(event,"repeat",False):
            if event.key == pygame.K_ESCAPE:
                self.toggle()
            elif event.key == pygame.K_UP:
                self.row = (self.row-1)%len(self.actions)
            elif event.key == pygame.K_DOWN:
                self.row = (self.row+1)%len(self.actions)
            elif event.key in (pygame.K_TAB,pygame.K_RIGHT,pygame.K_LEFT):
                self.column = (self.column+(-1 if event.key == pygame.K_LEFT else 1))%3
            elif event.key == pygame.K_RETURN:
                self.begin_capture()
            elif event.key in (pygame.K_DELETE,pygame.K_BACKSPACE):
                if self.column != 2 or self.actions[self.row] not in DIRECTIONS:
                    self.assign(None)
            elif event.key == pygame.K_s and getattr(event,"mod",0)&pygame.KMOD_CTRL:
                self.save()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect,row,column in self.cells:
                if rect.collidepoint(event.pos):
                    self.row,self.column = row,column
                    self.begin_capture()
                    return True
            for rect,callback in self.buttons:
                if rect.collidepoint(event.pos):
                    callback()
                    break
        return True

    def draw_hint(self, surface):
        font = pygame.font.SysFont("consolas",13)
        pairs = []
        for action in ("left","right","jump","dash","attack","shoot","interact","use_item","pause"):
            if action in self.settings.data["keys"]:
                label = "←" if action == "left" and self.last_device == "gamepad" else "→" if action == "right" and self.last_device == "gamepad" else self.label(action)
                pairs.append(label+": "+LABELS[action].lower())
        text = "   ".join(pairs)+"   |   F3: comandos"
        pygame.draw.rect(surface,(12,22,35),(0,surface.get_height()-27,surface.get_width(),27))
        rendered = font.render(text,True,(170,209,214))
        if rendered.get_width() > surface.get_width()-24:
            rendered = pygame.transform.smoothscale(rendered,(surface.get_width()-24,rendered.get_height()))
        surface.blit(rendered,(12,surface.get_height()-21))

    def draw(self, surface):
        if not self.open:
            if self.settings.warning:
                font = pygame.font.SysFont("segoeui",16)
                notice = font.render(self.settings.warning+" F3: comandos",True,(255,205,130))
                pygame.draw.rect(surface,(12,22,35),(12,82,notice.get_width()+16,28))
                surface.blit(notice,(20,86))
            return
        shade = pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        shade.fill((3,9,19,225))
        surface.blit(shade,(0,0))
        width,height = 900,520
        x,y = (surface.get_width()-width)//2,(surface.get_height()-height)//2
        pygame.draw.rect(surface,(18,31,47),(x,y,width,height),border_radius=12)
        font = pygame.font.SysFont("segoeui",16)
        small = pygame.font.SysFont("consolas",13)
        def text(value,dx,dy,color=(201,218,229),face=font):
            surface.blit(face.render(value,True,color),(x+dx,y+dy))
        text("COMANDOS · "+PROFILE_LABELS.get(self.settings.profile,self.settings.profile).upper(),22,14,(128,231,199),pygame.font.SysFont("segoeui",23,bold=True))
        text(self.gamepads.name[:90],22,49)
        text("Setas / Tab: selecionar   Enter: alterar   Delete: limpar alternativa/botão   Esc: cancelar",22,75,face=small)
        for label,dx in (("Ação",22),("Tecla principal",250),("Alternativa",440),("Gamepad",630)):
            text(label,dx,102,(132,159,184),small)
        self.cells,self.buttons = [],[]
        row_height=min(22,278/max(1,len(self.actions)-1))
        for row,action in enumerate(self.actions):
            yy = 125+row*row_height
            text(LABELS.get(action,action),22,yy,face=small)
            keys = self.draft["keys"][action]
            values = [KEY_LABELS.get(keys[0],keys[0].upper()),KEY_LABELS.get(keys[1],keys[1].upper()) if len(keys)>1 else "—","direcional / analógico" if action in DIRECTIONS else self.draft["buttons"][action] or "—"]
            for column,value in enumerate(values):
                rect = pygame.Rect(x+244+column*190,y+yy-2,183,min(21,row_height-1))
                selected = row == self.row and column == self.column
                pygame.draw.rect(surface,(42,87,85) if selected else (27,44,61),rect,border_radius=3)
                text("..." if selected and self.capture else value,250+column*190,yy,face=small)
                self.cells.append((rect,row,column))
        text(self.message[:111],22,426,(255,206,136),small)
        text(f"Zona morta: {self.draft['deadzone']:.0%}",22,453,face=small)
        def zone(delta):
            self.draft["deadzone"] = round(max(.2,min(.7,self.draft["deadzone"]+delta)),2)
        for label,dx,w,callback in (("−",200,35,lambda:zone(-.05)),("+",245,35,lambda:zone(.05)),
                                     ("Repor origem",350,140,self.restore),("Cancelar",510,120,self.toggle),("Guardar",650,210,self.save)):
            rect = pygame.Rect(x+dx,y+449,w,32)
            pygame.draw.rect(surface,(37,82,79),rect,border_radius=5)
            image = font.render(label,True,(216,241,230))
            surface.blit(image,image.get_rect(center=rect.center))
            self.buttons.append((rect,callback))
        text("A/B/X/Y seguem as posições Xbox. Analógico: centrar após perder o foco.  Ctrl+S: guardar",22,493,face=small)

    def close(self):
        self.gamepads.close()
