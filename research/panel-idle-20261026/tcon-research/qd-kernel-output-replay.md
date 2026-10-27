# QD kernel F3:0x128 request cache and recovery replay

## Scope and result

This is a bounded offline analysis of `binaries/qdf_tcon.ko`, SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
The module is an ELF64 little-endian AArch64 relocatable object. Addresses
below are section offsets, not live addresses. No TV, network, root,
process-memory, device, ioctl, getter, setter, power, or display action was
performed.

There is a positive kernel replay edge for the raw one-command request
`0x0000f30000000128`:

1. `QDFTcon_Tcon_InitDevice` builds a 226-entry command table. F3:0x128 is
   unique at index 218.
2. `QDFTcon_SendOneCommand` matches a request against that table and stores
   its first 32-bit payload word plus a valid flag **before** calling the
   lower sender.
3. `m_register_recovery_noFramerate` later scans the valid entries and sends
   the saved command/value pairs again. It ignores each lower return and
   returns zero.
4. `QDFTcon_Resume`, the QD power-on tail, and four monitor/sensing recovery
   sites call that replay routine immediately after the separate frame-mode
   recovery.

This establishes cached software **request replay**. It does not establish
that F3:0x128 is a calibrated duty, that the lower transfer succeeded, that a
controller accepted or applied it, or that a panel emitted light. The
`FinalDuty` label comes from the already recovered userspace producer; this
kernel table stores only a raw command and one raw word.

## Exact descriptor and table construction

The symbol table identifies two BSS objects:

| Symbol | BSS offset | Size | Fields used by this path |
|---|---:|---:|---|
| `m_npc_lut_register_data` | `+0x160` | 8 | pointer to one-word saved values |
| `m_npc_lut_register_info` | `+0x300` | 24 | count at `+0x300`, valid-word pointer at `+0x308`, command-u64 pointer at `+0x310` |

Those vendor symbol names do not limit the table to NPC commands. The exact
table contains 226 different 64-bit command keys.

`QDFTcon_InitVariable` clears the value pointer at `0x10b8` and zeroes the
24-byte info object through `ft_memset` at `0x1284..0x1290`.
`QDFTcon_Tcon_InitDevice` then:

- writes count 226 (`0xe2`) to BSS `+0x300` at `0xfb28..0xfb30`;
- allocates `count*8` bytes for command keys and stores the pointer at
  `+0x310` (`0x1026c..0x1027c`);
- allocates `count*4` bytes for valid words and stores the pointer at
  `+0x308` (`0x10280..0x10288`);
- takes the static command source from `.rodata+0x15f0`: the base used at
  `0x102c0` is the `.rodata+0x1228` relocation loaded earlier plus `0x3c8`;
- copies each 64-bit command and writes zero to the corresponding valid word
  at `0x102c8..0x102f4`; and
- separately allocates `count*4` bytes for saved values and stores the pointer
  at `+0x160` (`0x101e8..0x10228`).

The complete 1,808-byte static table has SHA-256
`1ca59d38d74dda0bbaf0d40453c57c6b53d0d3c692cee627d1856c9fd73bebb4`.
The relevant neighborhood is:

```text
index 217  0x0000f3000000012c
index 218  0x0000f30000000128
index 219  0x0000f30000000144
index 220  0x0000f30000000148
index 221  0x0000f30000000100
index 222  0x0000f30000000120
index 223  0x0000f30000000124
```

F3:0x128 occurs exactly once. The saved-value allocation is not itself
initialized in this body, but replay is gated by the separately zeroed valid
word. Therefore static construction does not invent a valid F3:0x128 value.

## Pre-send caching in `QDFTcon_SendOneCommand`

`QDFTcon_SendOneCommand` is `.text+0xd120`, size 304 bytes. The module init
ops table binds that exact function through relocations at `.init.text+0x2ac`
and `+0x2b4` before storing the pair containing it at `+0x2bc`.

The function receives the 64-bit command in `x0` and a payload pointer in
`x1`. If the value buffer, command table, and nonzero count exist, it scans
the table at `0xd198..0xd1b8`. On a match it performs, in this order:

