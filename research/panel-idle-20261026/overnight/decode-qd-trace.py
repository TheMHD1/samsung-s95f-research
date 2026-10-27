#!/usr/bin/env python3
"""Offline I2C transfer decoder; never sends TV traffic or infers physical light.

Only names already matched to exact QDF code are assigned. A successful Linux
I2C transfer is not MCU acceptance or emitted-light proof. Retains partial,
malformed and interrupted transfers instead of silently pairing their bytes.
"""
from pathlib import Path
import argparse,hashlib,json,re
EVENT=re.compile(r'^\s*(?P<task>.+?)-(?P<pid>\d+)\s+\(.*?\)\s+\[\d+\]\s+\S+\s+(?P<time>\d+\.\d+): (?P<event>\w+): (?P<body>.*)$')
MSG=re.compile(r'i2c-(\d+) #(\d+) a=([0-9a-f]+) f=([0-9a-f]+) l=(\d+)(?: \[([0-9a-f-]*)\])?$',re.I)
RESULT=re.compile(r'i2c-(\d+) n=(\d+) ret=(-?\d+)$')
NAMES={0x128:'dimming-level-request',0x180:'off-sensing-control',0x1a0:'EL-sensing-control',0x164:'panel-mute',0x160:'frame-mode',0x150:'VRR-DIA-enable',0x15c:'VRR-control',0x140:'factory-low-power-policy',0xc0:'screen-saver-method',0xc4:'screen-saver-brightness',0xcc:'screen-saver-waiting-policy',0xd0:'screen-saver-slope',0x174:'power-level-query-prepare',0x0d:'power-level-query-result',0x08:'ERR_DET-status'}
def decode(text,source_sha256=None):
 header=re.search(r'entries-in-buffer/entries-written: (\d+)/(\d+)',text)
 retained,written=map(int,header.groups()) if header else (None,None)
 observed_event_lines=sum(EVENT.match(line) is not None for line in text.splitlines())
 parse_errors=[]
 for lineno,line in enumerate(text.splitlines(),1):
  event=EVENT.match(line)
  if not event:continue
  kind,body=event['event'],event['body']
  grammar=RESULT if kind=='i2c_result' else MSG if kind in ('i2c_write','i2c_read','i2c_reply') else None
  if grammar is not None and not grammar.fullmatch(body):parse_errors.append({'line':lineno,'event':kind,'body':body})
 accounting_complete=header is not None and retained==written==observed_event_lines
 result={'source_sha256':source_sha256,'entries':{'retained':retained,'written':written},'observed_event_lines':observed_event_lines,'ring_accounting_complete':accounting_complete,'parse_errors':parse_errors,'semantic_capture_complete':accounting_complete and not parse_errors,'transfers':[],'orphan_results':[],'markers':[],'qualification':'Only observed host I2C bytes/transport results. No physical state or MCU command acceptance inferred. Filters can omit other addresses; partial transfers are not semantic evidence.'}
 pending={}
 def finish(key,why):
  tx=pending.pop(key);tx['close_reason']=why
  ids=sorted(tx['messages'])
  issues=tx['issues']
  n=tx.get('n')
  if n is None:issues.append('missing-transfer-result')
  elif ids!=list(range(n)):issues.append('missing-or-extra-message-index')
  msgs=[tx['messages'][i] for i in ids];tx['messages']=msgs
  for m in msgs:
   if m['direction']=='write' and m.get('write_hex') is None:issues.append('missing-write-payload')
   if m['direction']=='read' and m.get('reply_hex') is None:issues.append('missing-read-reply')
  if not result['ring_accounting_complete']:issues.append('ring-accounting-incomplete')
  if parse_errors:issues.append('capture-has-unparsed-i2c-event')
  tx['structurally_complete']=not issues
  tx['transport_outcome']='not-established'
  if n is not None:tx['transport_outcome']='all-messages-reported-transferred' if tx['ret']==n else 'short-or-failed-transfer'
  if tx['structurally_complete'] and all(m['address']==0x76 for m in msgs) and tx['bus']==5 and msgs and msgs[0].get('write_hex'):
   cmd=bytes.fromhex(msgs[0]['write_hex'])
   shape_ok=len(msgs)==2 and msgs[0]['direction']=='write' and msgs[1]['length']==4 and ((len(cmd)>1 and cmd[1]==0 and msgs[1]['direction']=='write') or (len(cmd)>1 and cmd[1] in (0x80,1) and msgs[1]['direction']=='read'))
   if len(cmd)==6 and cmd[0]==0xf3 and cmd[1] in (0,0x80,1):tx['qd_semantic_shape_valid']=shape_ok
   if len(cmd)==6 and cmd[0]==0xf3 and cmd[1] in (0,0x80,1) and shape_ok:
    selector=int.from_bytes(cmd[2:],'big')
    semantic={'command_hex':cmd.hex(),'selector_hex':hex(selector),'operation':{0:'write',0x80:'read',1:'status-handshake'}[cmd[1]],'name':NAMES.get(selector,'unmapped-QDF-selector')}
    if cmd[1]==1:semantic['name']='command-status-handshake';semantic['status_meaning']='not-decoded-here'
    if len(msgs)==2 and msgs[1]['direction']=='write':
     payload=bytes.fromhex(msgs[1]['write_hex']);semantic['write_payload_hex']=payload.hex()
     if len(payload)==4:semantic['write_payload_u32_be']=int.from_bytes(payload,'big')
    if len(msgs)==2 and msgs[1]['direction']=='read':semantic['read_reply_hex']=msgs[1]['reply_hex']
    tx['qd']=semantic
  result['transfers'].append(tx)
 for lineno,line in enumerate(text.splitlines(),1):
  match=EVENT.match(line)
  if not match:continue
  d=match.groupdict();pid=int(d['pid']);when=float(d['time']);kind=d['event'];body=d['body']
  if kind=='tracing_mark_write':result['markers'].append({'time':when,'pid':pid,'text':body})
  if kind=='i2c_result':
   m=RESULT.fullmatch(body)
   if not m:continue
   bus,n,ret=map(int,m.groups());key=(pid,bus)
   if key not in pending:result['orphan_results'].append({'line':lineno,'time':when,'pid':pid,'bus':bus,'n':n,'ret':ret});continue
   pending[key].update(n=n,ret=ret,end_time=when);finish(key,'result');continue
  if kind not in ('i2c_write','i2c_read','i2c_reply'):continue
  m=MSG.fullmatch(body)
  if not m:continue
  bus,index,addr,flags,length,payload=m.groups();bus=int(bus);index=int(index);addr=int(addr,16);flags=int(flags,16);length=int(length);key=(pid,bus)
  if kind!='i2c_reply' and index==0:
   if key in pending:finish(key,'new-index-zero-before-result')
   pending[key]={'start_line':lineno,'start_time':when,'task':d['task'],'pid':pid,'bus':bus,'messages':{},'issues':[]}
  if key not in pending:
   pending[key]={'start_line':lineno,'start_time':when,'task':d['task'],'pid':pid,'bus':bus,'messages':{},'issues':['capture-begins-mid-transfer']}
  tx=pending[key];raw=payload.replace('-','') if payload is not None else None
  if raw is not None and len(raw)!=length*2:tx['issues'].append('payload-length-mismatch')
  if kind=='i2c_reply':
   target=tx['messages'].get(index)
   if target is None or target['direction']!='read' or target['address']!=addr or target['length']!=length or int(target['flags'],16)!=flags:
    tx['issues'].append('unmatched-read-reply')
   elif target.get('reply_hex') is not None:tx['issues'].append('duplicate-read-reply')
   else:target['reply_hex']=raw
  else:
   if index in tx['messages']:tx['issues'].append('duplicate-message-index')
   tx['messages'][index]={'index':index,'time':when,'address':addr,'flags':hex(flags),'length':length,'direction':'write' if kind=='i2c_write' else 'read'}
   if (flags & 1) != (kind=='i2c_read'):tx['issues'].append('direction-flag-mismatch')
   if kind=='i2c_write':tx['messages'][index]['write_hex']=raw
 for key in list(pending):finish(key,'end-of-capture')
 result['transfers'].sort(key=lambda x:x['start_time'])
 result['focus']=[{'time':t['start_time'],'task':t['task'],'pid':t['pid'],'transport_outcome':t['transport_outcome'],**t['qd']} for t in result['transfers'] if t.get('qd',{}).get('selector_hex') in ('0x164','0x160','0x150','0x15c') and t['qd']['operation']!='status-handshake']
 result['maintenance_focus']=[{'time':t['start_time'],'task':t['task'],'pid':t['pid'],'transport_outcome':t['transport_outcome'],**t['qd']} for t in result['transfers'] if t.get('qd',{}).get('selector_hex') in ('0x180','0x1a0') and t['qd']['operation']!='status-handshake']
 result['dimming_focus']=[{'time':t['start_time'],'task':t['task'],'pid':t['pid'],'transport_outcome':t['transport_outcome'],**t['qd']} for t in result['transfers'] if t.get('qd',{}).get('selector_hex') in ('0x128','0x140','0xc0','0xc4','0xcc','0xd0') and t['qd']['operation']!='status-handshake']
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();raw=a.trace.read_bytes();d=decode(raw.decode('utf-8'),hashlib.sha256(raw).hexdigest());out=a.out or a.trace.with_suffix('.qd.json');out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'out':str(out),'ring_accounting_complete':d['ring_accounting_complete'],'semantic_capture_complete':d['semantic_capture_complete'],'parse_errors':len(d['parse_errors']),'transfers':len(d['transfers']),'partial':sum(not t['structurally_complete'] for t in d['transfers']),'focus':d['focus'],'maintenance_focus':d['maintenance_focus'],'dimming_focus':d['dimming_focus']},indent=2))
