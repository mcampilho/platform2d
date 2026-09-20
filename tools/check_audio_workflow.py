"""Verify sound requests during complete, input-driven game routes."""
import json
from collections import Counter
from check_rooms_route import ROOT, check_route as rooms_route
from check_precision_route import check_route as precision_route
import pygame
from examples.rooms.scene import RoomsScene
from examples.precision.scene import PrecisionScene
from platform2d.world.room import RoomWorld
from platform2d.world.tilemap import TileMap
from platform2d.audio.service import Audio, AudioControls, SilentAudio, EFFECTS


class Recorder(SilentAudio):
    def __init__(self):
        self.events = Counter()

    def play(self, name):
        self.events[name] += 1
        return True


def main():
    pygame.init()
    settings = lambda name: json.loads((ROOT/f"examples/{name}/settings.json").read_text())
    rooms = RoomsScene(RoomWorld.load(ROOT/"examples/rooms/assets/world.json"),settings("rooms"))
    precision = PrecisionScene(TileMap(json.loads((ROOT/"examples/precision/assets/ascent.json").read_text()),{"ladder","beacon"}),settings("precision"))
    for scene, route, expected in ((rooms,rooms_route,{"jump","pickup","door","victory"}),
                                   (precision,precision_route,{"jump","dash","pickup","checkpoint","victory"})):
        scene.audio = Recorder()
        route(scene)
        assert expected <= scene.audio.events.keys(), scene.audio.events
        assert scene.audio.events["victory"] == 1
        print(type(scene).__name__,dict(scene.audio.events))
    audio = Audio()
    assert audio.available and set(audio.sounds) == set(EFFECTS)
    controls = AudioControls(audio)
    controls.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F12))
    assert audio.volume == .55
    surface = pygame.Surface((960,576))
    rooms.draw(surface,1)
    controls.draw(surface)
    pygame.image.save(surface,str(ROOT/"artifacts/audio-controls.png"))
    audio.close()
    pygame.quit()
    print("Audio routes and mixer controls verified (virtual device).")


if __name__ == "__main__":
    main()
