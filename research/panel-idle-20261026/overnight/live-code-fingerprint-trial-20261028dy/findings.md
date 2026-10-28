# Actual live code fingerprint at the proposed checkpoint sites

Recorded 2026-10-28 03:59 UTC. The fixed read-only probe completed and all
four16-byte payload hashes match the selected image1 firmware package. This
is new live sampled-code correspondence evidence, not a deployed debugger,
active instruction-fetch observation, whole-image identity or write-safety
qualification.

| Proposed execution-log role | Image1 linked window | Accepted bus window | Result |
|---|---|---|---|
| Aggregate score/threshold |0x2020..202f|0x46002020/16|Exact selected-package match|
| A/B pointer selection |0xbd58..bd67|0x4600bd58/16|Exact selected-package match|
| Qualifying tuple formatter |0xc5d0..c5df|0x4600c5d0/16|Exact selected-package match|
| Common fault setter |0xc1e0..c1ef|0x4600c1e0/16|Exact selected-package match|

The selected package SHA256 remains
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
DW source-qualifies the address conversion; DX fixes the four addresses,
lengths, hashes and request order without address or bank arguments.
Independent host implementation review passed before the target request.
The parent then verified the saved predecessor and all21 frozen source files,
regenerated the exact manifest, and obtained fresh cached identity/holder
metadata. The first production request followed accepted DM's completed
ReadyForHeader/released/closed/stage-absent boundary.

The actual capture is `code-read-01/`. It contains one production invocation,
four complete headers/eight bulk transfers and64 input bytes. The first
OUT-before to final IN-after interval is181530599387–181530604026us, a4639us
sequential transport span rather than an atomic instruction snapshot. All
transfers completed exactly. Native finished ReadyForHeader, released its
claim and closed its FD; exact wrapper cleanup returned STAGE_ABSENT. The
separate on-target fake selftest passed724 checks with zero target operations.
No mismatch, retry, fallback, key, reset or controller-memory write occurred.

The manifest is
`c4d51611cf638f0ac4e9e3003c3b72ee592f460df19ed6138ce57ae7e6e92fac`.
The saved readiness digest is
`340ea97bed1743a9bde185f9bbd2c276dfdc8a4ed19cee40219318821070573e`.
Original private raw receipts and64 code bytes are retained locally. Public
evidence should expose derived addresses/hashes and original research source,
without publishing those raw OEM payload files or authentication metadata.
The independent full capture replay is being frozen separately in
`live-analysis/`; its final inventory governs that analysis.

The TV's original alternate limit40 was verified in the preceding final DM
sample, and this code reader makes no configuration write. Apps was the last
cached UI selection. This probe does not resample RT state or measure panel
light; no unattended picture or continued-clean-state claim follows from it.
There is no installed execution hook or background target task.

## What remains before an execution logger

DS specifies what each hook would record: actual score/threshold, actual
selected pointers, actual qualifying operands, and the fault setter's event
and caller. The new probe closes the narrower source-alias/live-payload gap
at those four sampled windows. It does not establish the complete control
flow, actual fetch alias, code writability or instruction-cache visibility.

The next source investigation is positively owned logger memory and an
installation/removal mechanism with independent rollback. Existing stock
MODE2 recovery is real and has owner-confirmed Apps recoveries, but its
GPIO/USB reset evidence alone does not prove that an arbitrary overwritten
instruction would be reloaded. DZ investigates startup/scatter/heap/stack and
reset/reload source evidence. Zero-filled memory is not assumed to be spare,
and no executable patch is deployed while those properties remain unknown.
