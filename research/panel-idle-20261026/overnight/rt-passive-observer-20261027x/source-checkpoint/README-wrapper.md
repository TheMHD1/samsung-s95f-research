# RTP passive observer — reviewed host-wrapper candidate

This host layer stages and runs the separately pinned native passive observer.
It is dry by default. Nothing in the wrapper build or tests contacts the TV,
root transport, network, or USB device. A live run requires all three explicit
arguments:

```text
--execute --manifest-sha256 <reviewed-wrapper-manifest-sha256> --output <fresh-absolute-directory>
```

The output directory must not already exist. Deployment remains a separate
reviewed action.

## One-shot lifecycle

`run-once.py` pins the existing root transport, its 45-second remote timeout
and 75-second host timeout, the boot ID, target `/usr/bin/dotnet`, the unchanged
native manifest, and every local input. It creates a unique root-owned 0700
stage, uploads exactly the three pinned managed runtime files as 0600 files,
checks their complete inventory and hashes, and runs the native 75-case
zero-I/O self-test.

It then invokes `--execute` exactly once in the foreground. Native stdout and
stderr go to fresh private files. The same root request returns one strictly
framed envelope with the boot/uptime, exit status, bounded sizes, hashes,
complete stage inventory, and base64 bytes. Stdout is capped at 24,576 bytes;
stderr is capped at 2,048 bytes; the authenticated root response remains under
the transport's 64 KiB limit.

Samsung's target .NET runtime can append `[GC_INFO]` diagnostics to stdout.
Both self-test and execute parsers classify only that exact prefix, permit at
most 32 bounded diagnostic lines plus exactly one JSON object, and reject all
other lines. The diagnostics are counted in the final result but never treated
as part of the JSON outcome.

Before launch, target-operation accounting changes from zero to
`inflight_or_unknown`. It remains unknown on any transport, framing, exit, or
native-contract failure. The wrapper saves authenticated native stdout and
stderr before parsing the exit code or JSON. There is no retry and no kill,
reset, write, gate, UI, or recovery operation.

## Accepted outcomes and retained raw bytes

An accepted native result must be terminal, `ReadyForHeader`, released and
closed, with exact read-only counters. The wrapper recognizes only the native
terminal names `AlreadyFaulted`, `TransitionCaptured`, `TimeLimit`, and
`CycleLimit`. It validates onset flags, clean/discard counters, cycle/header/
bulk counts, the bounded role ordering, all window addresses/lengths/hashes,
R's raw triplet decode, and every per-bulk timestamp and transfer result.

`AlreadyFaulted` is accepted only as an onset-missed result containing its
initial R plus one complete sequential post-fault `M,C,H,L,R` set. In
particular, H is retained; the wrapper does not reset or clear the fault.
Transitions at R-start and R-end have distinct validated retained shapes.
Clean time/cycle completion may retain only the final clean cycle and a
deadline-bounded clean partial cycle. `cleanCyclesDiscarded` must equal the
number of completed clean cycles omitted by rolling retention.

Each retained raw window is reconstructed from strict base64, checked against
its declared length and SHA-256, and saved under a unique allowlisted filename.
Samples remain sequential and non-atomic. The wrapper explicitly does not
claim an exact event tuple, a physical cause, or an observed physical picture.

Cleanup is permitted only after the authenticated envelope and accepted native
JSON prove a known `ReadyForHeader` result. It rechecks the exact stage
inventory, sizes, ownership, modes, and hashes before removing exactly the
known files and stage. Rejected or ambiguous runs retain the stage and complete
host call record for audit.

## Offline verification

Run:

```sh
python3 build-wrapper.py
```

The builder verifies that every native file and native manifest is unchanged,
pins the four deterministic fake-native fixtures and all host files, runs the
wrapper suite under normal and optimized Python, validates generated shell
syntax, dry zero-I/O behavior, framing and output bounds, outcome/counter/raw/
timestamp rejection paths, one-execution accounting, rejected-run retention,
and successful guarded cleanup. It emits `wrapper-build-manifest.json` without
rewriting `native-build-manifest.json` or any native source/binary.
