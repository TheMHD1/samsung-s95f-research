#!/usr/bin/env python3
"""GH fixed Fault200 Apps cached/public admission support; no input or vendor operation."""
import base64,hashlib,json,re,types
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent;B=HERE.parent
EB=B/'rtp-lane-gate-capture-20261028eb';EB_WRAPPER_SHA='886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8'
EB_PARSER_SHA='e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523'
EB_MANIFEST_SHA='e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11'
BOOT='00000000-0000-4000-8000-000000000000'
MAX_RESPONSE=65536;AGE_NS=1000000000
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def load(path,pin,name):
 raw=path.read_bytes();need(sha(raw)==pin,'pinned source '+name)
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def wrapper():return load(EB/'run-once.py',EB_WRAPPER_SHA,'gh_eb_wrapper')
def stamp(clock):
 t=clock();need(type(t)is int and t>=0,'host monotonic integer');return t
def snapshot_command():
 return ('set -eu\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'+'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\nvconftool get memory/eden/current_tab\nenlightenment_info -topvwins\ncat /proc/uptime\n')
def parse_snapshot(text):
 need(type(text)is str and 0<len(text.encode())<=MAX_RESPONSE and text.endswith('\n'),'bounded complete cached response')
 lines=text.splitlines();need(len(lines)>=4 and lines[0]==BOOT,'snapshot boot')
 uptime=r'[0-9]+\.[0-9]+ [0-9]+\.[0-9]+'
 need(re.fullmatch(uptime,lines[1])is not None and re.fullmatch(uptime,lines[-1])is not None,'boot uptime brackets')
 need(Decimal(lines[-1].split()[0])>=Decimal(lines[1].split()[0]),'uptime ordering')
 tabs=[v for v in lines if v.startswith('memory/eden/current_tab')]
 need(tabs==['memory/eden/current_tab, value = d/apps.tab (String)'],'exactly one canonical Apps row')
 saver=any(v in text for v in ['ScreenSaver.dll','ScreenSaverContent.dll'])
 csfs='/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll'in text
 need(not saver and csfs,'cached Apps+noSaver+CSFS required')
 return {'cachedTab':'d/apps.tab','screensaverWindowsPresent':saver,'csfsWindowPresent':csfs,'boot':BOOT,'uptimeBefore':lines[1],'uptimeAfter':lines[-1],'physicalPictureObserved':False}
def snapshot(adapter,record,record_path,output,label,clock):
 before=stamp(clock);command=snapshot_command();(output/(label+'-command.txt')).write_text(command)
 text=adapter.root(command,record,record_path)
 need(type(text)is str and len(text.encode())<=MAX_RESPONSE,'bounded cached reply');(output/(label+'-response.txt')).write_text(text)
 after=stamp(clock);need(before<=after,'query clock ordering');summary=parse_snapshot(text)
 checkpoint={'schema':'gh-cached-apps-v1','queryBeforeHostMonotonicNs':before,'queryReturnedHostMonotonicNs':after,'responseSha256':sha(text.encode()),'summary':summary,'wrapperUiOperations':0}
 save(output/(label+'-checkpoint.json'),checkpoint);return checkpoint
def dispatch(checkpoint,clock):
 now=stamp(clock);after=checkpoint['queryReturnedHostMonotonicNs'];need(type(after)is int and 0<=now-after<=AGE_NS,'final query return to native submission age')
 checkpoint.update(nativeSubmitHostMonotonicNs=now,hostSubmissionAgeNs=now-after,hostSubmissionAgeBoundNs=AGE_NS)
def identity_checkpoint(adapter,record,record_path,output,identity,marker):
 w=wrapper();command='set -eu\n'+w.metadata_body(identity,marker)
 need(len(command.encode())<=8192,'identity command bound');text=adapter.root(command,record,record_path)
 need(type(text)is str and len(text.encode())<=MAX_RESPONSE,'identity response bound');(output/(marker+'.txt')).write_text(text)
 census=w.parse_metadata(text,marker);save(output/(marker+'.json'),census);return census
def validate_framed(text):
 need(type(text)is str and len(text.encode())<=MAX_RESPONSE,'native response cap')
 pattern=r'BEFORE\n([0-9]+\.[0-9]+ [0-9]+\.[0-9]+)\nHELPER_EXIT\n([0-9]{1,3})\nRECEIPT_BASE64\n([A-Za-z0-9+/=\n]*)NATIVE_STDERR_BASE64\n([A-Za-z0-9+/=\n]*)AFTER\n([0-9]+\.[0-9]+ [0-9]+\.[0-9]+)\n'
 m=re.fullmatch(pattern,text);need(m is not None,'complete unique native framing')
 need(0<=int(m[2])<=255 and Decimal(m[5].split()[0])>=Decimal(m[1].split()[0]),'native exit/uptime')
 for encoded,cap in [(m[3],8192),(m[4],4096)]:
  compact=encoded.replace('\n','');raw=base64.b64decode(compact,validate=True)
  need(base64.b64encode(raw).decode()==compact and len(raw)<=cap,'native blob canonical/cap')
 return True

def call_stdout(c):
 need(type(c)is dict and type(c['command'])is str and type(c['command_bytes'])is int and c['command_bytes']==len(c['command'].encode())<=8192,'recorded command extent')
 need(type(c['transport_exit'])is int and c['transport_exit']==0 and c['host_timeout']is False and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'root transport status/bounds')
 def blob(x):
  need(type(x)is dict and set(x)=={'encoding','data'}and x['encoding']=='base64','transport blob schema')
  raw=base64.b64decode(x['data'],validate=True);need(base64.b64encode(raw).decode()==x['data'],'transport canonical bytes');return raw
 need(blob(c['transport_stderr'])==b'','transport stderr')
 raw=blob(c['transport_stdout']);w=wrapper();need(len(raw)<=MAX_RESPONSE and w.strict_json(raw)==c['response'],'authenticated response bytes')
 response=c['response'];need(response['authenticated']is True and type(response['uid'])is type(response['euid'])is int and response['uid']==response['euid']==0 and response['model']=='QN77S95FAFXZC','root identity')
 rows=response['commands'];need(type(rows)is list and len(rows)==1,'one command response');row=rows[0]
 need(row['command']==c['command']and type(row['exit_code'])is int and row['exit_code']==0 and row['timed_out']is False and row['stderr']=='','root echoed command/status')
 need(type(row['stdout'])is str and len(row['stdout'].encode())<=MAX_RESPONSE and c['started_utc']<=c['finished_utc'],'bounded root stdout/time');return row['stdout']
