#!/usr/bin/env python3
"""Host-only source/lineage check; never connects to USB or imports root transport."""
from pathlib import Path
import hashlib,json,re,types,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
checks=0
def need(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
def sha(b):return hashlib.sha256(b).hexdigest()
lineage=json.loads((D/'source-lineage.json').read_bytes())
for name,digest in lineage['parents'].items():need(sha((D/name).read_bytes())==digest,'parent '+name)
old=(D/'../volatile-limit-native-binding-20261028dq/Program.cs').read_text();old=old[old.index('    sealed class RealClock'):old.index('    sealed class FakeClock')]
a='if (input) Need(data.Length == length && (length == 64 || length == 256 || length == 68 || length == 16), "fixed input length");\n            else Need((length == 12 && AllowedHeader(data)) || (length == 2 && data.Length == 2 && (Half(data,0) == 40 || Half(data,0) == 200)), "fixed OUT only");'
b='if (input) Need(data.Length == length && InputLength(length), "fixed input length");\n            else Need(length == 12 && data.Length == 12 && AllowedHeader(data), "fixed read headers only");'
need(old.count(a)==1,'exact narrowing anchor')
expected='using System;\nusing System.IO;\nusing System.Collections.Generic;\nusing System.Diagnostics;\nusing System.Runtime.InteropServices;\nusing System.Threading;\ninternal static partial class Program\n{\n'+old.replace(a,b)+'}\n'
need((D/'NativeBinding.cs').read_text()==expected,'DQ binding plus read-only narrowing')
old=(D/'../volatile-limit-receipt-20261028dl/Program.cs').read_text();old=old[old.index('    [DllImport("libc.so.6",EntryPoint="open"'):old.index('    static int Main(')]
current=(D/'ReceiptMain.cs').read_text();current=current[current.index('    [DllImport'):current.index('    static int Main(')]
need(current==old.replace('/tmp/researcher-limit-dl-','/tmp/researcher-dm-'),'exact exclusive receipt helpers')
dq=(D/'../volatile-limit-native-binding-20261028dq/parse-result.py').read_text();dm=(D/'parse-result.py').read_text();need(dq[dq.index('def binding_checks('):dq.index('def parse_native(')]==dm[dm.index('def binding_checks('):dm.index('def parse_native(')],'exact DQ strict binding validator')
p=types.ModuleType('offline_dm_parser');exec(compile((D/'parse-result.py').read_bytes(),'parse-result.py','exec'),p.__dict__)
s=(D/'Program.cs').read_text();specs=[(name,int(address,16),int(n))for name,address,n in re.findall(r'new\("([^"]+)",(0x[0-9a-f]+),(\d+)\)',s)]
need(specs==p.SPECS and len(specs)==12,'native/parser fixed reads agree')
for name,address,n in specs:
 need(0x47000000<=address and address+n<=0x47020000,'SRAM alias '+name)
 need(n in (16,36,48,68,96,256),'fixed extent '+name)
need('BitConverter.GetBytes(0x101u)' in s and '0x102' not in s,'only read command builder')
need('Write(' not in s and 'public int Writes{get;set;}' in s,'no write operation implementation')
need('new byte[Specs.Length][]' in s and s.index('raws[i]=new byte[Specs[i].Length]')<s.index('p.Preflight()'),'read buffers before preflight')
source=D/'../selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';raw=source.read_bytes();need(sha(raw)==lineage['selected_source_sha256'],'selected firmware source pin')
proof=json.loads((D/'../firmware-display-path-20261028de/record-verification.json').read_bytes())['normal']
for x in proof['ranges']:
 off=int(x['file_offset'],16);need(sha(raw[off:off+x['length']])==x['sha256'],'source range '+x['label'])
print(json.dumps({'schema':'dm-source-verification-v1','checksPassed':checks,'targetOperations':0,'networkOperations':0,'oemExecutions':0,'sameDqNativeClaimBinding':True,'readOnlyAllowlistNarrowed':True,'exactExclusiveReceiptHelpers':True,'fixedReadPairs':12,'selectedSourceSha256':sha(raw),'recordEpochProven':False,'newTargetReadHeadersQualified':False},indent=2))
