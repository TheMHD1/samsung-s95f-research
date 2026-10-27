# Qualified supervisor port plan

This is an offline implementation plan. It does not clear another logger run,
modify the current helper or wrapper, or authorize TV, UI, controller, USB,
high-bank, persistence, or POFLG activity.

## Evidence and boundary

The marker-only launch qualification in `launcher-qualification-once` completed
with `target_device_operations=0` and `physical_picture_observed=false`. Its
dispatch PID was 6079, while the process that published the atomic handshake
was PID 6083 with process group 6083, session 6083, and start ticks 28325994.
It remained live through the 200 ms recheck, published completion after 3.01
seconds, exited, and left empty launcher stdout and stderr. The exact stage was
then removed only after all seven artifacts and hashes were retained.

Relevant retained hashes are:

- qualifier source: `74d964fa6e80d4834409d4e3b86998c729203c8448a5237b6139e8a7649e87d0`;
- qualification record: `6e94e58bb1336af457c342c8501f659eb5b4d0269f6345f7435b1e93a11d0555`;
- result: `610a87d31cde59520f426300732c51b3c807173a6b04623a0429029b04b4783a`;
- saved marker stat: `8d3e43810482d325fbb2f5f82688388a1ef62bec04201c9625aa8dd1b505ebb5`.

This qualifies the `nohup`/`setsid -f` launcher shape, not the native logger or
USB protocol. Control-v2 remains ambiguous. Absence of its old supervisor,
native child, or staged ready/exit state is necessary but does not expose the
firmware parser phase and is not sufficient proof of clean state. No new
controller traffic may be authorized unless closed-world no-transfer lineage
already exists (for example from D6 or an already-running complete USB trace),
or an independently established controller-parser reinitialization is proven.
That prerequisite is separate and must not be inferred from this source port.

## Current defects to remove

The current onset wrapper has four launcher weaknesses:

1. The supervisor uses `set -u`, so a failed marker command can be followed by
   later commands and potentially by native execution. It is not fail-closed.
2. It invokes `/bin/sh /tmp/.../supervisor.sh`, whereas the target-qualified
   shape treats the mode-0600 staged script as data and passes its exact bytes
   to `/bin/sh -c`.
3. It closes only descriptor 3. It does not close every inherited numeric file
   descriptor above 2.
4. It treats `$!` as the supervisor PID. With `setsid -f`, `$!` is only a
   short-lived dispatch process; the qualified run proved that the actual
   supervisor has a different PID.

The current supervisor also discards launch diagnostics, publishes no boot and
uptime handshake, and does not require the actual supervisor identity to be
live before the launch request returns.

## Exact source changes

All changes belong in a new reviewed copy of
`managed-usb-secondary-logger-onset/run-once.py`; the cleared native DLL and its
protocol must remain byte-identical.

### 1. Make the supervisor fail closed

Change the generated supervisor prologue from `set -u` to `set -eu`, retain
`umask 077`, and require the exact private stage as the current directory.
Before invoking `/usr/bin/dotnet`, it must publish these files through unique
same-directory temporary files, mode 0600, an absent-final check, and then a
same-directory rename. The unique mode-0700 stage has only this writer:

- `supervisor.pid`: its own `$$`;
- `supervisor.stat`: the complete contemporaneous `/proc/$$/stat` row;
- `supervisor.start`: exactly the boot ID and `/proc/uptime` captured after the
  PID/stat files.

Every temporary and final name must be absent before writing. Any failure in
`cd`, creation, chmod, `/proc` read, boot/uptime read, or rename must terminate
the supervisor before the native process is created. The native stdout,
stderr, and PID destinations must also be absent before launch.

Launch the unchanged native command in the background only after all three
handshake files exist. Record its PID atomically, and use an explicit
`if wait "$child"; then rc=0; else rc=$?; fi` construct so `set -e` does not
erase a legitimate nonzero native exit. Preserve the existing bounded output
size/hash completion record, but create `native.exit` through a unique mode-0600
temporary and absent-final check. A failure after child creation may not start
a second child; it must leave the private stage and diagnostics for review.

The supervisor must not contain a retry, device operation, UI operation,
signal, or fallback cleanup path. Native urgent restore remains solely inside
the already-cleared finite helper.

### 2. Treat the staged supervisor as data

Keep `supervisor.sh` mode 0600 and preserve its prelaunch byte count and SHA-256
checks. Do not invoke it as `/bin/sh PATH`. The detached subshell must use the
qualified data form:

```sh
exec /usr/bin/nohup /usr/bin/setsid -f /bin/sh -c "$(cat "$SUPERVISOR")"
```

The script embeds its fixed unique stage path, so it needs no caller-supplied
positional argument. The command substitution occurs inside the detached
subshell after descriptor closure. Absolute executable paths and preflight
`test -x` checks are required for `nohup`, `setsid`, and `/bin/sh`.

### 3. Close all inherited descriptors and retain launch diagnostics

