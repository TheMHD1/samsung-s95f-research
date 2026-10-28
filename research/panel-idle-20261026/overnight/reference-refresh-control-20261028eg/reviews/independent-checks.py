#!/usr/bin/env python3
"""Host-only independent frozen-input and source/model contract checks."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent.parent;B=D.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,label):
 global checks
 checks+=1
 if not v:raise ValueError(label)
def j(p):return json.loads(p.read_text())
inv=j(D/'source-inventory.json')
for f in inv['files']:
 raw=(D/f['name']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'source inventory '+f['name'])
need(sha((D/'refresh_model.py').read_bytes())=='25676e8d0d06404e909097ec1ac17faaff22ee558fd56e9679e799c4e464bc28','frozen model')
prov=j(D/'input-provenance.json');need(len(prov['files'])==36,'36 inputpins')
listed=set()
for f in prov['files']:
 p=B/f['relativeToOvernight'];raw=p.read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'actual provenance '+f['relativeToOvernight']);listed.add(p)
source=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';raw=source.read_bytes();image=raw[0x40200:0x60200]
need(len(raw)==5242880 and sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected exact package')
audit=j(D/'source-audit.json');cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS)
for a in audit['anchors']:
 va=int(a['va'],16);item=next(cs.disasm(image[va:va+4],va,count=1));need(item.mnemonic==a['mnemonic']and item.op_str==a['operands']and item.size==a['bytes']and sha(image[va:va+item.size])==a['sha256'],'all actual anchors')
for r in audit['sourceRanges']:
 va=int(r['va'],16);need(sha(image[va:va+r['bytes']])==r['sha256'],'complete selected source range')
# Supplement anchors around reload/branch/copy arguments, not merely parent anchor subset.
extra={0xc28c:('ldr','r1, [pc, #0x60]'),0xc290:('mov','r0, r1'),0xc29c:('b','#0xc2a4'),0x1c140:('ldr','r0, [pc, #0x60]'),0x1c142:('ldr','r0, [r0]'),0x1c14a:('ldrh','r0, [r0]'),0x1c156:('ldr','r0, [pc, #0x4c]'),0x1c158:('ldr','r1, [r0]'),0x1c15c:('ldr','r0, [pc, #0x48]'),0x1c162:('b','#0x1c18e'),0x1c176:('ldrh','r0, [r0]'),0x1c182:('ldr','r0, [pc, #0x20]'),0x1c184:('ldr','r1, [r0]'),0x1c188:('ldr','r0, [pc, #0x20]'),0x1c190:('ldrh','r0, [r0]'),0xb820:('mov','r0, r1'),0xb822:('ldr','r0, [r0]'),0xb878:('b','#0xb88e')}
for va,want in extra.items():
 item=next(cs.disasm(image[va:va+4],va,count=1));need((item.mnemonic,item.op_str)==want,'supplementary dominance/reload '+hex(va))
need(0x20000500+0x6c7==0x20000bc7,'C selector offset')
need((0x200004c2-0x200004a0,0x200004c4-0x200004a0)==(34,36),'M offsets')
need((0x20000494-0x20000490,0x20000498-0x20000490)==(4,8),'P offsets')
used={source}
for row in audit['retainedBoundarySamples']:
 directory=B/row['capture'];resultpath=directory/'result.json';result=j(resultpath);used.add(resultpath)
 need(resultpath in listed and result['accepted']and result['cleanup']=='STAGE_ABSENT','accepted pinned result')
 byname={f['name']:f for f in result['rawFiles']};decoded=[]
 for suffix,size in [('01-M.bin',68),('02-C.bin',16),('03-P.bin',16)]:
  p=directory/(row['prefix']+suffix);b=p.read_bytes();entry=byname[p.name];need(p in listed and len(b)==size==entry['bytes']and sha(b)==entry['sha256'],'pinned result/raw relationship');used.add(p);decoded.append(b)
 m,c,p=decoded
 need([row['trainer4a2'],row['trainerAggregate4a4'],row['selectorMirror4c2'],row['referenceRefreshCounter4c4']]==[struct.unpack_from('<H',m,o)[0]for o in (2,4,34,36)],'M source field decode')
 need(row['selectorC7']==c[7]and row['capturedDynamicAPointer']==hex(struct.unpack_from('<I',p,4)[0])and row['capturedDynamicBPointer']==hex(struct.unpack_from('<I',p,8)[0]),'C/P source field decode')
 need(row['referenceRefreshCounter4c4']==row['trainer4a2']==0,'actual boundary values')
need(used==listed and len(audit['retainedBoundarySamples'])==10,'exact provenance coverage no unpinned input')
spec=importlib.util.spec_from_file_location('eg_review_model',D/'refresh_model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
# Source-derived truth tables deliberately include signed-CMP/u16 truncation and row-zero priority edges.
for counter in (0,1,2,3,32767,32768,65534,65535):
 for selector in (0,1,2,255):
  for flag in (0,1,255):
   for height in (0,1,2,2160,65535):
    for row in sorted({0,1,2159,65534,65535,height-1 if height else 0}):
     active=bool(counter and selector and flag);top=active and row==0;bottom=active and row!=0 and row==height-1
     expected=counter
     if active:
      expected=(counter+int(top or bottom))%65536
      if expected>=3:expected=0
     kind='top' if top else 'bottom' if bottom else None
     need(model.snapshot(counter,selector,flag,row,height)==(expected,kind),'source-derived row/counter truth table')
for mirror in (0,1,2,255,256,32768,65535):
 for counter in (0,1,2,3,65535):
  for selector in range(256):
   want=(mirror,counter)if mirror==selector else(selector,1 if selector else 0)
   need(model.synchronize(mirror,counter,selector)==want,'all selector byte values/mirror width')
print(json.dumps({'accepted':True,'checks':checks,'inputPins':36,'sourceInventoryEntries':len(inv['files']),'retainedSamples':10,'targetOperations':0,'modelScope':'stable bounded blocks; no scheduling/copy atomicity/hook qualification'}))
