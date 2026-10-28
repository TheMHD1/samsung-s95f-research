#!/usr/bin/env python3
"""Project a fixed private HF cutoff into nonidentifying scientific metadata.

No transport imports, commands or device operations. Original raw logs, identities,
PIDs, clock values, root envelopes and OEM bytes are never emitted.
"""
import argparse,base64,hashlib,json,re,struct
from pathlib import Path
CUTOFF_SHA='01dc8243ec18b13ac71f1f2aec4ad7df9fc288d57f398d3fbbf37072d675c6b0'
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
def build(source):
 p=source/'panel-idle-20261026/overnight/menu-recovery-branch-trial-20261028hf'
 cutoff=p/'publication-cutoff-01.json';need(sha(cutoff.read_bytes())==CUTOFF_SHA,'fixed private cutoff')
 seal=json.loads(cutoff.read_bytes());allowed={x['path']:x for x in seal['privateSourceFiles']}
 for name,row in allowed.items():
  q=Path(name);need(not q.is_absolute()and'..'not in q.parts,'bounded source reference');b=(p/q).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'frozen input')
 def load(name):need(name in allowed,'source outside cutoff');return json.loads((p/name).read_bytes())
 def eb(folder):
  j=load(folder+'/native.receipt.json');result=load(folder+'/result.json')
  for k in ['accepted','opened','claimed','released','closed','packingQualified','laneGateContextQualified']:need(j[k]is True,'native '+k)
  need(j['protocolPhase']=='ReadyForHeader'and j['headersSent']==16 and j['bulkTransfers']==32 and j['writes']==j['uiOperations']==0,'EB lifecycle')
  need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT','EB wrapper')
  windows={}
  for w in j['windows']:
   b=base64.b64decode(w['base64'],validate=True);need(len(b)==w['bytes']and sha(b)==w['sha256'],'complete raw window binding');need(w['name']not in windows,'unique window');windows[w['name']]=b
  need(len(windows)==16,'all sixteen window inputs');r=windows['start-R'];e=windows['end-R'];need(r==e and len(r)==256,'stable full R')
  u16=lambda off:struct.unpack_from('<H',r,off)[0]
  return {'accepted':True,'phase':j['protocolPhase'],'headers':16,'bulks':32,'writes':0,'uiOperations':0,'released':True,'closed':True,'cleanup':result['cleanup'],'fullRStartEndEqual':True,'state':[u16(n)for n in [0,10,14]],'limit':u16(0xc4),'logger':u16(6),'globalSelector':u16(16),'c7':windows['C'][7],'c8':windows['C'][8],'scan':windows['M'][56],'bothNZero':not any(windows['start-N']+windows['end-N']),'atomicSnapshot':False,'allRawWindowsVerified':16}
 pre=eb('pre-eb-capture');post=eb('post-eb-capture')
 stock=load('stock-mode2/result.json');native=load('stock-mode2/mode2/result.json')
 need(stock['accepted']is True and stock['mode2_invocations']==1 and stock['threshold_writes']==stock['automatic_retries']==0,'one stock operation')
 need(native['accepted']is True and native['helper_exit']==0 and native['cleanup_confirmed']is True and native['request_count']==1 and native['classification']=='kernel_return_zero_only','strict stock result')
 analyses={k:load(k+'/archive/analysis.json')for k in ['kernel-baseline-v2','kernel-post-mode2','kernel-usb-loss']}
 for k,a in analyses.items():
  x=load(k+'/result.json');need(x['accepted']is True and x['archiveVerified']is True and a['captureAccepted']is True and a['archiveVerified']is True and a['rawSavedBeforeFiltering']is True,'accepted raw-before-filter archive')
  need(a['captureReceipt']['metadata']['dmesgExit']==0 and a['captureReceipt']['metadata']['stderrBytes']==0,'snapshot terminal')
 markers=analyses['kernel-post-mode2']['classification']['markerCounts'];observations=analyses['kernel-post-mode2']['classification']['observations']
 pid=seal['facts']['nativePidSourceBound'];need(all(x['printedPid']==pid for x in observations if x['marker'].startswith('qdf-')),'source-associated helper PID')
 before=load('pre-identity/identity.json');after=load('post-identity/identity.json');need(set(before)==set(after)and len(before)==16,'sixteen identity fields')
 changed=sorted(k for k in before if before[k]!=after[k]);need(changed==sorted(['sysfsStat','devnum','deviceNode','nodeStat']),'same-instance lifecycle differences');need(before['boot']==after['boot']and before['descriptorsSha256']==after['descriptorsSha256'],'same boot/descriptors')
 transition=load('usb-transition.json');need(transition['accepted']is True and transition['positiveDisconnectAndEnumeration']is True and transition['sameBootAndDescriptors']is True and transition['controllerFullResetProven']is False,'positive bounded lifecycle')
 old=load('baseline-refusal-analysis.json');forensic=load('baseline-forensic-fetch/result.json');ha=load('post-ha-capture/parent-refusal-analysis.json')
 raw=(p/'kernel-usb-loss/archive/kernel.raw').read_bytes()
 # A request marker, not proof of an external CEC peer or the actual owner.
 need(b'hdmicec-service'in raw and re.search(rb'(?:reason[^\n]{0,40}(?:0x2e|46)|(?:0x2e|46)[^\n]{0,40}hdmicec)',raw,re.I)is not None,'separate standby request marker')
 f={'schema':'public-stock-mode2-observation-v1','source':{'workstream':'menu-recovery-branch-trial-20261028hf','privateCutoffSha256':CUTOFF_SHA,'privateInputsVerified':len(allowed),'originalTransportProvenanceReplayed':False,'rawLogsIdentitiesPidsAndClocksPublished':False},'pre':pre,'stock':{'accepted':native['accepted'],'operation':41,'mode':2,'ioctl':'0xc010749f','requestCount':native['request_count'],'helperExit':native['helper_exit'],'nativeDeadlineSeconds':native['native_deadline_seconds'],'cleanupConfirmed':native['cleanup_confirmed'],'classification':native['classification'],'thresholdWrites':stock['threshold_writes'],'automaticRetries':stock['automatic_retries'],'physicalState':'unobserved'},'logs':{'allThreeSnapshotsAccepted':True,'rawSavedBeforeFiltering':True,'sourceAssociatedMarkerCounts':markers,'qdfMarkerPidMatchesNativeReceipt':True,'oclReturnLinesHavePid':False,'normalTailPositive':seal['facts']['actualPrintedNormalTailAndReplay'],'errSkipExplainsThisAttempt':False,'completeKernelRingProven':False,'clockDomainsCalibrated':False,'currentCallbackBindingProven':False},'postHistorical':post,'lifecycle':{'positiveDisconnectThenEnumeration':True,'sameLinuxBoot':True,'sameDescriptors':True,'identityFieldsVerified':len(before),'changedIdentityFieldNames':changed,'allDomainsResetProven':False},'originalCaptureRefusal':{'accepted':old['originalCaptureAccepted'],'terminalFrameProduced':old['terminalCaptureFrameProduced'],'dmesgExitKnown':old['dmesgExitKnown'],'dmesgExit':forensic['dmesgExit'],'forensicArchiveVerified':forensic['forensicArchiveVerified'],'forensicDmesgRuns':forensic['dmesgRuns'],'promotedToAccepted':False,'cause':'GNU stat reports regular empty file; v1 expected regular file'},'laterWitnessRefusal':{'accepted':ha['captureAccepted'],'nativeInvocations':ha['nativeInvocations'],'vendorTransfers':ha['vendorTransfers'],'stagingCreationRequests':ha['stagingCreationRequests'],'automaticRetry':ha['automaticRetry'],'newResetSent':ha['newResetSent']},'separateLaterStandby':{'requester':'hdmicec-service','reason':46,'source':'later retained kernel snapshot','attributionToPeerOrOwnerProven':False,'rtpRelapseProven':False},'limits':{'physicalRecoveryProven':False,'permanentPreventionProven':False,'instructionReloadProven':False,'universalRamClearingProven':False,'uniqueFaultClearingPathProven':False,'laterWakeIncluded':False}}
 from verify_stock_mode2_fixture import verify
 verify(f);return f
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--source',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args();x.output.write_text(json.dumps(build(x.source),indent=2,sort_keys=True)+'\n')
