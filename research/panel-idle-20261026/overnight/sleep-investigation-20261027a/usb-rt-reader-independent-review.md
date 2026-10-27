# Independent review: USB/AP_RTP logical-reader route

Reviewed offline on 2026-10-27. This review inspected the current
`tcon-research/qd-usb-ap-rtp-logical-read-route.md` and its current
reproducer without changing either file or making any TV, root, USB, network,
controller, or process call.

## Verdict: blocked by a reader-arithmetic error

The reproducer passes in normal and optimized Python modes, but it validates
an arithmetic model that is not the arithmetic implemented by the recovered
generic reader. Its headline conclusion that logical `0x21000a`, count one,
reads `0x4701240a` is not supported by the reader instructions.

This is a static-code error, not a live-target result. The reader, UART/CDC
boundaries, and all current artifacts remain read-only evidence; this review
does not turn any route into a command to send.

## Exact counterexample

For the AP_RTP row at stored file `0x3ce44`, the seven words are:

```text
+0x00 name VA          0x0003de8c  (AP_RTP)
+0x04                  0x47012400
+0x08                  0x00000100
+0x0c                  0x47010000
+0x10                  0x00002400
+0x14                  0x00210000
+0x18                  0x00210400
```

At image-0 linked VA `0x637c` (stored file `0x657c`), the reader does the
following for `r5 = 0x0021000a`, `r6 = 1`, and an output buffer in `r8`:

```text
6386  lsr.w  sl,r5,#16
638a  lsl.w  sl,sl,#16       ; sl = 0x00210000
638e  uxth   r7,r5           ; r7 = 0x000a
...
63a4  ldr.w  sb,[row,#0x14]  ; sb = 0x00210000
63b0  ldr.w  fp,[row,#0x18]  ; fp = 0x00210400
63b4  cmp    sb,sl           ; match
63c0  ldr    r0,[row,#8]     ; r0 = 0x100
63c2  cmp    r0,r7
63c4  bhi    63e4            ; NOT taken for 0x0a
63d0  ldr    r0,[row,#0x0c]  ; r0 = 0x47010000
63d2  add    r0,r7           ;       0x4701000a
63d4  sub.w  r3,fp,sb        ; r3 = 0x400
63d8  subs   r1,r0,r3        ; r1 = 0x4700fc0a
63da  lsls   r2,r6,#1        ; r2 = 2 bytes
63dc  mov    r0,r8
63de  bl     0xa72           ; copy helper
```

Thus the directly implemented source address for that supplied logical value
is **`0x4700fc0a`**, not `0x4701240a`. The alternative branch (`r7 > 0x100`)
loads `[row,+4]` then adds `r7`; it is not selected for `0x000a`.

The exact comparison has a second nuance: it is `bhi` after `cmp 0x100,low`,
so `low == 0x100` remains in the first displayed path; it is not literally
“below `0x100`.” Neither nuance changes the count-one byte length for
`0x000a`, but both matter for a claimed exact address.

## Reproducer assessment

The current checker correctly pins the package, direct `BL` caller list,
handler/table literals, bounded UART evidence, bounded CDC interval, and its
stored-byte hashes. Both invocations passed:

```text
python3 .../qd-usb-ap-rtp-logical-read-route-reproduce.py     PASS
python3 -O .../qd-usb-ap-rtp-logical-read-route-reproduce.py  PASS
```

However, its model replaces the reader body with:

```python
low = logical & 0xffff
physical = row[1] + low
```

when the actual taken path above loads `row[3]` and subtracts
`row[6] - row[5]`. Passing a hash-pinned checker cannot correct that semantic
substitution. The claimed packaged default at file `0x18380a` is consequently
the AP_RTP loader payload byte, not the output of the recovered generic-reader
calculation for logical `0x21000a`.

## Findings that remain boundedly supported

* The reader takes a word-count argument and shifts it left one before the
  copy (`r2 = r6 << 1`), so the selected one-word branch requests two bytes.
* Direct `BL` caller closure to linked VA `0x637c` is reproducibly
  `0x11058`, `0x1148c`, and `0x2a2f8`; `0x1148c` loads `r1 = 1`, `r2 = sp`,
  moves the parsed target to `r0`, then calls the reader.
* The `param` handler pointer is in the recovered command table. This proves
  installation in that table, not its external transport grammar or reach.
* The reproducer's bounded literal/direct-call census supports the stated
  distinction between a controller-local UART parser/ring path and the CDC
  mixed-code interval. It remains a bounded negative; no CDC-to-UART absence
  claim may be generalized beyond that interval/census.

The UART prose should retain the distinction between a parser passing the
`0x40152000` literal to its helper and a fully audited helper/MMIO semantics.
The current cited direct ISR read is stronger positive evidence for the ring
producer. Neither point repairs the reader-address blocker.

## Required correction before relying on this route

The report/reproducer must either:

1. model the actual `0x637c..0x63f6` branches and report the resulting source
   address without relabeling it as the AP_RTP live field; or
2. find a different logical value whose **actual** reader path resolves to
   `0x4701240a`, with bounded range/count reasoning and a separately proven
   ingress before any live consideration.

No such alternative was proposed or derived in this review. In particular,
this review does not calculate or recommend a command value.

## Scope of supersession: configuration loader versus generic reader

The arithmetic error is confined to the **generic logical reader** discussion.
It does not refute the separately recovered AP_RTP **type-4 loader** binding.
That loader's successful-path evidence remains a different dataflow: it takes
the record's two packaged source ranges and copies them to table `+0x04`
(`0x47012400`, `0x100` bytes) and table `+0x0c`
(`0x47010000`, `0x2400` bytes), respectively. The loader byte landmarks and
payload-to-destination result do not depend on the reader's `0x637c` branch.

The following statements are therefore superseded only to the extent that
they describe a logical-reader address translation:

* `qd-config-rtp-table-load.md` lines 115–123, specifically its assertion
  that logical `0x21000a` resolves to `0x4701240a`;
* `qd-config-rtp-table-independent-review.md` lines 215–255, specifically
  the listed “low below `0x100`” source mapping and any consequence drawn
  from it; and
* the reviewed USB/AP_RTP route report/reproducer's identical exact-address
  conclusion.

The AP_RTP table bytes, record metadata, two payload source locations,
successful-loader copy destinations, package-default byte extraction, and
startup reachability claims in those earlier configuration reports are **not
superseded by this review**. They should nevertheless avoid calling the two
logical-prefix table words an implemented reader mapping until the reader
branches are modeled correctly.

The existing `qd-config-rtp-table-reproduce.py` checks loader/table/data
binding and does not calculate a logical reader source address. Its successful
run remains evidence for that narrower loader result, not validation of the
later generic-reader prose.

## Review provenance

| Artifact | SHA-256 |
| --- | --- |
| selected profile | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| reviewed route report | `a28594a181c6bd5fd37bc4000b62ff16769872d74a51d56c6c05ad90290a7f75` |
| reviewed reproducer | `e174f6344cdedfe96159381d9778a275917dbdd5ddf595ae8b0a7626dc31284c` |
| reader bytes, stored `0x657c..0x6610` | `7ebc90f811630e1be84808d2dbac850e4c067c0643066714ef5a75b2b0f11b16` |
| command-table excerpt, stored `0x3d334..0x3d3bc` | `2b11956856f2b33086e9969b9fd0fe7a25865a37b9722114a54fa33d7e323b10` |

No source in this review is a live execution binding, current-flash equality
claim, or panel-fault conclusion.
