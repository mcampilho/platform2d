import os,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']=os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import pygame
from platform2d.tools.campaign_model import CampaignDocument
from platform2d.tools.campaign_editor import CampaignEditor
from platform2d.tools.level_editor import LevelEditor
from platform2d.tools.editor_model import MapDocument,new_map
from examples.editor.profiles import editor_profiles
from examples.campaign.scene import load_campaign

ASSETS=Path('examples/campaign/assets').resolve()

class CampaignDocumentTests(unittest.TestCase):
    def setUp(self): self.doc=CampaignDocument.load(ASSETS/'odyssey-duel.json')

    def test_order_history_and_start_preserve_all_stages(self):
        before=self.doc.snapshot(); last=self.doc.data['stages'][-1]['id']
        self.doc.move(7,0); self.assertEqual(self.doc.data['stages'][0]['id'],last)
        self.assertEqual(len(self.doc.data['stages']),8)
        self.doc.undo(); self.assertEqual(self.doc.snapshot(),before)
        self.doc.redo(); self.assertEqual(self.doc.data['stages'][0]['id'],last)

    def test_add_same_map_generates_unique_ids_and_remove_keeps_file(self):
        path=ASSETS/'duel-courtyard.json'; before=path.read_bytes()
        a=self.doc.add(path); b=self.doc.add(path)
        self.assertNotEqual(self.doc.data['stages'][a]['id'],self.doc.data['stages'][b]['id'])
        self.doc.remove(b); self.assertEqual(path.read_bytes(),before)

    def test_empty_campaign_editable_but_not_playable(self):
        doc=CampaignDocument(); doc.rename('Nova')
        with self.assertRaises(ValueError): doc.playable()
        self.assertTrue(any(i.severity=='error' for i in doc.inspect()[1]))

    def test_unique_ids_and_name_validation_are_atomic(self):
        before=self.doc.snapshot()
        for op in (lambda:self.doc.rename(' '),lambda:self.doc.rename_stage(0,'duel'),lambda:self.doc.rename_stage(0,'')):
            with self.assertRaises(ValueError): op()
            self.assertEqual(self.doc.snapshot(),before)

    def test_save_as_rebases_paths_and_does_not_modify_maps(self):
        originals={s['map']:Path(s['map']).read_bytes() for s in self.doc.data['stages']}
        # Relative references require the destination and maps on the same drive.
        # Hosted Windows runners may keep the checkout on D: and TEMP on C:.
        with tempfile.TemporaryDirectory(dir=ASSETS) as folder:
            target=Path(folder)/'nested'/'campaign.json'; self.doc.save(target)
            loaded=CampaignDocument.load(target)
            self.assertEqual(loaded.snapshot(),self.doc.snapshot())
            self.assertFalse(self.doc.dirty)
            self.assertEqual(load_campaign(target)[1],self.doc.playable()[1])
            raw=json.loads(target.read_text(encoding='utf-8'))
            self.assertTrue(all(not Path(s['map']).is_absolute() for s in raw['stages']))
        for path,raw in originals.items(): self.assertEqual(Path(path).read_bytes(),raw)

    def test_save_as_preserves_absolute_paths_when_relative_paths_are_unavailable(self):
        originals={s['map']:Path(s['map']).read_bytes() for s in self.doc.data['stages']}
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'nested'/'campaign.json'
            # Reproduce os.path.relpath's cross-drive failure on any test machine.
            with patch('platform2d.tools.campaign_model.os.path.relpath',
                       side_effect=ValueError('path and start are on different drives')) as relative:
                self.doc.save(target)
            self.assertEqual(relative.call_count,len(originals))
            raw=json.loads(target.read_text(encoding='utf-8'))
            self.assertTrue(all(Path(s['map']).is_absolute() for s in raw['stages']))
            self.assertEqual([Path(s['map']) for s in raw['stages']],
                             [Path(s['map']) for s in self.doc.data['stages']])
            self.assertEqual(CampaignDocument.load(target).snapshot(),self.doc.snapshot())
            self.assertEqual(load_campaign(target)[1],self.doc.playable()[1])
            self.assertFalse(self.doc.dirty)
        for path,raw in originals.items(): self.assertEqual(Path(path).read_bytes(),raw)

    def test_save_failure_preserves_previous_file_and_saved_state(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'campaign.json'; self.doc.save(target); before=target.read_bytes()
            self.doc.rename('Alterada')
            with patch('platform2d.tools.campaign_model.os.replace',side_effect=OSError('failed')):
                with self.assertRaises(OSError): self.doc.save()
            self.assertEqual(target.read_bytes(),before); self.assertTrue(self.doc.dirty)
            self.assertEqual(list(target.parent.glob('*.tmp')),[])

    def test_cannot_overwrite_referenced_map(self):
        path=Path(self.doc.data['stages'][0]['map']); before=path.read_bytes()
        with self.assertRaises(ValueError): self.doc.save(path)
        self.assertEqual(path.read_bytes(),before)

    def test_missing_reference_can_be_opened_and_repaired(self):
        data=self.doc.snapshot(); data['stages'][0]['map']=str(ASSETS/'missing.json')
        doc=CampaignDocument(data)
        self.assertTrue(any(i.severity=='error' for i in doc.inspect()[1]))
        with self.assertRaises(ValueError): doc.playable()
        doc.replace(0,ASSETS/'odyssey-launch.json')
        self.assertEqual(len(doc.playable()[2]),8)

    def test_incompatible_profile_and_duplicate_ids_block_export(self):
        before=self.doc.snapshot()
        with self.assertRaises(ValueError): self.doc.add('examples/classic/assets/station.json')
        self.assertEqual(self.doc.snapshot(),before)
        data=self.doc.snapshot(); data['stages'][1]['id']=data['stages'][0]['id']
        with self.assertRaises(ValueError): CampaignDocument(data).playable()

    def test_bad_json_and_manifest_are_rejected(self):
        for data in ([],{},dict(format='platform2d.campaign',version=True,name='X',stages=[])):
            with self.assertRaises(ValueError): CampaignDocument(data)

    def test_preview_suffix_does_not_change_start_or_document(self):
        before=self.doc.snapshot(); _,ids,docs=self.doc.playable(7)
        self.assertEqual(ids,['duel']); self.assertEqual(len(docs),1)
        self.assertEqual(before,self.doc.snapshot())
        with self.assertRaises(ValueError): self.doc.playable(8)

    def test_stage_limit(self):
        doc=CampaignDocument()
        for _ in range(32): doc.add(ASSETS/'duel-courtyard.json')
        before=doc.snapshot()
        with self.assertRaises(ValueError): doc.add(ASSETS/'duel-courtyard.json')
        self.assertEqual(before,doc.snapshot())

class CampaignEditorTests(unittest.TestCase):
    def setUp(self):
        pygame.init(); self.profiles=editor_profiles()
        self.doc=CampaignDocument.load(ASSETS/'odyssey-duel.json')
        self.editor=CampaignEditor(self.doc,self.profiles)
    def tearDown(self):
        if self.editor.controls: self.editor.stop_preview()
        pygame.quit()

    def test_keyboard_reorder_and_undo(self):
        e=self.editor; before=self.doc.snapshot(); e.stage_index=1
        e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_UP,mod=pygame.KMOD_SHIFT))
        self.assertEqual(e.stage_index,0); self.assertNotEqual(self.doc.snapshot(),before)
        e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_z,mod=pygame.KMOD_CTRL))
        self.assertEqual(self.doc.snapshot(),before)

    def test_preview_starts_selected_without_save_slot_or_map_changes(self):
        e=self.editor; before=self.doc.snapshot(); e.stage_index=7; e.start_preview(True)
        self.assertEqual(e.preview.progress.current,'duel')
        self.assertFalse(hasattr(e.preview,'slot'))
        e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT,mod=0))
        for _ in range(20): e.update(1/60)
        self.assertGreater(e.preview.active.player.body.x,64)
        e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE,mod=0))
        self.assertIsNone(e.preview); self.assertEqual(self.doc.snapshot(),before)

    def test_missing_map_validation_stays_in_editor(self):
        self.doc.data['stages'][0]['map']=str(ASSETS/'missing.json')
        self.editor.show_validation()
        self.assertEqual(self.editor.modal['kind'],'choice')
        self.assertTrue(any(label.startswith('ERRO') for label,_ in self.editor.modal['items']))

    def test_unsaved_exit_offers_cancel(self):
        e=self.editor; self.doc.rename('Alterada')
        e.handle_event(pygame.event.Event(pygame.QUIT))
        self.assertTrue(e.running); self.assertEqual(e.modal['kind'],'confirm')
        e.close_modal_action(e.modal['buttons'][-1][1]); self.assertTrue(e.running)

    def test_workspace_available_from_map_editor(self):
        classic=self.profiles['classic']; parent=LevelEditor(classic['factory'],classic['bindings'],profiles=self.profiles)
        parent.document.saved=parent.document.snapshot()
        parent.new_dialog(); label,callback=parent.modal['buttons'][-1]
        self.assertEqual(label,'Campanha'); parent.close_modal_action(callback)
        self.assertIsInstance(parent.workspace,CampaignEditor)
        parent.workspace.campaign.saved=parent.workspace.campaign.snapshot()
        parent.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4,mod=0))
        self.assertIsNone(parent.workspace)

    def test_edit_map_return_refreshes_without_changing_campaign_sequence(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'map.json'
            data=json.loads((ASSETS/'duel-courtyard.json').read_text(encoding='utf-8')); path.write_text(json.dumps(data),encoding='utf-8')
            doc=CampaignDocument(); doc.add(path); e=CampaignEditor(doc,self.profiles)
            before=doc.snapshot(); e.edit_map(); e.map_editor.document.rename('Nome novo')
            e.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F4,mod=0))
            self.assertIsNotNone(e.map_editor.modal)
            # Save and return through the same callback used by the dialog.
            e.map_editor.close_modal_action(e.map_editor.modal['buttons'][0][1])
            self.assertIsNone(e.map_editor); self.assertEqual(e.reports[0].name,'Nome novo')
            self.assertEqual(doc.snapshot(),before)
