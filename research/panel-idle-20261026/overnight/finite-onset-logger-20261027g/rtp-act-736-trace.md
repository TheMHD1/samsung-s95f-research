# V6 `rtp_act_736`: captured setter and host-wire boundary

Recorded 2026-10-27 UTC. This is an offline trace of retained V6 artifacts and
the already copied selected QD package. It made no TV, root, USB, controller,
network, UI, firmware, storage, threshold, or protection operation.

## Result

V6 captured a real software-fault transition in the fixed RT window. Before
the observation, halfword `0x4701240a` was zero. At the post-observation read
it was `0x1001`, while the secondary ring had appended exactly two terminal
lines:

```text
rtp_act_736
rtp_act_736
```

The retained selected package contains an exact instruction-level match:

```text
event tail at image-1 VA 0x2036: r0 = 0x2e0
image-1 VA 0x203a:             call common setter 0xc1e0

common setter 0xc1e0:
  root + 0x2400 = 1
  root + 0x240e = 0
  root + 0x240a = 0x1001
  log("rtp_act_%d\n", event)
  log("rtp_act_%d\n", event)
```

`0x2e0` is decimal 736. The store values, the two identical formatter calls,
the exact format literal, the two captured lines, and the simultaneous fixed
window change form one coherent path-level runtime match. This is materially
stronger than the earlier static inference from a shared `+0x240a` offset.

The host-wire consumer is also concrete. Image 0's recurring checker reads
the low bit of byte `0x4701240a`; `0x1001` stored little-endian makes that byte
`0x01`. If the recurring checker consumes it, it enters the common error path
with selector `0x10`. That path stores `0x0010` in the common status field
returned by selector 8 of command `F3 80 00 00 00 08`, producing controller
reply bytes `00 00 00 10` and host word `0x00000010`, whose exact QD host label
is **RT Protect**.

A later same-boot one-shot status query did return `0x00000010`, with a
matching raw QDF kernel line, and a still later same-boot one-shot fault-pin
sample returned one. Those later observations corroborate the mapped fault
state, but they occurred after the V6 window and are not represented as
simultaneous samples or proof of physical panel state.

## Retained V6 transition

The accepted V6 outcome has SHA-256
`1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9`.
It completed 16 exact protocol steps, restored the logger gate to zero, and
ended in `ReadyForHeader` with no reported native errors.

The fixed helper read target `0x101`, address `0x47012400`, length 64, using
header `010100000024014740000000`. The three retained snapshots show:

| snapshot | `+0x2400` | logger `+0x2406` | fault `+0x240a` | `+0x240e` |
| --- | ---: | ---: | ---: | ---: |
| pre-arm | `0` | `0` | `0x0000` | `1` |
| armed | `0` | `1` | `0x0000` | `1` |
| restored/post | `1` | `0` | `0x1001` | `0` |

Only `+0x2406` was deliberately changed and restored by the diagnostic. The
event flag, fault halfword, and cleared `+0x240e` are the exact independent
stores in the packaged common setter; the logger gate controls observation,
not those stores.

The full ring snapshots are each `0x3c0c` bytes. Their write/read cursors
advanced together from 143 to 1899. The exact 1,756-byte appended interval
has SHA-256
`deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba`.
It contains an RTP normal-scan header and numerous bounded RGB/difference
records, then ends with the two event lines. It contains no other
`rtp_act_` line.

The record order establishes that the diagnostics preceded the event text.
It does not identify which displayed RGB record supplied the final event
predicate, because the ring text does not retain the event caller's live
registers or selected threshold.

## Exact packaged caller

The selected 5 MiB package is
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
For image 1, `FILE = VA + 0x40200`.

The event caller is the tail of VA `0x1e68..0x203e` (stored
`0x42068..0x4223e`). It selects a comparison threshold into `fp` according to
its mode/index and object/context fields. At the final bounded tail it loads
a halfword into `r7`, stores that value at root `+0xf06` for mode 6 or
`+0xf08` otherwise, and executes:

```text
0x202a  cmp   r7, fp
0x202c  ble   0x203e
0x202e  uxtb  r0, r4
0x2030  movs  r1, #4
0x2032  bl    0x1c0c8
0x2036  mov.w r0, #0x2e0
0x203a  bl    0xc1e0
```

