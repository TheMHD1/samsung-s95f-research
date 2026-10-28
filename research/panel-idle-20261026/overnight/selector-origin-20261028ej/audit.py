#!/usr/bin/env python3
"""Scoped selected-image/retained-window audit. No target, network or root calls."""
from pathlib import Path
import base64,hashlib,json,re,struct,sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS
from capstone.arm import ARM_OP_MEM

H=Path(__file__).resolve().parent;B=H.parent
SHA='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=0
inputs={}
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
def read(rel):
 p=B/rel;need(p.is_file()and not p.is_symlink(),'ordinary scoped input')
 r=p.read_bytes();inputs[rel]={'path':rel,'bytes':len(r),'sha256':sha(r)};return r
raw=read('selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin')
need(len(raw)==5242880 and sha(raw)==SHA,'selected package identity')
d=raw[0x40200:0x60200];cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS);cs.detail=True
word=lambda a:struct.unpack_from('<I',d,a)[0]
anchors=[]
def ins(a,m,o):
 i=next(cs.disasm(d[a:a+4],a,count=1),None)
 need(i is not None and (i.mnemonic,i.op_str)==(m,o),'instruction '+hex(a))
 anchors.append({'va':hex(a),'fileOffset':hex(a+0x40200),'mnemonic':m,'operands':o,'bytes':i.size,'sha256':sha(i.bytes)})
