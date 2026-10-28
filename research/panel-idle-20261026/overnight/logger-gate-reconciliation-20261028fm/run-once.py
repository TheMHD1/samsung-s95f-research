#!/usr/bin/env python3
"""FM fixed logger restore only, one owner; dry by default."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import types
import uuid
import time

HERE = Path(__file__).resolve().parent
B = HERE.parent
OLD = B / 'managed-usb-rt-passive-observer/run-once.py'
OLD_SHA = 'a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82'
PARSER_SHA = '54eb7050d6db08704dce3a3c0d6c532d4e33b9e7d4588fa806ed664c6bdd0938'
ROOT = B / 'managed-ui-tab-launch/root-with-margin.py'
ROOT_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
CHECKPOINT_SHA = '740e0f0dca9719f8226e30f5a484a134b8d423ef2cab72f756ac4b612083793a'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
ASSEMBLY = 'LoggerGateReconciliation'
NAMES = [ASSEMBLY + suffix for suffix in ('.dll', '.deps.json', '.runtimeconfig.json')]
DESCRIPTORS = '12010002ef020140e8040120500201020301090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200'
MAX_STDOUT, MAX_STDERR, MAX_ROOT = 16384, 2048, 65536
META_KEYS = ['boot', 'sysfsRealpath', 'sysfsStat', 'busnum', 'devnum', 'deviceNode', 'nodeStat',
             'descriptorsSha256', 'configuration', 'authorized', 'runtimeStatus',
             'interfaceNumber', 'alternate', 'interfaceClass', 'interfaceSubClass', 'interfaceProtocol']


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON field ' + key)
            result[key] = value
        return result
    def bad(value):
        raise ValueError('non-JSON constant ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def load_pinned(path, digest, name):
    raw = path.read_bytes()
    need(sha(raw) == digest, 'local pin ' + path.name)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def old():
    return load_pinned(OLD, OLD_SHA, 'bx_frozen_passive_wrapper')


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


SOURCE_NAMES=['Protocol.cs','NativeBinding.cs','Engine.cs','ReceiptMain.cs','HostTests.cs','LoggerGateReconciliation.csproj','NuGet.Config','run-once.py','parse-result.py','prepare-readiness.py','verify-host.py','README.md','input-pins.json','build-host.sh','finalize.py']
def build_manifest():
    checkpoint_raw=(HERE/'host-build-checkpoint.json').read_bytes()
    need(sha(checkpoint_raw)==CHECKPOINT_SHA,'host checkpoint pin')
    cp=strict_json(checkpoint_raw);need(cp['targetOperations']==0 and cp['schema']=='fm-host-checkpoint-v1','host checkpoint contract')
    payload={}
    for name,expected in cp['files'].items():
        raw=(HERE/name).read_bytes();need(expected=={'bytes':len(raw),'sha256':sha(raw)},'host source/payload '+name)
        if name.startswith('bin/Release/net6.0/'):
            need(Path(name).name in NAMES,'payload whitelist');payload[Path(name).name]=raw
    need(set(payload)==set(NAMES),'three files')
    for row in strict_json((HERE/'input-pins.json').read_bytes())['files']:
        raw=(B/row['path']).read_bytes();need(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'frozen source dependency')
    need(sha((HERE/'parse-result.py').read_bytes())==PARSER_SHA,'parser pin')
    sources={name:{'bytes':len((HERE/name).read_bytes()),'sha256':sha((HERE/name).read_bytes())}for name in SOURCE_NAMES}
    return {'schema':'fm-logger-reconciliation-wrapper-manifest-v1','hostCheckpointSha256':CHECKPOINT_SHA,'nativeFiles':cp['files'],'sources':sources,'rootAdapterSha256':ROOT_SHA,'nativeInvocations':1,'retries':0,'threshold':40,'loggerWritesMaximum':1,'arms':0,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'rootCommandCap':8192,'rootResponseCap':65536,'structuredReceiptCap':24576,'wholeCooperativeBudgetUs':30000000,'wrapperUiOperations':0,'readinessSchema':'fm-logger-reconciliation-readiness-decision-v1','originalFgStageTouched':False,'physicalPictureObserved':False},payload


def manifest_bytes(manifest):
    return (json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n').encode()


PHASE_PROOF=B/'combined-event-trial-20261028fh/refusal-analysis/phase-proof.json'
PHASE_PROOF_SHA='b6b5573a9c1ecf3b3b075e62a3906a598f15c505e2ee846864be3e3d9c82c140'
def validate_restore_premise(p):
    need(type(p)is dict and set(p)=={'accepted','phase','released','closed','priorNativeAccepted','loggerOriginallyZero','loggerMayRemainOne','proofPath','proofSha256'},'restore-only exact premise')
    for k in ['accepted','released','closed','loggerOriginallyZero','loggerMayRemainOne']:need(p[k]is True,'restore premise '+k)
    need(p['priorNativeAccepted']is False and p['phase']=='ReadyForHeader','prior refusal and known phase')
    need(p['proofPath']==str(PHASE_PROOF) and p['proofSha256']==PHASE_PROOF_SHA and not PHASE_PROOF.is_symlink(),'fixed independent phase proof')
    raw=PHASE_PROOF.read_bytes();need(sha(raw)==PHASE_PROOF_SHA and len(raw)<=32768,'phase proof pin')
    v=strict_json(raw)
    need(v['decision']=='NATIVE_TERMINAL_KNOWN_READY_NOT_WRAPPER_ACCEPTANCE' and v['nativePhase']=='ReadyForHeader' and v['released']is True and v['closed']is True and v['originalAccepted']is False and v['wrapperAccepted']is False,'independent phase decision')
    need(v['restoreAttempted']is False and v['loggerMayRemain']is True and v['device']==65 and v['headers']==158 and v['bulks']==316,'fixed prior invocation')
    for row in v['inputs']:
        path=PHASE_PROOF.parent.parent/row['path'];need(not path.is_symlink() and '..'not in Path(row['path']).parts,'proof input path')
        data=path.read_bytes();need(len(data)==row['bytes']and sha(data)==row['sha256'],'independent proof source hash')
    native=strict_json((PHASE_PROOF.parent.parent/'capture-01/native.receipt.json').read_bytes())
    def logger_at(cap):
        w=next(w for w in cap['windows']if w['name']=='R');b=base64.b64decode(w['raw'],validate=True);need(len(b)==256,'original R extent');return int.from_bytes(b[6:8],'little')
    need(logger_at(next(c for c in native['controls']if c['role']=='prearm-R'))==0 and logger_at(next(c for c in native['controls']if c['role']=='armed-R'))==1,'original gate zero then one')
    need(native['phase']=='ReadyForHeader' and native['released']is True and native['closed']is True and native['restoreAttempted']is False,'original terminal owned-phase corroboration')
    return v


def load_readiness(path, digest):
    need(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest), 'readiness digest required')
    need(path.is_absolute() and not path.is_symlink() and path.is_file(), 'local readiness regular absolute file')
    with path.open('rb') as source:
        raw = source.read(32769)
    need(len(raw) <= 32768 and sha(raw) == digest, 'readiness bytes/digest')
    value = strict_json(raw)
    need(type(value) is dict and set(value) == {'schema', 'accepted', 'identity', 'interfaceUnbound',
         'noHolders', 'closedWorldVendorOutLineage', 'evidence', 'endpointQueueProof','restoreOnlyPremise'}, 'readiness exact fields')
    need(value['schema'] == 'fm-logger-reconciliation-readiness-decision-v1' and value['accepted'] is True,
         'readiness accepted decision')
    need(value['interfaceUnbound'] is True and value['noHolders'] is True and
         value['endpointQueueProof'] is False, 'readiness metadata/premise distinction')
    premise = value['closedWorldVendorOutLineage']
    need(type(premise) is dict and set(premise) == {'accepted', 'statement', 'evidenceSha256'} and
         premise['accepted'] is True and type(premise['statement']) is str and
         40 <= len(premise['statement']) <= 4096 and
         re.fullmatch('[0-9a-f]{64}', premise['evidenceSha256'] or ''), 'parent closed-world lineage premise')
    need(type(value['evidence']) is list and 1 <= len(value['evidence']) <= 32, 'readiness evidence list')
    for row in value['evidence']:
        need(type(row) is dict and set(row) == {'path', 'sha256'} and type(row['path']) is str and
             1 <= len(row['path']) <= 1024 and re.fullmatch('[0-9a-f]{64}', row['sha256'] or ''), 'evidence reference')
    validate_restore_premise(value['restoreOnlyPremise'])
    identity = value['identity']
    prior=strict_json((PHASE_PROOF.parent.parent/'capture-01/readiness-decision.json').read_bytes())
    need(identity==prior['identity'],'same original FH USB instance identity')
    need(type(identity) is dict and set(identity) == set(META_KEYS) and
         all(type(item) is str for item in identity.values()), 'readiness exact identity')
    need(identity['boot'] == BOOT and identity['busnum'] == '7' and
         re.fullmatch('[1-9][0-9]{0,2}', identity['devnum']) and int(identity['devnum']) <= 127,
         'readiness boot/bus/address')
    need(identity['deviceNode'] == '/dev/bus/usb/007/' + f"{int(identity['devnum']):03}", 'node address')
    need(re.fullmatch(r'/sys/devices/[A-Za-z0-9_./:+-]+/7-1', identity['sysfsRealpath']) and
         '..' not in identity['sysfsRealpath'].split('/'), 'sysfs realpath')
    need(re.fullmatch('[0-9]+:[0-9]+', identity['sysfsStat']) and
         re.fullmatch(r'bd:[0-9a-f]+:[0-9]+', identity['nodeStat']), 'instance stat identity')
    need(int(identity['nodeStat'].split(':')[1], 16) == 768 + int(identity['devnum']) - 1, 'USB node minor')
    expected = {'descriptorsSha256': sha(bytes.fromhex(DESCRIPTORS)), 'configuration': '1',
                'authorized': '1', 'runtimeStatus': 'active', 'interfaceNumber': '02', 'alternate': '0',
                'interfaceClass': 'ff', 'interfaceSubClass': '00', 'interfaceProtocol': '00'}
    need(all(identity[key] == item for key, item in expected.items()), 'readiness native metadata')
    return value, raw


FD_CENSUS_AWK = r'''function missing_fd(line, prefix, rest, opener, suffix, path, fields, count) {
    prefix = "stat: cannot stat ";
    if (index(line, prefix) != 1) {
        prefix = "stat: cannot statx ";
        if (index(line, prefix) != 1) {
            prefix = "stat: can" apostrophe "t stat ";
            if (index(line, prefix) != 1) return 0;
        }
    }
    rest = substr(line, length(prefix) + 1);
    opener = substr(rest, 1, 1);
    if (opener != apostrophe && opener != backtick) return 0;
    suffix = apostrophe ": No such file or directory";
    if (length(rest) <= length(suffix) + 1 ||
        substr(rest, length(rest) - length(suffix) + 1) != suffix) return 0;
    path = substr(rest, 2, length(rest) - length(suffix) - 1);
    count = split(path, fields, "/");
    return count == 5 && fields[1] == "" && fields[2] == "proc" &&
           fields[3] ~ /^[0-9]+$/ && fields[4] == "fd" && fields[5] ~ /^[0-9]+$/;
}
BEGIN { missing=0; seen=0; holders=0; bad=0; apostrophe=sprintf("%c",39); backtick=sprintf("%c",96) }
missing_fd($0) { missing++; next }
NF == 2 { seen++; if ($1 == "character special file" && $2 == bx_rdev) holders++; next }
{ bad++ }
END { print "FDCENSUS expected=" expected " missing=" missing " holders=" holders " errors=" bad;
      if (bad || holders || seen + missing != expected || (rc == 0 && missing != 0) || rc > 1) exit 1 }'''


def metadata_body(identity, marker, census=True):
    """Cached metadata only. Snapshot churn is counted, never queue proof."""
    q = shlex.quote
    usb = '/sys/bus/usb/devices/7-1'
    intf = usb + ':1.2'
    getters = {'boot': 'cat /proc/sys/kernel/random/boot_id', 'sysfsRealpath': f'readlink -f {usb}',
               'sysfsStat': f'stat -L -c "%d:%i" {usb}', 'busnum': f'cat {usb}/busnum',
               'devnum': f'cat {usb}/devnum', 'deviceNode': 'printf %s ' + q(identity['deviceNode']),
               'nodeStat': 'stat -L -c "%t:%T:%i" ' + q(identity['deviceNode']),
               'descriptorsSha256': f'sha256sum {usb}/descriptors | cut -d " " -f1'}
    for key, suffix in [('configuration', 'bConfigurationValue'), ('authorized', 'authorized'),
                        ('runtimeStatus', 'power/runtime_status')]:
        getters[key] = f'cat {usb}/{suffix}'
    for key, suffix in [('interfaceNumber', 'bInterfaceNumber'), ('alternate', 'bAlternateSetting'),
                        ('interfaceClass', 'bInterfaceClass'), ('interfaceSubClass', 'bInterfaceSubClass'),
                        ('interfaceProtocol', 'bInterfaceProtocol')]:
        getters[key] = "awk '{print $1}' " + f'{intf}/{suffix}'
    text = ''
    for key in META_KEYS:
        text += f'bx_value=$({getters[key]})\ntest "$bx_value" = {q(identity[key])}\n'
    text += (f'test -c {q(identity["deviceNode"])}\n' +
             f'test ! -e {intf}/driver\ntest ! -L {intf}/driver\n')
    if census:
        awk = FD_CENSUS_AWK
        text += ('bx_pids=0\nfor bx_proc in /proc/[0-9]*; do\n'
                 '  test -d "$bx_proc" || continue\n  bx_pids=$((bx_pids+1))\n  test "$bx_pids" -le 4096\n'
                 '  test -d "$bx_proc/fd" || continue\n  test -r "$bx_proc/fd" && test -x "$bx_proc/fd"\ndone\n'
                 'set -- /proc/[0-9]*/fd/*\ntest "$#" -ge 1\ntest "$#" -le 32768\n'
                 'if bx_fd_snapshot=$(LC_ALL=C stat -L -c "%F|%t:%T" "$@" 2>&1); then bx_stat_rc=0; else bx_stat_rc=$?; fi\n'
                 "printf '%s' \"$bx_fd_snapshot\" | awk -F '|' -v expected=\"$#\" -v rc=\"$bx_stat_rc\" -v bx_rdev=" +
                 q(':'.join(identity['nodeStat'].split(':')[:2])) + ' ' + q(awk) + '\n')
        for key in ('boot', 'sysfsRealpath', 'sysfsStat', 'devnum', 'nodeStat', 'runtimeStatus', 'configuration'):
            text += f'bx_value=$({getters[key]})\ntest "$bx_value" = {q(identity[key])}\n'
        text += f'test ! -e {intf}/driver\ntest ! -L {intf}/driver\n'
    return text + f'echo {marker}\n'


def parse_metadata(text, marker, census=True):
    if not census:
        need(text == marker + '\n', 'ordinary identity receipt ' + marker)
        return None
    matched = re.fullmatch(r'FDCENSUS expected=([0-9]+) missing=([0-9]+) holders=0 errors=0\n' + marker + r'\n', text)
    need(matched is not None, 'ordinary metadata receipt ' + marker)
    expected, missing = map(int, matched.groups())
    need(1 <= expected <= 32768 and 0 <= missing <= expected, 'FD census counts')
    return {'expected': expected, 'missingEnoent': missing, 'observedHolders': 0, 'otherErrors': 0,
            'continuousAbsenceEstablished': False}


def receipt_envelope(raw):
    need(type(raw) is str and len(raw.encode()) <= MAX_ROOT, 'receipt envelope bound')
    pattern = (r'DPMETA_BEGIN\n([^\n]+)\n([^\n]+)\n([0-9]+)\n' +
               r'([0-9]+)\n([0-9a-f]{64})\n'*3 +
               r'DPMETA_END\nRECEIPT_B64_BEGIN\n([A-Za-z0-9+/=\n]*)RECEIPT_B64_END\n' +
               r'STDOUT_B64_BEGIN\n([A-Za-z0-9+/=\n]*)STDOUT_B64_END\n' +
               r'STDERR_B64_BEGIN\n([A-Za-z0-9+/=\n]*)STDERR_B64_END\nDPRUN_COMPLETE\n')
    match = re.fullmatch(pattern, raw)
    need(match is not None, 'receipt envelope framing')
    g = match.groups(); need(g[0] == BOOT and re.fullmatch(r'[0-9]+[.][0-9]+ [0-9]+[.][0-9]+', g[1]), 'receipt boot/uptime')
    need(int(g[2]) in (0,1), 'receipt native exit')
    blobs=[]
    for i, cap in enumerate((24576, MAX_STDOUT, MAX_STDERR)):
        size, digest = int(g[3+2*i]), g[4+2*i]
        compact = g[9+i].replace('\n','')
        data=base64.b64decode(compact,validate=True)
        need(base64.b64encode(data).decode()==compact and len(data)==size and size<=cap and sha(data)==digest, 'receipt extent/hash')
        blobs.append(data)
    return {'exit_code':int(g[2]),'boot':g[0],'uptime':g[1]}, *blobs


def execute(output, readiness, readiness_raw, reviewed_manifest, payload, root, parser, clock=time.monotonic_ns, sleeper=time.sleep):
    frozen=old()
    need(output.is_absolute() and not output.exists() and not output.is_symlink(),'fresh absolute output')
    output.mkdir(parents=True,exist_ok=False,mode=0o700)
    (output/'readiness-decision.json').write_bytes(readiness_raw)
    (output/'reviewed-manifest.json').write_bytes(reviewed_manifest)
    stage='/tmp/researcher-fm-'+uuid.uuid4().hex
    record_path=output/'record.json'
    record={'schema':'fm-logger-reconciliation-wrapper-record-v1','manifestSha256':sha(reviewed_manifest),'readinessSha256':sha(readiness_raw),'remote_stage':stage,'calls':[],'native_invocations':0,'target_operations':0,'target_operations_status':'not_started','cleanup_required':True,'no_retry':True,'wrapperUiOperations':0,'endpointQueueProof':False}
    save(record_path,record)
    def call(command, native_submission=False):
        need(len(command.encode())<=8192,'root command bound')
        if native_submission:
            record.update(native_invocations=1,target_operations=None,target_operations_status='inflight_or_unknown')
        value=root.root(command,record,record_path)
        need(type(value)is str and len(value.encode())<=MAX_ROOT,'root response bound')
        return value
    boot=f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
    dotnet=f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n'
    prefix='set -eu\numask 077\n'+boot
    identity=readiness['identity']
    pre=call(prefix+metadata_body(identity,'PRE_READY'));(output/'metadata-pre.txt').write_text(pre);record['preCensus']=parse_metadata(pre,'PRE_READY');save(record_path,record)
    made=call(prefix+dotnet+f'test ! -e {stage}\ntest ! -L {stage}\nmkdir -m 700 {stage}\n'+frozen.dir_guard(stage)+'echo PRIVATE_STAGE_CREATED\n');need(made=='PRIVATE_STAGE_CREATED\n','stage receipt')
    for name in NAMES:
        raw=payload[name];target=stage+'/'+name;encoded=base64.b64encode(raw).decode();used=0
        for offset in range(0,len(encoded),5000):
            chunk=encoded[offset:offset+5000];extent=len(base64.b64decode(chunk,validate=True))
            init=(f'test ! -e {target}\ntest ! -L {target}\n: > {target}\nchmod 600 {target}\n')if offset==0 else ''
            reply=call(prefix+frozen.dir_guard(stage)+init+frozen.file_guard(target,used)+f'printf %s {shlex.quote(chunk)} | base64 -d >> {target}\n'+frozen.file_guard(target,used+extent)+'echo STAGED_CHUNK\n');need(reply=='STAGED_CHUNK\n','chunk receipt');used+=extent
        need(used==len(raw),'uploaded extent')
        reply=call(prefix+frozen.dir_guard(stage)+frozen.file_guard(target,used)+f'test "$(sha256sum {target} | cut -d " " -f1)" = {sha(raw)}\necho STAGED_FILE\n');need(reply=='STAGED_FILE\n','file receipt')
    all_remote=dict(payload)
    def payload_guard():
        body=frozen.dir_guard(stage)
        for name,raw in payload.items():
            path=stage+'/'+name;body+=frozen.file_guard(path,len(raw))+f'test "$(sha256sum {path} | cut -d " " -f1)" = {sha(raw)}\n'
        return body
    def run(mode):
        tag='selftest' if mode=='selftest' else 'native'
        receipt=stage+'/'+tag+'.receipt.json';out=stage+'/'+tag+'.stdout';err=stage+'/'+tag+'.stderr'
        names=list(all_remote)+[tag+'.receipt.json',tag+'.stdout',tag+'.stderr']
        args='--receipt-self-test' if mode=='selftest' else f'--execute --device {identity["devnum"]}'
        immediate='' if mode=='selftest' else metadata_body(identity,'IMMEDIATE_READY',census=False)
        command=(prefix+dotnet+payload_guard()+frozen.exact_inventory(stage,list(all_remote))+
                 f'test ! -e {receipt}\ntest ! -L {receipt}\ntest ! -e {out}\ntest ! -L {out}\ntest ! -e {err}\ntest ! -L {err}\n'+
                 f': > {out}\n: > {err}\nchmod 600 {out} {err}\n'+immediate+
                 f'cd {stage}\nset +e\n/usr/bin/dotnet {stage}/{NAMES[0]} {args} > {out} 2> {err}\nnative_rc=$?\nset -e\n'+
                 frozen.file_guard(receipt)+frozen.file_guard(out)+frozen.file_guard(err)+
                 f'test "$(wc -c < {receipt})" -le 24576\ntest "$(wc -c < {out})" -le {MAX_STDOUT}\ntest "$(wc -c < {err})" -le {MAX_STDERR}\n'+
                 frozen.exact_inventory(stage,names)+
                 'echo DPMETA_BEGIN\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\necho "$native_rc"\n')
        for f in [receipt,out,err]:command+=f'wc -c < {f}\nsha256sum {f} | cut -d " " -f1\n'
        command+='echo DPMETA_END\n'
        for f,label in [(receipt,'RECEIPT'),(out,'STDOUT'),(err,'STDERR')]:command+=f'echo {label}_B64_BEGIN\nbase64 {f}\necho {label}_B64_END\n'
        command+='echo DPRUN_COMPLETE\n'
        record['phase']=tag;save(record_path,record)
        response=call(command,native_submission=(mode=='native'));(output/(tag+'-envelope.txt')).write_text(response)
        if mode=='native':need(response.startswith('IMMEDIATE_READY\n'),'immediate readiness receipt');response=response[len('IMMEDIATE_READY\n'):]
        terminal,receipt_raw,stdout,stderr=receipt_envelope(response)
        for name,raw in [(tag+'.receipt.json',receipt_raw),(tag+'.stdout',stdout),(tag+'.stderr',stderr)]:
            (output/name).write_bytes(raw);all_remote[name]=raw
        record[tag+'Terminal']=terminal;record[tag+'DiagnosticStdout']={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False};save(record_path,record)
        need(terminal['exit_code']in ([0,1]if mode=='native'else[0]) and stderr==b'','terminal exit and empty stderr')
        return receipt_raw
    test_raw=run('selftest')
    test=strict_json(test_raw.decode('utf8'));need(test=={'schema':'fm-host-tests-v1','checks':406,'cases':72,'targetOperations':0,'restoreOnly':True} and all(type(test[k])is int for k in ['checks','cases','targetOperations']),'exclusive zero-I/O selftest receipt')
    before=call(prefix+metadata_body(identity,'BEFORE_INVOKE_READY'));(output/'metadata-before-invoke.txt').write_text(before);record['beforeInvokeCensus']=parse_metadata(before,'BEFORE_INVOKE_READY');save(record_path,record)
    native_raw=run('native');native,rows,interpretation=parser.parse_native(native_raw.decode('utf8'));save(output/'interpretation.json',interpretation)
    need(str(native['device'])==identity['devnum'],'device binding')
    need(native['accepted']is True and record['nativeTerminal']['exit_code']==0,'original native refusal preserved, stage retained')
    record.update(native_invocations_status='one_completed',target_operations=native['headers'],target_operations_status='accepted_restore_only',loggerPayloads=native['writes']);save(record_path,record)
    post=call(prefix+metadata_body(identity,'POST_READY'));(output/'metadata-post.txt').write_text(post);record['postCensus']=parse_metadata(post,'POST_READY');save(record_path,record)
    guarded=call(prefix+frozen.integrity(stage,all_remote,list(all_remote))+'echo FINAL_INTEGRITY_OK\n');need(guarded=='FINAL_INTEGRITY_OK\n','final exact inventory/hash receipt')
    cleanup=call(prefix+frozen.dir_guard(stage)+frozen.exact_inventory(stage,list(all_remote))+'rm -- '+' '.join(stage+'/'+n for n in all_remote)+'\n'+f'rmdir -- {stage}\ntest ! -e {stage}\ntest ! -L {stage}\necho STAGE_ABSENT\n');need(cleanup=='STAGE_ABSENT\n','cleanup receipt')
    record['cleanup_required']=False;record['cleanup_stdout']=cleanup;save(record_path,record)
    result={'schema':'fm-logger-reconciliation-wrapper-result-v1','accepted':True,'headers':native['headers'],'bulks':native['bulks'],'loggerPayloads':native['writes'],'thresholdWrites':0,'loggerRestore':native['restore'],'manifestSha256':sha(reviewed_manifest),'readinessSha256':sha(readiness_raw),'endpointQueueProof':False,'identitySnapshotsAtomic':False,'physicalPictureObserved':False,'wrapperUiOperations':0,'nativeInvocations':1,'retries':0,'cleanup':'STAGE_ABSENT','originalFgStageTouched':False}
    save(output/'result.json',result);return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--execute', action='store_true')
    cli.add_argument('--print-manifest', action='store_true')
    cli.add_argument('--manifest-sha256')
    cli.add_argument('--readiness', type=Path)
    cli.add_argument('--readiness-sha256')
    cli.add_argument('--output', type=Path)
    args = cli.parse_args()
    need(not (args.execute and args.print_manifest), 'one mode')
    if not args.execute and not args.print_manifest:
        print(json.dumps({'schema':'fm-logger-reconciliation-wrapper-dry-v1','targetOperations':0,'restoreOnly':True,'arms':0,'plannedNativeInvocations':1,'wrapperUiOperations':0,'thresholdWrites':0,'maxHeaders':5,'maxBulks':10,'readinessRequired':True,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'retries':0},separators=(',',':')))
        return
    manifest, payload = build_manifest()
    raw_manifest = manifest_bytes(manifest)
    if args.print_manifest:
        print(raw_manifest.decode(), end='')
        return
    need(args.manifest_sha256 == sha(raw_manifest), 'reviewed manifest digest required')
    need(args.output is not None and args.output.is_absolute() and not args.output.exists() and
         not args.output.is_symlink(), 'fresh absolute output required')
    need(args.readiness is not None, 'readiness path required')
    readiness, readiness_raw = load_readiness(args.readiness, args.readiness_sha256)
    # No root transport module load or target operation occurs until both local
    # review contracts have passed. Pass pinned payload bytes, never reread them.
    parser = load_pinned(HERE / 'parse-result.py', PARSER_SHA, 'bx_synchronized_parser')
    root = load_pinned(ROOT, ROOT_SHA, 'bx_synchronized_root')
    need(root.REMOTE_TIMEOUT_SECONDS == 45 and root.HOST_TIMEOUT_SECONDS == 75 and
         root.MAX_COMMAND == 8192 and root.MAX_RESPONSE == MAX_ROOT, 'root transport bounds')
    result = execute(args.output, readiness, readiness_raw, raw_manifest, payload, root, parser)
    print(json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    main()
