import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from platform2d.rendering.panorama import Panorama


class PanoramaTests(unittest.TestCase):
    def test_parallax_moves_image_and_preserves_alpha(self):
        pygame.init()
        try:
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "layer.png"
                source = pygame.Surface((120, 20), pygame.SRCALPHA)
                source.fill((230, 80, 50, 255), (0, 0, 60, 20))
                source.fill((20, 80, 210, 255), (60, 0, 60, 20))
                pygame.image.save(source, str(path))
                panorama = Panorama(path, height=20, parallax=.5)
                screen = pygame.Surface((60, 20))
                screen.fill((0, 0, 0))
                panorama.draw(screen, 0)
                self.assertEqual(screen.get_at((30, 10))[:3], (230, 80, 50))
                panorama.draw(screen, 100)
                self.assertEqual(screen.get_at((30, 10))[:3], (20, 80, 210))
                self.assertEqual(panorama.image.get_at((90, 10)).a, 255)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
