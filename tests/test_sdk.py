import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from platform2d.__main__ import create_project
from platform2d.paths import user_data_dir
from platform2d.rendering.theme import load_theme


class SDKTests(unittest.TestCase):
    def test_project_contains_compilable_package_and_escaped_title(self):
        with tempfile.TemporaryDirectory() as folder:
            root=create_project(Path(folder)/'my game','A "aventura"\nseguinte')
            self.assertTrue((root/'mygame/__init__.py').is_file())
            for path in root.rglob('*.py'): compile(path.read_text(encoding='utf-8'),str(path),'exec')
            self.assertIn('platform2d>=0.24', (root/'pyproject.toml').read_text())
            theme=load_theme(root/'mygame/theme.json')
            self.assertEqual(theme.name,'A "aventura"\nseguinte')
            self.assertEqual(theme.color('highlight'),(249,206,116))
            self.assertIn('"mygame" = ["*.json"', (root/'pyproject.toml').read_text())

    def test_existing_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'personal.txt'; path.write_text('keep')
            with self.assertRaises(ValueError): create_project(folder)
            self.assertEqual(path.read_text(),'keep')

    def test_invalid_title_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/'game'
            with self.assertRaises(ValueError): create_project(dest,' ')
            self.assertFalse(dest.exists())

    def test_application_id_cannot_escape_data_directory(self):
        for invalid in ('../escape','a/b','C:\\files','','a b',None):
            with self.assertRaises(ValueError): user_data_dir(invalid)
        with patch.dict(os.environ,{'LOCALAPPDATA':'C:/data'}),patch('platform2d.paths.sys.platform','win32'):
            self.assertEqual(user_data_dir('MyGame'),Path('C:/data/MyGame'))
