# Packaged persisted-log producer and bounded recovery map

Recorded 2026-10-27 UTC. This is an offline, read-only reverse-engineering
result. It made no TV, controller, USB, I2C, eMMC, root, network, firmware,
reset, or flash call. No prior artifact was changed.

## Transport restriction discovered after this offline trace

The storage addresses below are not cleared USB requests. The independently
recovered target0x203 family2 header validator rejects address/length ranges
at or above0x01000000. Therefore do not issue the proposed0x80000000 header
read through that transport. A supported high-bank route has not been proved.
The follow-up intended to resolve this route was stopped by an automated
security check and remains incomplete. No high-bank request was issued.

Likewise the text proves firmware-reported batch/header writes and counter
advancement. It does not independently prove durable storage commits or
successful readback. Treat later uses of “committed” in this initial report
as firmware-reported commit state, subject to that missing verification.

## Result

The retained 3 KiB main text-log capture contains an exact live positive
control for the selected `241230A` package's persisted telemetry service.
Package function VA `0x20510` creates one fixed `0x200`-byte binary record per
eligible service tick, stages at most ten records at RAM `0x2000be40`, requests
a batch write to an internal eMMC-address domain beginning at byte address
`0x80004000`, and then requests one of two `0x200`-byte metadata-header writes
at internal byte addresses `0x80000000` and `0x80000200`.

The three typo-preserving formats emitted by this function are present in the
selected package and absent byte-for-byte from the current stored first image:

```text
LOG Buffer Copy: %d(%d)
LOG eMMMC Data Write: %d ~ %d(%d)
LOG eMMMC Hedaer Write: %d(%d)
```

The capture contains Copy numbers `197151..197182`, attempted ten-record
batches `197146..197155`, `197156..197165`, and `197166..197175`, and header
attempt rows `1(41)`, `0(42)`, `1(43)`. The selector is exactly the low bit of
the incrementing header-write counter. This matches the package instructions
and their misspellings, not merely a generic `LOG` string. It does **not**
prove that any of those writes reached durable media: VA `0x20510` ignores
both write-wrapper return values and performs no readback or CRC verification.

This does **not** prove that every running instruction came from that package.
It does prove that the active text producer for these persistence rows has the
package generation's bytes/format contract; the current stored first image
does not contain those format byte strings.

The persisted region is not another copy of the 3 KiB textual circular log.
It stores `0x200`-byte binary telemetry structures built by VA `0x762c`.
Consequently it may preserve useful pre-onset state, counters, and ticks, but
it will not recover old `deadPool:`/`mod_match:` text verbatim.

## Pinned inputs and mapping

| artifact | size | SHA-256 |
| --- | ---: | --- |
| selected package `F_RSM1_BN9659934B_COMMON.bin` | `0x500000` | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| current stored `fixeddata.bin` | `0x500000` | `f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562` |
| active main-log capture `returned-block.bin` | `0xc00` | `6d82903d4abeb366af859c8966345514a50315a14a891ee1370f69fe173b912a` |

For package image 0, `FILE = VA + 0x200`. All addresses below are linked VAs
unless explicitly called storage byte addresses or RAM addresses. Thumb/M-class
decoding was done with `PYTHONPATH=/tmp/tcon-capstone`.

Important source-range hashes are:

