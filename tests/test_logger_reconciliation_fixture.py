"""Typed sixth-fixture replay and malformed scientific claims, fully offline."""
import base64,copy,hashlib,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('logger_science',ROOT/'tools/verify_logger_reconciliation.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class LoggerReconciliation(unittest.TestCase):
    def setUp(self):self.f=json.loads((ROOT/'fixtures/logger-refusal-restoration.json').read_bytes())
    def edit(self,w,offset,value):
        b=bytearray(base64.b64decode(w['base64']));b[offset]=value;w['base64']=base64.b64encode(b).decode();w['sha256']=hashlib.sha256(b).hexdigest()
    def test_exact_science(self):
        v=m.verify(self.f);self.assertFalse(v['originalWorkflowAccepted']);self.assertTrue(v['originalTerminalKnownReady']);self.assertEqual(v['completeUnpublishedQuiescentCycle'],19);self.assertEqual(v['cChangedOffsets'],[7,8]);self.assertTrue(v['loggerRestored']);self.assertEqual(v['restorationPreWriteState'],'Clean');self.assertEqual(v['finalSoftwareState'],'Clean40/logger0/N0')
        for k in ['cleanStateCausedByLoggerRestore','physicalPictureObserved','rootCauseFixEstablished','originalTransportProvenanceReplayedByPublicFixture']:self.assertFalse(v[k])
    def test_original_refusal_not_accepted(self):
        self.f['originalRefusal']['accepted']=True
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_known_phase_not_ambiguous(self):
        self.f['originalRefusal']['phase']='Unknown'
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_bool_not_pair_count(self):
        self.f['originalRefusal']['writes']=True
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_unpublished_q_cannot_be_clean(self):
        for i in [0,4]:self.edit(self.f['originalRefusal']['retained'][-1]['windows'][i],14,1)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_current_c8_must_differ(self):
        self.edit(self.f['originalRefusal']['retained'][-1]['windows'][2],8,3)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_current_c7_not_old_c7(self):
        self.edit(self.f['originalRefusal']['retained'][-1]['windows'][2],7,0)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_compact_h_not_forged(self):
        self.edit(self.f['originalRefusal']['projection'],6,1)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_compact_clock_not_independent_of_full_capture(self):
        w=self.f['originalRefusal']['retained'][0]['windows'][3];w['afterUs']+=1
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_no_clean_causality(self):
        self.f['cleanStateCausedByLoggerRestore']=True
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_restore_requires_zero_readback(self):
        self.edit(self.f['restoration']['windows'][-1],6,1)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_restore_has_only_one_observed_byte_change(self):
        self.edit(self.f['restoration']['windows'][-1],0x80,1)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_restore_source_context_not_wildcard(self):
        self.edit(self.f['restoration']['windows'][1],8,4)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_restoration_clock_orders_all_pairs(self):
        self.f['restoration']['pairBracketsUs'][-1][0]=0
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_final_n_nonzero_not_universal_clear(self):
        self.edit(self.f['finalValidation']['windows']['end-N'],0,1)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_final_full_r_not_only_stale_summary(self):
        self.edit(self.f['finalValidation']['windows']['end-R'],6,1)
        with self.assertRaises(ValueError):m.verify(self.f)
    def test_no_reset_or_physical_claim(self):
        for field,value in [('resetsInSequence',1),('physicalPictureObserved',True),('rootCauseFixEstablished',True)]:
            f=copy.deepcopy(self.f);f[field]=value
            with self.assertRaises(ValueError):m.verify(f)
    def test_private_operational_field_not_in_fixture(self):
        def visit(x):
            if isinstance(x,dict):
                for k,v in x.items():self.assertNotIn(k,{'device','boot','bindingChecks','bindingQualified','token','nonce','rootCommands','rootResponses','rawRing','dynamicAPointer','dynamicBPointer'});visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        visit(self.f);self.assertEqual(self.f['originalRefusal']['projection']['bytes'],900)
        f=copy.deepcopy(self.f);f['device']=65
        with self.assertRaises(ValueError):m.verify(f)
if __name__=='__main__':unittest.main()
