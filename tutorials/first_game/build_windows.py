"""Run in this directory after installing PyInstaller and Platform2D."""
import subprocess,sys
from pathlib import Path

root=Path(__file__).resolve().parent
if sys.platform!='win32': raise SystemExit('Cria a versão Windows num computador Windows.')
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--noupx','--onedir','--windowed',
                '--name','OPrimeiroJogo','--collect-data','platform2d.audio',str(root/'main.py')],cwd=root,check=True)
