# RTP packed-buffer origin: selected image 1

Recorded 2026-10-27 UTC. This is a finite offline trace of the already copied
selected QD package. It made no TV, root, USB, controller, network, UI,
firmware, reset, write, storage, protection, return-guard, high-bank,
persistence, or POFLG operation. It does not modify any frozen D7 evidence.

## Result

The selected image positively establishes this immediate producer chain:

```text
EXCO_PAR2_S0-associated words at 0x58601408
  -> refresh 0x3934
  -> ten-byte records at 0x2000a60c/0x2000a616 carrying prior/current fields
  -> producer 0x18ae8 computes two sources in the 0x60000000 aperture
  -> CPU copy 0x334 moves 0xb60 bytes to a ring payload at slot+8
  -> software stores descriptor fields into the eight-byte slot header
  -> selector 0x18ce0 supplies pointer slots 0x20000494 (A)/0x20000498 (B)
  -> the packed unpacker consumes payloads after their headers
```

This closes the immediate software origin of the packed buffers. It does not
close the physical origin or unit of the bytes at the computed `0x60000000`
addresses. The closest positive name is `EXCO_PAR2_S0`; no direct name,
caller, or string binds the payload aperture to display pixels, sensing,
loopback, a framebuffer, or another specific hardware stream.

The copy at `0x334` is a CPU load/store loop, not a DMA call.

## Superseded same-slot statement

The sentence in frozen `qd-rtp-scan-invocation.md` saying both producer
iterations write the same selected destination is superseded by this trace.
The original file remains unchanged. Producer `0x18ae8` recomputes its
destination from byte `0x20253000` in each loop iteration and advances that
byte modulo three before the next iteration.

For initial selector `s`:

```text
iteration 0 writes slot s
iteration 1 writes slot (s+1) mod 3
final selector is (s+2) mod 3
```

Afterward `0x18ce0(1)` returns `(s+2) mod 3`, while `0x18ce0(0)` returns
`s`. Dispatcher `0xb7ec` stores those pointers at `0x20000494` (A) and
`0x20000498` (B). A is therefore the slot not written by the immediately
preceding two-copy pass, and B is the first slot written by that pass. This
is temporal layout, not proof that A is a calibration baseline or B a
physical current frame.

## Ring payload and header

Selector `0x18ce0` returns
`0x20253002 + index * 0xb68`, for index zero through two. Each slot is an
eight-byte software header plus a `0xb60`-byte payload. Producer `0x18ae8`
calls `0x334` with count `0x5b`; that body loads and stores eight 32-bit words
per iteration, exactly `0x5b * 8 * 4 = 0xb60` bytes.

For descriptor index `i` (zero then one), the header is:

| offset | width | value |
| --- | ---: | --- |
| `+0` | byte | descriptor index `i` |
| `+1` | byte | `u8(descriptor+0) != 0` |
| `+2` | byte | `u8(descriptor+2)` |
| `+3` | byte | not written by this producer |
| `+4` | u16 LE | `u16(descriptor+4)` |
| `+6` | u16 LE | raw bits of `u16(descriptor+6)` |
| `+8` | `0xb60` bytes | CPU-copied payload |

The source is:

```text
0x60000000
 + u8(descriptor+2)  * 0x195 * 0x10000
 + s16(descriptor+6) * 3     * 0x400
```

The signed load at `descriptor+6` matters for address formation, even though
the same raw 16 bits are placed in header offset `+6`.

Image-1 scatter allocates and initially zeros `0x223c` bytes at
`0x20253000`, covering the selector, three slots, and two trailing bytes.
That is reset-image provenance only; each producer pass overwrites two slot
payloads and most of their header fields.

## Prior/current descriptor snapshots

Let `D = 0x2000a60a`. The producer records start at `D+2` and `D+0xc`.
Refresh `0x3934` first copies the prior tail `D+0x16..D+0x1d` into record 0
fields `D+4..D+0xb`. It then refreshes the tail from `H = 0x58601408`:

| source | destination |
| --- | --- |
| low byte `[H+0]` | `D+0x2a` gate/status |
| low byte `[H+4]` | `D+0x16` |
| low 16 `[H+8]` | `D+0x18` |
| low 16 `[H+0xc]` | `D+0x1a` |
| low 16 `[H+0x64]` | `D+0x1c` |

Finally it copies the refreshed tail into record 1 fields `D+0xe..D+0x15`.
Thus fields `+2..+9` in record 0 are the prior snapshot, while those fields
in record 1 are the current snapshot. Record bytes `+0/+1` are outside this
refresh copy; producer header byte `+1` separately tests record byte `+0`.
The source computation consumes record byte `+2` and halfword `+6`, while
header construction also consumes halfword `+4`. Copied halfword `+8` is not
used by `0x18ae8`.

The exact selected record at file `0x83c00` is named `EXCO_PAR2_S0`. Its
metadata has address word `0x58601400`, and the refresh root is exactly that
word plus eight. This proves an EXCO parameter-block association in the
selected package. It does not name individual field units, prove this record
was loaded in the observed boot, or identify the `0x60000000` payload.

Callback `0x18c94` directly calls refresh `0x3934`, checks context/status,
then calls producer `0x18ae8`. Registration body `0x195f8`, directly called
at `0xaef6`, installs Thumb pointer `0x18c95` into a callback slot rooted at
`0x20000468`. This is selected startup reachability, not live cadence.

## Dynamic pointers and fixed A payloads

The corrected fallback is:

```text
A = *(uint32_t *)0x20000494 + 8
B = *(uint32_t *)0x20000498 + 8
```

Both skip the producer header. Under ordinary mode/header conditions A may
instead be fixed payload `0x20015000` or `0x20015f10`, while B remains the
dynamic payload. Scatter initializes `0xb50` zero bytes at each fixed base.
Function `0x1c12c` can later CPU-copy `0xb60` bytes from dynamic B+8 into one
of them. These fixed regions do not have a producer header at their base and
must not be described as ring slots.

## First unresolved edge and limits

The selected image proves that packed content can depend on runtime EXCO
descriptor fields and on bytes at computed `0x60000000` addresses. It does
not prove:

- whether that aperture is MMIO, shared SRAM, frame storage, or loopback;
- which component fills it or its update cadence;
- display-pixel, sensor, voltage, current, brightness, or coordinate meaning;
- a software-to-physical panel-coordinate transform.

Nearby strings such as `CSP_DMA0_IRQ_Handler`,
`Active_TconInputBased_Handler`, `Active_TconOutputBased_Handler`, `RGB`, and
sensing text are not directly referenced by this bounded chain. String
proximity does not close the producer edge.

This is selected-package code provenance. Compatible live callback pointers
do not prove whole selected-function-body identity or that this exact body ran
during the retained V6 incident.

## Reproduction

`rtp-packed-buffer-origin.py` pins the package, bounded function hashes,
critical producer/selector bytes, direct calls, pointer/fixed-buffer literals,
scatter rows and decoded reset outputs, ring arithmetic, signed source
arithmetic, and the exact `EXCO_PAR2_S0` record. It uses only the standard
library:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 rtp-packed-buffer-origin.py
PYTHONDONTWRITEBYTECODE=1 python3 -O rtp-packed-buffer-origin.py
```


