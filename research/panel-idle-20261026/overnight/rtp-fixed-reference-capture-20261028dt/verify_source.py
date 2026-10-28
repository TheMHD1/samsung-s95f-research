#!/usr/bin/env python3
"""Offline lineage and narrow-source-delta verification. No root import."""
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
dm=B/'rtp-record-capture-20261028dm'
need((D/'NativeBinding.cs').read_bytes()==(dm/'NativeBinding.cs').read_bytes(),'byte-identical DQ-derived read-only native binding')
current=(D/'Program.cs').read_text();old=(dm/'Program.cs').read_text()
block=lambda s:s[s.index(' sealed class Controller'):s.index(' static Outcome Run(')]
need(block(current)==block(old),'unchanged transfer clock/phase/pendingIN/pair budget')
receipt=(D/'ReceiptMain.cs').read_text();before=(dm/'ReceiptMain.cs').read_text()
helper=lambda s:s[s.index('    [DllImport'):s.index('    static int Main(')]
need(helper(receipt)==helper(before).replace('researcher-dm-','researcher-dt-'),'unchanged exclusive receipt helper except stage')
parser=(D/'parse-result.py').read_text();binding=lambda s:s[s.index('def binding_checks('):s.index('def decode_fixed(') if 'def decode_fixed(' in s else s.index('def parse_native(')]
need(binding(parser)==binding((dm/'parse-result.py').read_text()),'identical strict binding validator')
p=types.ModuleType('offline_dt_parser');exec(compile(parser,'parse-result.py','exec'),p.__dict__)
specs=[(n,int(a,16),int(z))for n,a,z in re.findall(r'new\("([^"]+)",(0x[0-9a-f]+),(\d+)\)',current)]
need(specs==p.SPECS and len(specs)==14,'14 native/parser windows agree')
oldspec=[(n,int(a,16),int(z))for n,a,z in re.findall(r'new\("([^"]+)",(0x[0-9a-f]+),(\d+)\)',old)]
need([s for s in specs if not s[0].startswith('fixed-')]==oldspec,'all original12 reads/order preserved')
dr=json.loads((B/'rtp-fixed-reference-qualification-20261028dr/qualification.json').read_text())
for n,a,z in specs:
 need(0x47000000<=a<a+z<=0x47020000,'low SRAM '+n)
 need(z in (16,36,48,68,96,104,256),'fixed extent '+n)
 if n.startswith('fixed-'):
  w=next(w for w in dr['windows']if w['kind']==('top' if n=='fixed-top-candidate' else 'bottom')and w['bytes']==104)
  need((a,z)==(w['bus'],w['bytes']),'DR qualified mapping '+n)
need('BitConverter.GetBytes(0x101u)'in current and '0x102'not in current,'read builder only')
need('raws[i]=new byte[Specs[i].Length]'in current and current.index('raws[i]=new byte[Specs[i].Length]')<current.index('p.Preflight()'),'buffers before device access')
need('if(Specs[i].Name=="fixed-top-candidate"){ValidatePacking(raws[1],raws[2]);o.PackingQualified=true;}engine.Read'in current,'packing guard before candidate header')
need('o.Windows.Count==14&&o.PackingQualified'in current,'success packing contract')
print(json.dumps({'schema':'dt-source-verification-v1','accepted':True,'checksPassed':checks,'targetOperations':0,'nativeBindingByteIdenticalDM':True,'controllerByteIdenticalDM':True,'allOriginal12WindowsPreserved':True,'fixedReadPairs':14,'newWindowsDeviceObserved':False,'historicalFixedABranchProven':False},indent=2))
