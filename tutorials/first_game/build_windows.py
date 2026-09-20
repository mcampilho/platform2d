"""Run in this directory after installing PyInstaller and Platform2D."""
import argparse,subprocess,sys
from pathlib import Path
import platform2d

root=Path(__file__).resolve().parent
if sys.platform!='win32': raise SystemExit('Cria a versão Windows num computador Windows.')
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=root/'dist',help='Choose a fresh folder if OneDrive locks a previous build')
args=parser.parse_args()
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--noupx','--onedir','--windowed',
                '--distpath',str(args.output.resolve()),
                '--paths',str(Path(platform2d.__file__).resolve().parent.parent),
                '--specpath',str(root/'build'),
                '--name','OPrimeiroJogo','--collect-data','platform2d',
                '--add-data',f'{root / "locales"};locales',
                '--add-data',f'{root / "fonts"};fonts',str(root/'main.py')],cwd=root,check=True)
