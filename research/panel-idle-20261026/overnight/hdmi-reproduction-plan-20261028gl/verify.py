#!/usr/bin/env python3
"""Read-only host check of this fixed design and retained source pins; no device entrypoints."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
checks=0
def need(x,why):
 global checks
 if not x:raise ValueError(why)
 checks+=1
pins=json.loads((D/'input-pins.json').read_bytes())
for r in pins['files']:
 p=Path(r['path']);need(p.is_file()and not p.is_symlink(),'ordinary source');b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'source pin')
p=json.loads((D/'plan.json').read_bytes());need(all(type(v)is int and v==0 for v in p['operationsPerformed'].values()),'host-only')
need(p['preferredPair']['failingCase']['series']=='PROGRAM_04'and p['preferredPair']['workingControl']['season']==5,'exact pair')
need(p['locatorPolicy']['exactFilePathsRetainedInS95fReports']is False and p['locatorPolicy']['freshExactTitleAndProfileMatchRequired']is True and p['locatorPolicy']['rejectHttpStrmDuplicate']is True,'locator boundary')
need(p['control']['connectionCurrentlyVerified']is False and p['control']['credentialMaterialInPlan']is False and p['control']['fullExistingAutoplayScriptAllowed']is False,'route boundary')
need(p['firstPrerequisite']['currentHdmiExternalRtp0x1001Proven']is False and p['firstPrerequisite']['kernelQdf0x10ImpliesExternalRtpTuple']is False and p['firstPrerequisite']['fnMode1Aa0Ac2AssumedForHdmi']is False and p['firstPrerequisite']['genericProfileBypassAllowed']is False,'fault domain/profile')
n=p['prospectiveNoKeyRecorder'];need(n['status']=='DESIGN_ONLY_NO_QUALIFIED_HOST_ARM_SIGNAL'and n['secondConcurrentTvRootOrControllerRequestAllowed']is False and n['wholeMinuteExternalObservationFits']is False,'new route not qualified')
need(n['originalOptionalPairAdmissionCostUs']==4_000_000+26_000_000+7_000_000 and n['noWorkerOptionalPairAdmissionCostUs']==4_000_000+26_000_000,'source budget arithmetic')
engine=next(Path(r['path']).read_text()for r in pins['files']if r['path'].endswith('combined-event-successor-20261028fn/Engine.cs'))
need('CleanupReserveUs=6*PairBudgetUs+MarginUs, KeyJoinReserveUs=7_000_000, WholeBudgetUs=40_000_000'in engine,'exact declared budgets')
need('PairBudgetUs+CleanupReserveUs+KeyJoinReserveUs'in engine and 'key?.State.Completed==true'in engine,'actual source dependencies')
need(p['proposedBounds']['playbackObservationSecondsPerCase']==60 and p['proposedBounds']['automaticStartAttemptsPerCase']==1 and p['proposedBounds']['automaticPlaybackRetries']==0 and p['proposedBounds']['thresholdOrMaskWrites']==0,'finite sequence')
need(all(x is False for x in p['claims'].values()),'scientific limits')
print(json.dumps({'schema':'gl-host-design-verification-v1','checks':checks,'sourceInputs':len(pins['files']),'targetOperations':0,'networkOperations':0,'designOnly':True,'controlReachabilityProven':False,'currentHdmiExternalRtpProven':False,'noKeyRecorderImplemented':False},sort_keys=True))
