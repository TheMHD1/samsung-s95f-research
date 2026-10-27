# Independent review: control-v3 launch receipt and terminal retrieval

Recorded 2026-10-27 UTC. This is an offline review of the retained
`control-smoke-v3/record.json`. It made no TV, root, network, USB, controller,
process, UI, reset, signal, retry, cleanup, or old-helper call.

## Classification

The launch did not fail its target-side handshake checks. It failed only in
the host parser because one expected newline was returned as the two literal
ASCII bytes backslash and `n`.

An exact one-delimiter normalization is sufficient and bounded. After first
authenticating the original response and preserving it unchanged, replace the
single exact byte sequence (`5c 6e` is one literal backslash followed by
lowercase `n`):

```text
\nHANDSHAKE_STAT_BEGIN<LF>
```

with:

```text
<LF>HANDSHAKE_STAT_BEGIN<LF>
```

only when every pinned condition below holds. The normalized 582-byte receipt
passes the original `parse_launch` function unchanged. This recovery validates
the already-completed same-request handshake; it does not authorize a second
launch, infer the native outcome, or relax arbitrary diagnostic text.

Because the actual supervisor was running and the supervisor starts the native
child immediately after publishing its handshake, the native helper may have
performed controller transfers. Protocol phase remains unknown until the
finite terminal outcome is fetched and validated. No further USB request is
permitted merely from the recovered launch receipt.

## Raw record and envelope verification

`control-smoke-v3/record.json` is 30 authenticated calls, SHA-256
`fed51d0624c3c627e3cb49e40fa03a588c0314c9e06cff95fb9189e6b4d518f7`.
Its last call has these retained properties:

- logical command length 7,879 bytes;
- no host timeout and transport exit zero;
- authenticated root response with UID/EUID zero;
- exactly one echoed command, byte-equal to the requested command;
- remote exit zero, `timed_out=false`, and empty remote stderr; and
- 583 bytes of stdout, SHA-256
  `7ab528eda154b96a0a1e3878302dcd6f4a36fdc05c0fd082f4d7a52a18e60d3b`.

The pinned root transport's original `validate_response` accepts the raw
envelope and returns those exact 583 stdout bytes. The raw response contains
exactly one backslash byte. Its prefix is exactly:

```text
LAUNCH_ACK 9136 9140 28569437\nHANDSHAKE_STAT_BEGIN<LF>
```

There is exactly one occurrence of the full malformed delimiter and no other
backslash available for a broader rewrite. The remaining framed markers are
present once each and in order.

The logical shell command contains a single `\n` escape in the `printf`
format. The retained root-agent source constructs `/bin/sh -c` through
`QuoteArgument`, which doubles backslashes inside its double-quoted argument.
The resulting shell format emits literal `\n`; the authenticated stdout
demonstrates that exact transport interaction. The wrapper's parser expected a
real line break. No target handshake predicate depends on that final rendering:
all predicates precede the `printf`, and the remote command exited zero.

## Exact normalization acceptance

Recovery is acceptable only if all of these checks pass:

1. Pin the raw record SHA-256 and validate the unmodified authenticated
   response against its exact echoed command.
2. Require the raw stdout length and SHA-256 above, no carriage return or NUL,
   exactly one backslash byte, and exactly one malformed delimiter.
3. Require that delimiter immediately follows the anchored ACK tuple
   `LAUNCH_ACK 9136 9140 28569437` and immediately precedes the unique
   `HANDSHAKE_STAT_BEGIN` marker.
4. Perform that one replacement in memory only. Preserve the raw record and
   raw stdout unchanged.
5. Require normalized length 582 and SHA-256
   `aaf726531fa01b1841df1d73061542e6b88ae62fdaa3231cef6b9f328c167b31`.
6. Pass the normalized string to the original hash-pinned wrapper's
   `parse_launch`; do not introduce a permissive alternate parser.

The unchanged parser then returns:

```text
dispatch PID     9136
supervisor PID   9140
state            S
process group    9140
session          9140
start ticks      28569437
start uptime     114277.76 426562.77
receipt uptime   114278.03 426563.49
```

The target-side command had already checked the saved stat, live stat, boot,
PID/group/session/start-tick equality, repeated the live check after 200 ms,
and enforced handshake freshness. Its zero exit is part of the authenticated
response. Offline decoding independently produces:

- saved stat: 250 bytes, SHA-256
  `2f709d4eb77f7988acc7b970069c9a6bdecbf6e7aff22cfe4661de7ace71a6db`;
