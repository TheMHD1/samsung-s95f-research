"""Public scientific-fixture validation and deliberately damaged evidence cases."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_onset',ROOT/'tools/verify_onset.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class OnsetChecks(unittest.TestCase):
    def setUp(self):self.fixture=json.loads((ROOT/'fixtures/onset-cb.json').read_text())
    def test_retained_window_bytes_and_after_key_transition(self):
        result=m.verify(self.fixture)
        self.assertEqual(result['rawWindows'],18)
        self.assertEqual(result['softwareBracket']['widthUs'],250294)
        self.assertGreater(result['softwareBracket']['beforeUs'],result['keyUpReturnUs'])
        self.assertIsNone(result['exactPhysicalTransitionTimeUs'])
        self.assertFalse(result['causalityEstablished'])
    def test_damaged_or_overclaimed_evidence_is_rejected(self):
        cases=[]
        def case(change):
            fixture=copy.deepcopy(self.fixture);change(fixture);cases.append(fixture)
        case(lambda f:f['native']['retained'][0]['windows'][0].update(rawBase64='AAAA'))
        case(lambda f:f['native']['retained'][0]['windows'][0].update(address='0x47012404'))
        case(lambda f:f['native']['retained'][2]['windows'][0]['observedRtState'].update(fault=0))
        case(lambda f:f['native']['retained'][2]['transfers'][0].update(direction='IN'))
        case(lambda f:f['native'].update(bulkTransfers=71))
        case(lambda f:f['native'].update(writes=True))
        case(lambda f:f['native']['intervention']['calls'][1].update(timedOut=True))
        case(lambda f:f['native']['intervention']['calls'][1].update(afterUs=167671260500))
        case(lambda f:f['native']['retained'][1]['transfers'][0].update(beforeUs=0))
        case(lambda f:f['ownerObservation'].update(exactPhysicalTransitionTimeUs=167671260439))
        case(lambda f:f['ownerObservation'].update(causalityEstablished=True))
        for index,fixture in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises(ValueError):m.verify(fixture)

if __name__=='__main__':unittest.main()
