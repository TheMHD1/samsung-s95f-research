# QD monitor input provenance: sampled GPIO, return code, and cached health

This offline audit resolves the input side of the previously recovered QD
monitor. It adds interpretation rules for a future observed onset; it does not
establish that any of these branches caused the owner's blackout. No TV,
network, ioctl, GPIO, process-memory write, power, or factory action occurred.

The four exact copied ELFs are hash-gated by
[the reproducer](monitor-input-status-provenance.py). The source identities are:

| ELF | SHA-256 |
| --- | --- |
| libave.so.0.1 | a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777 |
| qdf_tcon.ko | 97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63 |
| tztv_frc_tcon.ko | aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd |
| tztv_frc_tcon_api.ko | 3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6 |

AVE addresses are ELF virtual addresses, not current process addresses. Module
addresses are offsets within the named ELF section, not live kernel addresses.
The retained [listing](monitor-input-status-provenance.disasm) excludes the
AVE routines' trailing literal pools from instruction decoding. This is a
bounded landmark check plus manual dataflow review, not an emulator or a
whole-firmware proof.

## Three monitor inputs have different semantics

The monitor at AVE `0x2695fc` calls these functions through resolved PLT slots:

| Monitor input | AVE routine / ordinary input source | Fault predicate |
| --- | --- | --- |
| ERR_DET | `ave_tcon_qd_err_detect_check`, `0x268ffc`; getter `ave_tcon_get_err_det_fault`, `0x25d01c` | Getter succeeds/nonnegative and returned output is nonzero |
| VDD_DET | `ave_tcon_qd_vdd_detect_check`, `0x268f70`; getter `ave_tcon_get_vdd_det_fault`, `0x25d0c0` | Getter succeeds/nonnegative and returned **fault output** is nonzero; QDF normally inverts a raw zero into this fault output |
| ELVDD/I2C aggregate | `ave_tcon_qd_tcon_hsm_status_check`, `0x269150`; getter `ave_tcon_qd_get_hsm_status`, `0x25d9fc` | Getter succeeds/nonnegative and `(HSM_output & 0x18) != 0` |

All three checking routines initialize their local output to zero. If the
getter returns a signed-negative result, they log and explicitly replace the
output with zero before applying the predicate. Their return is therefore
`0` for no counted fault or `-1` for a counted fault. A failed getter is not
propagated as a separate "unknown" state to this monitor.

Concrete ERR landmarks are the getter call at `0x269018`, negative-result
branch at `0x26901e`, output-zero store at `0x26905e`, and boolean negation
at `0x269030`. VDD has the corresponding call/branch/reset at
`0x268f8c/0x268f92/0x268fd2`. The HSM checker masks only `0x18` at
`0x26917c`, after its negative-result handling at `0x269172/0x2691ba`.

Consequently a line reporting no monitor fault does not distinguish a
successful healthy sample from an error that the checker converted to zero.
This is a static interpretation limitation, not an observed getter failure.

## Positive request and registration pairing

The matching AVE getters construct ioctl `0xc010749f` with operation and
initialized second word `{operation, 0, ...}`. ERR uses operation `0x1d`,
VDD uses `0x1e`, and HSM uses `0x23`. The getters copy their local second
word to the caller before returning the ioctl result. The higher checking
routine's signed-negative branch still clears that output on failure.

The API's `TCON_Request` jump table is `.rodata+0x6a0`, indexed by
`operation-1`; signed halfwords scaled by four are relative to `.text+0xe804`:

| Operation | API case | Registered table slot | QDF initializer pairing |
| --- | --- | --- | --- |
| `0x1d` | `.text+0xf198` | `+0x3d0` | ERR getter address materialized at `.init.text+0x2c8/0x2cc`, stored at `0x328` |
| `0x1e` | `.text+0xf1d8` | `+0x3e0` | VDD getter at `0x2d4/0x2d8`, stored at `0x2e8` through `x20=table+0x3e0` |
| `0x23` | `.text+0xeba0` | `+0x408` | HSM getter at `0x31c/0x320`, stored at `0x33c` |

Each case passes `request+4` as the output pointer. This is static pairing
with the copied QDF implementation. It is not a live callback-pointer read
or proof of module initialization, getter execution, or electrical state at an
incident. Missing table/callback handling is also relevant: ERR/VDD cases
return zero through `0xf364`, leaving the initialized result word; HSM's
missing callback returns `-1` through `0xf3b4`, which its AVE checker also
converts to no counted fault.

## QDF's ERR and VDD getters do not treat raw values alike

Both ordinary QDF getter routes first examine cached `m_tcon_power_state`
at BSS `+4`. If it is zero, they output zero and return zero without reading
the corresponding fault GPIO. Thus neither getter establishes the electrical
input state while the driver considers TCON power off.

With cached power nonzero and a registered provider returning zero:

