#!/usr/bin/env python3
"""Strict offline validator for a proposed HDMI-control binding sample.

This parser performs no acquisition and never opens /proc.  It validates saved
client JSON/text supplied by a caller against the fixed reader contract.
"""
import hashlib
import importlib.util
import json
import math
import re
import datetime
from pathlib import Path

BOOT = '00000000-0000-4000-8000-000000000000'
MODEL = 'QN77S95FAFXZC'
PID, START = 706, 603
MAIN = '/usr/lib/libhdmi-control.so.0.1'
IMPL = '/prd/usr/lib/libhdmi-control-impl-sec.so.0.1'
MAIN_HASH = '067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410'
IMPL_HASH = '5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1'
MAINWORD, IMPLWORD = 1148733441, 4022383920
EXE = '/usr/bin/avocd'
HERE = Path(__file__).resolve().parent
READER = HERE/'read-hdmi-control-binding.py'
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
READER_SHA = '84d60b3d066dd03fb4911e1a233014c70f553ac17dba427883ef8e2d235fa889'
COMMAND_SHA = 'f840067004cb1080f63fa9fbd1a2eb192ce2a739e587f35ceadecaad819a765a'
CLIENT_SHA = '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5'
MAX_SAMPLE_SECONDS = 26.0

def require(ok, detail):
    if not ok: raise ValueError(detail)

