#!/usr/bin/env python3
"""Offline admission of a completed ER40 capture before a separate EB read."""
import argparse
import base64
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
PARSER = B / 'rtp-quiescent-checkpoints-20261028er/parse-result.py'
PARSER_SHA = '3bc61ac0176fcb4ad228fe5357ff80ec856a32068705c5aa8a557d81c005a069'


def need(condition, reason):
    if not condition:
        raise ValueError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(directory, manifest_sha256):
    need(directory.is_absolute() and not directory.is_symlink(), 'ordinary absolute capture')
    need(sha(PARSER.read_bytes()) == PARSER_SHA, 'frozen ER parser')
    spec = importlib.util.spec_from_file_location('es_er_admission', PARSER)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    manifest_raw=(HERE/'deployment-manifest.json').read_bytes()
    need(sha(manifest_raw)==manifest_sha256,'explicit frozen FC manifest digest')
    manifest=json.loads(manifest_raw)
    need(manifest['schema']=='fc-reader-wake-wrapper-manifest-v1','FC manifest schema')
    for name,row in manifest['wrapperFiles'].items():
        need(Path(name).name==name and (HERE/name).is_file() and sha((HERE/name).read_bytes())==row['sha256'],'FC source pin')
    spec=importlib.util.spec_from_file_location('fc_admission_wrapper',HERE/'run-once.py');wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
    rebuilt,payload=wrapper.build_manifest()
    need(wrapper.manifest_bytes(rebuilt)==manifest_raw==(directory/'reviewed-manifest.json').read_bytes(),'regenerated/captured FC manifest')
    wake=wrapper.load_pinned(HERE/'wake-check.py',wrapper.WAKE_SHA,'fc_admission_wake')
    native_path = directory / 'native.receipt.json' 
    n, summaries, files, gc, q = parser.parse_native(native_path.read_text())
    need(gc == [] and q.get('trialQualified') is True, 'strict synchronized workflow qualification')
    result_path = directory / 'result.json'
    r = parser.load_parent().strict_json(result_path.read_text())
    need(type(r) is dict, 'wrapper result object')
    for key in ('nativeInvocations', 'retries', 'headersSent', 'bulkTransfers', 'scoreCheckpointCount','quiescentCyclesCompleted'):
        need(type(r.get(key)) is int, 'exact integer result field ' + key)
    need(type(r.get('rawFiles')) is list and all(type(row) is dict and type(row.get('bytes')) is int for row in r['rawFiles']), 'exact integer raw sizes')
    need(r.get('accepted') is True and r.get('trialQualified') is True
         and r.get('manifestSha256') == manifest_sha256 and r.get('schema')=='fc-reader-wake-wrapper-result-v1' and r.get('cleanup') == 'STAGE_ABSENT'
         and r.get('nativeInvocations') == 1 and r.get('retries') == 0, 'accepted one-shot ER result')
    need(all(type(r.get(k))is int for k in ['wrapperUiOperations','wrapperUiOperationsAttempted','wrapperUiOperationsCompleted','wrapperKeyChildAttempts']),'exact FC UI counter integers')
    need(r.get('wrapperUiOperations')==r.get('wrapperUiOperationsAttempted')==r.get('wrapperUiOperationsCompleted')==1 and r.get('wrapperKeyChildAttempts')==2,'truthful fixed wrapper UI counts')
    cp=parser.load_parent().strict_json((directory/'wake-checkpoint.json').read_text())
    wake_proof=wake.validate(directory,cp)
    need(sha((directory/'wake-checkpoint.json').read_bytes())==r.get('wakeCheckpointSha256'),'saved wake digest')
    record=parser.load_parent().strict_json((directory/'record.json').read_text())
    need(record.get('schema')=='fc-reader-wake-wrapper-record-v1'and record.get('wakeCheckpoint')==cp and record.get('wrapperUiOperations')==1,'wrapper record/wake binding')
    need(all(type(record.get(k))is int for k in ['native_invocations','target_operations','wrapperUiOperations']),'exact completed record counter integers')
    need(record.get('native_invocations_status')=='one_completed'and record.get('no_retry')is True,'completed/no-retry record status')
    need(record['native_invocations']==1 and record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','wrapper completed cleanup')
    need(record.get('manifestSha256')==manifest_sha256 and r.get('structuredReceipt')=='exclusive_private_file'and r.get('diagnosticStdoutIsSemanticReceipt')is False,'manifest/exclusive receipt record')
    first,last=cp['firstUiCallIndex'],cp['lastUiCallIndex'];calls=record['calls']
    need(type(first)is type(last)is int and 0<=first<=last<len(calls) and last-first+1==1+len(cp['snapshots']),'exact UI request span')
    need(first>=1 and calls[first-1]['command'].endswith('echo BEFORE_INVOKE_READY\n')and last+1<len(calls) and ' --execute --device 'in calls[last+1]['command'],'UI stage exact position')
    need(sum(' --execute --device 'in c['command']for c in calls)==1,'one native command')
    for c in calls:
        response=c['response'];rows=response['commands']
        need(type(c.get('transport_exit'))is int and type(response.get('uid'))is type(response.get('euid'))is int and type(rows[0].get('exit_code'))is int,'exact root status integers')
        need(c['host_timeout']is False and c['transport_exit']==0 and response['authenticated']is True and response['uid']==response['euid']==0 and len(rows)==1,'all saved root transports accepted')
        need(rows[0]['command']==c['command']and rows[0]['exit_code']==0 and rows[0]['timed_out']is False and rows[0]['stderr']=='','all saved root commands complete')
    need(calls[last+1]['response']['commands'][0]['stdout']==(directory/'native-envelope.txt').read_text(),'native request/envelope binding')
    for offset,c in enumerate(calls[first:last+1]):
        label='wake'if offset==0 else f'ui-snapshot-{offset:02d}'
        need(c['command']==(directory/(label+'-command.txt')).read_text(),'UI root command binding')
        response=c['response'];rows=response['commands'];need(response['authenticated']is True and response['uid']==response['euid']==0 and len(rows)==1 and c['transport_exit']==0 and c['host_timeout']is False,'UI authenticated transport')
        need(rows[0]['command']==c['command']and rows[0]['exit_code']==0 and rows[0]['timed_out']is False and rows[0]['stderr']==''and rows[0]['stdout']==(directory/(label+'-response.txt')).read_text(),'exact UI root response')
    ready,readyraw=wrapper.load_readiness(directory/'readiness-decision.json',r['readinessSha256'])
    need(record['readinessSha256']==sha(readyraw)and str(n['device'])==ready['identity']['devnum'],'readiness/native device')
    for row in ready['evidence']:need(sha(Path(row['path']).read_bytes())==row['sha256'],'readiness evidence unchanged')
    nine_files=dict(payload)
    for tag in ['selftest','native']:
        env=(directory/(tag+'-envelope.txt')).read_text()
        if tag=='native':need(env.startswith('IMMEDIATE_READY\n'),'native immediate readiness');env=env.removeprefix('IMMEDIATE_READY\n')
        terminal,receipt,stdout,stderr=wrapper.receipt_envelope(env)
        need(type(record[tag+'Terminal'].get('exit_code'))is int,'exact saved terminal exit integer')
        need(terminal==record[tag+'Terminal']and terminal['exit_code']==0 and stderr==b'','closed envelope')
        for suffix,value in [('receipt.json',receipt),('stdout',stdout),('stderr',stderr)]:
            need(value==(directory/(tag+'.'+suffix)).read_bytes(),'exact exclusive blobs')
            nine_files[tag+'.'+suffix]=value
        need(record.get(tag+'DiagnosticStdout')=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'opaque diagnostic hash binding')
        if tag=='selftest':
            test=parser.load_parent().strict_json(receipt.decode())
            need(type(test)is dict and set(test)=={'selfTestsPassed','keyTestsPassed','checkpointTestsPassed','targetOperations'}and all(type(v)is int for v in test.values())and test=={'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':79,'targetOperations':0},'exact zero-I/O selftest receipt')
    # Bind the actual terminal requests, not merely local completion labels.
    stage=record.get('remote_stage')
    need(type(stage)is str and re.fullmatch(r'/tmp/researcher-er-[0-9a-f]{32}',stage)is not None,'fixed ER owned stage')
    need(len(nine_files)==9 and set(payload)==set(wrapper.NAMES)and list(nine_files)==list(payload)+['selftest.receipt.json','selftest.stdout','selftest.stderr','native.receipt.json','native.stdout','native.stderr'],'exact nine remote files')
    prefix='set -eu\numask 077\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {wrapper.BOOT}\n'
    frozen=wrapper.old()
    native_index=last+1
    need(len(calls)==native_index+4,'native followed by exactly post-census/integrity/cleanup; no extra or missing tail requests')
    native_command=calls[native_index]['command']
    invocation=f'/usr/bin/dotnet {stage}/{wrapper.NAMES[0]} --execute --device {ready["identity"]["devnum"]} > {stage}/native.stdout 2> {stage}/native.stderr\n'
    need(f'cd {stage}\n'in native_command and invocation in native_command,'native invocation uses the recorded owned stage/device')
    need(first>=2 and ' --receipt-self-test > 'in calls[first-2]['command']and calls[first-2]['response']['commands'][0]['stdout']==(directory/'selftest-envelope.txt').read_text(),'selftest precedes full pre-native census and binds its saved envelope')
    for index,marker,filename,key in [(0,'PRE_READY','metadata-pre.txt','preCensus'),(first-1,'BEFORE_INVOKE_READY','metadata-before-invoke.txt','beforeInvokeCensus'),(native_index+1,'POST_READY','metadata-post.txt','postCensus')]:
        command=prefix+wrapper.metadata_body(ready['identity'],marker)
        text=calls[index]['response']['commands'][0]['stdout']
        need(calls[index]['command']==command and text==(directory/filename).read_text(),'exact cached identity/census command and saved response '+marker)
        census=record.get(key)
        need(type(census)is dict and all(type(census.get(k))is int for k in ['expected','missingEnoent','observedHolders','otherErrors'])and census.get('continuousAbsenceEstablished')is False,'exact saved census counter types')
        need(wrapper.parse_metadata(text,marker)==census,'strict saved census '+marker)
    integrity_command=prefix+frozen.integrity(stage,nine_files,list(nine_files))+'echo FINAL_INTEGRITY_OK\n'
    cleanup_command=(prefix+frozen.dir_guard(stage)+frozen.exact_inventory(stage,list(nine_files))+
        'rm -- '+' '.join(stage+'/'+name for name in nine_files)+'\n'+
        f'rmdir -- {stage}\ntest ! -e {stage}\ntest ! -L {stage}\necho STAGE_ABSENT\n')
    for index,command,text in [(native_index+2,integrity_command,'FINAL_INTEGRITY_OK\n'),(native_index+3,cleanup_command,'STAGE_ABSENT\n')]:
        need(len(command.encode())<=8192 and calls[index]['command']==command,'exact final owned-inventory command')
        need(calls[index]['response']['commands'][0]['stdout']==text,'exact final integrity/cleanup root receipt')
    need(record['cleanup_stdout']==calls[-1]['response']['commands'][0]['stdout']and r['cleanup']=='STAGE_ABSENT','cleanup result bound to actual final root response')
    need(n['accepted'] is True and n['protocolPhase'] == 'ReadyForHeader'
         and n['released'] is True and n['closed'] is True, 'closed native boundary')
    need(r['quiescentCyclesCompleted']==n['quiescentCyclesCompleted']and r.get('rtObservationOutcome')==q['rtObservationOutcome'],'exact result observation classifications')
    need(record['target_operations']==n['headersSent'],'record native header count')
    need(r['headersSent'] == n['headersSent'] and r['bulkTransfers'] == n['bulkTransfers'], 'exact transfer counts')
    inventory = []
    for name, raw, digest in files:
        need((directory / name).read_bytes() == raw, 'saved raw ' + name)
        inventory.append({'name': name, 'bytes': len(raw), 'sha256': digest})
    need(record.get('retained_raw_files')==inventory,'record raw inventory')
    need(q==parser.load_parent().strict_json((directory/'interpretation.json').read_text()),'saved strict interpretation')
    need(r['rawFiles'] == inventory, 'complete saved raw inventory')
    rows = q['scoreCheckpoints']['rows']
    need(1 <= len(rows) <= 56 and r['scoreCheckpointCount'] == len(rows), 'complete compact row count')
    need(all(x['startAlternateThreshold'] == x['endAlternateThreshold'] == 40 for x in rows), 'all compact limits40')
    need(n['terminalReason'] in ('TimeLimit', 'CycleLimit', 'TransitionCaptured'), 'qualified terminal reason')
    r_samples = []
    completed_ins = []
    for capture in n['retained']:
        transfers = capture['transfers']
        for index, window in enumerate(capture['windows']):
            if window['complete']:
                pair = transfers[2 * index:2 * index + 2]
                need(len(pair) == 2 and pair[1]['afterUs'] is not None, 'complete pair time')
                completed_ins.append(pair[1]['afterUs'])
                if window['name'] == 'R':
                    raw = base64.b64decode(window['rawBase64'], validate=True)
                    need(len(raw) == 256 and struct.unpack_from('<H', raw, 0xc4)[0] == 40, 'every retained R limit40')
                    r_samples.append((pair[1]['afterUs'], [struct.unpack_from('<H', raw, off)[0] for off in (0, 10, 14)]))
    need(bool(r_samples), 'actual retained R samples')
    expected = max(r_samples, key=lambda row: row[0])[1]
    if n['terminalReason'] == 'TransitionCaptured':
        need(expected == [1, 0x1001, 0], 'fault terminal has latest fault R')
    else:
        need(expected in ([0, 0, 1], [0, 0, 0]), 'bounded nonfault terminal has clean or quiescent latest R')
    all_sampled_clean = all(x['cleanRBrackets'] for x in rows) and all(t == [0, 0, 1] for _, t in r_samples)
    return {'schema': 'fc-completed-wake-er40-admission-v1', 'wakeCheckpoint':wake_proof,'terminalRootRequestsBound':True,'exactNineRemoteFiles':9,'manifestSha256':manifest_sha256, 'accepted': True,
            'headers': r['headersSent'], 'bulks': r['bulkTransfers'],
            'checkpoints': len(rows), 'maximumSampledA0': max(x['a0U32'] for x in rows),
            'terminal': n['terminalReason'], 'lastRtTuple': expected,
            'quiescentCyclesCompleted': n['quiescentCyclesCompleted'],
            'allSampledClean': all_sampled_clean, 'rtObservationOutcome': q['rtObservationOutcome'],
            'lastCompletedDataAfterUs': max(completed_ins), 'actualSampledLimit': 40,
            'phase': 'ReadyForHeader', 'released': True, 'closed': True,
            'cleanup': 'STAGE_ABSENT', 'targetOperations': 0,
            'physicalPictureObserved': False, 'endpointQueueProof': False,
            'inputs': [{'path': str(path), 'sha256': sha(path.read_bytes())}
                       for path in (PARSER, native_path, result_path)]}

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--capture', type=Path, required=True)
    cli.add_argument('--manifest-sha256', required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    need(args.output.is_absolute() and not args.output.exists(), 'fresh absolute proof output')
    result = verify(args.capture,args.manifest_sha256)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'inputs'}))

if __name__ == '__main__':
    main()