for row in [
(0x38e8,'ldr','r0, [pc, #4]'),(0x38ea,'ldr','r0, [r0]'),(0x38f4,'ldr','r0, [pc, #0]'),
(0x393e,'bl','#0x38e8'),(0x3942,'mov','r6, r0'),(0x3944,'bl','#0x38f4'),(0x3948,'mov','r5, r0'),
(0x394e,'ldrb.w','r0, [r6, #0x3d8]'),(0x3952,'strb.w','r0, [r5, #0x6c7]'),
(0x3956,'ldrb','r0, [r6]'),(0x3958,'strb.w','r0, [r5, #0x6c8]'),
(0x39f6,'movw','r0, #0x24c8'),(0x39fc,'ldrb.w','r1, [r5, #0x6c7]'),(0x3a00,'adds','r0, r0, #2'),(0x3a02,'strh','r1, [r0, r4]'),
(0x18c94,'push','{r4, lr}'),(0x18c96,'bl','#0x3934'),
(0x195f8,'push','{r4, lr}'),(0x195fa,'bl','#0x38fc'),(0x195fe,'mov','r4, r0'),
(0x19600,'movs','r0, #0'),(0x19602,'ldr','r1, [pc, #0x14]'),(0x19604,'strb','r0, [r1]'),
(0x19606,'ldr','r0, [pc, #0x14]'),(0x19608,'ldr','r1, [pc, #0x14]'),(0x1960a,'str','r0, [r1, #4]'),
(0x1960c,'movw','r0, #0x240c'),(0x19610,'ldrh','r0, [r0, r4]'),(0x19612,'str','r0, [r1]'),
(0x19532,'movs','r0, #0'),(0x19534,'ldr','r1, [pc, #0x2c]'),(0x19536,'strb','r0, [r1]'),
(0x19538,'ldr','r1, [pc, #0x2c]'),(0x1953a,'ldr.w','r0, [r1, r0, lsl #3]'),
(0x19540,'str','r0, [r1, #0x24]'),(0x19558,'movs','r0, #1'),(0x1955a,'ldr','r1, [pc, #0x14]'),(0x1955c,'strb','r0, [r1]'),
(0x19586,'ldr','r0, [pc, #0x64]'),(0x19588,'ldrb','r0, [r0]'),(0x1958a,'cmp','r0, #1'),(0x1958c,'bge','#0x195da'),
(0x1958e,'ldr','r0, [pc, #0x60]'),(0x19594,'add.w','r0, r0, r1, lsl #3'),(0x19598,'ldr','r0, [r0, #4]'),
(0x1959a,'cbz','r0, #0x195aa'),(0x195a6,'ldr','r0, [r1, #4]'),(0x195a8,'blx','r0'),
(0x195aa,'ldr','r0, [pc, #0x40]'),(0x195ac,'ldrb','r0, [r0]'),(0x195ae,'cbz','r0, #0x195d2'),
(0x195b2,'ldrb','r0, [r0]'),(0x195b4,'adds','r0, r0, #1'),(0x195b8,'strb','r0, [r1]'),
(0x195be,'ldr.w','r0, [r0, r1, lsl #3]'),(0x195c4,'str','r0, [r1, #0x24]'),
(0x195da,'movs','r0, #0'),(0x195de,'strb','r0, [r1]'),(0x195e2,'strb','r0, [r1]'),
(0x43e6,'bl','#0x19520'),(0x4446,'bl','#0xc250'),(0xaef6,'bl','#0x195f8'),
(0xe064,'ldr','r0, [r0, #0x1c]'),(0xe066,'and','r0, r0, #4'),(0xe06a,'cmp','r0, #4'),(0xe06e,'bl','#0x19574'),
(0xc27c,'ldrb.w','r0, [r5, #0x6c7]'),(0xc284,'cmp','r0, r1'),(0xc286,'beq','#0xc2a4'),
(0xc28e,'strh','r0, [r1]'),(0xc296,'movs','r0, #1'),(0xc29a,'strh','r0, [r1]'),
(0x19770,'bl','#0x38f4'),(0x19774,'mov','r5, r0'),(0x197a2,'ldrb.w','r0, [r5, #0x6c7]'),
(0x197a6,'ldr','r1, [pc, #0x148]'),(0x197a8,'ldrb','r1, [r1]'),(0x197aa,'cmp','r0, r1'),(0x197ac,'beq','#0x197c2'),
(0x197ae,'ldrb.w','r0, [r5, #0x6c7]'),(0x197b4,'strb','r0, [r1]'),(0x197ba,'cbz','r0, #0x197c0'),(0x197bc,'movs','r7, #1'),
(0x197da,'bl','#0x19730'),(0x197fe,'strb.w','r0, [r5, #0x6ce]'),
(0x1e9e,'movw','r0, #0x24c4'),(0x1ea6,'movw','r0, #0x2430'),
(0x1eca,'movw','r0, #0x24c4'),(0x1ed2,'mov.w','r0, #0x24c0'),
(0xbdc8,'movw','r0, #0x24c4'),(0xbdd0,'mov.w','r0, #0x24c0'),
(0xbdfa,'movw','r0, #0x24c4'),(0xbe02,'movw','r0, #0x2430')]:ins(*row)
literals={0x38f0:0x200002cc,0x38f8:0x20000500,0x19618:0x20000460,0x1961c:0x18c95,
0x19620:0x20000468,0x19560:0x40124000,0x19564:0x20000470,0x19568:0x20000468,
0x19570:0x20000460,0x195e8:0x40124000,0x195ec:0x20000470,0x195f0:0x20000468,
0x195f4:0x20000460,0x198f0:0x2000045d,0xc2f0:0x200004c2,0xc2f4:0x200004c4}
for a,v in literals.items():need(word(a)==v,'literal '+hex(a))
# Halfword-overlapping syntactic scan, not a CFG or proof of all reachable writes.
field=[];overlap=[];calls={hex(t):[]for t in (0x3934,0x18c94,0x19520,0x195f8,0x19574)}
absolute=[]
for a in range(0,0x1d6a4,2):
 i=next(cs.disasm(d[a:a+4],a,count=1),None)
 if not i:continue
 if '#0x6c7]'in i.op_str:field.append({'va':hex(a),'mnemonic':i.mnemonic,'operands':i.op_str})
 width={'strb':1,'strh':2,'str':4,'strd':8}.get(i.mnemonic.split('.')[0])
 if width and any(o.type==ARM_OP_MEM and o.mem.disp<=0x6c7<o.mem.disp+width for o in i.operands):
  overlap.append({'va':hex(a),'mnemonic':i.mnemonic,'operands':i.op_str,'width':width})
 if i.mnemonic in ('bl','b.w') and i.op_str.startswith('#0x') and i.op_str[1:]in calls:
  calls[i.op_str[1:]].append(hex(a))
 if a%4==0 and word(a)==0x20000bc7:absolute.append(hex(a))
