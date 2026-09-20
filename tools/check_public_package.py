"""Check the exact engine distributions before uploading them."""
import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath


def check(path):
    if path.suffix == '.whl':
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None, 'Corrupt wheel'
            files = {n: archive.read(n) for n in archive.namelist() if not n.endswith('/')}
        metadata = next(data for name, data in files.items() if name.endswith('.dist-info/METADATA'))
    else:
        with tarfile.open(path, 'r:gz') as archive:
            files = {}
            for member in archive.getmembers():
                assert not member.issym() and not member.islnk(), 'Unexpected archive link'
                if member.isfile():
                    name = PurePosixPath(member.name)
                    assert len(name.parts) > 1 and '..' not in name.parts and not name.is_absolute()
                    files[str(PurePosixPath(*name.parts[1:]))] = archive.extractfile(member).read()
        metadata = files['PKG-INFO']
        assert 'pyproject.toml' in files and 'docs/using-platform2d.md' in files
    for name in files:
        parts = PurePosixPath(name).parts
        assert not PurePosixPath(name).is_absolute() and '..' not in parts
        assert not set(parts) & {'tests', 'examples', 'games', 'saves', 'preferences', '__pycache__', 'artifacts'}
        assert not any(p.startswith('.env') or p in {'.pypirc', '.venv', '.git'} for p in parts)
    info = BytesParser().parsebytes(metadata)
    assert info['Name'] == 'platform2d'
    assert info['Version'] == '0.23.0', 'Update release checker when changing the release version'
    assert info['License-Expression'] == 'MIT'
    assert 'platform2d/__main__.py' in files
    assert any(n.startswith('platform2d/starter/') and n.endswith('.tmpl') for n in files)
    assert any(n.startswith('platform2d/audio/assets/') and n.endswith('.wav') for n in files)
    assert any(n.endswith('/LICENSE') or n == 'LICENSE' for n in files)
    print(f'OK: {path.name}: {len(files)} files, version {info["Version"]}, MIT')


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else 'dist')
    paths = sorted(folder.glob('*.whl')) + sorted(folder.glob('*.tar.gz'))
    assert len(paths) == 2, 'Use a clean folder containing exactly one engine wheel and one sdist'
    assert sum(p.suffix == '.whl' for p in paths) == 1
    for path in paths:
        check(path)


if __name__ == '__main__':
    main()
