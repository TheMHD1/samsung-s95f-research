# Two cap-helper arrays: enclosing NPC package record

2026-10-27 UTC. This is a local selected-package metadata comparison. No TV,
network, root, USB, register, UI, firmware or configuration action was made.

The [AC consumer trace](../pre-pd-companion-consumers-20261027ac/companion-consumers.md)
identified two fixed three-word inputs to its shared helper:
`C[k] = max_u32(word[0x584301f0+4k], word[0x584311f0+4k])`.
Both complete arrays fall inside first-group ranges of a type-7 package record
named **NPC**, at FILE `[0x81400,0x81600)`.

The exact metadata is base `0x58430000`, first-group count `2`:

| entry | source offset from configuration base FILE 0x80000 | destination offset from metadata base | length | described address range |
| ---: | ---: | ---: | ---: | --- |
| 0 | `0x11600` | `0` | `0x8e0` | `[0x58430000,0x584308e0)` |
| 1 | `0x11ee0` | `0x1000` | `0x8e0` | `[0x58431000,0x584318e0)` |

Each array is at offset `0x1f0` within its respective entry. Their described
stored source bytes are therefore FILE `[0x917f0,0x917fc)` and
`[0x920d0,0x920dc)`; each contains three zero u32 words.

This gives an enclosing package-record association for inputs previously
unnamed at that level. It does not assign individual field names, units or
current values, prove successful initialization on the observed boot, or
identify what refreshes either array. The labels “cap” and `C` describe their
mathematical role in the recovered ordinary calculations, not a physical
safety limit or a proposed adjustment.

The type-7 first-group source/destination/length semantics were independently
decoded and byte-bound in [Y](../ap-table-source-20261027y/table-source-trace.md).
This report uses those same semantics for both entries, including the second
entry's nonzero destination offset; merely adding the source offset to the
destination base would give the wrong address.

The `NPC` packaged address record and the `NPC_AP` RAM record are distinct
bindings. A shared substring in their names does not prove an alias or
equivalence. The actual getter/code edges in AC establish how the two fixed
arrays are read alongside outputs written into `NPC_AP`; this metadata does
not add a physical or runtime ownership claim.

`verify-cap-record.py` pins the selected package, complete NPC record, the
two byte-identical cap helpers and the reviewed type-7 loader slice. It
checks both descriptor-array entries, complete three-word containment,
helper literals, stored source arithmetic and zero values. No live values,
producer, physical blackout cause or fix is established.
