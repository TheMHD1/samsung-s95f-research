# Fixed RT fault-context reader (offline candidate)

This directory contains an offline-built, dry-by-default candidate for two
fixed, read-only vendor-memory requests. It has not been executed on the TV.
Independent review and the final predicate decision are required before any
target use.

## Frozen geometry

The native process permits only these requests, in this order:

| Step | Target | Bus address | Length | Little-endian header |
| --- | --- | --- | ---: | --- |
| context | `0x101` | `0x47010f00` | 64 | `01010000000f014740000000` |
| RT block | `0x101` | `0x47012400` | 256 | `010100000024014700010000` |

Each request is one exact 12-byte bulk OUT header followed by one exact bulk
IN. The resulting sequence is four synchronous bulk operations. The first
short count, exception, timeout, or over-count makes the protocol phase
unknown and forbids the second header (or any other vendor request). There is
no retry, USB reset, write request, gate change, firmware operation, UI action,
or caller-selected target/address/length. Interface release and file-descriptor
close are attempted after failure; they are host-side cleanup, not protocol
recovery.

The fixed boot, sysfs identity, descriptor, usbfs node, FD `statx`, reopened
device descriptor, identity recheck, interface claim/release, and ARM32 ABI
checks are retained from the reviewed D5 reader. Both receive arrays are
allocated before opening USB. A result is accepted only after all four exact
transfers, phase `ReadyForHeader`, release, and close.

## Interpretation boundary

The returned bytes are first reported only as bus contents. The package mapper
supports the conditional correspondence CPU `0x2001....` to bus `0x4701....`
on its non-A-core branch, and both windows lie inside independently reproduced
AP_RTP destination extents. The helper does not sample the live core-tag value,
make the two reads atomic, or prove whole-object/image identity. Offline
interpretation must therefore keep the CPU-alias statement conditional.

The older D7 `fault-context-read-plan.md` was an initial one-window plan made
before the final predicate. It is superseded by
`../finite-onset-logger-20261027g/fault-context-two-window-plan.md`, which fixes
the two geometries above. This README and the manifest describe the final
candidate; the initial note must not be used to schedule a one-window run.

## Host wrapper boundary

`run-once.py` is dry unless `--execute` is explicit and requires the reviewed
manifest SHA plus a fresh absolute output directory. It hash-checks its local
source/build inventory and the pinned `root-with-margin.py` adapter. The
adapter retains the authenticated persistent-only transport and uses a
45-second remote / 75-second host margin.

The wrapper creates one random private target stage, enforces root ownership,
mode 0700 for the directory and 0600 for every file, uploads exactly three
managed runtime artifacts, and runs the zero-I/O target self-test in a
separate completed root call. It then makes exactly one native invocation.
Target shell command text uses actual line feeds and `echo` markers; it does
not contain textual backslash escapes affected by RootAgent quoting.

Every authenticated call is retained in `record.json`. The complete execution
envelope and native stdout/stderr are saved before semantic acceptance. The
native JSON is small and permits only bounded GC diagnostics. Cleanup occurs
only after the envelope, zero exit/stderr, artifacts, all eight recorded
steps, and final `ReadyForHeader` state validate. Failure before that point
leaves the private stage for guarded follow-up; the wrapper never retries.
Successful cleanup first verifies exact five-file inventory, modes, owners,
sizes, and hashes, then removes only those five allowlisted files and that
exact stage directory.

## Offline verification

The native fake-operation suite covers success; preflight/open/FD/identity/
claim faults; negative, zero, short, over-count, and exception outcomes at
each of the four bulk steps; forbidden later traffic; release/close errors;
and bounded descriptor reading. `test-wrapper.py` covers strict native and
transport parsing, empty stderr framing, raw failed-outcome acceptance at the
framing layer, all-step exactness, GC classification, command guards, fixed
dry geometry, and dependency pins. Both suites are run normally and with
Python optimization where applicable. Default native and wrapper invocations
perform zero target operations; local `--execute` refuses the non-ARM32 host.

Use `build-offline.py` to reproduce the source derivation, local build, tests,
and `build-manifest.json`. It uses only the already installed SDK/runtime and
does not contact the TV or network.
