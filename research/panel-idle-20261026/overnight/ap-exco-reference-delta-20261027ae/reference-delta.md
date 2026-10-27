# Captured ordinary state versus two stored references

2026-10-27 UTC. This is a local comparison of the retained W capture with the
selected package and recovered stored backup. No new TV, network, root, USB,
register, UI or firmware operation was made.

The selected and recovered-backup ordinary AP_EXCO initializer payloads are
byte-identical, 826 bytes at FILE `0x182200`, SHA-256
`c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf`.
The [corrected S provenance](../ap-exco-helper-inputs-20261027s/ap-exco-helper-inputs.md)
binds that payload to the ordinary object; this is not the distinct derived
MULTI/AP_EXCO object. W retained only the first 824 ordinary bytes, and those
reads were sequential, not an atomic controller snapshot.

Of the 412 aligned halfwords in that prefix, 366 match both stored references
and 46 differ. No statement is made about the final two uncaptured bytes.

| known fields | both stored references | W captured values |
| --- | --- | --- |
| `+ca/+cc/+ce` helper controls | `1 / 1 / 0` | `1 / 1 / 0` |
| P0/P1/P2 at `+d0/+d4/+d8` | `7,464,960` each | same |
| P3 at `+dc` | `8,128,512` | same |
| debounce threshold `+e0` | `30` | `30` |
| counter `+e2` | `0` | `30` |
| counter `+e4` | `0` | `0` |
| helper output `+e6` | `0` | `1` |
| upper/tail selectors `+e8/+ea/+ec/+ee` | `0 / 3 / 3 / 3` | same |
| scale/caps `+f0/+f2/+f4/+f6` | `900 / 6 / 6 / 6` | same |
| computed indexes `+104/+106/+108` | `0 / 0 / 0` | `6 / 6 / 6` |
| recomputation enable `+116` | `1` | `1` |
| secondary controls `+2cc/+2ce` | `1 / 2` | `1 / 2` |
| secondary operand/counters `+2fc/+300/+302` | `0 / 0 / 0` | same |

The six first/recomputed sum mirrors are zero in both references and nonzero
in W. This is consistent with the already recovered calculation path and
the changed indexes/counter/output; it does not independently prove which
instructions wrote those values or in what order. Other differing offsets
are retained verbatim in the verifier output without assigning them units or
meaning.

The exact 90%/98% relationships to 3840×2160 were already present in both
stored initializers. They are therefore not, by themselves, evidence that a
live resolution-dependent calculation produced the captured thresholds.
Neither are they evidence of a threshold modification at the W sample: the
sampled values equal both stored references. This does not prove continuous
history, exclude earlier changes, identify which initializer was loaded, or
explain the physical blackout.

This comparison sharpens the next measurement: obtain the evolving source
sums, computed indexes, counter/output and derived selector during a working
control and a failing transition, while preserving the actual configuration
values in both records. Matching those late reference values does not make
them an approved tuning target or establish that changing them would fix the
damaged panel.

`verify-reference-delta.py` pins both complete retained images, S provenance,
the identical ordinary payload and W prefix. It reproduces all 46 differing
halfword offsets and the known-field comparisons using only local reads.
