# Pre-PD stored values and the remaining runtime source gap

2026-10-27 UTC. This is an offline read of the retained selected package and W
snapshot. It makes no TV, network, root, USB, register, UI or firmware request.
The enclosing-record association is established in the corrected
[Y source trace](../ap-table-source-20261027y/table-source-trace.md).

The `Pre-PD` record's first group describes package source FILE `[0x88000,
0x88ab0)` for address range `[0x58410000,0x58410ab0)`. These stored bytes are
not a live read of that address range and are not proof of successful loading
on the observed boot.

| stored range | exact fact |
| --- | --- |
| FILE `[0x889a4,0x88aa4)` | the full four-lane table region is 256 zero bytes, 64 zero u32 words |
| FILE `[0x88178,0x881b8)` | the companion region holds 16 strictly descending u32 constants |

The companion constants are:

```text
960, 768, 640, 512, 448, 384, 320, 256,
192, 160, 128, 96, 64, 36, 1, 0
```

This provides a concrete parameter sequence for tracing the companion's
consumers. It does not identify the values as pixel/luma levels or a known
histogram's boundaries. Their being numerically within ten bits is not a
field-unit or hardware-format identification. `Pre-PD` is retained verbatim
as a package record name; no expansion of the abbreviation is asserted.

Both of the first helper's selected sums would be zero if their source words
were those stored zero table values. W instead returned nonzero mirrored sums
around 8.25 million. Under the recovered summation model, the stored zero table
alone therefore cannot reproduce W's returned mirrors. This comparison does
not distinguish runtime production, another initializer, a different live
source, stale mirrors or another writer. It also does not prove that W sampled
this table directly, that this package was loaded on that boot, or that the
mirrors and source would have been simultaneous.

The next code work can focus on how the `Pre-PD`-associated source is refreshed
and how the companion constants are consumed. A live normal/failing comparison
still needs physical-light annotation and qualified reads; this finding does
not create a new MMIO read plan or alter the reviewed recorder. Source units,
cadence, precise runtime writer and physical blackout causality remain open.

`verify-stored-values.py` pins the package, complete enclosing record, exact
metadata and range arithmetic, both stored regions and the W binary. It
checks the constants and returned mirrors using only Python's standard
library. It does not reproduce a controller execution or claim a repair.
