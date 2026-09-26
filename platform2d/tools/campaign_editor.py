"""Atelier campaign workspace; game preview supplied by the host."""
from pathlib import Path
import pygame
from .level_editor import LevelEditor,PROFILE_NAMES,COLORS
from .campaign_model import CampaignDocument
from .controls_panel import ControlsPanel
from .editor_model import MapDocument

class CampaignEditor(LevelEditor):
    def __init__(self,campaign,profiles,default_path='levels/minha-campanha.json',audio=None,controls_dir=None,on_close=None,language='pt-PT'):
        self.campaign=campaign; self.stage_index=0; self.scroll=0; self.map_editor=None; self.on_close=on_close
        classic=profiles['classic']
        super().__init__(classic['factory'],classic['bindings'],profiles=profiles,default_path=default_path,audio=audio,controls_dir=controls_dir,language=language)
        self.status='Escolhe etapas, organiza a sequência e testa com F5.'
        pygame.display.set_caption(self.locale.t('editor.campaign_caption'))

    def refresh(self):
        self.reports,self.issues=self.campaign.inspect()
        self.structural_issues=self.issues
        self.stage_index=max(0,min(self.stage_index,len(self.reports)-1))
        self.scroll=max(0,min(self.scroll,max(0,len(self.reports)-7)))

    def finish_edit(self): pass

    def protect_unsaved(self,action):
        if not self.campaign.dirty: action(); return
        self.confirm('Campanha por guardar','Queres guardar as alterações à sequência?',[
            ('Guardar',lambda:self.save(after=action)),('Descartar',action),('Cancelar',lambda:None)])

    def replace_campaign(self,doc):
        self.campaign=doc; self.stage_index=self.scroll=0; self.refresh()

    def new_dialog(self): self.protect_unsaved(lambda:self.replace_campaign(CampaignDocument()))

    def browse(self,title,callback,folder=None):
        folder=Path(folder or self.campaign.path and self.campaign.path.parent or 'examples/campaign/assets').expanduser().resolve()
        items=[('↑ Pasta anterior',lambda:self.browse(title,callback,folder.parent))]
        for path in sorted(folder.iterdir(),key=lambda p:(not p.is_dir(),p.name.lower())):
            if path.is_dir() and not path.name.startswith('.'):
                items.append(('Pasta / '+path.name,lambda path=path:self.browse(title,callback,path)))
            elif path.is_file() and path.suffix.lower()=='.json':
                items.append((path.name,lambda path=path:callback(path)))
        self.choice(title+' — '+folder.name,items,[('Escrever caminho…',lambda:self.input_dialog(title,str(folder),callback))])

    def open_dialog(self):
        def selected(path):
            doc=CampaignDocument.load(path)
            self.protect_unsaved(lambda:self.replace_campaign(doc))
        self.browse('Abrir campanha',selected)

    def add_stage(self):
        def selected(path):
            self.stage_index=self.campaign.add(path); self.scroll=max(0,self.stage_index-6); self.refresh()
        self.browse('Adicionar mapa',selected)

    def replace_stage(self):
        if not self.reports: return
        def selected(path): self.campaign.replace(self.stage_index,path); self.refresh()
        self.browse('Substituir referência do mapa',selected)

    def move_stage(self,target):
        if not self.reports: return
        self.stage_index=self.campaign.move(self.stage_index,target)
        self.scroll=max(0,min(self.scroll,self.stage_index))
        if self.stage_index>=self.scroll+7: self.scroll=self.stage_index-6
        self.refresh()

    def remove_stage(self):
        if not self.reports: return
        def remove(): self.campaign.remove(self.stage_index); self.refresh()
        self.confirm('Retirar etapa?','Retira apenas a referência da campanha. O ficheiro do mapa permanece disponível. Podes desfazer.',[
            ('Retirar',remove),('Cancelar',lambda:None)])

    def history(self,redo=False):
        (self.campaign.redo if redo else self.campaign.undo)(); self.refresh()

    def rename_campaign(self):
        def apply(name): self.campaign.rename(name); self.refresh()
        self.input_dialog('Nome da campanha',self.campaign.data['name'],apply)

    def rename_stage(self):
        if not self.reports: return
        def apply(ident): self.campaign.rename_stage(self.stage_index,ident); self.refresh()
        self.input_dialog('ID da etapa',self.campaign.data['stages'][self.stage_index]['id'],apply)

    def save(self,as_new=False,after=None):
        self.refresh()
        if any(i.severity=='error' for i in self.issues): self.show_validation(); return
        def write(path):
            target=Path(path).expanduser().resolve()
            def perform():
                self.campaign.save(target)
                self.status='Campanha guardada. Os mapas continuam nos seus ficheiros.'
                if after: after()
            if target.exists() and target!=self.campaign.path:
                self.confirm('Substituir campanha?',target.name,[('Substituir',perform),('Cancelar',lambda:None)])
            else: perform()
        if as_new or self.campaign.path is None:
            self.input_dialog('Guardar campanha como',str(self.campaign.path or self.default_path),write,'save')
        else: self.guard(lambda:write(self.campaign.path))

    def show_validation(self):
        self.refresh()
        self.choice('Validação da campanha',[(('ERRO · ' if i.severity=='error' else 'AVISO · ')+i.message,lambda issue=i:self.confirm('Detalhe da validação',issue.message,[('Voltar',self.show_validation)])) for i in self.issues] or [('Estrutura válida. Testa a sequência com F5.',lambda:None)])
        self.status='A validação estrutural não prova que todos os combates e percursos têm solução.'

    def start_preview(self,selected=False):
        name,ids,docs=self.campaign.playable(self.stage_index if selected else 0)
        profile=self.profiles['campaign']
        self.preview=profile['factory'](name,ids,docs)
        setter=getattr(self.preview,'set_language',None)
        if setter: setter(self.language)
        self.preview.audio=self.audio
        self.controls=ControlsPanel(profile['bindings'],'campaign_editor',language=self.language)
        self.preview.format_controls=self.controls.format_hint
        self.preview_input=self.controls.input; self.accumulator=0
        self.status='Teste desde a etapa selecionada.' if selected else 'Teste da campanha completa.'

    def stop_preview(self):
        super().stop_preview()
        self.status='Teste terminado. A sequência e as gravações de jogo foram preservadas.'

    def edit_map(self):
        if not self.reports: return
        path=Path(self.campaign.data['stages'][self.stage_index]['map'])
        doc=MapDocument.load(path)
        classic=self.profiles['classic']
        self.map_editor=LevelEditor(classic['factory'],classic['bindings'],doc,path,profiles={k:v for k,v in self.profiles.items() if k!='campaign'},audio=self.audio,controls_dir=self.controls_dir,language=self.language)
        self.map_editor.locale.extra=getattr(self.locale,'extra',None)

    def return_from_map(self):
        def leave():
            if self.map_editor.controls: self.map_editor.stop_preview()
            self.map_editor=None; self.refresh()
            pygame.display.set_caption(self.locale.t('editor.campaign_caption'))
        if self.map_editor.preview: self.map_editor.stop_preview()
        self.map_editor.protect_unsaved(leave)

    def handle_event(self,event):
        if self.map_editor:
            if event.type==pygame.QUIT or event.type==pygame.KEYDOWN and event.key==pygame.K_F4 and not self.map_editor.modal:
                self.return_from_map()
            else: self.map_editor.handle_event(event)
            return
        if event.type==pygame.QUIT:
            if self.preview: self.stop_preview()
            self.protect_unsaved(self.on_close or (lambda:setattr(self,'running',False))); return
        if self.audio_controls and self.audio_controls.handle_event(event): return
        if self.modal: self.handle_modal(event); return
        if self.preview:
            if self.controls.handle_event(event): self.accumulator=0; return
            if event.type==pygame.WINDOWFOCUSLOST: self.preview.active.paused=True
            if event.type==pygame.KEYDOWN and event.key in (pygame.K_F5,pygame.K_ESCAPE): self.stop_preview()
            return
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for rect,callback in reversed(self.buttons):
                if rect.collidepoint(event.pos): self.guard(callback); return
        if event.type==pygame.MOUSEWHEEL:
            self.scroll=max(0,min(max(0,len(self.reports)-7),self.scroll-event.y))
        if event.type==pygame.KEYDOWN:
            ctrl=getattr(event,'mod',0)&pygame.KMOD_CTRL; shift=getattr(event,'mod',0)&pygame.KMOD_SHIFT
            if ctrl:
                if event.key==pygame.K_s: self.save(bool(shift))
                elif event.key==pygame.K_o: self.open_dialog()
                elif event.key==pygame.K_n: self.new_dialog()
                elif event.key in (pygame.K_z,pygame.K_y): self.history(event.key==pygame.K_y or bool(shift))
            elif event.key==pygame.K_F5: self.start_preview()
            elif event.key==pygame.K_F6: self.start_preview(True)
            elif event.key==pygame.K_F8: self.show_validation()
            elif event.key==pygame.K_DELETE: self.remove_stage()
            elif event.key==pygame.K_F4 and self.on_close: self.protect_unsaved(self.on_close)
            elif event.key in (pygame.K_UP,pygame.K_DOWN):
                delta=1 if event.key==pygame.K_DOWN else -1
                if shift: self.move_stage(self.stage_index+delta)
                else:
                    self.stage_index=max(0,min(len(self.reports)-1,self.stage_index+delta))
                    self.scroll=max(0,min(self.scroll,self.stage_index))
                    if self.stage_index>=self.scroll+7: self.scroll=self.stage_index-6

    def update(self,dt):
        if self.map_editor: self.map_editor.update(dt)
        else: super().update(dt)

    def draw_thumbnail(self,doc):
        rect=pygame.Rect(848,525,374,94)
        pygame.draw.rect(self.screen,(8,16,28),rect,border_radius=4)
        data=doc.data; tile=doc.tile_size
        scale=min(rect.w/(doc.size[0]*tile),rect.h/(doc.size[1]*tile))
        ox=rect.x+(rect.w-doc.size[0]*tile*scale)/2
        for row,line in enumerate(data['tiles']):
            for col,cell in enumerate(line):
                if cell!='.': pygame.draw.rect(self.screen,(74,104,126),(ox+col*tile*scale,rect.y+row*tile*scale,max(1,tile*scale),max(1,tile*scale)))
        for obj in data.get('objects',[]):
            x=ox+obj['x']*scale; y=rect.y+obj['y']*scale
            if rect.collidepoint(x,y): pygame.draw.circle(self.screen,COLORS.get(obj['type'],(220,218,190)),(round(x),round(y)),2)

    def draw(self):
        if self.map_editor:
            self.map_editor.draw()
            self.text('F4: voltar à campanha',28,776,(129,226,201)); return
        self.buttons=[]; self.screen.fill((13,22,37))
        if self.preview:
            self.text('TESTAR CAMPANHA · '+self.campaign.data['name'][:55],30,22,(130,232,203),self.title)
            self.text('F5 / Esc: voltar · Enter: etapa seguinte após vencer · F3: comandos · P: pausa',30,67)
            surface=pygame.Surface((960,576)); self.preview.draw(surface,self.accumulator/(1/60))
            self.screen.blit(pygame.transform.smoothscale(surface,(1080,648)),(100,111))
        else:
            self.text('ATELIER / CAMPANHAS',28,24,(130,232,203),self.title)
            for i,(label,callback) in enumerate([('Nova',self.new_dialog),('Abrir',self.open_dialog),('Guardar',self.save),('Guardar como',lambda:self.save(True)),('Desfazer',self.history),('Refazer',lambda:self.history(True))]):
                self.button(label,(470+i*128,24,120,34),callback)
            self.text(('● ' if self.campaign.dirty else '✓ ')+self.locale.literal(self.campaign.data['name'])[:67],28,86,(224,237,242),self.title)
            self.button('Mudar nome',(1065,86,176,34),self.rename_campaign)
            self.text(self.locale.t('editor.stage_count',count=len(self.reports)),28,146,(125,157,180))
            self.text('A primeira etapa inicia a campanha. Roda para percorrer.',28,172)
            for row,index in enumerate(range(self.scroll,min(len(self.reports),self.scroll+7))):
                report=self.reports[index]; stage=self.campaign.data['stages'][index]; y=209+row*62
                color=(38,77,82) if index==self.stage_index else (24,39,55)
                pygame.draw.rect(self.screen,color,(28,y,780,54),border_radius=6)
                self.buttons.append((pygame.Rect(28,y,780,54),lambda index=index:setattr(self,'stage_index',index)))
                error=any(i.severity=='error' for i in report.issues)
                self.text(f'{index+1:02}'+(self.locale.literal(' INÍCIO') if index==0 else ''),40,y+9,(129,226,201))
                self.text(self.locale.literal(report.name)[:47],134,y+8,(237,222,227) if error else (221,236,241),self.font)
                self.text(stage['id'][:40]+' · '+self.locale.literal(PROFILE_NAMES.get(report.profile,report.profile)),134,y+32,(147,173,192))
                self.text('ERRO' if error else 'AVISO' if report.issues else 'OK',738,y+18,(245,151,158) if error else (237,204,138))
            if not self.reports: self.wrapped('Adiciona mapas de Combate ou Aventura para criar a tua campanha.',52,256,650)
            for i,(label,callback) in enumerate([('Adicionar mapa',self.add_stage),('Subir',lambda:self.move_stage(self.stage_index-1)),('Descer',lambda:self.move_stage(self.stage_index+1)),('Começar aqui',lambda:self.move_stage(0)),('Trocar mapa',self.replace_stage),('Mudar ID',self.rename_stage),('Editar mapa',self.edit_map),('Retirar etapa',self.remove_stage)]):
                self.button(label,(848+(i%2)*198,209+(i//2)*49,186,38),callback)
            if self.reports:
                path=self.campaign.data['stages'][self.stage_index]['map']
                self.text('MAPA SELECIONADO',848,428,(129,226,201))
                self.wrapped(path,848,455,374,font=self.small,line_height=20)
            if self.reports and self.reports[self.stage_index].document:
                self.draw_thumbnail(self.reports[self.stage_index].document)
            self.wrapped('Guardar como cria uma campanha que referencia os mesmos mapas. Editar mapa altera o ficheiro partilhado; usa Guardar como no editor do mapa e Trocar mapa aqui para criar uma cópia.',848,634,370,font=self.small,line_height=20)
            self.button('Validar [F8]',(28,684,180,42),self.show_validation)
            self.button('Testar tudo [F5]',(224,684,205,42),self.start_preview)
            self.button('Testar daqui [F6]',(445,684,205,42),lambda:self.start_preview(True))
            self.text('Shift+↑/↓: reordenar · Ctrl+S: guardar'+(' · F4: voltar ao mapa' if self.on_close else ''),28,744)
            self.text(self.status[:143],28,775,(129,226,201))
        if self.modal: self.draw_modal()
        if self.audio_controls: self.audio_controls.draw(self.screen)
        if self.controls: self.controls.draw(self.screen)