| Raw value supplied by provider | ERR fault output | VDD fault output |
| --- | ---: | ---: |
| `0` | `0` | `1` |
| `1` | `1` | `0` |
| signed-negative value, if supplied | same nonzero raw word | `0` |

ERR's `QDFTcon_GetErrDetFault` (`.text+0x5608`, 284 bytes) preserves a
nonzero raw sample in the output and returns the provider's status. VDD's
`QDFTcon_GetVddDetFault` (`0x7b0`, 344 bytes) converts raw zero to fault 1
and any nonzero raw sample to fault 0. A nonzero provider return ordinarily
sets fault output zero while preserving that provider return; an absent
provider produces `-1`. At the AVE layer a negative return is converted
to no counted fault as described above.

There is a distinct engineering override: when `m_err_debug` (BSS `+0x28`)
equals exactly one, ERR uses `m_err_det_debug_status` (`+0x11c`) and VDD uses
`m_vdd_det_debug_status` (`+0x2c`) on their powered paths. This changes the
output word, not the provider return. It does not bypass the getters' early
cached-power-zero route, and a negative return is still cleared by AVE. No
override state was read or changed for this audit; its existence is not
evidence that it was enabled during an event.

## Provider status can differ from the raw-read result

The lower functions `_tztv_frc_tcon_read_err_det_status` (`0x1af0`, 316
bytes) and `_tztv_frc_tcon_read_vdd_det_status` (`0x1c30`, 316 bytes)
resolve/cache their GPIO, request it, set input direction, read the raw value,
store that raw value through the caller pointer, and free the GPIO. The
previous [DT audit](overnight-gpio-dt-driver-chain.md) identifies the properties
as `err_det` and `vdd_det`; these are not connector pin numbers.

After successful `gpio_request`, the saved return register is zero. The
direction-input return is not checked; the raw-read result is copied into the
output word, but it does not replace the saved status returned to QDF. ERR's
specific sites are request `0x1b90`, direction `0x1ba4`, raw read `0x1bb0`,
output store `0x1bbc`, and saved-status return `0x1bc4`. VDD's analogous
sites are `0x1cd0/0x1ce4/0x1cf0/0x1cfc/0x1d04`.

Therefore, **if** the raw-read call yields a signed-negative word after a
successful request, QDF can receive `(status=0, raw=negative)`. Under that
condition ERR counts a fault while VDD does not. This establishes what the
copied callers do with such a return; it does not establish that the deployed
GPIO implementation produced that return, that it happened on this TV, or that
this explains a blackout. Request/lookup failures instead return an error
without supplying a fresh raw value, and the higher AVE negative-result path
does not count that as a fault.

## HSM is a cached aggregate, not a fresh electrical read

`QDFTcon_GetHsmStatus` (`.text+0x978`, 284 bytes) builds its output from
cached BSS words:

| Output bit | Predicate |
| --- | --- |
| 0 | cached power is nonzero and cached TCON state `+0x10` differs from 1 |
| 1 | `m_hsm_pmic_state` `+0x30` equals zero |
| 2 | `m_hsm_lpddr4_state` `+0x34` equals zero |
| 3 | `m_hsm_elvdd_state` `+0x38` equals zero |
| 4 | `m_i2c_comm_state` `+0x3c` equals zero |

It makes no GPIO/controller read in its reviewed body; it logs and returns
zero for its nonnull output. The AVE ELVDD/I2C checker only considers bits
3 and 4. A bit-0/1/2-only HSM fault therefore does not increment that
particular aggregate counter. Other software may consume the full HSM result;
this audit does not claim those bits are globally ignored.

The writers and freshness of these cached words are outside this bounded
audit. `HSM=0` cannot establish current emission, rail state, absence of a
short pulse, or successful physical recovery.

## Consequence for the next observed blackout

Keep the monitor counters/latch and the stock getter errors as separate
evidence. A counter transition could reflect a sampled GPIO fault, a
negative word treated as a sample, or a cached health predicate; an unchanged
counter can coexist with a suppressed/failed getter. The existing
`qd_tcon_off=1` history latch still does not time a fresh shutdown.

No new getter should be invoked merely to inspect these inputs: the normal
provider changes GPIO direction and requests ownership. Use the reviewed
passive trace, existing stock logs and process-state sampler around a
physically observed onset. If those cannot expose the return/sample
distinction, retain it as an unresolved limitation rather than treating a
zero status as a hardware health verdict.

Reproduce locally:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/monitor-input-status-provenance.py
```

The helper checks exact ELF identities, selected instruction/relocation and
jump-table landmarks, and counterexamples in explicitly manual semantic
models. Those model checks do not execute or automatically prove the complete
binary dataflow. It compares the generated bounded listing with the retained
file; `--write-disassembly` is a one-time exclusive-create option.
