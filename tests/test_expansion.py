import copy,json,os,tempfile,unittest
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from platform2d.core.input import Actions
from platform2d.gameplay.cargo import Cargo
from platform2d.physics.body import Body,Box
from platform2d.physics.collision import Collider
from platform2d.actors.exploration import ExploreController
from platform2d.tools.editor_model import MapDocument
from platform2d.tools.adventure_reachability import AdventureSearch
from examples.campaign.scene import CampaignScene,load_campaign
from examples.campaign.progress import capture,restore
from examples.editor.profiles import editor_profiles,template_document
from platform2d.tools.level_editor import LevelEditor

ASSETS=Path('examples/campaign/assets')


class CargoTests(unittest.TestCase):
    def setUp(self):
        self.cargo=Cargo([dict(id='box',type='crate',x=64,y=52,w=48,h=48),dict(id='plate',type='plate',x=128,y=94,w=64,h=6,weight=2)])
        self.floor=Collider(Box(0,100,400,32)); self.player=Body(40,70,on_ground=True)

    def test_push_obeys_walls_and_does_not_push_chains(self):
        wall=Collider(Box(128,0,32,100))
        for _ in range(120):
            self.cargo.update(1/60,self.player,1,[self.floor,wall],400)
            self.player.x=self.cargo.crates['box'].x-24
        self.assertEqual(self.cargo.crates['box'].box.right,128)
        self.cargo.crates['other']=Body(128,52,48,48)
        self.cargo.update(.1,self.player,1,[self.floor],400)
        self.assertEqual(self.cargo.crates['other'].x,128)
        self.assertEqual(self.cargo.crates['box'].box.right,128)

    def test_weight_and_height_both_matter(self):
        self.player.teleport(140,70)
        self.assertFalse(self.cargo.active(self.player))
        self.cargo.crates['box'].teleport(136,52)
        self.assertEqual(self.cargo.active(),{'plate'})
        self.cargo.crates['box'].y=30
        self.assertFalse(self.cargo.active())

    def test_falling_crate_does_not_embed_player(self):
        b=self.cargo.crates['box']; b.teleport(64,0); self.player.teleport(64,70)
        for _ in range(60): self.cargo.update(1/60,self.player,0,[self.floor],400)
        self.assertEqual(b.box.bottom,self.player.y)
        self.assertFalse(b.box.overlaps(self.player.box))

    def test_bad_save_is_atomic(self):
        before=self.cargo.snapshot()
        for state in ({'box':[float('nan'),0]},{'box':[64,80]},{'box':[400,52]},{'unknown':[0,0]}):
            with self.assertRaises(ValueError): self.cargo.restore(state,[self.floor],400,200)
            self.assertEqual(self.cargo.snapshot(),before)


