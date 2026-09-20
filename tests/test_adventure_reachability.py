import os,unittest
from copy import deepcopy
from pathlib import Path
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from platform2d.tools.adventure_reachability import AdventureSearch
from platform2d.tools.editor_model import MapDocument,new_map
from platform2d.tools.level_editor import LevelEditor
from examples.editor.profiles import editor_profiles
from platform2d.core.input import Actions

ROOT=Path('examples/campaign/assets')

def enclosed():
    data=MapDocument.load(ROOT/'odyssey-launch.json').snapshot()
    cells=[list(row) for row in data['tiles']]
    for x in range(15,23): cells[8][x]=cells[14][x]='#'
    for y in range(8,15): cells[y][15]=cells[y][22]='#'
    data['tiles']=[''.join(row) for row in cells]
    next(o for o in data['objects'] if o['id']=='part-0').update(x=550,y=350)
    return data

class AdventureSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); cls.profiles=editor_profiles(); cls.profile=cls.profiles['adventure']
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def search(self,data,**kwargs):
        return AdventureSearch(data,self.profile['movement'],self.profile['factory'],**kwargs).run()

    def test_original_flight_has_ordered_deliveries_and_real_launch(self):
        data=MapDocument.load(ROOT/'odyssey-launch.json').snapshot(); before=deepcopy(data)
        result=self.search(data)
        self.assertEqual(result.status,'solved'); self.assertEqual(data,before)
        scene=self.profile['factory'](MapDocument(data).playable())
        order=[]; count=0
        for action in result.actions:
            scene.update(1/60,action)
            if len(scene.rocket.delivered)>count:
                order.append(scene.rocket.part_order[count]); count+=1
        self.assertTrue(scene.won); self.assertTrue(scene.rocket.ready)
        self.assertEqual(order,['part-0','part-1','part-2']); self.assertEqual(scene.deaths,0)

    def test_original_palace_replays_all_grabs_and_coins(self):
        data=MapDocument.load(ROOT/'odyssey-palace.json').snapshot(); result=self.search(data)
        self.assertEqual(result.status,'solved')
        scene=self.profile['factory'](MapDocument(data).playable())
        for action in result.actions: scene.update(1/60,action)
        self.assertTrue(scene.won); self.assertGreaterEqual(scene.player.controller.grabs,8)
        self.assertEqual(len(scene.collected_items),8); self.assertEqual(scene.deaths,0)

    def test_walk_scroll_route_avoids_hazards(self):
        data=MapDocument.load(ROOT/'odyssey-valley.json').snapshot(); result=self.search(data)
        self.assertEqual(result.status,'solved')

    def test_enclosed_required_piece_is_proved_inaccessible(self):
        result=self.search(enclosed()); self.assertEqual(result.status,'impossible')
        self.assertTrue(any('part-0' in i.message and 'fechada' in i.message for i in result.issues))
        self.assertEqual(result.actions,())

    def test_opening_enclosure_removes_negative_proof(self):
        data=enclosed(); rows=[list(row) for row in data['tiles']]
        for x in range(17,21): rows[8][x]='.'
        data['tiles']=[''.join(r) for r in rows]
        result=self.search(data,max_seconds=2)
        self.assertNotEqual(result.status,'impossible')

    def test_very_high_target_exceeds_even_ledge_envelope(self):
        data=new_map(30,18); data.update(editor_profile='adventure',properties=dict(traversal='ledge',scroll='horizontal',weapon_enabled=False))
        data['objects']=[dict(id='spawn',type='spawn',x=64,y=482),dict(id='coin',type='coin',x=500,y=260),dict(id='goal',type='goal',x=850,y=454)]
        result=self.search(data); self.assertEqual(result.status,'impossible')
        self.assertIn('coin',result.issues[0].message)

    def test_budget_exhaustion_is_not_impossibility(self):
        data=MapDocument.load(ROOT/'odyssey-launch.json').snapshot()
        for options in (dict(max_nodes=0),dict(max_seconds=0)):
            result=self.search(data,**options)
            self.assertEqual(result.status,'inconclusive'); self.assertFalse(result.actions)

    def test_duel_and_projectiles_require_manual_test(self):
        data=MapDocument.load(ROOT/'duel-courtyard.json').snapshot()
        self.assertEqual(self.search(data).status,'inconclusive')
        data=MapDocument.load(ROOT/'odyssey-valley.json').snapshot()
        data['properties']['weapon_enabled']=True
        data['objects'].append(dict(id='turret',type='turret',x=800,y=482))
        self.assertEqual(self.search(data).status,'inconclusive')

    def test_factory_required_for_positive_certificate(self):
        data=MapDocument.load(ROOT/'odyssey-launch.json').snapshot()
        result=AdventureSearch(data,self.profile['movement']).run()
        self.assertEqual(result.status,'inconclusive')

    def test_failed_real_replay_cannot_be_reported_as_solved(self):
        data=MapDocument.load(ROOT/'odyssey-launch.json').snapshot()
        class RejectingScene:
            won=False; deaths=0
            def update(self,dt,actions): pass
        result=AdventureSearch(data,self.profile['movement'],lambda level:RejectingScene()).run()
        self.assertEqual(result.status,'inconclusive'); self.assertFalse(result.actions)

    def test_a_death_in_real_replay_rejects_candidate(self):
        data=MapDocument.load(ROOT/'odyssey-launch.json').snapshot()
        class DeadScene:
            won=True; deaths=1
            def update(self,dt,actions): pass
        result=AdventureSearch(data,self.profile['movement'],lambda level:DeadScene()).run()
        self.assertEqual(result.status,'inconclusive')

    def test_editor_caches_result_until_map_or_movement_changes(self):
        doc=MapDocument.load(ROOT/'odyssey-palace.json'); profile=self.profiles['classic']
        editor=LevelEditor(profile['factory'],profile['bindings'],doc,profiles=self.profiles)
        editor.show_validation()
        for _ in range(500):
            editor.update(1/60)
            if editor.analysis is None: break
        self.assertEqual(editor.analysis_result.status,'solved')
        result=editor.analysis_result; editor.refresh(); self.assertIs(editor.analysis_result,result)
        editor.start_solution()
        for _ in range(len(result.actions)+1): editor.update(1/60)
        self.assertTrue(editor.preview.won); editor.stop_preview()
        doc.rename('Outro título'); editor.refresh(); self.assertIsNone(editor.analysis_result)

    def test_editor_cancel_discards_pending_search(self):
        doc=MapDocument.load(ROOT/'odyssey-launch.json'); profile=self.profiles['classic']
        editor=LevelEditor(profile['factory'],profile['bindings'],doc,profiles=self.profiles)
        before=doc.snapshot(); editor.show_validation(); editor.close_validation()
        for _ in range(10): editor.update(1/60)
        self.assertIsNone(editor.analysis); self.assertIsNone(editor.analysis_result)
        self.assertEqual(doc.snapshot(),before)

    def test_jetpack_exit_marker_is_not_a_required_objective(self):
        data=enclosed()
        next(o for o in data['objects'] if o['id']=='part-0').update(x=160,y=360)
        data['objects'].append(dict(id='unused-exit',type='goal',x=550,y=350,w=24,h=30))
        result=self.search(data,max_seconds=2)
        self.assertNotEqual(result.status,'impossible')

    def test_cached_result_invalidates_when_movement_changes(self):
        profiles=editor_profiles(); doc=MapDocument.load(ROOT/'odyssey-palace.json'); classic=profiles['classic']
        editor=LevelEditor(classic['factory'],classic['bindings'],doc,profiles=profiles)
        editor.show_validation()
        for _ in range(500):
            editor.update(1/60)
            if editor.analysis is None: break
        self.assertIsNotNone(editor.analysis_result)
        profiles['adventure']['movement'].speed+=10; editor.refresh()
        self.assertIsNone(editor.analysis_result)
