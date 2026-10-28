#!/usr/bin/env python3
"""FR finite source/epoch separation audit. Read retained host files only."""
from pathlib import Path
import base64,hashlib,json,struct,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def u16(b,a):return struct.unpack_from('<H',b,a)[0]
def u32(b,a):return struct.unpack_from('<I',b,a)[0]
def run():
 for row in json.loads((P/'input-pins.json').read_bytes())['files']:
  path=Path(row['path']);path=path if path.is_absolute()else B/path;b=path.read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'input pin '+row['path'])
 blob=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(len(blob)==0x500000 and sha(blob)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected asset')
 image=blob[0x40200:0x60200]
 sys.path.insert(0,'/tmp/tcon-capstone');from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 dis=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 def ins(a,mn,op):
  i=next(dis.disasm(image[a:a+4],a),None);need(i is not None and(i.mnemonic,i.op_str)==(mn,op),'source instruction '+hex(a));return {'va':hex(a),'mnemonic':mn,'operands':op}
 anchors=[]
 def add(a,m,o):anchors.append(ins(a,m,o))
 # Aggregate admission, q/history, delayed add, conditional subtraction and low16 comparison.
 for a,m,o in [(0x1e98,'ldrb.w','r0, [r6, #0x6c7]'),(0x1e9e,'movw','r0, #0x24c4'),(0x1ea6,'movw','r0, #0x2430'),(0x1eac,'mov','fp, r0'),(0x1ef6,'movw','r0, #0x249e'),(0x1efc,'cmp','r0, #1'),(0x1efe,'bne','#0x1fe8'),(0x1f00,'bl','#0x35a4'),(0x1f06,'bne','#0x1efe'),(0x35ac,'movw','r0, #0x240e'),(0x35b2,'cbnz','r0, #0x35b8'),(0x1f14,'and.w','r1, r1, r0, lsl #1'),(0x1f26,'and','r1, r0, #0x1f'),(0x1f3c,'strh.w','r1, [r2, r0, lsl #3]'),(0x1f4e,'strh','r1, [r0, #2]'),(0x1f60,'strh','r1, [r0, #4]'),(0x1f6e,'strh','r1, [r0, #6]'),(0x1f78,'movw','r0, #0x24a0'),(0x1f80,'ble','#0x1fb2'),(0x1f8a,'adds','r0, r0, #1'),(0x1fba,'bl','#0x1e46'),(0x1fbe,'cbz','r0, #0x200e'),(0x1fca,'ldrh.w','r0, [r2, r0, lsl #3]'),(0x1fce,'add','r1, r0'),(0x1fd4,'str.w','r1, [r2, r0, lsl #2]'),(0x1fd8,'movw','r0, #0x24d2'),(0x1fe0,'bl','#0xca10'),(0x1fea,'bl','#0xc8a0'),(0x1ff8,'cmp','r0, sl'),(0x1ffa,'blo','#0x200e'),(0x2002,'sub.w','r1, r0, sl'),(0x200a,'str.w','r1, [r2, r0, lsl #2]'),(0x2012,'ldrh.w','r0, [r1, r0, lsl #2]'),(0x2016,'uxth','r7, r0'),(0x202a,'cmp','r7, fp'),(0x202c,'ble','#0x203e'),(0x2036,'mov.w','r0, #0x2e0'),(0x203a,'bl','#0xc1e0')]:add(a,m,o)
 for a,n in [(0x1e48,8),(0x1e4c,9),(0x1e50,10),(0x1e54,12),(0x1e58,24),(0x1e5c,25)]:add(a,'cmp','r1, #'+(hex(n)if n>=10 else str(n)))
 # Formatter keeps publishing, printing, sourcecount and aggregate as distinct stages.
 for a,m,o in [(0xc604,'bhi','#0xc6de'),(0xc60a,'cmp','r0, #4'),(0xc60c,'bge','#0xc63c'),(0xc616,'strb','r0, [r1]'),(0xc620,'strd','r7, sl, [sp, #4]'),(0xc624,'str.w','r8, [sp]'),(0xc628,'str','r0, [sp, #0xc]'),(0xc62e,'ldr.w','r1, [r2, r0, lsl #2]'),(0xc632,'mov','r3, r6'),(0xc634,'mov','r2, sb'),(0xc638,'bl','#0x1b8c8'),(0xc64c,'cmp.w','r0, #0x200'),(0xc6b2,'adds','r0, r0, #1'),(0xc6b8,'str.w','r0, [r2, r1, lsl #2]'),(0xc6de,'b','#0xc708'),(0xc710,'adds','r0, r0, #1'),(0xc718,'strh.w','r1, [r2, r0, lsl #1]'),(0xc738,'movw','r0, #0x249e'),(0xc740,'beq','#0xc79e'),(0xb7fc,'movs','r1, #0'),(0xb800,'strh.w','r1, [r2, r0, lsl #1]'),(0xb808,'cmp','r0, #6'),(0xb80a,'blt','#0xb7fc'),(0xbfbc,'bl','#0x1e68'),(0xbfd0,'bl','#0x1e68'),(0xbfdc,'bl','#0x1e68')]:add(a,m,o)
 # Refresher resets print budget separately; whole epoch reset clears the aggregates too.
 for a,m,o in [(0x3a04,'movs','r0, #0'),(0x3a06,'strb.w','r0, [sp, #0xe]'),(0x3a0e,'bl','#0xbb58'),(0xbb92,'ldrb.w','r0, [sp, #0xe]'),(0xbb98,'strb','r0, [r1]'),(0xca88,'movs','r1, #0'),(0xcaa6,'movs','r2, #0'),(0xca8c,'str.w','r1, [r2, r0, lsl #2]'),(0xca92,'strh.w','r1, [r2, r0, lsl #1]'),(0xca98,'str.w','r1, [r2, r0, lsl #2]'),(0xca9e,'strh.w','r1, [r2, r0, lsl #1]'),(0xcaae,'strh.w','r2, [r3, r1, lsl #1]'),(0xcabe,'cmp','r0, #6'),(0xb964,'bl','#0xca84'),(0xcb50,'bl','#0xca84'),(0xc228,'bl','#0xcb2c'),(0xb6a0,'bl','#0xcb2c')]:add(a,m,o)
 literals={0x2044:0x2000d0fc,0x2048:0x2000d108,0x204c:0x2000ba40,0x206c:0x2000d0e4,0xb890:0x2000ba40,0xc84c:0x2000ba28,0xc850:0x200004ca,0xc854:0x200004be,0xc88c:0x2000ba40,0xbbb8:0x200004be,0xcafc:0x2000ba28,0xcb00:0x2000ba40,0xcb04:0x2000d0e4,0xcb08:0x2000d0fc,0xcb0c:0x2000d108}
 for a,v in literals.items():need(u32(image,a)==v,'literal '+hex(a))
 fmt=image[0xc858:image.index(0,0xc858)].decode();need(fmt=='[RTP %3d]RGB:%d x:%4d y:%4d/c:%4d/diff:%d/m:%s\n','exact detail format')
 # SWU owns the complete independent header proof. Revalidate its sealed report/spans.
 fo=B/'combined-event-successor-trial-20261028fo/live-analysis';decoded_raw=(fo/'decoded.json').read_bytes();need(sha(decoded_raw)=='2ae4c84ab06ff2db7492329e39d88c6730141038d73f1f70ffb338c22f2f1c4c','sealed FO decode')
 decoded=json.loads(decoded_raw)
 for r in decoded['sourceSpans']:
  at=int(r['fileOffset'],16);need(r['image']==1 and at==int(r['va'],16)+0x40200 and sha(blob[at:at+r['bytes']])==r['sha256'],'SWU source span '+r['va'])
 need(decoded['ring']['candidateHeader']['numeric']==159 and decoded['maximumSampledH0']==36,'sealed header and all-row maximum')
 # Bind only the small source-relevant row fields back to the original compact receipt.
 native=json.loads((B/'combined-event-successor-trial-20261028fo/capture-01/native.receipt.json').read_bytes());packed=base64.b64decode(native['rows']['rawBase64'],validate=True);need(len(packed)==56*58 and sha(packed)==native['rows']['sha256'],'actual packed rows')
 rows=[]
 for k in range(56):
  b=packed[k*58:(k+1)*58];r=decoded['rows'][k];need(u32(b,6)==r['h0']and u16(b,10)==r['hHalf28']and list(struct.unpack_from('<4H',b,12))==r['history']and u32(b,20)==r['ordinalSlot0'],'FO row source fields '+str(k+1));rows.append({'cycle':k+1,'h0':u32(b,6),'q':u16(b,10),'history':list(struct.unpack_from('<4H',b,12)),'ordinal':u32(b,20)})
 need(max(r['h0']for r in rows)==36 and rows[0]['h0']==rows[-1]['h0']==0 and any(r['h0']>0 for r in rows),'endpoint-only zero claim is false')
 need(decoded['nativeAccepted']and decoded['cleanCycles']==55 and decoded['quiescentCycles']==1,'FO lifecycle summary')
 # Finite source models: publication and current count are not the aggregate.
 skip={8,9,10,12,24,25}
 def aggregate(a,h,q,s,bp,t,gate=1):
  if gate!=1:return a,list(h),q,None
  q=((q<<1)&31)+int(s>bp);h=[h[1],h[2],h[3],s]
  if q not in skip:
   a=(a+h[0])&0xffffffff
   if a>=t:a-=t
  return a,h,q,a&0xffff
 for q in range(32):
  for s in [0,4,160,161,65535]:
   a,h,nq,score=aggregate(20,[0,4,0,0],q,s,160,1)
   need(nq==((q<<1)&31)+int(s>160)and score==a&65535,'q/history/score finite model')
   need(a==(20 if nq in skip else 23),'delayed addition4 minusT1 or skip')
   need(h==[4,0,0,s],'history shift inserts current sourcecount')
 need(aggregate(20,[0,0,0,0],0,0,160,20)[0]==0,'positive subtraction can return aggregate to zero without reset')
 need(aggregate(0,[0,0,0,4],0,4,160,0)[0]==0,'formatted/current counts are delayed, not immediate aggregate')
 need(aggregate(0,[0,0,4,4],0,4,160,0)[0]==0,'second delayed example')
 need(aggregate(0,[0,4,4,4],0,4,160,0)[0]==4,'third shifted delayed count reaches accumulator')
 need(aggregate(20,[1,2,3,4],0,10,160,0,0)==(20,[1,2,3,4],0,None),'aggregate gate bypass changes neither history nor accumulator')
 ordinal=0;count=0;printed=[]
 for call in range(100):
  # A refreshed print budget permits the illustrative lines; actual refresh timing is unknown.
  if ordinal<=40:printed.append(ordinal);ordinal+=1
  count=(count+1)&65535
 need(printed==list(range(41))and ordinal==41 and count==100,'publication41 does not cap current sourcecount')
 # Positive BL candidates from every halfword; not an alias-complete code/writer census.
 targets={0xca84:[],0xcb2c:[],0x1e68:[],0xbb58:[]}
 for a in range(0,len(image)-4,2):
  i=next(dis.disasm(image[a:a+4],a),None)
  if i and i.mnemonic=='bl':
   for target in targets:
    if i.op_str=='#'+hex(target):targets[target].append(hex(a))
 need(targets=={0xca84:['0xb964','0xcb50'],0xcb2c:['0xb6a0','0xc228'],0x1e68:['0xbfbc','0xbfd0','0xbfdc'],0xbb58:['0x3a0e']},'bounded aligned direct BL candidates')
 spans=[]
 for role,a,z in [('q-filter',0x1e46,0x1e68),('aggregate',0x1e68,0x2070),('gate-helper',0x35a4,0x35bc),('dispatch',0xb7ec,0xb890),('frame-end',0xb8a8,0xb976),('formatter',0xc5d0,0xc842),('refresher-budget',0x39c4,0x3a1a),('runtime-context-copy',0xbb58,0xbbbc),('reset',0xca84,0xcafc),('initialization',0xcb2c,0xcbae),('unpacker-tail',0xbfac,0xbfe0),('unpacker-publication-bound',0xbdf0,0xbe0c),('T-helper-normal',0xc8a0,0xca08),('T-helper-alternate',0xca10,0xca76),('T-lane-helper',0x2740,0x278a)]:spans.append({'role':role,'image':1,'va':hex(a),'endExclusive':hex(z),'fileOffset':hex(a+0x40200),'sha256':sha(image[a:z])})
 return {'schema':'fr-rtp-publication-aggregate-source-v1','checks':checks,'targetRootNetworkOperations':0,'selectedAssetSha256':sha(blob),'sourceSpans':spans,'decisiveInstructions':anchors,'literalTargets':{hex(k):hex(v)for k,v in literals.items()},'detailFormat':fmt,'detailArguments':['ordinal[mode-1]','channel-like','lane_index (without xBase)','row-like','B','unsigned difference','mode string'],'headerSourceDelegatedToFo':{'reportSha256':sha(decoded_raw),'numeric':159,'meaning':'pre-increment u16 CPU200004a0 invocation counter; not score, temperature or threshold'},'positiveWriterEdges':{'aggregate':'1fd4 add delayed history[0];200a subtractT whenA>=T;ca98 whole reset','sourceCount':'b800 reset before each dispatcher; c718 increment for every admitted formatter record including publication bypass;ca92 whole reset','publicationOrdinal':'c6b8 increment while preordinal<=bound;ca8c reset; nonaggregate wait branchc780 may decrement','history':'1f3c/1f4e/1f60/1f6e shift/currentcount insert; caae reset','q':'1f1c/1f2c shift/mask;1f92 event bit when sourcecount>root24a0;ca9e reset','printBudget':'3a04/3a06 outgoing0;3a0e->bb58;bb98 CPU4be0; c616 increments up to4 per refresh'},'directBlCandidates':{hex(k):v for k,v in targets.items()},'finiteModelWitness':{'publicationOrdinals':41,'publicationFinalOrdinal':41,'qualifyingSourceCount':100,'aggregateCanReturnZeroWithoutReset':True,'qSkipValues':sorted(skip),'delay':'post-shift history[0], not freshly inserted history[3]'},'foObservation':{'rows':56,'maximumSampledAggregate':36,'firstSampledAggregate':rows[0]['h0'],'lastSampledAggregate':rows[-1]['h0'],'nonzeroAggregateCycles':[r['cycle']for r in rows if r['h0']>0],'publicationFinalOrdinal':rows[-1]['ordinal'],'candidateDetailRows':len(decoded['ring']['candidateRows']),'sourceFields':rows},'completeWriterCensus':False,'actualInvocationTraceProven':False,'actualFpProven':False,'recordEpochProven':False,'ringNoWrapProven':False,'eventAbsenceProven':False,'physicalCorrectnessProven':False}
if __name__=='__main__':print(json.dumps(run(),sort_keys=True,indent=2))
