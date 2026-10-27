# RTP event-736 ordinary predicate and diagnostic state

Recorded 2026-10-27 UTC. This is an offline trace of the already copied
selected QD package and retained V6 artifacts. It made no TV, root, USB,
controller, network, UI, reset, threshold, protection, or storage operation.
It covers only the ordinary caller at image-1 VA `0x1e68..0x2040`; it does not
analyze or propose a change to persistence, a high bank, POFLG, a return
guard, or any protection branch.

## Result

The immediate event predicate is now exact. Let `R` be the image-1 root
returned by VA `0x38fc`, let `m` be the selected mode, and let `i=m-1`.
Immediately before the final comparison, the routine obtains:

```text
A[i] = uint32 at CPU RAM 0x2000d0e4 + 4*i
r7   = low16(A[i])
fp   = one selected uint16 field below R
```

It stores `r7` to `R+0x0f06` only for mode 6, or to `R+0x0f08` for every
other mode, then executes:

```text
202a  cmp   r7,fp
202c  ble   203e
202e  uxtb  r0,r4       ; mode
2030  movs  r1,#4
2032  bl    1c0c8
2036  mov.w r0,#0x2e0
203a  bl    c1e0
```

Both compared operands were zero-extended halfwords, so the encoded signed
`ble` has the same ordering as an unsigned 16-bit comparison here. The
ordinary local condition for reaching the two calls is therefore exactly
`low16(A[i]) > fp`. The first call receives `(uint8(mode),4)`; the second
receives the literal `0x2e0`, decimal 736. The common setter prints that
number with `rtp_act_%d`, explaining the retained `rtp_act_736` text. No enum
table or semantic name for 736 was recovered, so this report calls it only a
numeric event/debug argument.

The retained V6 log and final `0x1001` establish that this tail ran during the
observation interval. They do not retain the live `mode`, `r7`, or `fp`, and
they do not establish which physical condition the accumulator represents.

## Actual direct caller and mode selection

There are exactly three halfword-aligned direct `BL` encodings to VA
`0x1e68` in selected image 1, all in the tail of the packed unpacker:

| call VA | mode passed in `r0` | condition at the tail |
| ---: | ---: | --- |
| `0xbfbc` | 4 | `uint16[0x200004aa] == 1` |
| `0xbfd0` | 6 | first condition false and `uint16[0x200004ac] == 1` |
| `0xbfdc` | 1 | both conditions false |

The routine itself implements a mode-2 threshold branch and a fallback for
other values, but this direct-caller census does not show a direct mode-2
call. It is not a whole-program proof against an indirect call.

The two other arguments have continuous provenance from the shared RTP
orchestrator:

```text
VA b6f2: r1 = uint16[0x200004d4]  ; formatter label RGB
VA b6f6: r0 = uint16[0x200004d0]  ; formatter label y
VA b6fa: call selector b7ec

selector preserves y in r5 and RGB in r6
selector passes r2=y, r3=RGB to unpacker bd58
unpacker preserves y in sl and RGB in r6
tail passes r1=y, r2=RGB to predicate 1e68
predicate preserves them in r8 and sb
```

Thus the predicate receives the same `y` and `RGB` scalars printed in the
detailed RTP records. It receives no lane index `x`, packed-B lane `c`,
absolute lane `diff`, or detailed-record counter.

The V6 rows are all labelled `NORMAL`, but V6 did not snapshot
`0x200004aa/0x200004ac` at the event tail. The row label therefore does not,
by itself, prove that the later tail selected mode 1; a flag could change
between the row formatter and the tail.

## Exact `fp` selection

VA `0x38fc` loads the root pointer from CPU slot `0x200004e0`. Reset/scatter
evidence initializes that slot to `0x20010000`; this remains a packaged/reset
provenance, not a fresh CPU-RAM sample at the V6 instant. VA `0x38f4` returns
the fixed context base `0x20000500`, making its byte `+0x6c7` concrete CPU
address `0x20000bc7`.

The comparison threshold loaded into ARM register `fp` is:

| mode | selected halfword relative to `R` |
| ---: | --- |
| 1 | `R+0x24c4` if `byte[0x20000bc7] != 0`, otherwise `R+0x2430` |
| 2 | `R+0x2432` |
| 4 | `R+0x2440` |
| 6 | `R+0x24c4` if `byte[0x20000bc7] != 0`, otherwise `R+0x24c0` |
| other | same selection as mode 1 |

