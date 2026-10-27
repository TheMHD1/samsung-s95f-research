# Pre-PD header/control consumer follow-up

Recorded 2026-10-27 UTC. This is a bounded offline source trace of the
selected image-0 package. It made no TV, network, root, USB, device-node,
firmware, UI, setting, or configuration operation. Image-0 coordinates use
`FILE = VA + 0x200`.

## Result

No direct selected-image-0 constant pointing into the header/control prefix
`[0x58410000, 0x58410178)` was found. Across every byte position in the
`0x40000`-byte image-0 window, no little-endian 32-bit value falls in that
range. No Thumb `MOVT` contains high half `0x5841`. The two already known
fixed companion consumers start at `0x58410178` and use only forward indices
`0..15`; neither reaches backward into the prefix.

The only positive bounded selected-image copy/write path remains the generic
type-7 package loader:

```text
FILE [0x88000, 0x88ab0) -> CPU [0x58410000, 0x58410ab0)
```

If that loader path executes successfully, it copies the stored package
payload into the entire named `Pre-PD` range, including both the companion and
the four-lane source. Loader execution on the observed boot was not captured,
and this is not a runtime refresh edge. The stored four-lane source is zero
while later ordinary derived values were nonzero, so the bounded package-copy
path does not explain the live producer observed indirectly in W.

This pass therefore found no source-backed sample-latch, refresh, counter, or
readiness control in the header prefix, and no new positive producer edge for
`0x584109a4`. That result closes this particular static-header lead: the next
diagnostic should not treat an uncaptured prefix field as a known readiness or
refresh control. The runtime table producer remains outside the positive
ordinary image-0 edges established here.

## Exact bounded evidence

The selected package is
`selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`, SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.

The whole 5 MiB package contains exactly one byte-positioned 32-bit value in
the header-prefix range: `0x58410000` at FILE `0x80624`. This is the address
field at `Pre-PD` metadata record offset `+0x24`, outside image 0. The complete
record at FILE `0x80600..0x807ff` has SHA-256
`11696518d668a8c2ac409a0cf2d7a7e462f2e410bba6e5a0747007618e2ec87f`
and the reviewed fields:

| offset | value | bounded meaning |
| ---: | ---: | --- |
| `+0x20` | `7` | loader type |
| `+0x24` | `0x58410000` | destination base |
| `+0x28` | `1` | first-group count |
| `+0x2c` | `0x8000` | source offset from package configuration base |
| `+0x6c` | `0` | destination offset |
| `+0xac` | `0xab0` | copy length |

The checker pins the reviewed type-7 dispatch at VA `0x7586..0x75a1`, its
first-group loader slice at VA `0x5c74..0x5e23`, and the complete stored
payload SHA-256
`af62caa7f38a9a6a3702901ca84aa09a9ae895f1b498cabc846e51469872ddd8`.
This proves package/load-path semantics, not that the copy ran on the observed
boot or that its result remained current.

The fixed companion literal `0x58410178` occurs at VAs `0x10428` and
`0x19334`, loaded at `0x10342` and `0x190b2`. In complete consumers
`0x10334..0x10423` and `0x19064..0x1932f`, all companion loads use indices
`0..15`, hence byte offsets `0..0x3c`. The first consumer uses `(index-1)`
only after excluding index zero; the second copies `L[index]` for the same
bounded index range. These are forward reads of
`[0x58410178,0x584101b8)`, not control-prefix accesses.

The broader literal `0x58400000` still occurs at VAs `0x713c` and `0x1f3d4`.
Its direct sites at `0x70a2` and `0x1f3ca` store at offset zero. They do not
derive `+0x10000`, `+0x10178`, or `+0x109a4`, so they add no `Pre-PD`
header or producer edge.

## Scope and limits

This is not a whole-program absence proof. The byte-positioned constant scan
and high-half `MOVT` scan do not exclude:

- a pointer passed by a caller or peripheral;
- multi-step arithmetic from another base;
- DMA or hardware updates;
- code outside selected image 0; or
- a producer whose destination is computed without an embedded address.

It also deliberately does not repeat Y's exact `0x584109a4` table-address
census, AB's stored-value comparison, AD's image-1 census, or AA's updater
invocation trace. Those reports are hash-pinned inputs. The useful new result
is narrower: the selected ordinary image-0 code contains no direct header-
prefix pointer, and the known companion paths do not walk backward into that
prefix. No semantics should be assigned to those uncaptured bytes from this
evidence.

## Reproduction

Run:

```sh
python3 prepd-control-consumers-reproduce.py --self-test
python3 -O prepd-control-consumers-reproduce.py --self-test
```

The standard-library-only checker pins the selected package and four required
prior reports, verifies the metadata/load edge and the two complete companion
consumer bodies, performs the bounded prefix scans, and exercises mutations
of the metadata, an inserted header pointer, and a companion load.
