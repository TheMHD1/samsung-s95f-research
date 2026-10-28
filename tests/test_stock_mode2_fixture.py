"""Typed HF projection: source claims, rejected channels and historical scope."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from verify_stock_mode2_fixture import verify
class StockMode2Fixture(unittest.TestCase):
 def setUp(self):self.f=json.loads((ROOT/'fixtures/stock-mode2-observation.json').read_bytes())
 def reject(self,section,key,value):
  f=copy.deepcopy(self.f);f[section][key]=value
  with self.assertRaises((ValueError,KeyError,TypeError)):verify(f)
 def test_positive_historical_observation(self):
  r=verify(self.f);self.assertEqual(r['preState'],[1,4097,0]);self.assertEqual(r['postHistoricalState'],[0,0,1]);self.assertTrue(r['normalTailPositive']);self.assertFalse(r['physicalRecoveryProven'])
 def test_rejected_capture_never_promoted(self):
  for key in ['accepted','terminalFrameProduced','dmesgExitKnown','promotedToAccepted']:self.reject('originalCaptureRefusal',key,True)
  for value in [0,255,False]:self.reject('originalCaptureRefusal','dmesgExit',value)
  self.reject('originalCaptureRefusal','forensicDmesgRuns',1)
  for key in ['nativeInvocations','vendorTransfers','stagingCreationRequests']:self.reject('laterWitnessRefusal',key,1)
  for key in ['accepted','automaticRetry','newResetSent']:self.reject('laterWitnessRefusal',key,True)
 def test_no_reset_physical_or_cec_inflation(self):
  for k in self.f['limits']:self.reject('limits',k,True)
  for k in ['allDomainsResetProven']:self.reject('lifecycle',k,True)
  for k in ['rtpRelapseProven','attributionToPeerOrOwnerProven']:self.reject('separateLaterStandby',k,True)
  for k in ['originalTransportProvenanceReplayed','rawLogsIdentitiesPidsAndClocksPublished']:self.reject('source',k,True)
  for k in ['clockDomainsCalibrated','completeKernelRingProven','currentCallbackBindingProven','errSkipExplainsThisAttempt','oclReturnLinesHavePid']:self.reject('logs',k,True)
 def test_exact_types_and_state_lifecycle(self):
  for section in ['pre','postHistorical']:
   for k in ['headers','bulks','writes','uiOperations','limit','logger','globalSelector','allRawWindowsVerified']:self.reject(section,k,True)
   for k in ['accepted','released','closed','fullRStartEndEqual']:self.reject(section,k,False)
   self.reject(section,'phase','Unknown');self.reject(section,'cleanup','RETAINED');self.reject(section,'atomicSnapshot',True)
  self.reject('pre','state',[0,0,1]);self.reject('postHistorical','state',[1,4097,0]);self.reject('postHistorical','limit',200)
  self.reject('stock','classification','physical_recovery');self.reject('stock','requestCount',2);self.reject('stock','thresholdWrites',1)
 def test_marker_and_identity_scope(self):
  for key in self.f['logs']['sourceAssociatedMarkerCounts']:
   f=copy.deepcopy(self.f);f['logs']['sourceAssociatedMarkerCounts'][key]=True
   with self.assertRaises(ValueError):verify(f)
  self.reject('lifecycle','identityFieldsVerified',17);self.reject('lifecycle','changedIdentityFieldNames',[])
  self.reject('source','privateInputsVerified',25);self.reject('source','privateCutoffSha256','0'*64)
if __name__=='__main__':unittest.main()
