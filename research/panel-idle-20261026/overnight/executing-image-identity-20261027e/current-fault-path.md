# D5 current-vs-active fault-path coordinates

Read-only static audit. Image-0 stored FILE = linked VA + `0x200`.

Current backup: `firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin`,
SHA-256 `f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562`.

## Active-generation qualification

`callback-alias-read-once/record.json` has SHA-256
`1521a21b322d6899124d94587b9e06d5570e66b12993b55684aaf88930f4a791` and
returned the clean callback tuple:

```text
2945d 293d1 294fb 00000000
00000 28b85 28cf1 294f5
```

This matches the selected packaged callback prediction. It establishes the
active callback generation at the translated alias, but not whole-image
identity. Consequently, packaged coordinates below are the active-generation
hypotheses; current-backup coordinates are comparison evidence only.

## Exact VA/FILE distinctions

The older protection report’s numeric labels were FILE offsets despite being
described as linked VAs. Correct coordinates are:

| path | linked VA | stored FILE |
|---|---:|---:|
| packaged EEPROM check | `0x97e8..0x9868` | `0x99e8..0x9a68` |
| packaged feedback/check-repair | `0x9968..0x99fe` | `0x9b68..0x9bfe` |
| packaged recurring live loop | `0x214d4..0x21510` | `0x216d4..0x21710` |
| current stored EEPROM check | `0x97d0..0x9850` | `0x99d0..0x9a50` |
| current stored feedback/check-repair | `0x9950..0x99e6` | `0x9b50..0x9be6` |
| current stored recurring live loop | `0x21254..0x21290` | `0x21454..0x21490` |

The packaged live loop at linked VA `0x214d4` tests `+0x240a` bit 0 and, if
set, calls the common event helper then selector `0x10` dispatch. Its sole
known loop caller is packaged linked VA `0x39be8` (stored FILE `0x39de8`).

The current stored live-loop equivalent at linked VA `0x21254` has the same
shape but different helper targets. It must not be treated as executing code
without an immutable code read proving that identity.

## Guards and candidate checkpoints

Packaged EEPROM check VA `0x97e8` reads EEPROM `0xe0`, sets `+0x2466`, reads
`+0x24aa`/`+0x2484`, and calls selector `0x10` at VA `0x9834` or `0x9862`.
Packaged feedback VA `0x9968` increments `+0x24ac`, writes EEPROM bytes 2/3,
and retries readback ten times before VA `0x99f8` calls the event helper.
The packaged recurring loop VA `0x214d4` tests `+0x240a` and dispatches
selector `0x10` at VA `0x214f2`.

These are the most useful non-mutating checkpoint boundaries, together with
fields `+0x240a`, `+0x240e`, `+0x2466`, `+0x2484`, `+0x24aa`, and `+0x24ac`.
They identify software protection/event ingress, not a proven panel-power
command or kernel crash.

## DMA mapping

Current mapper linked VA `0x9a48..0x9a6c` loads literal `0xe00fdfdc` at VA
`0x9a70`; input `0x20000000..0x20200000` maps by `+0x25000000` for core tag
`0xa`, otherwise by `+0x27000000`. The operation-3 CPU destination is
`0x20001bc0`; raw `0x20000580` is therefore not the relevant USB DMA window.

## Reproduction

Run `D5/verify-current-fault-path.py` with `PYTHONPATH=/tmp/tcon-capstone`.
It pins both images, reports SHA-256 hashes of the exact VA slices above, and
checks the key Capstone instruction sequences and VA/FILE conversion.