On the reset-established root value, those are image-1 CPU addresses
`0x20012430`, `0x20012432`, `0x20012440`, `0x200124c0`, and `0x200124c4`.
The routine proceeds only when `uint16[R+0x249e] == 1`, then waits for helper
VA `0x35a4` to return zero. A failed gate exits without the accumulator tail,
latch store, or event call.

The retained V6 bus snapshot covers only `0x47012400..0x4701243f`. It has
`0x00c8` at `0x47012430` and zero at `0x47012432`, but these are image-0/AP_RTP
window bytes. They must not be substituted for the image-1 CPU threshold
without a separately established live address-space relation. The snapshot
does not cover the other candidate thresholds.

## Exact accumulator provenance

The four literal pool words used by the ordinary state machine are:

```text
VA 2044  0x2000d0fc  six uint16 state/counter slots q[i]
VA 2048  0x2000d108  six 8-byte history records H[i]
VA 204c  0x2000ba40  six source halfwords s[i] in this routine
VA 206c  0x2000d0e4  six uint32 accumulators A[i]
```

For a call that passes the root gate, the code performs this exact ordinary
update, with normal machine-width wrapping:

```text
i = mode - 1

q[i] = (2 * q[i]) & 0x1f

H[i].h0 = old H[i].h1
H[i].h1 = old H[i].h2
H[i].h2 = old H[i].h3
H[i].h3 = s[i]

if s[i] > uint16[R+0x24a0]:
    q[i] = uint16(q[i] + 1)
    uint16[R+0x24a2] = q[i]
    log("BPFLG :%d  (y:%d / rgb:%d)\n", q[i], y, RGB)

if q[i] not in {8, 9, 10, 12, 24, 25}:
    A[i] = uint32(A[i] + H[i].h0)
    T = uint16(ca10()) if uint16[R+0x24d2] != 0 else uint16(c8a0())
    if A[i] >= T:
        A[i] = A[i] - T

r7 = low16(A[i])
```

The helper at VA `0x1e46` is the exact membership test behind the set shown
above: it returns zero only for `8,9,10,12,24,25`. Both `c8a0` and `ca10`
store their returned halfword at `R+0x0f04`, so `R+0x0f04` is the best local
latch for the `T` used by the most recent invocation. The subtraction occurs
at most once per invocation; this trace does not assume `A[i] < 2*T` or call
the operation a mathematical modulus.

This also explains why no single detailed row can be named as the trigger.
The final value is a scan/context accumulator. The 31 retained rows expose
individual `x`, `c`, and `diff` values, but none of those is an argument to
VA `0x1e68`. The related counters are separate:

| retained/logged item | storage | relation to final predicate |
| --- | --- | --- |
| detailed row `x/c/diff` | per unpacked lane/call | not passed to `0x1e68` |
| detailed row first `%3d` | `uint32[0x2000ba28 + 4*i]` | separate record counter |
| `[RTP:NORMAL][395]` | pre-increment `uint16[0x200004a0]` | separate scan/status counter |
| optional `BPFLG` first `%d` | `q[i]` at `0x2000d0fc + 2*i` | gates accumulator update through the membership test |
| predicate `r7` | low 16 bits of `A[i]` | directly compared with `fp` |

`y` and `RGB` are common between the row formatter and predicate caller, but
within VA `0x1e68` they are only arguments to the optional `BPFLG` text. They
do not feed the accumulator arithmetic or final compare.

## Read-only diagnostic fields while the fault remains latched

The smallest informative CPU-local snapshot is not just `R+0x0f06/0x0f08`.
It should preserve mode selection, all six slots (because V6 did not prove the
live mode), the selected-threshold controls, and the two shared scalars:

