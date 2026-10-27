# Image-1 RTP primary event `0x338`: input and predicate provenance

Recorded 2026-10-27 UTC. This is a bounded offline trace of the retained
selected profile. It made no TV, root, network, controller, or firmware
operation. In particular, it does **not** establish that this scan ran during
any blackout, that its packed samples denote a particular physical quantity,
or that its local event reaches the host fault status.

## Result

The primary RTP event is not raised merely because a value is nonzero. The
recovered image-1 path turns two packed, 12-bit data fields from two RAM
buffers into an unsigned absolute difference, applies one of several mode
gates, records samples and increments an index-specific counter, then raises
event `0x338` only when all of the following later conditions hold:

1. the local object field `+0x249e` is **not** one;
2. the index-specific word counter exceeds global halfword `0x200004ca`;
3. helper `0x35a4` returns zero; and
4. the event path calls `0x1c0c8(index, 4)` before its common setter.

The common setter then writes `1`, `0`, and halfword `0x1001` at image-1
object offsets `+0x2400`, `+0x240e`, and `+0x240a`, respectively. Reset
scatter initialization positively gives that object root as `0x20010000`, so
the effective local store is `0x2001240a`.

The selected AP_RTP configuration positively initializes the *image-0* RT
block `0x47012400..0x470124ff`, including a default zero at
`0x4701240a` and mode `+0x2410 = 4`. It does not, in the recovered startup
path, populate image-1 root `0x20010000`. Thus these facts refine the local
predicate and the packaged configuration provenance but do **not** create a
positive bridge from image-1's `0x2001240a` store to image-0's fixed
`0x4701240a` reader.

## Pinned source and corrected address convention

| item | value |
| --- | --- |
| selected package | `../overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` |
| package SHA-256 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| image-1 stored span | file `0x40000..0x5ffff` |
| image-1 mapping | linked VA = file offset `- 0x40200` |
| reset-established context root | `*(uint32_t *)0x200004e0 = 0x20010000` |

Earlier image-1 labels used a component-start mapping and are high by `0x200`.
For example, the old file range `0x4c7d0..0x4ca40` is linked
`0xc5d0..0xc840`; the event setter is linked `0xc1e0`, stored at file
`0x4c3e0`. This report uses the corrected linked labels.

Source slices, retained to make this bounded walk auditable:

| purpose | stored range | SHA-256 |
| --- | --- | --- |
| primary event body | `0x4c7d0..0x4ca40` | `04e0f7d8eb32f0008feb9bf29d05dba7488b95619006ebae024d812ad874509a` |
| difference/mode wrapper | `0x4bdbc..0x4bf2c` | `b35128c2517d1ba5938ee2f3413087aa19e9ebd505b35656a471e7de3ea4db0d` |
| packed-input unpacker/caller | `0x4bf58..0x4c240` | `dc9c513b47436ecce6297c99bb3083be667a254aa5fa210f170d53bd15c6a291` |
| common event setter | `0x4c3e0..0x4c412` | `f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102` |

## Primary per-sample predicate

The per-sample body is linked `0xc5d0..0xc840`; it obtains the root from the
getter at `0x38fc`. It first bounds input `r7` against halfwords at
`0x200004c6` and `0x200004c8`, then requires:

```text
*(uint32_t *)(0x2000ba28 + 4*(index - 1)) <= *(uint16_t *)0x200004ca
```

before storing collection fields. It records five values at root offsets
`+0x1000`, `+0x1400`, `+0x1800`, `+0x1c00`, and `+0x2000`, and increments the
same per-index counter at `0x2000ba28 + 4*(index-1)`.

The exact `0x338` tail is:

```text
c738  ldrh  r0, [root, #0x249e]
c73c  cmp   r0, #1
c73e  beq   c79e                 ; suppress primary event
c742  load  counter[index-1] from 0x2000ba28
c74a  load  bound from 0x200004ca
c74e  cmp   counter, bound
c750  bls   c79e                 ; require counter > bound
c752  bl    0x35a4
c756  cbz   r0, c786             ; require helper return == 0
c786  movs  r1, #4
c788  mov   r0, index
c78a  bl    0x1c0c8
c78e  mov.w r0, #0x338
c792  bl    0xc1e0
```

