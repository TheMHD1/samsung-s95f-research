# Independent review of selector-1 code-write readiness

Recorded 2026-10-27 UTC. This is an independent, offline review of
`code-write-readiness.md` and `verify-code-write-readiness.py` against the
original selected package, recovered storage backup, and frozen N mapped-view
capture. It made no TV, network, root, USB, controller, device-node, helper,
UI, write, reset, or configuration request. It did not modify the reviewed R
sources or frozen evidence.

Reviewed source pins:

```text
code-write-readiness.md
f00251e798d8016e46f29adcfac10c50d1c2b8c6c6088f3b556473edf0b17ce2

verify-code-write-readiness.py
79847d6b16e5283ee24deb3475c3695312e354ae9c64a5a345e1806983fd934a
```

## Verdict

**Bounded clear.** The conclusion that no selector-1 code checkpoint/write or
write probe is qualified follows from the retained evidence and is stated
with the required limits.

- **P1 findings:** none.
- **P2 findings:** none.

The first unresolved prerequisite is correctly identified as positive
mutable-backing classification or an explicit write-acceptance/permission
edge for the selector-1 mapped code view. Additional prerequisites remain
unproved even after that first gap: RAM execution permission, current core-PC
execution from the view, and a recoverable rollback path.

This is a finite positive-evidence assessment, not a global claim that no
mapping, copy, permission setup, or writer exists anywhere in the SoC or
firmware.

## Stored and mapped-view evidence

The selected and recovered-current files independently reproduce the pinned
5 MiB hashes:

```text
selected  bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
current   f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562
```

Their complete stored image-1 slots, FILE `0x40000..0x7ffff`, are
byte-identical and have SHA-256
`56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf`.
This is storage identity for that slot, not a live whole-image or execution
proof.

The verifier pins frozen N manifest
`a365b51fe014af70d50697bdeefd0b5eac2d6abb342fda1c6d21ab6ec2b145d7`
and result
`3119fb85c08b970794adcdf975313d825c80a301b995e293f2fc5cb458df57c1`.
All three retained selector-1 reads have exact length/hash and match the
corresponding selected-package slices:

```text
0x46001e60 / 512  8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49
0x460038c0 / 64    0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb
0x4601bb60 / 576   035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8
```

The retained result explicitly records sequential, non-atomic reads, no bus
alteration, and no proof of current execution or whole-image identity. The R
report correctly treats exact readable content as a mapped-view observation,
not as evidence of mutable backing, write acceptance, executable RAM, or a
current program counter.

## Reset path and raw system address

The image-1 vector is exactly initial SP `0x20020000` and Thumb reset word
`0x369`. The reset body at VA `0x368` has the reported bytes/hash. Its first
literal resolves to odd word `0xdc01`, called through `blx`; its second
resolves to odd word `0x141`, used to branch to the scatter dispatcher.

The complete first reset callee VA `0xdc00..0xdc13` matches SHA-256
`720dd0735e0becce7d432e13f0eeb3f5f0d5b9aba240d5b0eaddca5ef557ed89`.
It loads through raw literal `0xe000ed88`, changes the loaded word, writes it
back through the same raw address, and returns.

R correctly avoids naming either the routine or register. The bytes alone do
not qualify a symbol such as `SystemInit`, a register semantic, a memory
permission effect, or any relationship to selector-1 backing. Leaving
`0xe000ed88` unnamed is both accurate and sufficient for the readiness
decision.

## Exact nine scatter ranges

The dispatcher VA `0x140..0x1f3` matches SHA-256
`cf4020e3cdb1b314345608c30d00c1efa1e0ad4cf87bf8e54aa92f568fcb6330`.
Its relative table bounds at anchor `0x174` resolve to linked VAs
`0x1d6a4..0x1d733`, exactly nine 16-byte records. Stored FILE is therefore
`0x5d8a4..0x5d933`, matching the verifier's 144-byte table and SHA-256
`73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef`.

The nine decoded destination half-open ranges are:

```text
0x20000000..0x200004f8
0x20015000..0x20015b50
0x20015f10..0x20016a60
0x2020a000..0x2020cd30
0x20253000..0x2025523c
0x20209000..0x202096c0
0x20209800..0x20209ec0
0x20269000..0x2026d890
0x200004f8..0x2000e19c  (zero-fill handler)
```

None overlaps any of these bounded code domains:

```text
linked code VA                 0x00000000..0x0003ffff
selector-0 mapped code view    0x44000000..0x4403ffff
selector-1 mapped code view    0x46000000..0x4601ffff
```

This proves that the exact ordinary reset-scatter records do not themselves
copy or zero code into the selector-1 view. It does not exclude boot-ROM
mapping, computed/indirect setup, undocumented hardware behavior, or later
loaders.

## Ordinary launch and mapper boundary

The ordinary launch slice VA `0x2ac`, context slice VA `0x1ba0c`, and mapper
VA `0x1bb74` reproduce their pinned hashes. The mapper positively explains
how selector-nonzero linked addresses below `0x20000` become `0x4600....`
addresses. It contains no positive backing-type declaration, permission
configuration, write-acceptance contract, or core-PC observation.

The report therefore correctly distinguishes:

- address translation and successful reads, which are proved;
- mutable/RAM backing and writes, which are not proved;
- execution permission and actual current execution, which are not proved;
  and
- recovery/rollback behavior, which is neither proved nor investigated.

The known `0x4500....` and `0x4700....` data mappings cannot supply the
missing classification for a distinct `0x4600....` code view merely by
numeric analogy.

## Why stopping before a probe is correct

A write probe would assume the property it is intended to discover while
crossing a controller-state and recoverability boundary. The available
target-`0x101` reads establish no target-`0x102` write acceptance. Without
positive backing/write semantics, there is also no qualified address,
payload, visibility rule, execution-coherency rule, or restore path.

Accordingly R correctly proposes none of the following:

```text
write address or payload
target write helper
permission change
checkpoint patch
write-and-restore trial
live target probe
```

The conclusion does not depend on inspecting flash/storage banks,
bootloaders, persistence, POFLG, protection, return guards, or other excluded
branches.

## Verifier reproduction and limits

Normal and optimized verifier runs completed successfully and emitted
byte-identical JSON with SHA-256
`c1834f223bbe830fcab9c2de2ac3ed5817e10fb0e20e0ba3c42abe9c731b45b3`.
The output correctly records:

```text
status                                      qualification_gap
target_operations                           0
ordinary_reset_scatter_code_destination_count 0
mutable_backing_classification_proved       false
mapped_view_write_acceptance_proved         false
mapped_view_ram_execution_permission_proved false
current_core_pc_proved                      false
recovery_or_rollback_proved                 false
write_probe_qualified                       false
```

The verifier uses explicit exceptions and remains effective under `python
-O`. It meaningfully pins both whole retained files, complete stored-slot
equality, frozen N evidence and exact raw windows, vector/reset bytes, first
callee/raw address, dispatcher/table/rows, launch/context slices, mapper, and
the required negative readiness fields.

The bounded evidence does not prove a global absence of writable code
backing, write mechanisms, permission setup, or indirect/later initialization.
It proves only that the inspected positive paths do not supply the missing
qualification and that the retained reads themselves do not close it.