```text
d1bc  ldr w0,[x21]                     first 32-bit payload word
d1c4  str w0,[values,index,lsl #2]     save value
d1d0  ldr x1,[bss+0x308]               valid-word array
d1d4  str w2,[x1,index,lsl #2]         save valid = 1
...
d1e4  mov x0,command
d1e8  ldr w1,[payload]
d1ec  mov w2,#1
d1f0  bl  m_send_cmd_with_lock
```

Thus an F3:0x128 request through this public operation saves exactly one
32-bit word at `values[218]` and sets `valid[218]=1` before the lower call.
There is no rollback on a nonzero lower return. If the descriptor is absent
or the command is not in the table, the caching loop is skipped but the lower
send at `0xd1e4..0xd1f0` still occurs.

The function returns the lower sender's result, but that result describes the
attempt, not controller acceptance or physical application. A later identical
generic request overwrites the saved word; this kernel cache is not an
equality-suppression cache.

An engineering-test function, `QDFTcon_EW_QdNpcTest`, also constructs and
sends F3:0x128 directly at `0x11694..0x116cc` and
`0x116f0..0x116f8`. Those calls go straight to
`m_send_cmd_with_lock`, not through `QDFTcon_SendOneCommand`; they therefore
do not populate this generic valid/value entry.

## Recovery order and F3:0x128 replay

`m_register_recovery_noFramerate` is `.text+0xf6d8`, size 568 bytes. It first
loads BSS policy words and calls 28 named helpers in a fixed sequence. Concrete
output-related examples include:

- `m_npc_lumi_global_gain` from BSS `+0xb4` at `0xf6f8..0xf708`;
- `m_set_ss_brightness` from BSS `+0xd0` at `0xf734..0xf738`;
- `m_set_lpm_level` from BSS `+0xf4` at `0xf76c..0xf770`; and
- `m_set_npc_dim_lvl2` from BSS `+0x124` at `0xf77c..0xf780`.

The screen-saver brightness helper is a separate, explicit cached-policy
restore: it accepts unsigned values 0..7 and sends `F3:0x00c4` with one word
at `0xeba8..0xebb8`. The NPC/global-gain and dim-level helpers use other
commands. These named paths must not be conflated with F3:0x128.

After all 28 named calls, the routine verifies the values, command, valid, and
count fields at `0xf808..0xf824`. Its generic loop:

```text
f85c  ldr w2,[valid,index,lsl #2]
f860  cmp w2,#1
f864  b.ne next
f878  ldr w1,[values,index,lsl #2]
f87c  ldr x0,[commands,index,lsl #3]
f880  bl  m_send_cmd_with_lock
```

The valid word remains in `w2`, so an eligible replay passes exact value 1 as
the lower helper's third argument. It is not a payload count. As established
separately in `qd-mute-concurrency.md`, that third argument is the helper's
per-call lock control. The saved scalar itself is in `w1`; for index 218, the
pair is F3:0x128 and its saved word. The lower helper therefore serializes this
individual replay, not the whole recovery sequence. Its return is immediately
overwritten by later loop/log work; it is neither aggregated nor used to clear
the valid flag. The routine returns zero unconditionally at
`0xf8f8..0xf90c`. The preceding 28 helper returns are likewise discarded.

This means recovery is an attempted restore of remembered requests, not a
verified transaction and not a retry-until-success mechanism.

## Direct callers and the separate frame-mode step

There are exactly six direct calls to `m_register_recovery_noFramerate` in
this module's `.text`. Every one is immediately preceded by a call to
`m_tcon_recovery_frame_mode`:

| Replay call | Direct caller | Preceding frame call |
|---:|---|---:|
| `0x10cd8` | `QDFTcon_MonitorTemperatureSensor` | `0x10cd4` |
| `0x10de0` | `QDFTcon_MonitorTemperatureSensor` | `0x10ddc` |
| `0x11040` | `QDFTcon_Resume` | `0x1103c` |
| `0x11934` | `m_set_power_control` | `0x11930` |
| `0x121d8` | `QDFTcon_SetElSensing` | `0x121d4` |
| `0x13bec` | `QDFTcon_SetOffSensing` | `0x13be8` |

