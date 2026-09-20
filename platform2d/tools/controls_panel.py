"""A modal command editor shared by games and Atelier previews."""
from copy import deepcopy
import re
import pygame
from platform2d.i18n import InterfaceText
from platform2d.core.input import Input
from platform2d.core.gamepad import Gamepads
from platform2d.core.control_settings import ControlSettings, BUTTONS, DIRECTIONS, button_codes, validate

class ControlsPanel:
    def __init__(self, bindings, profile="custom", path=None, language="pt-PT"):
        self.locale = InterfaceText(language)
        self.language = self.locale.language
        self.t = self.locale.t
        self.labels = {action:self.t('action.'+action) if 'action.'+action in self.locale.translator.metadata['messages'] else action for action in bindings}
        self.settings = ControlSettings(bindings,profile,path)
        data = self.settings.data
        self.input = Input(data["keys"],button_codes(data),data["deadzone"])
        self.gamepads = Gamepads(self.input)
        self.open = False
        self.capture = False
        self.row = self.column = 0
        self.actions = list(bindings)
        self.message = self.t('invalid_preferences') if self.settings.warning else ''
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
        return self.key_label(key)

    def key_label(self,key):
        ident='key.'+key.replace(' ','_')
        return self.t(ident) if ident in self.locale.translator.metadata['messages'] else key.upper()

    def set_language(self,language):
        self.locale.translator.select(language)
        self.language=self.locale.language
        self.labels={action:self.t('action.'+action) if 'action.'+action in self.locale.translator.metadata['messages'] else action for action in self.actions}
        self.capture=False
        self.message=self.t('invalid_preferences' if self.settings.warning else 'select_cell')

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
            self.message = self.t('invalid_preferences') if self.settings.warning else self.t('select_cell')

    def save(self):
        try:
            self.settings.save(self.draft)
        except (OSError,ValueError) as error:
            self.message = self.locale.legacy_error(error)
            return
        self.input.configure(self.draft["keys"],button_codes(self.draft),self.draft["deadzone"])
        self.open = self.capture = False

    def restore(self):
        self.draft = deepcopy(self.settings.defaults)
        self.capture = False
        self.message = self.t('restored')

    def begin_capture(self):
        if self.column == 2 and self.actions[self.row] in DIRECTIONS:
            self.message = self.t('movement_reserved')
            return
        self.capture = True
        self.message = self.t('press_key' if self.column < 2 else 'press_button')

    def assign(self, value):
        candidate = deepcopy(self.draft)
        action = self.actions[self.row]
        if self.column == 2:
            candidate["buttons"][action] = value
        else:
            keys = candidate["keys"][action]
            if value is None:
                if self.column == 0:
                    self.message = self.t('primary_required')
                    return
                candidate["keys"][action] = keys[:1]
            elif self.column < len(keys):
                keys[self.column] = value
            else:
                keys.append(value)
        try:
            validate(candidate,self.settings.defaults["keys"])
        except ValueError as error:
            self.message = self.locale.legacy_error(error)
            return
        self.draft = candidate
        self.capture = False
        self.message = self.t('changed')

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
                    self.message = self.t('cancelled')
                elif self.column < 2:
                    self.assign(pygame.key.name(event.key))
            elif self.column == 2 and event.type == pygame.CONTROLLERBUTTONDOWN and event.instance_id == self.input.device:
                label = next((k for k,v in BUTTONS.items() if v == event.button),None)
                if label is None:
                    self.message = self.t('dpad_reserved')
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
        pairs=[self.label(action)+': '+self.labels[action].lower()
               for action in ('left','right','jump','dash','attack','shoot','interact','use_item','pause')
               if action in self.settings.data['keys']]
        text=' · '.join(pairs)+' | '+self.t('hint')
        pygame.draw.rect(surface,(12,22,35),(0,surface.get_height()-29,surface.get_width(),29))
        self.locale.box(surface,text,(12,surface.get_height()-27,surface.get_width()-24,27),13)

    def draw(self, surface):
        if not self.open:
            if self.settings.warning:
                self.locale.box(surface,self.t('invalid_preferences')+' '+self.t('hint'),(20,86,surface.get_width()-40,30))
            return
        shade=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
        shade.fill((3,9,19,225)); surface.blit(shade,(0,0))
        width,height=900,520
        x,y=(surface.get_width()-width)//2,(surface.get_height()-height)//2
        pygame.draw.rect(surface,(18,31,47),(x,y,width,height),border_radius=12)
        def rect(dx,dy,w,h=24):
            return pygame.Rect(x+(width-dx-w if self.locale.rtl else dx),y+dy,w,h)
        def text(value,dx,dy,w=856,size=15,color=(201,218,229)):
            return self.locale.box(surface,value,rect(dx,dy,w),size,color)
        profile_key='profile.'+self.settings.profile
        profile=self.t(profile_key) if profile_key in self.locale.translator.metadata['messages'] else self.settings.profile
        text(self.t('header')+' · '+profile,22,10,750,size=23,color=(128,231,199))
        device=self.gamepads.devices.get(self.input.device)
        device_name=device.name if device else self.t('gamepad_error' if self.gamepads.error else 'no_gamepad')
        text(device_name,22,47,size=16)
        text(self.t('select'),22,76,size=13)
        for label,dx,w in (('action',22,210),('primary',250,175),('alternate',440,175),('gamepad',630,240)):
            text(self.t(label),dx,102,w,size=14,color=(132,159,184))
        self.cells,self.buttons=[],[]
        row_height=27
        first=max(0,self.row-9)
        text(f'{first+1}-{min(first+10,len(self.actions))}/{len(self.actions)}',790,15,90,size=13)
        for row in range(first,min(first+10,len(self.actions))):
            action=self.actions[row]
            yy=128+(row-first)*row_height
            text(self.labels[action],22,yy,210,size=13)
            keys=self.draft['keys'][action]
            values=[self.key_label(keys[0]),self.key_label(keys[1]) if len(keys)>1 else '—',
                    self.t('movement') if action in DIRECTIONS else self.draft['buttons'][action] or '—']
            for column,value in enumerate(values):
                cell=rect(244+column*190,yy-2,183,min(24,row_height))
                selected=row==self.row and column==self.column
                pygame.draw.rect(surface,(42,87,85) if selected else (27,44,61),cell,border_radius=3)
                text('...' if selected and self.capture else value,250+column*190,yy,170,size=13)
                self.cells.append((cell,row,column))
        text(self.message,22,421,size=14,color=(255,206,136))
        text(self.t('deadzone',value=round(self.draft['deadzone']*100)),22,459,170,size=13)
        def zone(delta):
            self.draft['deadzone']=round(max(.2,min(.7,self.draft['deadzone']+delta)),2)
        for label,dx,w,callback in (('-',200,35,lambda:zone(-.05)),('+',245,35,lambda:zone(.05)),
                                    (self.t('restore'),310,170,self.restore),
                                    (self.t('cancel'),490,170,self.toggle),(self.t('save'),670,190,self.save)):
            button=rect(dx,450,w,34)
            pygame.draw.rect(surface,(37,82,79),button,border_radius=5)
            image=self.locale.render(label,15,(216,241,230),w-12)
            surface.blit(image,image.get_rect(center=button.center))
            self.buttons.append((button,callback))
        text(self.t('footer'),22,494,size=12)

    def close(self):
        self.gamepads.close()
