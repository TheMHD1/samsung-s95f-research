"""Offline scientific-fixture checks and corrupted/overclaimed evidence cases."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_rtp',ROOT/'tools/verify_rtp.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class RtpFixtureChecks(unittest.TestCase):
    def setUp(self):self.fixture=json.loads((ROOT/'fixtures/rtp-dp40-dm.json').read_text())

    def test_scores_records_and_scope(self):
        result=m.verify(self.fixture)
        self.assertEqual(result['rawWindows'],48)
        self.assertEqual(result['rawBytesIncludingCheckpoints'],4986)
        self.assertEqual(result['dpCleanScores'],[0,0,0,0,38])
        self.assertEqual(result['dpPostfaultA0'],42)
        self.assertEqual(result['dpSoftwareBracket']['widthUs'],249541)
        self.assertEqual(result['dmConditionalAByX'][624],3052)
        for k in ('recordEpochProven','actualFixedABranchProven','physicalPictureObserved','preventionEstablished'):
            self.assertFalse(result[k])

    def test_fixture_has_no_device_auth_or_network_metadata(self):
        forbidden={'device','boot','boot_id','bootId','bindingChecks','bindingQualified','identity','token','nonce','hostname','serverIpv4','transport_stdout','transport_stderr'}
        def walk(obj):
            if isinstance(obj,dict):
                self.assertFalse(forbidden.intersection(obj))
                for value in obj.values():walk(value)
            elif isinstance(obj,list):
                for value in obj:walk(value)
        walk(self.fixture)
        text=json.dumps(self.fixture)
        self.assertNotIn('/home/',text)
        self.assertNotIn('/sys/',text)
        self.assertNotIn('192.168.',text)

    def test_damaged_or_overclaimed_evidence_rejected(self):
        cases=[]
        def case(change):
            fixture=copy.deepcopy(self.fixture);change(fixture);cases.append(fixture)
        case(lambda f:f['dp40'].update(device=58))
        case(lambda f:f['dp40'].update(physicalPictureObserved=True))
        case(lambda f:f['dp40'].update(writes=False))
        case(lambda f:f['dp40'].update(headersSent=47))
        case(lambda f:f['dp40'].update(protocolPhase='Unknown'))
        case(lambda f:f['dp40']['scoreCheckpoints'].update(recordBytes=32))
        case(lambda f:f['dp40']['scoreCheckpoints'].update(count=6))
        case(lambda f:f['dp40']['scoreCheckpoints'].update(rawBase64='AAAA'))
        case(lambda f:f['dp40']['retained'][0]['windows'][0].update(address='0x60000000'))
        case(lambda f:f['dp40']['retained'][0]['windows'][0].update(rawBase64='AAAA'))
        case(lambda f:f['dp40']['retained'][2]['windows'][0]['observedRtState'].update(fault=0))
        case(lambda f:f['dp40']['retained'][0]['transfers'][0].update(errno=5))
        case(lambda f:f['dp40']['intervention']['calls'][1].update(afterUs=178075994145))
        case(lambda f:f['dp40']['intervention']['calls'][0].update(exitCode=False))
        case(lambda f:f['dmFault'].update(atomicSnapshot=True))
        case(lambda f:f['dmFault'].update(uiOperations=False))
        case(lambda f:f['dmFault']['windows'][6].update(bytes=95))
        case(lambda f:f['dmBaseline']['windows'][0].update(base64='AAAA'))
        case(lambda f:f['dmFault']['steps'][1].update(after='Unknown'))
        case(lambda f:f['dmFault']['steps'][1].update(count=255))
        for index,fixture in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises((ValueError,KeyError,TypeError)):m.verify(fixture)


if __name__=='__main__':unittest.main()