```text
VA 056f0..0574b  dual-header reader/validator  63bc2ff8a1cf3c9d97603bd095ef3431321ff13cad3ea005b75a60086e32e62f
VA 0762c..07c7f  binary record builder          e574f25b0eddf06d4914513501e3c24a9ca2a9d536d054769af6a894870975fd
VA 07c80..07cef  metadata-header builder        bbda99a683ed41a57d1dd29f4b7f5f9e2071d597c206a70332f0418545be623d
VA 20454..204df  startup header selection       7968a5380bba1f28991cf66d179cfd4b9cf85225235bccdee2ee88adb4d71308
VA 20510..20623  recurring persistence service  a5fb6873b5364319728b7e46150d2974ce617d9c3518ed2b663b839f20c593dd
VA 09bd4..09cb7  aligned eMMC read wrapper       7eb2e0e5029fb8ac2c64fe88c207c7922dafbfcc651928dcae21b1a2cef2343b
VA 09ee4..09fc5  aligned eMMC write wrapper      67ede89b8a2d30fb6043b353d85fb8a493fd9d384e3a138bd37f125a6e659023
VA 16924..1695f  command/sector programmer       282ab21323a50a4492d17f76f603baa3ca045e658c05e06687ce57ac9818b597
VA 16b70..16cd3  storage-controller leaf         c8d764cfde98205a0c82fcc5d89cb5afde088a301063ee14fed33273f2bd5826
VA 1d9cc..1da4f  retry/read/checksum helper      0ffb9f0ee71d483136215caa01ae621f021caeb0b061c1ad8a2e7b15ff950020
VA 29258..293b3  USB target/range validator       febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234
VA 0b6dc..0b6f9  emergency schedule              9bfe11209ff36e04e88964a663f7bf3b6f3b7c31140827730562687e2f5b6f36
VA 39bda..39c4d  ordinary recurring schedule     e2d3cc629921b0cdccdd3151a4b545dbb594c5b214ff87faf9e7c81c03bd8936
```

## Exact storage write dataflow

VA `0x20510` runs only when byte getter `0x38af0` returns nonzero. That getter
reads RAM `0x20000e30`. It clamps common-object halfword `+0x162` to at least
five, obtains the current low tick from `0x24df0`, and waits until the delta
from RAM `0x20000850` reaches that interval. It refuses to create another
record once total record count RAM `0x20000858` is already `0x300000`.

For an eligible record it performs, in order:

1. increment total record count `N = *(u32 *)0x20000858`;
2. call `0x762c(current_tick_low, 0)` to build the record in the slot selected
   by the old staged count;
3. increment staged count `B = *(u32 *)0x20000874`;
4. emit `LOG Buffer Copy: N(B)`;
5. when `B` reaches the current flush threshold or ten, request the batch
   write and ignore the returned status;
6. reset `B`, increment the header counter at `0x20000868`, build a header,
   request the selected header-sector write, ignore that returned status, and
   set the later flush threshold to ten.

The initial threshold is one (`0x204f8`), so the first runtime record is
submitted immediately; subsequent submissions normally contain ten records.

### Address and unit equations

The eMMC wrapper receives byte address in `r2` and byte length in `r3`. It
rejects either value when its low nine bits are nonzero and shifts the byte
address right by nine before the lower command. Thus the constants and
arithmetic below are byte addresses at this call boundary, with `0x200`-byte
sector alignment; they are not already sector numbers.

For a batch ending at displayed record number `N` with staged count `B`:

```text
first displayed record = N - B + 1
first zero-based index  = N - B
data byte address       = 0x80004000 + (N - B) * 0x200
data byte length        = B * 0x200
displayed range         = (N - B + 1) .. N
```

The captured `197156..197165(10)` row therefore corresponds exactly to byte
address `0x80004000 + 197155*0x200`, length `0x1400`.

These are **internal storage-wrapper addresses**, not target-`0x203`-cleared
host addresses. The internal read wrapper VA `0x9bd4` and write wrapper VA
`0x9ee4` have the same address treatment:

```text
read  VA 0x09c54  require address low nine bits == 0
      VA 0x09c90  sector = address >> 9
      VA 0x09c96  operation = 1
      VA 0x09ca2  call storage leaf 0x16b70

write VA 0x09f64  require address low nine bits == 0
      VA 0x09fa0  sector = address >> 9
      VA 0x09fa6  operation = 2
      VA 0x09fb2  call storage leaf 0x16b70
```

VA `0x16b70` passes that sector value unchanged to VA `0x16924`, which stores
it as the storage-controller argument at MMIO object `+0x28`. No instruction
in this bounded chain masks bit 31 before the shift or interprets it as a
partition selector. Therefore internal byte address `0x80000000` becomes
sector `0x00400000`; it is an actual high logical storage offset in this
contract, not a recovered flag selecting a low bank.

