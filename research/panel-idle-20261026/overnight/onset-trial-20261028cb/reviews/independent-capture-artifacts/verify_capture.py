#!/usr/bin/env python3
"""Offline retained CB verification; no root imports, network or target calls."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import types

TRIAL=Path(__file__).resolve().parents[2]
BASE=TRIAL.parent
OUT=Path(__file__).resolve().parent
SOURCE=BASE/'onset-sync-20261027bx'
checks=0

def need(ok,why):
    global checks
    if not ok:raise ValueError(why)
    checks+=1

def sha(data):return hashlib.sha256(data).hexdigest()
def load(path,digest,name):
    raw=path.read_bytes();need(sha(raw)==digest,'source pin '+path.name)
    m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m

def main():
    w=load(SOURCE/'run-once.py','2e7916110354d6ab3449c940c404be572e43aa425436556a6532d4498994e53f','review_wrapper')
    p=load(SOURCE/'parse-result.py','c2a653fa8ce07f18c3e817103228d7d0840a92a6e83ed44a4c8f968e856f3b06','review_parser')
    manifest_raw=(TRIAL/'reviewed-manifest.json').read_bytes();need(sha(manifest_raw)=='8cb73c48ff6ef21e13e563efc96b59aa7f6353054d3f433cd3962d24523515ff','reviewed manifest')
    now,payload=w.build_manifest();need(w.manifest_bytes(now)==manifest_raw,'frozen sources/payload still match')
    native_raw=(TRIAL/'native.stdout.bin').read_bytes();stderr=(TRIAL/'native.stderr.bin').read_bytes();need(stderr==b'','native stderr')
    value,captures,raw_files,gc,q=p.parse_native(native_raw.decode('utf-8'))
    need(q['transportAccepted'] and q['trialQualified'] and not q['trialRejectionReasons'],'accepted strict parser qualification')
    result=json.loads((TRIAL/'result.json').read_text());record=json.loads((TRIAL/'record.json').read_text())
    for key,v in q.items():need(result[key]==v,'stored qualification '+key)
    need(result['captures']==captures,'capture summaries')
    need(result['manifestSha256']==record['manifestSha256']==sha(manifest_raw),'manifest binding')
    readiness_raw=(TRIAL/'readiness-decision.json').read_bytes();ready,_=w.load_readiness(TRIAL/'readiness-decision.json',sha(readiness_raw))
    need(result['readinessSha256']==record['readinessSha256']==sha(readiness_raw),'readiness digest binding')
    need(ready['identity']['devnum']=='54' and ready['identity']['nodeStat'].split(':')[:2]==['bd','335'],'fresh device54')
    need(not ready['endpointQueueProof'],'no queue proof claim')
    evidence=[]
    for row in ready['evidence']:
        f=Path(row['path']);need(sha(f.read_bytes())==row['sha256'],'readiness evidence hash '+f.name)
        evidence.append({'logical_path':str(f.relative_to(BASE)),'sha256':row['sha256']})
    need(any(x['sha256']==ready['closedWorldVendorOutLineage']['evidenceSha256'] for x in evidence),'premise reference binds actual evidence')
    expected_names=set();rt=[];retained=[]
    for name,raw,digest in raw_files:
        need(sha(raw)==digest,'embedded raw digest '+name);need((TRIAL/name).read_bytes()==raw,'saved raw bytes '+name)
        expected_names.add(name);retained.append({'name':name,'bytes':len(raw),'sha256':digest})
        if name.endswith('-R.bin'):
            stop,fault,gate=(struct.unpack_from('<H',raw,i)[0] for i in (0,10,14))
            classification='Clean' if (stop,fault,gate)==(0,0,1) else 'Faulted' if (stop,fault,gate)==(1,0x1001,0) else 'Unexpected'
            rt.append({'name':name,'stop':stop,'fault':fault,'ordinaryGate':gate,'classification':classification})
    need(expected_names=={f.name for f in TRIAL.glob('retained-*.bin')},'exact saved raw inventory')
    need(retained==result['rawFiles']==record['retained_raw_files'],'raw file metadata binding')
    need(len(retained)==18 and len(rt)==6,'retained raw/R counts')
    need([x['classification'] for x in rt]==['Clean','Clean','Clean','Clean','Faulted','Faulted'],'independent RT tuple sequence')
    need((value['cyclesStarted'],value['cleanCyclesCompleted'],value['cleanCyclesDiscarded'])==(6,5,4),'cycle counters')
    need(value['headersSent']==value['inputsCompleted']==36 and value['bulkTransfers']==72,'global pair counters')
    need(5*6+1+5==value['headersSent'],'five full clean cycles plus transition and postfault')
    need(value['terminalReason']=='TransitionCaptured' and value['protocolPhase']=='ReadyForHeader' and value['released'] and value['closed'],'native terminal phase/cleanup')
    need(record['native_invocations']==1 and record['native_invocations_status']=='one_completed' and record['target_operations']==36,'one invocation record')
    need(not record['cleanup_required'] and record['cleanup_stdout']=='STAGE_ABSENT\n' and result['cleanup']=='STAGE_ABSENT','cleanup accepted')
    native_calls=[];cleanups=[]
    for n,c in enumerate(record['calls']):
        command=c['command'];need(len(command.encode())==c['command_bytes']<=8192,'command cap')
        need(not c['host_timeout'] and c['transport_exit']==0,'transport completion')
        response=c['response'];need(response['authenticated'] is True and response['uid']==response['euid']==0,'root record identity')
        rows=response['commands'];need(len(rows)==1 and rows[0]['command']==command,'single command echo')
        row=rows[0];need(row['exit_code']==0 and row['stderr']=='' and row['timed_out'] is False,'target shell contract')
        need(not any(x in command for x in ['input_keyevent','vconftool','ftrace','vlogutil','SetPower','run-power-cycle','reboot']),'no hidden wrapper UI/reset/collector')
        if ' --execute > ' in command:native_calls.append((n,row['stdout']))
        if '\nrm -- ' in command:cleanups.append((n,row['stdout']))
    need(len(native_calls)==len(cleanups)==1 and native_calls[0][0]<cleanups[0][0],'one execute then cleanup')
    envelope=(TRIAL/'execute-envelope.txt').read_text();need(envelope==native_calls[0][1],'execute envelope saved exactly')
    need(envelope.startswith('IMMEDIATE_READY\n'),'immediate identity receipt')
    terminal,stdout,err=w.old().parse_envelope(envelope[len('IMMEDIATE_READY\n'):])
    need(stdout==native_raw and err==stderr and terminal==record['terminal'] and terminal['exit_code']==0,'terminal/native bytes verified')
    need(cleanups[0][1]=='STAGE_ABSENT\n','actual cleanup receipt')
    census={}
    for file,marker in [('metadata-pre.txt','PRE_READY'),('metadata-before-invoke.txt','BEFORE_INVOKE_READY'),('metadata-post.txt','POST_READY')]:
        census[file]=w.parse_metadata((TRIAL/file).read_text(),marker)
    state=value['intervention'];need(state['key']=='Left' and state['attempted'] and state['completed'] and len(state['calls'])==2,'one successful key workflow')
    down,up=state['calls'];need([x['phase'] for x in state['calls']]==['down','up'] and all(x['exitCode']==0 and x['started'] and x['reaped'] and not x['timedOut'] for x in state['calls']),'down/up success')
    order=q['ordering'];clean=order['latestCleanRead'];fault=order['firstFaultRead'];need(up['afterUs']<clean['beforeUs']<clean['afterUs']<fault['beforeUs']<fault['afterUs'],'clean and fault both strictly after key up return')
    timing={'startUs':value['startUs'],'endUs':value['endUs'],'triggerBaselineEndUs':captures[0]['last_us'],'armedUs':state['armedUs'],'down':down,'up':up,'latestCleanR':clean,'firstFaultR':fault,'conservativeSoftwareBracketWidthUs':fault['afterUs']-clean['beforeUs'],'downReturnToBracketStartUs':clean['beforeUs']-down['afterUs'],'upReturnToBracketStartUs':clean['beforeUs']-up['afterUs'],'downReturnToFirstFaultOutUs':fault['beforeUs']-down['afterUs']}
    ui=json.loads((TRIAL/'ui-after/before-summary.json').read_text());need(ui['cached_current_tab']=='d/ug.tab@Live' and ui['csfs_window_present'] and not ui['screensaver_windows_present'],'separate post UI cached Live')
    physical=json.loads((TRIAL/'owner-blackout-observation.json').read_text());need(physical['darkPanelReported'] and physical['exactPhysicalTransitionTimeUs'] is None and not physical['physicalLightWithinSoftwareBracketProved'] and not physical['causalityEstablished'],'owner physical report has honest scope')
    input_names=['native.stdout.bin','native.stderr.bin','execute-envelope.txt','record.json','result.json','readiness-decision.json','reviewed-manifest.json','metadata-pre.txt','metadata-before-invoke.txt','metadata-post.txt','owner-blackout-observation.json','ui-after/before-summary.json']
    inputs=[{'name':name,'bytes':(TRIAL/name).stat().st_size,'sha256':sha((TRIAL/name).read_bytes())} for name in input_names]
    out={'schema':'cb-independent-capture-verification-v1','pass':True,'checks':checks,'target_operations_by_reviewer':0,'network_calls':0,'native_stdout_bytes':len(native_raw),'gc_lines':len(gc),'retained_raw_files':retained,'independently_decoded_rt_windows':rt,'counters':{k:value[k] for k in ['cyclesStarted','cleanCyclesCompleted','cleanCyclesDiscarded','headersSent','bulkTransfers','inputsCompleted']},'timing':timing,'qualification':q,'census':census,'authenticated_shell_calls':len(record['calls']),'readiness_evidence':evidence,'inputs':inputs,'physical_report':'Owner subsequently reported panel went dark; no exact physical transition timestamp and no causal proof.','separate_post_ui_cached_tab':ui['cached_current_tab']}
    (OUT/'verification.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    (OUT/'parsed-result.json').write_text(json.dumps(p.parse_result(native_raw.decode()),indent=2,sort_keys=True)+'\n')
    print(json.dumps({'pass':True,'checks':checks,'strict_transport_and_trial':True,'raw_windows_verified':len(retained),'authenticated_calls':len(record['calls']),'conservative_software_bracket_us':timing['conservativeSoftwareBracketWidthUs'],'target_operations_by_reviewer':0}))

if __name__=='__main__':main()
