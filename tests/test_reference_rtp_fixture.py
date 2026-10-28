"""Second-run fixed-reference equality, corrupted evidence and scope limits."""
import base64,copy,hashlib,importlib.util,json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_reference_rtp',ROOT/'tools/verify_reference_rtp.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class ReferenceRtpChecks(unittest.TestCase):
    def setUp(self):self.fixture=json.loads((ROOT/'fixtures/rtp-reference-run.json').read_text())

    def test_distinct_second_run_and_conditional_bottom_match(self):
        r=m.verify(self.fixture)
        self.assertEqual(r['rawWindows'],52)
        self.assertEqual(r['rawBytesIncludingCheckpoints'],5402)
        self.assertEqual(r['dpCleanScores'],[0,0,0,0,28])
        self.assertEqual(r['dpPostfaultA0'],42)
        self.assertEqual(r['dpSoftwareBracket']['widthUs'],253126)
        self.assertEqual(r['conditionalBottomMatches'],41)
        self.assertEqual(r['topMismatches'],41)
        self.assertEqual(r['fixedCandidates']['bottom'][622],454)
        for key in ('absent622623BSourceObserved','actualFixedABranchProven','recordEpochProven','preventionEstablished','physicalPictureObserved'):
            self.assertFalse(r[key])

    def test_ignored_tail_is_not_an_extra_sample(self):
        for label in ('dtBaseline','dtFault'):
            for w in self.fixture[label]['windows']:
                if w['name'].startswith('fixed-'):
                    raw=bytearray(base64.b64decode(w['base64']));raw[-2]^=0xff;raw[-1]^=0xff
                    w.update(base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(m.verify(self.fixture)['conditionalBottomMatches'],41)

    def test_mutations_and_private_metadata_rejected(self):
        cases=[]
        def case(change):
            f=copy.deepcopy(self.fixture);change(f);cases.append(f)
        case(lambda f:f['dp40']['scoreCheckpoints'].update(count=6))
        case(lambda f:f['dp40'].update(headersSent=49))
        case(lambda f:f['dp40'].update(physicalPictureObserved=True))
        case(lambda f:f['dtFault'].update(packingQualified=False))
        case(lambda f:f['dtFault'].update(bindingChecks=[]))
        case(lambda f:f['dtFault'].update(device=59))
        case(lambda f:f['dtFault'].update(atomicSnapshot=True))
        case(lambda f:f['dtFault']['windows'][10].update(address=0x47015470))
        case(lambda f:f['dtFault']['windows'][11].update(bytes=160))
        case(lambda f:f['dtFault']['steps'][23].update(count=103))
        case(lambda f:f['dtFault']['steps'][20].update(after='Unknown'))
        for index,f in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises((ValueError,KeyError,TypeError)):m.verify(f)
        text=json.dumps(self.fixture)
        for forbidden in ('"device"','"bindingChecks"','"boot"','/home/','/sys/','192.168.'):
            self.assertNotIn(forbidden,text)


if __name__=='__main__':unittest.main()