The fifth wrapper argument controls buffer handling; it does not alter the
storage sector or select a partition. The target-`0x203` caller places sentinel
`0xabcd` in that stack argument at VA `0x29166`. Read-wrapper VA
`0x9bf6..0x9c00` recognizes it, clears the temporary fifth-argument register,
skips the lock/mapping block, and retains fixed DMA address `0x20270000` loaded
at VA `0x9be8` from literal VA `0x9cb8`. For a non-sentinel call, a nonzero
fifth argument directly replaces that DMA address; zero instead maps the
ordinary `r1` buffer at VA `0x9c6a..0x9c8c`. None of those branches changes
`r5`, which is shifted into the sector at VA `0x9c90`.

The storage leaf likewise has no hidden bank interpretation in this path.
It receives read operation `1`, selects command word `0x02000010` for lengths
at most one sector or `0xa0002351` for longer reads, and passes the sector
unchanged in `r2` to VA `0x16924`. VA `0x1692e` stores that exact value at
controller object `+0x28`. Thus neither the `0xabcd` sentinel nor the read
command word is a partition selector derived from address bit 31.

This internal read path is callable by firmware startup, but the supported USB
target-`0x203` path cannot express it. Target `0x203` is family 2. Validator VA
`0x29382..0x293ae` requires both the requested address and address-plus-length
to remain below `0x01000000`. It rejects `0x80000000` before VA `0x9bd4` is
reached. No alternate supported USB read target that maps the high storage
bank was recovered in this bounded trace.

The region is linear in this function, not circular. The count ceiling is
`0x300000` records, giving data range:

```text
0x80004000 .. 0xe0003fff inclusive
```

No supported instruction wraps the persisted record index. The word
"circular" applies to the live `0xc00`-byte text buffer at RAM `0x20205000`,
not this persisted record area.

### Write-status boundary

The text rows are attempt/counter evidence only. At VA `0x205c0`, the data
call to write wrapper `0x9ee4` returns in `r0`; VA `0x205c4` immediately
overwrites `r0` with a RAM load and logs the Data Write row. At VA `0x20602`,
the header call returns in `r0`; VA `0x20606` immediately overwrites it with
another RAM load and logs the Hedaer Write row. Neither site compares, stores,
or branches on the returned status. The service resets staged count, advances
header counter, and updates RAM `0x2000085c` even after a failed lower write.
No readback or CRC appears in `0x20510..0x20623`.

### Staging RAM and fixed record layout

VA `0x762c` constructs a `0x200`-byte binary structure and copies it into:

```text
0x2000be40 + (old_B mod 10) * 0x200
```

VA `0x20510` calls the builder before incrementing `B`. Thus a new batch uses
slots 0 through 9 in chronological order; after the increment makes `B == 10`,
the contiguous write starts at RAM `0x2000be40` and spans all ten sectors.
For the first-runtime one-record flush, old `B == 0`, so the single record is
likewise in slot 0.

The beginning of each persisted record is exact:

| record offset | width | producer |
| ---: | ---: | --- |
| `+0x00` | 4 | total record number `N` from `0x20000858` |
| `+0x04` | 4 | session count from `0x20000860` |
| `+0x08` | 4 | low tick passed by `0x20510` |
| `+0x0c` | 4 | zero passed by `0x20510` (high tick slot) |
| `+0x10` | 2 | return of `0x27664` |
| `+0x12` | 2 | same return of `0x27664` |
| `+0x14` | 2 | return of `0x7d5c` |
| `+0x16` | 2 | return of `0x7cf0` |
| `+0x18` | 8 | pair returned by `0x38b14` |
| `+0x20` | 4 | return of `0x27658` |
| `+0x24` | 4 | return of `0x7d50` |
| `+0x28` | 4 | return of `0x1c544` |
| `+0x2c` | 4 | return of `0x1c480` |
| `+0x30` | 1 | return of `0x1e020` |
| `+0x31` | 1 | return of `0x1e014` |
| `+0x32` | 18 | nine halfwords from `0x2703c` |