expected=[0x1e98,0x1ec4,0x1edc,0x3952,0x39fc,0xb83a,0xb862,0xbdc2,0xbdf4,0xc27c,0xc288,
0x18c3a,0x19792,0x197a2,0x197ae,0x19834,0x198b0,0x1992c,0x1b7e0,0x1bf70,0x1c13a]
need([int(r['va'],16)for r in field]==expected,'bounded direct-displacement access census')
need(len(overlap)==1 and overlap[0]['va']=='0x3952','bounded fixed-displacement overlapping store census')
need(absolute==[],'no aligned absolute selector literal')
need(calls=={'0x3934':['0x18c96'],'0x18c94':[],'0x19520':['0x43e6'],'0x195f8':['0xaef6'],'0x19574':['0xe06e']},'bounded direct-call census')
ptrs=[hex(a)for a in range(0,0x1d6a0,2)if word(a)==0x18c95]
need(ptrs==['0x1961c'],'bounded callback pointer census')
need(0x20000500+0x6c7==0x20000bc7 and 0x20010000+0x24ca==0x200124ca,'address arithmetic')
need(0x20000468+8==0x20000470,'index storage follows one configured callback slot')
# Source-backed startup coverage, not proof MODE2 executed it on any particular trial.
need(struct.unpack_from('<4I',d,0x1d6a4+8*16)==(0x1d95c,0x200004f8,0xdca4,0x1d8),'image1 BSS scatter row')
need(0x200004f8<=0x20000bc7<0x2000e19c,'selector static zero-init coverage')
need(0x20000468+8<=0x200004f8,'proposed exact 8-byte table is in startup static data')

captures=[]
for rel in ['rtp-lane-gate-trial-20261028ed/table-read-01',
'volatile-limit-trial-20261028dk/score-baseline-01',
'volatile-limit-trial-20261028dk/reference-onset-01',
'volatile-limit-trial-20261028dk/dv-observation-01',
'volatile-limit-trial-20261028dk/dv-rechallenge-01',
'lane-gate-onset-20261028ee/onset-01']:
 result=json.loads(read(rel+'/result.json'));nraw=read(rel+'/native.receipt.json');native=json.loads(nraw)
 need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT','saved accepted wrapper result')
 need(native['accepted']is True and native['protocolPhase']=='ReadyForHeader'and native['released']is True and native['closed']is True,'saved native accepted terminal')
 indexed={x['name']:x for x in result['rawFiles']};windows={}
 if 'retained'in native:
  for capture in native['retained']:
   prefix=rf"retained-[0-9]{{2}}-{capture['role'].replace('-','_')}-cycle{capture['cycleIndex']:03}-"
   for i,w in enumerate(capture['windows']):
    names=[k for k in indexed if re.fullmatch(prefix+f'{i:02}-'+w['name']+r'\.bin',k)]
    need(len(names)==1,'native retained filename correspondence')
    windows[names[0]]=w
 else:windows={w['name']+'.bin':w for w in native['windows']}
 for name,row in indexed.items():
  if not name.endswith('R.bin'):continue
  r=read(rel+'/'+name);w=windows[name]
  need(len(r)==row['bytes']==256 and sha(r)==row['sha256']==w['sha256'],'R raw/result/native hash')
  need(base64.b64decode(w.get('rawBase64',w.get('base64')),validate=True)==r,'R native/raw bytes')
  prefix=re.sub(r'[0-9]{2}-R\.bin$','',name)
  candidates=[k for k in indexed if k.startswith(prefix)and k.endswith('C.bin')] if name not in ('start-R.bin','end-R.bin') else ['C.bin']
  need(len(candidates)<=1,'at most one same-capture C window')
  cname=candidates[0]if candidates else None
  c=None
  if cname is not None:
   c=read(rel+'/'+cname);cw=windows[cname]
   need(len(c)==16 and sha(c)==indexed[cname]['sha256']==cw['sha256'],'C raw/result/native hash')
   need(base64.b64decode(cw.get('rawBase64',cw.get('base64')),validate=True)==c,'C native/raw bytes')
  half=lambda o:struct.unpack_from('<H',r,o)[0]
  captures.append({'capture':rel,'rFile':name,'rSha256':sha(r),'cFile':cname,'cSha256':sha(c)if c is not None else None,
  'configuredDelayRoot240cU16':half(12),'selectorMirrorRoot24caU16':half(0xca),'selectorC7U8':c[7]if c is not None else None,
  'rt':{'stop':half(0),'fault':half(10),'ordinaryGate':half(14),'alternateLimit':half(0xc4)},
  'sameEpochOrCallbackTimingProven':False})
