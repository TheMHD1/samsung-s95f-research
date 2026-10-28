#!/usr/bin/env python3
"""Build only DM owned source from the exact DQ native USB binding."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;J=D.parent/'volatile-limit-native-binding-20261028dq';b=(J/'Program.cs').read_bytes()
if hashlib.sha256(b).hexdigest()!='c589815120878e619458e98c558a81962b9318a7dd6bd76dd48cdd39eef770a7':raise ValueError('DQ pin')
s=b.decode();real=s[s.index('    sealed class RealClock'):s.index('    sealed class FakeClock')]
old='if (input) Need(data.Length == length && (length == 64 || length == 256 || length == 68 || length == 16), "fixed input length");\n            else Need((length == 12 && AllowedHeader(data)) || (length == 2 && data.Length == 2 && (Half(data,0) == 40 || Half(data,0) == 200)), "fixed OUT only");'
new='if (input) Need(data.Length == length && InputLength(length), "fixed input length");\n            else Need(length == 12 && data.Length == 12 && AllowedHeader(data), "fixed read headers only");'
if real.count(old)!=1:raise ValueError('USB bounded substitution')
real=real.replace(old,new)
(D/'NativeBinding.cs').write_text('using System;\nusing System.IO;\nusing System.Collections.Generic;\nusing System.Diagnostics;\nusing System.Runtime.InteropServices;\nusing System.Threading;\ninternal static partial class Program\n{\n'+real+'}\n')
parents={
 '../volatile-limit-native-binding-20261028dq/Program.cs':'c589815120878e619458e98c558a81962b9318a7dd6bd76dd48cdd39eef770a7',
 '../volatile-limit-native-binding-20261028dq/parse-result.py':'4c79318b8d1e5d6554bfd6bcd84c50674a3955c15a19aef443aba7356a3fe02d',
 '../volatile-limit-native-binding-20261028dq/deployment-manifest.json':'a7a985c9c257f8e939e440bcfe0c48266e1856406790f67f731106406536537f',
 '../volatile-limit-receipt-20261028dl/Program.cs':'d66128ae3faa00f907a3c017799a26f8ad06d783945deee3532f55312d09a307',
 '../volatile-limit-receipt-20261028dl/run-once.py':'eaaacabc19bbf948db3a83391d15a1cf41c0405b1d30d0eea68e27f660316c40',
 '../firmware-display-path-20261028de/record-formatter-appendix.md':'daa211014c488ec6f4ed46f44fdaf17aefaa38ffdd9790cda464c51ca024987c',
 '../firmware-display-path-20261028de/record-verification.json':'52b9fd52453b0d81e92f9029b3ccb1ef2a9344baf196033d7a87ab9ec2656ff3'}
for name,digest in parents.items():
 if hashlib.sha256((D/name).read_bytes()).hexdigest()!=digest:raise ValueError('parent pin '+name)
(D/'source-lineage.json').write_text(json.dumps({'schema':'dm-record-source-lineage-v1','parents':parents,'native_inherited':'DQ RealClock/GuardNativeBinding/RealOps exact except fixed read-header-only OUT and static IN lengths','receipt_inherited':'DL Receipt/PublishReceipt exact except shorter DM stage prefix; fake selftest returns structured JSON directly rather than Console capture','wrapper_inherited':'Pinned DL wrapper mechanically adapted to twelve read pairs, fixed device invocation, DM schemas/prefix/assembly; exact original passive/root transport pins remain manifest-bound','selected_source_sha256':'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','target_operations':0,'new_target_read_headers_qualified':False,'atomic_record_epoch_proven':False},indent=2)+'\n')
