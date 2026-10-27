# AP_EXCO baseline versus the saved candidate context

The selected package and the already recovered controller backup have
byte-identical AP_EXCO directory records and both AP_EXCO payloads. The
ordinary callback's two source bytes are **20 and 0 in both baselines**.
The later saved candidate context contains **1 and 3** at the corresponding
mirror offsets. An older stored firmware generation therefore does not, by
itself, explain this particular difference between baseline and observed
context.

This comparison uses only the existing local files; it sends no TV request
and does not explore an active bank or persisted selection. The package
loader/ordinary callback trace supplies the source arithmetic:

| Source | Copied payload geometry | SHA256 |
| --- | --- | --- |
| AP_EXCO metadata | FILE `0x85e00`, 512 bytes | `dad4caf149769f0b363a11231267d73752802a3bd7484bd720562bbaa7be1cd8` |
| first payload | FILE `0x182200`, `0x33a` bytes | `c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf` |
| second payload | FILE `0x182600`, `0x1200` bytes | `5000ce2a135b4b463505a32cf5b525916605b32c21a20de4bd91607d4b839761` |

Object offset `+0` is first-payload byte `0x182200`, value 0. Object offset
`+0x3d8` is second-payload byte `0x182600 + (0x3d8-0x33a) = 0x18269e`,
value 20. The selected and recovered complete artifacts are independently
SHA-pinned by `compare-ap-exco.py` before this record/payload comparison.

The saved 16-byte candidate window is
`70 08 80 07 40 0b 5c 01 03 00 00 00 00 00 00 00`. Its startup constants,
handshake-like byte and numeric mirror agreement provide context-layout
corroboration, as described in the frozen D7 reports. They do not prove the
live AP_EXCO source object, a universal CPU/bus alias, which callback ran,
or a named setting.

The remaining ordinary question is which runtime writer or handoff supplies
the actual source/mirror values. No answer is inferred from numeric 1, 3 or
20 alone. The separate runtime-origin trace is outside the D7 frozen
checkpoint. Neither this comparison nor the earlier captures justify
silently substituting static defaults into the event-time predicate.

`compare-ap-exco.py` emits `comparison.json` reproducibly using standard
Python and zero target operations.
