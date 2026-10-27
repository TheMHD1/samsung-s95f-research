# SSB mode-gate follow-up

Recorded 2026-10-27 UTC. This is an offline audit of the selected 5 MiB QD
package. No USB packet was constructed or transmitted, and no TV, USB node,
driver, UART, root shell, network endpoint, or external service was touched.

## Correction and result

RAM byte `0x20000571` is not a permanently unresolved enable gate. It is the
per-transfer backend mode:

* the parser first writes `2` as an unselected/invalid sentinel;
* validated normalized operations `1` and `2` replace it with `0`;
* validated normalized operations `3` and `4` replace it with `1`; and
* the later `mode == 2` branch drops operations which did not select a
  supported transfer backend.

The earlier bounded report
[`ssb-device-read-protocol-20261027.md`](ssb-device-read-protocol-20261027.md),
SHA-256
`6bafcfb45e95b18a3646b71e5da37a43df4a863e6368e57dfb808e139da7021c`,
correctly recovered the target-`0x203` eMMC-sector leaf and buffer limits, but
its conclusion that no later mode producer was recovered is superseded by
this report. Both producers reuse the same PC-relative literal at linked VA
`0x291f0` / FILE `0x293f0`; searching only for additional raw address words
missed those instruction xrefs. No request was sent under the earlier
conclusion.

For target `0x203`, the proven local path is:

1. validator VA `0x29258` accepts `0x203`, observes family `2`, and stores the
   separate remap flag RAM `0x20000570 = 0`;
2. parser VA `0x28fb4..0x28fc4` takes the low target byte and clears optional
   bit 4, so `0x203` becomes normalized operation `3`;
3. VA `0x29062..0x2907a` recognizes operation `3` and writes transfer mode
   `1` to RAM `0x20000571`;
4. the family-2 remap flag bypasses address mapper VA `0xefa4`;
5. the test at VA `0x290d6..0x290de` sees mode `1`, not sentinel `2`, and
   continues; and
6. the operation-3 branch at VA `0x2914e..0x29176` calls the previously
   established eMMC read leaf VA `0x9bd4`.

This resolves the specific execution-phase objection. It does not prove
current live firmware equality, eMMC partition identity, returned-data
freshness, or read success. In particular, the recovered caller still ignores
the eMMC leaf's return before scheduling response data. Those remaining
integrity boundaries are independent of the corrected mode audit.

## Exact producer dataflow

Image 0 uses **FILE = linked VA + `0x200`**. At the start of each parsed
header:

```text
VA 28f44  movs r0,#2
VA 28f46  ldr  r1,[pc,#2a8]   ; VA 291f0 -> RAM 20000571
VA 28f48  strb r0,[r1]
```

After validation and low-byte normalization, operations `1/2` execute:

```text
VA 2905a  movs r0,#0
VA 2905c  ldr  r1,[pc,#190]   ; PC 29060 + 190 = VA 291f0
VA 2905e  strb r0,[r1]
```

Operations `3/4` execute:

```text
VA 29076  movs r0,#1
VA 29078  ldr  r1,[pc,#174]   ; PC 2907c + 174 = VA 291f0
VA 2907a  strb r0,[r1]
```

Only afterward does VA `0x290d6..0x290de` compare the byte with `2`. Thus the
early store is an initialization sentinel, not evidence that all shipped
storage operations are dead.

The continuation callback independently gives the modes concrete semantics.
At VA `0x28c0a..0x28c30`, mode `0` schedules USB IN directly from the current
address. At VA `0x28c52..0x28c90`, mode `1` calls eMMC read VA `0x9bd4` into
the fixed response buffer and then schedules USB IN from that buffer. Mode
`2` takes neither continuation. This corroborates “direct-address” versus
“buffered eMMC” as code behavior rather than names inferred from constants.
The same callback subtracts the completed transfer length from remaining
bytes at VA `0x28bb4..0x28bc6`; when the remainder reaches zero it stores
operation `6` and calls VA `0x29500` at `0x28be8..0x28bf0` to rearm the next
12-byte header. This closes the normal completion-to-next-header control-flow
edge, without establishing whether the preceding storage read succeeded.

## Startup, aliases, and census boundary

The pinned reset scatter row 0 expands to RAM `0x20000000..0x20000f4b`; its
initial byte at `0x20000571` is zero. That is packaged initialization evidence,
not a live RAM measurement. It is not required for header correctness because
the parser overwrites the byte with `2` before classifying every header.

The checker performs a complete raw exact-word census over stored image 0
(FILE `0x200..<0x40200`). Exact `0x20000571` words occur only at FILE
`0xf348`, `0x28edc`, `0x290ec`, and `0x293f0`. The first belongs to address
mapper VA `0xefa4`; the middle two are continuation consumers; the last is the
shared parser literal used by all three direct writers above. It also pins
nearby direct-pointer literals `0x2000056c`, `0x20000570`, and `0x20000574`.

For the adjacent word/alias question, both exact direct references to RAM
`0x20000570` are byte operations: validator byte writes and callback byte
reads. No recovered direct word/halfword store through those exact literals
spans `0x20000571`. This is a complete exact-literal census, but only a bounded
alias census: computed pointers, DMA, and an external core could access the
same RAM without embedding its absolute address. Such an unknown writer could
change concurrent behavior; it is not needed to make the ordinary `0x203`
path locally reachable because the parser's own mode-1 store is exact.

## Inputs and reproducibility

* Selected package:
  `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
  5,242,880 bytes, SHA-256
  `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
* Pinned reset-scatter decoder:
  `tcon-research/qd-rt-window-reset-output-reproduce.py`, SHA-256
  `fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02`.
* Decoder mode: ARM Thumb, M-class, little-endian.

Run the offline checker:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/ssb-mode-gate-followup-20261027.py
PYTHONPATH=/tmp/tcon-capstone python3 -O tcon-research/ssb-mode-gate-followup-20261027.py
```

The checker pins the package and scatter output, initial RAM byte, exact
producer/consumer instructions, PC-relative literal resolution, target
normalization, remap-byte behavior, continuation semantics, source slices,
and exact stored-image pointer census.

## Actionable remaining evidence

No further `0x20000571` producer is required to explain ordinary target
`0x203` dispatch. The next missing evidence is elsewhere:

1. bind the installed executing firmware to this selected package more
   strongly than the already matching cached USB descriptor;
2. bind the chosen eMMC sector to a specific intended object/partition; and
3. recover a trustworthy success/freshness discriminator, because the local
   caller does not gate its USB response on the eMMC leaf return.

Until those are addressed, a returned sector could corroborate a known
prefix but cannot by itself prove current executable equality or successful
fresh storage acquisition. This report makes no live-request readiness or
physical-state claim.
