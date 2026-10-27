# Fixed late RTP mode-window reader (offline candidate)

This dry-by-default candidate performs exactly two target-`0x101` vendor
memory reads: bus `0x470004a0`, length `0x44` (68), header
`01010000a004004744000000`; then bus `0x47000bc0`, length `0x10` (16), header
`01010000c00b004710000000`. The protocol has four exact synchronous bulk
steps, each with a 2-second usbfs timeout. It has no address or length
arguments, retry, write request, USB reset, UI action, or firmware change.

The native engine retains the reviewed current-boot ARM32 ABI, sysfs/device/
descriptor identity, FD, claim/release, and close checks. Before each transfer
the phase becomes `Unknown`; only an exact count advances it. A short, error,
exception, or over-count stops all vendor traffic. Release and close are
attempted but are not treated as protocol recovery.

## Transport versus interpretation

A complete 68-byte response with exact framing and final `ReadyForHeader` is
accepted as raw bus evidence. The bytes at returned offsets `0x0a`, `0x0c`,
and `0x40` are decoded as candidate `aa`, candidate `ac`, and a root word.
Conditional image-1 interpretation is accepted only when the same-response
root word equals `0x20010000`.

If the root mismatches, the transport remains accepted: the wrapper saves the
raw 68-byte artifact and hashes, reports `interpretation_accepted: false` and
`root-anchor-mismatch`, then performs the same guarded terminal cleanup. It
does not relabel a fully exact transaction as protocol-unknown and does not
discard the bytes.

The second 16-byte response is always reported only as raw candidate bus
bytes. Byte offset 7 is compared numerically with the first window's u16
mirror candidate at offset `0x22`; the adjacent u16 at `0x24` is reported as
an enable candidate. Agreement is a consistency observation only and does not
promote the second window to a proved CPU alias or recover event-time state.

Even a matching-root result is a late volatile sample. It cannot recover the
mode at the earlier V6 event, prove a physical panel state, establish the
unsampled core tag, or identify the alternate-threshold byte. The CPU
`0x2000...` interpretation remains conditional on the reviewed non-A mapping
and same-window root anchor.

## Host boundary

`run-once.py` requires explicit `--execute`, an exact reviewed manifest SHA,
and a fresh absolute output directory. It uses the pinned 45-second remote /
75-second host root adapter, creates a unique root-owned 0700 stage, enforces
0600 files and exact inventory/hashes, completes a separate zero-I/O target
self-test, and makes one native invocation. Target commands use actual line
feeds and echo markers, avoiding RootAgent textual-backslash framing issues.

The call record is changed from zero to `inflight_or_unknown` before the
active call and to two exact operations only after full native parsing. The
raw envelope and stdout/stderr are retained. Cleanup is allowed only after an
exact closed envelope and a complete known-Ready native outcome; it verifies
and removes only the three staged binaries and two native output files. Any
ambiguous transport leaves the private stage and record for guarded review.

## Offline verification

The native fake suite covers matching-root success, exact root-mismatch raw
acceptance, preflight/open/FD/identity/claim faults, negative/zero/short/over
counts and exceptions at both bulk steps, forbidden later traffic, cleanup
failures, and descriptor bounds. The wrapper suite checks both interpretation
outcomes, raw extents/hashes and decoded offsets, exact eight-step transcript,
strict contiguous envelopes, GC classification, fixed dry geometry, operation
accounting, and pins under normal and optimized Python.

`build-offline.py` uses an empty-source `NuGet.Config`, the already installed
SDK/runtime, and no network. No target execution has occurred for this
candidate. Independent review is required; only the root coordinator may run
it afterward.
