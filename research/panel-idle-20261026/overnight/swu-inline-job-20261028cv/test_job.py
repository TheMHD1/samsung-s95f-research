"""Offline tests only: fake request adapter and isolated local shell children."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import job


def spec():
    return job.JobSpec('/tmp/swu-stream-20261028cn', 'SwuStreamTarget.dll',
                       '11111111-2222-3333-4444-555555555555', 'a' * 64,
                       (job.Payload('SwuStreamTarget.dll', 1, 'b' * 64),), 11, 21, 71)


class Fake:
    lock_held = True
    def __init__(self, replies):
        self.replies = iter(replies)
        self.commands = []
    def exec(self, command):
        self.commands.append(command)
        r = next(self.replies)
        if isinstance(r, BaseException):
            raise r
        return r


class Tests(unittest.TestCase):
    def test_spec_rejections(self):
        s = spec()
        bad = [dict(stage='/tmp/x;id'), dict(stage='/tmp/../etc'), dict(dll='x.dll'),
               dict(boot='bad'), dict(dotnet_sha256='A' * 64), dict(payloads=[]),
               dict(payloads=(job.Payload('../x', 1, 'a' * 64),)),
               dict(payloads=(s.payloads[0], s.payloads[0])), dict(native_seconds=True),
               dict(native_seconds=1701), dict(io_seconds=11), dict(host_seconds=1801),
               dict(supervisor_seconds=11), dict(host_seconds=40)]
        for changes in bad:
            with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                replace(s, **changes).validate()

    def test_shell_syntax_and_detachment(self):
        s = spec()
        commands = [*job.scripts(s), job.launch_command(s), job.status_command(s),
                    job.stop_command(s), job.collect_command(s), job.cleanup_command(s)]
        for command in commands:
            r = subprocess.run(['/bin/sh', '-n'], input=command, text=True, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertLessEqual(len(command.encode()), 8192)
        self.assertIn('< /dev/null >', job.launch_command(s))
        self.assertIn('2> ', job.launch_command(s))
        self.assertIn('setsid /bin/sh -c "$(cat ', job.launch_command(s))
        self.assertNotIn('setsid /bin/sh '+s.job+'/worker.sh ', job.launch_command(s))
        self.assertIn(hashlib.sha256(job.scripts(s)[0].encode()).hexdigest(), job.launch_command(s))
        self.assertIn(hashlib.sha256(job.scripts(s)[1].encode()).hexdigest(), job.launch_command(s))
        self.assertNotIn('rm -r', job.cleanup_command(s))

    def test_actual_cr_payload_shape_and_launch_size(self):
        p = HERE.parent/'swu-platform-target-20261028cr/deployment-payload.json'
        if not p.exists(): self.skipTest('retained private CR payload manifest absent')
        data = json.loads(p.read_text())
        s = replace(spec(), stage=data['stage'], native_seconds=1700,
                    supervisor_seconds=1750, host_seconds=1800,
                    payloads=tuple(job.Payload(n, v['bytes'], v['sha256'])
                                   for n, v in data['payloads'].items()))
        command = job.launch_command(s)
        self.assertLessEqual(len(command.encode()), 8192)
        self.assertEqual(len(s.payloads), 5)
        r = subprocess.run(['/bin/sh', '-n'], input=command, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_stored_child_hash_guard_rejects_tampering(self):
        s = spec()
        child, worker = job.scripts(s)
        line = next(x for x in worker.splitlines() if x.startswith('test "$(sha256sum '))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'child.sh'; p.write_text(child)
            command = line.replace(s.job, d)
            r = subprocess.run(['/bin/sh', '-c', command], capture_output=True)
            self.assertEqual(r.returncode, 0)
            p.write_text(child+'\n# changed\n')
            r = subprocess.run(['/bin/sh', '-c', command], capture_output=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(r.stderr, b'')

    def test_proc_identity_real_host(self):
        raw = Path('/proc/self/stat').read_text()
        # Python's self differs from the shell's; compare shell against its own
        # stat using a known current process PID/start/group/session tuple.
        tail = raw[raw.rfind(') ') + 2:].split()
        command = job.PROC + f'proc_identity {os.getpid()}; printf "%s|%s|%s\\n" "$start" "$pgrp" "$session"'
        r = subprocess.run(['/bin/sh', '-c', command], capture_output=True, text=True, check=True)
        self.assertEqual(r.stdout, f'{tail[19]}|{tail[2]}|{tail[3]}\n')

    def test_proc_absent_is_quiet_and_other_error_fails(self):
        r = subprocess.run(['/bin/sh', '-c', 'set -eu\n'+job.PROC+
                            'proc_identity 2147483647; printf "%s\\n" "$present"'],
                           capture_output=True, text=True, check=True)
        self.assertEqual(r.stdout, '0\n')
        self.assertEqual(r.stderr, '')
        # Force a failed stat read for a directory that still exists: failure
        # must remain unavailable, rather than claiming process disappearance.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'123'; p.mkdir()
            text = job.PROC.replace('/proc/$1', str(Path(d))+'/$1')
            r = subprocess.run(['/bin/sh', '-c', 'set -eu\n'+text+'proc_identity 123\n'],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(r.stderr, '')

    def test_gc_filter_exact_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'stdout'
            p.write_text('[GC_INFO] x\n'*2000+'result=good\n [GC_INFO] retain\nX[GC_INFO] retain\n')
            s = spec(); command = job.collect_command(s)
            line = next(x for x in command.splitlines() if x.startswith('awk '))
            line = line.replace(s.job, d)
            r = subprocess.run(['/bin/sh', '-c', line], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((Path(d)/'stdout.safe.tmp').read_text(),
                             'result=good\n [GC_INFO] retain\nX[GC_INFO] retain\n')

    def test_status_receipt_rechecked_after_exit_race(self):
        s = spec()
        with tempfile.TemporaryDirectory() as d:
            j = Path(d)
            (j/'supervisor').write_text('2147483647|1\n')
            receipt = f'{s.digest}|0|0|1\n'
            # Receipt is absent for the first test; commit it precisely when
            # proc lookup observes the already-exited supervisor.
            simulated = ('proc_identity() { present=0; printf %s '+job.quote(receipt)+
                         ' > '+str(j/'exit')+'; }\n')
            command = job.status_command(s).replace(job.job_guard(s), 'set -eu\n', 1)
            command = command.replace(job.PROC, simulated).replace(s.job, d)
            r = subprocess.run(['/bin/sh', '-c', command], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stderr, '')
            self.assertEqual(job.parse_status(r.stdout, s)['exit_code'], 0)

    def test_strict_status(self):
        s = spec()
        good = f'EXIT|{s.digest}|0|0|1\n'
        r = job.parse_status(good, s)
        self.assertFalse(r['trial_accepted'])
        self.assertTrue(r['termination_confirmed'])
        for raw in [good+'noise\n', good.replace(s.digest, '0'*64),
                    good.replace('|0|0|1', '|256|0|1'), 'RUNNING|0|1\n',
                    'RUNNING|1|0\n', 'STARTING', good.replace('|0|0|1', '|0|2|1')]:
            with self.subTest(raw=raw), self.assertRaises(RuntimeError):
                job.parse_status(raw, s)

    def test_run_one_dispatch(self):
        s = spec()
        fake = Fake(['LAUNCH_SUBMITTED\n', 'STARTING\n', 'RUNNING|12|345\n',
                     f'EXIT|{s.digest}|0|0|1\n'])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            result = job.run(fake, s, out, monotonic=lambda: 0, sleep=lambda n: None)
            self.assertEqual(len(fake.commands), 4)
            self.assertEqual(result['launch_attempts'], 1)
            self.assertTrue(result['transport_completed'])
            self.assertFalse(result['trial_accepted'])
            self.assertEqual((out/'launch-intent.json').stat().st_mode & 0o777, 0o600)
            self.assertTrue((out/'terminal.json').exists())
            with self.assertRaises(RuntimeError):
                job.run(fake, s, out)

    def test_ambiguous_launch_no_resubmit(self):
        fake = Fake([TimeoutError()])
        with tempfile.TemporaryDirectory() as d, self.assertRaises(TimeoutError):
            try:
                job.run(fake, spec(), Path(d))
            finally:
                self.assertEqual(len(fake.commands), 1)
                self.assertTrue((Path(d)/'reconciliation-required.json').exists())

    def test_rejected_reply_no_resubmit(self):
        for reply in ['WRONG\n', 'LAUNCH_SUBMITTED\nnoise']:
            fake = Fake([reply])
            with tempfile.TemporaryDirectory() as d, self.assertRaises(RuntimeError):
                job.run(fake, spec(), Path(d))
            self.assertEqual(len(fake.commands), 1)

    def test_host_deadline_conditional_stop(self):
        s = spec()
        times = iter([0, 70])
        fake = Fake(['LAUNCH_SUBMITTED\n', 'STOP_REQUESTED\n'])
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(RuntimeError, 'host-deadline'):
            job.run(fake, s, Path(d), monotonic=lambda: next(times))
        self.assertEqual(len(fake.commands), 2)
        self.assertIn('expected:$pid:$pid', fake.commands[1])

    def test_lock_required(self):
        fake = Fake([])
        fake.lock_held = False
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(RuntimeError, 'lock'):
            job.run(fake, spec(), Path(d))
        self.assertEqual(fake.commands, [])

    def test_access_rejects_bad_root_frames(self):
        class Module:
            def __init__(self, frame): self.frame = frame; self.calls = 0
            def persistent_request(self, request, timeout): self.calls += 1; return self.frame
        good = dict(uid=0, euid=0, exit_code=0, timed_out=False, stdout='ok\n', stderr='')
        for patch in [dict(uid=1), dict(euid=1), dict(exit_code=1), dict(timed_out=True),
                      dict(uid=False), dict(stderr='bad'), dict(stdout='x'*16385)]:
            m = Module(dict(good, **patch)); a = job.Access(m); a.lock_held = True
            with self.assertRaises(RuntimeError): a.exec('echo fixed')
            self.assertEqual(m.calls, 1)
        m = Module(good); a = job.Access(m)
        with self.assertRaises(RuntimeError): a.exec('echo fixed')
        self.assertEqual(m.calls, 0)

    def test_isolated_supervisor_success_and_deadline(self):
        # Production scripts are syntax checked unchanged above. Here only the
        # environmental preamble/stage and fixed helper are replaced: no TV.
        # This executes real setsid, /proc PID binding, atomic receipts and kill.
        s = spec()
        for deadline in [False, True]:
            with self.subTest(deadline=deadline), tempfile.TemporaryDirectory() as d:
                stage = Path(d); j = stage/'cm-job'; j.mkdir(mode=0o700)
                (j/'plan').write_text(s.digest+'\n')
                child, worker = job.scripts(s)
                child_hash = hashlib.sha256(child.encode()).hexdigest()
                prefix = job.common(s)
                child = child.replace(prefix, 'set -eu\numask 077\n', 1).replace(s.stage, str(stage))
                worker = worker.replace(prefix, 'set -eu\numask 077\n', 1).replace(s.stage, str(stage))
                child = child.replace(f'exec /usr/bin/dotnet {stage}/{s.dll}',
                                      'exec /bin/sleep 6' if deadline else 'exit 7')
                worker = worker.replace(child_hash, hashlib.sha256(child.encode()).hexdigest())
                if deadline: worker = worker.replace('limit=$((up+21))', 'limit=$((up+1))')
                (j/'child.sh').write_text(child); (j/'worker.sh').write_text(worker)
                with (j/'supervisor.out').open('wb') as out, (j/'supervisor.err').open('wb') as err:
                    p = subprocess.Popen(['/usr/bin/setsid', '/bin/sh', '-c', (j/'worker.sh').read_text()],
                                         stdin=subprocess.DEVNULL, stdout=out, stderr=err)
                    p.wait(timeout=12)
                self.assertEqual(p.returncode, 0, (j/'supervisor.err').read_text())
                receipt = job.parse_status('EXIT|'+(j/'exit').read_text(), s)
                self.assertEqual(receipt['deadline'], deadline)
                self.assertTrue(receipt['termination_confirmed'], (receipt, (j/'supervisor.err').read_text()))
                self.assertEqual(receipt['exit_code'], 137 if deadline else 7)


if __name__ == '__main__':
    unittest.main()
