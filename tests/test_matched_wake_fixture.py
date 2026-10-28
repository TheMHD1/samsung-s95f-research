"""Focused negative tests for the bounded GJ projection; original receipts are private."""
import base64,copy,hashlib,json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from verify_matched_wake_contrast import verify
class MatchedWakeFixture(unittest.TestCase):
 def setUp(self):self.fixture=json.loads((ROOT/'fixtures/matched-wake-contrast.json').read_bytes())
 def reject(self,mutate):
  f=copy.deepcopy(self.fixture);mutate(f)
  with self.assertRaises((ValueError,KeyError,TypeError)):verify(f)
 def test_positive_and_bounded_claims(self):
  r=verify(self.fixture);self.assertEqual((r['raised200']['clean'],r['raised200']['maxH'],r['control40']['faulted'],r['control40']['maxH']),(55,36,1,48));self.assertEqual((r['retainedFullRWindows'],r['retainedR16']),(28,4));self.assertEqual(r['finalOrdinal5'],52);self.assertFalse(r['thresholdPreventionEstablished'])
 def test_no_scientific_promotion(self):
  for key in ['physicalPictureObserved','actualFpProven','executingPcProven','matchedAllHistoryProven','thresholdPreventionEstablished','rootCauseFixEstablished','originalTransportProvenanceReplayed']:
   with self.subTest(key=key):self.reject(lambda f:f.__setitem__(key,True))
  for case in ['raised200','control40']:
   for key in ['chronologicalDeltaProven','lapCountProven','sharedEpochProven','twoLinesMeanTwoInvocations']:
    self.reject(lambda f:f[case]['ring'].__setitem__(key,True))
 def test_rehashed_retained_projection_bytes(self):
  for case in ['raised200','control40']:
   for i in range(50):
    def mutate(f):
     w=f[case]['native']['projection'];b=bytearray(base64.b64decode(w['base64']));b[i]^=1;w.update(base64=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
    with self.subTest(case=case,byte=i):self.reject(mutate)
 def test_lifecycle_counts_events_and_exposure(self):
  for case in ['raised200','control40']:
   for key in ['headers','bulks','inputs','writes','retries','threshold','cleanCycles','quiescentCycles']:
    self.reject(lambda f:f[case]['native'].__setitem__(key,True))
   self.reject(lambda f:f[case]['workflow'].__setitem__('cleanup','NOT_REMOVED'))
   self.reject(lambda f:f[case]['native']['intervention']['calls'][0].__setitem__('beforeUs',f[case]['native']['endUs']))
   self.reject(lambda f:f[case]['ring'].__setitem__('candidateEvent736Lines',99))
   self.reject(lambda f:f[case]['ring']['details'][0].__setitem__('conditional12bitACandidates',[]))
  for case in ['raised200','control40']:
   def alter_r16(f):
    w=f[case]['native']['retained'][0]['windows'][0];b=bytearray(base64.b64decode(w['base64']));struct.pack_into('<H',b,16,1);w.update(base64=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
   self.reject(alter_r16)
  for case in ['set200','restore40']:
   self.reject(lambda f:f[case].__setitem__('headers',True));self.reject(lambda f:f[case].__setitem__('phase','Unknown'))
 def test_final_counts_are_not_universal_clear(self):
  def alter(f,key,offset,value):
   w=f['finalValidation']['windows'][key];b=bytearray(base64.b64decode(w['base64']));struct.pack_into('<H',b,offset,value);w.update(base64=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
  for key,offset,value in [('end-N',20,0),('start-N',20,0),('B',0,0),('M',12,2),('end-R',0xc4,200)]:self.reject(lambda f:alter(f,key,offset,value))
  self.reject(lambda f:f['sequence'].__setitem__('stockMode2At200',1))
if __name__=='__main__':unittest.main()
