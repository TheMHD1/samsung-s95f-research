"""One-time scoped input inventory constructor; refuses to overwrite a freeze."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;B=H.parent
specs={
'autonomous-fault-harness-20261028dh/initialize-baseline.py':['maximum_stock_mode2_requests','gates.apps_gate(out)'],
'autonomous-fault-harness-20261028dh/run-deadline-mode2.py':["manifest['operation'] == 41 and manifest['mode'] == 2 and manifest['deadline_seconds'] == 12",'parsed = parse_receipt',"'classification': parsed['classification']","'helper_exit': rc, 'cleanup_confirmed': True, 'request_count': 1"],
'autonomous-fault-harness-20261028dh/deadline-mode2/Program.cs':['uint previousAlarm = alarm(12);','FileMode.CreateNew'],
'autonomous-fault-harness-20261028dh/deadline-mode2/build-manifest.json':[],
'recovery-quickpath-20261027bv/recover.py':['cached_current_tab','def public_gate'],
'managed-tcon-power-cycle-once/run-power-cycle-once.py':['"classification": "kernel_return_zero_only"'],
'ui-navigation-20261027br/navigate.py':[],
'volatile-limit-trial-20261028dk/prepare-score-header-v2.py':['for index in range(10):','for index in range(2):',"nav.one_key('wake'"],
'autonomous-fault-harness-20261028dh/prepare-onset.py':['@@ USB_LIFECYCLE','wrapper.metadata_body'],
'volatile-limit-trial-20261028dk/prepare-current-readiness.py':["'dp-score-checkpoint-readiness-decision-v1'",'evidence changed after decision'],
'rtp-lane-gate-trial-20261028ed/prepare-readiness.py':["'eb-rtp-lane-gate-readiness-decision-v1'","'endpointQueueProof': False"],
'rtp-score-checkpoints-20261028dp/Program.cs':['public int MaxCycles = 80;','public long DurationUs = 20_000_000;','An accepted header creates a pending IN.','if (pair != PairResult.Complete) return pair;','result.CleanCyclesCompleted == 1','intervention.Finish();','phase == ProtocolPhase.ReadyForHeader && result.Released && result.Closed'],
'rtp-score-checkpoints-20261028dp/ReceiptMain.cs':['static int Main(string[] args)','outcome.Intervention.Completed','FileStream Receipt(string name)'],
'rtp-score-checkpoints-20261028dp/OnsetKey.cs':['Left'],
'rtp-score-checkpoints-20261028dp/NativeBinding.cs':[],
'rtp-score-checkpoints-20261028dp/ScoreCheckpoints.cs':[],
'rtp-score-checkpoints-20261028dp/parse-result.py':['startAlternateThreshold',"'everyComparatorCallObserved':False"],
'rtp-score-checkpoints-20261028dp/parent-synchronized-parser.py':['full clean cycle-one trigger baseline','keyWithinObservedWindow','EndUs includes the worker join'],
'rtp-score-checkpoints-20261028dp/transport-parser.py':[],
'rtp-score-checkpoints-20261028dp/run-once.py':['/tmp/researcher-dp-',"target_operations_status='inflight_or_unknown'","test_raw=run('selftest')","'cleanup':'STAGE_ABSENT'","'automaticRestore':False"],
'rtp-score-checkpoints-20261028dp/deployment-manifest.json':[],
'rtp-lane-gate-capture-20261028eb/Program.cs':['if(before=="ReadyForHeader")throw;','o.ProtocolPhase="Unknown";NativeResult n;','Need(n.Value==b.Length,"short/failed "+name);','Transfer(s.Name+"-data",true,raw,"ReadyForHeader")','o.Windows.Count==16'],
'rtp-lane-gate-capture-20261028eb/NativeBinding.cs':[],
'rtp-lane-gate-capture-20261028eb/parse-result.py':["[('headersSent',16),('bulkTransfers',32)",'len(rows)==3',"struct.unpack('<68H'","'actualComparatorCallProven':False"],
'rtp-lane-gate-capture-20261028eb/run-once.py':['eb-rtp-lane-gate-readiness-decision-v1','native_invocations=1','BEFORE_INVOKE_READY',"tag+'.receipt.json'"],
'rtp-lane-gate-capture-20261028eb/deployment-manifest.json':[],
'rtp-lane-table-writers-20261028ec/training-gate-correction.json':[],
'rtp-lane-table-writers-20261028ec/README.md':[],
'controller-scratch-rollback-20261028dz/README.md':[],
}
rows=[]
for name,anchors in specs.items():
 raw=(B/name).read_bytes();text=raw.decode();stored=[]
 for snippet in anchors:
  if snippet not in text:raise ValueError((name,snippet))
  stored.append({'label':snippet[:100],'snippet':snippet,'line':text[:text.index(snippet)].count('\n')+1})
 rows.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'anchors':stored})
with (H/'input-provenance.json').open('x') as out:
 json.dump({'schema':'ef-source-inputs-v1','pathBase':'overnight','files':rows,'liveAcquisition':False},out,indent=2);out.write('\n')
