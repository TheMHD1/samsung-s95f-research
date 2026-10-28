#!/usr/bin/env python3
"""Bounded EB lineage/source equality checks, no root import or device access."""
import hashlib,json,re,types
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent;checks=0
def need(ok,msg):
 global checks
 checks+=1
 if not ok:raise ValueError(msg)
sha=lambda b:hashlib.sha256(b).hexdigest()
lineage=json.loads((D/'source-lineage.json').read_text())
for name,digest in lineage['parents'].items():need(sha((D/name).read_bytes())==digest,'parent pin '+name)
dt=B/'rtp-fixed-reference-capture-20261028dt'
need((D/'NativeBinding.cs').read_bytes()==(dt/'NativeBinding.cs').read_bytes(),'unchanged native binding')
current=(D/'Program.cs').read_text();old=(dt/'Program.cs').read_text()
block=lambda s:s[s.index(' sealed class Controller'):s.index(' static Outcome Run(')]
need(block(current)==block(old),'unchanged controller transfer/phase/clock/pair budget')
receipt=(D/'ReceiptMain.cs').read_text();before=(dt/'ReceiptMain.cs').read_text()
helper=lambda s:s[s.index('    [DllImport'):s.index('    static int Main(')]
need(helper(receipt)==helper(before).replace('researcher-dt-','researcher-eb-'),'exclusive receipt helper unchanged except prefix')
need((D/'ReferenceModel.cs').read_bytes()==(dt/'ReferenceModel.cs').read_bytes(),'unchanged fixed-reference decoder/model')
parser=(D/'parse-result.py').read_text()
binding=lambda s:s[s.index('def binding_checks('):s.index('def decode_fixed(')]
need(binding(parser)==binding((dt/'parse-result.py').read_text()),'unchanged strict binding parser')
p=types.ModuleType('eb_parser');exec(compile(parser,'parse-result.py','exec'),p.__dict__)
specs=lambda s:[(n,int(a,16),int(z))for n,a,z in re.findall(r'new\("([^"]+)",(0x[0-9a-f]+),(\d+)\)',s)]
now=specs(current);prior=specs(old)
need(now==p.SPECS and len(now)==16,'16 native/parser windows agree')
need([s for s in now if not s[0].endswith('lane-gate')]==prior,'all14 DT windows in unchanged order')
planpath=B/'rtp-lane-gate-qualification-20261028ea/fixed-read-plan.json'
need(sha(planpath.read_bytes())=='35cf50b7794d859629c7dd526c455af2756585d0b7269f5d071fa5f0f5d76878','frozen EA readplan')
plan=json.loads(planpath.read_bytes())
for name,address,length in now:
 need(0x47000000<=address<address+length<=0x47020000,'complete SRAM interval '+name)
 need(length in (16,36,48,68,96,104,136,256),'fixed extent '+name)
for spec,w in zip(now[10:12],plan['windows']):
 need(spec[1:]==(int(w['busAddress'],16),w['bytes']),'EA complete gate read interval')
 need((0x101).to_bytes(4,'little').hex()+spec[1].to_bytes(4,'little').hex()+spec[2].to_bytes(4,'little').hex()==w['headerLittleEndianHex'],'EA exact header')
need(now[10][0]=='primary-lane-gate' and now[11][0]=='secondary-lane-gate','first new header')
need('if(Specs[i].Name=="primary-lane-gate"){ValidateLaneContext(raws[0],raws[1],raws[2]);o.PackingQualified=true;o.LaneGateContextQualified=true;}engine.Read' in current,'guard before first new gate/reference header')
model=(D/'LaneGateModel.cs').read_text()
need('ValidatePacking(m,c)'in model and 'BitConverter.ToUInt16(r,16)<6'in model,'root/geometry and ordinary-mode guard')
exitproof=json.loads((D/'early-exit-source.json').read_bytes())
asset=(D/exitproof['sourceRelativePath']).read_bytes()
need(sha(asset)==exitproof['sourceSha256']=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package early-exit source')
for row in exitproof['ranges']:
 offset=int(row['fileOffset'],16);need(sha(asset[offset:offset+row['bytes']])==row['sha256'],'exact comparator exit range')
 need([(i['mnemonic'],i['operands'])for i in row['instructions']]==[('bl','#0xbbbc'),('cbnz','r0, #'+hex(int(row['linkedVa'],16)+8)),('b','#0xbfac')],'conditional return0 exits loop')
need('o.Windows.Count==16&&o.PackingQualified&&o.LaneGateContextQualified'in current,'success requires complete qualified capture')
need('BitConverter.GetBytes(0x101u)'in current and '0x102'not in current,'only read headers')
need('raws[i]=new byte[Specs[i].Length]'in current and current.index('raws[i]=new byte[Specs[i].Length]')<current.index('p.Preflight()'),'preallocate before device open')
print(json.dumps({'schema':'eb-source-verification-v1','accepted':True,'checksPassed':checks,'targetOperations':0,'nativeBindingByteIdenticalDT':True,'controllerByteIdenticalDT':True,'allOriginal14WindowsPreserved':True,'fixedReadPairs':16,'historicalGateExecutionProven':False},indent=2))
