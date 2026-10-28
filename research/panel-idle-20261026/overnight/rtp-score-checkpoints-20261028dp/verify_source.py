#!/usr/bin/env python3
"""Host-only DP source delta and lineage proof; no root transport import."""
from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;F=D.parent/'firmware-rtp-producer-20261028df/capture';Q=D.parent/'volatile-limit-native-binding-20261028dq';M=D.parent/'rtp-record-capture-20261028dm';sha=lambda b:hashlib.sha256(b).hexdigest();checks=0
def need(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
parents=json.loads((D/'parent-pins.json').read_text())
for name,digest in parents.items():need(sha((F/name).read_bytes())==digest,'DF pin '+name)
q=(Q/'Program.cs').read_bytes();need(sha(q)=='c589815120878e619458e98c558a81962b9318a7dd6bd76dd48cdd39eef770a7','frozen DQ native')
text=q.decode();section=text[text.index('    sealed class RealClock'):text.index('    sealed class FakeClock')]
a='if (input) Need(data.Length == length && (length == 64 || length == 256 || length == 68 || length == 16), "fixed input length");\n            else Need((length == 12 && AllowedHeader(data)) || (length == 2 && data.Length == 2 && (Half(data,0) == 40 || Half(data,0) == 200)), "fixed OUT only");'
b='if (input) Need(data.Length == 256 && IsInputLength(length), "fixed input length");\n            else Need(length == 12 && data.Length == 12 && FindHeader(data) != null, "fixed read headers only");'
need(section.count(a)==1,'DQ USB adapter anchor');expected='using System;\nusing System.IO;\nusing System.Collections.Generic;\nusing System.Diagnostics;\nusing System.Runtime.InteropServices;\nusing System.Threading;\ninternal static partial class Program\n{\n'+section.replace(a,b)+'}\n';need((D/'NativeBinding.cs').read_text()==expected,'exact DQ guards/ownership with DP read-only adapter')
old=(F/'Program.cs').read_text();new=(D/'Program.cs').read_text()
def part(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
for name,a,b in [('fixed_windows','    static readonly WindowSpec R','    readonly record struct Identity'),('ReadPair','    static PairResult ReadPair','    static PairResult ReadSet'),('ReadSet','    static PairResult ReadSet','    static CaptureDto ToDto')]:need(part(old,a,b)==part(new,a,b),'unchanged '+name)
a=part(old,'    static Outcome Run','    // sysfs binary attributes');b=part(new,'    static Outcome Run','    // sysfs binary attributes')
a=a.replace('Identity id = ops.Preflight();','Identity id = ops.Preflight();result.Device=id.Device;').replace('Need(ops.Preflight() == id, "USB identity changed");','ops.Revalidate(id);').replace('result.Claimed = true; result.Released = false;','result.Claimed = true; result.Released = false;ops.Revalidate(id);result.BindingQualified=true;').replace('                RtState endState = ClassifyRt(buffers.Current.Windows[7].Buffer);','                result.ScoreCheckpoints.Add(buffers.Current, result.StartUs!.Value);\n                RtState endState = ClassifyRt(buffers.Current.Windows[7].Buffer);').replace('        result.ProtocolPhase = phase.ToString();','        if(!result.BindingQualified&&result.HeadersSent==0)result.BindingChecks=new List<BindingCheck>(ops.BindingChecks);\n        result.ProtocolPhase = phase.ToString();')
need(a==b,'Run changes limited to Device/binding and completed-cycle checkpoint/audit')
need((D/'OnsetKey.cs').read_bytes()==(F/'OnsetKey.cs').read_bytes(),'oneLeft implementation byte-identical')
a=(M/'ReceiptMain.cs').read_text();b=(D/'ReceiptMain.cs').read_text();need(part(a,'    [DllImport','    static int Main(')==part(b,'    [DllImport','    static bool QualifiedBindingReady').replace('/tmp/researcher-dp-','/tmp/researcher-dm-'),'exclusive receipt helpers exact DM')
s=(D/'ScoreCheckpoints.cs').read_text();need('Size=34, Capacity=80' in s and 'readonly byte[] raw=new byte[Size*Capacity]' in s,'preallocated bounded raw storage')
need('Array.Copy(h,4,raw,at+6,4)'in s and 'Array.Copy(h,28,raw,at+10,2)'in s and 'Array.Copy(h,40,raw,at+12,8)'in s and 'Array.Copy(n,0,raw,at+20,4)'in s and 'Array.Copy(c.Windows[1].Buffer,42,raw,at+32,2)'in s,'exact selected H/N/M source byte slices')
need('c.Transfers[10].BeforeUs' in s and 'c.Transfers[11].AfterUs'in s and 'c.Transfers[0].BeforeUs'not in s,'H fullpair only, no invented compact RT timing')
need(new.index('result.BindingQualified=true')<new.index('string? startError = null'),'binding metadata precedes observation clock')
need('UnsafeRelaxedJsonEscaping'in new and 'JsonSerializer.Serialize(value))>128' in new,'fixed Base64 size and serialized error limit')
lineage={'schema':'dp-source-lineage-v1','target_operations':0,'df_parent_files':parents,'dq_native_sha256':sha(q),'dq_manifest_sha256':sha((Q/'deployment-manifest.json').read_bytes()),'dm_receipt_source_sha256':sha((M/'ReceiptMain.cs').read_bytes()),'dm_wrapper_source_sha256':'805bde0cac28e7b586a75978e899d7daa1cf4fd5509e50744208f714c6d5d203','selected_controller_source_sha256':'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','readPairReadSetOneLeftUnchanged':True,'RunDelta':'Device; DQ cached revalidate pre/postclaim beforeclock; compact completedcycle record; preheader-refusal-only audit','errorDelta':'firsterror type/prefix capped128serializedJSONbytes; no retry/phase change','nativeReceipt':'private exclusive0600 JSON; stdout opaque; no fourth blob','live_DP_execution_observed':False}
# This tool emits evidence only; the caller saves it without modifying source.
print(json.dumps({'schema':'dp-source-verification-v1','checksPassed':checks,'targetOperations':0,'networkOperations':0,'oemExecutions':0,'lineage':lineage},indent=2))
