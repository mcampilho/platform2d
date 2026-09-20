"""Atomic, bounded JSON storage with validation before reads and replacement."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from .progress import unique_object,fail


class JsonSlot:
    MAX_BYTES = 2*1024*1024

    def __init__(self,path=None):
        self.path = Path(path) if path is not None else None
        self.memory = None

    @property
    def exists(self):
        return self.path.exists() if self.path is not None else self.memory is not None

    def read(self,validate):
        if self.path is None:
            if self.memory is None:
                raise ValueError("Ainda não existe gravação.")
            return validate(deepcopy(self.memory))
        try:
            with self.path.open('rb') as handle:
                raw = handle.read(self.MAX_BYTES+1)
            if len(raw)>self.MAX_BYTES:
                raise ValueError("Gravação demasiado grande.")
            data = json.loads(raw.decode('utf-8-sig'),object_pairs_hook=unique_object,
                              parse_constant=lambda value:fail("Número não finito na gravação."))
        except FileNotFoundError as error:
            raise ValueError("Ainda não existe gravação.") from error
        except (UnicodeError,json.JSONDecodeError,RecursionError) as error:
            raise ValueError("Ficheiro de gravação inválido; foi preservado.") from error
        return validate(data)

    def write(self,payload,validate):
        data = validate(deepcopy(payload))
        if self.exists:
            self.read(validate)  # Preserve unrelated, incompatible or corrupt files.
        raw = json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        if len(raw.encode('utf-8'))>self.MAX_BYTES:
            raise ValueError("Gravação demasiado grande.")
        if self.path is None:
            self.memory = data
            return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=self.path.parent,suffix='.tmp',delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(raw); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary,self.path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