- saved start: 69 bytes, SHA-256
  `7806fd9e6947c58f15da931b6a88947df2fd07cbea3e914431e717ff2e62778f`;
- boot ID `00000000-0000-4000-8000-000000000000`; and
- receipt minus start uptime 0.27 seconds.

These facts recover the original handshake classification only. They do not
say whether native READY, urgent restoration, release/close, or terminal
cleanup occurred.

## Bounded read-only terminal retrieval

The native helper has a fixed 20-second observation hold and 45-second
ordinary deadline. Artifact retrieval is eligible only after target uptime
`114322.76`, more than 45 seconds after the saved supervisor start. Retrieval
must not invoke the DLL, run a self-test, open a device, reset anything, signal
a process, retry the launch, or remove the stage.

The reviewed read-only sequence is:

1. **One terminal census.** In one authenticated root read, recheck the same
   boot ID and the exact root-owned mode-0700 stage. Enumerate only the fixed
   four input names and ten possible output names. For every existing name,
   reject symlinks and record type, UID/GID, mode, and size; re-hash the four
   immutable inputs. Also retain target uptime. Do not hash a possibly active
   output before finding the atomic exit record, and do not use or modify any
   temporary file.
2. **Stop on non-terminal state.** If `native.exit` is absent after the finite
   deadline, or if any unexpected name or `*.tmp` is present, retain the census
   and stop. Do not poll again, retry, signal, clean, or issue controller
   traffic. A READY file without a valid exit is not restoration proof.
3. **Fetch small terminal metadata.** If `native.exit` exists, read only the
   fixed bounded files `supervisor.pid`, `supervisor.stat`,
   `supervisor.start`, `native.pid`, `native.exit`, and, when present,
   `logger.ready`; fetch `supervisor.launch.stdout` and
   `supervisor.launch.stderr` as bounded base64. Bind the saved supervisor
   bytes to the recovered handshake and require the exit record's
   `supervisor_pid=9140`, same boot, integer child PID/exit, and bounded
   stdout/stderr counts and hashes.
4. **Fetch native outputs by terminal contract.** Only after the valid exit
   record, read `native.stdout` once with its exact recorded byte count and
   SHA-256 guard, and `native.stderr` once with its exact corresponding guards.
   Keep stdout at or below 50,000 bytes and stderr at or below 2,048 bytes.
   Direct stdout retrieval avoids base64 expansion approaching the root
   response ceiling; diagnostics remain base64-framed because they are small.
5. **Validate entirely offline.** Parse the exact native stdout with the
   existing native parser and `validate_outcome`; bind child PID, exact READY
   JSON/hash, protocol steps, restore result, release/close, output artifacts,
   and final protocol phase. Any inconsistency leaves phase unknown.
6. **Retain the stage.** Even an accepted terminal result is not cleanup
   authorization in this recovery. Preserve all target artifacts until the
   recovered record and an independent runtime audit are complete.

The census and fetches are ordinary reads of already-produced files. They do
not change controller state. The first anomaly ends retrieval; there is no
fallback parser beyond the exact delimiter normalization and no second native
invocation.

## Fixed inventories

Expected inputs:

- `ManagedUsbSecondaryLoggerOnset.dll`
- `ManagedUsbSecondaryLoggerOnset.deps.json`
- `ManagedUsbSecondaryLoggerOnset.runtimeconfig.json`
- `supervisor.sh`

Possible terminal outputs:

- `supervisor.launch.stdout`
- `supervisor.launch.stderr`
- `supervisor.pid`
- `supervisor.stat`
- `supervisor.start`
- `native.pid`
- `native.stdout`
- `native.stderr`
- `native.exit`
- `logger.ready`

The stage is
`/tmp/researcher-usb-onset-cf319c141c8141698db46d55634de752`. The aggregate
manifest is
`aa4fc99a5cd22f86736e49487322b1c6aa6996eae482c8fda3a1971049b386d6`;
the wrapper is
`25b942ae2dbca8b210d9b195bb79b2b509d7501825e0b8d107ddc718911b6bd6`;
the root adapter is
`bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a`.

## Disposition

The original same-request supervisor handshake is recoverable through one
exact, hash-pinned delimiter correction. This clears only the receipt framing
failure. Native execution likely began, so controller protocol phase is
**unknown pending a valid finite terminal outcome**. The bounded next action is
read-only artifact retrieval as specified above, never a launch retry or new
controller transaction.
