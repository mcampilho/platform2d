"""Recorded, deterministic witness that completes the Lost Keys Mine."""
from platform2d.core.input import Actions


SEGMENTS = (
    ({'right'},30),(set(),2),({'jump'},45),(set(),45),({'right'},18),
    ({'right','jump'},45),({'right'},38),({'right'},24),({'right','jump'},45),
    ({'right'},70),({'jump'},45),(set(),45),({'jump'},45),(set(),45),
    ({'left','jump'},45),({'left'},2),({'left','jump'},45),({'left'},2),
    ({'left','jump'},45),({'left'},11),({'left','jump'},45),({'left'},35),
    (set(),2),({'jump'},45),(set(),35),({'right'},2),({'right','jump'},45),
    ({'right'},35),({'left'},40),(set(),2),({'jump'},45),(set(),35),
    ({'right'},22),({'right','jump'},45),({'right'},2),({'right','jump'},33),
    ({'left','jump'},12),({'right'},1),({'right','jump'},45),(set(),35),
    ({'down','jump'},1),({'down'},80),({'down','jump'},1),({'down'},100),
    ({'down','jump'},1),({'down'},40),
)


def solution_actions():
    previous=frozenset()
    for keys,count in SEGMENTS:
        held=frozenset(keys)
        for _ in range(count):
            yield Actions(held,held-previous,previous-held)
            previous=held


def main():
    import json,os
    from pathlib import Path
    os.environ.setdefault('SDL_VIDEODRIVER','dummy')
    os.environ.setdefault('SDL_AUDIODRIVER','dummy')
    os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
    import pygame
    from examples.campaign.factory import create_scene
    from platform2d.tools.editor_model import MapDocument
    pygame.init()
    document=MapDocument.load(Path(__file__).parent/'assets/willy-keys.json')
    settings=json.loads((Path(__file__).parents[1]/'ranged/settings.json').read_text(encoding='utf-8'))
    scene=create_scene(document,settings)
    actions=tuple(solution_actions())
    for action in actions: scene.update(1/60,action)
    if not scene.won or scene.deaths or len(scene.collected_items)!=5:
        raise SystemExit('Falha: a rota gravada já não resolve o nível.')
    print(f'Solução confirmada: 5 chaves, saída, 0 mortes, {len(actions)/60:.1f} s simulados.')


if __name__=='__main__': main()
