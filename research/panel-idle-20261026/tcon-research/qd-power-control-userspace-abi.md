# QD panel power-control ABI and recovery limits

Recorded 2026-10-27 UTC. This is offline inspection of the copied exact-build
ELF files. No power command, reset, rail write, helper deployment or TV control
was performed for this report. Addresses are ELF VAs for AVE and section
offsets for relocatable kernel modules, never live addresses.

## Result

The stock userspace-to-kernel route to the already reconstructed panel power
lifecycle is now positively bound. AVE uses ioctl `0xc010749f`, a 16-byte
envelope, operation **decimal41 / hexadecimal0x29**, and mode in word1.
The dispatcher loads callback offset `0x458`; QDF installs
`QDFTcon_SetQdTconPowerControl` into that exact slot. Mode2 calls the normal
off sequence and then normal on sequence. This is a candidate mechanism for a
future controlled recovery experiment, not evidence of recovery or prevention.

A zero result is particularly weak here: a missing interface or missing power
callback returns zero **without performing a power operation**. Other lower
paths also discard errors or publish caches before successful hardware work.
No automatic recovery loop or protection bypass follows from this finding.

## Exact sources

| file under `binaries/` | SHA-256 |
| --- | --- |
| `libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `tztv_frc_tcon_api.ko` | `3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6` |
| `qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| `tztv_frc_tcon.ko` | `aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd` |

The character-device open/compat dispatch is shared with the independently
reviewed [status ABI](qd-error-status-read-abi.md). This report does not repeat
that proof or claim a service-level IPC binding.

## ARM32 wrappers

`ave_api_set_qd_tcon_power_control` is exported at Thumb symbol `0x291e19`,
size1024. Its main path preserves input in r6, restores r0 at `0x291e78`,
then calls PLT `0x8c5f4` at `0x291e7c`. The actual `.rel.plt` entry resolves
to `_Z29ave_tcon_qd_set_power_controli`, not an inferred name match.

That lower wrapper has Thumb symbol `0x25c2e1`, size156. At `0x25c2ec` it
passes envelope base r7+4; `0x25c2f6` stores the input mode at r7+8;
`0x25c304..306` stores operation0x29 at r7+4. It builds request0xc010749f
at `0x25c2ee..2f2` and calls PLT `0x8df5c`, positively resolved to
`tcon_ioctl(unsigned long, void*)`, at `0x25c308`.

| envelope byte offset | role |
| --- | --- |
| 0 | operation41 |
| 4 | integer mode |
| 8, 12 | unused by the recovered operation41 case; stock wrapper does not initialize them in this slice |

A future restricted helper would initialize unused words, reject every mode
except its one deliberately chosen operation, retain the return/errno, and
never interpret an unchanged envelope as hardware acknowledgement. No such
power helper is supplied or deployed here.

## API dispatch and return propagation

Both `TCON_Request` dispatch tables select `.text+0xed80` for operation41:

| table offset in `.rodata` | signed halfword index40 | branch origin | computed target |
| --- | ---: | --- | --- |
| 0x6a0 | 351 | 0xe804 | 0xed80 |
| 0x768, debug-log branch | -445 | 0xf474 | 0xed80 |

The debug branch at `0xf3bc` logs before selecting the second table; it does
not change this operation's target. At `0xed80..84` relocations identify
the interface pointer as API BSS+0x620. The code tests it, loads its slot
0x458, tests the slot, loads word1, and calls the slot at `0xed98`.
Either absent-pointer branch reaches `0xf35c`, which returns0. A present
callback's return is preserved through `0xe7e0`.

The ioctl export copies16 bytes in at `0x3bec`, calls `TCON_Request` at
`0x3bfc`, preserves its signed result in x20 at `0x3c08`, copies16 bytes
back at `0x67ac`, and returns x20 through `0x67c0 -> 0x3160` if copying
succeeds. Copy errors have their own failure path. This is integer result
propagation, not a separate confirmation that the panel emitted light.

## Intended QDF binding

QDF `.init.text+0x454/458` has relocations to
`QDFTcon_SetQdTconPowerControl`; `+0x484` stores that pointer in table
base x19+0x458. The base is put in x0 at `+0x528` and passed to
`map_tcon_functions` by the call at **+0x5c0**. The API implementation at
`0x7c58..60` stores that base at BSS+0x620. The call address is0x5c0;
0x528 is argument setup, not the call. Static intended binding does not
measure the live pointer or exclude later module lifetime changes.

`QDFTcon_SetQdTconPowerControl` is `.text+0x11c48`, size304:

| mode | recovered behavior |
| --- | --- |
| 0 | `m_set_power_control(0)` |
| 1 | `m_set_power_control(1)` |
| 2 | off at0x11ce0, then on at0x11cec; return bitwise OR of the two integer results |
| other | log and return0 without an action |

Mode2 inserts no extra wrapper-level delay or compensating rollback. The
actual lower waits and rail/reset operations are documented in
[power hardware sequence](qd-power-control-hardware-sequence.md).

## What must be measured before drawing a recovery conclusion

The immediate useful checkpoints are entry mode, lower returned errors,
ERR_DET before/after, controller status before/after, transport suspension,
and whether the intended HDMI/picture state was restored. The owner must
eventually observe actual panel light; audio, screenshots, caches and return0
cannot replace that observation. While the owner sleeps, a power action
cannot establish physical recovery and could erase the preserved fault state.

The on path can see ERR_DET nonzero, publish power/PVCC caches1, and skip
normal controller-status/recovery setup. Conversely some GPIO errors leave
the sample zero and permit that setup. Thus a blind loop issuing mode2 would
neither diagnose the cause nor reliably restore the image. This report keeps
the candidate available for a future single controlled test with logging;
it does not propose suppressing the controller fault.

## Reproduce offline

`PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-power-control-userspace-abi-reproduce.py`

The script hash-checks the copied inputs, verifies wrapper instructions and
PLT bindings, both signed dispatch-table entries, callback slot registration,
return landmarks, missing-pointer zero and off/on call order. It reads local
files only; it is not emulation, a complete CFG proof or a runtime test.
