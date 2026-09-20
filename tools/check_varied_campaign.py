"""Complete the four distinct rooms using movement and input only."""
import json
import os
from pathlib import Path
import sys
import tempfile
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import capture,restore
from platform2d.core.input import Actions
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.level_editor import LevelEditor
from examples.editor.profiles import editor_profiles


def main():
    pygame.init(); surface=pygame.display.set_mode((960,576))
    name,ids,docs=load_campaign(ROOT/'examples/campaign/assets/expedition.json')
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text())
    campaign=CampaignScene(name,ids,docs,settings)
    previous=set(); ticks=0
    snapshots=[d.snapshot() for d in docs]
    def tick(held=()):
        nonlocal previous,ticks
        held=set(held)
        campaign.update(1/60,Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
        previous=held; ticks+=1
        assert campaign.active.deaths==0,(campaign.progress.index,ticks,campaign.active.player.body)
    def until(label,condition,held=()):
        for _ in range(1200):
            if condition(): return
            tick(held)
        raise AssertionError((label,campaign.active.player.body,campaign.active.collected_items,campaign.active.destroyed))
    def move(x): until('move '+str(x),lambda:campaign.active.player.body.x>=x,{'right'})
    def jump(x):
        tick({'right'})
        until('jump '+str(x),lambda:campaign.active.player.body.x>=x,{'right','jump'})
        until('land',lambda:campaign.active.player.body.on_ground)
        tick()
    def kill(*ids): until('combat',lambda:set(ids)<=campaign.active.destroyed,{'shoot'})
    def finish():
        until('exit',lambda:campaign.active.won,{'right'})
        print(campaign.progress.current,campaign.active.shots,'shots',campaign.active.collected_items)
        state=capture(campaign)
        restore(state,campaign)
        assert capture(campaign)==state
        tick(); tick({'continue'}); tick()
    def shot(index):
        campaign.draw(surface,1)
        pygame.image.save(surface,str(ROOT/f'artifacts/expedition-{index}.png'))
    shot(1)
    kill('guard-a'); move(260); jump(375); kill('guard-b'); move(575); jump(705); kill('guard-c'); finish()
    shot(2)
    move(145); jump(220); move(280); jump(400); move(425); move(470); jump(580); move(610); move(670); jump(810); move(835)
    assert all(o['id'] in campaign.active.collected_items for o in campaign.active.coins)
    assert campaign.active.shots==0
    finish()
    shot(3)
    move(230); jump(375); move(495); move(582); jump(728)
    assert all(o['id'] in campaign.active.collected_items for o in campaign.active.coins)
    assert campaign.active.shots==0
    finish()
    shot(4)
    move(145); jump(230); move(350)
    until('ground',lambda:campaign.active.player.body.on_ground and campaign.active.player.body.y>475)
    kill('guard-a','guard-b')
    move(495); jump(560); move(605); jump(725); move(790)
    assert all(o['id'] in campaign.active.collected_items for o in campaign.active.coins)
    finish()
    assert campaign.progress.finished
    assert [d.snapshot() for d in docs]==snapshots
    profiles=editor_profiles(); classic=profiles['classic']
    editor=LevelEditor(classic['factory'],classic['bindings'],MapDocument(docs[1].data),profiles=profiles)
    editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_c,mod=0))
    assert editor.tool=='coin'
    editor.mission_properties()
    editor.close_modal_action(editor.modal['items'][0][1])
    editor.close_modal_action(editor.modal['items'][3][1])
    assert editor.document.data['properties']['theme']=='reactor'
    editor.document.undo()
    assert editor.document.data['properties']['theme']=='garden'
    editor.document.redo()
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'mission.json'; editor.document.save(path)
        assert MapDocument.load(path).data['properties']['theme']=='reactor'
    editor.mission_properties(); editor.draw()
    pygame.image.save(editor.screen,str(ROOT/'artifacts/editor-mission.png'))
    print(f'Expedition: four rooms, {ticks} steps, zero deaths; collection rooms without shots, all objectives and save roundtrips verified.')
    pygame.quit()


if __name__=='__main__': main()
