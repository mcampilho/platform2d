"""Certificates are checked against the actual game, not just the search model."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame

from examples.classic.scene import ClassicScene
from platform2d.actors.controller import Movement
from platform2d.core.input import Actions
from platform2d.physics.body import Box
from platform2d.tools.editor_model import MapDocument, new_map
from platform2d.tools.level_editor import LevelEditor
from platform2d.tools.reachability import ReachabilitySearch, covered_by
from platform2d.world.tilemap import TileMap

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT/"examples/classic/settings.json").read_text())


class ReachabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def replay(self, data):
        result = ReachabilitySearch(data,Movement(**SETTINGS["movement"])).run()
        self.assertEqual(result.status,"solved")
        scene = ClassicScene(TileMap(data),SETTINGS)
        for action in result.actions:
            scene.update(1/60,action)
        self.assertTrue(scene.won)
        self.assertEqual(scene.deaths,0)
        self.assertEqual(len(scene.collected),scene.coin_count)
        return result

    def test_workshop_certificate_wins_actual_game(self):
        data = json.loads((ROOT/"examples/editor/assets/workshop.json").read_text())
        original = deepcopy(data)
        self.replay(data)
        self.assertEqual(data,original)

    def test_goal_before_last_coin_preserves_game_order(self):
        data = new_map(8,8)
        data["objects"].append(dict(id="last",type="coin",x=160,y=170))
        self.replay(data)

    def test_high_required_crystal_is_impossible(self):
        data = new_map()
        data["objects"].append(dict(id="high",type="coin",x=320,y=40))
        result = ReachabilitySearch(data).run()
        self.assertEqual(result.status,"impossible")
        self.assertEqual(result.issues[0].position,(320,40))

    def test_gap_beyond_horizontal_range_is_impossible(self):
        data = new_map()
        data["tiles"][16:] = ["###"+"."*34+"###"]*2
        self.assertEqual(ReachabilitySearch(data).run().status,"impossible")

    def test_unreachable_alternative_exit_does_not_reject_valid_route(self):
        data = new_map(8,18)
        data["objects"].append(dict(id="extra",type="goal",x=160,y=0))
        self.replay(data)

    def test_budget_exhaustion_is_inconclusive(self):
        result = ReachabilitySearch(new_map(),max_nodes=0).run()
        self.assertEqual(result.status,"inconclusive")
        self.assertFalse(result.actions)
        self.assertTrue(all(i.severity == "warning" for i in result.issues))

    def test_union_coverage_and_partial_overlap(self):
        self.assertTrue(covered_by(Box(16,0,32,30),[Box(0,0,32,32),Box(32,0,32,32)]))
        self.assertFalse(covered_by(Box(16,0,32,30),[Box(0,0,32,32)]))
        document = MapDocument()
        document.data["objects"].append(dict(id="buried",type="coin",x=20,y=512,w=40,h=26))
        self.assertTrue(any(i.severity == "error" and "buried" in i.message for i in document.validate()))
        document.data["objects"][-1]["y"] = 500
        self.assertFalse(any(i.severity == "error" and "buried" in i.message for i in document.validate()))

    def test_damage_precedes_goal_and_coin_in_json(self):
        data = new_map(8,8)
        data["objects"][1].update(x=64,y=162)
        data["objects"].extend([dict(id="coin",type="coin",x=64,y=162),dict(id="danger",type="hazard",x=64,y=162)])
        scene = ClassicScene(TileMap(data),SETTINGS)
        scene.update(1/60,Actions(frozenset(),frozenset(),frozenset()))
        self.assertFalse(scene.won)
        self.assertFalse(scene.collected)
        self.assertEqual(scene.deaths,1)

    def test_editor_incremental_analysis_replay_and_invalidation(self):
        editor = LevelEditor(lambda level:ClassicScene(level,SETTINGS),SETTINGS["bindings"],MapDocument(new_map(8,8)))
        before = deepcopy(editor.document.data)
        editor.show_validation()
        self.assertIsNotNone(editor.analysis)
        for _ in range(2000):
            editor.update(0)
            if editor.analysis_result:
                break
        self.assertEqual(editor.analysis_result.status,"solved")
        editor.draw()
        editor.start_solution()
        for _ in range(len(editor.solution_actions)+1):
            editor.update(1/60)
        self.assertTrue(editor.preview.won)
        editor.stop_preview()
        self.assertEqual(editor.document.data,before)
        editor.document.paint(4,3,"#")
        editor.refresh()
        self.assertIsNone(editor.analysis_result)
        editor.show_validation()
        editor.close_validation()
        self.assertIsNone(editor.analysis)
