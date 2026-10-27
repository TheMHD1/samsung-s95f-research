# Ordinary selected-image usage of the four emergency-path MMIO blocks

Recorded 2026-10-27 UTC. This is a bounded offline review of the selected
package's image 0. It made no TV, root, USB, controller, network, MMIO,
firmware, power, reset, or physical-observation operation. It does not propose
a write, patch, bypass, forced state, collector, or protection change.

## Result

The four emergency-path MMIO addresses are **not unique to the emergency
path** in the selected image. The broad pre-loop initialization sequence calls
the corrected helpers `0x3dfc` and `0x3e14` and directly writes all four exact
addresses before entering the ordinary recurring loop:

| exact address | pre-loop initialization writes established here | selector/emergency use already established |
| --- | --- | --- |
| `0x40130010` | `8` via `0x3dfc`, then direct `0x10` | `8` via the same `0x3dfc` helper |
| `0x40131010` | direct `4` | final `0x25b24(nonzero)` store of `4` |
| `0x40132010` | `0x200` via `0x3e14`, then direct `0x80` (and further initialization values) | conditional `0x200`, then final `0x80` |
| `0x4013400c` | direct `8` | selector-`0x10` direct store of `0x10` |

Thus the emergency sequence reuses an ordinarily initialized hardware-block
family; it is not the sole code context that touches these addresses. The
strongest new conclusion is about reuse and non-uniqueness, not physical
meaning. The bytes still do not identify a panel rail, enable, reset, scan,
timing, PWM, or pixel-output register, and they do not prove that the selected
package was the executing image or that any particular runtime write occurred.
Sharing an address—or even an address/value pair—does not prove that two
contexts have the same higher-level state or semantics. In particular, the
`8` versus `0x10` writes to `0x4013400c` cannot be interpreted as an
overwrite, bit set/clear, or persistent readback state without the missing
register contract.

The same image contains generic indexed configuration and status helpers over
six bases from `0x40130000` through `0x40135000`. This positively places all
four addresses in a broader regularly spaced control-block family. Without a
chip register map or a qualified live binding, the family remains unnamed.
GPIO-related strings elsewhere in the asset are not sufficient: this bounded
trace found no direct string reference that names these exact helpers or
registers, so no GPIO role is inferred from string proximity.

## Inputs and corrected coordinates

The selected package is:

