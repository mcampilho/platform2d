"""Campaign authoring: absolute working references, relative atomic exports."""
from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from .editor_model import MapDocument,Issue

FORMAT='platform2d.campaign'

@dataclass
class StageReport:
    name: str
    profile: str
    document: object
    issues: list

class CampaignDocument:
    def __init__(self,data=None,path=None,base=None):
        data=deepcopy(data) if data is not None else dict(format=FORMAT,version=1,name='A minha campanha',stages=[])
        if not isinstance(data,dict) or data.get('format')!=FORMAT or type(data.get('version')) is not int or data['version']!=1:
            raise ValueError('Formato de campanha incompatível.')
        if not isinstance(data.get('name'),str) or not isinstance(data.get('stages'),list):
            raise ValueError('A campanha precisa de nome e de uma lista de etapas.')
        self.path=Path(path).expanduser().resolve() if path else None
        root=self.path.parent if self.path else Path(base or '.').resolve()
        for stage in data['stages']:
            if not isinstance(stage,dict) or not isinstance(stage.get('id'),str) or not isinstance(stage.get('map'),str) or not stage['map'].strip():
                raise ValueError('Cada etapa precisa de ID e caminho de mapa.')
            stage['map']=str((root/Path(stage['map']).expanduser()).resolve())
        self.data=data; self.saved=self.snapshot() if path else None
        self.undo_stack=[]; self.redo_stack=[]

    @classmethod
    def load(cls,path):
        path=Path(path).expanduser().resolve()
        return cls(json.loads(path.read_text(encoding='utf-8-sig')),path)

    def snapshot(self): return deepcopy(self.data)
    @property
    def dirty(self): return self.data!=self.saved

    def change(self,callback):
        before=self.snapshot()
        try: callback()
        except Exception:
            self.data=before; raise
        if before!=self.data:
            self.undo_stack.append(before); self.undo_stack=self.undo_stack[-100:]; self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.snapshot()); self.data=self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.snapshot()); self.data=self.redo_stack.pop()

    def rename(self,name):
        if not name.strip(): raise ValueError('Escolhe um nome para a campanha.')
        self.change(lambda:self.data.update(name=name.strip()))

    def rename_stage(self,index,ident):
        ident=ident.strip()
        if not ident or any(s['id']==ident for i,s in enumerate(self.data['stages']) if i!=index):
            raise ValueError('Escolhe um ID não vazio e único.')
        self.change(lambda:self.data['stages'][index].update(id=ident))

    def add(self,path):
        if len(self.data['stages'])>=32: raise ValueError('Máximo de 32 etapas.')
        path=Path(path).expanduser().resolve()
        doc=MapDocument.load(path)
        if doc.profile not in {'ranged','adventure'}: raise ValueError('Escolhe um mapa Combate ou Aventura.')
        ident=path.stem; used={s['id'] for s in self.data['stages']}; number=2
        while ident in used: ident=f'{path.stem}-{number}'; number+=1
        self.change(lambda:self.data['stages'].append(dict(id=ident,map=str(path))))
        return len(self.data['stages'])-1

    def replace(self,index,path):
        path=Path(path).expanduser().resolve(); doc=MapDocument.load(path)
        if doc.profile not in {'ranged','adventure'}: raise ValueError('Escolhe um mapa Combate ou Aventura.')
        self.change(lambda:self.data['stages'][index].update(map=str(path)))

    def remove(self,index): self.change(lambda:self.data['stages'].pop(index))

    def move(self,index,target):
        if not 0<=target<len(self.data['stages']): return index
        def apply(): self.data['stages'].insert(target,self.data['stages'].pop(index))
        self.change(apply); return target

    def inspect(self):
        issues=[]; reports=[]; stages=self.data['stages']; used=set()
        if not self.data['name'].strip(): issues.append(Issue('error','A campanha precisa de nome.'))
        if not 1<=len(stages)<=32: issues.append(Issue('error','A campanha precisa de 1 a 32 etapas.'))
        for index,stage in enumerate(stages):
            local=[]; doc=None; name=Path(stage['map']).stem; profile='—'
            if not stage['id'].strip() or stage['id'] in used:
                local.append(Issue('error','ID vazio ou repetido.'))
            used.add(stage['id'])
            try:
                doc=MapDocument.load(stage['map']); name=doc.data['name']; profile=doc.profile
                if profile not in {'ranged','adventure'}: local.append(Issue('error','Perfil incompatível: usa Combate ou Aventura.'))
                local.extend(doc.validate())
            except (OSError,ValueError,TypeError,KeyError) as error:
                local.append(Issue('error',str(error).splitlines()[0]))
            reports.append(StageReport(name,profile,doc,local))
            issues.extend(Issue(i.severity,f'{index+1}. {stage["id"]}: {i.message}') for i in local)
        return reports,issues

    def playable(self,start=0):
        reports,issues=self.inspect()
        errors=[i.message for i in issues if i.severity=='error']
        if errors: raise ValueError('\n'.join(errors))
        if not 0<=start<len(reports): raise ValueError('Etapa inicial inválida.')
        return self.data['name'],[s['id'] for s in self.data['stages'][start:]],[r.document for r in reports[start:]]

    def save(self,path=None):
        target=Path(path or self.path or '').expanduser().resolve()
        if target.suffix.lower()!='.json': raise ValueError('Escolhe um ficheiro .json.')
        if any(target==Path(s['map']) for s in self.data['stages']):
            raise ValueError('A campanha não pode substituir um dos seus mapas.')
        self.playable()
        data=self.snapshot()
        for stage in data['stages']:
            try: stage['map']=Path(os.path.relpath(stage['map'],target.parent)).as_posix()
            except ValueError: stage['map']=Path(stage['map']).as_posix()
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,suffix='.tmp',delete=False) as handle:
                temporary=Path(handle.name); json.dump(data,handle,ensure_ascii=False,indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary,target)
        finally:
            if temporary is not None and temporary.exists(): temporary.unlink()
        self.path=target; self.saved=self.snapshot(); return target
