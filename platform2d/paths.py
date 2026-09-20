"""Per-application writable data, never beside an installed executable."""
import os
from pathlib import Path
import re
import sys


def user_data_dir(application):
    if not isinstance(application,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',application):
        raise ValueError('Application ID must contain only letters, numbers, underscore or hyphen.')
    if sys.platform=='win32': root=Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))
    elif sys.platform=='darwin': root=Path.home()/'Library/Application Support'
    else: root=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
    return root/application
