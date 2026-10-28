#!/usr/bin/env python3
"""One synchronized-onset invocation; dry by default, no implicit UI/recovery."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex
import types
import uuid

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'managed-usb-rt-passive-observer/run-once.py'
OLD_SHA = 'a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82'
PARSER_SHA = 'c2a653fa8ce07f18c3e817103228d7d0840a92a6e83ed44a4c8f968e856f3b06'
ROOT = HERE.parent / 'managed-ui-tab-launch/root-with-margin.py'
ROOT_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
CHECKPOINT_SHA = '2eb6f75ac69b299eb55abb134df5fd6258bc032b8aa0d3fc7c56b195748b6a5a'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
ASSEMBLY = 'SynchronizedOnset'
NAMES = [ASSEMBLY + suffix for suffix in ('.dll', '.deps.json', '.runtimeconfig.json')]
DESCRIPTORS = '12010002ef020140e8040120500201020301090262000301048032080b00020202010a09040000010202010a052400100105240100010424020205240600010705830308001009040100020a00000a07050102400010070581024000000904020002ff0000000705820200020007050202000200'
MAX_STDOUT, MAX_STDERR, MAX_ROOT = 24576, 2048, 65536
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


def build_manifest():
    """Read local frozen inputs only; never load the root adapter."""
    checkpoint_raw = (HERE / 'host-build-checkpoint.json').read_bytes()
    need(sha(checkpoint_raw) == CHECKPOINT_SHA, 'native host checkpoint pin')
    checkpoint = strict_json(checkpoint_raw)
    need(checkpoint['schema'] == 'bx-synchronized-onset-host-checkpoint-v1' and
         checkpoint['target_executions'] == 0, 'host checkpoint contract')
    pinned = {}
    payload = {}
    for name, expected in checkpoint['files'].items():
        raw = (HERE / name).read_bytes()
        need(expected == {'bytes': len(raw), 'sha256': sha(raw)}, 'checkpoint file ' + name)
        pinned[name] = expected
        if name.startswith('bin/Release/net6.0/'):
            need(Path(name).name in NAMES, 'native payload allowlist')
            payload[Path(name).name] = raw
    need(set(payload) == set(NAMES), 'three native payload files')
    for path, digest in [(OLD, OLD_SHA), (HERE / 'parse-result.py', PARSER_SHA), (ROOT, ROOT_SHA)]:
        need(sha(path.read_bytes()) == digest, 'source dependency ' + path.name)
    wrapper_files = {}
    for name in ('run-once.py', 'test-runner.py', 'README-wrapper.md'):
        raw = (HERE / name).read_bytes()
        wrapper_files[name] = {'bytes': len(raw), 'sha256': sha(raw)}
    manifest = {'schema': 'synchronized-onset-wrapper-manifest-v1',
                'nativeCheckpointSha256': CHECKPOINT_SHA, 'nativeFiles': pinned,
                'wrapperFiles': wrapper_files, 'parentWrapperSha256': OLD_SHA,
                'parserSha256': PARSER_SHA, 'rootAdapterSha256': ROOT_SHA,
                'targetDotnetSha256': DOTNET_SHA, 'boot': BOOT,
                'nativeDurationUs': 20000000, 'nativeKeyJoinBoundMs': 7000,
                'rootTimeoutSeconds': 45, 'hostTimeoutSeconds': 75,
                'nativeStdoutCap': MAX_STDOUT, 'nativeStderrCap': MAX_STDERR,
                'rootResponseCap': MAX_ROOT, 'nativeInvocations': 1, 'retries': 0,
                'wrapperUiOperations': 0, 'recoveryOperations': 0,
                'readinessSchema': 'synchronized-onset-readiness-decision-v1'}
    return manifest, payload


def manifest_bytes(manifest):
    return (json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n').encode()


def load_readiness(path, digest):
    need(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest), 'readiness digest required')
    need(path.is_absolute() and not path.is_symlink() and path.is_file(), 'local readiness regular absolute file')
    with path.open('rb') as source:
        raw = source.read(32769)
    need(len(raw) <= 32768 and sha(raw) == digest, 'readiness bytes/digest')
    value = strict_json(raw)
    need(type(value) is dict and set(value) == {'schema', 'accepted', 'identity', 'interfaceUnbound',
         'noHolders', 'closedWorldVendorOutLineage', 'evidence', 'endpointQueueProof'}, 'readiness exact fields')
    need(value['schema'] == 'synchronized-onset-readiness-decision-v1' and value['accepted'] is True,
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
    identity = value['identity']
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


def execute(output, readiness, readiness_raw, reviewed_manifest, payload, root, parser):
    """Dependencies supplied only after pinned local contract/decision acceptance."""
    frozen = old()
    need(output.is_absolute() and not output.exists() and not output.is_symlink(), 'fresh absolute output')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / 'readiness-decision.json').write_bytes(readiness_raw)
    (output / 'reviewed-manifest.json').write_bytes(reviewed_manifest)
    stage = '/tmp/researcher-onset-sync-' + uuid.uuid4().hex
    record_path = output / 'record.json'
    record = {'schema': 'synchronized-onset-wrapper-record-v1', 'manifestSha256': sha(reviewed_manifest),
              'readinessSha256': sha(readiness_raw), 'remote_stage': stage, 'calls': [],
              'native_invocations': 0, 'target_operations': 0, 'target_operations_status': 'not_started',
              'cleanup_required': True, 'no_retry': True, 'wrapperUiOperations': 0,
              'endpointQueueProof': False, 'readinessScope': 'parent closed-world lineage premise plus metadata snapshots'}
    save(record_path, record)
    def call(command):
        need(len(command.encode()) <= 8192, 'root command bound')
        text = root.root(command, record, record_path)
        need(type(text) is str and len(text.encode()) <= MAX_ROOT, 'root returned text bound')
        return text
    boot = f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
    dotnet = f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n'
    prefix = 'set -eu\numask 077\n' + boot
    identity = readiness['identity']
    pre = call(prefix + metadata_body(identity, 'PRE_READY'))
    (output / 'metadata-pre.txt').write_text(pre)
    record['preCensus'] = parse_metadata(pre, 'PRE_READY')
    save(record_path, record)
    created = call(prefix + dotnet + f'test ! -e {stage}\ntest ! -L {stage}\nmkdir -m 700 {stage}\n' +
                   frozen.dir_guard(stage) + 'echo PRIVATE_STAGE_CREATED\n')
    need(created == 'PRIVATE_STAGE_CREATED\n', 'stage receipt')
    for name in NAMES:
        raw = payload[name]; target = stage + '/' + name
        encoded = base64.b64encode(raw).decode('ascii'); raw_offset = 0
        for offset in range(0, len(encoded), 5000):
            chunk = encoded[offset:offset+5000]; extent = len(base64.b64decode(chunk, validate=True))
            initialize = (f'test ! -e {target}\ntest ! -L {target}\n: > {target}\nchmod 600 {target}\n') if offset == 0 else ''
            response = call(prefix + frozen.dir_guard(stage) + initialize + frozen.file_guard(target, raw_offset) +
                            f'printf %s {shlex.quote(chunk)} | base64 -d >> {target}\n' +
                            frozen.file_guard(target, raw_offset+extent) + 'echo STAGED_CHUNK\n')
            need(response == 'STAGED_CHUNK\n', 'chunk receipt')
            raw_offset += extent
        need(raw_offset == len(raw), 'upload extent')
        response = call(prefix + frozen.dir_guard(stage) + frozen.file_guard(target, len(raw)) +
                        f'test "$(sha256sum {target} | cut -d " " -f1)" = {sha(raw)}\necho STAGED_FILE\n')
        need(response == 'STAGED_FILE\n', 'file receipt')
    # Inherited functions use the frozen original assembly names by default.
    check = lambda items=payload, names=NAMES: frozen.integrity(stage, items, names)
    dll = stage + '/' + NAMES[0]
    selftest = call(prefix + dotnet + check() + f'/usr/bin/dotnet {dll} --self-test\n')
    (output / 'selftest.stdout.txt').write_text(selftest)
    frozen.parse_selftest(selftest)
    keytest = call(prefix + dotnet + check() + f'/usr/bin/dotnet {dll} --key-self-test\n')
    (output / 'key-selftest.stdout.txt').write_text(keytest)
    rows, _ = frozen.parse_lines_with_gc(keytest)
    need(rows == [{'keyTestsPassed': 22, 'targetOperations': 0, 'maxTestOutputBytes': 14476}], 'key self-test contract')
    out, err = stage + '/native.stdout', stage + '/native.stderr'
    # Full census has its own root deadline. Immediate identity-only checks
    # leave native20sec+transfer2sec+join7sec within the remote45sec budget.
    before = call(prefix + metadata_body(identity, 'BEFORE_INVOKE_READY'))
    (output / 'metadata-before-invoke.txt').write_text(before)
    record['beforeInvokeCensus'] = parse_metadata(before, 'BEFORE_INVOKE_READY')
    save(record_path, record)
    command = (prefix + dotnet + check() +
               f'test ! -e {out}\ntest ! -L {out}\ntest ! -e {err}\ntest ! -L {err}\n' +
               f': > {out}\n: > {err}\nchmod 600 {out} {err}\n' +
               metadata_body(identity, 'IMMEDIATE_READY', census=False) +
               f'set +e\n/usr/bin/dotnet {dll} --execute > {out} 2> {err}\nnative_rc=$?\nset -e\n' +
               frozen.file_guard(out) + frozen.file_guard(err) +
               f'test "$(wc -c < {out})" -le {MAX_STDOUT}\ntest "$(wc -c < {err})" -le {MAX_STDERR}\n' +
               frozen.exact_inventory(stage, NAMES + ['native.stdout', 'native.stderr']) +
               'echo META_BEGIN\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\necho "$native_rc"\n' +
               f'wc -c < {out}\nsha256sum {out} | cut -d " " -f1\nwc -c < {err}\nsha256sum {err} | cut -d " " -f1\n' +
               f'echo INVENTORY_OK\necho META_END\necho STDOUT_B64_BEGIN\nbase64 {out}\n' +
               f'echo STDOUT_B64_END\necho STDERR_B64_BEGIN\nbase64 {err}\n' +
               'echo STDERR_B64_END\necho EXECUTE_COMPLETE\n')
    record.update(native_invocations=1, native_invocations_status='at_most_one_not_proven_entered',
                  target_operations=None, target_operations_status='inflight_or_unknown')
    save(record_path, record)
    response = call(command)
    (output / 'execute-envelope.txt').write_text(response)
    # Preserve entire authenticated envelope before any framing interpretation.
    need(response.startswith('IMMEDIATE_READY\n'), 'immediate readiness receipt')
    terminal, stdout, stderr = frozen.parse_envelope(response[len('IMMEDIATE_READY\n'):])
    (output / 'native.stdout.bin').write_bytes(stdout)
    (output / 'native.stderr.bin').write_bytes(stderr)
    record['terminal'] = terminal; record['terminal_validated'] = True; save(record_path, record)
    need(stderr == b'', 'native stderr empty')
    native, captures, raw_files, gc, qualification = parser.parse_native(stdout.decode('utf-8', errors='strict'))
    need(terminal['exit_code'] == (0 if native['accepted'] else 1), 'native accepted/exit consistency')
    need(qualification['transportAccepted'] is True and native['observationAccepted'] is True and
         native['protocolPhase'] == 'ReadyForHeader' and native['released'] is True and native['closed'] is True,
         'accepted ready/released/closed required')
    for name, raw, expected_sha in raw_files:
        need(re.fullmatch(r'retained-[0-9]{2}-[a-z_]+-cycle[0-9]{3}-[0-9]{2}-[RMCHL]\.bin', name) and
             sha(raw) == expected_sha, 'retained raw file contract')
        (output / name).write_bytes(raw)
    record.update(native_invocations_status='one_completed', target_operations=native['headersSent'],
                  target_operations_status='accepted_exact_read_requests',
                  native_outcome_sha256=sha(stdout), transportAccepted=True, qualification=qualification,
                  retained_raw_files=[{'name': name, 'bytes': len(raw), 'sha256': digest} for name, raw, digest in raw_files])
    save(record_path, record)
    post = call(prefix + metadata_body(identity, 'POST_READY'))
    (output / 'metadata-post.txt').write_text(post)
    record['postCensus'] = parse_metadata(post, 'POST_READY')
    save(record_path, record)
    all_remote = dict(payload, **{'native.stdout': stdout, 'native.stderr': stderr})
    names = NAMES + ['native.stdout', 'native.stderr']
    cleanup = call(prefix + check(all_remote, names) +
                   'rm -- ' + ' '.join(stage + '/' + name for name in names) + '\n' +
                   f'rmdir -- {stage}\ntest ! -e {stage}\ntest ! -L {stage}\necho STAGE_ABSENT\n')
    need(cleanup == 'STAGE_ABSENT\n', 'cleanup receipt')
    record['cleanup_required'] = False; record['cleanup_stdout'] = cleanup; save(record_path, record)
    result = {'schema': 'synchronized-onset-wrapper-result-v1', **qualification,
              'terminalReason': native['terminalReason'], 'headersSent': native['headersSent'],
              'bulkTransfers': native['bulkTransfers'], 'cyclesStarted': native['cyclesStarted'],
              'cleanCyclesCompleted': native['cleanCyclesCompleted'], 'cleanCyclesDiscarded': native['cleanCyclesDiscarded'],
              'captures': captures, 'rawFiles': record['retained_raw_files'], 'gcDiagnosticLines': len(gc),
              'manifestSha256': sha(reviewed_manifest), 'readinessSha256': sha(readiness_raw),
              'endpointQueueProof': False, 'identitySnapshotsAtomic': False,
              'wrapperUiOperations': 0, 'nativeInvocations': 1, 'retries': 0, 'cleanup': 'STAGE_ABSENT'}
    save(output / 'result.json', result)
    return result


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
        print(json.dumps({'schema': 'synchronized-onset-wrapper-dry-v1', 'targetOperations': 0,
                          'nativeDurationUs': 20000000, 'nativeKeyJoinBoundMs': 7000,
                          'rootTimeoutSeconds': 45, 'hostTimeoutSeconds': 75, 'nativeInvocations': 0,
                          'plannedNativeInvocations': 1, 'wrapperUiOperations': 0, 'retries': 0,
                          'readinessRequired': True, 'endpointQueueProof': False}, separators=(',', ':')))
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
