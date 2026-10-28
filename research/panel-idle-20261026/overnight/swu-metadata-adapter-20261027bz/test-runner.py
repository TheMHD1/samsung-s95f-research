#!/usr/bin/env python3
"""No-network orchestration tests; every target request is replaced by a fake."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import types

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('runner_under_test', HERE / 'run-once.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
manifest = HERE / 'deployment-manifest.json'
m.save(manifest, m.manifest())
digest = m.sha(manifest.read_bytes())
tests = 0


def require(value, why):
    if not value:
        raise RuntimeError(why)


class FakeRoot:
    def __init__(self, failure):
        self.failure, self.invocations, self.cleanups, self.calls = failure, 0, 0, 0

    def root(self, command, record, output):
        self.calls += 1
        require(len(command.encode()) <= 8192, 'transport command cap')
        parsed = subprocess.run(['sh', '-n'], input=command.encode(), capture_output=True)
        require(parsed.returncode == 0, 'generated shell syntax')
        if 'base64 -d >>' in command and self.failure == 'upload':
            raise ValueError('injected failed upload')
        if '\nrun_exit=$?' in command:
            self.invocations += 1
            if self.failure == 'framing':
                return 'damaged envelope\n'
            code = 70 if self.failure == 'native' else 0
            selectors = 'SELECTOR result=0 value=0\n' * (4 if self.failure == 'selector' else 5)
            diagnostic = ('SWU_METADATA_DIAGNOSTIC stage=quarantined result=0x00000000 origin=0x00000003 '
                          'local=0 calls=1,1,1 counts=4016,0 observed=4016,0 closed=1 released=3 finalized=1 metadata_published=0\n')
            return f'RUN_EXIT={code}\nSTDOUT_BEGIN\n' + selectors + diagnostic + 'STDOUT_END\nSTDERR_BEGIN\nSTDERR_END\n'
        if '\nrmdir ' in command:
            self.cleanups += 1
            return 'STAGE_REMOVED\n'
        return ''


for failure in ('none', 'upload', 'native', 'framing', 'selector'):
    fake = FakeRoot(failure)
    m.load_root = lambda: fake
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / 'run'
        refused = False
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                m.execute(output, digest)
        except ValueError:
            refused = True
        require(refused == (failure != 'none'), 'trial success/failure')
        require(fake.invocations == (0 if failure == 'upload' else 1), 'at most one invocation')
        require(fake.cleanups == (1 if failure == 'none' else 0), 'ambiguous/failure stage retained')
        if failure == 'none':
            result = json.loads((output / 'result.json').read_text())
            require(result['sequence_completed'] and not result['metadata_validated'] and
                    not result['plaintext_saved'], 'narrow successful claim')
        else:
            require(not (output / 'result.json').exists(), 'no success record after failure')
        tests += 1
fake = FakeRoot('none'); m.load_root = lambda: fake
with tempfile.TemporaryDirectory() as temporary:
    try:
        m.execute(Path(temporary) / 'bad', '0' * 64)
        raise RuntimeError('bad manifest accepted')
    except ValueError:
        require(fake.calls == 0, 'manifest failure precedes target call')
tests += 1
print(json.dumps({'host_orchestration_cases': tests, 'target_operations': 0,
                  'generated_shell_syntax_checked': True}))
