#!/usr/bin/env python3
"""One-shot duty-read runner, dry by default; target mode requires review."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, uuid
from pathlib import Path
H=Path(__file__).resolve().parent; M=H/'build-manifest.json'; RM=H/'runner-manifest.json'
N=('ManagedTconDutyRead.deps.json','ManagedTconDutyRead.dll','ManagedTconDutyRead.runtimeconfig.json')
S=H.parent/'managed-tcon-status-read'/'run-status-read.py'
STATUS_RUNNER_SHA='7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a'
ACCESS_SHA='3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5'
BUILD_SHA='2474d06b231e328cb6e85a13163dc5594dce8e2a4114e4206166dff874840a35'
ABI_SHA='52b1be2e269edc353ffa3f290305067c3c720a3ae000526e08f59d2bbe412172'
class E(ValueError): pass
def q(v,m):
 if not v: raise E(m)
def dg(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def mod():
 q(dg(S)==STATUS_RUNNER_SHA,'status runner changed before import')
 sp=importlib.util.spec_from_file_location('status',S); x=importlib.util.module_from_spec(sp); sp.loader.exec_module(x)
 q(dg(x.ACCESS)==ACCESS_SHA,'access client changed')
 x.REMOTE_NAMES=N
 return x
def contract():
 q(dg(M)==BUILD_SHA,'immutable build manifest pin')
 q(json.loads(RM.read_text()).get('build_manifest_sha256')==dg(M),'runner manifest reference')
 m=json.loads(M.read_text()); q(m.get('schema')=='managed-tcon-duty-read-build-v1','schema'); f=m['files']; out={}
 for n in N:
  k='bin/Release/net6.0/'+n; b=(H/k).read_bytes(); q(hashlib.sha256(b).hexdigest()==f.get(k),'payload '+n); out[n]=b
 for name,expected in f.items():
  q(dg(H/name)==expected,'build source mismatch '+name)
 for item in m['provenance'].values():
  q(dg(H.parents[1]/item['path'])==item['sha256'],'provenance mismatch')
 return m,out
def parse(t,pid):
 a=t.splitlines(); q(a[:1]==['QD_TCON_DUTY_READ_V1'] and a[-1:]==['READ_COMPLETE'],'bounds'); x=[z for z in a if '=' in z]; q(all(z.count('=')==1 for z in x),'shape'); d=dict(z.split('=',1) for z in x)
 q([z for z in a if '=' not in z]==['QD_TCON_DUTY_READ_V1','READ_COMPLETE'],'unexpected bare line')
 q(re.fullmatch(r'[0-9]+',d.get('OPEN_RETURN','')) is not None,'device open failed')
 need={'ARCH','PTR_BYTES','STRUCT_BYTES','ENDIAN_LITTLE','OPERATION_OFFSET','OUTPUT_OFFSET','COMMAND_HIGH_OFFSET','COMMAND_LOW_OFFSET','ARGUMENT_COUNT','UID','EUID','PID_LIBC','PID_SYSCALL','DEVICE','OPEN_FLAGS','IOCTL_REQUEST','COMMAND_U64','WIRE_REQUEST_HEX','EXPECTED_RESPONSE_BYTES','PAYLOAD_BEFORE','OPEN_RETURN','OPEN_ERRNO','IOCTL_RETURN','IOCTL_ERRNO','PAYLOAD_AFTER','CLOSE_RETURN','CLOSE_ERRNO','CLASSIFICATION','RESULT_HEX','RESULT_U32','PHYSICAL_BRIGHTNESS_INFERRED','PACKAGED_RANGE_0_1023','PROFILE_RANGE_CLASSIFICATION'}; q(set(d)==need and len(x)==len(need),'unknown/duplicate field')
 fixed={'ARCH':'Arm','PTR_BYTES':'4','STRUCT_BYTES':'16','ENDIAN_LITTLE':'1','OPERATION_OFFSET':'0','OUTPUT_OFFSET':'4','COMMAND_HIGH_OFFSET':'8','COMMAND_LOW_OFFSET':'12','ARGUMENT_COUNT':'0','UID':'0','EUID':'0','PID_LIBC':str(pid),'PID_SYSCALL':str(pid),'DEVICE':'/dev/tztv_tcon','OPEN_FLAGS':'0x80002','IOCTL_REQUEST':'0xc010749f','COMMAND_U64':'0x0000f30000000128','WIRE_REQUEST_HEX':'f30000000128','EXPECTED_RESPONSE_BYTES':'4','PAYLOAD_BEFORE':'00000013,a55a5aa5,0000f300,00000128','OPEN_ERRNO':'0','IOCTL_RETURN':'0','IOCTL_ERRNO':'0','CLOSE_RETURN':'0','CLOSE_ERRNO':'0','CLASSIFICATION':'kernel_output_written','PHYSICAL_BRIGHTNESS_INFERRED':'0','PACKAGED_RANGE_0_1023':'1','PROFILE_RANGE_CLASSIFICATION':'within_packaged_low10_range'}; q(all(d[k]==v for k,v in fixed.items()),'fixed schema')
 z=re.fullmatch(r'00000013,([0-9a-f]{8}),0000f300,00000128',d['PAYLOAD_AFTER']); q(z and z.group(1)!='a55a5aa5','envelope'); v=int(z.group(1),16); q(v<=1023 and d['RESULT_HEX']=='0x'+z.group(1) and d['RESULT_U32']==str(v),'result'); return {'classification':'kernel_output_written','duty_u32':v,'physical_brightness_inferred':False,'raw_fields':d}
def lifecycle(private,boot,files):
 x=mod(); exe=x.execute(private,boot,files).replace('TconStatusRead','ManagedTconDutyRead'); return [x.create(private,boot),*x.stage(private,boot,files),exe,x.postflight(private,boot,files),x.cleanup(private,boot)]
def dry(m,files):
 x=mod(); p='/tmp/researcher-tcon-'+'0'*32; cmds=[x.preflight(),*lifecycle(p,'00000000-0000-0000-0000-000000000000',files)]; return {'dry_run':True,'no_tv_or_device_calls':True,'one_shot':True,'retry_permitted':False,'flash_guard_risk':'No target flash flag has been read; this is an unresolved preflight race, not a claim that no implementation is possible.','lifecycle_reused_from_hashpinned_status_runner':dg(S),'command_count':len(cmds),'all_commands_bounded':all(0<len(c.encode())<=8192 for c in cmds),'payloads':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},'parser':'exact schema, unknown-field rejection'}
def run_once(destination,m,files):
 x=mod()
 x.MANIFEST=M
 x.ABI_REPORT_SHA256=ABI_SHA
 q(dg(H.parents[1]/'tcon-research/qd-generic-read-command-abi.md')==ABI_SHA,'generic ABI changed')
 original_execute=x.execute
 x.execute=lambda private,boot,data: original_execute(private,boot,data).replace('TconStatusRead.dll','ManagedTconDutyRead.dll')
 x.parse_managed=parse
 original_save=x.save
 def save(path,record):
  record['schema']='managed-tcon-duty-read-result-v1'
  record['measurement']='fixed selector 0x128, generic read operation19'
  record['physical_state']='unobserved'
  record['limitations']=[
   'Changed output is kernel_output_written; no physical brightness inference.',
   'No live firmware flash/update flag is sampled. Concurrency race not excluded.',
   'The generic wrapper lacks the separate status getter flash-update gate.',
   'A six-byte request and four-byte reply may have controller bookkeeping effects.',
   'Packaged profile equality to live controller flash is not established.',
  ]
  original_save(path,record)
 x.save=save
 return x.run_once(destination,m,files)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--reviewed',action='store_true');p.add_argument('--output');a=p.parse_args();m,f=contract()
 if not a.run: q(not a.reviewed and a.output is None,'flags');print(json.dumps(dry(m,f),sort_keys=True));return
 q(a.reviewed and a.output and os.path.isabs(a.output),'live flags')
 result=run_once(Path(os.path.abspath(a.output)),m,f)
 print(json.dumps({'result':a.output,'accepted':result['accepted'],'cleanup_confirmed':result.get('cleanup_confirmed'),'physical_state':'unobserved','measurement':result.get('execution',{}).get('result')},sort_keys=True))
 if not result['accepted']: raise SystemExit(1)
if __name__=='__main__':main()
