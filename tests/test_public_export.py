"""Host-only release-transform checks. No TV, subprocess or network operations."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('public_export',Path(__file__).parents[1]/'tools/export_public.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ExportChecks(unittest.TestCase):
    def test_token_identity_and_payload_redaction(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'private').mkdir();(root/'private/s95f.token').write_text('87654321')
            redact=m.redactor(root)
            text=redact('87654321 192.168.5.201 192.168.5.10 aa:bb:cc:dd:ee:ff 12345678-1234-4123-8123-123456789abc '+'A'*600)
            for value in ['87654321','192.168.','aa:bb:cc:dd:ee:ff','12345678-1234','A'*600]:self.assertNotIn(value,text)
            self.assertIn('198.51.100.20',text)
            # Scientific protocol UUID uses version-zero and must survive.
            self.assertEqual(redact('22222221-0000-0000-0000-000000000001'),'22222221-0000-0000-0000-000000000001')
    def test_scientific_setting_keys_and_identifier_aliases(self):
        with tempfile.TemporaryDirectory() as d:
            redact=m.redactor(Path(d))
            self.assertEqual(redact('db/home/screen_tab = 1'),'db/home/screen_tab = 1')
            self.assertEqual(redact('/home/alice/fixture'),'/home/researcher/fixture')
        saved=m.NAME_REPLACEMENTS
        try:
            m.NAME_REPLACEMENTS=[('samplelabel','program_a')]
            changed=m.public_name('def test_samplelabel_fixture(): pass')
            import ast
            ast.parse(changed)
            self.assertIn('test_program_a_fixture',changed)
        finally:m.NAME_REPLACEMENTS=saved
    def test_annotated_disassembly_preserved_whole_dump_omitted(self):
        self.assertEqual(m.disposition(Path('study/function-proof.disasm'),b'245934: add r0, r1',[])[0],'export')
        self.assertEqual(m.disposition(Path('study/vendor.full.disasm'),b'245934: add r0, r1',[])[0],'omit')
        self.assertEqual(m.disposition(Path('study/vendor.bin'),b'abc',[])[0],'omit')
    def test_json_keys_are_redacted_and_technical_values_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            obj={'/home/alice/a':{'token':'REAL_SECRET','count':56,'title':'private viewing title','paramTypes':0x01010d0d}}
            got=m.scrub_json(obj,m.redactor(Path(d)))
            self.assertIn('/home/researcher/a',got)
            item=got['/home/researcher/a'];self.assertEqual(item['count'],56);self.assertEqual(item['paramTypes'],0x01010d0d)
            self.assertNotIn('REAL_SECRET',json.dumps(got));self.assertNotIn('private viewing title',json.dumps(got))
    def test_envelope_extraction_drops_staging_and_session(self):
        obj={'host':'192.168.5.201','authenticated':True,'commands':[{'command':'read RT','stdout':'RT=1','exit_code':0},{'command':'base64 -d > payload','stdout':'payloadsecret','exit_code':0}], 'transport_stdout':{'data':'privateencoded'}}
        got=m.extract_observations(obj,lambda x:x)
        self.assertEqual(len(got['observations']),1)
        self.assertEqual(got['observations'][0]['stdout'],'RT=1')
        for value in ['authenticated','payloadsecret','privateencoded','192.168.']:self.assertNotIn(value,json.dumps(got))
    def test_opaque_omission_and_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';dest=Path(d)/'public';root.mkdir();dest.mkdir();(root/'private').mkdir()
            (root/'private/s95f.token').write_text('87654321');(root/'proof.md').write_text('observed 192.168.2.201')
            m.export(root,dest)
            records=json.loads((dest/'manifests/source-dispositions.json').read_text())['records']
            secret=next(r for r in records if r['disposition']=='omit')
            self.assertNotIn('source_sha256',secret);self.assertNotIn('public_path',secret)
            public=next(r for r in records if r['disposition']=='export')
            self.assertNotEqual(public['source_sha256'],public['public_sha256'])
            self.assertEqual(m.sha((dest/public['public_path']).read_bytes()),public['public_sha256'])

if __name__=='__main__':unittest.main()