The remainder through `+0x1ff` is also a fixed firmware structure populated
from controller state, MMIO-derived fields, counters, and arrays before a
single `memcpy(..., 0x200)` at `0x7c4e..0x7c56`. Semantic names for all of
those later fields were not recovered, so this report does not invent them.
The first words are enough to order records and inspect the producer tick
without guessing from strings.

## Header copies, layout, and selection

Each metadata header is one sector:

```text
selector 0 -> byte address 0x80000000
selector 1 -> byte address 0x80000200
```

After each data batch, `0x205da..0x205e6` increments the header counter and
sets `selector = counter & 1`. VA `0x7c80` builds a zero-filled sector,
populates the fields below, calculates word 0 so the unsigned sum of all 128
little-endian 32-bit words is `0xffffffff`, and VA `0x205f4..0x20602` requests
the selected-sector write.

| header offset | width | value/provenance |
| ---: | ---: | --- |
| `+0x00` | 4 | checksum word: `0xffffffff - sum(words[1..127])` |
| `+0x04` | variable NUL string | copied from pointer stored at RAM `0x2000086c` |
| `+0x08` | 4 | total record count `N` advertised by this header attempt |
| `+0x0c` | 4 | layout magic `0x00030304` |
| `+0x10` | 4 | session count from RAM `0x20000860` |
| `+0x14` | 4 | zero/reserved in this builder |
| `+0x18` | 4 | header-attempt low tick passed from `0x20510` |
| `+0x1c` | 4 | zero/high tick slot |
| `+0x20..+0x1ff` | 480 | zero in this builder |

Startup function `0x20454` asks `0x56f0` to read both selectors. The lower
read retries up to three times and accepts a header only if all of these hold:

- the read helper reports success;
- the sum of all 128 words is `0xffffffff`;
- the NUL string at `+0x04` matches the runtime identifier at
  `*(char **)0x2000086c`;
- caller `0x20454` sees magic `0x00030304` at `+0x0c`; and
- its `+0x08` record count is strictly greater than the best count already
  accepted in this startup pass.

For an accepted winner, startup restores `+0x08` to total count
`0x20000858`, `+0x10` to session count `0x20000860`, low tick `+0x18` to
`0x20000864`, and the winning selector number to `0x20000868`. A tie does not
replace the first accepted selector. A later header attempt increments that
restored selector/counter and therefore targets the opposite header.

The text capture independently agrees: header counters 41, 42, 43 select 1,
0, 1. The newest text-evidenced attempted batch ends at record 197175; Copy
rows 197176..197182 were staged afterward. The text alone proves neither the
197175 batch nor its header was durable.

## Other captured line producers and loop discrimination

The exact package producers are:

| text | producer VA | decisive dataflow |
| --- | ---: | --- |
| `VD Degrad.(%d) : %d %d` | `0x497c..0x4a6c`, log call `0x4a2e` | three iterations supply index, source word, calculated word |
| `mod_match: ...` | `0x32c9c`, log call `0x32ce8` | first verifies three bytes at object `+0x0d` equal `+0x0a`, then logs two string getters and bytes `+0x0a..+0x0c` |
| `framework_ch:%d, p_sen_ch:%d` | `0x35548`, log call `0x35592` | logs object byte `+0x23` and word read from MMIO `0x58602a08` |
| `fe_p_sen_ch:%d` | `0x3682c`, log call `0x36840` | runs `0x365dc(arg)` and `0x3628c(arg)`, then logs the original argument |
| `deadPool:%d` | `0x3ab40`, log call `0x3ab4c` | stores/logs its argument; distinct from setter VA `0x3ab34` |
| three persistence rows | `0x20510` | fields and storage flow documented above |

For discrimination, the strongest result is negative: persistence activity
cannot distinguish the emergency schedule from the ordinary schedule.
There are exact direct calls to the same VA `0x20510` at emergency-loop VA
`0xb6f0` and ordinary-loop VA `0x39c08`. Both schedules also call the same
text-buffer drain, VA `0x39404` (`0xb6e8` with argument zero and `0x39bdc`
with argument zero). Therefore continuing Copy/eMMC lines and a moving text
buffer prove live service, not ordinary-loop survival.

