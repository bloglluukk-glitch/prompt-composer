"""Portable behavioral checks. Uses only the Python standard library."""
from pathlib import Path
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import contextmanager

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
from prompt_composer import PromptComposer, dry_run_evaluation, load_json, run_all_fixtures, selected_ids, render_markdown

@contextmanager
def temporary_directory():
    base=Path(os.environ.get('PROMPT_COMPOSER_TEST_TMPDIR',tempfile.gettempdir())).resolve()
    with tempfile.TemporaryDirectory(prefix='prompt-composer-test-',dir=base) as folder:
        assert Path(folder).resolve().is_relative_to(base)
        yield folder


class ComposerChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.composer = PromptComposer()
        cls.runs = run_all_fixtures(cls.composer)

    def test_all_twelve_examples(self):
        self.assertEqual(self.runs['summary'], {'fixtures': 12, 'passed': 12, 'failed': 0})

    def test_language_pairs_select_same_knowledge(self):
        for path in (HERE/'examples'/'ko').glob('*.json'):
            ko=self.composer.compose(load_json(path))
            en=self.composer.compose(load_json(HERE/'examples'/'en'/path.name))
            self.assertEqual(selected_ids(ko), selected_ids(en), path.name)

    def test_english_prompts_have_no_korean(self):
        for run in self.runs['dry_runs']:
            for key in ('concise_en','detailed_en'):
                self.assertIsNone(re.search(r'[가-힣]',run['composer_result']['prompt'][key]))

    def test_korean_prompts_and_schedule(self):
        request=load_json(HERE/'examples'/'ko'/'01_coat_reveal.json')
        result=self.composer.compose(request)['composer_result']
        self.assertIn('코팅',result['prompt']['detailed_ko'])
        self.assertIn('시간 계획',result['prompt']['detailed_ko'])
        for step in result['temporal_sequence']:
            self.assertTrue(re.search(r'[가-힣]',step['action_ko']))
            self.assertEqual(step['basis'],'editorial_plan_not_measured')

    def test_explicit_delivery_settings_survive(self):
        request=load_json(HERE/'examples'/'en'/'01_coat_reveal.json')
        body=self.composer.compose(request)['composer_result']
        self.assertEqual(body['output_request'],request['output'])
        for value in ['duration in seconds: 5','fps: 24','aspect ratio: 16:9','resolution: 1920x1080']:
            self.assertIn(value,body['prompt']['detailed_en'])

    def test_unspecified_delivery_is_not_invented(self):
        body=self.composer.compose({'user_brief':'A satin-metal product.','subject':{'description':'a product'}})['composer_result']
        self.assertEqual(body['output_request'],{})
        self.assertNotIn('fps:',body['prompt']['detailed_en'])
        self.assertEqual(body['curve_translation']['status'],'unspecified')

    def test_partial_curve_does_not_invent_rebound(self):
        body=self.composer.compose({'user_brief':'A product follows a speed ramp.','curve':{'curve_data':{'acceleration':'fast'}}})['composer_result']
        self.assertNotIn('rebound',body['curve_translation']['prompt_fragment'])
        self.assertNotIn('overshoot',body['curve_translation']['prompt_fragment'])

    def test_profile_id_alone_is_unresolved(self):
        body=self.composer.compose({'user_brief':'A product moves.','curve':{'curve_profile_id':'example-profile'}})['composer_result']
        self.assertTrue(body['curve_translation']['unresolved_profile'])
        self.assertEqual(body['curve_translation']['prompt_fragment'],'')

    def test_unmapped_subject_is_disclosed(self):
        body=self.composer.compose({'user_brief':'새틴 제품이 있다.','subject':{'description':'가상의 새로운 물체'}})['composer_result']
        self.assertIn('the specified subject',body['prompt']['concise_en'])
        self.assertTrue(any('no deterministic English mapping' in x['issue'] for x in body['uncertainty']))

    def test_generic_words_do_not_select_everything(self):
        result=self.composer.compose({'user_brief':'A beautiful product in a studio.','subject':{'description':'a product'}})
        self.assertEqual(selected_ids(result),set())

    def test_no_transmission_for_subsurface_brief(self):
        result=self.composer.compose(load_json(HERE/'examples'/'en'/'02_sss_backlight.json'))
        self.assertIn('RS-VM-016',selected_ids(result));self.assertNotIn('RS-VM-015',selected_ids(result))

    def test_derived_shafts_keep_components(self):
        result=self.composer.compose(load_json(HERE/'examples'/'en'/'05_fog_godrays.json'))
        selected=selected_ids(result)
        self.assertTrue({'RS-VM-030','RS-VM-029','RS-VM-003'}<=selected)
        derived=[x for x in result['composer_result']['provenance'] if x['source_id']=='RS-VM-030'][0]
        self.assertTrue(derived['derived_only'])

    def test_invalid_input_fails_helpfully(self):
        for request in [{'user_brief':''},{'user_brief':'x','input_mode':'bad'},
                        {'user_brief':'x','model_target':'provider-specific'},
                        {'user_brief':'x','subject':[]},
                        {'user_brief':'x','output':{'fps':True}},
                        {'user_brief':'x','output':{'duration_seconds':-1}},
                        {'user_brief':'x','output':{'duration_seconds':float('inf')}},
                        {'user_brief':'x','output':{'type':'image'}},
                        {'user_brief':'x','input_mode':'start_end'},
                        {'user_brief':'x','curve':{'curve_data':{'rebound_count':-1}}}]:
            with self.subTest(request=request):
                with self.assertRaises(ValueError):self.composer.compose(request)

    def test_negative_constraints_survive(self):
        request=load_json(HERE/'examples'/'en'/'04_rack_focus.json')
        body=self.composer.compose(request)['composer_result']
        self.assertEqual(body['request_constraints'],request['constraints'])
        self.assertNotIn('RS-VM-027',selected_ids({'composer_result':body}))

    def test_source_files_stay_unchanged(self):
        self.assertTrue(self.composer.source_integrity()['unchanged'])

    def test_no_network_and_no_asset_opening(self):
        import socket
        with patch.object(socket,'socket',side_effect=AssertionError('No network allowed')):
            request=load_json(HERE/'examples'/'en'/'01_coat_reveal.json')
            request['assets']['start_image']='never-open-this-placeholder.png'
            result=self.composer.compose(request)
            self.assertTrue(result['composer_result']['source_integrity']['unchanged'])

    def test_markdown_in_both_languages(self):
        result=self.composer.compose(load_json(HERE/'examples'/'en'/'03_micro_imperfection.json'))
        self.assertIn('## Selection rationale',render_markdown(result,'en'))
        self.assertIn('## 선택 근거',render_markdown(result,'ko'))

    def test_run_from_unrelated_working_directory(self):
        with temporary_directory() as temp:
            run=subprocess.run([sys.executable,'-B',str(HERE/'prompt_composer.py'),'--input',str(HERE/'examples'/'en'/'04_rack_focus.json')],cwd=temp,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr.decode(errors='replace'))
            self.assertIn('RS-VM-023',selected_ids(json.loads(run.stdout)))

    def test_cli_output_does_not_overwrite(self):
        with temporary_directory() as temp:
            output=Path(temp)/'plan.md';output.write_text('keep me',encoding='utf-8')
            run=subprocess.run([sys.executable,'-B',str(HERE/'prompt_composer.py'),'--input',str(HERE/'examples'/'en'/'04_rack_focus.json'),'--format','markdown','--language','en','--output',str(output)],cwd=temp,capture_output=True)
            self.assertEqual(run.returncode,2);self.assertEqual(output.read_text(encoding='utf-8'),'keep me')

    def test_fresh_copy_with_no_private_database(self):
        with temporary_directory() as temp:
            dest=Path(temp)/'portable'
            shutil.copytree(HERE,dest,ignore=shutil.ignore_patterns('.git','__pycache__','outputs'))
            run=subprocess.run([sys.executable,'-B',str(dest/'prompt_composer.py'),'--all-fixtures'],cwd=temp,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr.decode(errors='replace'))
            self.assertEqual(json.loads(run.stdout)['summary']['passed'],12)


if __name__=='__main__':
    unittest.main(verbosity=2)