need(all(x['configuredDelayRoot240cU16']==200 for x in captures),'retained configured delay values')
need(all(x['selectorC7U8']is None or x['selectorMirrorRoot24caU16']==x['selectorC7U8']for x in captures),'retained source mirror consistency')
prior=['firmware-rtp-producer-20261028df/README.md',
'firmware-rtp-producer-20261028df/cross-core-slg-addendum.md',
'firmware-rtp-producer-20261028df/source-upstream/README.md',
'firmware-rtp-producer-20261028df/source-upstream/byte-verification.json',
'rtp-fixed-reference-qualification-20261028dr/README.md',
'controller-scratch-rollback-20261028dz/README.md',
'controller-scratch-rollback-20261028dz/source-audit.json',
'reference-refresh-control-20261028eg/README.md',
'reference-refresh-control-20261028eg/source-audit.json',
'code-alias-qualification-20261028dw/README.md',
'code-alias-qualification-20261028dw/source-qualification.json']
for rel in prior:read(rel)
ranges=[(0x38e8,0x14),(0x3934,0x28),(0x39ee,0x18),(0x18c94,0x46),(0x19520,0xd8),
(0x195f8,0x2c),(0xe060,0x32),(0x43e2,8),(0x4440,10),(0xaef6,4),(0xc250,0xa8),
(0x1976c,0x94),(0x198f0,12),(0x1e68,0x8c),(0xbdbe,0x50),(0x1d724,16)]
report={'schema':'ej-selector-origin-source-v1','selectedAssetSha256':SHA,'codeAddressDomain':'image1-CPU',
'image1FileBias':'0x40200','anchors':anchors,'literals':{hex(a):hex(v)for a,v in literals.items()},
'sourceRanges':[{'va':hex(a),'bytes':n,'fileOffset':hex(a+0x40200),'sha256':sha(d[a:a+n])}for a,n in ranges],
'syntacticC7DisplacementAccesses':field,'syntacticOverlappingStores':overlap,'alignedAbsoluteSelectorLiterals':absolute,
'directCallCandidates':calls,'thumbCallbackPointerCandidates':ptrs,'completeWriterCensus':False,
'samples':captures,'configuredDelayUnitQualified':False,'actualCallbackPeriodQualified':False,
'persistedOrHighBankOperationPathsFollowed':False,'targetCalls':0,'networkCalls':0}
manifest={'schema':'ej-input-provenance-v1','pathBase':'overnight','files':sorted(inputs.values(),key=lambda r:r['path']),
'rawInputsCopied':False,'networkAcquisition':False}
outputs={'source-audit.json':report,'input-provenance.json':manifest}
for name,value in outputs.items():
 encoded=(json.dumps(value,indent=2)+'\n').encode()
 if sys.argv[1:]==['--record']:
  with (H/name).open('xb')as f:f.write(encoded)
 else:need((H/name).read_bytes()==encoded,'frozen '+name)
print(json.dumps({'accepted':True,'checks':checks,'instructionAnchors':len(anchors),'sampledRWindows':len(captures),
'sourceAuditSha256':sha((json.dumps(report,indent=2)+'\n').encode()),'targetCalls':0,'networkCalls':0},sort_keys=True))
