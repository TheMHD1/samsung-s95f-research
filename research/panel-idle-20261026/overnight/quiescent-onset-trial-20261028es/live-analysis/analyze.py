#!/usr/bin/env python3
"""Offline, pinned ES actual capture replay; no transport imports or target operations."""
import base64,copy,hashlib,json,re,statistics,struct,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;S=D.parent;B=S.parent;T=S/'trial-01'
checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def readj(path):return json.loads(path.read_bytes())
def half(b,o):return struct.unpack_from('<H',b,o)[0]
def triplet(b):return [half(b,o)for o in (0,10,14)]
def pin_inputs():
 entries=readj(D/'input-pins.json')['files']
 for row in entries:
  p=B/row['path'];b=p.read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'pinned input '+row['path'])
 return len(entries)
def binding_summary(n):
 return [{'stage':c['stage'],'ownClaim':c['ownClaim'],'localFdMatches':c['localFdMatches'],'kernelReturn':None if c['kernel']is None else c['kernel']['return'],'kernelErrno':None if c['kernel']is None else c['kernel']['errno'],'kernelName':None if c['kernel']is None else c['kernel']['name'],'followMatchesCanonicalDeviceInode':all(c['follow'][k]==c['canonical'][k]for k in ('inode','devMajor','devMinor'))if c['ownClaim']else None}for c in n['bindingChecks']]
def transport_and_saved(role,wrapper,n,rawfiles):
 p=T/role;r=readj(p/'result.json');record=readj(p/'record.json')
 need(r['accepted']is True and r['cleanup']=='STAGE_ABSENT'and r['nativeInvocations']==1 and r['retries']==0,'accepted wrapper '+role)
 need(n['accepted']is True and n['protocolPhase']=='ReadyForHeader'and n['released']and n['closed'],'native closed '+role)
 need(record['native_invocations']==1 and record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','record complete '+role)
 need(r['manifestSha256']==sha((p/'reviewed-manifest.json').read_bytes())==sha((wrapper.HERE/'deployment-manifest.json').read_bytes()),'manifest '+role)
 ready,readyraw=wrapper.load_readiness(p/'readiness-decision.json',r['readinessSha256'])
 need(ready['identity']['devnum']=='62'and n['device']==62,'same qualified62 '+role)
 need(sha(readyraw)==sha((T/({'baseline':'baseline-readiness','onset':'onset-readiness','post-tables':'post-readiness'}[role])/'readiness.json').read_bytes()),'exact readiness '+role)
 for e in ready['evidence']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'readiness evidence '+role)
 for marker,file in [('PRE_READY','metadata-pre.txt'),('BEFORE_INVOKE_READY','metadata-before-invoke.txt'),('POST_READY','metadata-post.txt')]:
  q=wrapper.parse_metadata((p/file).read_text(),marker);need(q['observedHolders']==q['otherErrors']==0,'cached census '+role)
 for kind in ['selftest','native']:
  raw=(p/(kind+'-envelope.txt')).read_text()
  if kind=='native':need(raw.startswith('IMMEDIATE_READY\n'),'immediate identity '+role);raw=raw.removeprefix('IMMEDIATE_READY\n')
  terminal,receipt,out,err=wrapper.receipt_envelope(raw)
  need(terminal['exit_code']==0 and err==b'','envelope exit '+role)
  for suffix,actual in [('receipt.json',receipt),('stdout',out),('stderr',err)]:need((p/(kind+'.'+suffix)).read_bytes()==actual,'envelope bytes '+role+kind+suffix)
 for c in record['calls']:
  response=c['response'];cmds=response['commands']
  need(c['host_timeout']is False and c['transport_exit']==0 and c['transport_stderr']=={'data':'','encoding':'base64'},'root transport '+role)
  need(response['authenticated']is True and response['uid']==response['euid']==0 and len(cmds)==1,'root identity '+role)
  need(cmds[0]['command']==c['command']and cmds[0]['exit_code']==0 and cmds[0]['timed_out']is False and cmds[0]['stderr']=='','root command completed '+role)
 inventory=[]
 for name,raw,digest in rawfiles:
  need((p/name).read_bytes()==raw and sha(raw)==digest,'exact saved raw '+role+name)
  inventory.append({'name':name,'bytes':len(raw),'sha256':digest})
 need(r['rawFiles']==inventory and r['headersSent']==n['headersSent']and r['bulkTransfers']==n['bulkTransfers'],'counts/inventory '+role)
 return {'accepted':True,'device':62,'headers':n['headersSent'],'bulks':n['bulkTransfers'],'phase':n['protocolPhase'],'released':n['released'],'closed':n['closed'],'cleanup':'STAGE_ABSENT','rootCallsVerified':len(record['calls']),'rawFiles':inventory,'nativeReceiptSha256':sha((p/'native.receipt.json').read_bytes()),'readinessSha256':r['readinessSha256'],'manifestSha256':r['manifestSha256'],'binding':binding_summary(n)if'bindingChecks'in n else {'qualified':n['bindingQualified'],'fullSuccessAuditOmittedByFrozenSource':True}}
