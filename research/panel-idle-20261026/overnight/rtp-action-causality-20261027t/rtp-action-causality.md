# RTP event action causality: latch, emergency action, and output boundary

Recorded 2026-10-27 UTC. This is a bounded offline analysis of already
retained package bytes and captures. It made no TV, root, USB, controller,
network, UI, reset, firmware, storage, MMIO, or display operation. It does not
propose a bypass, threshold change, protection change, return-guard change, or
firmware patch.

## Result

The captured `rtp_act_736` event is not itself a direct panel-off call.
Image 1 performs two separate software actions:

1. `0x1c0c8(mode, 4)` ORs action bit `0x0004` into one of three mode-state
   halfwords; and
2. `0xc1e0(736)` sets the common fault state and appends two diagnostic lines.

Image 0 has a recurring poll capable of consuming the second action's window
bit. If that poll observes byte `+0x240a` set, it enters the shared
selector-`0x10` emergency handler.
That handler is materially more than reporting: before storing host-visible
status `0x10`, it tears down interrupt resources and performs exact MMIO
writes. The trace stops at two subsequent calls into the excluded storage
boundary and does not follow the later return-guard branch.

This establishes a concrete software path from the numeric predicate to an
emergency control state. It still does **not** establish a commanded physical
panel shutdown. None of the exact MMIO registers has a recovered hardware
name binding it to panel enable, a panel rail, reset, scan, timing, PWM, or
pixel output. The two `rtp_act_736` lines prove only that the image-1 setter ran
while its ring logger was enabled; they do not prove that image 0 polled the
bit, that the emergency handler ran, or that any physical output changed.

The later same-boot host status `0x10` is stronger than the log alone, but its
origin is not unique. In the selected package, every direct selector-`0x10`
entry executes the selector-specific action before the common selector store
returned by the host status command. Subject to the still-open executing-image
boundary, that status is evidence that *some* selector-`0x10` software action
completed far enough to store `0x10`. Two other direct selector-`0x10` call
sites (`0x9834` and `0x9862`) compete with the recurring poll at `0x214f2`.
The later status therefore does not prove V6 caused the common-handler entry,
and it does not prove the MMIO registers' physical effect.

## Corrected address convention and inputs

The selected package is:

