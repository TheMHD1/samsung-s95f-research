#!/usr/bin/env python3
"""Produce an explicitly inferred chronology, preserving the raw ring."""
from pathlib import Path
import re,json,hashlib
p=Path(__file__).resolve().parent
b=(p/'main-event-log-read-once/returned-block.bin').read_bytes()
def need(value,why):
 if not value:raise ValueError(why)
need(hashlib.sha256(b).hexdigest()=='6d82903d4abeb366af859c8966345514a50315a14a891ee1370f69fe173b912a','raw payload identity')
rows=list(re.finditer(rb'LOG Buffer Copy: (\d+)\((\d+)\)\n',b))
falls=[(a,c) for a,c in zip(rows,rows[1:]) if int(c.group(1))<int(a.group(1))]
need(len(falls)==1,'single observed counter discontinuity')
last_new,first_old=falls[0];cut=last_new.end();rotated=b[cut:]+b[:cut]
seq=[int(m.group(1)) for m in re.finditer(rb'LOG Buffer Copy: (\d+)',rotated)]
need(seq==list(range(197151,197183)),'consecutive retained copy sequence')
audit=json.loads((p/'state-runtime-audit.json').read_text())
runs={r['run']:r for r in audit['runs']}
log=runs['main-event-log-read-once'];index=runs['main-log-index-read-once']
report={'schema':'main-log-ring-interpretation-v1','raw_sha256':hashlib.sha256(b).hexdigest(),'length':len(b),'all_ascii_printable_or_space':all(v in (9,10,13) or 32<=v<127 for v in b),'copy_records_in_physical_order':len(rows),'physical_order_one_counter_drop':[int(last_new.group(1)),int(first_old.group(1))],'inferred_next_write_offset':hex(cut),'rotation_inferred_from_sequence_not_measured_index':True,'rotation_first_line_may_be_partial':True,'copy_sequence_after_rotation':seq,'index_read_later':{'uptime_delay_seconds':round(index['uptime_before']-log['uptime_after'],2),'package_candidate':index['observed']['packaged_index_candidate'],'stored_candidate':index['observed']['current_stored_index_candidate'],'not_atomic_with_ring':True},'raw_message_presence':{s:s.encode() in b for s in ['RT-P activate!','rtp_act_','LOG eMMMC Data Write','VD Degrad.','deadPool:']},'physical_panel_state_observed':False,'cause_proved':False}
(p/'main-log-chronology-inferred.txt').write_bytes(rotated)
(p/'main-log-interpretation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: retained counter sequence197151..197182; inferred cursor'+hex(cut)+'; no physical/fault inference')
