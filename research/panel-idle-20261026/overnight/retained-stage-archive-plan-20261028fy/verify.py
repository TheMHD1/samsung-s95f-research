#!/usr/bin/env python3
"""Pure fixed plan, shell syntax and framing tests. Never executes target commands."""
import base64,copy,hashlib,json,subprocess,types
from pathlib import Path
D=Path(__file__).resolve().parent;checks=0;negatives=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def reject(f):
 global negatives
 try:f()
 except (ValueError,KeyError,TypeError):negatives+=1;ck(True,'expected rejection');return
 raise ValueError('unexpected acceptance')
m=types.ModuleType('fixed_builder');m.__file__=str(D/'build-plan.py');exec(compile((D/'build-plan.py').read_bytes(),str(D/'build-plan.py'),'exec'),m.__dict__);p=m.build()
ck((json.dumps(p,indent=2,sort_keys=True)+'\n').encode()==(D/'archive-plan.json').read_bytes(),'sealed plan exact')
ck(len(p['knownHostFiles'])==9 and len(p['ringFiles'])==2 and p['remoteFiles']==11,'11 file accounting')
max_response=0
for i,row in enumerate(p['commands'],1):
 command=row['command'];ck(command==(D/f'command-{i:02}.sh').read_text(),'saved command exact');ck(sha(command.encode())==row['commandSha256']and len(command.encode())==row['commandBytes']<=8192,'command extent/hash')
 ck(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'host syntax check only')
 for forbidden in ['rm --','rmdir ','/usr/bin/dotnet ','input_keyevent','/dev/bus','ioctl','base64 -d',' > ','>>'] :ck(forbidden not in command,'no forbidden action '+forbidden)
 ck(command.count('sha256sum ')==11 and command.count('base64 ')==1 and 'FN_SIDECAR_BEGIN'in command and 'FN_SIDECAR_END'in command,'full guards/single payload encode')
 ck('/* 'in command and '/.[!.]* 'in command and '/..?*;'in command,'hidden inventory included')
 # Synthetic exact-size content qualifies only a synthetic cloned expected hash.
 raw=bytes((i%251 for i in range(row['expectedBytes'])));sp=copy.deepcopy(p);sp['ringFiles'][row['file']]['sha256']=sha(raw);good='FN_SIDECAR_BEGIN\n'+base64.encodebytes(raw).decode()+'FN_SIDECAR_END\n'
 ck(m.parse_ring(good,row['file'],sp)==raw,'positive bounded canonical synthetic frame')
 response=copy.deepcopy(json.loads((m.C/'record.json').read_bytes())['calls'][-1]['response']);response['commands'][0]['stdout']=good
 extent=len(json.dumps(response).encode());max_response=max(max_response,extent);ck(extent<=65536,'actual envelope shape synthetic full ring bound')
 for bad in [good+'trailer\n',good.replace('FN_SIDECAR_BEGIN','OTHER'),good[:-1],'x'*65537,'FN_SIDECAR_BEGIN\n====\nFN_SIDECAR_END\n','FN_SIDECAR_BEGIN\nAA=\nFN_SIDECAR_END\n'] :reject(lambda bad=bad:m.parse_ring(bad,row['file'],sp))
 badplan=copy.deepcopy(sp);badplan['ringFiles'][row['file']]['bytes']+=1;reject(lambda:m.parse_ring(good,row['file'],badplan))
 badplan=copy.deepcopy(sp);badplan['ringFiles'][row['file']]['sha256']='0'*64;reject(lambda:m.parse_ring(good,row['file'],badplan))
reject(lambda:m.parse_ring('FN_SIDECAR_BEGIN\nFN_SIDECAR_END\n','arbitrary',p))
ck(m.parse_ring('FN_SIDECAR_BEGIN\nFN_SIDECAR_END\n','post-ring.bin',p)==b'','actual empty post ring positive')
print(json.dumps({'schema':'fy-host-qualification-v1','checks':checks,'malformedRefusals':negatives,'commandCount':2,'shellSyntaxChecks':2,'maxCommandBytes':max(x['commandBytes']for x in p['commands']),'maxRepresentativeRootEnvelopeBytes':max_response,'planSha256':sha((D/'archive-plan.json').read_bytes()),'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