```text
../selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
size   5242880
SHA256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

Image 0 uses `FILE = VA + 0x200`; image 1 uses `FILE = VA + 0x40200`.
Some older reports used image-0 labels higher by `0x200`. Thus their
`0xb860`, `0x14b10`, and `0x25d24` are corrected here to `0xb660`,
`0x14910`, and `0x25b24`.

The required prior traces were read first:

* `finite-onset-logger-20261027g/rtp-act-736-trace.md`;
* `finite-onset-logger-20261027g/rtp-736-predicate.md`; and
* `tcon-research/qd-rtp-primary-event-input-provenance.md`.

The retained late fault-state windows used below are
`finite-onset-logger-20261027g/fault-context-after-v6/{context,rt}.bin`, with
SHA-256 `0683bb72...f2439` and `91055b0c...79f9`. A much later read under
`current-host-health-20261027v/rt-context-once/` returned byte-identical
windows, 6,804.94 seconds later. Equality proves stable returned bytes over
that interval, not event-time atomicity or a universal absence of writers.

## Image-1 action helper retains a mode bucket

The event tail is exact:

```text
202a  cmp   r7, fp
202c  ble   203e
202e  uxtb  r0, r4       ; mode
2030  movs  r1, #4       ; action bit
2032  bl    1c0c8
2036  mov.w r0, #0x2e0  ; decimal 736
203a  bl    c1e0
```

`0x1c0c8..0x1c12b` obtains root `R` and performs only a halfword
read/OR/write:

| mode | destination | operation |
| ---: | ---: | --- |
| 1 | `R+0x2486` | `u16 |= 0x0004` |
| 2 | `R+0x2488` | `u16 |= 0x0004` |
| 4 | `R+0x248c` | `u16 |= 0x0004` |
| 6 | `R+0x248c` | `u16 |= 0x0004` |
| other | none | return |

This retains mode 1 and mode 2 distinctly, but deliberately merges modes 4
and 6. It contains no call, MMIO access, transfer, or output operation.

A finite halfword-aligned direct-call census in selected image 1 finds five
calls to this helper. VA `0xc640` passes action bit 2. VAs `0x2032`,
`0xc78a`, `0xc7d0`, and `0xc826` all pass action bit 4 before their respective
common event setters. The bounded explicit-offset census finds only:

* the pre-scan clear at `0xbad8..0xbae4`, which clears `+0x2486`, then
  `+0x2488`, then `+0x248c` by arithmetic;
* the ordinary wrapper's read/OR-1/write updates at `0xbc56..0xbc64`,
  `0xbc88..0xbc96`, `0xbcc0..0xbcce`, and `0xbd00..0xbd0e`; and
* `0x1c0c8` itself.

No explicit fixed-offset use in that bounded image-1 census tests action bit
4 or consumes it as an output command. This is a finite decoded-code result,
not a whole-program absence proof against computed addressing, bulk copies,
interrupt code, or another image.

## Why the action fields can remain readable after the fault

The ordinary caller at `0x4446` invokes `0xc250`. That function makes byte
`0x200004d8` equal one only while both `R+0x2400 == 0` and
`R+0x240e == 1`; otherwise it writes zero. It then passes that byte as `r0`
to `0xb644` at `0xc2e6`.

At `0xb6a6..0xb6a8`, `0xb644` branches directly to its finalization block
when this argument is zero. The skipped region includes the only direct call
to the pre-scan clear (`0xb6ce -> 0xb9f4`) and the path through
`0xb7ec -> 0xbd58 -> 0x1e68` that can update the predicate/action fields.
The common setter makes exactly that zero condition by storing
`R+0x2400=1` and `R+0x240e=0`.

Therefore, on this directly traced ordinary path, the next pass after the
fault suppresses both the RTP scan/predicate path and its action-field clear.
Other writers and reset remain possible; this is not a lifetime persistence
claim.

The late returned RT window contains a retained action mark:

```text
R/window +0x2486 = 0x0007   (bits 0, 1, and 2 set)
R/window +0x2488 = 0x0000
R/window +0x248c = 0x0000
R/window +0x2400 = 0x0001
R/window +0x240a = 0x1001
R/window +0x240e = 0x0000
```

Bit `0x0004` appears only in the mode-1 bucket in that late sample. This is
consistent with a mode-1 event hypothesis, but it does **not** narrow V6's
event mode. There was no pre-V6 read of these action fields, the only ordinary
clear is conditional, and four distinct direct event sites can OR action mask
4. The same late capture has window threshold `+0x24c4=40`, context score
`+0x0f08=44`, and alternate selector byte `+0x6c7=1`, a numerically
consistent `44 > 40`. It still cannot identify which event set the mark or
recover V6's live operands. The samples were taken about 1,927 seconds after
V6; their byte-identical later repetition strengthens retention only, not
freshness or event-time simultaneity.

## `0xc1e0`: fault latch and diagnostic text, not output control

`0xc1e0..0xc211` performs this complete direct sequence:

```text
R+0x2400 <- 1
R+0x240e <- 0
R+0x240a <- 0x1001
log("rtp_act_%d\n", 736)
log("rtp_act_%d\n", 736)
```

The log sink `0x1b8c8` writes formatted bytes to the secondary ring only when
logger gate `R+0x2406 bit0` is set. It has no edge to the image-0 emergency
handler. Consequently, two captured lines prove the setter reached both log
calls; they are not acknowledgements from an output block.

## Downstream image-0 emergency action

Image 0's recurring poll `0x214d4..0x21511` reads bit 0 of window byte
`0x4701240a`. When set, it logs `RT-P activate!` and calls common entry
`0xb660(selector=0x10, message)`.

For selector `0x10`, the common entry runs, in order:

1. interrupt/resource teardown at `0x96d8`, including NVIC clear-enable
   writes for six runtime-selected IRQ records;
2. selector-specific action `0x14910(0x10)`;
3. common selector store `0x2b764(0x10)`, which is what host status selector
   8 later returns.

The `0x10` arm of `0x14910` clears a second-object halfword `+8`, calls
`0x25b24(1)`, stores `0x10` at MMIO `0x4013400c`, and then makes two calls
before the common selector store. Those two calls are the explicit boundary
of this analysis; their storage behavior is not traced here. Within
`0x25b24(1)`, the final exact stores are:

```text
0x40132010 <- 0x00000080
0x40131010 <- 0x00000004
```

Earlier helpers also store `8` at `0x40130010` and, conditionally, `0x200`
at `0x40132010`. These are genuine hardware-address writes. No retained
register description assigns them a display-output meaning.

The subsequent storage and return-guard branches are deliberately outside
this report. No conclusion here depends on their behavior.

## What is proved versus what would distinguish physical shutdown

Proved for the selected package and retained samples:

* the numeric RTP predicate calls a per-mode action-bit store, then a common
  fault setter;
* V6 captured that setter's exact state transition and two diagnostic lines;
* the late fault windows contain action bit 4 only in the mode-1 bucket, with
  no proof that V6 freshly set it;
* the common fault state suppresses the next ordinary RTP scan path;
* image 0 has a recurring fault-bit poll into a shared emergency handler which
  performs exact MMIO actions before storing host status `0x10`; and
* two competing direct selector-`0x10` callers prevent assigning the later
  host status uniquely to that recurring poll or to V6.

Not proved:

* that `rtp_act_736` text acknowledges any downstream action;
* that the live controller executed every selected-package byte unchanged;
* the event-instant values of mode, `r7`, or `fp` without the alias/retention
  inference;
* the hardware meaning of the four `0x4013....` MMIO locations;
* an intentional panel-output, rail, reset, PWM, timing, or scan shutdown.

The smallest concrete observations that would separate the remaining cases
are observational, not patches:

1. **Downstream software entry:** capture image-0 `RT-P activate!` and
   `System Emergence!!` text aligned to the image-1 event. Their absence from
   the image-1 ring is expected; a separate image-0 log source is required.
2. **Hardware action:** trace writes to `0x40130010`, `0x40131010`,
   `0x40132010`, and `0x4013400c`. A timestamped write proves the command was
   issued; readback may be meaningless for write-only command registers.
3. **Physical output:** simultaneously observe a positively identified
   panel-enable/rail/reset/PWM signal or a documented output-enable register.
   Only this last correlation can distinguish an intentional output shutdown
   from a fault report plus an unrelated physical panel collapse.

The existing late host status `0x10` supplies non-origin-unique software
evidence, and the stable action fields preserve a mode-1 bucket mark without
proving its freshness. Neither substitutes for items 2 and 3.

## Reproduction

`verify-rtp-action-causality.py` uses only Python's standard library. It pins
the package, the retained windows, corrected image mappings, exact function
slices, event/action/setter bytes, the bounded fixed-offset reference census,
and the late action fields:

```sh
python3 verify-rtp-action-causality.py
python3 -O verify-rtp-action-causality.py
```

Both commands must emit one compact JSON object with `ok: true`.
