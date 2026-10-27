#!/usr/bin/env python3
"""Offline trace summary. Only observed bytes are decoded; no TV access."""
from pathlib import Path
from collections import Counter
import argparse,json,re
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);a=p.parse_args()
s=a.trace.read_text()
header=re.search(r'entries-in-buffer/entries-written: (\d+)/(\d+)',s)
pattern=re.compile(r'^\s*(?P<task>.+?)-(?P<pid>\d+)\s+\(.*?\)\s+\[\d+\]\s+\S+\s+(?P<time>\d+\.\d+): (?P<event>\w+): (?P<body>.*)$')
rows=[];transactions=[];pending={};counts=Counter();ioctls=Counter()
for line in s.splitlines():
 m=pattern.match(line)
 if not m:continue
 d=m.groupdict();d['time']=float(d['time']);d['pid']=int(d['pid']);counts[d['event']]+=1;rows.append(d)
 if d['event']=='sys_enter':
  v=re.match(r'NR 54 \(([0-9a-f]+), ([0-9a-f]+),',d['body'])
  if v:ioctls[f'fd{int(v[1],16)}:0x{v[2]}']+=1
 if d['event'] in ('i2c_write','i2c_reply'):
  v=re.search(r'i2c-(\d+) #(\d+) a=([0-9a-f]+).*?l=(\d+) \[([0-9a-f-]+)\]',d['body'])
  if not v:continue
  bus,index,addr,length,payload=int(v[1]),int(v[2]),int(v[3],16),int(v[4]),v[5]
  raw=bytes.fromhex(payload.replace('-',''))
  key=(d['pid'],bus,addr)
  if d['event']=='i2c_write' and index==0 and length==6:
   tx={'time':d['time'],'task':d['task'],'pid':d['pid'],'bus':bus,'addr_observed':hex(addr),'command_bytes':payload,'command_kind':'not inferred from packet bits','responses':[]}
   transactions.append(tx);pending[key]=tx
  elif key in pending:
   pending[key]['responses'].append({'event':d['event'],'time':d['time'],'bytes':payload})
result={'trace':str(a.trace),'entries':{'retained':int(header[1]),'written':int(header[2])} if header else None,'time_range':[rows[0]['time'],rows[-1]['time']] if rows else None,'event_counts':dict(counts),'ioctl_counts':dict(ioctls),'i2c_transactions':transactions,'qualification':'No fresh physical-screen confirmation during sleeping-owner capture; no generated I2C requests. Tracepoints observe existing kernel traffic; no emitted-light measurement. Transport-specific direction is not inferred from names alone.'}
out=a.trace.with_suffix('.summary.json');out.write_text(json.dumps(result,indent=2)+'\n');print(out);print(json.dumps({k:v for k,v in result.items() if k!='i2c_transactions'},indent=2))
