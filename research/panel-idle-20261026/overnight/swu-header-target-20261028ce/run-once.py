#!/usr/bin/env python3
"""Central fixed metadata adapter runner. Dry default, no automatic retry."""
import argparse
import base64
import zlib
import types
import sys
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ADAPTER = BASE / 'managed-ui-tab-launch/root-with-margin.py'
ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
STAGE = '/tmp/swu-header-20261028ce'
PAYLOAD = {name: HERE / 'bin/Release/net6.0' / name for name in
           ('SwuMetadataAdapter.dll', 'SwuMetadataAdapter.deps.json', 'SwuMetadataAdapter.runtimeconfig.json')}
PAYLOAD['header-envelope.bin'] = HERE / 'header-envelope.bin'
SOURCE_NAMES = ['Core.cs', 'Native.cs', 'Program.cs', 'SwuMetadataAdapter.csproj', 'run-once.py', 'PrivateHeaderFile.cs', 'IntegrationTests.cs', 'HeaderAuthentication.cs', 'framing_model.py', 'HostTests.cs', 'test-runner.py', 'NuGet.Config', 'verify-host.py', 'README.md']


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_host_authentication(raw, public, representation, selected, pad, roots,
                               *, public_sha='ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3',
                               public_crc=0x860be2ed, plaintext_crc=0xcbcf1d91):
    # Optional explicit anchors exist for signed synthetic host fixtures only.
    # The live caller supplies no override and always uses the installed-key pin.
    need(len(raw)==4032 and len(public)==426 and sha(public)==public_sha,'public/input pin')
    tail=raw[-1]; canonical=1<=tail<=16 and raw[-tail:]==bytes([tail])*tail
    raw_fits=zlib.crc32(raw)==plaintext_crc
    padded_fits=canonical and zlib.crc32(raw[:-tail])==plaintext_crc
    need(raw_fits != padded_fits,'unique CRC representation')
    expected_pad=0 if raw_fits else tail
    expected_form='Raw4032' if raw_fits else 'CanonicalPkcs7'
    need(representation==expected_form and pad==expected_pad and selected==4032-expected_pad,'host representation mismatch')
    plain=raw[:selected]
    need(zlib.crc32(public)==public_crc and int.from_bytes(plain[:4],'little')==public_crc,'key CRC')
    need(int.from_bytes(plain[4:6],'little')==256,'RSA signature size')
    key=serialization.load_pem_public_key(public)
    need(key.key_size==2048,'RSA public key size')
    key.verify(plain[6:262],plain[262:],padding.PKCS1v15(),hashes.SHA512())
    model_path=HERE/'framing_model.py';model_raw=model_path.read_bytes()
    need(sha(model_raw)=='e4ff82b67f2b6514f7c97a6bf309fa3dbdcef4a5acb6256724f8b24835c624af','framing model pin')
    module=types.ModuleType('ce_pinned_host_framing');module.__file__=str(model_path)
    sys.modules[module.__name__]=module
    exec(compile(model_raw,str(model_path),'exec'),module.__dict__)
    details=module.model_unpadded(plain,plaintext_crc,module.PublicKeyAnchor(public_crc,256))
    need(details['root_count']==roots,'root count independent match')
    return details


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def manifest():
    paths = [HERE / name for name in SOURCE_NAMES] + list(PAYLOAD.values())
    return {'schema': 'swu-metadata-adapter-deployment-v1', 'boot': BOOT,
            'root_adapter_sha256': ADAPTER_SHA, 'target_dotnet_sha256': DOTNET_SHA,
            'stage': STAGE, 'payload_names': sorted(PAYLOAD),
            'files': {str(p.relative_to(HERE)): {'bytes': p.stat().st_size,
                                                'sha256': sha(p.read_bytes())} for p in paths},
            'scope': 'Exactly one fixed metadata-only TEEC 0/1/2 sequence; authenticated raw4032 header private quarantine only after installed-key CRC/RSA/framing-subset validation. Full schema false, no firmware writing. Native25s/root45s bounds, no retry.'}