Replace `3>&-` with the target-qualified `closefds` function. It must enumerate
`/proc/self/fd/*`, accept only numeric names, preserve 0, 1, and 2, and close
each numeric descriptor greater than 2 with `eval "exec $n>&-"`. Run it in a
subshell immediately before `exec`.

Before dispatch, atomically create root-owned mode-0600
`supervisor.launch.stdout` and `supervisor.launch.stderr`. Redirect the detached
subshell's stdout and stderr there and stdin from `/dev/null`. Both files become
fixed bounded outputs. Successful qualification requires both to remain empty;
failure evidence must retain their exact size and SHA-256 without interpreting
free-form text as authority.

### 4. Replace launcher-PID trust with an actual-child handshake

Rename the host record field from `launcher_pid` to `dispatch_pid`. `$!` may be
recorded for audit but must never be compared with the supervisor, used for a
signal, or accepted as proof of execution.

Within the same authenticated launch root request:

1. Start the detached subshell once.
2. Poll at 50 ms intervals for no more than one second for all three atomic
   supervisor handshake files.
3. Apply the pinned mode/type guards and tight size ceilings.
4. Parse the saved stat row using the robust final-`) ` split.
5. Require the saved PID to match `supervisor.pid`, be greater than 1, and have
   `PID == process group == session`; bind its start ticks.
6. Read the live `/proc/PID/stat` and require the same PID, group, session, and
   start ticks with non-zombie/non-dead state.
7. Require the handshake boot ID to equal the reviewed boot and its uptime to
   be fresh at the end of the request.
8. Wait 200 ms and repeat the complete live identity check.
9. Return one fixed receipt containing dispatch PID, actual supervisor PID, and
   supervisor start ticks.

Only the actual supervisor identity becomes `record['supervisor_identity']`.
The later status poll must match saved `supervisor.stat` to that identity; it
must no longer require equality with the dispatch PID. READY validation keeps
binding the managed child PID to the actual supervisor's process group and
session. Completion keeps binding `supervisor_pid` to the same actual identity.

If the launch request times out, returns nonzero, lacks any handshake field, or
fails either identity check, classify the run as ambiguous. There is no retry,
second launch, signal, status poll, fetch, or cleanup. The stage and root
response envelope remain retained. A bounded diagnostic branch may include the
private launch stderr bytes in that same failed response, but those bytes do
not relax the ambiguity rule.

### 5. Update fixed inventories and terminal handling

The prelaunch inventory remains the three native files plus `supervisor.sh`.
Postlaunch allowlists must explicitly add the three handshake files and two
launcher diagnostic files, alongside the existing native PID/stdout/stderr,
ready file when published, and exit record. Temporary names are never valid in
a terminal inventory.

At terminal completion, fetch and hash both launcher diagnostic files with
strict size limits before cleanup. An accepted native outcome additionally
requires them to be empty. Preserve all existing native READY/final-outcome
binding, restored RT, post-ring, output-limit, and no-UI checks. Cleanup is
permitted only after a validated terminal outcome and exact host retention of
every fixed artifact; ambiguous or partial states stay untouched.

## Offline verification required before review

Extend the fake root transport and shell-model tests without any target call:

- generated supervisor, launch, status, fetch, and cleanup commands pass
  `/bin/sh -n` and remain below 8192 command bytes; modeled responses remain
  below 65536 bytes;
- normal Python and `python -O` produce identical pass counts and dry mode has
  zero target operations;
- a local marker model proves dispatch PID differs from the `setsid -f` child,
  while the actual child has `PID == PGRP == SID` and stable start ticks at the
  200 ms recheck;
- an inherited descriptor above 2 is absent in the detached child, while
  descriptors 0/1/2 have the specified redirections;
- mode-0600 script data succeeds through `sh -c "$(cat ...)"`; no test or source
  executes `/bin/sh SUPERVISOR_PATH`;
- injected failure at every pre-native handshake create, write, chmod, read,
  and rename point yields no native-start sentinel;
- missing, partial, malformed, stale-boot, stale-uptime, zombie, reused-PID,
  wrong-group/session, changed-start-ticks, and death-before-200-ms handshakes
  all fail before READY/UI and cause no later root request;
- a timeout or malformed launch response performs exactly one dispatch and no
  retry, signal, status poll, fetch, or cleanup;
- the accepted fake path uses distinct dispatch/supervisor/native PIDs, binds
  the native process to the actual supervisor, retains empty launch diagnostics,
  verifies completion, and cleans only after all host artifacts/hashes exist;
- nonempty or oversized launch diagnostics, unexpected terminal names, any
  leftover temporary, absent completion, READY/final hash mismatch, and cleanup
  residue all fail closed with raw evidence retained;
- existing native-core tests remain at their independently cleared counts and
  hashes, proving the port changed orchestration only.

After those tests, an independent reviewer must pin the new wrapper, aggregate
manifest, tests, generated supervisor bytes, and documentation. A later live
control still requires the separate closed-world no-transfer lineage or proven
controller-parser reinitialization prerequisite, an explicit one-run
authorization, a fresh stage/output directory, and no automatic UI action.
