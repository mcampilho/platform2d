"""Exercise menus, checkpoint saves and continuation in a fresh process."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.app import CampaignApp
from platform2d.core.input import Input
from platform2d.tools.controls_panel import ControlsPanel
from platform2d.audio.service import Audio


def main(path,resume=False):
    pygame.init(); screen=pygame.display.set_mode((960,576))
    name,ids,docs=load_campaign(ROOT/'examples/campaign/assets/campaign.json')
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text())
    settings['bindings'].update({'continue':['return'],'save_progress':['f6'],'load_progress':['f9']})
    campaign=CampaignScene(name,ids,docs,settings)
    app=CampaignApp(campaign,path)
    audio=Audio(muted=True); app.audio=audio
    panel=ControlsPanel(settings['bindings'],'campaign')
    app.open_controls=panel.toggle; app.format_controls=panel.format_hint
    inputs=Input(settings['bindings']); previous=set()
    def key(code):
        app.handle_event(pygame.event.Event(pygame.KEYDOWN,key=code))
    def screenshot(name):
        app.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts'/name))
    screenshot('campaign-title.png')
    # Navigate with keyboard, then inspect options and the complete controls panel.
    key(pygame.K_DOWN); key(pygame.K_DOWN); key(pygame.K_RETURN)
    assert app.mode=='options'
    screenshot('campaign-options.png')
    for _ in range(4): key(pygame.K_DOWN)
    key(pygame.K_RETURN)
    assert panel.open
    panel.draw(screen); pygame.image.save(screen,str(ROOT/'artifacts/campaign-controls.png'))
    panel.toggle(); key(pygame.K_ESCAPE)
    assert app.mode=='title'
    if resume:
        key(pygame.K_DOWN); key(pygame.K_RETURN)
        assert app.started and app.mode is None
        assert campaign.active.active_checkpoint=='safe-point'
        assert campaign.active.inventory.count('power')==1
        assert campaign.active.health.remaining==5
        assert campaign.active.destroyed=={'training','sentry-a'}
    else:
        key(pygame.K_RETURN)
        assert app.started
    def tick(held):
        nonlocal previous
        held=set(held)
        for pressed,names in ((False,previous-held),(True,held-previous)):
            for name in names:
                code=pygame.key.key_code(settings['bindings'][name][0])
                inputs.feed([pygame.event.Event(pygame.KEYDOWN if pressed else pygame.KEYUP,key=code)])
        app.update(1/60,inputs.consume()); previous=held
        assert campaign.active.deaths==0
    def until(label,condition,held):
        for _ in range(1400):
            if condition(): return
            tick(held)
        raise AssertionError((label,campaign.active.player.body,app.notice))
    if resume:
        for _ in range(24): tick(set())
        screenshot('campaign-resumed.png')
    for index in range(3):
        scene=campaign.active
        until('first upgrade',lambda:scene.player.body.x>=150,{'right','shoot'})
        if not resume: screenshot('campaign-feedback.png')
        until('first sector',lambda:{'training','sentry-a'}<=scene.destroyed,{'shoot'})
        until('cover',lambda:scene.player.body.x>=356,{'right'})
        until('jump',lambda:scene.player.body.x>469,{'right','jump'})
        until('land',lambda:scene.player.body.on_ground and scene.player.body.y>475,set())
        if not resume:
            until('checkpoint',lambda:scene.active_checkpoint=='safe-point',{'right'})
            tick({'save_progress'}); tick(set())
            assert path.exists()
            key(pygame.K_ESCAPE); screenshot('campaign-pause.png')
            before=scene.elapsed
            for _ in range(20): tick({'right','shoot'})
            assert scene.elapsed==before
            # Simulate closing the application; another interpreter continues.
            panel.close(); audio.close(); pygame.quit()
            result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--resume',str(path)],cwd=ROOT,check=True)
            return
        until('second sector',lambda:len(scene.destroyed)==4,{'shoot'})
        until('exit',lambda:scene.won,{'right'})
        screenshot(f'campaign-experience-stage-{index+1}.png')
        inventory=scene.inventory.snapshot()
        tick(set()); tick({'continue'})
        if index<2:
            assert campaign.active.inventory.snapshot()==inventory
    assert campaign.progress.finished
    final=app.slot.read(lambda data:data)
    assert final['index']==2 and final['stage']['won']
    print('Campaign experience: menus/options/controls, pause, F6, fresh-process Continue, three stages and final autosave passed; zero deaths.')
    panel.close(); audio.close(); pygame.quit()


if __name__=='__main__':
    if len(sys.argv)>1:
        main(Path(sys.argv[2]),True)
    else:
        with tempfile.TemporaryDirectory() as folder:
            main(Path(folder)/'campaign.progress.json')
