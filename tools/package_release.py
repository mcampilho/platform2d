"""Assemble explicit public file sets. No saves, venvs or private preferences."""
import hashlib,json,shutil,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/releases'


def add_tree(zipfile_,source,prefix,extensions=None):
    for p in sorted(source.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or any(part.endswith('.egg-info') for part in p.parts): continue
        if extensions and p.suffix not in extensions: continue
        zipfile_.write(p,str(Path(prefix)/p.relative_to(source)))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    game=ROOT/'artifacts/windows-1.0.0/ResgateNaEstacao'
    assert (game/'ResgateNaEstacao.exe').is_file()
    assert (ROOT/'artifacts/resgate-final-check/verification.json').is_file()
    third=ROOT/'artifacts/third-party'
    licences=game/'licenses'; licences.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'LICENSE',licences/'Platform2D-MIT.txt')
    shutil.copy2(ROOT/'games/resgate/LICENSE',licences/'Resgate-MIT.txt')
    shutil.copy2(Path(sys.base_prefix)/'LICENSE.txt',licences/'Python-LICENSE.txt')
    shutil.copytree(third/'pygame',licences/'pygame',dirs_exist_ok=True)
    shutil.copy2(third/'pygame-2.6.1.tar.gz',licences/'pygame-2.6.1-source.tar.gz')
    shutil.copy2(ROOT/'games/resgate/README.md',game/'LEIA-ME.md')
    (game/'CREDITOS.txt').write_text('Resgate na Estação 1.0.0 / Platform2D 0.23.0\nCódigo, mapas e arte procedural: Miguel e colaboradores Platform2D (MIT).\nPython, Pygame, SDL e bibliotecas: respetivos autores. Ver licenses.\nPygame 2.6.1 sem modificações; código-fonte incluído.\nO SDK e o código do jogo permitem reconstruir a aplicação com bibliotecas modificadas compatíveis.\nEmpacotamento: PyInstaller 6.22.0, sem UPX. Windows x64; sem assinatura digital.\n',encoding='utf-8')
    sdk=OUT/'Platform2D-SDK-0.23.0.zip'
    with zipfile.ZipFile(sdk,'w',zipfile.ZIP_DEFLATED) as z:
        prefix='Platform2D-SDK-0.23.0'
        for name in ('platform2d-0.23.0-py3-none-any.whl','resgate_na_estacao-1.0.0-py3-none-any.whl'):
            z.write(ROOT/'artifacts/dist'/name,f'{prefix}/wheels/{name}')
        for name in ('using-platform2d.md','distributing-platform2d.md','learning-independent-game.md', 'first-game-tutorial.md', 'second-computer-test.md', 'publishing-github-pypi.md'):
            z.write(ROOT/'docs'/name,f'{prefix}/docs/{name}')
        z.write(ROOT/'LICENSE',f'{prefix}/LICENSE')
        z.write(ROOT/'docs/using-platform2d.md',f'{prefix}/LEIA-ME.md')
        add_tree(z,ROOT/'platform2d',f'{prefix}/engine-source/platform2d',{'.py','.tmpl','.wav'})
        z.write(ROOT/'pyproject.toml',f'{prefix}/engine-source/pyproject.toml')
        z.write(ROOT/'LICENSE',f'{prefix}/engine-source/LICENSE')
        z.write(ROOT/'MANIFEST.in',f'{prefix}/engine-source/MANIFEST.in')
        add_tree(z,ROOT/'tutorials/first_game',f'{prefix}/tutorials/first_game',{'.py','.md'})
        z.write(ROOT/'docs/using-platform2d.md',f'{prefix}/engine-source/docs/using-platform2d.md')
        # Explicit game sources, not its local build/egg-info directories.
        add_tree(z,ROOT/'games/resgate/resgate',f'{prefix}/resgate-source/resgate',{'.py','.json','.ico','.png'})
        add_tree(z,ROOT/'games/resgate/tests',f'{prefix}/resgate-source/tests',{'.py'})
        for name in ('pyproject.toml','README.md','LICENSE','build_windows.py','requirements-build.txt','launch.py'):
            z.write(ROOT/'games/resgate'/name,f'{prefix}/resgate-source/{name}')
        add_tree(z,ROOT/'artifacts/sdk-starter-demo',f'{prefix}/starter',{'.py','.md','.toml'})
    windows=OUT/'ResgateNaEstacao-1.0.0-Windows-x64.zip'
    with zipfile.ZipFile(windows,'w',zipfile.ZIP_DEFLATED) as z: add_tree(z,game,'ResgateNaEstacao')
    with zipfile.ZipFile(sdk) as z:
        assert not any('/saves/' in n or '/.venv/' in n or '/preferences/' in n for n in z.namelist())
        assert z.testzip() is None
    with zipfile.ZipFile(windows) as z: assert z.testzip() is None
    (OUT/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in (sdk,windows)),encoding='utf-8')
    for path in (sdk,windows): print(f'{path.name}: {path.stat().st_size/1024/1024:.1f} MiB')


if __name__=='__main__': main()