```text
overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin
size    5242880
SHA256  bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

Image 0 uses `FILE = VA + 0x200`. The functions reviewed here are therefore
the corrected image-0 VAs `0x3dfc`, `0x3e14`, and `0x25b24`; the older
`0x3ffc`, `0x4014`, and `0x25d24` names were file-offset-shifted by `0x200`.

The following existing reports were read only to preserve their established
results and boundaries:

| report | SHA-256 |
| --- | --- |
| `rtp-action-causality-20261027t/rtp-action-causality.md` | `4465ca1a50b9c4a851cf0233a4172e930987b1b1dec7f1b7d3972e264755dbb5` |
| `tcon-research/owner-photo-board-map.md` | `93ede258bbb6f5b163466205c0ed828cf0b912ec0a1dacdc9ec7371d07f0f0a3` |
| `tcon-research/qd-emergency-loop-output-sequence.md` | `02fe780962a6c4894351aea6b547aa03628c92d64b95a56f69f1d3b717230a6d` |

No storage, return-guard, high-bank, bootloader, or emergency-loop branch was
followed beyond the already bounded selector action. In particular, this work
does not revisit the excluded calls following the selector-`0x10` MMIO store.

## Exact small helpers

### `0x3dfc..0x3e13`

This complete 24-byte body has SHA-256
`fcb86b1b0ae40b9bc1028553195339714f4093f392c17ab6379d05c71d292583`.
It performs only:

```text
*(u8 *)0x20000cb0 = 0
*(u32 *)0x40130010 = 0x00000008
return
```

The MMIO address is encoded as literal base `0x40130000` followed by a
32-bit store at `+0x10`; it is not inferred from numerical adjacency.

### `0x3e14..0x3e2b`

This complete 24-byte body has SHA-256
`6dcca660a03c895a2a4f098dbe79d8d35485dbd55acefb4b083161613e9763b1`.
It performs only:

```text
*(u8 *)0x20000cb1 = 0
*(u32 *)0x40132010 = 0x00000200
return
```

Again, the exact destination is literal base `0x40132000` plus `0x10`.
The paired RAM-byte clears are proven, but their semantic names and relation
to the MMIO commands remain unknown.

### `0x25b24..0x25b5f`

This complete corrected body has SHA-256
`94f4a4f1407e57b0e80f80fa4b16b353b6c41dd7f98d566203b916f1f1387b48`.
It:

1. obtains the common object;
2. always calls `0x3dfc`;
3. calls `0x3e14` only when common halfword `+0x36` is zero or one;
4. passes common halfword `+0x92` to `0x10de0`; and
5. only when its argument is nonzero, stores `0x80` at `0x40132010` and
   then `4` at `0x40131010`.

The direct halfword-aligned BL census finds `0x25b24` called only at
`0x14976`, `0x14998`, `0x149a6`, and `0x149b0`, all inside the selected
`0x14910` selector-action body. This bounded direct-call result does not
exclude indirect or computed calls.

## Ordinary pre-loop counterpart

The complete `0x1e02c..0x1e32d` body has SHA-256
`310b70a2bda4673776316802a58fb30fbc031ec91f0b7776450d0fd1ec434bbe`.
Its only direct BL callers in the finite halfword-aligned image-0 census are
`0x39a3e` and `0x39b3a`. Both occur in the broad initialization sequence
before the ordinary recurring loop begins at `0x39bda` and branches back at
`0x39c4c`.

Within that initialization body, the exact ordering relevant here is:

```text
0x1e258  call 0x3e14             -> 0x40132010 = 0x00000200
0x1e266  base 0x40134000, +0x0c -> 0x4013400c = 0x00000008
0x1e272  call 0x3dfc             -> 0x40130010 = 0x00000008
0x1e280  base 0x40130000, +0x10 -> 0x40130010 = 0x00000010
0x1e28e  base 0x40131000, +0x10 -> 0x40131010 = 0x00000004
0x1e29c  base 0x40132000, +0x10 -> 0x40132010 = 0x00000080
```

The function continues writing other values to the same block family. Those
additional stores reinforce that this is a configuration sequence, but do
not supply hardware names. The important exact comparisons are:

- ordinary initialization and `0x25b24(nonzero)` both store `4` at
  `0x40131010` and `0x80` at `0x40132010`;
- ordinary initialization and the selector action both invoke `0x3dfc`, so
  both store `8` at `0x40130010`; and
- ordinary initialization stores `8` at `0x4013400c`, whereas selector
  `0x10` stores `0x10` there.

The direct-call census also finds five non-`0x25b24` call sites for each
small helper:

```text
0x3dfc: 1dce6 1dd02 1dd4c 1dd80 1e272   [plus 25b2e]
0x3e14: 1dce2 1dd06 1dd48 1de90 1e258   [plus 25b3c]
```

This is further positive evidence that the two fixed-store helpers are shared
lifecycle/configuration operations rather than code private to the selector
action. It is not a global caller-absence proof.

## Generic six-block configuration/status pair

Two complete source bodies independently expose the regular block layout:

| body | SHA-256 | bounded behavior |
| --- | --- | --- |
| `0x40f4..0x41cf` | `e3ffa3b78352ea9121badf6c6bd5024b514e319c5ab29af6700bc19e9ae65aec` | selects one of six bases, then read/modify/writes a selected nibble in base `+0` or `+4` |
| `0x41d0..0x423b` | `ff2fdbe01813c49a772f4a0bb9f2462ae8d51b65e22e7ffc0d7537d179d807d9` | selects the same six bases, reads base `+0x18`, and returns one selected bit |

Both bodies contain the same literal base list:

```text
0x40130000  0x40131000  0x40132000
0x40133000  0x40134000  0x40135000
```

Input ranges `0x00..0x5f` choose the block in steps of `0x10`. The first
helper uses the input modulo 16 to choose the lower or upper configuration
word and the input modulo 8 to choose a four-bit field. The second uses the
input modulo 16 to select a status bit from `+0x18`. Direct wrapper bodies
`0xd810` and `0xd822` call them at `0xd81a` and `0xd82a`, respectively.

This is structurally compatible with a banked line/control peripheral, but
that description is deliberately generic. No reviewed chip map assigns a
name to the block, and the owner-photo board map cannot translate a CPU MMIO
literal into a photographed board signal or connector pin.

## Consequence for the output-causality gap

The prior causal result remains: selector `0x10` reaches real hardware-address
writes before its status store. This report narrows what those writes can
mean from code context:

- they are part of a broader ordinarily initialized block family;
- their exact addresses are not emergency-only;
- three emergency values (`8`, `4`, and `0x80`) also occur during ordinary
  pre-loop initialization; and
- `0x4013400c` receives a distinct ordinary value `8` and selector-`0x10`
  value `0x10`.

That makes “generic control/configuration command” better supported than
“dedicated emergency panel-off register.” It still does not determine whether
the selector values disable, enable, acknowledge, select, or pulse anything,
nor whether any effect is related to the physical black panel. A hardware
role requires a qualified register map or an independently observed signal;
neither is present here.

## Reproduction

`ordinary-io-usage-reproduce.py` uses only Python's standard library. It
hash-pins the selected package and the three boundary reports, pins complete
relevant image-0 ranges, verifies the literal bases and exact store opcodes,
reconstructs the finite direct-BL caller sets, and emits the bounded findings.

```text
python3 ordinary-io-usage-reproduce.py
python3 -O ordinary-io-usage-reproduce.py
```

Both modes must emit byte-identical JSON. No evidence check relies on Python
`assert` behavior.