| CPU address/range | width | reason |
| --- | ---: | --- |
| `0x200004a0` | 2 | scan/status counter printed as 395 |
| `0x200004aa`, `0x200004ac` | 2 each | direct caller's mode-4/mode-6 selectors |
| `0x200004d0`, `0x200004d4` | 2 each | common `y`/`RGB` diagnostic scalars |
| `0x200004e0` | 4 | live image-1 root pointer `R` |
| `0x20000bc7` | 1 | selects the alternate mode-1/mode-6 `fp` |
| `0x2000ba28..0x2000ba4b` | `0x24` | six row counters followed by six `s[i]` halfwords |
| `0x2000d0e4..0x2000d137` | `0x54` | all six `A`, `q`, and `H` slots |
| `R+0x0f04..R+0x0f09` | 6 | latest `T`, mode-6 `r7`, and non-mode-6 `r7` latches |
| `R+0x2400..R+0x24ff` | `0x100` | fault state plus every `fp` and root control in this trace |

Within the last root range, the especially relevant halfwords are
`+0x240a` (latched `0x1001` in the packaged setter), `+0x2430`, `+0x2432`,
`+0x2440`, `+0x249e`, `+0x24a0`, `+0x24a2`, `+0x24c0`, `+0x24c4`, `+0x24d2`,
and `+0x24d6`. This is a diagnostic inventory, not authorization for a live
read; any CPU-address read path needs its own finite review.

### Keep CPU RAM and the `0x4701...` window separate

The selected AP_RTP configuration positively defines two image-0/window
ranges, `0x47010000..0x470123ff` and `0x47012400..0x470124ff`. Therefore a
fixed read at `0x47010f00..0x47010f3f` would positively remain inside the
configured window and would include window offsets `+0x0f04/+0x0f06/+0x0f08`.
Likewise `0x47012400..0x470124ff` includes the window copies/fields at the
threshold offsets above.

Those bus addresses are not the numeric CPU addresses written by image 1:

| image-1 CPU address on reset-established `R` | corresponding offset in separately proven window |
| ---: | ---: |
| `0x20010f04/06/08` | `0x47010f04/06/08` |
| `0x20012430/32/40/c0/c4` | `0x47012430/32/40/c0/c4` |

The recovered mapper and same-boot observations support the alias hypothesis,
but there is no direct core-tag observation or prior read of
`0x47010f00..0x47010f3f`. A future read there would test the hypothesis; it
must report returned window bytes, not silently relabel them CPU RAM. The V6
`0x47012400` read already proves only its returned image-0/window bytes and
their correlation with the event, not a universal `0x2001 == 0x4701` alias.

For the already qualified `0x4701...` address space, the minimum useful
prospective fault-latched capture is consequently two fixed, read-only
windows—not an exploratory CPU-global read:

1. `0x47010f00`, length 64, to include `+0x0f04`, `+0x0f06`, and `+0x0f08`;
2. `0x47012400`, length 256, to include the event state, all five candidate
   `fp` offsets, and the root controls through `+0x24d6`.

The first would show both possible `r7` latch offsets without requiring the
mode to be guessed. The second would show every possible window-side
threshold and selector in one bounded block. Their values would still be
window-side observations; comparison to the image-1 equations is conditional
on the alias hypothesis. Two sequential reads are also not an atomic
snapshot, and the latches may have been updated by scans after V6. The CPU
global ranges `0x200004..`, `0x2000ba..`, and `0x2000d0..` have no already
qualified direct read in this plan and must not be reached by address
arithmetic alone.

## Bounded conclusion

The ordinary predicate is no longer an unexplained `r7 > fp`: `r7` is the
low half of a per-mode 32-bit accumulator at `0x2000d0e4+4*(mode-1)`, after a
specific history/state update, and `fp` is one of five exact root-relative
halfwords. Mode 6 latches `r7` at `R+0x0f06`; all other modes latch it at
`R+0x0f08`. V6 proves the numeric event path ran, but lacks the CPU-local
snapshot needed to recover the actual mode, accumulator, and selected
threshold after the fact.

This narrows the next diagnostic to read-only state capture. It does not
justify changing a threshold, bypassing the comparison, suppressing the
setter, or inferring physical pixel/electrical units from the software
accumulator.

## Reproduction

`rtp-736-predicate.py` pins the selected package, retained V6 outcome and
ring delta, corrected image mapping, all direct callers, literal RAM bases,
threshold branches, state-machine tail, event calls, and the separately
addressed V6 window values. It uses only Python's standard library:

```sh
python3 rtp-736-predicate.py
python3 -O rtp-736-predicate.py
```

Both modes emit one compact JSON result and perform no external operation.
