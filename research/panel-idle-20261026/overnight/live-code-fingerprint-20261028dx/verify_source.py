#!/usr/bin/env python3
"""Host-only source lineage, fixed-address, sample and inherited mechanics audit."""
from pathlib import Path
import hashlib,json,re,struct,types,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent;M=B/'rtp-record-capture-20261028dm';W=B/'code-alias-qualification-20261028dw'
checks=0
def check(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
sha=lambda b:hashlib.sha256(b).hexdigest()
for n,digest in json.loads((D/'source-lineage.json').read_bytes())['parentFiles'].items():check(sha((M/n).read_bytes())==digest,'DM parent '+n)
for n,digest in json.loads((D/'dw-source-pins.json').read_bytes())['pins'].items():check(sha((W/n).read_bytes())==digest,'DW proof '+n)
check((M/'NativeBinding.cs').read_bytes()==(D/'NativeBinding.cs').read_bytes(),'native binding byte-identical DM')
old=(M/'Program.cs').read_text();new=(D/'Program.cs').read_text()
for start,end in [(' sealed class Controller',' static Outcome Run'),(' static byte[] Header',' sealed class Outcome'),(' readonly record struct Identity',' static readonly Spec[] Specs')]:check(old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)],'inherited exact source '+start)
old_receipt=(M/'ReceiptMain.cs').read_text().replace('researcher-dm-','researcher-dx-').replace('dm-rtp-record','dx-code-fingerprint').replace('fixedReadPairs\\\":12','fixedReadPairs\\\":4')
check(old_receipt==(D/'ReceiptMain.cs').read_text(),'receipt/main only revision/count changes')
for start,end in [('try{long deadline','var engine='),('catch(Exception e){o.Errors.Add(e.GetType().Name','o.Accepted=')]:check(old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)],'unchanged lifecycle '+start)
parser=types.ModuleType('parser');exec(compile((D/'parse-result.py').read_bytes(),'parse-result.py','exec'),parser.__dict__)
plan=json.loads((W/'fixed-read-plan.json').read_bytes());asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();check(sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','DW selected input')
samples=re.search(r'SampleHex=\{([^}]+)\}',(D/'HostTests.cs').read_text()).group(1);samples=json.loads('['+samples+']')
for i,w in enumerate(plan['windows']):
 spec=(w['name'],int(w['busAddress'],16),16);check(parser.SPECS[i]==spec,'fixed parser spec')
 check('new("'+w['name']+'",'+w['busAddress']+',16)'in new,'fixed native spec')
 check(parser.FINGERPRINTS[i]==w['expectedSha256']and '"'+w['expectedSha256']+'"'in new,'fixed expected hashes')
 sample=bytes.fromhex(samples[i]);offset=int(w['fileOffset'],16);check(len(sample)==16 and sample==asset[offset:offset+16]and sha(sample)==w['expectedSha256'],'reviewed FakeOps data only')
 check(0<int(w['linkedVa'],16)and int(w['linkedVa'],16)+16<=0x20000 and spec[1]%4==0,'DW complete range bound')
 check(struct.pack('<III',0x101,spec[1],16).hex()==w['headerLittleEndianHex'],'exact fixed header')
check(len(parser.SPECS)==len(parser.FINGERPRINTS)==len(samples)==4,'four only')
check('"--address"'not in (D/'ReceiptMain.cs').read_text()and '"--execute-set"'not in (D/'ReceiptMain.cs').read_text(),'no address/write action CLI')
old_parser=(M/'parse-result.py').read_text();new_parser=(D/'parse-result.py').read_text();start='def binding_checks(';end='def parse_native('
check(old_parser[old_parser.index(start):old_parser.index(end)]==new_parser[new_parser.index(start):new_parser.index(end)],'independent strict binding validation unchanged')
old_wrapper=(M/'run-once.py').read_text();new_wrapper=(D/'run-once.py').read_text()
for start,end in [('def metadata_body(','def parse_metadata('),('def receipt_envelope(','def execute(')]:
 check(old_wrapper[old_wrapper.index(start):old_wrapper.index(end)]==new_wrapper[new_wrapper.index(start):new_wrapper.index(end)].replace('DXMETA','DMMETA').replace('DXRUN','DMRUN'),'unchanged metadata/envelope '+start)
print(json.dumps({'sourceChecksPassed':checks,'targetOperations':0,'networkOperations':0}))
