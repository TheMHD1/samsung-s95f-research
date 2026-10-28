"""Host-only fixed-job lifetime library. No CLI, staging, TLS, retry, or TV default.

The caller freezes a JobSpec and payload manifest before importing live access.
An ambiguous request is never resubmitted. Raw native output is not trial acceptance.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from urllib.request import ProxyHandler, build_opener

ACCESS_SHA256 = "3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5"
HEX = re.compile(r"[0-9a-f]{64}\Z")
BOOT = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z")
STAGE = re.compile(r"/tmp/swu-stream-20261028[a-z]{2}\Z")
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,79}\Z")


def need(ok: bool, label: str) -> None:
    if not ok:
        raise RuntimeError(label)


@dataclass(frozen=True)
class Payload:
    name: str
    size: int
    sha256: str


@dataclass(frozen=True)
class JobSpec:
    stage: str
    dll: str
    boot: str
    dotnet_sha256: str
    payloads: tuple[Payload, ...]
    native_seconds: int
    supervisor_seconds: int
    host_seconds: int
    io_seconds: int = 10

    def validate(self) -> None:
        need(bool(STAGE.fullmatch(self.stage)), "fixed-stage-policy")
        need(self.dll == "SwuStreamTarget.dll", "fixed-entry-policy")
        need(bool(BOOT.fullmatch(self.boot)), "boot-policy")
        need(bool(HEX.fullmatch(self.dotnet_sha256)), "dotnet-pin-policy")
        need(type(self.payloads) is tuple and 1 <= len(self.payloads) <= 12, "payload-count")
        names = []
        for p in self.payloads:
            need(type(p) is Payload and bool(NAME.fullmatch(p.name)), "payload-name")
            need(type(p.size) is int and 0 < p.size <= 8 * 1024 * 1024, "payload-size")
            need(bool(HEX.fullmatch(p.sha256)), "payload-pin")
            names.append(p.name)
        need(len(set(names)) == len(names) and self.dll in names, "payload-unique-entry")
        need(all(type(v) is int for v in (self.native_seconds, self.supervisor_seconds,
                                         self.host_seconds, self.io_seconds)), "deadline-types")
        need(1 <= self.io_seconds <= 10 and self.io_seconds < self.native_seconds <= 1700,
             "native-io-deadline-policy")
        need(self.native_seconds + 10 <= self.supervisor_seconds <= 1750 and
             self.supervisor_seconds + 50 <= self.host_seconds <= 1800, "outer-deadline-policy")

    @property
    def job(self) -> str:
        return self.stage + "/cm-job"

    def canonical(self) -> dict:
        self.validate()
        return dict(stage=self.stage, dll=self.dll, boot=self.boot,
                    dotnet_sha256=self.dotnet_sha256,
                    payloads=[vars(p) for p in self.payloads], native_seconds=self.native_seconds,
                    supervisor_seconds=self.supervisor_seconds, host_seconds=self.host_seconds,
                    io_seconds=self.io_seconds)

    @property
    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.canonical(), sort_keys=True,
                                        separators=(",", ":")).encode()).hexdigest()


def quote(s: str) -> str:
    return shlex.quote(s)


def common(spec: JobSpec) -> str:
    spec.validate()
    return ("set -eu\numask 077\n" +
            f'test "$(cat /proc/sys/kernel/random/boot_id)" = {quote(spec.boot)}\n' +
            f'test ! -L {spec.stage}\ntest -d {spec.stage}\n' +
            f'test "$(stat -c "%u:%g:%a" {spec.stage})" = 0:0:700\n')


def exact_payloads(spec: JobSpec) -> str:
    s = common(spec)
    s += f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {spec.dotnet_sha256}\n'
    for p in spec.payloads:
        path = spec.stage + "/" + p.name
        s += (f'test ! -L {path}\ntest -f {path}\n'
              f'test "$(stat -c "%u:%g:%a:%h:%s" {path})" = 0:0:600:1:{p.size}\n'
              f'test "$(sha256sum {path} | cut -d " " -f1)" = {p.sha256}\n')
    return s


# Read the final ')' separator: process names may contain spaces or ')'. Field
# 22 becomes item 20 after stripping pid+comm. No awk/transport escape coupling.
PROC = '''proc_identity() {
    case "$1" in ''|*[!0-9]*|0) return 1;; esac
    present=1
    if raw=$(cat "/proc/$1/stat" 2>/dev/null); then :
    elif test ! -d "/proc/$1" && test -r /proc/self/stat; then
        present=0; return 0
    else return 1
    fi
    rest=${raw##*) }
    set -- $rest
    state=$1; pgrp=$3; session=$4
    shift 19
    start=$1
    case "$start:$pgrp:$session" in *[!0-9:]*|'') return 1;; esac
}
uptime_seconds() {
    read up ignored < /proc/uptime
    up=${up%%.*}
    case "$up" in *[!0-9]*|'') return 1;; esac
}
'''


def scripts(spec: JobSpec) -> tuple[str, str]:
    """Fixed shell scripts; no caller command or argument interpolation exists."""
    spec.validate()
    j = spec.job
    child = (common(spec) + PROC + f'cd {spec.stage}\n' +
             'pid=$$\nproc_identity "$pid"\ntest "$present" = 1\n' +
             'test "$pgrp:$session" = "$pid:$pid"\n' +
             f'printf "%s|%s\\n" "$pid" "$start" > {j}/child.tmp\n' +
             f'mv {j}/child.tmp {j}/child\n' +
             'uptime_seconds\nlimit=$((up+5))\n' +
             f'while test ! -f {j}/go; do uptime_seconds; test "$up" -lt "$limit" || exit 125; sleep 1; done\n' +
             f'exec /usr/bin/dotnet {spec.stage}/{spec.dll}\n')
    worker = (common(spec) + PROC +
              f'test "$(cat {j}/plan)" = {spec.digest}\n' +
              'supervisor=$$\nproc_identity "$supervisor"\ntest "$present" = 1\n' +
              'test "$pgrp:$session" = "$supervisor:$supervisor"\n' +
              f'printf "%s|%s\\n" "$supervisor" "$start" > {j}/supervisor.tmp\n' +
              f'mv {j}/supervisor.tmp {j}/supervisor\n' +
              f'setsid /bin/sh {j}/child.sh < /dev/null > {j}/stdout 2> {j}/stderr &\n' +
              'launcher=$!\nuptime_seconds\nready_limit=$((up+5))\n' +
              f'while test ! -f {j}/child; do uptime_seconds; test "$up" -lt "$ready_limit" || exit 125; sleep 1; done\n' +
              f'IFS="|" read child expected < {j}/child\n' +
              'test "$child" = "$launcher"\nproc_identity "$child"\ntest "$present" = 1\n' +
              'test "$start:$pgrp:$session" = "$expected:$child:$child"\n' +
              f': > {j}/go\nuptime_seconds\nlimit=$((up+{spec.supervisor_seconds}))\n' +
              'deadline=0\nwhile :; do\n proc_identity "$child"\n test "$present" = 1 || break\n' +
              ' test "$start:$pgrp:$session" = "$expected:$child:$child" || exit 125\n' +
              ' test "$state" != Z || break\n uptime_seconds\n' +
              ' if test "$up" -ge "$limit"; then\n' +
              '  deadline=1\n  kill -9 "-$child" || true\n  break\n fi\n sleep 1\ndone\n' +
              # A D-state task may survive SIGKILL. Do not block forever in wait.
              'terminated=1\nif test "$deadline" = 1; then\n sleep 1\n' +
              ' proc_identity "$child"\n if test "$present" = 1; then\n'
              '  test "$start:$pgrp:$session" = "$expected:$child:$child" || exit 125\n'
              '  if test "$state" != Z; then terminated=0; fi\n fi\nfi\n' +
              'rc=124\nif test "$terminated" = 1; then set +e; wait "$launcher"; rc=$?; set -e; fi\n' +
              f'printf "%s|%s|%s|%s\\n" "{spec.digest}" "$rc" "$deadline" "$terminated" > {j}/exit.tmp\n' +
              f'mv {j}/exit.tmp {j}/exit\n')
    return child, worker


def launch_command(spec: JobSpec) -> str:
    child, worker = scripts(spec)
    j = spec.job
    s = exact_payloads(spec) + 'command -v setsid > /dev/null\n' + f'test ! -e {j}\ntest ! -L {j}\nmkdir {j}\nchmod 700 {j}\n'
    for name, text in (("plan", spec.digest + "\n"), ("child.sh", child), ("worker.sh", worker)):
        s += f"printf %s {quote(text)} > {j}/{name}\nchmod 600 {j}/{name}\n"
    # Every inherited standard handle is redirected before detachment. Root
    # transport pipe readers therefore cannot be held open by this job.
    s += (f'setsid /bin/sh {j}/worker.sh < /dev/null > {j}/supervisor.out 2> {j}/supervisor.err &\n'
          'printf "LAUNCH_SUBMITTED\\n"\n')
    need(len(s.encode()) <= 8192, "launch-command-too-large")
    return s


def job_guard(spec: JobSpec) -> str:
    j = spec.job
    return (common(spec) + f'test ! -L {j}\ntest -d {j}\n'
            f'test "$(stat -c "%u:%g:%a" {j})" = 0:0:700\n'
            f'test ! -L {j}/plan\ntest "$(cat {j}/plan)" = {spec.digest}\n')


def status_command(spec: JobSpec) -> str:
    j = spec.job
    return (job_guard(spec) + PROC +
            f'emit_exit() {{\n test -f {j}/exit\n test ! -L {j}/exit\n'
            f' test "$(wc -c < {j}/exit)" -le 96\n'
            f' printf "EXIT|"; cat {j}/exit\n}}\n'
            f'if test -f {j}/exit && test ! -L {j}/exit; then\n emit_exit\n'
            f'elif test -f {j}/supervisor && test ! -L {j}/supervisor; then\n'
            f' IFS="|" read pid expected < {j}/supervisor\n'
            ' proc_identity "$pid"\n if test "$present" = 0 || test "$state" = Z; then\n'
            # Receipt is committed before supervisor exit. This second bounded
            # read closes the initial receipt-test vs normal process-exit race.
            '  emit_exit\n else\n test "$start:$pgrp:$session" = "$expected:$pid:$pid"\n'
            '  printf "RUNNING|%s|%s\\n" "$pid" "$start"\n fi\nelse\n printf "STARTING\\n"\nfi\n')


def parse_status(text: str, spec: JobSpec) -> dict:
    if text == "STARTING\n":
        return {"state": "starting"}
    m = re.fullmatch(r"RUNNING\|([1-9][0-9]{0,9})\|([1-9][0-9]{0,19})\n", text)
    if m:
        return dict(state="running", pid=int(m[1]), start=int(m[2]))
    m = re.fullmatch(r"EXIT\|([0-9a-f]{64})\|([0-9]{1,3})\|([01])\|([01])\n", text)
    need(m is not None and m[1] == spec.digest and int(m[2]) <= 255, "status-frame")
    return dict(state="exited", exit_code=int(m[2]), deadline=bool(int(m[3])),
                termination_confirmed=bool(int(m[4])), trial_accepted=False)


def stop_command(spec: JobSpec) -> str:
    j = spec.job
    return (job_guard(spec) + PROC +
            f'test ! -L {j}/child\nIFS="|" read pid expected < {j}/child\n'
            'proc_identity "$pid"\nif test "$present" = 1; then\n'
            ' test "$start:$pgrp:$session" = "$expected:$pid:$pid"\n'
            ' test "$state" = Z || kill -9 "-$pid"\nfi\n'
            'printf "STOP_REQUESTED\\n"\n')


def collect_command(spec: JobSpec) -> str:
    """Bounded terminal metadata output only; helper stdout must be reviewed safe."""
    j = spec.job
    return (job_guard(spec) +
            f'test ! -L {j}/exit\ntest -f {j}/exit\n'
            f'test "$(cut -d "|" -f1 {j}/exit)" = {spec.digest}\n'
            f'for f in stdout stderr supervisor.out supervisor.err; do\n'
            f' test ! -L {j}/"$f"\n test -f {j}/"$f"\n'
            f' test "$(stat -c "%u:%g:%a:%h" {j}/"$f")" = 0:0:600:1\n'
            'done\n'
            f'test "$(wc -c < {j}/stdout)" -le 1048576\n'
            f'test "$(wc -c < {j}/stderr)" -le 4096\n'
            f'test "$(wc -c < {j}/supervisor.out)" -eq 0\n'
            f'test "$(wc -c < {j}/supervisor.err)" -eq 0\n'
            f'test ! -e {j}/stdout.safe\ntest ! -L {j}/stdout.safe\n'
            f'test ! -e {j}/stdout.safe.tmp\ntest ! -L {j}/stdout.safe.tmp\n'
            f'''awk 'index($0, "[GC_INFO]") != 1 {{print}}' {j}/stdout > {j}/stdout.safe.tmp\n'''
            f'test "$(wc -c < {j}/stdout.safe.tmp)" -le 4096\n'
            f'mv {j}/stdout.safe.tmp {j}/stdout.safe\n'
            f'printf "STDOUT_BEGIN\\n"; cat {j}/stdout.safe\n'
            f'printf "STDOUT_END\\nSTDERR_BEGIN\\n"; cat {j}/stderr\n'
            f'printf "STDERR_END\\nSUPERVISOR_ERROR_BEGIN\\n"; cat {j}/supervisor.err\n'
            'printf "SUPERVISOR_ERROR_END\\n"\n')


def cleanup_command(spec: JobSpec) -> str:
    """Delete only a closed, exact known job tree; never payloads or raw sink."""
    j = spec.job
    names = "plan child.sh worker.sh supervisor.out supervisor.err stdout stderr supervisor child go exit"
    return (job_guard(spec) + PROC +
            f'test ! -L {j}/exit\ntest -f {j}/exit\n'
            f'IFS="|" read plan rc deadline terminated < {j}/exit\n'
            f'test "$plan" = {spec.digest}\ntest "$terminated" = 1\n'
            f'for identity in child supervisor; do\n'
            f' test ! -L {j}/"$identity"\n IFS="|" read pid expected < {j}/"$identity"\n'
            ' proc_identity "$pid"\n if test "$present" = 1; then\n'
            '  test "$start:$pgrp:$session" = "$expected:$pid:$pid"\n'
            '  test "$state" = Z\n fi\ndone\n'
            f'for p in {j}/* {j}/.[!.]* {j}/..?*; do\n'
            ' if test ! -e "$p" && test ! -L "$p"; then continue; fi\n'
            ' case "${p##*/}" in plan|child.sh|worker.sh|supervisor.out|supervisor.err|stdout|stderr|stdout.safe|stdout.safe.tmp|supervisor|child|go|exit) ;; *) exit 1;; esac\n'
            ' test ! -L "$p"\n test -f "$p"\n'
            ' test "$(stat -c "%u:%g:%a:%h" "$p")" = 0:0:600:1\ndone\n' +
            'rm ' + ' '.join(j + '/' + n for n in names.split()) + '\n' +
            f'rm -f {j}/stdout.safe {j}/stdout.safe.tmp\n' +
            f'rmdir {j}\nprintf "JOB_REMOVED\\n"\n')


class Access:
    """Already-guarded imported persistent access; request submission never retries."""
    def __init__(self, module):
        self.module = module
        self.lock_held = False

    def exec(self, command: str) -> str:
        need(self.lock_held, "access-lock-required")
        need(0 < len(command.encode()) <= 8192, "short-command-size")
        r = self.module.persistent_request(dict(operation="exec", command=command, timeout=10), 25)
        need(all(type(r.get(k)) is int and r[k] == 0 for k in ("uid", "euid", "exit_code")) and
             r.get("timed_out") is False and r.get("stderr") == "", "root-response-rejected")
        need(type(r.get("stdout")) is str and len(r["stdout"].encode()) <= 16384, "root-output-size")
        return r["stdout"]


@contextmanager
def guarded_access(access_path: Path):
    """Explicit live entry: use only in a centrally coordinated reviewed adapter.

    No invocation occurs on module import. No bridge acquisition/bootstrap path.
    Global owner lock remains held across all caller work, including polling.
    """
    need(access_path.name == "s95f-access.py" and not access_path.is_symlink(), "access-path")
    raw = access_path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == ACCESS_SHA256, "access-source-pin")
    module_spec = importlib.util.spec_from_file_location("cm_pinned_access", access_path)
    need(module_spec is not None and module_spec.loader is not None, "access-import")
    module = importlib.util.module_from_spec(module_spec)
    # Load the bytes just hashed instead of reopening through the import loader.
    exec(compile(raw, str(access_path), "exec"), module.__dict__)
    lock_path = module.BASE.parent / "private/s95f-access.lock"
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        guard = subprocess.run(("sudo", "-n", "/usr/sbin/nft", "list", "table", "inet", "samsung_sdb_guard"),
                               capture_output=True, text=True, timeout=5)
        need(guard.returncode == 0 and "tcp dport 26099" in guard.stdout and "drop" in guard.stdout,
             "firewall-guard")
        need(module.route_callback_host(module.TV) == module.CONTROLLER, "route-guard")
        opener = build_opener(ProxyHandler({}))
        with opener.open(f"http://{module.TV}:8001/api/v2/", timeout=5) as response:
            module.check_identity(json.load(response)["device"])
        need((module.BASE / "persistent/control.sock").exists(), "persistent-required")
        need(module.persistent_request({"operation": "status"}).get("state") == "ready", "persistent-ready")
        access = Access(module)
        access.lock_held = True
        fingerprint = access.exec("cat /etc/tizen-release")
        need(f"BUILD_ID={module.BUILD}" in fingerprint.splitlines(), "build-guard")
        try:
            yield access
        finally:
            access.lock_held = False


def save_new(path: Path, record: dict) -> None:
    raw = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


def run(access: Access, spec: JobSpec, evidence: Path, *, monotonic=time.monotonic,
        sleep=time.sleep) -> dict:
    """Single launch and finite status loop. Caller MUST hold guarded_access.

    Evidence dir must be a caller-created private empty directory. No cleanup
    deletes target payloads or provisional plaintext. Ambiguity preserves them.
    """
    spec.validate()
    need(getattr(access, "lock_held", False), "lifecycle-lock-required")
    need(evidence.is_dir() and not evidence.is_symlink() and
         evidence.stat().st_uid == os.geteuid() and
         evidence.stat().st_mode & 0o777 == 0o700 and not any(evidence.iterdir()), "evidence-private-empty")
    command = launch_command(spec)  # Refuse oversized specifications before an intent exists.
    save_new(evidence / "launch-intent.json", dict(spec=spec.canonical(), digest=spec.digest,
                                                   launch_attempts=1, trial_accepted=False))
    deadline = monotonic() + spec.host_seconds
    polls = 0
    try:
        need(access.exec(command) == "LAUNCH_SUBMITTED\n", "launch-reply")
        # Reserve one maximum 25s status request and one 25s conditional stop.
        # The controller's socket timeout bounds attempts, not D-state tasks.
        while monotonic() + 50 < deadline:
            status = parse_status(access.exec(status_command(spec)), spec)
            polls += 1
            if status["state"] == "exited":
                result = dict(status, polls=polls, launch_attempts=1, job_retained=True,
                              job_terminal_confirmed=status["termination_confirmed"],
                              transport_completed=status["termination_confirmed"] and not status["deadline"] and status["exit_code"] == 0,
                              retry_attempts=0)
                save_new(evidence / "terminal.json", result)
                return result
            sleep(min(1, max(0, deadline - monotonic())))
        # A stop request is conditional on exact child PID/starttime/group/boot.
        need(access.exec(stop_command(spec)) == "STOP_REQUESTED\n", "stop-reply")
        raise RuntimeError("host-deadline-stop-requested")
    except BaseException as error:
        save_new(evidence / "reconciliation-required.json", dict(
            error_type=type(error).__name__, launch_attempts=1, retry_attempts=0,
            job_retained=True, trial_accepted=False, remote_supervisor_deadline_seconds=spec.supervisor_seconds))
        raise
