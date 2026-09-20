"""Export reviewed source roots; omit local levels, saves and build products."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/releases'
TREES = ('platform2d', 'examples', 'tests', 'tools', 'docs', 'tutorials', 'translations', '.github')
SKIP = {'__pycache__', 'build', 'dist', '.venv', 'saves', 'preferences'}
EXTENSIONS = {'.py', '.md', '.json', '.png', '.wav', '.ico', '.toml', '.tmpl', '.yml', '.yaml', '.txt', '.ttf', '.otf', '.tsv'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    selected = []
    for tree in (*TREES, 'games/resgate'):
        for path in (ROOT / tree).rglob('*'):
            relative = path.relative_to(ROOT)
            if not path.is_file() or set(relative.parts) & SKIP:
                continue
            if any(p.endswith('.egg-info') for p in relative.parts):
                continue
            if path.suffix in EXTENSIONS or path.name == 'LICENSE':
                selected.append(path)
    selected.extend(ROOT.glob('*.cmd'))
    selected.extend(ROOT / name for name in ('README.md', 'LICENSE', 'CONTRIBUTING.md', 'CHANGELOG.md', '.gitignore', 'pyproject.toml', 'MANIFEST.in'))
    target = OUT / 'Platform2D-GitHub-source.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(selected)):
            archive.write(path, 'platform2d/' + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
    # Release attachments are downloaded together into one folder.
    attachments = sorted(OUT.glob('*.zip')) + sorted((ROOT / 'artifacts/publication').glob('platform2d-*'))
    (OUT / 'SHA256SUMS.txt').write_text(''.join(
        hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
        p.name + '\n'
        for p in attachments if p.is_file()), encoding='utf-8')
    print(f'{target}: {len(set(selected))} source files')


if __name__ == '__main__':
    main()
