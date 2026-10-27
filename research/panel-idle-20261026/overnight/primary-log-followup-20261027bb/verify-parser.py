#!/usr/bin/env python3
"""Offline acceptance/regression checks; never calls a target."""
import copy, hashlib, importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'parse-primary-log.py'
if hashlib.sha256(p.read_bytes()).hexdigest()!='054e8606d8e774b4bb5f9ca771a11700da6b5874c10b5337198fe8fbe3bbfb33': raise ValueError('parser pin')
s=importlib.util.spec_from_file_location('parser',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
results=[]
for name,d in [('historical',HERE.parent/'executing-image-identity-20261027e/main-event-log-read-once'),('current',HERE/'capture-once')]:
 raw=(d/'stdout.txt').read_bytes(); record=m.json_object((d/'record.json').read_bytes(),'record')
 m.validate_record(record,raw); outcome,data,timing=m.parse_stdout(raw)
 if (d/'returned-block.bin').read_bytes()!=data: raise ValueError('saved data differs')
 results.append(name+':accepted')
raw=(HERE/'capture-once/stdout.txt').read_bytes();record=m.json_object((HERE/'capture-once/record.json').read_bytes(),'record')
def reject(label,fn):
 try: fn()
 except m.Rejected: results.append(label+':rejected');return
 raise ValueError(label+' unexpectedly accepted')
reject('unknown-line',lambda:m.parse_stdout(raw.replace(b'ACTIVE_READ_BEGIN',b'UNKNOWN\nACTIVE_READ_BEGIN')))
reject('duplicate-json-key',lambda:m.json_object('{"a":1,"a":2}','mutation'))
outcome,_,_=m.parse_stdout(raw)
o=copy.deepcopy(outcome);o['Steps'][2]['Value']=11
reject('short-header',lambda:m.validate_outcome(o))
o=copy.deepcopy(outcome);o['DataSha256']='0'*64
reject('data-hash',lambda:m.validate_outcome(o))
r=copy.deepcopy(record);r['cleanup_stdout']=''
reject('cleanup',lambda:m.validate_record(r,raw))
r=copy.deepcopy(record);r['calls'][0]['command']='changed command'
reject('command-echo',lambda:m.validate_record(r,raw))
print(json.dumps({'checks':results,'target_operations':0},sort_keys=True))
