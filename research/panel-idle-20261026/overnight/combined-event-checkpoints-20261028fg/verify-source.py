#!/usr/bin/env python3
"""Host-only narrow source equivalence and fixed I/O accounting checks."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;E=B/'rtp-quiescent-checkpoints-20261028er';checks=0
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def section(s,a,z):return s[s.index(a):s.index(z,s.index(a))]
e=(E/'Program.cs').read_text();p=(P/'Protocol.cs').read_text()
check(section(e,'    static PairResult ReadPair(','    static PairResult ReadSet(')==section(p,'    static PairResult ReadPair(','    static PairResult ReadSet('),'ReadPair byte identical including pending IN clock rule')
for a,z in [('    static byte[] Header(','    static readonly WindowSpec R'),('    static readonly WindowSpec R','    static readonly WindowSpec[] AllSpecs'),('    interface IOps','    interface IClock')]:check(section(e,a,z)==section(p,a,z).replace('    static readonly WindowSpec Ring = Spec("Ring",0x20200000,15372);\n',''),'fixed inherited block '+a)
e=(E/'NativeBinding.cs').read_text();p=(P/'NativeBinding.cs').read_text();check(e[:e.index('        public NativeResult Bulk')]==p[:p.index('        bool loggerPayloadPending')],'all binding/preflight/claim/release/close prefix exact')
for s in ['Timeout = TimeoutMs','Ep = input ? 0x82u : 0x02u','ioctlTransfer(fd, BulkRequest, ref transfer)','GCHandleType.Pinned']:check(s in p,'native transport invariant '+s)
e=(E/'OnsetKey.cs').read_text();p=(P/'OnsetKey.cs').read_text();check(e[:e.index('    sealed class FakeIntervention')]+ '}\n'==p,'OneLeft/RealKeyOps/FakeKeyOps exact prefix')
e=(E/'ScoreCheckpoints.cs').read_text();p=(P/'ScoreCheckpoints.cs').read_text();check((e[:e.index(' sealed class ScoreFakeOps')]+'}\n').replace('er-quiescent-checkpoints-v1','fg-stockevent-checkpoints-v1')==p,'58B packing exact schema only')
check((P/'wake-check.py').read_bytes()==(B/'reader-wake-checkpoints-20261028fc/wake-check.py').read_bytes(),'FC wake helper exact bytes')
s=(P/'Engine.cs').read_text()
for text in ['CleanupReserveUs=6*PairBudgetUs+MarginUs','KeyJoinReserveUs=7_000_000','WholeBudgetUs=40_000_000','PairBudgetUs+CleanupReserveUs+KeyJoinReserveUs','2*PairBudgetUs+PairBudgetUs+CleanupReserveUs','x.WholeDeadline','phase==ProtocolPhase.ReadyForHeader&&!clockLost&&o.Error==null','phase=ProtocolPhase.ExpectingPayload','ops.Bulk(fd,false,payload,2)','LoggerR(after,0)','Context(m,c)']:check(text in s,'engine invariant '+text)
check('020100000624014702000000'in (P/'Protocol.cs').read_text(),'only logger write header')
check('0x20200000,15372'in(P/'Protocol.cs').read_text(),'fixed full ring')
s=(P/'run-once.py').read_text();check("load_pinned(HERE / 'parse-result.py', PARSER_SHA"in s,'production CLI loads FG parser not ER parser')
print(json.dumps({'sourceChecks':checks,'targetOperations':0},sort_keys=True))