`deadPool:` requires VA `0x3ab40`; the emergency loop's direct VA `0x3ab34(1)`
only writes byte `0x20000e30` and emits no text. That same byte enables both
VA `0x20510` and VA `0x276ec`, which are retained in the emergency loop.
Thus the nearby `deadPool:1` line must not be misattributed to the setter, and
its presence is not a proof that the normal top-level schedule ran.

The other four producers are downstream state/event paths rather than direct
calls in either top-level schedule. The bounded direct-call census does not
close their reachability through computed callbacks, interrupts, or the
separately linked image, so their observed activity is **inconclusive** as a
normal-versus-emergency discriminator. It must not be promoted to proof that
an ordinary-only top-level call ran. A useful discriminating marker would have
to be tied to one of the thirteen ordinary-only scheduled calls and exclude
asynchronous reachability, not merely be absent from the six direct emergency
calls. In particular, `0x39404`, `0x20510`, `0x276ec`, `0x16fc0`, and
`0x1f3e4` are retained by the emergency loop.

## Transport-cleared read boundary and bounded RAM candidates

No acquisition was performed here. The earlier `0x400 @ 0x80000000`
recommendation is withdrawn: target `0x203` rejects it at the family-2
`<0x01000000` range gate. No high-storage-bank request is cleared by the
recovered USB protocol, and no such request has been issued.

The supported read-only alternative is the already proved target-`0x101`
direct-memory path using the live DMA alias. Family 1 is explicitly accepted
by validator VA `0x292de..0x292e6` and does not take the family-2 16 MiB
address/range checks. Prior retained live reads establish that CPU RAM
`0x20000580` is visible through alias `0x45000580`; therefore the corresponding
aliases below follow the proved `+0x25000000` mapping rather than inventing a
new storage route. The largest request is `0x1400`, below the same live vendor
path's already exercised `0x2000` chunk size.

The exact bounded three-read candidate is:

| order | target | alias address | length | 12-byte little-endian header |
| ---: | ---: | ---: | ---: | --- |
| 1 | `0x101` | `0x45000850` | `0x2c` | `01010000500800452c000000` |
| 2 | `0x101` | `0x4500be40` | `0x1400` | `0101000040be004500140000` |
| 3 | `0x101` | `0x45000850` | `0x2c` | `01010000500800452c000000` |

The two metadata reads bracket the larger staging-buffer read. Accept a
coherent snapshot only when total count, last-attempt count, staged count, and
header-attempt counter agree in both metadata copies. If any changes, retain
all raw bytes and report a race; do not loop indefinitely or escalate to a
storage write/reset path.

The `0x2c` metadata block at CPU `0x20000850` has these exact fields:

| offset | RAM | width | bounded use |
| ---: | ---: | ---: | --- |
| `+0x00` | `0x20000850` | 4 | last record-service tick |
| `+0x04` | `0x20000854` | 1 | first-record/session latch used by `0x762c` |
| `+0x08` | `0x20000858` | 4 | total record number `N` |
| `+0x0c` | `0x2000085c` | 4 | `N` copied after the most recent header write attempt |
| `+0x10` | `0x20000860` | 4 | session count |
| `+0x14` | `0x20000864` | 4 | low tick restored from the startup-selected header |
| `+0x18` | `0x20000868` | 4 | current header-attempt counter; low bit selects header |
| `+0x1c` | `0x2000086c` | 4 | runtime identifier-string pointer |
| `+0x20` | `0x20000870` | 2 | rotating telemetry sub-index used by the record builder |
| `+0x24` | `0x20000874` | 4 | current staged-record count `B` |
| `+0x28` | `0x20000878` | 4 | flush threshold, normally ten after first attempt |

