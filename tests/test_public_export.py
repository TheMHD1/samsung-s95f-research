"""Host-only release-transform checks. No TV, subprocess or network operations."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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
    def test_completed_reader_license_preserved_without_private_source_tree(self):
        notice=b'MIT License\nCopyright upstream author\n'
        self.assertEqual(m.disposition(Path('reader/LICENSE.upstream-MIT'),notice,[])[0],'export')
        self.assertEqual(m.disposition(Path('reader/private/LICENSE.upstream-MIT'),notice,[])[0],'omit')
        self.assertEqual(m.disposition(Path('reader/LICENSE.unrecognized'),notice,[])[0],'omit')
    def test_private_filename_mapping_keys_withhold_names_sizes_and_hashes(self):
        source={'files':{'private/tls-config.json':{'bytes':270,'sha256':'a'*64},'section-plan.bin':{'bytes':72,'sha256':'b'*64},'Program.cs':{'bytes':17,'sha256':'c'*64}},'nested':{'work/PRIVATE/secret.txt':'secret-digest'}}
        got=m.scrub_json(source,lambda x:x)
        text=json.dumps(got)
        for private in ['tls-config.json','section-plan.bin','secret.txt','secret-digest','a'*64,'b'*64]:self.assertNotIn(private,text)
        self.assertEqual(got['files']['Program.cs'],source['files']['Program.cs'])
        self.assertEqual(got['files']['_public_export_omitted_private_reference_count'],2)
        self.assertEqual(got['nested']['_public_export_omitted_private_reference_count'],1)
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
    def test_large_omissions_are_hashed_without_full_reads(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';dest=Path(d)/'public';root.mkdir();dest.mkdir()
            blob=b'PK\x03\x04'+b'x'*8_000_001
            (root/'vendor.zip').write_bytes(blob)
            (root/'bulk.txt').write_bytes(blob[4:])
            original=Path.read_bytes
            def bounded_read(path):
                if path.parent==root:raise AssertionError('large input read in full')
                return original(path)
            with patch.object(Path,'read_bytes',bounded_read):m.export(root,dest)
            rows=json.loads((dest/'manifests/source-dispositions.json').read_text())['records']
            self.assertEqual({r['reason'] for r in rows},{'binary-firmware-media-or-build-product','bulk-acquisition-not-authored-analysis'})
            self.assertEqual({r['source_sha256'] for r in rows},{m.sha(blob),m.sha(blob[4:])})
            self.assertEqual(sum(r['bytes'] for r in rows),len(blob)*2-4)
            self.assertTrue(all(r['disposition']=='omit' and 'public_path' not in r for r in rows))
    def test_explicit_in_progress_scope_is_inventoried_without_reading(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';dest=Path(d)/'public';root.mkdir();dest.mkdir()
            (root/'draft-work.md').write_text('not frozen')
            with patch.object(Path,'read_bytes',side_effect=AssertionError('deferred input read')):
                m.export(root,dest,('draft-work',))
            manifest=json.loads((dest/'manifests/source-dispositions.json').read_text())
            self.assertEqual(manifest['deferred_name_fragments'],['draft-work'])
            row=manifest['records'][0]
            self.assertEqual(row['reason'],'in-progress-outside-public-snapshot')
            self.assertEqual(row['bytes'],10)
            self.assertNotIn('source_sha256',row)
            self.assertNotIn('public_path',row)
    def test_disappearing_deferred_input_stays_omitted_without_read(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';dest=Path(d)/'public';root.mkdir();dest.mkdir()
            (root/'draft-work.md').write_text('not frozen')
            original=Path.lstat
            def vanished(path,*args,**kwargs):
                if path.name=='draft-work.md':raise FileNotFoundError('simulated editor rename')
                return original(path,*args,**kwargs)
            with patch.object(Path,'lstat',vanished),patch.object(Path,'read_bytes',side_effect=AssertionError('deferred read')):
                m.export(root,dest,('draft-work',))
            manifest=json.loads((dest/'manifests/source-dispositions.json').read_text());row=manifest['records'][0]
            self.assertEqual(row['reason'],'in-progress-outside-public-snapshot');self.assertIn('size_unavailable',row)
            for key in ['bytes','source_sha256','public_path']:self.assertNotIn(key,row)
            self.assertEqual(manifest['totals']['disappeared_deferred_files'],1)
    def test_explicit_frozen_source_selection_excludes_future_files_before_read(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';dest=Path(d)/'public';root.mkdir();dest.mkdir()
            (root/'stable.md').write_text('known source');(root/'future.md').write_text('moving source')
            original=Path.read_bytes
            def guarded(path):
                if path.name=='future.md':raise AssertionError('unselected source read')
                return original(path)
            selected=frozenset({m.sha(b'stable.md')})
            with patch.object(Path,'read_bytes',guarded):m.export(root,dest,(),selected,'f'*64)
            manifest=json.loads((dest/'manifests/source-dispositions.json').read_text());rows=manifest['records']
            self.assertEqual(manifest['source_id_scope_sha256'],'f'*64)
            self.assertEqual((dest/'research/stable.md').read_text(),'known source')
            unknown=next(x for x in rows if x['source_id']==m.sha(b'future.md'))
            self.assertEqual(unknown['reason'],'outside-explicit-source-snapshot')
            for key in ['source_sha256','public_path','public_sha256']:self.assertNotIn(key,unknown)
    def test_nested_private_and_moved_sensitive_records_never_read_or_hashed(self):
        names = ['study/private/parsed.json', 'study/Private/tls.json',
                 'study/section-descriptors.json', 'study/parsed-header.json',
                 'study/numeric-reconciliation.json', 'study/tls-config.json',
                 'study/connection-private.json', 'study/listener-port.json',
                 'study/acquisition-private.json', 'study/section-plan.bin',
                 'study/itemsAESPassphraseEncrypted.txt', 'study/itemsPublicRSAKey.txt']
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';dest=Path(d)/'public';root.mkdir();dest.mkdir()
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('SENSITIVE_PRIVATE_CONTENT')
            with patch.object(Path,'read_bytes',side_effect=AssertionError('private content read')), \
                 patch.object(m,'file_sha',side_effect=AssertionError('private content hashed')):
                m.export(root,dest)
            rows=json.loads((dest/'manifests/source-dispositions.json').read_text())['records']
            self.assertEqual(len(rows),len(names))
            for row in rows:
                self.assertEqual(row['disposition'],'omit')
                for key in ['bytes','source_sha256','public_path','public_sha256']:
                    self.assertNotIn(key,row)
            self.assertEqual(list((dest/'research').rglob('*')),[])
            self.assertNotIn('SENSITIVE_PRIVATE_CONTENT',(dest/'manifests/source-dispositions.json').read_text())
    def test_oem_extraction_trees_and_acquisition_chunks_are_path_denied(self):
        for name in ['firmware-extracted-20261028/uImage',
                     'firmware-extracted-20261028/extraction-inventory.json',
                     'study/extracted-fs/etc/config.txt',
                     'study/partition-dump-01/partition',
                     'study/source-acquisition-01/vendor.c',
                     'study/SWUCoreTV.records/chunk-0001.json']:
            self.assertEqual(m.disposition(Path(name),b'plain OEM contents',[]),
                             ('omit','private-oem-extraction-or-acquisition'))
        # Original authored tools/reports remain eligible beside acquisitions.
        for name in ['study/target-file-acquisition-03/acquisition-tool-at-run.py',
                     'study/firmware-kernel-analysis/report.md',
                     'study/item_schema.py', 'study/test_item_schema.py']:
            self.assertEqual(m.disposition(Path(name),b'authored source or analysis',[])[0],'export')
        for name in ['sources/vendor/module.c','sources/vendor/LICENSE']:
            self.assertEqual(m.disposition(Path(name),b'upstream bytes',[Path('sources/vendor')]),
                             ('omit','upstream-source-referenced-not-vendored'))
    def test_mixed_inventories_omit_private_reference_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            redact=m.redactor(Path(d))
            obj={'files':[
                {'path':'study/private/raw.json','bytes':123,'sha256':'PRIVATE_HASH'},
                {'path':'study/tls-config.json','sha256':'PRIVATE_CONFIG_HASH'},
                {'path':'renamed.json','private':True,'sha256':'PRIVATE_MARKED_HASH'},
                {'path':'study/Program.cs','bytes':456,'sha256':'AUTHORED_HASH'}],
                'nonce_hex':'NONCE_SECRET','salt8':[1,2,3], 'signature256':'RAW_SIGNATURE',
                'salt_bytes':{'hex':'PRIVATE_SALT'},'rsa_signature_bytes':{'hex':'PRIVATE_SIGNATURE'},
                'signature_scope':'ciphertext', 'derive':1}
            got=m.scrub_json(obj,redact);text=json.dumps(got)
            for value in ['PRIVATE_HASH','PRIVATE_CONFIG_HASH','PRIVATE_MARKED_HASH',
                          'NONCE_SECRET','RAW_SIGNATURE','PRIVATE_SALT','PRIVATE_SIGNATURE','raw.json','renamed.json']:
                self.assertNotIn(value,text)
            self.assertNotIn('123',text)
            self.assertIn('AUTHORED_HASH',text);self.assertEqual(got['derive'],1)
            self.assertEqual(got['signature_scope'],'ciphertext')

if __name__=='__main__':unittest.main()
