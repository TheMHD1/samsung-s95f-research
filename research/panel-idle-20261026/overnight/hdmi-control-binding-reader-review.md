# HDMI-control binding reader offline review notes

The proposed reader remains **unrun**.  This note and its parser do not open a
TV `/proc` path, invoke the generated command, or authorize a capture.

## Added response contract

`parse-hdmi-control-binding.py` accepts only one successful authenticated
connector command for the exact intent command and command SHA-256.  It binds
the fixed model, root UID/EUID, host-assisted persistence field, boot value at
both identity snapshots, AVOC executable/PID/start tick, both hashes, source
device/inode/path identities, map identity repetition, fixed derived storage
and callback arithmetic, ten sampled values, and the exact final completion
marker.  It verifies source maps against the reported device/inode pairs and
requires mapping coverage for the storage, getter, callback, and table reads.

The two five-word snapshots must match exactly.  This checks the repeated
flag/table/callback/main-getter/implementation-entry observations, but remains
non-atomic: a change away and back between observations is still possible.
The returned summary explicitly records `physical_state: unobserved`.

The validator requires the host `client-stderr` sidecar to be empty and accepts
exactly 30 **embedded command-stderr** lines: ten repetitions of the stock
`dd` three-line shape (`1+0 records in`, `1+0 records out`, then
`4 bytes (4 B) copied, <finite> s, <finite> <unit>/s`).  Missing, extra, or
malformed stderr is rejected.
This is accounting for the planned ten four-byte reads, not evidence that any
read occurred.

## Local fixtures

`hdmi-control-binding-reader-tests.py` imports the candidate only to obtain
its command text.  It supplies fabricated connector JSON, result status, and
stderr strings; it does not run that command and never reads `/proc`.
The accepted fixture includes the exact code words `1148733441` and
`4022383920`.  Rejection fixtures cover malformed/extra frame material,
invalid maps, source device mismatch, zero flag, even callback, wrong code
word, changed repeated snapshot, changed boot, nonzero result, and truncated
or extra `dd` stderr accounting.

`hdmi-control-binding-command-tests.py` additionally runs the entire generated
shell command against a fresh temporary proc-like fixture.  It replaces only
the command's two source paths and maps/memory paths with temporary files and
places mock `cat`, `dd`, `stat`, `readlink`, `sha256sum`, and `date` ahead of
the normal PATH.  It never opens a real `/proc` path.  The success fixture
requires all ten local fake `dd` reads; failure fixtures reject duplicate
maps, a `dd` error, truncated read, post-first-snapshot map change, zero flag,
even/wrong callback, wrong process start, source device mismatch, and wrong
hash.  This validates generated-shell handling in a local fixture, not a TV.

Nothing in this review changes the target-execution hold: independent review
of the candidate, parser, and both fixture suites remains required.