def decode_retained(n):
 values=[]
 for cap in n['retained']:
  row={'role':cap['role'],'cycle':cap['cycleIndex'],'windows':[]}
  for i,w in enumerate(cap['windows']):
   b=base64.b64decode(w['rawBase64']);x={'name':w['name'],'bytes':len(b),'sha256':sha(b),'readBracketUs':[cap['transfers'][2*i]['beforeUs'],cap['transfers'][2*i+1]['afterUs']]}
   if w['name']=='R':x.update(rt=triplet(b),limit=half(b,196),operatingMode=half(b,16),recordLatch=half(b,144),selectorMirror=half(b,202),root2468=half(b,104))
   if w['name']=='H':x.update(a0U32=struct.unpack_from('<I',b,4)[0],q0U16=half(b,28),history=list(struct.unpack_from('<4H',b,40)))
   if w['name']=='N':x.update(ordinals=list(struct.unpack_from('<6I',b)),counts=list(struct.unpack_from('<6H',b,24)))
   if w['name']=='M':x.update(trainer=[half(b,2),half(b,4)],refresh=[half(b,34),half(b,36)],aa=half(b,10),ac=half(b,12),publicationMirror=half(b,42),override4cc=b[44])
   if w['name']=='P':x.update(dynamicAPointer=struct.unpack_from('<I',b,4)[0],dynamicBPointer=struct.unpack_from('<I',b,8)[0])
   if w['name']=='C':x.update(selectorC7=b[7],geometry=list(struct.unpack_from('<3H',b)))
   row['windows'].append(x)
  values.append(row)
 return values
def decode_eb(q,rawfiles):
 d={name:raw for name,raw,_ in rawfiles}
 return {'startR':q['startR'],'endR':q['endR'],'startN':q['startN'],'endN':q['endN'],'rBytesEqual':q['rBytesEqual'],'nBytesEqual':q['nBytesEqual'],'sourceContext':q['sourceContext'],'all68PrimaryZero':not any(d['primary-lane-gate.bin']),'all68SecondaryZero':not any(d['secondary-lane-gate.bin']),'localEligibilityOnly':True,'actualComparatorCallProven':False,'referenceCandidates':q['fixedReferenceCandidates'],'descriptorHalfwords':q['descriptorRawHalfwords'],'tuples':q['candidateTuples'],'readBrackets':q['readBrackets'],'recordEpochProven':False,'actualFixedABranchProven':False}
def trace_summary():
 p=T/'kernel-trace';b=(p/'trace.txt').read_bytes();r=readj(p/'result.json');state=readj(p/'state.json');start=(p/'start.txt').read_text();stop=(p/'stop.txt').read_text()
 need(r['accepted']is True and r['instance_removed']is True and r['global_tracer_modified']is False and r['retained_bytes']==len(b)and r['sha256']==sha(b),'accepted trace hash/cleanup')
 need('STARTED\n1\n'in start and '[mono]'in start and start.endswith('GLOBAL_AFTER\n0\nnop\n'),'trace clock/start/global')
 need(stop.endswith('GLOBAL_AFTER\n0\nnop\n')and re.search(r'TRACE_BYTES\n'+str(len(b))+r'\nTRACE_SHA\n'+sha(b),stop),'trace stop/global/hash')
 stats=[]
 for cpu,text in re.findall(r'/per_cpu/(cpu[0-9]+)/stats\n(.*?)(?=/sys/|GLOBAL_AFTER|\Z)',stop,re.S):
  vals={k:int(v)for k,v in re.findall(r'^(entries|overrun|commit overrun|dropped events|read events): ([0-9]+)$',text,re.M)}
  need(vals['overrun']==vals['commit overrun']==vals['dropped events']==0,'trace no recorded loss '+cpu);stats.append({'cpu':cpu,**vals})
 need(len(stats)==4,'four CPU stats')
 events=[]
 for line in b.decode().splitlines():
  match=re.search(r'\s([0-9]+\.[0-9]+): (irq_handler_entry|irq_handler_exit|gpio_value|gpio_direction|suspend_resume): (.*)$',line)
  if match:events.append({'kernelTraceTime':match[1],'kind':match[2],'detail':match[3]})
 need(len(events)==28 and sum(x['entries']for x in stats)==28,'trace event count')
 need(all('irq=30 'in e['detail']for e in events),'all retained events irq30')
 for i in range(0,len(events),2):
  need(events[i]['kind']=='irq_handler_entry'and events[i+1]['kind']=='irq_handler_exit'and float(events[i]['kernelTraceTime'])<=float(events[i+1]['kernelTraceTime']),'paired ordered IRQ30 events')
 return {'accepted':True,'bytes':len(b),'sha256':sha(b),'events':events,'entryExitPairs':14,'cpuStats':stats,'filters':state['events'],'clockReceipt':'mono selected','firstEventTraceTime':events[0]['kernelTraceTime'],'lastEventTraceTime':events[-1]['kernelTraceTime'],'instanceRemoved':True,'globalTracerModified':False,'nativeClockMappingProven':False,'crossClockSubtractionPerformed':False,'absenceScope':'No IRQ84, selected GPIO or suspend_resume events in retained filtered trace. No exclusion of uninstrumented/controller-local paths.'}