Thus the immediate local condition is unsigned/halfword value `r7` greater
than the selected `fp` threshold, followed by helper `0x1c0c8(index, 4)`.
The live values of `r4`, `r7`, `fp`, and the upstream physical meaning of the
sample are not present in V6. The trace therefore does not rename `RTP`,
assign an electrical unit, or identify a safe threshold change.

The caller-body slice `0x1e68..0x2040` hashes to
`c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a`.
The common-setter slice `0xc1e0..0xc212` hashes to
`f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102`.
The exact literal at VA `0xc214` is `rtp_act_%d\n\0`.

## Fixed-window and host-wire consumer

For image 0, `FILE = VA + 0x200`. Its recurring checker at linked VA
`0x214d4..0x21510` has this exact path:

```text
0x214d6  call 0xef94              ; returns fixed 0x47010000
0x214dc  r0 = 0x240a
0x214e0  load byte [0x47010000 + r0]
0x214e2  keep bit 0
0x214e6  skip if zero
0x214f0  r0 = 0x10
0x214f2  call common error 0xb660
```

The complete checker slice hashes to
`6636bd288c51f566df590a89e48aabb761377a5da4a64d01e868a8fdee371049`.
The common path calls the selector store at VA `0x2b764`; that exact 22-byte
body overwrites common-object halfword `+0x10` with the selector. Its hash is
`3d538c104bca6958c66173c7d56a095ded57e9453134e78933ee6d0e26fffb03`.

For the host status request, the packaged path is:

```text
wire request F3 80 00 00 00 08
  -> command 0xf380, selector 8
  -> image-0 selector table VA 0x21df8
  -> case 8 at VA 0x21e66 loads common-object halfword +0x10
  -> controller reply 00 00 00 10
  -> QDF four-byte reversal yields host word 0x00000010
```

The selector-table body hashes to
`7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0`.
The separately pinned transport/serializer proof is
`tcon-research/qd-profile-rt-status-wire.md`, SHA-256
`6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e`.

This closes the prior missing producer-to-consumer edge for this captured
state: V6 directly observed `0x1001` at the same fixed-window address whose
low bit the recurring image-0 consumer tests. The conclusion remains
conditional at the execution-identity boundary: the callback generation and
runtime behavior match the selected package, but no full live code read proves
that every running instruction byte equals the package.

## Later same-boot corroboration and timing limit

V6 ended its observation at uptime `115907.45`. The accepted one-shot host
status helper ran at uptime `116071.70`, 164.25 seconds later, and returned
`0x00000010`. The cached kernel line is:

```text
[116071.646556] [TCON:QDF] QDFTcon_GetErrDetStatus[15976:TconStatusRead.]: ERR DET Status:0x10
```

Its PID matches the helper. The exact QD decoder labels bit 4 `RT Protect`.
The accepted one-shot fault-pin sample ran later at uptime `116125.46` and
returned one. All artifacts use boot ID
`00000000-0000-4000-8000-000000000000`.

These facts establish a same-boot sequence:

```text
V6: local fixed-window 0 -> 0x1001 plus event 736 logs
  164.25 s later: host status 0x10
  218.01 s later: fault pin 1
```

They do not establish sub-second ordering between the controller event,
physical light loss, host poll, and GPIO assertion. The status operation and
GPIO input request were also active diagnostic calls, not passive timestamps.

## Bounded conclusion

The strongest supported interpretation is now specific: an ordinary packaged
RTP event with code `0x2e0`/736 reached the common local setter during V6,
produced the exact `0x1001` fault field and duplicated diagnostic lines, and
left the fixed-window bit consumed by image 0's selector-`0x10` path. The
packaged host-wire path maps that selector to `0x10`/RT Protect, and the later
same-boot query actually returned `0x10`.

This is a diagnosis boundary, not a repair. It does not prove the physical
meaning of RTP/RT, identify the damaged component, prove the UI request was
consumed, establish what the physical panel displayed, or justify disabling
the setter, error path, storage, protection, threshold, or recovery logic.
The trace stops at the ordinary setter and wire consumer.

## Reproduction

The verifier pins every live artifact and source slice described above,
checks exact ring cursors/delta, RT halfwords, Thumb branch targets, fixed
consumer, selector store, and wire-selector case. It uses only Python's
standard library and performs no external operation:

```sh
python3 finite-onset-logger-20261027g/verify-rtp-act-736-trace.py
python3 -O finite-onset-logger-20261027g/verify-rtp-act-736-trace.py
```

Both modes pass and emit one compact JSON summary.
