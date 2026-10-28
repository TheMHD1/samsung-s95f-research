#!/usr/bin/env python3
"""Bounded read-only audit of stock event logger; no helper construction or I/O."""
import base64, hashlib, json, struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
B=HERE.parent
CHECKS=0

def need(ok, why):
 global CHECKS
 CHECKS+=1
 if not ok: raise ValueError(why)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def bl(raw,va):
 a,b=struct.unpack('<HH',raw)
 need(a&0xf800==0xf000 and b&0xd000==0xd000,'BL opcode')
 s=(a>>10)&1;j1=(b>>13)&1;j2=(b>>11)&1
 v=s<<24|(1^j1^s)<<23|(1^j2^s)<<22|(a&0x3ff)<<12|(b&0x7ff)<<1
 return va+4+(v-(1<<25) if v&(1<<24) else v)

def source():
 pins=json.loads((HERE/'input-pins.json').read_bytes())
 for row in pins['files']:
  raw=(B/row['path']).read_bytes()
  need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'input '+row['path'])
 p=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
 need(len(p)==0x500000 and sha(p)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package')
 ranges=[('caller',0x202a,0x203e,'5fe6959316cdb24dd8ababf5d3fc41281a0cab454234ed3199b9e3dfdbb00d67'),('setter',0xc1e0,0xc214,'ef832cb56479311b66ecb2b80545352b3f3c896b02219b4b3c98ac5d1b5fc0d2'),('sink',0x1b8c8,0x1b948,'67c168a05c5abd9fe7c167f6601ff9b895da7e528b8c8f7168a0c4ab3ce64928'),('gatebody',0x1b8d6,0x1b8e2,'b20b04ad37ef14f8879b6892227ba4c282a48932cea1146c08d7f8f1cc3a07f2'),('saveA',0x183d8,0x183f4,'37408a88fcebb46c2aaa3b2744017991fff11aeffc439c4ef7cba9e1f2c97fce'),('restoreA',0x18548,0x18558,'004120a9145865b50a9b99ec8f530a167d66979b6dbe65250c45df858231bf2d'),('saveB',0x1ba54,0x1ba74,'387208d691d801bad88cbfc17ce4f1b8c945436630e42ac99d84ba7f037685a2'),('restoreB',0x1baa6,0x1baba,'3be8b6379a4a7ed495f62188c75b592ce545e4107a99019b6d0f4ceb7aabe678')]
 output=[]
 for name,a,z,digest in ranges:
  need(sha(p[0x40200+a:0x40200+z])==digest,name+' slice')
  output.append(dict(role=name,image=1,addressDomain='linked_VA',address=hex(a),fileOffset=hex(a+0x40200),bytes=z-a,sha256=digest))
 for call,target in [(0x203a,0xc1e0),(0xc1e4,0x38fc),(0xc206,0x1b8c8),(0xc20e,0x1b8c8),(0xc638,0x1b8c8),(0x19aa6,0x1b8c8)]:
  need(bl(p[0x40200+call:0x40204+call],call)==target,'call '+hex(call))
 need(p[0x40200+0xc214:0x40200+0xc220]==b'rtp_act_%d\n\0','event literal')
 need(struct.unpack_from('<I',p,0x40200+0x1b944)[0]==0x20200000,'direct ring literal')
 f=(B/'volatile-logger-qualification-20261027f/reviewed-helper/Program.cs').read_text()
 g=(B/'finite-onset-logger-20261027g/source-checkpoint-v6/managed-usb-secondary-logger-onset-framing/Program.cs').read_text()
 for text in (f,g):
  for token in ['01010000000020200C3C0000','010100000024014740000000','020100000624014702000000','ArmPayload = { 1, 0 }, RestorePayload = { 0, 0 }','RingLength = 15372','WriteUrgentRestore','restore forbidden: protocol phase is not positively header-ready']:
   need(token in text,'historical fixed action '+token)
 need('HoldMs = 3000' in f and 'ArmDeadlineMs = 10000' in f and 'WholeDeadlineMs = 20000' in f,'F timing')
 need('HoldMs = 20000' in g and 'ArmDeadlineMs = 30000' in g and 'WholeDeadlineMs = 45000' in g,'G timing')
 need('> 55000' in g and 'Console.WriteLine(json)' in g,'historical55K stdout boundary')
 # Historical snapshots and native receipt, not a new target execution.
 history=[]
 for label,directory,span,events in [('F','volatile-logger-qualification-20261027f/logger-smoke-once',6,0),('G-V6','finite-onset-logger-20261027g/onset-v6',1756,2)]:
  d=B/directory;j=json.loads((d/'native-outcome.json').read_bytes())
  need(j['Accepted'] is True and j['ProtocolPhase']=='ReadyForHeader' and j['Released'] and j['Closed'],'accepted historical '+label)
  need(j['PreArmGate']==0 and j['ArmedGate']==1 and j['RestoredGate']==0 and j['RestoreVerified'] and not j['LogFlagMayRemainChanged'],'historical gate '+label)
  need(len(j['Steps'])==16 and not j['Errors'],'historical sequence '+label)
  for step in j['Steps']:need(step['Count']==step['Expected'] and step['Errno']==0,'historical exact '+label)
  rings=[base64.b64decode(j[x+'RingBase64'],validate=True) for x in ('Baseline','Post')]
  for raw in rings:need(len(raw)==15372,'ring extent')
  bw,br,bf=struct.unpack_from('<III',rings[0]);pw,pr,pf=struct.unpack_from('<III',rings[1])
  need(0<=bw<=15360 and 0<=pw<=15360 and pw-bw==span,'historical nonwrapping cursor span')
  delta=rings[1][12+bw:12+pw]
  need(delta.count(b'rtp_act_736\n')==events,'historical event count')
  if label=='F':need(delta==b't[10]\n','F exact delta')
  else:
   need(delta.endswith(b'rtp_act_736\n'*2),'V6 event suffix')
   rt=base64.b64decode(j['RestoredRtBase64'],validate=True)
   need([struct.unpack_from('<H',rt,o)[0] for o in (0,6,10,14)]==[1,0,0x1001,0],'V6 restored triplet')
  history.append(dict(label=label,retainedCursorSpanBytes=span,event736Lines=events,baselineHeader=[bw,br,bf],postHeader=[pw,pr,pf],deltaSha256=sha(delta),noUnobservedWholeWrapProven=False))
 # Standard-library models: modulo cursor ambiguity and no restoration after uncertainty.
 def advance(index,count):
  for _ in range(count):index=index%15360+1
  return index
 need(advance(15359,1)==15360 and advance(15360,1)==1,'per-byte wrap index boundary')
 need(advance(1,15360)==advance(1,30720)==1,'one/two whole laps indistinguishable')
 for phase in ('ExpectingReadIn','ExpectingWritePayload','Unknown'):
  need(phase!='ReadyForHeader','restore forbidden in '+phase)
 need((15372*2*4//3 + ((24302+2)//3)*4)>65536,'two rings plus ER receipt exceed root cap even before other blobs')
 return dict(schema='stock-fault-event-logging-options-audit-v1',checks=CHECKS,inputFiles=len(pins['files']),sourceRanges=output,history=history,gate=dict(cpu='0x20012406',bus='0x47012406',bytes=2,original=0,armed=1,restore=0),ring=dict(direct='0x20200000',headerBytes=12,dataBytes=15360,readBytes=15372),event736=dict(perSetterFormatterCalls=2,lineBytes=12,pcTrace=False,liveRegisters=False,exactTimestamp=False),newHelperImplemented=False,targetOperations=0,networkOperations=0)

if __name__=='__main__':print(json.dumps(source(),sort_keys=True,indent=2))