`0xc1e0..0xc212` gets the same root and writes `+0x2400=1`, `+0x240e=0`,
and `+0x240a=0x1001`. This is the exact answer to what asserts the local
`+0x240a` value. The body contains no recovered cross-image call, host packet,
or controller transfer.

## Where the compared values come from

The difference wrapper `0xbbbc..0xbd2c` receives its two compared inputs in
`r0` and `r1`, preserves them in `r8` and `r7`, and computes unsigned
`abs(r0-r1)` at `0xbc20..0xbc42`. Its direct call sites are in
`0xbd58..0xc040`, which derives those operands from two buffer bases:

* a first buffer based on the caller's original `r0` plus an offset;
* a second buffer based on original `r1` plus that offset.

The first operand is extracted with `ubfx ..., #0, #12` or `#12, #12`; other
sites assemble a value from a shifted byte field and four bits from the next
halfword. The second operand is selected from locally unpacked halfwords.
Consequently the proven representation is packed **12-bit data fields** in
RAM. The code does not name their unit or establish resistance, current,
voltage, brightness, or a pixel coordinate.

The immediate upstream path selects a source slot through linked `0x18ce0`:
it uses byte `0x20253000` to choose one of three `0xb68`-stride regions rooted
at `0x20253002`. A call at `0xb67a` stores the chosen pointer to
`0x20000498`; later linked `0x1c12c` conditionally copies `0xb60` bytes from
`*(uint32_t *)0x20000498 + 8` to either `0x20015000` or `0x20015f10`.
Those bounded bodies are RAM selector/copy logic; no MMIO load, peripheral
read, or DMA producer was recovered there. Startup scatter does place a
decompressed region at `0x20253000`, but it does not prove that the later
sample bytes remain static or identify their runtime writer.

## Mode and configuration reachability

Before it calls the per-sample body, `0xbbbc` has four finite routes:

| wrapper condition | call mode |
| --- | ---: |
| `*(u16*)0x200004aa == 1` and difference exceeds global threshold at `0x200004b6/0x200004b8` | 4 |
| `*(u16*)0x200004ac == 1` | 6 |
| root `+0x2410 == 4` and difference exceeds the alternate global threshold | 1 |
| root `+0x2410` is 1 or 3 and difference exceeds that threshold | 1 |

The selected AP_RTP record has a positive packaged initialization binding for
the image-0 field at `0x47012410` (offset `+0x2410`) to value `4`. Therefore,
*if that selected image-0 configuration was successfully loaded and the
relevant runtime object is the one read by this image-1 wrapper*, its `==4`
comparison is structurally satisfied. That conditional is deliberately not a
claim that it is the image-1 object: the recovered image-1 root is
`0x20010000`, while the loader's destination is `0x47010000`.

The global gates/thresholds at `0x200004aa`, `0x200004ac`,
`0x200004b6..0x200004bc`, the per-index counter bound, and helper `0x35a4`
have no recovered AP_RTP payload binding in this trace. Their values, the
actual invocation of the scan orchestrator, and the origin of the packed
buffers remain the discriminators needed before treating `0x338` as a
root-cause candidate during ordinary video.

## Bounded practical interpretation

This creates a specific future observation model without proposing any
control: a local `0x1001` write requires a scan invocation, a permitted mode
route, packed-buffer difference processing, an index counter beyond its bound,
and a zero result from `0x35a4`. It is not a single static threshold or a
direct response to final-duty I2C traffic. The retained firmware does not
show whether any of those predicates held on the TV.

The AP_RTP loader gives real initialization provenance for image-0's RT block;
image-1 reset gives real provenance for its RAM root. The missing operation is
a proven inter-core/window transfer or a live memory observation tying those
two different addresses together. No threshold, counter, latch, or protection
field was changed, and no recovery or playback test was started.

## Related retained evidence

* [qd-config-rtp-table-load.md](qd-config-rtp-table-load.md) proves the
  AP_RTP table/loader destinations and selected defaults.
* [qd-image1-context-initialization.md](qd-image1-context-initialization.md)
  proves image-1 reset scatter and its root pointer.
* [qd-profile-rtp-image1.md](qd-profile-rtp-image1.md) is the earlier RTP
  trace; its stored-file relative labels predate the corrected `0x200`
  component-prefix convention.
