import base64,copy,hashlib,json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from verify_wake_onset import verify
class WakeOnset(unittest.TestCase):
 def setUp(self):self.cases={k:json.loads((R/'fixtures'/('wake-'+k.lower()+'.json')).read_bytes())for k in ['GC','GF']}
 def bad(self,case,change):
  f=copy.deepcopy(self.cases[case]);change(f)
  with self.assertRaises((ValueError,KeyError,TypeError)):verify(f)
 def test_positive(self):
  a,b=[verify(self.cases[k])for k in ['GC','GF']]
  self.assertEqual((a['rows'],a['clean'],a['quiescent'],a['maximumSampledH']),(77,76,1,36))
  self.assertEqual((b['rows'],b['clean'],b['quiescent'],b['faulted'],b['maximumSampledH'],b['conservativeStatusEnclosureUs']),(26,24,1,1,48,25476))
 def test_claims(self):
  for case in self.cases:
   for key in ['physicalPictureObserved','actualFpProven','executingPcProven','selectedAProven','keyConsumptionProven','forYouTransitionProven','rootCauseFixEstablished','thresholdPreventionEstablished','originalTransportProvenanceReplayed']:
    with self.subTest(case=case,key=key):self.bad(case,lambda f,k=key:f.__setitem__(k,True))
 def test_accounting(self):
  for case in self.cases:
   for key in ['headers','bulks','inputs','writes','retries','threshold','cyclesStarted','cleanCycles','quiescentCycles']:
    with self.subTest(case=case,key=key):self.bad(case,lambda f,k=key:f['native'].__setitem__(k,f['native'][k]+1))
   self.bad(case,lambda f:f['native'].__setitem__('writes',True))
   self.bad(case,lambda f:f['native'].__setitem__('accepted',False))
   self.bad(case,lambda f:f['native'].__setitem__('terminal','TimeLimit'if case=='GF'else'TransitionCaptured'))
   self.bad(case,lambda f:f['workflow'].__setitem__('wrapperUiOperations',1 if case=='GF'else 0))
   self.bad(case,lambda f:f['workflow'].__setitem__('cleanup','NOT_REMOVED'))
 def test_packed_rehash_tamper(self):
  for case in self.cases:
   # Mutate every projected byte of the independently retained first full row.
   for pos in range(50):
    def change(f,pos=pos):
     w=f['native']['projection'];b=bytearray(base64.b64decode(w['base64']));b[pos]^=1;w.update(base64=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
    with self.subTest(case=case,pos=pos):self.bad(case,change)
 def test_clock_key_and_ring(self):
  for case in self.cases:
   self.bad(case,lambda f:f['native']['intervention']['calls'][0].__setitem__('beforeUs',f['native']['endUs']))
   self.bad(case,lambda f:f['native']['intervention']['calls'][0].__setitem__('exitCode',1))
   self.bad(case,lambda f:f['native']['intervention']['calls'][1].__setitem__('reaped',False))
   for key in ['candidateBytes','normalInvocationCounter','baselineEvent736Lines','postEvent736Lines','candidateEvent736Lines']:
    with self.subTest(case=case,key=key):self.bad(case,lambda f,k=key:f['ring'].__setitem__(k,f['ring'][k]+1))
   for key in ['chronologicalDeltaProven','lapCountProven','sharedEpochProven','twoLinesMeanTwoInvocations']:
    self.bad(case,lambda f,k=key:f['ring'].__setitem__(k,True))
   self.bad(case,lambda f:f['ring']['postCursors'].__setitem__(0,15361))
   self.bad(case,lambda f:f['ring']['details'][0].__setitem__('conditional12bitACandidates',[4096]))
   self.bad(case,lambda f:f['ring']['details'].pop())
   self.bad(case,lambda f:f['native']['retained'].pop())
if __name__=='__main__':unittest.main()
