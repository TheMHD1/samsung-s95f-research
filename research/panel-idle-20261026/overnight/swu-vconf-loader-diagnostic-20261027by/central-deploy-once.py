#!/usr/bin/env python3
"""Central one-shot vconf loader diagnostic; no getter or TEEC invocation."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path

STATE = Path(__file__).resolve().parent
HERE = Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/swu-vconf-loader-diagnostic-20261027by')
OUT = STATE / 'target-run-01'
STAGE = '/tmp/swu-vconf-loader-diagnostic-20261027by'
ADAPTER = Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/managed-ui-tab-launch/root-with-margin.py')
if not hashlib.sha256(ADAPTER.read_bytes()).hexdigest() == 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a': raise ValueError('adapter hash')
for name, digest in {'Program.cs':'233ff68dffccfbeeb93e701d3ce32a9e68dd305cc40955f90edc62024811af5c','Guard.cs':'52533463e0961ac3eb304eac929b24972bd7c919ad3b10f785ab4126c30412e1','Support.cs':'754eb9d636955e2525984c984bc595a751c06b2192e7b7838fa53cb131ae1bde','VconfLoaderDiagnostic.csproj':'f056f2d30fb6255bf4036f5ed69efe7d3742899f83479e4466ce23957c03989c'}.items():
    if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest: raise ValueError('source hash')
FILES = {n: (HERE / 'bin/Release/net6.0' / n).read_bytes() for n in
         ('VconfLoaderDiagnostic.dll', 'VconfLoaderDiagnostic.deps.json', 'VconfLoaderDiagnostic.runtimeconfig.json')}
for name, digest in {'VconfLoaderDiagnostic.dll':'45264f7c7d62b2c985870097f0fbb8a59fc8ee1b8e54fb47d6b34b3175d9378e','VconfLoaderDiagnostic.deps.json':'8a2ebe0f8e7f6521909e7c1b3f88090791f9ac07cb09f1245c1e2a503631d94d','VconfLoaderDiagnostic.runtimeconfig.json':'aeb46a15366e38511c192ccf65312442c64e8753b3c16fd2ca0b4cb34a5c59f3'}.items():
    if hashlib.sha256(FILES[name]).hexdigest() != digest: raise ValueError('payload hash')
OUT.mkdir(mode=0o700)
(OUT / 'runner-at-run.py').write_bytes(Path(__file__).read_bytes())
spec = importlib.util.spec_from_file_location('diag_central_root', ADAPTER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
record = {'scope': 'fixed vconf loader and symbol ownership diagnostic; getter never invoked', 'calls': [], 'invocations': 0, 'teec_calls': 0, 'retries': 0}


def guard():
    return ('set -eu\n'
            'test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000\n'
            'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310\n')


def call(command, label):
    return mod.root(command, record, OUT / (label + '.json'))


call(guard() + f'test ! -e {STAGE}\ntest ! -L {STAGE}\numask 077\nmkdir {STAGE}\nchmod 700 {STAGE}\n', 'stage')
for name, data in FILES.items():
    path = STAGE + '/' + name
    call(guard() + f'test ! -e {path}\numask 077\n: > {path}\nchmod 600 {path}\n', 'create-' + name)
    for offset in range(0, len(data), 3072):
        encoded = base64.b64encode(data[offset:offset + 3072]).decode()
        call(guard() + f'test ! -L {path}\ntest "$(wc -c < {path})" = {offset}\nprintf %s \'{encoded}\' | base64 -d >> {path}\n', f'upload-{name}-{offset}')
    call(guard() + f'test "$(sha256sum {path} | cut -d " " -f1)" = {hashlib.sha256(data).hexdigest()}\n', 'verify-' + name)
record['invocations'] = 1
command = guard() + f'umask 077\nset +e\n/usr/bin/dotnet {STAGE}/VconfLoaderDiagnostic.dll > {STAGE}/stdout.txt 2> {STAGE}/stderr.txt\nrc=$?\nset -e\n'
command += f'test "$(wc -c < {STAGE}/stdout.txt)" -le 10000\ntest "$(wc -c < {STAGE}/stderr.txt)" -le 2048\nprintf "DIAGNOSTIC_EXIT=%s\\n" "$rc"\ncat {STAGE}/stdout.txt\nprintf "STDERR_BEGIN\\n"\ncat {STAGE}/stderr.txt\nprintf "STDERR_END\\n"\n'
text = call(command, 'invoke-once')
(OUT / 'diagnostic.txt').write_text(text)
print(text)
