"""Separate clean200/clean40 comparison and its publication boundaries."""
import base64,copy,hashlib,importlib.util,json,struct,sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('public_limit_rtp',ROOT/'tools/verify_limit_rtp.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LimitRtpChecks(unittest.TestCase):
    def setUp(self):self.fixture=json.loads((ROOT/'fixtures/rtp-limit-comparison.json').read_text())

    def test_both_clean_does_not_establish_prevention(self):
        r=m.verify(self.fixture)
        self.assertEqual(r['observe200']['maximumA0'],26)
        self.assertEqual(r['rechallenge40']['maximumA0'],24)
        self.assertEqual(r['observe200']['cleanCycles'],80)
        self.assertEqual(r['rechallenge40']['cleanCycles'],80)
        self.assertEqual(r['restoredValue'],40)
        self.assertEqual(r['checkpointBytes'],5440)
        for k in ('greaterThan40WitnessAt200','causalPreventionEstablished','physicalPictureObserved','callbackAdmissionReplayed'):
            self.assertFalse(r[k])
        self.assertEqual(r['targetOperations'],0)

    def test_modified_evidence_and_private_metadata_rejected(self):
        cases=[]
        def case(change):
            f=copy.deepcopy(self.fixture);change(f);cases.append(f)
        case(lambda f:f['source'].update(writeAddress='0x470124c0'))
        case(lambda f:f['set200'].update(bindingChecks=[]))
        case(lambda f:f['restore40'].update(device=60))
        case(lambda f:f['set200'].update(rootCauseFixEstablished=True))
        case(lambda f:f['set200'].update(limitMayHaveChanged=True))
        case(lambda f:f['restore40'].update(readbackVerified=False))
        case(lambda f:f['set200']['windows'][0].update(base64='AAAA'))
        case(lambda f:f['restore40']['steps'][11].update(after='Unknown'))
        case(lambda f:f['set200']['steps'][11].update(count=1))
        case(lambda f:f['observe200'].update(cleanCyclesCompleted=True))
        case(lambda f:f['rechallenge40'].update(onsetObserved=True))
        case(lambda f:f['observe200'].update(physicalPictureObserved=True))
        case(lambda f:f['observe200']['retained'][1]['windows'][0].update(address='0x470124c4'))
        case(lambda f:f['observe200']['scoreCheckpoints'].update(count=79))
        for i,f in enumerate(cases):
            with self.subTest(case=i):
                with self.assertRaises((ValueError,KeyError,TypeError)):m.verify(f)

    def test_rehashed_checkpoint_changes_do_not_evade_semantics(self):
        for offset,value in ((2,40),(6,41)):
            with self.subTest(offset=offset):
                f=copy.deepcopy(self.fixture);c=f['observe200']['scoreCheckpoints'];raw=bytearray(base64.b64decode(c['rawBase64']))
                struct.pack_into('<H'if offset==2 else'<I',raw,offset,value)
                c.update(rawBase64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
                with self.assertRaises(ValueError):m.verify(f)

    def test_rehashed_readback_must_show_restoration(self):
        w=self.fixture['restore40']['windows'][-1];raw=bytearray(base64.b64decode(w['base64']));struct.pack_into('<H',raw,0xc4,200)
        w.update(base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):m.verify(self.fixture)

    def test_privacy_subset(self):
        text=json.dumps(self.fixture)
        for value in ('"device"','"bindingChecks"','"boot"','/home/','/sys/','192.168.'):
            self.assertNotIn(value,text)
        for label in ('set200','restore40'):
            self.assertEqual(self.fixture[label]['windows'][0],{'name':'callbacks','bytes':64,'rawOmitted':True})

if __name__=='__main__':unittest.main()
