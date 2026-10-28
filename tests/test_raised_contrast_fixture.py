"""Pure public EX scientific contrast; no acquisition or target imports."""
import base64,copy,hashlib,importlib.util,json,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('contrast',ROOT/'tools/verify_raised_contrast.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class RaisedContrast(unittest.TestCase):
    def setUp(self):self.fixture=json.loads((ROOT/'fixtures/raised-restored-contrast.json').read_text())
    def mutate_blob(self,f,key,offset,value):
        w=f[key]['projection'];b=bytearray(base64.b64decode(w['base64']));b[offset]=value
        w['base64']=base64.b64encode(b).decode();w['sha256']=hashlib.sha256(b).hexdigest()
    def test_scientific_derivation(self):
        r=module.verify(self.fixture)
        self.assertEqual((r['raisedRows'],r['cleanRows'],r['quiescentRows']),(56,55,1))
        self.assertEqual(len(r['cleanC7OneScoreAbove40Cycles']),23)
        self.assertEqual((r['maximumSampledH0Low16'],r['lastRetainedScore']),(76,52))
        self.assertEqual(r['first40Control']['maximumSampledH0Low16'],0)
        self.assertEqual(r['explicit40Snapshot'],'Faulted')
        self.assertTrue(r['restorationReadbackObserved']);self.assertFalse(r['recoveryOrderingVerifiedByThisFixture'])
        for key in ('pureThresholdCausalityEstablished','actualFPSelectionObserved','physicalPictureObserved','permanentFixEstablished'):self.assertFalse(r[key])
        self.assertEqual(r['targetOperations'],0)
    def test_compact_quiescent_is_not_clean(self):
        self.mutate_blob(self.fixture,'raised200',18*50,0)
        with self.assertRaisesRegex(ValueError,'row counters'):module.verify(self.fixture)
    def test_intermediate_limit_drift_cannot_hide_behind_last_context(self):
        self.mutate_blob(self.fixture,'raised200',20*50+2,40)
        with self.assertRaisesRegex(ValueError,'sampled limits'):module.verify(self.fixture)
    def test_intermediate_witness_c7_change_is_detected(self):
        rows=module.verify(self.fixture)['cleanC7OneScoreAbove40Cycles']
        self.mutate_blob(self.fixture,'raised200',(rows[0]-1)*50+1,0)
        with self.assertRaisesRegex(ValueError,'witnesses'):module.verify(self.fixture)
    def test_last_context_is_not_only_a_compact_claim(self):
        w=self.fixture['raised200']['retained'][-1]['windows'][1]
        b=bytearray(base64.b64decode(w['base64']));struct.pack_into('<H',b,12,1)
        w['base64']=base64.b64encode(b).decode();w['sha256']=hashlib.sha256(b).hexdigest()
        with self.assertRaisesRegex(ValueError,'alternate context'):module.verify(self.fixture)
    def test_writer_has_no_other_observed_R_byte_change(self):
        w=self.fixture['restore40']['windows']['readback-R'];b=bytearray(base64.b64decode(w['base64']));b[0x80]^=1
        w['base64']=base64.b64encode(b).decode();w['sha256']=hashlib.sha256(b).hexdigest()
        with self.assertRaisesRegex(ValueError,'only observed'):module.verify(self.fixture)
    def test_bool_is_not_counter(self):
        self.fixture['raised200']['cyclesStarted']=True
        with self.assertRaisesRegex(ValueError,'distinct cycles'):module.verify(self.fixture)
    def test_snapshot_full_R_fault_is_derived(self):
        for name in ('start-R','end-R'):
            w=self.fixture['explicitControl40']['windows'][name];b=bytearray(base64.b64decode(w['base64']));struct.pack_into('<H',b,10,0)
            w['base64']=base64.b64encode(b).decode();w['sha256']=hashlib.sha256(b).hexdigest()
        with self.assertRaisesRegex(ValueError,'full R classification'):module.verify(self.fixture)
    def test_projection_has_no_private_operational_fields(self):
        def walk(x):
            if isinstance(x,dict):
                for k,v in x.items():
                    self.assertNotIn(k,{'device','bindingChecks','bindingQualified','boot','bootId','token','nonce','rootCommands','rootResponses','capturedDynamicAPointer','capturedDynamicBPointer'});walk(v)
            elif isinstance(x,list):
                for v in x:walk(v)
        walk(self.fixture)
        self.assertEqual(self.fixture['raised200']['projection']['bytes'],56*50)

if __name__=='__main__':unittest.main()
