#!/usr/bin/env python3
"""Fixed non-clearing kernel log snapshot protocol and offline classifier. No transport."""
import argparse, base64, hashlib, json, os, re, stat, sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
RAW_CAP = 1048576
ERR_CAP = 2048
CHUNK = 16384
COMMAND_CAP = 8192
RESPONSE_CAP = 65536
CHUNK_FRAME_CAP = 24000
SCHEMA = 's95f-stock-log-hc-v2'
LIMITS = dict(rawBytes=RAW_CAP, stderrBytes=ERR_CAP, chunkBytes=CHUNK,
              commandBytes=COMMAND_CAP, responseBytes=RESPONSE_CAP, chunkFrameBytes=CHUNK_FRAME_CAP,
              maximumFetchCalls=65, parentRemoteSeconds=45, parentHostSeconds=75)

def need(value, message):
    if not value:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def identifiers(nonce, boot):
    need(type(nonce) is str and re.fullmatch('[0-9a-f]{32}', nonce), 'nonce must be 32 lowercase hex')
    need(type(boot) is str and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', boot), 'exact boot syntax')
    return '/tmp/s95f-stock-log-v2-' + nonce

def command_checked(body):
    need('\\' not in body, 'no backslash-sensitive root-agent quoting')
    need(len(body.encode()) <= COMMAND_CAP, 'command bound')
    return body

def guard(stage, boot):
    return f'''set -eu
LC_ALL=C
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export LC_ALL PATH
[ "$(id -u)" = 0 ]
[ "$(cat /proc/sys/kernel/random/boot_id)" = '{boot}' ]
stage='{stage}'
'''

def capture_command(nonce, boot):
    stage = identifiers(nonce, boot)
    # The shell ulimit unit is deliberately not used as a byte-size attestation.
    # Accepted data has a separate exact byte cap and must have dmesg exit zero.
    return command_checked(guard(stage, boot) + f'''umask 077
[ ! -e "$stage" ]
[ ! -L "$stage" ]
mkdir -m 700 "$stage"
[ "$(stat -c '%u:%g:%a' "$stage")" = '0:0:700' ]
before=$(cut -d ' ' -f 1 /proc/uptime)
set +e
(ulimit -f 2048 && dmesg) > "$stage/kernel.raw" 2> "$stage/stderr.raw"
rc=$?
set -e
after=$(cut -d ' ' -f 1 /proc/uptime)
[ "$(cat /proc/sys/kernel/random/boot_id)" = '{boot}' ]
[ ! -L "$stage/kernel.raw" ]
[ ! -L "$stage/stderr.raw" ]
[ -f "$stage/kernel.raw" ]
[ "$(stat -c '%u:%g:%a' "$stage/kernel.raw")" = '0:0:600' ]
[ -f "$stage/stderr.raw" ]
[ "$(stat -c '%u:%g:%a' "$stage/stderr.raw")" = '0:0:600' ]
[ "$(ls -A "$stage" | wc -l)" -eq 2 ]
echo HC_CAPTURE_BEGIN
echo nonce={nonce}
echo boot={boot}
echo procUptimeBefore=$before
echo procUptimeAfter=$after
echo dmesgExit=$rc
echo rawBytes=$(stat -c %s "$stage/kernel.raw")
echo rawSha256=$(sha256sum "$stage/kernel.raw" | cut -d ' ' -f 1)
echo stderrBytes=$(stat -c %s "$stage/stderr.raw")
echo stderrSha256=$(sha256sum "$stage/stderr.raw" | cut -d ' ' -f 1)
echo stageMode=0:0:700
echo fileMode=0:0:600
echo fileCount=2
echo HC_CAPTURE_END
''')

def decimal_time(text):
    need(type(text) is str and re.fullmatch('[0-9]+[.][0-9]+', text), 'uptime decimal syntax')
    return Decimal(text)

def parse_capture(data, nonce, boot):
    identifiers(nonce, boot)
    need(type(data) is bytes and len(data) <= RESPONSE_CAP, 'capture response bound')
    lines = data.decode('ascii').splitlines()
    need(data == ('\n'.join(lines) + '\n').encode('ascii'), 'canonical capture lines')
    names = ['nonce', 'boot', 'procUptimeBefore', 'procUptimeAfter', 'dmesgExit', 'rawBytes', 'rawSha256',
             'stderrBytes', 'stderrSha256', 'stageMode', 'fileMode', 'fileCount']
    need(len(lines) == len(names) + 2 and lines[0] == 'HC_CAPTURE_BEGIN' and lines[-1] == 'HC_CAPTURE_END', 'complete capture frame')
    row = {}
    for name, line in zip(names, lines[1:-1]):
        need(line.startswith(name + '='), 'fixed metadata ordering')
        row[name] = line[len(name) + 1:]
    need(row['nonce'] == nonce and row['boot'] == boot, 'capture instance binding')
    need(decimal_time(row['procUptimeAfter']) >= decimal_time(row['procUptimeBefore']), 'uptime ordering only')
    for key in ['dmesgExit', 'rawBytes', 'stderrBytes', 'fileCount']:
        need(re.fullmatch('0|[1-9][0-9]*', row[key]) is not None, 'unsigned canonical metadata')
        row[key] = int(row[key])
    need(row['dmesgExit'] <= 255, 'shell exit range')
    need(row['stageMode'] == '0:0:700' and row['fileMode'] == '0:0:600' and row['fileCount'] == 2, 'private fixed two-file inventory')
    for key in ['rawSha256', 'stderrSha256']:
        need(re.fullmatch('[0-9a-f]{64}', row[key]) is not None, 'SHA syntax')
    eligible = row['rawBytes'] <= RAW_CAP and row['stderrBytes'] <= ERR_CAP
    reasons = []
    if not eligible: reasons.append('capture size exceeds archive cap; stage retained')
    if row['dmesgExit'] != 0: reasons.append('dmesg returned nonzero; original refusal retained')
    if row['stderrBytes'] != 0: reasons.append('dmesg stderr is nonempty')
    accepted = eligible and not reasons
    return dict(schema=SCHEMA, metadata=row, captureAccepted=accepted, archiveEligible=eligible,
                refusalReasons=reasons, captureFrameSha256=sha(data), remoteStageRetained=True,
                completeKernelRingProven=False, controllerInitializationProven=False,
                controllerFaultClearProven=False, physicalRecoveryProven=False)

def revalidate_receipt(receipt):
    need(type(receipt) is dict and receipt.get('schema') == SCHEMA, 'receipt schema')
    row = receipt['metadata']
    names = ['nonce', 'boot', 'procUptimeBefore', 'procUptimeAfter', 'dmesgExit', 'rawBytes', 'rawSha256',
             'stderrBytes', 'stderrSha256', 'stageMode', 'fileMode', 'fileCount']
    frame = ('HC_CAPTURE_BEGIN\n' + ''.join(k + '=' + str(row[k]) + '\n' for k in names) + 'HC_CAPTURE_END\n').encode()
    expected = parse_capture(frame, row['nonce'], row['boot'])
    need(receipt == expected, 'receipt must exactly reproduce validated metadata frame')
    return row

def fetch_command(receipt, kind, index):
    row = revalidate_receipt(receipt)
    need(receipt['archiveEligible'], 'oversize capture cannot be fetched')
    need(kind in ['raw', 'stderr'], 'fixed file kind')
    need(type(index) is int and index >= 0, 'chunk index integer')
    size = row['rawBytes'] if kind == 'raw' else row['stderrBytes']
    need(index < (size + CHUNK - 1) // CHUNK, 'chunk index in exact file extent')
    count = min(CHUNK, size - index * CHUNK)
    stage = identifiers(row['nonce'], row['boot'])
    file = 'kernel.raw' if kind == 'raw' else 'stderr.raw'
    return command_checked(guard(stage, row['boot']) + f'''[ ! -L "$stage" ]
[ -d "$stage" ]
[ "$(stat -c '%u:%g:%a' "$stage")" = '0:0:700' ]
[ "$(ls -A "$stage" | wc -l)" -eq 2 ]
[ ! -L "$stage/kernel.raw" ]
[ ! -L "$stage/stderr.raw" ]
[ -f "$stage/kernel.raw" ]
[ "$(stat -c '%u:%g:%a:%s' "$stage/kernel.raw")" = '0:0:600:{row['rawBytes']}' ]
[ -f "$stage/stderr.raw" ]
[ "$(stat -c '%u:%g:%a:%s' "$stage/stderr.raw")" = '0:0:600:{row['stderrBytes']}' ]
[ "$(sha256sum "$stage/kernel.raw" | cut -d ' ' -f 1)" = '{row['rawSha256']}' ]
[ "$(sha256sum "$stage/stderr.raw" | cut -d ' ' -f 1)" = '{row['stderrSha256']}' ]
echo HC_CHUNK_BEGIN
echo nonce={row['nonce']}
echo kind={kind}
echo index={index}
echo offset={index * CHUNK}
echo bytes={count}
dd if="$stage/{file}" bs={CHUNK} skip={index} count=1 2>/dev/null | base64
[ "$(sha256sum "$stage/kernel.raw" | cut -d ' ' -f 1)" = '{row['rawSha256']}' ]
[ "$(sha256sum "$stage/stderr.raw" | cut -d ' ' -f 1)" = '{row['stderrSha256']}' ]
[ "$(cat /proc/sys/kernel/random/boot_id)" = '{row['boot']}' ]
echo HC_CHUNK_END
''')

def parse_chunk(data, receipt, kind, index):
    row = revalidate_receipt(receipt)
    fetch_command(receipt, kind, index)  # shares all extent/receipt checks
    need(type(data) is bytes and len(data) <= CHUNK_FRAME_CAP, 'chunk response cap')
    size = row['rawBytes'] if kind == 'raw' else row['stderrBytes']
    count = min(CHUNK, size - index * CHUNK)
    lines = data.decode('ascii').splitlines()
    prefix = ['HC_CHUNK_BEGIN', 'nonce=' + row['nonce'], 'kind=' + kind, 'index=' + str(index), 'offset=' + str(index * CHUNK), 'bytes=' + str(count)]
    need(lines[:6] == prefix and len(lines) >= 8 and lines[-1] == 'HC_CHUNK_END', 'complete chunk framing and identity')
    encoded = ''.join(lines[6:-1])
    need(all(re.fullmatch('[A-Za-z0-9+/]*={0,2}', x) for x in lines[6:-1]), 'base64 alphabet only')
    raw = base64.b64decode(encoded, validate=True)
    need(base64.b64encode(raw).decode() == encoded and len(raw) == count, 'canonical exact chunk bytes')
    return raw

def archive(receipt, chunk_directory, output):
    row = revalidate_receipt(receipt)
    need(receipt['archiveEligible'], 'capture is not archive eligible')
    chunk_directory, output = Path(chunk_directory), Path(output)
    expected = {f'{kind}-{i:02d}.txt' for kind, size in [('raw', row['rawBytes']), ('stderr', row['stderrBytes'])]
                for i in range((size + CHUNK - 1) // CHUNK)}
    need(not chunk_directory.is_symlink() and stat.S_IMODE(chunk_directory.stat().st_mode) == 0o700, 'private real chunk directory')
    need({p.name for p in chunk_directory.iterdir()} == expected, 'exact chunk inventory; no missing/extras')
    assembled = {}
    for kind, size, digest in [('raw', row['rawBytes'], row['rawSha256']), ('stderr', row['stderrBytes'], row['stderrSha256'])]:
        parts = []
        for i in range((size + CHUNK - 1) // CHUNK):
            path = chunk_directory / f'{kind}-{i:02d}.txt'
            need(not path.is_symlink() and path.is_file() and stat.S_IMODE(path.stat().st_mode) == 0o600 and path.stat().st_size <= RESPONSE_CAP, 'bounded regular chunk')
            parts.append(parse_chunk(path.read_bytes(), receipt, kind, i))
        blob = b''.join(parts)
        need(len(blob) == size and sha(blob) == digest, 'whole archived file hash and size')
        assembled[kind] = blob
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, blob in [('kernel.raw', assembled['raw']), ('stderr.raw', assembled['stderr'])]:
        fd = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(blob); f.flush(); os.fsync(f.fileno())
    dfd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(dfd)
    finally: os.close(dfd)
    # Classification happens only AFTER both original files have been fsynced.
    report = classify(assembled['raw'])
    result = dict(schema=SCHEMA, captureReceipt=receipt, archivedRawSha256=sha(assembled['raw']),
                  archivedStderrSha256=sha(assembled['stderr']), rawSavedBeforeFiltering=True,
                  archiveVerified=True, captureAccepted=receipt['captureAccepted'], classification=report)
    write_private_json(output / 'analysis.json', result)
    return result

def write_private_json(path, value):
    blob = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(blob); f.flush(); os.fsync(f.fileno())

# Exact source fragments are validated against pinned ELF strings by audit.py.
MARKERS = [
 ('qdf-mode2-request', 'QDF', 'Reset('),
 ('qdf-power-off', 'QDF', 'Tcon Power Off'),
 ('qdf-power-on', 'QDF', 'Tcon Power On'),
 ('qdf-err-skipped-recovery', 'QDF', 'err_det is fault. skip the tcon recovery.'),
 ('qdf-normal-tail-entered', 'QDF', 'Check Tcon and register recovery'),
 ('qdf-init-status-start', 'QDF', 'Qd init check start'),
 ('qdf-init-status-result', 'QDF', 'Qd init check['),
 ('qdf-access-success', 'QDF', 'TCON Access Success'),
 ('qdf-access-error', 'QDF', 'TCON Access Error'),
 ('qdf-display-status-result', 'QDF', 'Qd Display check['),
 ('qdf-display-error', '', 'TCON Device Display Check Error'),
 ('qdf-monitor-status', 'QDF', 'TCON Monitor Status PMIC'),
 ('qdf-frame-mode-read', 'QDF', 'read frame mode['),
 ('qdf-frame-mode-same', 'QDF', 'Same frame mode('),
 ('qdf-frame-mode-recovery', 'QDF', 'Set Frame mode for recovery'),
 ('qdf-register-replay-start', 'QDF', 'resume npc_lut data'),
 ('qdf-register-replay-end', 'QDF', 'resume npc_lut data done'),
 ('qdf-ocl-reset-call', 'QDF', 'tztv_set_sdp_jp_tcon_power_reset['),
 ('ocl-reset-return', 'OCL', 'Reset TCON power='),
 ('frc-pvcc-gpio', 'frc-tcon', 'gpio [sw-pvcc]'),
 ('frc-nreset-gpio', 'frc-tcon', 'gpio [tcon-nreset]'),
 ('frc-power-mode', 'frc-tcon', '[ft_set_power]'),
 ('frc-init-start', 'frc-tcon', '[FRC Init Start]'),
 ('frc-init-end', 'frc-tcon', '[FRC Init End]'),
 ('frc-resume-end', 'frc-tcon', 'resume end'),
]

def classify(raw):
    need(type(raw) is bytes and len(raw) <= RAW_CAP, 'fixed classifier input cap')
    observations = []
    counts = {}
    offset = 0
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        text = line.decode('utf-8', errors='replace')
        for name, scope, fragment in MARKERS:
            if fragment in text and (not scope or scope in text):
                if name == 'qdf-register-replay-start' and 'data done' in text: continue
                if name == 'qdf-mode2-request' and not re.search(r'Reset\(2\)', text): continue
                timestamp = re.search(r'\[\s*([0-9]+\.[0-9]+)\]', text)
                pid = re.search(r'\[([0-9]+):', text)
                observations.append(dict(marker=name, line=number, byteOffset=offset, byteLength=len(line),
                                         lineSha256=sha(line), printkTimestamp=timestamp[1] if timestamp else None,
                                         printedPid=int(pid[1]) if pid else None))
                counts[name] = counts.get(name, 0) + 1
        offset += len(line)
    return dict(rawBytes=len(raw), rawSha256=sha(raw), markerCounts=counts, observations=observations,
                interpretation='source-associated printed messages only; no automatic per-invocation branch verdict',
                completeKernelRingProven=False, absentMessageProvesAbsentExecution=False,
                currentCallbackBindingProven=False, controllerInstructionReloadProven=False,
                sharedFaultFlagsClearedProven=False, physicalRecoveryProven=False,
                nativeClockMappingProven=False)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan'); p.add_argument('--nonce', required=True); p.add_argument('--boot', required=True)
    p = sub.add_parser('receipt'); p.add_argument('--nonce', required=True); p.add_argument('--boot', required=True); p.add_argument('frame', type=Path)
    p = sub.add_parser('fetch-plan'); p.add_argument('receipt', type=Path)
    p = sub.add_parser('archive'); p.add_argument('receipt', type=Path); p.add_argument('chunks', type=Path); p.add_argument('output', type=Path)
    args = ap.parse_args()
    if args.command == 'plan':
        result = dict(schema=SCHEMA, limits=LIMITS, captureCommand=capture_command(args.nonce, args.boot),
                      liveCalls=0, next='parent validates authenticated envelope, then receipt and fixed chunk plan; no automatic transport')
    elif args.command == 'receipt':
        need(args.frame.stat().st_size <= RESPONSE_CAP and not args.frame.is_symlink(), 'bounded local capture frame')
        result = parse_capture(args.frame.read_bytes(), args.nonce, args.boot)
    elif args.command == 'fetch-plan':
        need(not args.receipt.is_symlink() and args.receipt.stat().st_size <= 16384, 'bounded local receipt')
        receipt = json.loads(args.receipt.read_text()); row = revalidate_receipt(receipt)
        result = dict(schema=SCHEMA, captureAccepted=receipt['captureAccepted'], commands=[
            dict(kind=kind, index=i, hostName=f'{kind}-{i:02d}.txt', command=fetch_command(receipt, kind, i))
            for kind, size in [('raw', row['rawBytes']), ('stderr', row['stderrBytes'])]
            for i in range((size + CHUNK - 1) // CHUNK)], liveCalls=0)
    else:
        need(not args.receipt.is_symlink() and args.receipt.stat().st_size <= 16384, 'bounded local receipt')
        result = archive(json.loads(args.receipt.read_text()), args.chunks, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, UnicodeError, KeyError, TypeError, InvalidOperation) as exc:
        print(json.dumps(dict(schema=SCHEMA, accepted=False, error=str(exc), liveCalls=0)), file=sys.stderr)
        sys.exit(1)
