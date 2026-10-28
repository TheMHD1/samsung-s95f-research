#!/usr/bin/env python3
"""Bounded source/native equivalence; no target module or transport import."""
from pathlib import Path
import hashlib,json,struct,sys,re
P=Path(__file__).resolve().parent;B=P.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
for f in json.loads((P/'input-pins.json').read_text())['files']:
 x=Path(f['path']);need(x.is_file() and x.stat().st_size==f['bytes'] and sha(x.read_bytes())==f['sha256'],'input '+x.name)
asset=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';raw=asset.read_bytes();need(len(raw)==5242880 and sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected source')
images=[raw[0x200:0x40200],raw[0x40200:0x60200]]
sys.path.insert(0,'/tmp/tcon-capstone');from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
def ins(i,a,m,o):
 q=next(md.disasm(images[i][a:a+4],a,count=1));need((q.mnemonic,q.op_str)==(m,o),'instruction '+str(i)+':'+hex(a))
word=lambda i,a:struct.unpack_from('<I',images[i],a)[0]
need(images[0][0x39d4c:0x39d9c]==images[1][0x1bb74:0x1bbc4],'identical mapper bodies')
for a,m,o in [(0x1bb74,'mov','r2, r0'),(0x1bb76,'cbnz','r1, #0x1bb7c'),(0x1bb7c,'cbnz','r2, #0x1bb9c'),(0x1bb7e,'cmp.w','r1, #0x40000'),(0x1bb82,'bhs','#0x1bb8a'),(0x1bb8a,'cmp.w','r1, #0x20000000'),(0x1bb8e,'blo','#0x1bbba'),(0x1bb90,'ldr','r0, [pc, #0x2c]'),(0x1bb92,'cmp','r1, r0'),(0x1bb94,'bhs','#0x1bbba'),(0x1bb96,'add.w','r0, r1, #0x25000000')]:ins(1,a,m,o)
need(word(1,0x1bbc0)==word(0,0x39d98)==0x20020000,'strict source SRAM upper boundary')
getters=[(0xe670,0xe674,0x2000f0e0),(0xe678,0xe67c,0x2000ff14),(0xe76c,0xe770,0x200158a8)]
for site,literal,pointer in getters:
 ins(0,site,'ldr','r0, [pc, #0]');ins(0,site+2,'bx','lr');need(word(0,literal)==pointer,'object pointer literal')
windows=[('AP',0x2000f0e0,20),('AP-EXCO-data',0x2000ff14,12),('AP-EXCO-context',0x200158a8+0x7c,4)]
proposals=[]
for name,cpu,n in windows:
 need(0x20000000<=cpu<cpu+n<=0x20020000,'complete CPU SRAM interval')
 bus=cpu+0x25000000;need(0x45000000<=bus<bus+n<=0x45020000,'complete source bus SRAM interval')
 need(bus%4==0 and n%4==0,'fixed aligned read')
 proposals.append({'name':name,'cpuAddress':hex(cpu),'sourceBusAddress':hex(bus),'bytes':n,'header':struct.pack('<III',0x101,bus,n).hex(),'exactIntervalPreviouslyLiveQualified':False})
for i,a,m,o in [(0,0x2b76c,'add.w','r5, r0, #0x10'),(0,0x2b776,'strh','r0, [r5]'),(0,0x14972,'strh','r0, [r6, #8]'),(0,0xb6c4,'movw','r1, #0x1234'),(0,0xb6ce,'movw','r1, #0xabcd'),(0,0xb6f8,'b','#0xb6dc')]:ins(i,a,m,o)
old=B/'rtp-lane-gate-capture-20261028eb';need((P/'NativeBinding.cs').read_bytes()==(old/'NativeBinding.cs').read_bytes(),'byte-identical native binding')
for token,tail in [(' sealed class Controller {',' static Outcome Run(')]:
 new=(P/'Program.cs').read_text();prior=(old/'Program.cs').read_text();need(new.split(token)[1].split(tail)[0]==prior.split(token)[1].split(tail)[0],'unchanged transfer/clock/pending-IN engine')
need('ValidateLaneContext' not in new and '0x102' not in new,'no unrelated lane/profile guards or writes')
need(new.count('new("')==5,'five fixed spec entries')
receipt=(P/'ReceiptMain.cs').read_text();need(receipt==(old/'ReceiptMain.cs').read_text().replace('researcher-eb-','researcher-ha-').replace('eb-rtp-lane-gate-dry-v1','ha-ap-fault-witness-dry-v1').replace('fixedReadPairs\\\":16','fixedReadPairs\\\":5'),'receipt logic only prefix/family/count delta')
spans=[]
for i,a,n in [(0,0xe670,16),(0,0xe76c,8),(0,0x39d4c,80),(1,0x1bb74,80),(0,0xb6c0,0x3a),(0,0x2b764,0x16),(0,0x14970,0x1a),(0,0x2fed4,0x24)]:spans.append({'image':i,'va':hex(a),'fileOffset':hex(a+[0x200,0x40200][i]),'bytes':n,'sha256':sha(images[i][a:a+n])})
print(json.dumps({'schema':'ha-source-qualification-v1','checks':checks,'status':'PASS_SOURCE_ONLY_PROSPECTIVE_AP_READS','sourceSpans':spans,'newReadWindows':proposals,'rootBrackets':{'address':'0x47012400','bytesEach':256,'count':2},'fixedHeaders':5,'fixedBulks':10,'expectedInputBytes':548,'writes':0,'targetOperations':0,'currentPcProven':False,'externalKernelELReasonIdentityProven':False},indent=2,sort_keys=True))
