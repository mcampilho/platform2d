"""Exercise authoring and play the exported sequence with keyboard events."""
import os,json,sys,tempfile
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import pygame
from platform2d.tools.editor_model import new_map
from platform2d.tools.campaign_model import CampaignDocument
from platform2d.tools.campaign_editor import CampaignEditor
from examples.editor.profiles import editor_profiles
from examples.campaign.scene import load_campaign


def main():
    pygame.init(); profiles=editor_profiles()
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder); maps=root/'maps'; maps.mkdir()
        for i in range(2):
            data=new_map(30,18); data.update(editor_profile='ranged',name=f'Etapa de teste {i+1}',properties=dict(weapon_enabled=False))
            data['objects']=[dict(id='spawn',type='spawn',x=64,y=482),dict(id='upgrade',type='pickup',item='power',quantity=1,x=100,y=482,w=24,h=30),dict(id='goal',type='goal',x=190,y=454,w=32,h=58)]
            (maps/f'map-{i}.json').write_text(json.dumps(data),encoding='utf-8')
        doc=CampaignDocument(); editor=CampaignEditor(doc,profiles,root/'export/campaign.json')
        for i in range(2):
            editor.browse('Adicionar mapa',lambda path:setattr(editor,'stage_index',doc.add(path)),maps)
            callback=next(callback for label,callback in editor.modal['items'] if label==f'map-{i}.json')
            editor.close_modal_action(callback); editor.refresh()
        original_maps={p:p.read_bytes() for p in maps.glob('*.json')}
        editor.stage_index=1
        editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_UP,mod=pygame.KMOD_SHIFT))
        assert doc.data['stages'][0]['id']=='map-1'
        editor.history(); assert doc.data['stages'][0]['id']=='map-0'
        editor.rename_campaign(); editor.modal['text']='Campanha de verificação'; editor.submit_modal()
        editor.save(); assert editor.modal['kind']=='save'
        editor.submit_modal(); assert not doc.dirty
        name,ids,documents=load_campaign(doc.path); assert ids==['map-0','map-1']
        editor.replace_campaign(CampaignDocument.load(doc.path)); before=editor.campaign.snapshot()
        editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F5,mod=0))
        for index in range(2):
            editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT,mod=0))
            for _ in range(180):
                editor.update(1/60)
                if editor.preview.active.won: break
            assert editor.preview.active.won
            assert editor.preview.active.inventory.count('power')==index+1
            editor.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_RIGHT,mod=0))
            if index==0:
                editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN,mod=0)); editor.update(1/60)
                editor.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_RETURN,mod=0))
        assert editor.preview.progress.finished
        editor.draw(); pygame.image.save(editor.screen,str(ROOT/'artifacts/campaign-editor-completed.png'))
        editor.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE,mod=0))
        assert editor.campaign.snapshot()==before
        for path,raw in original_maps.items(): assert path.read_bytes()==raw
        editor.stage_index=1; editor.start_preview(True)
        assert len(editor.preview.documents)==1 and editor.preview.active.inventory.count('power')==0
        editor.stop_preview()
    demo=CampaignDocument.load(ROOT/'examples/campaign/assets/odyssey-duel.json')
    demo.path=None; demo.saved=None
    editor=CampaignEditor(demo,profiles); editor.stage_index=7; editor.scroll=1; editor.draw()
    pygame.image.save(editor.screen,str(ROOT/'artifacts/campaign-editor.png'))
    editor.show_validation(); editor.draw(); pygame.image.save(editor.screen,str(ROOT/'artifacts/campaign-editor-validation.png'))
    pygame.quit()
    print('Campaign editor verified: graphical map choice, reorder/undo, save-as/reopen, two levels completed with carried inventory, isolated selected-stage test; source maps unchanged.')

if __name__=='__main__': main()
