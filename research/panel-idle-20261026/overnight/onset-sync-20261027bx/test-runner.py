#!/usr/bin/env python3
"""Offline fake-root runner checks. Never import root transport or contact TV."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import shlex
import sys
import tempfile
import types

HERE = Path(__file__).resolve().parent
runner = types.ModuleType('bx_runner_tests'); runner.__file__ = str(HERE / 'run-once.py')
exec(compile(Path(runner.__file__).read_bytes(), runner.__file__, 'exec'), runner.__dict__)
parser = runner.load_pinned(HERE / 'parse-result.py', runner.PARSER_SHA, 'bx_runner_parser')
checks = 0
commands = []


def check(ok, why):
    global checks
    if not ok: raise ValueError(why)
    checks += 1


def rejected(function, why):
    try:
        function()
    except (ValueError, KeyError, TypeError, OSError, UnicodeError):
        check(True, why)
        return
    raise ValueError('accepted: ' + why)


def decision():
    # Synthetic identity for fake-shell tests, never asserted as target evidence.
    identity = {'boot': runner.BOOT, 'sysfsRealpath': '/sys/devices/platform/usb/usb7/7-1',
                'sysfsStat': '42:1234', 'busnum': '7', 'devnum': '53',
                'deviceNode': '/dev/bus/usb/007/053', 'nodeStat': 'bd:334:12345',
                'descriptorsSha256': runner.sha(bytes.fromhex(runner.DESCRIPTORS)),
                'configuration': '1', 'authorized': '1', 'runtimeStatus': 'active',
                'interfaceNumber': '02', 'alternate': '0', 'interfaceClass': 'ff',
                'interfaceSubClass': '00', 'interfaceProtocol': '00'}
    return {'schema': 'synchronized-onset-readiness-decision-v1', 'accepted': True,
            'identity': identity, 'interfaceUnbound': True, 'noHolders': True,
            'closedWorldVendorOutLineage': {'accepted': True,
                'statement': 'SYNTHETIC HOST TEST ONLY: no assertion about any real device queue or lineage.',
                'evidenceSha256': 'a'*64}, 'evidence': [{'path': '/host/fake-only.json', 'sha256': 'b'*64}],
            'endpointQueueProof': False}


def native(armed=True):
    original = HERE.parent / 'managed-usb-rt-passive-observer/fixtures' / (
        'accepted-transition-rstart.json' if armed else 'accepted-already-faulted.json')
    raw = original.read_bytes()
    expected = ('4a0df14090e29d0c4e90f63571edf7631ac42f595eac965eca16efcdd5a00309' if armed else
                '23e1b61b576079bae8283b9a4f5a8fa0af279b7f534dc3d468e04211d6f4fb04')
    check(runner.sha(raw) == expected, 'frozen original fixture pin')
    value = json.loads(raw)
    state = {'key': 'Left', 'trigger': 'first-full-clean-cycle', 'attempted': armed,
             'completed': armed, 'uiReceiptObserved': False, 'physicalPictureObserved': False, 'calls': []}
    if armed:
        state.update(armedUs=1200, endUs=1700)
        baseline = copy.deepcopy(value['retained'][0]); baseline['role'] = 'trigger-baseline'
        value['retained'].insert(0, baseline)
    for phase, before, after in [('down',1300,1400), ('up',1500,1600)]:
        row = {'phase': phase, 'started': armed, 'reaped': armed, 'timedOut': False, 'stdoutBytes': 0, 'stderrBytes': 0}
        if armed: row.update(beforeUs=before, afterUs=after, exitCode=0)
        state['calls'].append(row)
    value.update(schema=parser.SCHEMA, intervention=state, observationAccepted=True, accepted=armed)
    return (json.dumps(value, separators=(',', ':'))+'\n').encode()


def envelope(stdout, rc=0, stderr=b''):
    b64 = lambda raw: base64.b64encode(raw).decode()
    return ('IMMEDIATE_READY\nMETA_BEGIN\n' + runner.BOOT + '\n1.0 2.0\n' + str(rc) + '\n' +
            str(len(stdout)) + '\n' + runner.sha(stdout) + '\n' + str(len(stderr)) + '\n' + runner.sha(stderr) +
            '\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n' + b64(stdout) +
            '\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n' + b64(stderr) + '\nSTDERR_B64_END\nEXECUTE_COMPLETE\n')


class FakeRoot:
    def __init__(self, kind='success', armed=True):
        self.kind = kind; self.invocations = 0; self.cleanups = 0; self.stages = 0; self.seen = []
        self.stdout = native(armed); self.rc = 0 if armed else 1
    def root(self, command, record, path):
        commands.append(command); self.seen.append(command)
        check(len(command.encode()) <= 8192, 'command extent')
        checked = subprocess.run(['sh', '-n'], input=command.encode(), capture_output=True)
        check(checked.returncode == 0, 'shell syntax: '+checked.stderr.decode())
        check(not any(x in command for x in ['ftrace', 'VLOG', 'vconftool', 'reboot', 'killall', 'GetImage', 'SetPower']), 'no hidden unrelated action')
        record.setdefault('calls', []).append({'fake': True, 'command': command})
        runner.save(path, record)
        if command.endswith('echo PRE_READY\n'):
            if self.kind == 'pre-race': raise ValueError('synthetic identity race at precheck')
            return 'FDCENSUS expected=123 missing=2 holders=0 errors=0\nPRE_READY\n'
        if command.endswith('echo BEFORE_INVOKE_READY\n'):
            if self.kind == 'before-race': raise ValueError('synthetic preinvoke census refusal')
            return 'FDCENSUS expected=125 missing=3 holders=0 errors=0\nBEFORE_INVOKE_READY\n'
        if 'echo PRIVATE_STAGE_CREATED\n' in command:
            self.stages += 1; return 'PRIVATE_STAGE_CREATED\n'
        if command.endswith('echo STAGED_CHUNK\n'): return 'STAGED_CHUNK\n'
        if command.endswith('echo STAGED_FILE\n'): return 'STAGED_FILE\n'
        if command.endswith(' --self-test\n'):
            return '{"selfTestsPassed":75,"targetOperations":0,"maxTestOutputBytes":10541}\n'
        if command.endswith(' --key-self-test\n'):
            return '{"keyTestsPassed":22,"targetOperations":0,"maxTestOutputBytes":14476}\n'
        if ' --execute > ' in command:
            if self.kind == 'immediate-race': raise ValueError('synthetic identity race before invoke')
            self.invocations += 1
            if self.kind == 'timeout': raise OSError('synthetic timeout; no retry')
            if self.kind == 'partial-envelope': return 'IMMEDIATE_READY\nMETA_BEGIN\n'
            if self.kind == 'partial-native': return envelope(b'{"schema":', 1)
            if self.kind == 'bad-key':
                value=json.loads(self.stdout); value['intervention']['calls'][0]['exitCode']=1
                return envelope(json.dumps(value).encode())
            if self.kind == 'bad-exit': return envelope(self.stdout, 1-self.rc)
            if self.kind == 'stderr': return envelope(self.stdout, self.rc, b'error')
            return envelope(self.stdout, self.rc)
        if command.endswith('echo POST_READY\n'):
            if self.kind == 'post-race': raise ValueError('synthetic identity race after invoke')
            return 'FDCENSUS expected=120 missing=1 holders=0 errors=0\nPOST_READY\n'
        if command.endswith('echo STAGE_ABSENT\n'):
            self.cleanups += 1
            if self.kind == 'cleanup-fail': raise OSError('synthetic cleanup guard failure')
            if self.kind == 'cleanup-receipt': return 'WRONG\n'
            return 'STAGE_ABSENT\n'
        raise ValueError('unclassified fake command')


# Dry CLI must not inspect build files, import transport, create output or write
# pycache. -B is explicit; runner itself loads pinned sources by compile only.
dry=subprocess.run([sys.executable, '-B', str(HERE/'run-once.py')], capture_output=True)
check(dry.returncode == 0 and dry.stderr == b'' and json.loads(dry.stdout)['targetOperations'] == 0, 'default dry')
manifest, payload = runner.build_manifest(); reviewed = runner.manifest_bytes(manifest)
check(set(payload) == set(runner.NAMES), 'snapshot three payloads')
check(runner.manifest_bytes(runner.build_manifest()[0]) == reviewed, 'deterministic manifest')
check(manifest['nativeInvocations'] == 1 and manifest['wrapperUiOperations'] == 0, 'one invocation/UI scope')
with tempfile.TemporaryDirectory(prefix='bx-runner-host-only-') as tmp:
    base=Path(tmp)
    ready=decision(); ready_raw=(json.dumps(ready)+'\n').encode(); path=base/'decision.json';path.write_bytes(ready_raw)
    loaded, exact=runner.load_readiness(path, runner.sha(ready_raw))
    check(loaded == ready and exact == ready_raw, 'exact supplied readiness bytes')
    rejected(lambda: runner.load_readiness(path, '0'*64), 'readiness digest refusal')
    for name, mutation in [
        ('not accepted',lambda x:x.update(accepted=False)),
        ('queue proof claim',lambda x:x.update(endpointQueueProof=True)),
        ('no lineage',lambda x:x['closedWorldVendorOutLineage'].update(accepted=False)),
        ('no holders not asserted',lambda x:x.update(noHolders=False)),
        ('wrong boot',lambda x:x['identity'].update(boot='0'*36)),
        ('wrong dev',lambda x:x['identity'].update(devnum='54')),
        ('inactive',lambda x:x['identity'].update(runtimeStatus='suspended')),
        ('descriptor',lambda x:x['identity'].update(descriptorsSha256='0'*64)),
        ('bound',lambda x:x.update(interfaceUnbound=False)),
        ('extra',lambda x:x.update(extra=True)),
        ('bad node minor',lambda x:x['identity'].update(nodeStat='bd:335:12345')),
    ]:
        bad=copy.deepcopy(ready);mutation(bad);raw=json.dumps(bad).encode();path.write_bytes(raw)
        rejected(lambda:runner.load_readiness(path,runner.sha(raw)), name)
    path.write_bytes(ready_raw)
    # Main must reject both digest contracts before loading any root adapter.
    saved_loader=runner.load_pinned; saved_argv=sys.argv[:]; root_loads=[]
    def forbid_root(source,digest,name):
        if source == runner.ROOT:
            root_loads.append(str(source))
            raise ValueError('FORBIDDEN root import in refusal test')
        return saved_loader(source,digest,name)
    runner.load_pinned=forbid_root
    try:
        for manifest_digest, ready_digest in [('0'*64,runner.sha(ready_raw)),(runner.sha(reviewed),'0'*64)]:
            sys.argv=[str(HERE/'run-once.py'),'--execute','--manifest-sha256',manifest_digest,
                      '--readiness',str(path),'--readiness-sha256',ready_digest,'--output',str(base/'refused')]
            rejected(runner.main,'CLI local digest refusal')
        check(root_loads == [] and not (base/'refused').exists(), 'no root load/output on local refusal')
    finally:
        runner.load_pinned=saved_loader;sys.argv=saved_argv
    for armed in (True,False):
        root=FakeRoot(armed=armed);out=base/('normal' if armed else 'unarmed')
        result=runner.execute(out,ready,ready_raw,reviewed,payload,root,parser)
        check(root.invocations == 1 and root.cleanups == 1 and root.stages == 1, 'one-shot stages/invoke/cleanup')
        check(result['transportAccepted'] is True and result['trialQualified'] is armed, 'transport vs qualification')
        check(result['physicalPictureObserved'] is False and result['uiReceiptObserved'] is False and
              result['keyCausalityEstablished'] is False, 'narrow claim')
        check((out/'execute-envelope.txt').is_file() and (out/'native.stdout.bin').read_bytes() == root.stdout, 'raw saves')
        check(json.loads((out/'record.json').read_text())['cleanup_required'] is False, 'cleanup recorded')
        check(result['headersSent'] == json.loads(root.stdout)['headersSent'], 'baseline counters unchanged')
    for kind in ['pre-race','before-race','immediate-race','timeout','partial-envelope','partial-native','bad-key','bad-exit',
                 'stderr','post-race','cleanup-fail','cleanup-receipt']:
        root=FakeRoot(kind);out=base/kind
        rejected(lambda:runner.execute(out,ready,ready_raw,reviewed,payload,root,parser),kind)
        check(root.invocations <= 1, 'no retry '+kind)
        check(root.cleanups == (1 if kind.startswith('cleanup') else 0), 'ambiguous retain '+kind)
        check(not (out/'result.json').exists() and json.loads((out/'record.json').read_text())['cleanup_required'] is True,
              'no accepted result/cleanup claim '+kind)
        if kind in ['partial-envelope','partial-native','bad-key','bad-exit','stderr','post-race','cleanup-fail','cleanup-receipt']:
            check((out/'execute-envelope.txt').is_file(), 'save envelope before reject '+kind)
        if kind in ['partial-native','bad-key','bad-exit','stderr','post-race','cleanup-fail','cleanup-receipt']:
            check((out/'native.stdout.bin').is_file(), 'save native before reject '+kind)
# Check generated metadata uses exactly one batched stat census, no per-FD
# external command, and precise rdev matching (alternate path names covered).
body=runner.metadata_body(decision()['identity'],'PRE_READY')
check(body.count('bx_fd_snapshot=$(LC_ALL=C stat ') == 1 and 'for bx_fd' not in body, 'bounded batch census')
check('test "$#" -le 32768' in body and 'stat -L -c "%F|%t:%T" "$@"' in body, 'census bounded/noholders')
check(max(len(command.encode()) for command in commands) <= 8192, 'all command maxima')
# Execute only the standalone awk classifier with synthetic text; no target
# shell or /proc traversal. ENOENT is snapshot churn, never queue clearance.
def classify(text, expected, rc):
    return subprocess.run(['awk','-F','|','-v','expected='+str(expected),'-v','rc='+str(rc),
                           '-v','bx_rdev=bd:334',runner.FD_CENSUS_AWK],input=text.encode(),capture_output=True)
# Exact ordinary-target diagnostic fixture acquired by the parent, never
# generated by this host test. Opening quote is ASCII backtick, closing quote
# is ASCII apostrophe; keep the source bytes and hash pinned.
actual_stat=(HERE/'stat-format-qualified-03.txt').read_bytes()
check(runner.sha(actual_stat) == 'df9ca13c2d7fa58897e0292519cbf2034d9f8b8b0a8e49b51e26dd8d14e702fe',
      'actual target stat fixture pin')
actual_lines=actual_stat.decode('ascii').splitlines()
check(actual_lines[3] == "stat: cannot stat `/proc/2147483647/fd/2147483647': No such file or directory",
      'actual backtick/apostrophe diagnostic')
actual_reply=classify('\n'.join(actual_lines[:4])+'\n',4,1)
check(actual_reply.returncode == 0 and actual_reply.stderr == b'' and
      actual_reply.stdout == b'FDCENSUS expected=4 missing=1 holders=0 errors=0\n',
      'actual target stat ENOENT classification')
for text, expected, rc, accepted in [
    ('regular file|0:0\ncharacter special file|1:3\n',2,0,True),
    ("stat: cannot statx '/proc/123/fd/4': No such file or directory\nregular file|0:0\n",2,1,True),
    ("stat: can't stat '/proc/123/fd/4': No such file or directory\nregular file|0:0\n",2,1,True),
    ("stat: cannot stat `/proc/123/fd/4': No such file or directory\nregular file|0:0\n",2,1,True),
    ("stat: cannot stat `/proc/123/fd/4': Permission denied\n",1,1,False),
    ("stat: cannot stat `/proc/non_numeric/fd/4': No such file or directory\n",1,1,False),
    ("stat: cannot stat `/proc/123/fd/4`: No such file or directory\n",1,1,False),
    ("stat: cannot stat `/proc/123/fd/4': No such file or directory extra\n",1,1,False),
    ('character special file|bd:334\n',1,0,False),
    ('character special file|bd:3340\n',1,0,True),
    ("stat: cannot statx '/proc/123/fd/4': Permission denied\n",1,1,False),
    ("stat: cannot statx '/etc/passwd': No such file or directory\n",1,1,False),
    ('regular file|0:0\n',2,0,False),
    ("stat: cannot statx '/proc/123/fd/4': No such file or directory\n",1,0,False),
    ('regular file|0:0\n',1,2,False),
    ('unexpected diagnostic\n',1,1,False),
]:
    response=classify(text,expected,rc)
    check((response.returncode == 0) is accepted and response.stderr == b'', 'synthetic stat classifier')
    if accepted:
        counts=runner.parse_metadata(response.stdout.decode()+'PRE_READY\n','PRE_READY')
        check(counts['continuousAbsenceEstablished'] is False, 'snapshot narrow scope')
# Execute the exact shell-quoted census command-substitution and awk pipeline
# emitted by metadata_body. Mock only stat using a local fixture; do not execute
# identity getters, actual /proc traversal, or any target/root transport.
first=body.index('if bx_fd_snapshot=')
last=body.index('\nbx_value=',first)
exact_pipeline=body[first:last]
check(chr(92) not in runner.FD_CENSUS_AWK and chr(92) not in exact_pipeline,
      'census classifier/pipeline has no backslash transport sensitivity')
with tempfile.TemporaryDirectory(prefix='bx-exact-census-host-only-') as tmp:
    fixture=Path(tmp)/'stat.txt'
    for text,expected,rc,accepted in [
        ('\n'.join(actual_lines[:4])+'\n',4,1,True),
        ('regular file|0:0\ncharacter special file|1:3',2,0,True),
        ('character special file|bd:334\n',1,0,False),
        ("stat: cannot stat `/proc/123/fd/4': Permission denied\n",1,1,False),
    ]:
        fixture.write_text(text)
        script=('set -eu\nstat() { cat '+shlex.quote(str(fixture))+'; return '+str(rc)+'; }\n' +
                'set -- '+' '.join('/proc/2147483647/fd/'+str(i) for i in range(expected))+'\n'+exact_pipeline+'\n')
        response=subprocess.run(['sh'],input=script.encode(),capture_output=True)
        check((response.returncode == 0) is accepted and response.stderr == b'',
              'execute exact generated census shell on local fixture')
        if accepted:
            counts=runner.parse_metadata(response.stdout.decode()+'PRE_READY\n','PRE_READY')
            check(counts['expected'] == expected and counts['observedHolders'] == 0,
                  'exact generated shell receipt and counts')
for text in ['PRE_READY\n','FDCENSUS expected=0 missing=0 holders=0 errors=0\nPRE_READY\n',
             'FDCENSUS expected=1 missing=2 holders=0 errors=0\nPRE_READY\n',
             'FDCENSUS expected=1 missing=0 holders=1 errors=0\nPRE_READY\n']:
    rejected(lambda:runner.parse_metadata(text,'PRE_READY'),'malformed census receipt')
print(json.dumps({'schema':'synchronized-onset-wrapper-host-tests-v1','checks':checks,
                  'shellsSyntaxChecked':len(commands),'maxCommandBytes':max(map(lambda s:len(s.encode()),commands)),
                  'targetOperations':0,'fakeNativeInvocationsOnly':True},sort_keys=True))
