# Managed USB RTP passive observer — native candidate

This directory contains an offline-built, read-only native helper candidate.
Nothing here has been executed on the TV. There is intentionally no host/root
wrapper in this build; deployment and one-shot supervision require a separate
review.

## Fixed contract

Default invocation is dry and performs zero target operations. The only live
CLI is exactly `--execute`, and it refuses unless the process is 32-bit,
little-endian, and the usbfs bulk-transfer structure is 16 bytes. Unknown CLI
arguments return 63 without output. `--self-test` uses fake transport and fake
monotonic clocks only.

The helper inherits the pinned identity, boot, descriptor, character-device,
unbound-interface, claim/release, and endpoint checks from
`managed-usb-rt-fault-context-read`. It hard-codes target `0x101`, interface
2, a two-second timeout for each bulk call, no retry, and these reads:

| ID | address | bytes | header |
| --- | ---: | ---: | --- |
| R | `0x47012400` | 256 | `010100000024014700010000` |
| M | `0x470004a0` | 68 | `01010000a004004744000000` |
| C | `0x47000bc0` | 16 | `01010000c00b004710000000` |
| H | `0x4700d0e0` | 96 | `01010000e0d0004760000000` |
| L | `0x47010f00` | 64 | `01010000000f014740000000` |

One ordinary cycle is exactly `R-start, M, C, H, L, R-end`. Every read is one
exact 12-byte OUT header followed by one exact-length IN. The phase changes to
unknown before each usbfs call and returns to `ReadyForHeader` only after an
exact count. A short, long, failed, or throwing transfer permanently forbids
another vendor header. Release and close are still attempted.

## Finite observer behavior

Production bounds are fixed at 20 seconds, 80 cycles, and a nominal 250 ms
cycle period. Before every new header the native monotonic clock is checked
against the deadline. If a header has already completed, its matching IN is
attempted even when the deadline expires or a clock read fails; the helper
never sleeps with an IN pending. This bounds deadline overshoot to the current
OUT/IN pair: at most two two-second calls. Sleep occurs only in
`ReadyForHeader`.

The first complete R sample is classified only by the exact triplet:

```text
Clean          stop=0, fault=0,      ordinary_gate=1
Faulted        stop=1, fault=0x1001, ordinary_gate=0
Unexpected     anything else
```

An initially faulted R is `AlreadyFaulted`: onset was missed, so the helper
captures one bounded `M,C,H,L,R` set and stops. An unexpected initial or later
R stops without a new header. From a clean start, fault at R-end or at the next
R-start marks a transition. The helper attempts at most one post-fault
`M,C,H,L,R` set. The global deadline still applies between its pairs; if it
expires, the partial post-fault set is retained and the run is not accepted.

The helper never calls the candidate fields an exact event tuple. All windows
are sequential USB observations. Only R's three exact halfwords are decoded;
M, C, H, and L remain raw bytes with hashes and timestamps.

## Bounded retention and output

All response buffers and fixed transfer slots are allocated before preflight
or USB open. During observation, only these captures can remain:

- the last fully clean cycle;
- the transition cycle or transition R-start;
- at most one post-fault set;
- an initial already-faulted R; and
- the current partial capture after a deadline/error.

Each newly completed clean cycle replaces the prior clean cycle. The output
reports `cleanCyclesDiscarded` explicitly. It never emits all 80 cycles or all
960 possible transfer steps. Retained captures include each completed raw
response, short-response prefix, SHA-256, and monotonic timestamps immediately
before and after every bulk call. Global counters cover discarded cycles.

Serialized execute output is capped at 24,576 UTF-8 bytes, comfortably within
the future wrapper's 64 KiB authenticated envelope. The largest self-test
capture currently serializes to 10,541 bytes.

## Safety boundary

The source contains no vendor write, gate arm, restore, reset, threshold
change, retry, fallback address, firmware operation, UI action, or physical
claim. It does not recover a blackout by itself. Managed scheduling and GC are
not hard real-time guarantees, so the before/after timestamps—not the nominal
250 ms period—define the actual sampling interval.

## Offline verification

Using the pinned local .NET 6 runtime:

```sh
python3 build-native.py
```

The build script verifies the local runtime pin and parent-source pins, builds
with zero warnings, runs the 75-case fake native suite, checks the dry
contract, unknown-CLI refusal, host ABI refusal, output bound, and reproducible
managed outputs, then writes `native-build-manifest.json`. It makes no target,
network, USB, or root call.
