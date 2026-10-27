#!/usr/bin/env python3
"""Reuse the reviewed stock bracket once, with fresh host paths only."""
from pathlib import Path
import hashlib,importlib.util,json,sys
HERE=Path(__file__).resolve().parent
B=HERE.parent
SOURCE=B/'stock-rt-lifecycle-trial-20261027av/run-stock-bracket.py'
OLD=B/'sleep-investigation-20261027a/stock-mode2-experiment.py'
LABEL='owner-paired-bh-20261027'
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
need(sha(SOURCE)=='c127fe9d496e7ed27b1a657ca7cfe27db96a4ecedf65fad520859493223b668f','AV source pin')
need(sha(OLD)=='da66959e8024a661a9877f21c796297fa59eb262260a05a147bcb7c41f019898','old orchestration pin')
need(sys.argv[1:] in [[],['--run','--reviewed']],'exact invocation')
if not sys.argv[1:]:
 print(json.dumps({'target_operations':0,'planned_overrides':['HERE','DEST','LABEL'],'collector_and_native_helpers':'unchanged','stock_MODE2_requests_maximum':1}));raise SystemExit(0)
need(not(HERE/'bracket').exists() and not(B/(LABEL+'.onset')).exists(),'fresh trial required')
s=importlib.util.spec_from_file_location('pinned_av_owner_bracket',SOURCE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
need(m.B==B and m.SOURCE==OLD,'fixed source paths')
m.HERE=HERE;m.DEST=HERE/'bracket';m.LABEL=LABEL
(HERE/'owner-action-intent.json').write_text(json.dumps({'question':'Does one stock controller lifecycle recover the owner-observed persistent black panel?','host_overrides':['HERE','DEST','LABEL'],'unchanged':['B','SOURCE','BOOT','PREFLIGHT','collector bytes','native helper bytes','baseline/busy/sentinel/pin/deadline gates'],'max_MODE2_requests':1,'retry':False,'physical_observation':'Separate owner report; inherited collector remains unobserved','post_X':'Withheld pending accepted lifecycle and cleanup review'},indent=2)+'\n')
sys.argv=[str(Path(__file__)),'--run','--reviewed'];m.main()