`m_tcon_recovery_frame_mode` is a distinct path. It reads F3:0x160, compares
the returned word with BSS `m_tcon_frame_mode` at `+0x13c`, and can call
`m_tcon_set_frame_mode`. It does not consume the dynamic F3:0x128 entry.

In `QDFTcon_Resume`, replay is on the input-10 branch only when
`m_is_resume_recovery_needed` at BSS `+0x8` is nonzero
(`0x10fe0..0x11040`). The status-check, frame-recovery, and register-recovery
returns are not aggregated. The routine then clears the recovery flag and two
SRP fields and continues to an F3:0x164 zero request; its public return is
zero. This is not proof that every ordinary resume replays F3:0x128.

## QD power-control recovery and cache lifetime

`QDFTcon_SetQdTconPowerControl` maps input 0 to the off half of
`m_set_power_control`, input 1 to its on half, and input 2 to an off-then-on
sequence. In the on half, after the platform-specific supply/reset callbacks
and delay, an available ERR_DET callback can report a nonzero sampled word and
branch around recovery at `0x118d4..0x11994`. Otherwise the tail:

```text
11928  mov w0,#2
1192c  bl  m_check_tcon_status
11930  bl  m_tcon_recovery_frame_mode
11934  bl  m_register_recovery_noFramerate
11938  str w23,[bss+4]                  remembered power state = 1
```

The tail ignores all three recovery/status returns. `m_set_power_control`
returns the earlier accumulated supply/reset callback status in `w19`, not a
combined result for the frame or register replay.

The off half clears `m_tcon_power_state`, `m_tcon_state`, and `m_pvcc_status`
at `0x11a68..0x11a70`, then calls the platform-specific supply/reset path. It
does not clear the generic pointers, count, valid words, or saved values. The
on half's use of `m_register_recovery_noFramerate` is direct positive evidence
that this module intentionally carries those request records across this
power-control cycle.

The separate initialization path is the recovered invalidation boundary:
`QDFTcon_InitVariable` zeros the replay descriptor, and fresh table population
zeros every valid word. This analysis does not establish how often either
initialization function can be re-entered, and it does not claim that an
external controller reset preserves controller-internal state.

The userspace `DimmingBackendRoseMQD::t_Set2DFinalDuty::siDimLvl` cache is in
the `avocd` process, not this module's BSS. No direct userspace-cache write or
explicit invalidation event was recovered in these bounded bodies. External
callbacks and other-process reactions are not closed by this audit. The
positive result is that the recovered kernel path carries and replays its
own records across the examined power-control sequence; a separate
userspace-cache invalidation mechanism has not been established here.

## Boundary relative to the userspace final-duty path

The userspace base final-duty producer sends the same F3:0x128 request through
`ave_tcon_api_send_onecommand` and then makes a separate
`ave_frc_write_i2c(0x42b48, value)` call. The kernel mechanism recovered here
stores and replays only the F3:0x128 one-command leg. It does not establish a
replay of that separate FRC selector call or of the userspace arithmetic and
virtual mutation that produced the word.

No live kernel table, valid flag, saved payload, recovery invocation, lower
return, or incident-aligned transfer was sampled for this report. It therefore
does not show that index 218 was valid during the owner's blackout, that a
replay occurred, that a replay recovered or caused the picture, or that any
part of this path should be invoked or patched.

## Reproduction

The hash-gated offline checker verifies exact symbol spans, BSS layout,
initialization relocations and instructions, the full table hash and unique
index, pre-send cache ordering, all 28 named restore call pairs, generic replay
loop, six-call direct inventory, frame/Resume/power ordering, and the distinct
screen-saver and engineering-test paths. CFG descriptions above remain manual
interpretation of those pinned landmarks.

```sh
PYTHONPATH=/tmp/tcon-capstone \
  python3 tcon-research/qd-kernel-output-replay-reproduce.py
```

Companion artifacts:

- `qd-kernel-output-replay-reproduce.py`
- `qd-kernel-output-replay.disasm`

