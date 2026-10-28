#!/usr/bin/env python3
"""Fixed actual DT baseline replay; reads local files only, never invokes runner."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
DT=HERE.parent
BASE=DT.parent
CAPTURE=BASE/'volatile-limit-trial-20261028dk/reference-baseline-01'
checks=0

def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)

def sha(b):return hashlib.sha256(b).hexdigest()
def readjson(p):return json.loads(p.read_text())

def analyze():
 for entry in readjson(HERE/'input-pins.json')['files']:
  b=Path(entry['path']).read_bytes();need(len(b)==entry['bytes'] and sha(b)==entry['sha256'],'input pin '+entry['path'])
 manifestBytes=(DT/'deployment-manifest.json').read_bytes();manifest=readjson(DT/'deployment-manifest.json');mh=sha(manifestBytes)
 need(mh=='ed1e1594f3dc23528c69894c21a19c214593a0ae12c0dd20ec5ceebc9fda4d80','frozen manifest anchor')
 need((CAPTURE/'reviewed-manifest.json').read_bytes()==manifestBytes,'exact captured deployment manifest')
 for section in ('nativeFiles','wrapperFiles'):
  for name,pin in manifest[section].items():
   b=(DT/name).read_bytes();need(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'manifest source/payload '+name)
 need(sha((DT/'host-build-checkpoint.json').read_bytes())==manifest['nativeCheckpointSha256'],'build checkpoint')
 need(manifest['parserSha256']=='85e6d0783dc0455d4002e6e0332e23eed15d7d8b21c5ece3b3443c5529428b47','frozen parser anchor')
 spec=importlib.util.spec_from_file_location('dt_pinned_offline_parser',DT/'parse-result.py');parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
 n,raws,interpretation=parser.parse_native((CAPTURE/'native.receipt.json').read_text())
 need(interpretation==readjson(CAPTURE/'interpretation.json'),'exact interpretation replay')
 result=readjson(CAPTURE/'result.json');record=readjson(CAPTURE/'record.json')
 need(result['accepted'] is True and result['nativeInvocations']==1 and result['cleanup']=='STAGE_ABSENT','saved wrapper acceptance/cleanup')
 need(result['manifestSha256']==record['manifestSha256']==mh,'manifest chain')
 need(result['headersSent']==n['headersSent']==14 and result['bulkTransfers']==n['bulkTransfers']==28,'14 pairs/28 bulks')
 need(result['retries']==n['writes']==n['uiOperations']==0,'no retries/writes/UI')
 actual={};summaries=[]
 need(len(raws)==len(result['rawFiles'])==14,'fourteen raw files')
 for (name,b,digest),declared in zip(raws,result['rawFiles']):
  need(sha(b)==digest and (CAPTURE/name).read_bytes()==b,'strict raw file '+name)
  need(declared=={'name':name,'bytes':len(b),'sha256':digest},'wrapper declared raw '+name)
  actual[name]=b;summaries.append({'name':name,'bytes':len(b),'sha256':digest,'allZero':not any(b)})
 decodedReferences={}
 for position in ('top','bottom'):
  name='fixed-'+position+'-candidate.bin';b=actual[name]
  need(len(b)==104 and not any(b),'actual zero104 '+position)
  # Independent bitstream decoding, distinct from frozen parser's four-values-per6B loop.
  bits=int.from_bytes(b[:102],'little')
  lanes={str(568+i):(bits>>(12*i))&4095 for i in range(68)}
  need(all(v==0 for v in lanes.values()),'all68 complete decoded lanes zero '+position)
  requested={x:lanes[x]for x in interpretation['fixedReferenceCandidates'][position]}
  need(requested==interpretation['fixedReferenceCandidates'][position],'independent requested-lane replay '+position)
  index=[x[0] for x in parser.SPECS].index('fixed-'+position+'-candidate')
  need(parser.SPECS[index][1]==({'top':0x47015354,'bottom':0x47016264}[position]),'fixed bus address '+position)
  decodedReferences[position]={'busAddress':hex(parser.SPECS[index][1]),'bytes':104,'allZero':True,
   'sha256':sha(b),'firstLane':568,'lastCompleteLane':635,'completeLanes':68,
   'decodedBytes':102,'ignoredTailBytes':2,'allCompleteLaneValues':lanes,
   'requestedLaneValues':requested,'readBracket':interpretation['readBrackets']['fixed-'+position+'-candidate']}
 for col in ('X','Y','RGB','Diff'):
  need(actual[col+'.bin']==bytes(96),'cleared sampled column '+col)
 need(any(actual['B.bin']),'B retains nonzero data')
 need(actual['start-R.bin']==actual['end-R.bin'] and actual['start-N.bin']==actual['end-N.bin'],'matching sequential R/N bytes')
 need(interpretation['startR']=={'stop':0,'fault':0,'ordinaryGate':1,'alternateLimit':40,'mode1RecordLatch':0},'actual clean state')
 need(interpretation['startN']=={'ordinals':[0]*6,'sourceCounts':[0]*6},'actual zero ordinals/counts')
 need(interpretation['sourceContext']['selectorC7']==0 and interpretation['sourceContext']['publicationBoundMirror']==200,'baseline selector/mirror')
 # Retained chain binds the FINAL review version. Initial version is preserved history.
 readyBytes=(CAPTURE/'readiness-decision.json').read_bytes();rh=sha(readyBytes);ready=json.loads(readyBytes)
 need(rh=='a8761a8dbe6d80d79a7ee86675859ab89f5eb3bfdb461134bb86c6e6d3a073bd','actual readiness anchor')
 need(rh==result['readinessSha256']==record['readinessSha256'],'saved readiness chain')
 evidence=[]
 for e in ready['evidence']:
  observed=sha(Path(e['path']).read_bytes());need(observed==e['sha256'],'readiness evidence '+e['path'])
  evidence.append({'path':e['path'],'declaredSha256':e['sha256'],'observedSha256':observed,'matches':True})
 finalBytes=(DT/'reviews/independent-validation.json').read_bytes();initialBytes=(DT/'reviews/independent-validation-initial.json').read_bytes()
 finalHash=sha(finalBytes);initialHash=sha(initialBytes)
 need(finalHash=='a09c5c3f913a263a326bc62d66309a63d2faf0ea3fbd06085a544ad7e8cbe4c4','final review')
 need(initialHash=='2f095687a0ceff1c6df5970d53029d8a569434c5e656a6251c47b813fa8435d3','initial review preserved')
 refs=[e for e in ready['evidence'] if e['path']==str(DT/'reviews/independent-validation.json')]
 need(len(refs)==1 and refs[0]['sha256']==finalHash,'actual readiness bound final review')
 final=json.loads(finalBytes);initial=json.loads(initialBytes)
 need(set(final)-set(initial)=={'sourceRangesVerified','sourceRangeEvidence'} and not(set(initial)-set(final)),'only final range evidence added')
 need(all(final[k]==v for k,v in initial.items()),'all prior review fields unchanged')
 reconstructed={k:v for k,v in final.items() if k not in ('sourceRangesVerified','sourceRangeEvidence')}
 need((json.dumps(reconstructed,indent=2,sort_keys=True)+'\n').encode()==initialBytes,'byte-exact historical review reconstruction')
 package=(BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
 need(sha(package)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package source')
 for r in final['sourceRangeEvidence']:
  off=int(r['file_offset'],16);need(sha(package[off:off+r['bytes']])==r['sha256'],'selected source range '+r['label'])
 return {'schema':'dt-actual-baseline-analysis-v1','checks':checks,'nativeReceiptSha256':sha((CAPTURE/'native.receipt.json').read_bytes()),
 'manifestSha256':mh,'parserSha256':manifest['parserSha256'],'rawFiles':summaries,'fixedReferences':decodedReferences,
 'interpretation':interpretation,'captureSoftwareSpanUs':{'beforeUs':n['steps'][0]['beforeUs'],'afterUs':n['steps'][-1]['afterUs'],'widthUs':n['steps'][-1]['afterUs']-n['steps'][0]['beforeUs']},
 'provenance':{'actualSavedReadinessSha256':rh,'savedRecordAndResultMatch':True,'finalReviewSha256':finalHash,'initialReviewHistorySha256':initialHash,
 'readinessReferencedFinalVersion':True,'observedEvidenceDrift':False,'allReadinessEvidence':evidence,'initialReviewByteExactReconstructed':True,
 'finalOnlyAddedFields':['sourceRangeEvidence','sourceRangesVerified'],'originalReadinessOrCaptureRewritten':False,
 'scope':'Consistency of retained readiness, record, result, source/payload and current evidence pins; not an invented launch-time filesystem snapshot'},
 'claims':{'strictTransportAccepted':True,'savedWrapperAccepted':True,'physicalPictureObserved':False,'atomicSnapshot':False,
 'referenceIdentityAtFaultProven':False,'actualSelectedABranchProven':False,'allFixedReferenceBuffersProvenZero':False,
 'historicalFaultScoreOrActualARecovered':False,'readinessRehabilitationNeeded':False},
 'originalCounters':{'headers':14,'bulkTransfers':28,'nativeInvocations':1,'writes':0,'uiOperations':0,'protocolPhase':n['protocolPhase'],'released':n['released'],'closed':n['closed'],'cleanup':result['cleanup']}}

if __name__=='__main__':
 d=analyze();s=json.dumps(d,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==s,'exact decoded replay')
 elif not sys.argv[1:]:(HERE/'decoded.json').write_text(s)
 else:raise SystemExit('usage: analyze.py [--check]')
 print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(s.encode()),'observedReadinessDrift':False,'hostOnly':True}))
