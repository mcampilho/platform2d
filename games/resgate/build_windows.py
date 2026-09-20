"""Run with a Windows Python where the game, engine and PyInstaller are installed."""
import argparse,os,subprocess,sys
import platform2d,resgate
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=Path('dist'))
    args=parser.parse_args()
    if sys.platform!='win32': parser.error('A distribuição Windows deve ser construída em Windows.')
    output=args.output.resolve(); work=output.parent/'resgate-build'; work.mkdir(parents=True,exist_ok=True)
    entry=work/'launch.py'; entry.write_text('from resgate.__main__ import main\nif __name__ == "__main__": main()\n',encoding='utf-8')
    icon=Path(__file__).resolve().parent/'resgate/assets/icon.ico'
    env=dict(os.environ); env.pop('PYTHONPATH',None)
    env['PYINSTALLER_CONFIG_DIR']=str(work/'cache')
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--noupx','--onedir','--windowed',
                    '--paths',str(Path(platform2d.__file__).resolve().parent.parent),
                    '--paths',str(Path(resgate.__file__).resolve().parent.parent),
                    '--name','ResgateNaEstacao','--distpath',str(output),'--workpath',str(work/'work'),
                    '--specpath',str(work),'--collect-data','resgate','--collect-data','platform2d',
                    '--icon',str(icon),str(entry)],cwd=work,env=env,check=True)


if __name__=='__main__': main()