class ExpansionTests(unittest.TestCase):
    def setUp(self): pygame.init()
    def tearDown(self): pygame.quit()

    def game(self,mode):
        name,ids,docs=load_campaign(ASSETS/f'{mode}.json')
        settings=json.loads(Path('examples/ranged/settings.json').read_text(encoding='utf-8'))
        campaign=CampaignScene(name,ids,docs,settings)
        return campaign,campaign.active

    def test_twelve_stages_preserve_original_eight(self):
        _,_,old=load_campaign(ASSETS/'odyssey-duel.json')
        _,_,new=load_campaign(ASSETS/'odyssey-horizons.json')
        self.assertEqual(len(new),12)
        self.assertEqual([d.snapshot() for d in old],[d.snapshot() for d in new[:8]])

    def test_pause_freezes_environment(self):
        for mode in ('cargo','swim','escape','explore'):
            _,s=self.game(mode); s.paused=True
            before=(s.cargo.snapshot(),s.oxygen,s.escape_time,s.elapsed)
            s.update(1,Actions(held=frozenset({'right','jump'})))
            self.assertEqual(before,(s.cargo.snapshot(),s.oxygen,s.escape_time,s.elapsed))

    def test_cargo_save_restores_positions_and_restart_repositions(self):
        c,s=self.game('cargo'); s.cargo.crates['crate-a'].teleport(328,464)
        data=capture(c); restore(data,c)
        self.assertEqual(c.active.cargo.snapshot(),s.cargo.snapshot())
        c.active.update(1/60,Actions(pressed=frozenset({'restart'})))
        self.assertEqual(c.active.cargo.crates['crate-a'].x,192)

    def test_cargo_victory_requires_weight(self):
        c,s=self.game('cargo'); s.collected_items={o['id'] for o in s.coins}
        self.assertFalse(s.objectives_ready)
        data=capture(c); data['stage']['won']=True
        with self.assertRaisesRegex(ValueError,'placas'): restore(data,c)
        self.assertIs(c.active,s)

    def test_lost_crate_resets_puzzle_and_remains_saveable(self):
        c,s=self.game('cargo'); s.cargo.crates['crate-a'].teleport(600,s.level.height-30)
        s.update(1/60,Actions())
        self.assertEqual(s.cargo.crates['crate-a'].x,192)
        restore(capture(c),c)

    def test_cargo_restore_moves_player_clear_of_crate_at_spawn(self):
        c,s=self.game('cargo'); s.cargo.crates['crate-a'].teleport(64,464)
        restore(capture(c),c)
        self.assertFalse(any(c.active.player.body.box.overlaps(b.box) for b in c.active.cargo.crates.values()))

    def test_escape_threat_continues_after_camera_reaches_end(self):
        _,s=self.game('escape'); s.player.respawn((2200,482)); s.escape_time=35
        s.update(1/60,Actions()); self.assertEqual(s.deaths,1)

    def test_gate_does_not_close_on_player(self):
        _,s=self.game('cargo'); s.player.respawn((1030,482))
        s.prepare_world(1/60,Actions())
        self.assertIn('cargo-gate',s.open_gates)
        self.assertFalse(any(s.player.body.box.overlaps(col.box) for col in s.level.colliders))

    def test_draw_never_advances_puzzle_or_oxygen(self):
        for mode in ('cargo','swim','escape','explore'):
            c,s=self.game(mode); s.update(1/60,Actions()); before=capture(c)
            state=(s.oxygen,s.escape_time,s.cargo.snapshot(),copy.deepcopy(vars(s.player.body)))
            for alpha in (0,.5,1): s.draw(pygame.Surface((960,576)),alpha)
            self.assertEqual(capture(c),before)
            self.assertEqual(state,(s.oxygen,s.escape_time,s.cargo.snapshot(),vars(s.player.body)))

    def test_swimming_drains_air_and_air_pockets_refill(self):
        _,s=self.game('swim'); s.player.respawn((400,960)); s.oxygen=4
        s.update(1/60,Actions()); self.assertLess(s.oxygen,4)
        s.player.respawn((80,1020)); s.update(1/60,Actions()); self.assertGreater(s.oxygen,4)

    def test_drowning_respawns_with_full_oxygen(self):
        _,s=self.game('swim'); s.player.respawn((400,960)); s.oxygen=.001
        s.update(1/60,Actions()); self.assertEqual(s.deaths,1); self.assertEqual(s.oxygen,12)

    def test_swimming_current_moves_idle_player(self):
        _,s=self.game('swim'); s.player.respawn((400,960)); x=s.player.body.x
        for _ in range(30): s.update(1/60,Actions())
        self.assertGreater(s.player.body.x,x+5)

    def test_escape_waiting_is_dangerous_and_checkpoint_restarts_camera(self):
        _,s=self.game('escape')
        for _ in range(180): s.update(1/60,Actions())
        self.assertGreater(s.deaths,0)
        s.active_checkpoint='mid'; s.respawn_point=(1088,482); s.respawn()
        self.assertEqual(s.escape_time,0); self.assertEqual(s.camera.x,968)
        self.assertGreater(s.player.body.x,s.camera.x)

    def test_ability_survives_save_and_restart_but_not_new_game(self):
        c,s=self.game('explore'); s.player.respawn((1744,482)); s.update(1/60,Actions())
        self.assertTrue(s.ability); restore(capture(c),c)
        self.assertTrue(c.active.ability)
        c.active.update(1/60,Actions(pressed=frozenset({'restart'})))
        self.assertTrue(c.active.ability)
        c.reset(); self.assertFalse(c.active.ability)

    def test_second_jump_needs_ability_and_only_one_extra(self):
        body=Body(0,100,vy=10); controller=ExploreController()
        action=Actions(held=frozenset({'jump'}),pressed=frozenset({'jump'}))
        controller.before_physics(body,action,1/60); self.assertGreater(body.vy,0)
        controller.enabled=True; controller.before_physics(body,action,1/60)
        self.assertLess(body.vy,0); self.assertTrue(controller.extra_used)
        body.vy=10; controller.before_physics(body,action,1/60); self.assertGreater(body.vy,0)

    def test_exploration_cannot_claim_victory_without_ability(self):
        c,s=self.game('explore'); s.collected_items={'lab-crystal'}
        data=capture(c); data['stage']['won']=True
        with self.assertRaisesRegex(ValueError,'capacidade'): restore(data,c)

    def test_dynamic_search_is_explicitly_inconclusive(self):
        for mode in ('cargo','swim','escape','explore'):
            doc=template_document(mode); result=AdventureSearch(doc.data).step()
            self.assertEqual(result.status,'inconclusive')

    def test_map_roundtrip_history_preview_preserve_new_objects(self):
        profiles=editor_profiles()
        for mode in ('cargo','swim','escape','explore'):
            doc=template_document(mode); before=doc.snapshot()
            index=next(i for i,o in enumerate(doc.data['objects']) if o['type']=='goal')
            doc.update_object(index,x=doc.data['objects'][index]['x']+1); doc.commit(); doc.undo()
            self.assertEqual(doc.snapshot(),before)
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'level.json'; doc.save(path); restored=MapDocument.load(path)
                self.assertEqual(restored.snapshot(),before)
                editor=LevelEditor(profiles['classic']['factory'],profiles['classic']['bindings'],restored,path,profiles=profiles)
                editor.start_preview(); editor.preview.update(1/60,Actions()); editor.stop_preview()
                self.assertEqual(editor.document.snapshot(),before)

    def test_invalid_weight_current_and_crate_overlap(self):
        for mode,kind,changes in [('cargo','plate',{'weight':True}),('swim','water',{'current':float('inf')}),('cargo','crate',{'w':49})]:
            doc=template_document(mode); index=next(i for i,o in enumerate(doc.data['objects']) if o['type']==kind)
            with self.assertRaises(ValueError): doc.update_object(index,**changes)
        doc=template_document('cargo'); crate=next(o for o in doc.data['objects'] if o['type']=='crate'); crate['y']=500
        self.assertTrue(any(i.severity=='error' and 'sobreposta' in i.message for i in doc.validate()))
