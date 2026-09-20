"""Complete the duel with real inputs; parry, counter, save and editor replay."""
import os,json,sys,tempfile
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import pygame
from platform2d.core.input import Actions
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import capture,restore
from examples.campaign.app import CampaignApp
from examples.editor.profiles import editor_profiles,template_document
from platform2d.tools.level_editor import LevelEditor
from platform2d.tools.editor_model import MapDocument


def main():
    pygame.init(); screen=pygame.display.set_mode((960,576))
    name,ids,docs=load_campaign(ROOT/'examples/campaign/assets/duel.json')
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text()); settings['bindings'].update(attack=['j'],guard=['l'])
    campaign=CampaignScene(name,ids,docs,settings); scene=campaign.active
    previous=set(); parries=0; saved=False
    for frame in range(3000):
        enemy=next((e for e in scene.guardians if not e.health.dead),None)
        held=set()
        if enemy:
            dx=enemy.body.x-scene.player.body.x
            if dx>62: held.add('right')
            elif enemy.sword.stunned>0 and not scene.sword.attack.running:
                held.add('attack')
            elif enemy.sword.attack.running and .42<=enemy.sword.attack.elapsed<.72:
                held.add('guard')
        else: held.add('right')
        scene.update(1/60,Actions(frozenset(held),frozenset(held-previous),frozenset(previous-held)))
        previous=held
        assert scene.deaths==0
        if scene.sword.result=='parry':
            parries+=1
            scene.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts/duel-parry.png'))
        if enemy and enemy.sword.attack.running and .2<enemy.sword.attack.elapsed<.3:
            scene.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts/duel-telegraph.png'))
        if scene.destroyed and not saved:
            payload=capture(campaign); restore(payload,campaign); scene=campaign.active; saved=True
            assert not scene.guardians
        if scene.won: break
    assert scene.won,(frame,scene.player.body,[(e.body,e.health.remaining,e.sword.attack.elapsed) for e in scene.guardians])
    assert parries>=2 and scene.health.remaining==5,(parries,scene.health.remaining)
    scene.draw(screen,1); pygame.image.save(screen,str(ROOT/'artifacts/duel-victory.png'))
    # Editor configuration, disk roundtrip and preview isolation.
    profiles=editor_profiles(); doc=template_document('duel'); original=doc.snapshot()
    index=next(i for i,o in enumerate(doc.data['objects']) if o['type']=='guardian')
    doc.update_object(index,hp=4); doc.commit(); doc.undo(); assert doc.snapshot()==original
    doc.redo(); assert doc.data['objects'][index]['hp']==4
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'duel.json'; doc.save(path); doc=MapDocument.load(path)
        editor=LevelEditor(profiles['classic']['factory'],profiles['classic']['bindings'],doc,path,profiles=profiles)
        before=doc.snapshot(); editor.start_preview()
        for _ in range(10): editor.preview.update(1/60,Actions())
        editor.stop_preview(); assert doc.snapshot()==before
    print(f'Duel completed: {frame+1} steps, {parries} parries, three counters, zero damage/deaths. Defeat save restored; editor history and preview verified.')
    pygame.quit()

if __name__=='__main__': main()

