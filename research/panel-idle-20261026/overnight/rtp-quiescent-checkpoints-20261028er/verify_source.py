#!/usr/bin/env python3
"""Offline ER delta guard; never imports root/TV adapters."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;P=D.parent/'rtp-refresh-dense-checkpoints-20261028em';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
def part(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
need(sha((P/'source-inventory.json').read_bytes())=='57f39a8f4041944d4cb2515b03c25fabedcc6b5de37206d65bbeb23306ee8be2','frozen EM inventory')
for row in json.loads((P/'source-inventory.json').read_text())['files']:
 b=(P/row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'parent '+row['path'])
for n in ('NativeBinding.cs','OnsetKey.cs','NuGet.Config'):need((D/n).read_bytes()==(P/n).read_bytes(),'byte-identical '+n)
old=(P/'Program.cs').read_text();new=(D/'Program.cs').read_text()
for a,b in [('    static readonly WindowSpec R','    readonly record struct Identity'),('    static PairResult ReadPair','    static PairResult ReadSet'),('    static PairResult ReadSet','    static CaptureDto ToDto'),('    // sysfs binary attributes','    sealed class FakeClock')]:need(part(old,a,b)==part(new,a,b),'unchanged '+a.strip())
need(part(old,'        Buffers buffers = new();','            bool stop = false;')==part(new,'        Buffers buffers = new();','            bool stop = false;'),'identical preflight/open/fd/claim/postclaim/clock start')
need(part(old,'                string? afterError','        if (intervention != null)')==part(new,'                string? afterError','        if (intervention != null)'),'identical pacing/catch/release/close')
need('enum RtState { Clean, Faulted, Unexpected, Quiescent }'in new,'oldnibbles retained; Q3')
need('stop == 0 && fault == 0 && gate == 0 && Half(value, 0xc4) == 40'in new,'exact Quiescent at40 only')
for text in ['startState == RtState.Quiescent && cycleIndex == 1','endState == RtState.Quiescent && cycleIndex == 1','bool cleanCycle = startState == RtState.Clean && endState == RtState.Clean','if (cleanCycle) result.CleanCyclesCompleted++; else result.QuiescentCyclesCompleted++;','cycleIndex == 1 && cleanCycle','cleanCycle ? "last-clean" : "last-quiescent"']:
 need(text in new,'semantics '+text)
s=(D/'ScoreCheckpoints.cs').read_text();need('Size=58, Capacity=56'in s,'58x56 preallocated')
need(part(s,'   Need(Count<Capacity','   // Appended source bytes only:')==part((P/'ScoreCheckpoints.cs').read_text(),'   Need(Count<Capacity','   // Appended source bytes only:'),'original34 byte builder unchanged')
for a in ['Array.Copy(e,0xca,raw,at+54,2)','Array.Copy(e,0x68,raw,at+56,2)']:need(a in s,'new existingR tap '+a)
need('MaxCycles = 56'in new and 'DurationUs = 2_000_000'in new and 'PeriodUs = 25_000'in new,'fixed limits')
need((D/'ReceiptMain.cs').read_text()==(P/'ReceiptMain.cs').read_text().replace('researcher-em-','researcher-er-').replace('==46','==79').replace('checkpointTestsPassed=46','checkpointTestsPassed=79'),'same receipt/production entrypoint apart from stage/testcount')
need('Quiescent'not in (D/'NativeBinding.cs').read_text() and 'Quiescent'not in (D/'OnsetKey.cs').read_text(),'no changed binding/key dispatch')
need(sha((D.parent/'selector-origin-20261028ej/source-audit.json').read_bytes())=='c599ac5db30cc09b9117f4ae0dba18771f27bbcc63f9ca3bccfa9c2cb9589563','frozen EJ selector mirror source')
print(json.dumps({'schema':'er-source-validation-v1','checksPassed':checks,'targetOperations':0,'networkOperations':0,'unchangedReadMapTransportBindingKey':True,'nativeProcessAlarmImplemented':False},sort_keys=True))
