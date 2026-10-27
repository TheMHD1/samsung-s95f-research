# Finite RT block recorder

This derivative keeps the same compile-time-only target0x101/address0x47012400/
256-byte request. Explicit execution takes at most20 samples with nominal250ms
start spacing. No new sample starts beyond5500ms elapsed; each bulk operation
has a two-second timeout. This is a short qualification recorder, not a
continuous logger or a long armed owner-trigger capture.

Each sample independently runs the full preflight/open/FD validation/identity
recheck/claim/OUT12/IN256/release/close path. Its record is emitted after cleanup.
Any transport or cleanup anomaly stops the series before another sample. Bit0
of the little-endian field at+0x0a also stops it, preserving the first observed
asserted sample. There is no retry/reset/protection or payload write operation.

Each record includes monotonic start/end, elapsed time, UTC start, /proc/uptime
before/after, complete transport result, raw bytes and SHA256. Scheduling uses
the actual prior start, preventing catch-up bursts. Slow requests can exhaust
the start budget; that is rejected as deadline rather than reported complete.
The outer25-second root timeout remains an additional failure boundary under
severe scheduling stalls. No hard real-time guarantee is claimed.

Default invocation has zero target I/O.35 tests include the26 native-engine/
stream fixtures and9 series cases: full run, first asserted flag, short OUT,
preflight failure, deadline, backward clock, output failure, release failure
and factory exception. The source/build manifest binds five files and four
recorded host checks; the wrapper is fingerprinted in the runtime record.

One actual smoke completed20/20 samples in4755ms. Start gaps were250ms except
two251ms gaps. First read latency was43ms; subsequent latencies were1–8ms.
All payloads matched the prior256-byte block and all RT flags were zero.
Every interface/FD cleanup and private-stage removal succeeded. Stdout was
23593bytes, below the retained-response cap. The independent reviewer audited
all20 root responses, reassembled the upload and checked every timing/result.

These results qualify only the short recorder at this baseline. They establish
no physical picture state or repair, no absence of polling effects in another
state, and no atomicity across concurrent field updates. A longer armed
recorder needs separately bounded file output, ready/GO handshakes and runtime
qualification. See `../rt-onset-memory-20261027c/progress.md`.
