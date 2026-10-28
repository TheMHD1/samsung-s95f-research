#!/usr/bin/env python3
"""Host-only mechanical receipt-wrapper adaptation; does not load root transport."""
from pathlib import Path
import hashlib,re
D=Path(__file__).resolve().parent;P=D.parent/'rtp-record-capture-20261028dm/run-once.py'
raw=P.read_bytes()
if hashlib.sha256(raw).hexdigest()!='805bde0cac28e7b586a75978e899d7daa1cf4fd5509e50744208f714c6d5d203':raise ValueError('frozen DM wrapper pin')
s=raw.decode().replace('dm-rtp-record','dp-score-checkpoint').replace('researcher-dm-','researcher-dp-').replace("ASSEMBLY = 'RecordCapture'","ASSEMBLY = 'ScoreCheckpoints'")
s=s.replace('DMMETA','DPMETA').replace('DMRUN','DPRUN')
s=re.sub(r"CHECKPOINT_SHA = '[^']+'","CHECKPOINT_SHA = 'CHECKPOINT_PENDING'",s)
s=re.sub(r"PARSER_SHA = '[^']+'","PARSER_SHA = 'PARSER_PENDING'",s)
s=s.replace("['selfTestsPassed','targetOperations']","['selfTestsPassed','keyTestsPassed','checkpointTestsPassed','targetOperations']")
s=s.replace("test=={'selfTestsPassed':485,'targetOperations':0} and set(test)=={'selfTestsPassed','targetOperations'}","test=={'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':44,'targetOperations':0} and set(test)=={'selfTestsPassed','keyTestsPassed','checkpointTestsPassed','targetOperations'}")
s=s.replace("native_raw=run('native');native,raw_files,interpretation=parser.parse_native(native_raw.decode('utf8'));save(output/'interpretation.json',interpretation)","native_raw=run('native');native,captures,raw_files,gc,interpretation=parser.parse_native(native_raw.decode('utf8'));need(gc==[] and interpretation['trialQualified'],'exclusive qualified synchronized capture');save(output/'interpretation.json',interpretation)")
s=s.replace("r'(start-R|M|C|start-N|D|X|Y|RGB|B|Diff|end-N|end-R)\\.bin'","r'(score-checkpoints|retained-[0-9]{2}-[a-z_]+-cycle[0-9]{3}-[0-9]{2}-(R|M|C|P|N|H|L))\\.bin'")
s=s.replace("'accepted_fixed_read_only_record_capture'","'accepted_read_only_score_checkpoints_with_one_Left'")
s=s.replace("'operation':'fixed_read_only_record_capture','headersSent':12,'bulkTransfers':24","'operation':'read_only_score_checkpoints_with_one_Left','headersSent':native['headersSent'],'bulkTransfers':native['bulkTransfers'],'scoreCheckpointCount':native['scoreCheckpoints']['count'],'trialQualified':interpretation['trialQualified'],'keyCausalityEstablished':False")
s=s.replace("'nativeDurationUs': 40000000, 'writes': 0","'nativeDurationUs': 20000000, 'writes': 0, 'nativeUiWorkflow': 'one_Left_after_first_full_clean_cycle'")
(D/'run-once.py').write_text(s)
(D/'wrapper-parent-sha256.txt').write_text(hashlib.sha256(P.read_bytes()).hexdigest()+'\n')
