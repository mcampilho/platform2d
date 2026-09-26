import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
import pygame

from platform2d.rendering.theme import DEFAULT_PALETTE, ThemeHandle, fallback_theme, load_theme
from platform2d.tools.theme_tool import create_theme, inspect_theme, render_preview


class VisualThemeTests(unittest.TestCase):
    def test_fallback_has_complete_palette_without_assets(self):
        theme = fallback_theme()
        self.assertEqual(theme.id, "default")
        self.assertEqual(set(theme.palette), set(DEFAULT_PALETTE))
        self.assertEqual(theme.assets, {})
        self.assertEqual(theme.sprites, {})
        self.assertEqual(load_theme(None), theme)

    def test_manifest_resolves_assets_and_inherits_missing_colors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "background.png").write_bytes(b"image is validated by existence here")
            manifest = {
                "format": "platform2d.theme", "version": 1,
                "id": "test", "name": "Test",
                "palette": {"accent": [1, 2, 3]},
                "assets": {"background": "background.png"},
                "parallax": {"background": .2},
            }
            path = root / "test.theme.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            theme = load_theme(path, root)
            self.assertEqual(theme.color("accent"), (1, 2, 3))
            self.assertEqual(theme.color("text"), DEFAULT_PALETTE["text"])
            self.assertEqual(theme.assets["background"], root / "background.png")

    def test_missing_asset_and_unsafe_name_are_rejected(self):
        base = {"format": "platform2d.theme", "version": 1,
                "id": "bad", "name": "Bad", "assets": {"background": "missing.png"}}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.theme.json"
            for name in ("missing.png", "../outside.png"):
                base["assets"]["background"] = name
                path.write_text(json.dumps(base), encoding="utf-8")
                with self.subTest(name=name), self.assertRaises(ValueError):
                    load_theme(path)

    def test_theme_template_can_be_checked_and_previewed(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "new-theme"
            manifest = create_theme(destination, "moon-garden", "Jardim Lunar")
            theme, report = inspect_theme(manifest)
            self.assertEqual(theme.id, "moon-garden")
            self.assertEqual(report, [])
            preview = render_preview(theme, destination / "preview.png", (320, 240))
            self.assertTrue(preview.is_file())
            self.assertGreater(preview.stat().st_size, 0)
            with self.assertRaises(ValueError):
                create_theme(destination, "another", "Outro")

    def test_sprite_atlas_is_validated_inspected_and_previewed(self):
        pygame.init()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            atlas=pygame.Surface((32,16),pygame.SRCALPHA)
            pygame.draw.rect(atlas,(255,100,50),(0,0,16,16))
            pygame.draw.rect(atlas,(50,180,255),(16,0,16,16))
            pygame.image.save(atlas,str(root/'actor.png'))
            data={"format":"platform2d.theme","version":1,"id":"animated","name":"Animated",
                  "sprites":{"actor":{"image":"actor.png","frame_size":[16,16],
                  "clips":{"walk":{"frames":[0,1],"fps":6}},"anchor":[.5,1],"directional":True}}}
            path=root/'animated.theme.json'; path.write_text(json.dumps(data),encoding='utf-8')
            theme,report=inspect_theme(path)
            self.assertIn('actor',theme.sprites)
            self.assertEqual(report[0][:4],('sprite.actor','actor.png',32,16))
            self.assertTrue(render_preview(theme,root/'preview.png',(420,300)).is_file())

    def test_invalid_sprite_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'actor.png').write_bytes(b'x')
            base={"format":"platform2d.theme","version":1,"id":"bad","name":"Bad",
                  "sprites":{"actor":{"image":"actor.png","frame_size":[16,16],
                  "clips":{"idle":{"frames":[0]}}}}}
            path=root/'bad.theme.json'
            for field,value in (("frame_size",[0,16]),("anchor",[2,1]),("directional","yes")):
                data=json.loads(json.dumps(base)); data['sprites']['actor'][field]=value
                path.write_text(json.dumps(data),encoding='utf-8')
                with self.subTest(field=field),self.assertRaises(ValueError): load_theme(path)

    def test_reload_keeps_last_valid_theme_after_editing_error(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); path=create_theme(root/'theme','safe-theme','Tema Seguro')
            handle=ThemeHandle(path)
            original=handle.current
            path.write_text('{invalid json',encoding='utf-8')
            self.assertFalse(handle.reload())
            self.assertIs(handle.current,original)
            self.assertTrue(handle.error)
            data={"format":"platform2d.theme","version":1,"id":"updated",
                  "name":"Atualizado","palette":{},"assets":{},"parallax":{}}
            path.write_text(json.dumps(data),encoding='utf-8')
            self.assertTrue(handle.reload())
            self.assertEqual(handle.current.id,'updated')
            self.assertEqual(handle.error,'')


if __name__ == "__main__":
    unittest.main()
