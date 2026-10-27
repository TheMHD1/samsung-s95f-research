# FRC extension bridge to SDP register access

Offline follow-up to [the FRC duty write/save/replay audit](frc-duty-write-recovery.md).
The request under examination is operation 2 with a 16-byte envelope
`{0, value, 0x42b48, 1}`. No such request was issued for this analysis. No live
callback pointer, mapped register base, store, downstream acceptance or physical
picture was observed. A complete static route is conditional on initialized
stock tables and the gates below; it is not evidence of incident execution.

## Sources and reproducibility

Exact copied inputs:

| ELF | SHA-256 |
| --- | --- |
| tztv_frc_tcon.ko | aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd |
| sdp_frc.ko | 05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d |

The [bridge helper](frc-extension-bridge-reproduce.py) and
[SDP helper](sdp-frc-register-write-reproduce.py) hash-pin those source files
and their shared ELF reader, verify selected instructions/relocations/data,
and compare retained bounded listings. The bridge helper also checks manually
transcribed branch/return counterexamples; these are not ELF execution or full
control-flow verification. Manual source review remains necessary. Default
execution is offline and does not write the listings.

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/frc-extension-bridge-reproduce.py
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/sdp-frc-register-write-reproduce.py
```

All module code addresses below are offsets within the named ELF section, not
usable live kernel addresses. Unless specified, section is `.text`.

## Build-specific dynamic endpoint selection

`_tztv_frc_tcon_ext_cmd` (`tztv_frc_tcon`, `0x2d78`, 352 bytes) receives
`(operation, buffer, length)` and stores them in `w21/x22/w23`. The cold path
loads `g_chip_type` at BSS `+0x30` and chooses the symbol name:

| Chip code | Resolved name |
| --- | --- |
| 3, 8, 9, 11, 12 | NVT_TCON_ex_proc |
| 10 | MTK_ex_proc |
| Other u32 values, including 14 | sdp_display_ex_proc |

The unsigned CMP/CCMP chain is at `0x2e38..0x2e4c`; string bytes are
`.rodata+0x518`, `.rodata+0x530`, and `.rodata.str1.8+0x2438` respectively.
This copied build's `_tztv_get_chip_type` (`.text.unlikely+0x8c`, 52 bytes)
writes **14** through its nonnull output pointer. Probe passes BSS `+0x30`
to it at `.text.unlikely+0x2ec4..0x2ed4`. Thus the ordinary compiled probe
initialization selects the SDP name. This is positive build-specific evidence;
we have not captured that field or excluded every later writer at runtime.

`resolve_symbol` (`0x2a78`, 136 bytes) locks `module_mutex`, calls
`find_symbol`, unlocks, and converts the returned signed-relative symbol value
to an address. The bridge stores the result in BSS `+0x80` and sets its local
initialization flag BSS `+0x78` on success. Subsequent calls use that cached
pointer. The routine itself neither inspects the envelope nor validates length.

The zero-return caveat is state-dependent:

- Cold lookup failure returns `-1` and leaves initialization unset.
- Initialized flag with a null callback returns zero without forwarding.
- A successful first lookup with operation `-1` sets the flag and returns zero
  without forwarding. **Operation -1 on an already initialized callback does
  forward**; it is not a safe general-purpose passive lookup operation.
- Ordinary forwarding returns the downstream callback's status.

The copied SDP module exports `sdp_display_ex_proc`; this supplies a concrete
static candidate for the named resolution. No live symbol binding is asserted.

## The callback initialization chain is recoverable statically

The first indirect call is not a terminal unknown. The copied initializers
provide the following conditional pairing:

1. `sdp_display_ex_proc` (`0x1efc8`, 20 bytes) calls
   `dispay_coordinator_ex_proc` (`0x22060`, 32 bytes).
2. That coordinator loads pointer storage `inst_disp_output_coord`, BSS
   `+0x8cc10`, then directly invokes structure slot `+0x48`. There is no
   separate C++ vptr dereference in this body.
3. `display_coordinator_Init` (`.text.unlikely+0x1408`) calls
   `disp_coord_set(&inst_disp_output_coord, 4)` at `+0x1440`.
   `disp_coord_set` (`0x21fe0`) selects
   `get_instance_of_display_output_coordinator` (`0x22ea8`) for type 4 and
   stores its result through that pointer.
4. The singleton getter uses the object at BSS `+0x8cd08`; its uninitialized
   route calls `.text.unlikely+0x1564`, then
   `display_output_coordinator_Init` (`0x22818`). This initializer places
   `display_output_do_process` (`0x22d08`) in object slot `+0x48` via the
   relocated `x6` and `stp x7,x6` at `0x22878`.
5. For operation **2**, `display_output_do_process` takes its non-one-command
   branch, calls getter slot `+0x70`, then the returned device structure's
   slot `+0x30`, preserving operation/buffer/length. The getter is statically
   installed as `get_display_device_frc` (`0x22608`), which loads the pointer
   stored at coordinator object `+0xa0` (BSS address `+0x8cda8`). That storage
   address is not itself the returned device instance.
6. Initialization obtains that instance using
   `get_instance_of_abstract_display_device_frc` (`0x25c00`) and stores it
   at `0x22894`. `display_device_frc_Init` (`.text.unlikely+0x1c28`) uses
   instance BSS `+0x8cf88`, and installs `dd_frc_send_trig_bypass`
   (`0x25ac0`) in its slot `+0x30` at `.text.unlikely+0x1c78`.
7. Operation 2 differs from special operations `0x600/0x601`, so this device
   callback forwards it to `sdp_frc_ex_proc` (`0x2258`, 4656 bytes).

These are ordinary static initializer relationships, not captured current
tables. Early read-only agent conclusions that the first/second BSS indirect
was intrinsically unresolvable were superseded by tracing these same-file
initializers. No new kernel memory access was required.

## Operation 2 decodes a register access

`sdp_frc_ex_proc` has initialization, policy, completion, runtime-power,
mutex and operation-mask gates before dispatch. For example its initial
optional instance callback at `0x2288..0x2298` can return early with the
saved result zero. This audit does not establish those gates' incident values.
The relevant request must reach case 2 at `0x291c`.

The case copies all four envelope words into a local structure, requires
length 16 (`0x2920/0x2940`), and tests word 0. Nonzero word 0 takes a distinct
`tcon_mediation_proc` route; the examined envelope has word 0 zero. With
word 3 equal to one, the branch at `0x2954` checks the selector using
`sdp_frc_acl_IS_ACCESSIBLE` at `0x2ec0`. ACL failure returns `-EINVAL`.

The copied ACL permits selectors at most `0x5f000`, excluding five inclusive
ranges held at `.data+0x1a90` in 24-byte entries:

```text
18000..18f00  19000..19f00  20000..21000  21000..22000  34140..34ef8
```

Thus `0x42b48` passes this **static** ACL. This does not prove no runtime
modification or successful overall dispatch.

After ACL success, the case holds the instance's spinlock and calls
`sdp_frc_proc_reg_access` (`0x4de8`) at `0x2970`. Word 3 zero selects a
read; word 3 one selects `sdp_frc_proc_s_reg` (`0x49b8`); other values return
`-EINVAL`. On the examined write path, `s_reg` checks word 0 is zero, loads
word 1 as the value, and calls `wrap_write(instance, selector, value)` at
`0x4a20`.

## Allowed access is a barrier plus a register store; dummy access also exists

`wrap_write` (`0xcdb0`) loads the instance's mapped base pointer at `+0x138`,
adds the unsigned selector, and calls `ft_write(address,value)` (`0x1e780`).
`ft_write` loads `devio_access` from `.data+0x21650` and invokes its slot +8.
The on-disk relocation initializes that pointer to `allowed_access`
(`.data+0x21678`), whose +8 relocation names `__devio_write` (`0x1e680`).
That body is exactly:

```asm
dmb oshst
str w1, [x0]
ret
```

This identifies a memory-mapped register-access implementation, not a Linux
I2C adapter call, on the traced allowed path. The mapped base/physical address,
hardware interpretation and downstream propagation are not established here.
Function names containing `I2C` upstream do not prove that Linux I2C traffic
represents this leg. An I2C trace alone cannot cover these conditional stores.

`devio_access_disable` (`0x1e710`) switches the same pointer to the adjacent
dummy table (`.data+0x21658`); its write callback logs rather than issuing the
store. `devio_access_enable` (`0x1e728`) selects the allowed table again.
No incident value or complete writer/caller census is established. Absence
of direct calls to these symbols would not exclude inlined pointer updates.

After the `wrap_write` call, `s_reg` does not use its return as an acceptance
result and normally returns zero at `0x4a40`. There is no readback or physical
acknowledgment in that examined write path. Even an allowed register store is
not proof that the damaged panel emits light. Dummy access and higher bypass
paths reinforce why a successful ioctl result cannot establish application.

## Consequence for diagnosis

The proposed dimming leg can now be followed from userspace, through ioctl
dispatch, bridge resolution, coordinator/device initialization, request decode,
ACL and register-access indirection down to the conditional store instruction.
This closes several static unknowns. It does **not** show that this route
caused, recovered or prevented the owner's blackout.

Next measurements must distinguish request-cache suppression, upstream bypass,
SDP policy/power gating, dummy versus allowed access, and output failure after
an allowed store. Existing stock traces and source-backed read-only metadata
should be preferred; this report authorizes no raw MMIO access, direct register
write, disabling of protection or unobserved recovery attempt.