For stable `1 <= B <= 10`, staging slots 0 through `B-1` contain the current
batch in order. At `B == 10`, its eMMC request may already be in flight;
durability is still unknown. Require each slot's `+0x00` record number to be
`N-B+1 .. N` and its `+0x08` tick to advance monotonically modulo 32 bits.
Slots `B..9` are stale and must not be treated as current. When `B == 0`,
there is no current staged record; slot 0 may contain the last generated
header image and slots 1..9 may be stale records. Values `B > 10`,
`N > 0x300000`, or inconsistent record numbers are rejection/race indicators.

This RAM route cannot retrieve arbitrary older persisted records or both
on-media headers. It can recover the currently staged window plus exact live
producer counters, which is the only bounded route presently cleared by both
the firmware validator and the demonstrated DMA alias. The historical host
uptime 75262 still cannot be converted into a record address without a proved
cross-clock anchor and a supported high-bank read route.

## Failure modes, security, rollback, and verification gate

- **False-success transport:** target operation 3 returned the retained 5 MiB
  byte stream, but its caller ignores the storage leaf's status. For the RAM
  candidate, require exact OUT/IN lengths, cleanup, two stable metadata copies,
  plausible bounds, record-number continuity, raw SHA-256, and non-stale
  content. A generic helper `Accepted` bit is not fresh-read proof.
- **Address-domain separation:** `0x80000000` is the internal wrapper's byte
  address and becomes storage sector `0x00400000`; target `0x203` rejects it
  because family 2 is restricted below `0x01000000`. Do not send a truncated,
  masked, wrapped, sector-number, or target-`0x101` version of that address.
- **Unproved durability/torn update:** the service requests data first and a
  header second, but ignores both statuses. Text rows prove attempted calls and
  firmware counter advancement only. A valid header recovered independently
  would advertise a prefix; it still requires generation/freshness checks.
- **Stale generation/header:** the header embeds a runtime identifier string.
  Offline validation can check checksum/magic/count, but equality to current
  runtime identity needs retained bytes from the device. A mismatch is a stop
  condition, not permission to rewrite the header.
- **Counter/tick wrap:** record count is bounded before 32-bit overflow, but
  the stored low tick may wrap. Do not binary-search tick values across a wrap
  without first detecting it.
- **Sensitive telemetry:** raw records include broad controller state and
  MMIO-derived values. Keep them local with existing evidence permissions;
  do not upload them merely to decode field names.
- **Snapshot race:** the producer can change staging RAM during a read. The
  metadata-buffer-metadata sequence detects, but cannot prevent, that race.
  One mismatch permits reporting incoherence, not an unbounded retry loop.
- **Rollback:** the proposed alias acquisitions are read-only, so there is no
  storage rollback. On any mismatch, release/close the existing transport
  normally and stop. Do not reset, retry through a write-capable path, erase,
  repair, select a bank, or flash firmware.
- **Migration risk:** transplanting this layout to the older stored image is
  unsafe. Its producer offsets/hashes differ and it lacks the three exact
  persistence formats. Re-derive constants before using the method on any
  other build; do not assume address stability from nearby shifted strings.

Verification is reproducible with:

```bash
PYTHONPATH=/tmp/tcon-capstone python3 \
  ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/executing-image-identity-20261027e/persisted-log-trace.py
```

The verifier uses explicit `need()` failures, not Python `assert`, so checks
remain active under `python -O`. It verifies all three source hashes, decisive
range hashes, package formats, their absence in the stored image, both direct
schedule calls, wrapper read/write modes, ignored write statuses, family-2
range gates, and captured attempt cadence. If a `0x200`/`0x400` raw header file
is later retained through some independently supported route, `--header PATH`
parses it offline without contacting the controller; this option is not a
claim that target `0x203` can acquire the high-bank header.

Three already-retained raw files from the bounded RAM sequence can be checked
without device access using:

```bash
PYTHONPATH=/tmp/tcon-capstone python3 persisted-log-trace.py \
  --metadata-before META_A.bin --staging STAGING.bin \
  --metadata-after META_B.bin
```

The parser requires exact sizes `0x2c`, `0x1400`, and `0x2c`, stable critical
counters, bounded `N/B`, expected current-slot record numbers, and advancing
modulo-32-bit record ticks. It reports SHA-256 for every raw input and never
acquires or writes anything.