def load_root():
    spec = importlib.util.spec_from_file_location('swu_bx_central_root', ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def guard():
    return ('set -eu\n'
            f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
            f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n')


def stage_guard():
    return (f'test ! -L {STAGE}\ntest -d {STAGE}\n'
            f'test "$(stat -c "%u:%g:%a" {STAGE})" = 0:0:700\n')


def exact_guard(names):
    text = stage_guard()
    for name in names:
        path = f'{STAGE}/{name}'
        text += f'test ! -L {path}\ntest -f {path}\n'
        text += f'test "$(stat -c "%u:%g:%a" {path})" = 0:0:600\n'
        if name in PAYLOAD:
            raw = PAYLOAD[name].read_bytes()
            text += f'test "$(wc -c < {path})" = {len(raw)}\n'
            text += f'test "$(sha256sum {path} | cut -d " " -f1)" = {sha(raw)}\n'
    cases = '|'.join(sorted(names))
    text += f'count=0\nfor path in {STAGE}/* {STAGE}/.[!.]* {STAGE}/..?*; do\n'
    text += '[ -e "$path" ] || [ -L "$path" ] || continue\n'
    text += f'case "${{path##*/}}" in {cases}) count=$((count+1));; *) exit 91;; esac\ndone\n'
    return text + f'test "$count" = {len(names)}\n'


def execute(output, digest):
    mpath = HERE / 'deployment-manifest.json'
    need(mpath.is_file() and sha(mpath.read_bytes()) == digest, 'deployment manifest identity')
    need(json.loads(mpath.read_text()) == manifest(), 'source/payload drift')
    need(sha(ADAPTER.read_bytes()) == ADAPTER_SHA, 'root adapter drift')
    need(output.is_absolute() and not output.exists(), 'fresh absolute output directory')
    output.mkdir(parents=True, mode=0o700)
    (output / 'runner-at-run.py').write_bytes(Path(__file__).read_bytes())
    (output / 'deployment-manifest.json').write_bytes(mpath.read_bytes())
    mod = load_root()
    record = {'schema': 'swu-metadata-bounded-run-v1', 'calls': [],
              'invocations': 0, 'target_operation_state': 'not_dispatched', 'retries': 0}

    def call(command, label):
        save(output / 'record.json', record)
        return mod.root(command, record, output / (label + '.json'))

    call(guard() + f'test ! -e {STAGE}\ntest ! -L {STAGE}\numask 077\nmkdir {STAGE}\nchmod 700 {STAGE}\n', 'stage')
    for name, local in PAYLOAD.items():
        raw = local.read_bytes(); remote = f'{STAGE}/{name}'
        call(guard() + stage_guard() + f'test ! -e {remote}\ntest ! -L {remote}\numask 077\n: > {remote}\nchmod 600 {remote}\n', 'create-' + name)
        for offset in range(0, len(raw), 3072):
            chunk = base64.b64encode(raw[offset:offset + 3072]).decode('ascii')
            cmd = guard() + stage_guard() + f'test ! -L {remote}\ntest -f {remote}\n'
            cmd += f'test "$(wc -c < {remote})" = {offset}\n'
            cmd += f"printf '%s' '{chunk}' | base64 -d >> {remote}\n"
            call(cmd, f'upload-{name}-{offset:06d}')
    record.update(invocations=1, target_operation_state='inflight_or_unknown')
    save(output / 'record.json', record)
    cmd = guard() + exact_guard(PAYLOAD)
    cmd += f'umask 077\nset +e\n/usr/bin/dotnet {STAGE}/SwuMetadataAdapter.dll > {STAGE}/stdout.txt 2> {STAGE}/stderr.txt\nrun_exit=$?\nset -e\n'
    cmd += f'test "$(wc -c < {STAGE}/stdout.txt)" -le 4096\ntest "$(wc -c < {STAGE}/stderr.txt)" -le 2048\n'
    cmd += 'printf "RUN_EXIT=%s\\n" "$run_exit"\n'
    cmd += f'printf "STDOUT_BEGIN\\n"\ncat {STAGE}/stdout.txt\nprintf "STDOUT_END\\nSTDERR_BEGIN\\n"\ncat {STAGE}/stderr.txt\nprintf "STDERR_END\\n"\n'
    text = call(cmd, 'invoke-once')
    (output / 'diagnostic.txt').write_text(text)
    matched = re.fullmatch(r'RUN_EXIT=([0-9]+)\nSTDOUT_BEGIN\n(.*?)STDOUT_END\nSTDERR_BEGIN\n(.*?)STDERR_END\n', text, re.S)
    need(matched is not None, 'run framing unknown; stage retained, never retry')
    rc, stdout, stderr = int(matched[1]), matched[2], matched[3]
    rows = [line for line in stdout.splitlines() if not line.startswith('[GC_INFO]')]
    diagnostic = [line for line in rows if line.startswith('SWU_METADATA_DIAGNOSTIC ')]
    auth_rows=[line for line in rows if line.startswith('SWU_HEADER_AUTH ')]
    need(rc == 0 and stderr == '' and len(diagnostic) == 1 and len(auth_rows)==1 and
         rows.count('SELECTOR result=0 value=0') == 5 and len(rows) == 7 and
         all(line.startswith(('SELECTOR ', 'SWU_METADATA_DIAGNOSTIC ', 'SWU_HEADER_AUTH ')) for line in rows),
         'native sequence not accepted; stage retained, never retry')
    need(re.fullmatch(r'SWU_METADATA_DIAGNOSTIC stage=quarantined result=0x00000000 origin=0x[0-9a-f]{8} local=0 calls=1,1,1 counts=[0-9]+,[0-9]+ observed=[0-9]+,[0-9]+ closed=1 released=3 finalized=1 metadata_published=0', diagnostic[0]) is not None,
         'native terminal cleanup/command contract')
    counts=re.search(r' counts=([0-9]+),([0-9]+) observed=([0-9]+),([0-9]+) ',diagnostic[0])
    need(counts is not None,'native count framing')
    update,final,observed_update,observed_final=map(int,counts.groups())
    need(0<=update<=4032 and 0<=final<=4032 and update+final==4032 and
         (update,final)==(observed_update,observed_final),'native actual aggregate counts')
    auth=re.fullmatch(r'SWU_HEADER_AUTH accepted=1 reason=None representation=(Raw4032|CanonicalPkcs7) raw_bytes=4032 selected_bytes=([0-9]+) padding_bytes=([0-9]+) root_count=([0-9]+) present_roots=([0-9]+) checked_leaves=([0-9]+) signature_authenticity_validated=1 framing_subset_checked=1 full_schema_validated=0 metadata_published=0 private_raw_saved=1',auth_rows[0])
    need(auth is not None,'authentication not accepted; retain stage, no retry')
    representation=auth[1]; selected,pad,roots,present,leaves=map(int,auth.groups()[1:])
    need((representation=='Raw4032' and selected==4032 and pad==0) or
         (representation=='CanonicalPkcs7' and 1<=pad<=16 and selected+pad==4032),'representation/count mismatch')
    need(0<=leaves<=present<=roots<=selected-317,'bounded root status')
    record.update(target_operation_state='terminal_native_cleanup_reported',native_exit=rc,
                  signature_authenticity_validated=True,framing_subset_checked=True,full_schema_validated=False)
    save(output/'record.json',record)
    raw_path=STAGE+'/authenticated-header-raw.bin'
    fetch=guard()+exact_guard(list(PAYLOAD)+['stdout.txt','stderr.txt','authenticated-header-raw.bin'])+f'test ! -L {raw_path}\ntest -f {raw_path}\n'
    fetch+=f'test "$(stat -c "%u:%g:%a:%s" {raw_path})" = 0:0:600:4032\n'
    fetch+=f'bx_hash=$(sha256sum {raw_path} | cut -d " " -f1)\nprintf "PRIVATE_RAW_SHA256=%s\\n" "$bx_hash"\nprintf "PRIVATE_RAW_BASE64_BEGIN\\n"\nbase64 {raw_path}\nprintf "PRIVATE_RAW_BASE64_END\\n"\n'
    fetch+=f'test "$(sha256sum {raw_path} | cut -d " " -f1)" = "$bx_hash"\n'
    receipt=call(fetch,'fetch-authenticated-private-header')
    (output/'private-header-envelope.txt').write_text(receipt)
    match=re.fullmatch(r'PRIVATE_RAW_SHA256=([0-9a-f]{64})\nPRIVATE_RAW_BASE64_BEGIN\n([A-Za-z0-9+/=\n]+)PRIVATE_RAW_BASE64_END\n',receipt)
    need(match is not None,'private header framing')
    raw=base64.b64decode(''.join(match[2].split()),validate=True)
    need(len(raw)==4032 and sha(raw)==match[1],'private header copy count/hash')
    # Independent host implementation binds the exact installed PUBLIC key.
    public=(BASE/'swu-public-key-20261028cc/itemsPublicRSAKey.txt').read_bytes()
    details=verify_host_authentication(raw,public,representation,selected,pad,roots)
    need(sum(bool(x['present']) for x in details['records'])==present,'present roots independent match')
    need(sum(bool(x.get('leaf_layout_checked',False)) for x in details['records'])==leaves,'leaf count independent match')
    target=output/'authenticated-header-raw.bin'
    with target.open('xb') as stream:stream.write(raw)
    target.chmod(0o600)
    save(output/'authentication-summary.json',{'representation':representation,'rawBytes':4032,'selectedBytes':selected,'paddingBytes':pad,'rootCount':roots,'presentRoots':present,'checkedLeaves':leaves,'installedKeySignatureVerifiedOnTv':True,'installedKeySignatureVerifiedIndependentlyOnHost':True,'fullSchemaValidated':False,'metadataPublished':False})
    names = list(PAYLOAD) + ['stdout.txt', 'stderr.txt', 'authenticated-header-raw.bin']
    cleanup = guard() + exact_guard(names)
    cleanup+=f'test "$(wc -c < {raw_path})" = 4032\ntest "$(sha256sum {raw_path} | cut -d " " -f1)" = {sha(raw)}\n'
    # Remove only the reviewed fixed stage after the terminal native contract.
    cleanup += 'rm -- ' + ' '.join(shlex.quote(f'{STAGE}/{n}') for n in names) + '\n'
    cleanup += f'rmdir {STAGE}\ntest ! -e {STAGE}\nprintf "STAGE_REMOVED\\n"\n'
    need(call(cleanup, 'cleanup') == 'STAGE_REMOVED\n', 'cleanup contract')
    save(output / 'result.json', {'sequence_completed': True, 'invocations': 1,
                                 'native_diagnostic': diagnostic[0], 'stage_removed': True,
                                 'metadata_validated': False, 'plaintext_saved_privately': True, 'signature_authenticity_validated': True, 'full_schema_validated': False,
                                 'permanent_prevention': False})
    print(json.dumps({'sequence_completed': True, 'invocations': 1, 'stage_removed': True,
                      'metadata_validated': False, 'plaintext_saved_privately': True, 'signature_authenticity_validated': True, 'full_schema_validated': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze-manifest', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    need(not (args.execute and args.freeze_manifest), 'choose one mode')
    if args.freeze_manifest:
        need(args.output is None and args.manifest_sha256 is None, 'freeze arguments')
        save(HERE / 'deployment-manifest.json', manifest())
        print(sha((HERE / 'deployment-manifest.json').read_bytes()))
    elif args.execute:
        need(args.output is not None and re.fullmatch('[0-9a-f]{64}', args.manifest_sha256 or '') is not None, 'execution arguments')
        execute(args.output, args.manifest_sha256)
    else:
        need(args.output is None and args.manifest_sha256 is None, 'dry arguments')
        print(json.dumps({'target_operations': 0, 'execute_required': True,
                          'payload_names': sorted(PAYLOAD), 'metadata_published': False,
                          'retries': 0, 'stage': STAGE}))
