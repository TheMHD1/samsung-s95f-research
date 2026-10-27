# Read-only runtime QD dimming baseline — 2026-10-26

This capture closes the previously unknown active-object identity and one raw
AutoDim field value for a single sample. **It is not an onset capture or a
confirmed physical-black sample.** No owner picture-state observation is
available for this interval. No process was stopped, attached with ptrace,
injected, patched, or asked to change the output.

## Exact copied-code derivation

The [upstream audit](../tcon-research/qd-autodim-upstream.md) and
[runtime observer map](../tcon-research/qd-runtime-observer-map.md) identify
`ave_dimming::SetAutoDim`'s route. Thumb `ADD r6,pc` at `0x150f8c`
plus literal `0x15108c` resolves to the ELF GOT base `0x5a4000`.
Literal `0x151090` is `0x29ec`, making the slot `0x5a69ec`.
Its `R_ARM_GLOB_DAT` symbol is `ave_dimming::m_pDimmingPanel`, ELF value
`0x5be2a4`; the GOT slot must still be read to account for actual relocation.

The zero-offset executable mapping and ELF PT_LOAD vaddr zero establish the
current AVE load bias `0xf6b77000`. The named file-backed mapping ends at
`0xf7125000`; its anonymous readable/writable BSS continuation extends to
`0xf7139000`. Thus the global address below is mapped even though it lies
past the named-library lines. The active-object pointer itself is in anonymous
mapping `0xf7200000..0xf7238000`. Its inner pointer lies in the shared AVE map
`0xf6380000..0xf6411000`, `/dev/shm/shm_ave`.

These are user-process mappings. They do not provide a kernel/QDF-module RAM
reader or direct access to the external controller firmware.
Offset interpretation relies on the previously fingerprinted matching binary;
these runtime JSONs record path/inode mappings, not a fresh on-device library
hash or a hash of live executable memory.

## Collection record and decoded values

[`runtime-dimming-state-20261026T112858Z.json`](runtime-dimming-state-20261026T112858Z.json)
preserves the exact remote command, raw base64, stderr, exit status, and
decoded words. Remote date is **11:28:59 UTC**, uptime
`35748.44..35748.46`. Eight small reads total **40 bytes**. Guards check the
expected boot ID, the single avocd PID, and its executable before reading.

| Meaning | Runtime address | Read value |
| --- | ---: | --- |
| AVE GOT slot | `0xf711d9ec` | `0xf71352a4`, the global's runtime address |
| Global active-object pointer | `0xf71352a4` | `0xf7203698` |
| Active object's vptr | `0xf7203698` | `0xf71162e8` |
| Active object's inner pointer | `0xf720369c` | `0xf63895d8` |
| Outer initialized field, object `+0x18` | `0xf72036b0` | `1` |
| Raw AutoDim request, inner `+0x2a8` | `0xf6389880` | `0` |

Subtracting AVE's bias from the vptr gives `0x59f2e8`, the address point of
`QDDimming`'s vtable (`0x59f2e0 + 8`). It is not the distinct
`QDDimmingMNT` vtable address point `0x5a094c`. This identifies the object
reached by this global at this sample; it is not a global inventory of all
dimming/backend objects in the process.

The map snapshot was taken at 11:26:49, approximately 130 seconds before
the state read. The state command verifies boot/PID/executable, but maps were
not captured atomically with it. This is an additional provenance limit.
The GOT word, global word and two-word object header were each read again
after the field read. All three matched. That guards against an observed
pointer change during this approximately 20 ms interval; it is **not an atomic
snapshot**, and cannot exclude a change away and back. AutoDim was read once.
The initialized field was also read once. This is narrower than the observer
map's proposed stronger repeated-field snapshot; no repeated-field stability
claim is made here.
All eight base64 values decode to their expected four/eight-byte lengths;
the command returned zero without a timeout. Stderr contains only `dd` copy
counts, accounting for all 40 bytes, and no memory-read error.

## Failed reader and successful access are both retained

The first attempt used `od -j address -N4 /proc/706/mem` and failed with
`cannot skip past end of combined input`. That attempt returned no word.
It is recorded in
[`runtime-dimming-first-word-20261026T112537Z.json`](runtime-dimming-first-word-20261026T112537Z.json).
Using `dd bs=4 skip=address/4 count=1` then succeeded; exact decoded byte
lengths are required because the `base64` pipeline's exit alone cannot prove
the preceding reader succeeded. No permission policy was changed.

Other acquisition files preserve the initial library map, successful GOT/global
word reads and initial object header. The complete mapping used to bound
addresses is
[`runtime-avocd-maps-20261026T112649Z.json`](runtime-avocd-maps-20261026T112649Z.json).
Hardcoded addresses are valid only for this guarded process/boot/mapping;
future sessions must derive addresses from fresh maps and pointer reads.

## What this changes in the diagnosis

* The active QD implementation is now directly sampled, rather than assumed
  from firmware support or static vtables.
* The raw AutoDim request field was zero at this interval, with the outer
  initialized low byte equal to one. This does not reveal what it was at a blackout,
  prove that duty/panel emission was normal, or exclude other dimming paths.
* Bounded process/shared-memory observation is available without a setter.
  It can be added to a future owner-confirmed visible-to-black transition.
  No matching before/after physical transition has yet been recorded.

The persistent output-loss cause and a reliable recovery/prevention method
remain unresolved. No factory/kernel/protection change or permanent repair
was deployed by this collection.