def mutation_tests(parser,n):
 total=0
 def refuse(z):
  nonlocal total
  try:parser.parse_native(json.dumps(z))
  except(ValueError,TypeError,KeyError,StopIteration):total+=1;return
  raise ValueError('malformed actual clone accepted')
 for key,value in [('accepted',False),('observationAccepted',False),('protocolPhase','Unknown'),('released',False),('closed',False),('quiescentCyclesCompleted',0),('headersSent',231),('bulkTransfers',463),('bindingQualified',False)]:
  z=copy.deepcopy(n);z[key]=value;refuse(z)
 for at in [14*58,27*58+54]:
  z=copy.deepcopy(n);b=bytearray(base64.b64decode(z['scoreCheckpoints']['rawBase64']));b[at]^=2;z['scoreCheckpoints']['rawBase64']=base64.b64encode(b).decode();z['scoreCheckpoints']['sha256']=sha(b);refuse(z)
 z=copy.deepcopy(n);z['intervention']['calls'][0]['reaped']=False;refuse(z)
 return total
def run():
 count=pin_inputs();ER=B/'rtp-quiescent-checkpoints-20261028er';EB=B/'rtp-lane-gate-capture-20261028eb'
 erp=load(ER/'parse-result.py');ebp=load(EB/'parse-result.py');erw=load(ER/'run-once.py');ebw=load(EB/'run-once.py')
 for folder in [ER,EB]:
  for f in readj(folder/'source-inventory.json')['files']:
   raw=(folder/f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'frozen source '+f['path'])
 n,_,rf,gc,q=erp.parse_native((T/'onset/native.receipt.json').read_text());need(gc==[]and q['trialQualified'],'strict ER actual')
 need(q==readj(T/'onset/interpretation.json'),'saved ER interpretation exact')
 onset=transport_and_saved('onset',erw,n,rf);rows=q['scoreCheckpoints']['rows'];need(len(rows)==28 and n['cyclesStarted']==29 and n['cleanCyclesCompleted']==26 and n['quiescentCyclesCompleted']==2,'actual compact counters')
 need(n['headersSent']==232 and n['bulkTransfers']==464,'28*8 plus one transitionR plus7 postfault')
 phases={}
 for role in ['baseline','post-tables']:
  a,raw,inter=ebp.parse_native((T/role/'native.receipt.json').read_text());need(inter==readj(T/role/'interpretation.json'),'saved EB interpretation '+role)
  phases[role]={'lifecycle':transport_and_saved(role,ebw,a,raw),'samples':decode_eb(inter,raw),'firstOutUs':a['steps'][0]['beforeUs'],'lastInUs':a['steps'][-1]['afterUs']}
 guard=load(S/'verify-observation.py');admission=guard.verify(T/'onset');need(admission==readj(T/'onset-admission.json'),'admission exact')
 result=readj(T/'result.json');need(result['accepted_pair']is True and result['target_recovery_invocations']==0 and result['post_relation']=='same_as_ER_last_R'and result['ER_last_R']==[1,4097,0]and result['EB_post_R']==[[1,4097,0],[1,4097,0]],'coordinator exact accepted pair')
 stages=['trace-start','prepare','baseline-readiness','baseline','onset-readiness','onset','admission','post-readiness','post-tables','trace-stop']
 for stage in stages:
  intent=readj(T/'ledger'/(stage+'-intent.json'));done=readj(T/'ledger'/(stage+'-completion.json'))
  need(done['exit_code']==0 and done['stdout_sha256']==sha((T/'ledger'/(stage+'.stdout')).read_bytes())and done['stderr_sha256']==sha((T/'ledger'/(stage+'.stderr')).read_bytes())and (T/'ledger'/(stage+'.stderr')).read_bytes()==b'','ledger completion '+stage)
  need(intent['automatic_retry']is False and sha(Path(intent['argv'][1]).read_bytes())==intent['helper_sha256'],'ledger source '+stage)
 need([x['cycleIndex']for x in rows if x['quiescentRBracketObserved']]==[15,16],'two actual Q cycles')
 need(all(x[k]==0 for x in rows for k in ['mCpu4a2U16','mCpu4a4U16','endRRoot2460U16','endRRoot246eU16','endRRoot2468U16','q0U16']),'sampled trainer/writer controls zero')
 need([x['selectorC7']for x in rows]==[0]*14+[1]*14 and [x['endRRoot24caU16']for x in rows]==[0]*14+[1]*14,'selector and mirror observed edge')
 retained=decode_retained(n);post=next(x for x in retained if x['role']=='post-fault');posth=next(x for x in post['windows']if x['name']=='H');need(posth['a0U32']==48,'actual postfault H48')
 deltas=[b['hReadBracket']['headerBeforeUs']-a['hReadBracket']['headerBeforeUs']for a,b in zip(rows,rows[1:])]
 bracket=q['ordering']['softwareTransitionBracket'];width=bracket['afterUs']-bracket['beforeUs'];need(width==25967,'exact retained software bracket')
 fields=['startRtClassification','endRtClassification','selectorC7','mCpu4c2U16','mCpu4c4U16','endRRoot24caU16','endRRoot2468U16','publicationBoundMirror','a0U32','recordOrdinal0U32','history0U16x4','capturedDynamicAPointerU32','capturedDynamicBPointerU32']
 changes=[]
 for i,r in enumerate(rows):
  diff={k:r[k]for k in fields if i==0 or r[k]!=rows[i-1][k]}
  if diff:changes.append({'cycle':r['cycleIndex'],**diff})
 gaps={'baselineLastInToERFirstOutUs':n['retained'][0]['transfers'][0]['beforeUs']-phases['baseline']['lastInUs'],'ERLastInToPostEBFirstOutUs':phases['post-tables']['firstOutUs']-max(t['afterUs']for c in n['retained']for t in c['transfers']if t['direction']=='IN'),'sameNativeClockPremise':'Existing native helpers use the same retained RealClock implementation; no ftrace clock values subtracted.'}
 mut=mutation_tests(erp,n);pin_inputs()
 return {'schema':'es-actual-independent-analysis-v1','acceptedObservationVerified':True,'inputFilesVerified':count,'onsetLifecycle':onset,'baseline':phases['baseline'],'postTables':phases['post-tables'],'nativeStartUs':n['startUs'],'nativeEndUs':n['endUs'],'nativeDurationUs':n['endUs']-n['startUs'],'cyclesStarted':29,'cleanComplete':26,'quiescentComplete':2,'compactCount':28,'compactRows':rows,'changes':changes,'retained':retained,'compactMaximumA0':max(x['a0U32']for x in rows),'postFaultRetainedA0':posth['a0U32'],'compactAbove40Witness':False,'key':n['intervention'],'ordering':q['ordering'],'softwareTransitionBracketWidthUs':width,'hStartSpacingUs':{'intervals':len(deltas),'minimum':min(deltas),'median':statistics.median(deltas),'maximum':max(deltas),'over25000':sum(x>25000 for x in deltas),'all':deltas},'sameNativeClockGaps':gaps,'trace':trace_summary(),'malformedActualCloneRefusals':mut,'checksPassed':checks,'scope':{'physicalPictureObserved':False,'actualFpProven':False,'actualComparatorCallProven':False,'callbackTraceProven':False,'referenceEpochProven':False,'keyUiConsumptionProven':False,'recoveryIncluded':False},'targetOperations':0,'rootCalls':0,'networkOperations':0}
if __name__=='__main__':
 value=run();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if '--write'in sys.argv:(D/'decoded.json').write_bytes(raw)
 else:need((D/'decoded.json').read_bytes()==raw,'reproduces decoded byte-exactly')
 print(json.dumps({'accepted':True,'checksPassed':checks,'inputFilesVerified':value['inputFilesVerified'],'malformedRefusals':value['malformedActualCloneRefusals'],'decodedSha256':sha(raw),'targetOperations':0,'rootCalls':0,'networkOperations':0}))
