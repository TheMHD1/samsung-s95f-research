#!/usr/bin/env python3
"""Verify a typed HF software/log observation; no original transport replay."""
import argparse,json
from pathlib import Path
CUTOFF_SHA='01dc8243ec18b13ac71f1f2aec4ad7df9fc288d57f398d3fbbf37072d675c6b0'
def verify(f):
 checks=0
 def need(ok,why):
  nonlocal checks
  if not ok:raise ValueError(why)
  checks+=1
 def exact(o,expected,label):
  need(type(o)is dict and set(o)==set(expected),label+' fields')
  for k,v in expected.items():need(type(o[k])is type(v)and o[k]==v,label+' '+k)
 need(type(f)is dict and set(f)=={'schema','source','pre','stock','logs','postHistorical','lifecycle','originalCaptureRefusal','laterWitnessRefusal','separateLaterStandby','limits'},'top fields')
 need(f['schema']=='public-stock-mode2-observation-v1','schema')
 exact(f['source'],{'workstream':'menu-recovery-branch-trial-20261028hf','privateCutoffSha256':CUTOFF_SHA,'privateInputsVerified':26,'originalTransportProvenanceReplayed':False,'rawLogsIdentitiesPidsAndClocksPublished':False},'source')
 for key,state,c7,scan in [('pre',[1,4097,0],1,0),('postHistorical',[0,0,1],0,1)]:
  exact(f[key],{'accepted':True,'phase':'ReadyForHeader','headers':16,'bulks':32,'writes':0,'uiOperations':0,'released':True,'closed':True,'cleanup':'STAGE_ABSENT','fullRStartEndEqual':True,'state':state,'limit':40,'logger':0,'globalSelector':4,'c7':c7,'c8':3,'scan':scan,'bothNZero':True,'atomicSnapshot':False,'allRawWindowsVerified':16},key)
  need(all(type(v)is int for v in f[key]['state']),key+' integer tuple')
 exact(f['stock'],{'accepted':True,'operation':41,'mode':2,'ioctl':'0xc010749f','requestCount':1,'helperExit':0,'nativeDeadlineSeconds':12,'cleanupConfirmed':True,'classification':'kernel_return_zero_only','thresholdWrites':0,'automaticRetries':0,'physicalState':'unobserved'},'stock')
 markers={'ocl-reset-return':2,'qdf-access-success':1,'qdf-display-status-result':1,'qdf-frame-mode-read':1,'qdf-frame-mode-same':1,'qdf-init-status-result':1,'qdf-init-status-start':1,'qdf-mode2-request':1,'qdf-monitor-status':1,'qdf-normal-tail-entered':1,'qdf-ocl-reset-call':2,'qdf-power-off':1,'qdf-power-on':1,'qdf-register-replay-end':1,'qdf-register-replay-start':1}
 logs=f['logs'];need(set(logs)=={'allThreeSnapshotsAccepted','rawSavedBeforeFiltering','sourceAssociatedMarkerCounts','qdfMarkerPidMatchesNativeReceipt','oclReturnLinesHavePid','normalTailPositive','errSkipExplainsThisAttempt','completeKernelRingProven','clockDomainsCalibrated','currentCallbackBindingProven'},'logs fields')
 exact(logs['sourceAssociatedMarkerCounts'],markers,'typed marker counts')
 for k,v in {'allThreeSnapshotsAccepted':True,'rawSavedBeforeFiltering':True,'qdfMarkerPidMatchesNativeReceipt':True,'oclReturnLinesHavePid':False,'normalTailPositive':True,'errSkipExplainsThisAttempt':False,'completeKernelRingProven':False,'clockDomainsCalibrated':False,'currentCallbackBindingProven':False}.items():need(logs[k]is v,'log premise/limit '+k)
 exact(f['lifecycle'],{'positiveDisconnectThenEnumeration':True,'sameLinuxBoot':True,'sameDescriptors':True,'identityFieldsVerified':16,'changedIdentityFieldNames':sorted(['sysfsStat','devnum','deviceNode','nodeStat']),'allDomainsResetProven':False},'lifecycle')
 exact(f['originalCaptureRefusal'],{'accepted':False,'terminalFrameProduced':False,'dmesgExitKnown':False,'dmesgExit':None,'forensicArchiveVerified':True,'forensicDmesgRuns':0,'promotedToAccepted':False,'cause':'GNU stat reports regular empty file; v1 expected regular file'},'original refusal')
 exact(f['laterWitnessRefusal'],{'accepted':False,'nativeInvocations':0,'vendorTransfers':0,'stagingCreationRequests':0,'automaticRetry':False,'newResetSent':False},'later refusal')
 exact(f['separateLaterStandby'],{'requester':'hdmicec-service','reason':46,'source':'later retained kernel snapshot','attributionToPeerOrOwnerProven':False,'rtpRelapseProven':False},'standby')
 exact(f['limits'],{'physicalRecoveryProven':False,'permanentPreventionProven':False,'instructionReloadProven':False,'universalRamClearingProven':False,'uniqueFaultClearingPathProven':False,'laterWakeIncluded':False},'limits')
 return {'schema':'s95f-public-stock-mode2-verification-v1','checks':checks,'preState':f['pre']['state'],'postHistoricalState':f['postHistorical']['state'],'normalTailPositive':True,'separateStandbyRequestReason':46,'originalTransportProvenanceReplayed':False,'physicalRecoveryProven':False,'targetOperations':0}
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--fixture',type=Path,default=Path(__file__).resolve().parents[1]/'fixtures/stock-mode2-observation.json');x=a.parse_args();print(json.dumps(verify(json.loads(x.fixture.read_bytes())),sort_keys=True,indent=2))
