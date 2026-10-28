"""Boundary regressions use synthetic identities only; no target or network I/O."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


exporter = module('uuid_exporter', 'tools/export_public.py')
verifier = module('uuid_verifier', 'tools/verify_public.py')
SYNTHETIC = '12345678-1234-4123-8123-123456789abc'
SENTINEL = '00000000-0000-4000-8000-000000000000'
LINUX_TYPE = '0fc63daf-8483-4772-8e79-3d69d8477de4'
PROTOCOL_V0 = '22222221-0000-0000-0000-000000000001'


class UuidPrivacyChecks(unittest.TestCase):
    def redact(self, text):
        # Existing directory, with no credential acquisition or private state.
        with tempfile.TemporaryDirectory() as directory:
            return exporter.redactor(Path(directory))(text)

    def verify_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'research').mkdir()
            (root / 'manifests').mkdir()
            raw = text.encode()
            (root / 'research/sample.txt').write_bytes(raw)
            row = {'disposition': 'export', 'public_path': 'research/sample.txt',
                   'public_bytes': len(raw),
                   'public_sha256': hashlib.sha256(raw).hexdigest()}
            (root / 'manifests/source-dispositions.json').write_text(
                json.dumps({'records': [row]}))
            return verifier.verify(root)

    def test_plain_prose_and_quote_boundaries(self):
        for before, after in [('', ''), ('Boot ID stayed', ', uptime'),
                              ('same boot ID', '.'), ('"', '"'), ('X', 'Y')]:
            with self.subTest(before=before, after=after):
                self.assertEqual(self.redact(before + SYNTHETIC + after),
                                 before + SENTINEL + after)

    def test_literal_and_multiply_escaped_newlines(self):
        for depth in range(7):
            delimiter = '\n' if depth == 0 else '\\' * (2 ** (depth - 1)) + 'n'
            with self.subTest(depth=depth):
                self.assertEqual(self.redact(delimiter + SYNTHETIC + delimiter),
                                 delimiter + SENTINEL + delimiter)

    def test_unicode_quote_escape_and_nested_escape_boundaries(self):
        for depth in range(6):
            delimiter = '\\' * (2 ** depth) + 'u0022'
            with self.subTest(depth=depth):
                self.assertEqual(self.redact(delimiter + SYNTHETIC + delimiter),
                                 delimiter + SENTINEL + delimiter)

    def test_adjacent_hex_characters_do_not_hide_uuid(self):
        self.assertEqual(self.redact('dead' + SYNTHETIC + 'beef'),
                         'dead' + SENTINEL + 'beef')

    def test_all_supported_versions_variants_and_uppercase(self):
        for version in '12345':
            for variant in '89ab':
                value = (SYNTHETIC[:14] + version + SYNTHETIC[15:19]
                         + variant + SYNTHETIC[20:]).upper()
                with self.subTest(version=version, variant=variant):
                    self.assertEqual(self.redact(value), SENTINEL)

    def test_version_zero_protocol_remains_scientific(self):
        for value in [PROTOCOL_V0, '00000000-0000-0000-0000-000000000000']:
            self.assertEqual(self.redact(value), value)

    def test_only_explicit_public_type_and_sentinel_remain(self):
        for value in [LINUX_TYPE, LINUX_TYPE.upper(), SENTINEL]:
            self.assertEqual(self.redact('GUID' + value), 'GUID' + value)
        near_type = LINUX_TYPE[:-1] + '5'
        self.assertEqual(self.redact(near_type), SENTINEL)

    def test_correction_is_idempotent(self):
        once = self.redact('\\n' + SYNTHETIC + '\\u0022')
        self.assertEqual(self.redact(once), once)

    def test_nested_json_stays_parseable_with_science_unchanged(self):
        obj = {'nested': json.dumps({'stdout': '\n' + SYNTHETIC + '\n'}),
               'limit': 40, 'scores': [0, 40, 42], 'phase': 'ReadyForHeader'}
        corrected = json.loads(self.redact(json.dumps(obj)))
        self.assertEqual(corrected['scores'], obj['scores'])
        self.assertEqual(corrected['limit'], 40)
        self.assertEqual(corrected['phase'], obj['phase'])
        self.assertEqual(json.loads(corrected['nested'])['stdout'],
                         '\n' + SENTINEL + '\n')

    def test_jsonl_end_to_end_export_replaces_escaped_boot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'input'
            out = Path(directory) / 'output'
            root.mkdir()
            out.mkdir()
            rows = [{'stdout': '\n' + SYNTHETIC + '\n', 'count': value}
                    for value in [18, 19]]
            (root / 'sample.jsonl').write_text(
                ''.join(json.dumps(row) + '\n' for row in rows))
            exporter.export(root, out)
            text = (out / 'research/sample.jsonl').read_text()
            self.assertNotIn(SYNTHETIC, text)
            got = [json.loads(line) for line in text.splitlines()]
            self.assertEqual([row['count'] for row in got], [18, 19])
            self.assertTrue(all(row['stdout'] == '\n' + SENTINEL + '\n'
                                for row in got))
            self.assertEqual(verifier.verify(out)['errors'], [])

    def test_independent_verifier_rejects_each_hidden_form(self):
        cases = [SYNTHETIC, '\\n' + SYNTHETIC + '\\n',
                 '\\\\n' + SYNTHETIC, '\\u0022' + SYNTHETIC,
                 '\\\\u0022' + SYNTHETIC, 'stayed' + SYNTHETIC,
                 'dead' + SYNTHETIC + 'beef']
        for text in cases:
            with self.subTest(text=text):
                errors = self.verify_text(text)['errors']
                self.assertEqual([e['kind'] for e in errors],
                                 ['boot-or-session-uuid'])
                # Verification reports location, never the matched value.
                self.assertNotIn(SYNTHETIC, json.dumps(errors))

    def test_independent_verifier_allows_sentinel_and_public_protocol(self):
        self.assertEqual(self.verify_text(
            SENTINEL + ' GUID' + LINUX_TYPE + ' ' + PROTOCOL_V0)['errors'], [])

    def test_verifier_checks_past_allowed_first_matches(self):
        errors = self.verify_text(SENTINEL + ' GUID' + LINUX_TYPE
                                  + '\\n' + SYNTHETIC)['errors']
        self.assertEqual([e['kind'] for e in errors], ['boot-or-session-uuid'])

    def test_exporter_version_records_correction(self):
        self.assertEqual(exporter.VERSION, '2026-10-28.4')


if __name__ == '__main__':
    unittest.main()