def _uptime(line):
    fields=line.split(); require(len(fields)==2,'uptime fields')
    vals=[]
    for value in fields:
        require(re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',value) is not None,'uptime syntax')
        parsed=float(value); require(math.isfinite(parsed),'finite uptime')
        vals.append(parsed)
    return vals

def _utc(value, detail):
    require(isinstance(value,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\+00:00',value) is not None,detail)
    try: parsed=datetime.datetime.fromisoformat(value)
    except ValueError: raise ValueError(detail)
    require(parsed.tzinfo is not None and parsed.utcoffset()==datetime.timedelta(0),detail)
    return parsed

def _maps(lines):
    require(lines,'empty selected maps')
    for line in lines:
        fields=line.split(maxsplit=5); require(len(fields)==6,'maps fields')
        require(re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{8}',fields[0]) is not None,'maps range')
        lo,hi=(int(v,16) for v in fields[0].split('-')); require(0<=lo<hi<=0x100000000 and lo%0x1000==0 and hi%0x1000==0,'maps bounds')
        require(re.fullmatch(r'[r-][w-][x-][ps]',fields[1]) is not None,'maps perms')
        require(re.fullmatch(r'[0-9a-f]{8}',fields[2]) is not None,'maps offset')
        require(re.fullmatch(r'[0-9a-f]{2}:[0-9a-f]{2}',fields[3]) is not None,'maps dev')
        require(fields[4].isdigit(),'maps inode')
    return tuple(lines)

def _covered(rows, address, size, path=None, executable=None):
    require(0<=address and size>0 and address+size<=0x100000000,'coverage bounds')
    for row in rows:
        f=row.split(maxsplit=5); lo,hi=(int(x,16) for x in f[0].split('-'))
        if lo <= address and address+size <= hi and 'r' in f[1] and (path is None or f[5]==path) and (executable is None or ('x' in f[1]) == executable):
            return
    raise ValueError('required mapping coverage')

def _identity(lines):
    require(len(lines)==7,'identity line count')
    require(lines[0]==BOOT,'boot')
    require(lines[1]==EXE,'exe')
    require(lines[2]==f'{PID} {START}','pid/start')
    require(lines[3]==f'{MAIN_HASH}  {MAIN}','main hash')
    require(lines[4]==f'{IMPL_HASH}  {IMPL}','impl hash')
    out=[]; sources=[]
    for line,path in zip(lines[5:],[MAIN,IMPL]):
        f=line.split(maxsplit=3); require(len(f)==4 and f[3]==path,'source identity path')
        require(f[0].isdigit() and f[1].isdigit(),'source identity numbers')
        require(re.fullmatch(r'[0-9a-f]{2}:[0-9a-f]{2}',f[2]) is not None,'source identity device')
        out.append(line)
        dev=int(f[0]); encoded=f'{(dev >> 8) & 0xfff:02x}:{(dev & 0xff) | ((dev >> 12) & 0xfff00):02x}'
        require(encoded==f[2],'source device encoding')
        sources.append((f[2],f[1],path))
    return tuple(out),tuple(sources)

def _take(lines, index, marker):
    require(index < len(lines) and lines[index] == marker,'marker '+marker)
    return index+1

def validate_response(client_stdout, client_stderr, result, intent):
    """Return a compact accepted summary or raise ValueError.

    `client_stdout` is the parsed connector JSON, `client_stderr` its raw
    sidecar, `result` the saved host result dict, and `intent` the saved intent.
    """
    require(hashlib.sha256(READER.read_bytes()).hexdigest()==READER_SHA,'exact reader source hash')
    require(hashlib.sha256(CLIENT.read_bytes()).hexdigest()==CLIENT_SHA,'exact local acquisition client hash')
    spec=importlib.util.spec_from_file_location('exact_binding_reader',READER)
    reader=importlib.util.module_from_spec(spec); spec.loader.exec_module(reader)
    command=reader.module.COMMAND
    require(hashlib.sha256(command.encode()).hexdigest()==COMMAND_SHA,'exact reviewed command hash')
    require(intent.get('command')==command,'exact current reader command')
    require(intent.get('command_sha256')==COMMAND_SHA,'intent command hash')
    require(intent.get('client_sha256')==CLIENT_SHA,'exact acquisition client hash')
    require(intent.get('argv')==['python3',str(CLIENT),'root','--persistent-only','--timeout','25','--command',command],'exact argv')
    require(intent.get('retry') is False and intent.get('physical_state')=='unobserved','intent safeguards')
    require(intent.get('purpose')==reader.__doc__,'intent purpose')
    _utc(intent.get('started_utc'),'started timestamp')
    require(set(intent)=={'command','command_sha256','client_sha256','argv','purpose','retry','physical_state','started_utc'},'intent fields')
    require(client_stdout.get('model')==MODEL and client_stdout.get('host')=='198.51.100.20','model/host')
    require(client_stdout.get('authenticated') is True,'authenticated')
    require(client_stdout.get('uid')==0 and client_stdout.get('euid')==0,'uid/euid')
    require(client_stdout.get('root_persistence')=='host-assisted' and client_stdout.get('global_system_files_unchanged_at_acquisition') is True,'persistence')
    require(set(client_stdout)=={'model','host','authenticated','uid','euid','root_persistence','global_system_files_unchanged_at_acquisition','commands'},'client fields')
    require(result.get('returncode')==0 and result.get('host_timeout') is False,'client result')
    started=_utc(intent['started_utc'],'started timestamp'); finished=_utc(result.get('finished_utc'),'finished timestamp')
    require(finished>=started,'host timestamp order')
    require(set(result)=={'returncode','host_timeout','finished_utc'},'result fields')
    commands=client_stdout.get('commands'); require(isinstance(commands,list) and len(commands)==1,'one command')
    item=commands[0]; require(item.get('command')==command,'command binding')
    require(set(item)=={'command','exit_code','timed_out','stdout','stderr'},'command result fields')
    require(item.get('exit_code')==0 and item.get('timed_out') is False,'remote status')
    require(client_stderr=='','host stderr sidecar')
    lines=item.get('stdout','').splitlines(); i=0
    i=_take(lines,i,'@@ TIME_START'); start_epoch=lines[i]; require(start_epoch.isdigit(),'start epoch'); i+=1; up_start=_uptime(lines[i]); i+=1
    i=_take(lines,i,'@@ ID_START'); ident_start,source_start=_identity(lines[i:i+7]); i+=7
    i=_take(lines,i,'@@ BASES'); base=[int(x) for x in lines[i].split()]; require(len(base)==4 and all(x>=0 for x in base),'bases'); i+=1
    i=_take(lines,i,'@@ MAPS_START'); ms=i
    while i<len(lines) and lines[i] != '@@ VALUES_START': i+=1
    maps_start=_maps(lines[ms:i]);
    for dev,inode,path in source_start:
        rows=[row.split(maxsplit=5) for row in maps_start if row.split(maxsplit=5)[5]==path]
        require(rows and all(row[3:5]==[dev,inode] for row in rows),'source map identity')
    i=_take(lines,i,'@@ VALUES_START')
    values_start=[int(x) for x in lines[i].split()]; require(len(values_start)==5,'values start'); i+=1
    i=_take(lines,i,'@@ VALUES_END'); values_end=[int(x) for x in lines[i].split()]; require(len(values_end)==5,'values end'); i+=1
    require(values_start==values_end,'snapshot repeat')
    flag,table,callback,mainword,implword=values_start
    require(flag==0x100 and table>0 and callback%2==1,'value gates')
    require((mainword,implword)==(MAINWORD,IMPLWORD),'code words')
    main_bias,impl_bias,storage,expected_callback=base
    require(storage==main_bias+0x47e834fc and callback==expected_callback==impl_bias+0x8575,'base binding')
    for path,bias,link_base in ((MAIN,main_bias,0x47e10000),(IMPL,impl_bias,0)):
        zero=[row for row in maps_start if row.split(maxsplit=5)[5]==path and row.split(maxsplit=5)[1]=='r-xp' and row.split(maxsplit=5)[2]=='00000000']
        require(len(zero)==1 and int(zero[0].split(maxsplit=5)[0].split('-')[0],16)-link_base==bias,'unique offset-zero executable map')
    _covered(maps_start,storage,8,MAIN,False); _covered(maps_start,main_bias+0x47e613a4,4,MAIN,True)
    _covered(maps_start,callback-1,4,IMPL,True); _covered(maps_start,table,60)
    i=_take(lines,i,'@@ MAPS_END'); me=i
    while i<len(lines) and lines[i] != '@@ ID_END': i+=1
    maps_end=_maps(lines[me:i]); require(maps_start==maps_end,'maps repeat')
    i=_take(lines,i,'@@ ID_END'); ident_end,source_end=_identity(lines[i:i+7]); require(ident_start==ident_end and source_start==source_end,'identity repeat'); i+=7
    i=_take(lines,i,'@@ TIME_END'); end_epoch=lines[i]; require(end_epoch.isdigit(),'end epoch'); i+=1; up_end=_uptime(lines[i]); i+=1
    wall_delta=int(end_epoch)-int(start_epoch); up_delta=up_end[0]-up_start[0]
    require(0<=wall_delta<=MAX_SAMPLE_SECONDS and 0<=up_delta<=MAX_SAMPLE_SECONDS and up_end[1]>=up_start[1],'finite bounded time order')
    i=_take(lines,i,'@@ COMPLETE'); require(i<len(lines) and lines[i]=='PASS_SAMPLED_BINDING_ONLY','complete'); i+=1
    require(i==len(lines),'trailing stdout')
    err=item.get('stderr','').splitlines(); require(len(err)==30,'ten dd stderr triplets')
    for n in range(0,30,3):
        require(err[n]=='1+0 records in' and err[n+1]=='1+0 records out','dd records')
        match=re.fullmatch(r'4 bytes \(4 B\) copied, ([0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?) s, ([0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?) (B|kB|MB|GB)/s',err[n+2])
        require(match is not None and all(math.isfinite(float(value)) for value in match.groups()[:2]),'dd byte line')
    return {'physical_state':'unobserved','atomic':False,'dd_reads':10,'table':table,'callback':callback,
            'main_bias':base[0],'impl_bias':base[1],'storage':base[2]}
