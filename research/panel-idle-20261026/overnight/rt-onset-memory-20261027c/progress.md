# RT recorder qualification and a different storage header

This work adds a verified short recorder for the controller's full RT field
block and a read-only storage-sector result that changes patch planning.
The blackout remains unresolved. The physical picture was unobserved during
all three runs. No flash, protection value, EEPROM value, UI navigation or
panel-reset command was issued. Temporary helpers ended and their stages were
removed. Root remains host-assisted.

## Authoritative runtime results

The [reproducible audit](audit-runtime.py) checks raw authenticated transport
envelopes, exact command echoes, build identities, reconstructed upload chunks,
helper records, returned bytes/timing and cleanup. The read-only independent
reviewer separately reconciled those same artifacts. The preserved previous
90-file checkpoint is unchanged.

| Test | Actual result | Interpretation limit |
| --- | --- | --- |
| Fixed RT block read | OUT12/IN256, complete/accepted, release/close0, stage absent | A DMA snapshot can overlap field updates |
| Short RT recorder |20/20 accepted samples in4755ms;250–251ms start gaps; all payloads identical | Five-second unobserved baseline, no fault onset |
| Address-zero sector | OUT12/IN512, complete/accepted, release/close0, stage absent | Storage leaf return is discarded; freshness unproved |

All runs used boot34f419d2-6256-4e1f-a7a9-8d46b875857d. The recorder's
outer uptime101195.75–101200.96 encloses its actual sample window
101196.19–101200.94. The first read took43ms and subsequent reads1–8ms;
these are service latencies, not CPU-utilization or visible-impact measurements.
Every sample reopened, validated and closed its USB FD. The output23593bytes
fits the64KiB retention limit.35 injected cases passed before its active run,
including9 series/clock/failure cases with zero target operations.

## What the full RT block adds

All21 actual RT block reads in this work—one initial snapshot and20 later
samples—returned SHA256
`7044ed744404edf22eff6d90a7cc9cdcd5704cbbad5e0e2f85de03acfa23217d`.
The isolated first read and later short series do not establish continuity
between their windows.

| Relative block offset | Image0 address | Sample halfword | Bounded interpretation |
| --- | --- | ---: | --- |
|0x0a|0x4701240a|0|Live RT field whose bit0 feeds the reconstructed error path |
|0x10|0x47012410|4|Mode context; matches the packaged initializer |
|0x66|0x47012466|1|Consistent with the packaged successful EEPROM-signature check |
|0x84|0x47012484|0|History gate is zero in this sample |
|0x9e|0x4701249e|1|Already1 in the packaged initializer; image0 semantics unresolved |
|0xaa|0x470124aa|100|Comparison byte used by the packaged history branch |
|0xac|0x470124ac|243|History value differs from packaged zero; not a proven incident total |

Under the reconstructed packaged logic, the history branches require the
0x84 gate to be nonzero. A value243 exceeding100 therefore does not select
those branches for this sampled state. Clearing that history value is not a
supported fix. The [instruction-bound check](verify-history-interpretation.py)
pins the logic and the retained snapshot while explicitly leaving executing
image identity unproved.

The EEPROM-check function is linked image0 VA0x97e8 / stored FILE0x99e8.
The history-feedback function is VA0x9968 / FILE0x9b68. All image0 file
coordinates are VA+0x200. Some exploratory notes initially treated stored
offsets as linked addresses; parent direct disassembly corrected them before
using the interpretation. The fixed-root accessor at VA0xef94 returns
0x47010000. No EEPROM/helper function was invoked by this offline check.

Image1's separate root is0x20010000. Its local field0x2001249e participates
in a primary-event guard, but no bridge to0x4701249e is proved. The sampled
image0 value1 cannot be called a disabled image1 protection path.

## Address-zero sector reply differs from the selected package

The [512-byte reply](emmc-sector-read-once/returned-sector.bin) hashes to
`3683a8b7fb7937de2c8fc57b770e949e20ad528890a3ccc67b5c0cabaec9cb7a`.
The packaged first512 bytes hash to
`e7e66554e47c4925ffd142fcbe21fce5d72a591bbcad2ea312ad11e3c7f49694`.

| Header field | Returned bytes | Selected package |
| --- | --- | --- |
|Build tag at0x40|241205A|241230A|
|Timestamp text at0x80|12-05-2024 16:17:49|12-30-2024 15:56:21|
|Last8bytes|4200001503e8406c|420000ee03eae012|

Exactly13 byte offsets differ:044,045,083,084,08c,08e,08f,091,092,1fb,
1fd,1fe,1ff. Magic5a5aa5a5, compiler ARMCC_5.06.0.45, mcu_ata, platform and
builder labels match. This is a structured different reply, not a match to
the selected package's sector zero. The root/USB/stage records all reconcile.

The reconstructed packaged controller schedules the response even if the eMMC
leaf returns an error.
Thus a different stored object/slot, stale scratch content or a different
installed build remains possible; this alone cannot identify executing code.
The current profile had been selected through FW/MD strings and matching
parameter/USB layouts. Those facts survive, but they do not override this
new byte-level discrepancy. No absolute-offset firmware patch is ready.

## Next work toward diagnosis and repair

First, obtain disjoint code/config-sector fingerprints and then a bounded
read-only backup of the stock5MiB object. The next fingerprint should include
sector0x200 (packaged vector/startup bytes) and a protocol-code sector, with
exact transport counts and preserved mismatches. Distinct changing sectors
can strengthen address/freshness evidence; full length alone cannot. A full
backup needs its own output-file cap, aggregate hash, read-error accounting,
host chunk retrieval and verified cleanup before any restore/flash plan.

For physical onset, extend the qualified short recorder into a separately
reviewed finite armed capture. It should expose a ready/GO handshake before
opening USB, bound its wait and capture duration, stop on the first asserted
RT flag or I/O anomaly, and write bounded local records for chunked retrieval.
A60-second series would exceed the root response cap if returned inline, so
the current5-second wrapper must not simply be lengthened. Kernel/traffic
observer integration and longer capacity remain unqualified.

The owner-observed Apps/sparse-Home and HDMI patterns remain the causal test
controls. A future paired run needs fresh visible/black annotations while
the recorders are armed. Current zero RT fields and prior software reset
results cannot substitute for those observations or establish panel recovery.
