# Image0 return guards: reset and recovered configuration routes

Recorded 2026-10-27 UTC from the delegated offline startup and writer review.
No TV, firmware, register, EEPROM, GPIO or USB action was performed for this
analysis. Existing evidence is preserved. This report records static findings;
it does not measure the guards on the running controller.

## Result

Both emergency-loop return guards are zero after the packaged reset scatter
initialization. No ordinary startup initializer assigning the two required
magic values was recovered. The only recovered direct root writer is an
AP_EXCO configuration route for the second guard. No direct writer for the
first guard was recovered. A runtime mismatch remains conditional: subsequent
computed, external, DMA or configuration writes are not excluded.

## Source and address convention

The 5 MiB selected factory asset is
`overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin`,
SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Its identity with the entire currently executing controller image has not
been established. For image0 executable code, linked VA = file offset minus
0x200. Absolute RAM addresses do not receive that adjustment. All code
locations below are explicitly FILE offsets unless called VA.

## Reset and startup

Scatter record12 names source VA0x3e764, destination RAM0x20000f4c,
length0x16438 and handler VA0x1d8 (stored at FILE0x3d8). That handler is
the zero-fill operation. The destination range includes both halfwords:
common object RAM0x2000f0e0[0] and second object RAM0x2000ff14[0].
Consequently both are zero after this reset scatter operation.

Startup FILE0x39ba6 obtains the common object and calls FILE0x27d4, but that
callee discards the incoming r0; this is not a recovered guard initializer.
Startup FILE0x39c62 calls FILE0x2eb90. That body compares the two roots with
0x1234 and 0xabcd. On a match it changes adjacent common-object fields at
+0x170, +0x172, +0x174 and +0x80; it does not assign the two magic roots.

## Recovered writer boundary

The direct accessor census for the common root, FILE0xe870, recovered no
root-halfword store. The second-root accessor FILE0xe878 has a recovered
configuration route: FILE0xc6bc command0 stores a caller-provided halfword
at FILE0xc6f0. Its sole recovered direct caller FILE0x761e follows the
FILE0x75ec AP_EXCO name match. The command uses low16 bits; the value comes
from the first input halfword. Command0x228 compares the abcd magic for an
adjacent origin write, rather than assigning the root magic itself.

## Consequence and limits

The previously documented FILE0xb860 error path tests these roots only after
its selector action and history/status stores. Return requires 0x1234 and
0xabcd. Otherwise its unconditional emergency service loop does not recheck
the guards. Reset-zero plus no recovered ordinary initializer strengthens the
need to inspect runtime guard provenance, but does not establish their values
at the owner's fault or prove that every RT event enters the permanent loop.
The physical role of its touched MMIO registers remains unresolved. No guard
patch or bypass has been prepared or deployed.

## Reproducible source intervals

The parent verified the complete asset SHA and computed these exact retained
byte hashes while persisting the delegated findings. These are interval
identity checks, not a new independent whole-program analysis.

```text
FILE 0x340..0x390 exclusive-end: 68bc22e2c160866c599989df258b97f1c06f5b647b046a2639b9b67ebee927a0
FILE 0x3e340..0x3e400 exclusive-end: 3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d
FILE 0x39b98..0x39ce0 exclusive-end: df63aba1f8c755c6d29015bafae03c32a6e9f52489e18d3d8d10fef2c0ca2fe5
FILE 0x2eb90..0x2ebe0 exclusive-end: dcc18e0f55e1b1f9aaa4e4e8b53ca457c7dfd427aca579efb5816130b0c8d4af
FILE 0xb860..0xb8fa exclusive-end: 40e434612828833aa7b433798a352a99c766cbb47351d2cb42ba364a868d2c6a
FILE 0xc6bc..0xc730 exclusive-end: 461f1ea821d7ebe9d9e1cde733d47ad2b42780c6aa19edbb564f89fa9b25b617
FILE 0x75ec..0x7630 exclusive-end: bf04787b92b4f8ce9ca71fed37ba6e5260e4af8aa9c2d38224ac79dcfbc38565
```
