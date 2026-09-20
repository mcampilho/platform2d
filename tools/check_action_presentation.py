"""Render a magnified pose sheet and the real carrying scene for visual review."""
import os,sys,json
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import pygame
from platform2d.rendering.action_pose import draw_actor
from examples.campaign.scene import CampaignScene,load_campaign


def main():
    pygame.init(); pygame.display.set_mode((960,576))
    target=ROOT/'artifacts'; target.mkdir(exist_ok=True)
    sheet=pygame.Surface((1120,560)); sheet.fill((12,23,37))
    font=pygame.font.Font(None,24)
    phases=[('carry','TRANSPORTAR'),('windup','PREPARAR'),('strike','GOLPE'),('guard','DEFENDER'),
            ('recover','RECUPERAR'),('hurt','ATINGIDO'),('stagger','VULNERÁVEL')]
    for row in range(2):
        for col,(phase,label) in enumerate(phases):
            tile=pygame.Surface((100,110)); tile.fill((12,23,37))
            draw_actor(tile,(20,40),phase=phase,progress=.5,guardian=bool(row),reduced=False)
            sheet.blit(pygame.transform.scale(tile,(160,176)),(col*160,row*270+50))
            sheet.blit(font.render(label,True,(180,227,217)),(col*160+6,row*270+230))
    sheet.blit(font.render('EXPLORADOR / GUARDIÃO · poses ampliadas',True,(255,207,137)),(12,12))
    pygame.image.save(sheet,str(target/'action-poses.png'))
    name,ids,docs=load_campaign(ROOT/'examples/campaign/assets/odyssey.json')
    settings=json.loads((ROOT/'examples/ranged/settings.json').read_text(encoding='utf-8'))
    scene=CampaignScene(name,ids,docs,settings).active
    scene.rocket.carrying=scene.rocket.part_order[0]
    screen=pygame.Surface((960,576)); scene.draw(screen,1)
    pygame.image.save(screen,str(target/'carrying-presentation.png'))
    pygame.quit(); print('Pose sheet and carrying scene rendered in artifacts.')


if __name__=='__main__': main()
