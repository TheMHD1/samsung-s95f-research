# Independent review: control-v2 launch lineage

Recorded 2026-10-27 UTC. This is a read-only review of
`control-v2-launch-lineage.md` and its pinned retained artifacts. It made no
TV, root, process, network, USB, controller, UI, or old-script execution.

## Bounded classification

Under the explicitly stated ordinary private-stage assumption—no unrecorded
actor removed output names, replaced or recreated the stage, or modified the
staged program after the guarded launch—the evidence establishes that the
detached managed `--execute` child did **not** execute.

This classification is narrower than “nothing launched.” The outer shell did
assign PID 2667 to one background `setsid` job; `setsid` or a shell process may
have existed briefly. It is also narrower than “no managed program ran”: the
separate, earlier `--self-test` invocation completed and reported zero target
operations. The conclusion concerns only the detached onset helper's
`/usr/bin/dotnet ... --execute` child after call 29.

The classification is conditional rather than an unconditional system-wide
history proof. The retained data is not a whole-system file-access or USB
trace and does not exclude an unrecorded privileged actor that created and
then removed artifacts or removed and recreated the stage.

## Decisive evidence

The original supervisor uses `set -u`, not `set -eu`:

```sh
printf '%s\n' "$$" > supervisor.pid.tmp
mv supervisor.pid.tmp supervisor.pid
cat /proc/$$/stat > supervisor.stat.tmp
mv supervisor.stat.tmp supervisor.stat
rc=0
/usr/bin/dotnet ... --execute > native.stdout 2> native.stderr </dev/null &
```

Consequently, missing `supervisor.pid` and `supervisor.stat` alone do **not**
prove that execution stopped before the dotnet line. A marker write or rename
could fail and the shell could continue because `-e` was absent. The source
audit's final implication from “first marker absent” directly to “native not
launched” is therefore too strong if considered by itself.

The later absence of both `native.stdout` and `native.stderr` supplies the
stronger edge. For the asynchronous dotnet command, the shell applies the
three redirections before it can execute `/usr/bin/dotnet`:

1. open/truncate `native.stdout` for standard output;
2. open/truncate `native.stderr` for standard error;
3. open `/dev/null` for standard input; and
4. only then attempt the dotnet exec.

The launch preflight had just verified a root-owned mode-0700 private stage.
If entered, the supervisor would run as root after `cd` to that stage. If the
first output open failed, dotnet could not execute. If both opens succeeded,
both pathnames would remain even if dotnet were absent, failed immediately, or
the managed program rejected before its first controller call. The supervisor
contains no deletion, the native execute path contains no deletion of these
artifacts, the old wrapper recorded no cleanup, and none of the 71 post-launch polls removes
anything.

At same-boot uptime `112546.91`, the retained inspection found the private
directory still present with exactly its four fixed inputs and neither output
file. Under the no-unrecorded-remover/no-stage-replacement assumption, this
excludes execution of the detached managed command. The missing
`logger.ready` is not used for that conclusion; readiness occurs only after
earlier controller work and would be too late a marker.

## Retained lineage checked

- `control-smoke-v2/record.json` has SHA-256
  `db6046dd91f056c7c0649adea3b933a2bd1399e36d91dd532827d4d96334fd02`
  and contains 101 authenticated calls.
- Call 28 ran only the reviewed `--self-test`, whose result reports
  85/26/59 tests and `targetOperations=0`.
- Call 29 contains one fixed background `setsid` launch and returned
  `LAUNCHER_PID=2667`; it has no success evidence for `setsid`, `/bin/sh`, or
  the supervisor body because launch diagnostics were redirected to
  `/dev/null`.
- Calls 30–100 are 71 observation-only polls across 64.16 seconds. They do not
  launch, signal, retry, truncate, remove, or clean the stage. Their absence
  checks cover `supervisor.stat`, `native.exit`, and `logger.ready`, not the
  two redirection files.
- `control-smoke-v2/missing-completion-metadata.json`, SHA-256
  `aa64bbe1df60332b218163c9cd91b7b93f49610d5df24c1e7e5d5fc9cb972da2`,
  supplies the later same-boot exact directory listing: four inputs, no
  supervisor/native/temp/ready/exit artifact, no PID 2667, and no matching
  managed process at that inspection time.
- The exact reconstructed supervisor is 1,105 bytes, SHA-256
  `2118a377f8a28ed0b11ae9c9bbccd7f8ffa49a519850001ea905e70c05e724bb`,
  and matches the pinned old wrapper's generator for the recorded private
  stage.

The later listing pins sizes rather than fresh hashes of the four retained
inputs and does not record the directory inode. Those gaps are why the
no-replacement/no-unrecorded-remover condition must remain explicit; they do
not weaken the redirection-order inference once that condition is adopted.

## Session lineage versus blanket USB lineage

The retained normal-session action census after the accepted D6
`ReadyForHeader` boundary consists of:

- control-smoke-once self-test and guarded cleanup only;
- control-smoke-v2 staging, zero-operation self-test, the one failed detached
  launch, and observation-only polls;
- the read-only missing-completion inspection;
- UI staging, one pre-send dependency failure, cleanup, stock dependency-file
  read/copy, and the later fixed Apps AppControl qualification and cleanup;
- the marker-only launcher qualification; and
- cached Linux/process metadata reads.

The reviewed records classify those actions as either zero target operations,
ordinary AppControl, marker-only process work, file acquisition, or read-only
Linux metadata. Agents separately reported no additional TV/controller calls
throughout these tasks. With the failed detached `--execute` child excluded by
the private-stage inference, there is no **known** intervening controller USB
transfer in that action census.

Therefore two conclusions must remain distinct:

- **Closed-world normal-session lineage:** if the retained action census is
  complete and the ordinary private stage had no unrecorded remover or
  replacement, D6's final `ReadyForHeader` boundary can be carried across the
  failed v2 attempt. The v2 launch is not an intervening vendor transfer.
- **Blanket system-wide USB lineage:** not proved. These filesystem records do
  not exclude an unknown process, kernel driver, or external USB user outside
  the retained action census. They also do not directly read the firmware's
  current parser phase.

This is the requested bounded classification, not proof against a malicious
root actor or every possible autonomous system component. No reset, probe,
endpoint transaction, or new controller operation follows from it.

## Reviewed source document

`control-v2-launch-lineage.md` SHA-256:
`cd6be83ccbda0bd2e467f035dc477e6e8ee55fc5cbbd9f919f37af0d745de6a9`.
