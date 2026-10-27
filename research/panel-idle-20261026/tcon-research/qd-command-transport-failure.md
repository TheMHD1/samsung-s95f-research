# QD command transport: mute-zero observability limits

Offline reconstruction from the exact captured `binaries/qdf_tcon.ko` only:
SHA-256 `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
No TV command, device node, I2C request, process control, setting, or network
action was made. Addresses are `.text` offsets within the relocatable module,
not live kernel addresses. The bounded raw-disassembly reproducer is
`tcon-research/qd-command-transport-reproduce.py`; it hash-checks the module
before printing only the three ranges used below. Its current captured output
is `tcon-research/qd-command-transport.raw.disasm` (SHA-256
`f4ee158c1e2e410fb79520c282e8b04c16c672ec964d2738f6d28170e849f13b`).

## Result

`m_send_cmd_with_lock.constprop.0` at `.text+0xbba0` does **not** make return
zero equivalent to a bus write, command acknowledgement, requested mute state,
or OLED emission. A zero-payload `F3:...0164` has a dedicated no-emission
return-zero path. Separately, normal transport uses pre/post `F3:01` reads and
a one-byte local comparison; that does not decode panel state or emitted light.

| Caller-visible condition | Exact proof | Not proved |
| --- | --- | --- |
| zero from special `F3:...0164`, payload-zero path | helper returned directly before any I2C operation | command was emitted, accepted, unmuted the TCON, or produced light |
| zero after normal path | a selected local write/comparison control-flow exit reached zero | vendor-level semantic success or panel emission |
| `-1` | a bounded special pre-read failure path gave up | which physical component failed |
| mute cache equals zero | QDF wrote its cache | the preceding send succeeded |

## Exact zero-payload fast path

```asm
qdf_tcon.ko:.text+0xbbec  ldr  w19,[x25,#404]   ; BSS +0x194
                         orr  w19,w21,w19      ; payload | cached word
                         cbz  w19,0xbe80
...
                     0xbe80  mov  x0,#0x164
                             movk x0,#0xf300,lsl #32
                             cmp  x20,x0
                             b.ne 0xbbf8
                             ... printk ...
                             b    0xbe38        ; return w19 (zero)
```

The BSS symbol table calls `+0x194` `m_panel_dpms_pvcc_status`. This control
flow requires payload zero and a zero cached word, then confirms the command is
exactly `0xf30000000164`. It returns at `.text+0xbe38` without reaching either
raw/common write block (`.text+0xbd10` / `.text+0xbe50`) or either `F3:01`
read. The symbol name is evidence, but its vendor semantics and callers are
intentionally outside this transport report.

Payload one cannot take this branch. Therefore the transport observability of
mute-one and mute-zero is asymmetric. This identifies a false-success
possibility, not an occurrence in any recorded blackout.

## Other successful no-transport gates

The PVCC special case is not the only no-I2C success exit. The helper checks
`m_suspend_status` (BSS+0) for1 at `0xbbc8` and takes `0xbf70` to return0.
It checks `m_command_skip` (BSS+0x10c) for1 at `0xbbf8..0xbc00`, taking
`0xc140` to log/return0 before the mutex. It also requires `m_tcon_state`
(BSS+0x10)==1 at `0xbc08..0xbc10`; otherwise `0xc10c` logs/returns0,
unlocking the mutex if this call acquired it. These broader gates can suppress
payload1 as well as payload0. Payload1 cannot take the *specific PVCC-zero*
branch, but that does not guarantee it emits. Preserve suspend, command-skip,
and TCON-state logs alongside PVCC evidence in an observed test. No current
values or incident-aligned activation of these gates have been established.

Log literals useful for that distinction are `SUSPEND %s: Command =[0x%x]`
at `.rodata.str1.8+0x3390`, `tcon state[%d]` at `+0x3510`, and
`qd command skip[%d], cmd =[0x%llX]` at `+0x4540`. The PVCC-specific version
at `+0x53e0` includes `m_panel_dpms_pvcc_status:%d`; do not collapse the
general and specific skip messages into one inferred cause.

## Real transport and exact bounded waits

Outside that fast path, the helper optionally acquires `frc_tcon_lock`, checks
BSS `+0x10 == 1`, builds six command bytes plus four payload bytes, and uses
adapter/bus argument `5`, address argument `0x76`, and a ten-byte raw write at
`.text+0xbd10..0xbd2c` when that mode is selected. The alternate common write
is `.text+0xbe50..0xbe78`. Neither operation samples physical light.

Before a write it calls `m_read_cmd_no_lock` with packed `0xf30100000000` at
`.text+0xbca4`. On a zero return it repeats after a one-millisecond sleep only
when the selected reply byte is `1` or `2`. The counter increments before the
test and permits at most eleven pre-reads in that ordinary loop; it then exits
with a nonzero local count. The binary gives no recovered vendor meaning for
values `1` and `2`, so this is a control-flow classification, not a claim that
they mean ready, busy, or an MCU state.

At `.text+0xbcb8..0xbcc8`, only `-ETIMEDOUT` (`-110`) and `-EREMOTEIO`
(`-121`) increment a separate pre-read error count. On its second occurrence,
`.text+0xbde0` clears BSS `+0x10` and `+0x3c` then returns `-1`. Other nonzero
pre-read returns do not enter that special-error count, so they must not be
described as the same failure class.

After a zero write return, `.text+0xbd38..0xbd88` calculates an eight-bit sum
over locally built command/payload bytes. It issues another `F3:01` read at
`.text+0xbd8c` and compares the selected response byte at `.text+0xbda4`. A
mismatch receives one immediate 1-ms re-read (`.text+0xbdcc..0xbdd4`); later
mismatch branches can restart the outer sequence. The resulting branch graph
has zero-return exits after retry/logging paths, so return zero is not a full
acknowledgement witness.

`m_read_cmd_no_lock` at `.text+0xb8a0` only performs the vendor read and
byte-reverses four returned bytes into caller storage. It does not interpret
flags, mute state, faults, power health, or pixel output. Transport, local byte
comparison, state readback, and emission are distinct layers.

## Recorded `F3:01` replies

The prior passive black-state trace records:

```
F3 01 00 00 00 00 -> 00 00 81 04
F3 00 00 00 01 74 + 00 00 00 01
F3 01 00 00 00 00 -> 00 00 69 04
```

(`tcon-research/overnight-passive-black-i2c-decode.md`). After byte reversal, raw `00 00 69 04` becomes scalar `0x00006904`,
stored as little-endian bytes `04 69 00 00`. **The pre-read loop loads byte0
(raw final byte `0x04`), while the post-write comparison loads byte1 at
`0xbd98` (raw third byte `0x69` for the second sample).** The earlier version
of this report incorrectly assigned the final raw byte to both checks;
independent review caught and corrected it before any live control test.
The post-write selected byte is compared with the locally computed eight-bit
sum, not a named fixed panel-health constant. No complete vendor mapping of
either whole word to MCU mode, fault or emission has been recovered.

## Named mute setter versus raw mute-zero

`QDFTcon_t_Tcon_SetMute` is `.text+0xce00`. On a zero request with nonzero
cached mute it sends `F3:...0164=0` at `+0xcf7c..+0xcf8c`, then unconditionally
writes the mute cache (BSS `+0x140`) to zero at `+0xcf94`. It reads
`F3:...0164` at `+0xcf98..+0xcfac`, and if the returned word is nonzero issues
one further zero write at `+0xd008..+0xd018`.

That named setter is a stronger software-side observation point than a bare
helper invocation because it has a read/re-send attempt. It still is not a
physical-emission witness: the returned function value remains the first send
result in `w20`, while the second send result is not copied into `w20` before
return. The unconditional cache store also cannot validate hardware state.

## Scope

This establishes failure observability limits, especially for mute-zero. It
does not identify the cause of the physical blackouts, establish that a mute
command occurred during one, rule out panel damage, or justify a live/private
recovery command. A useful future discriminator is a time-aligned passive
trace recording whether a real `F3:...0164=0` write occurs, its raw return,
following `F3:01` bytes, and any named `F3:0164` readback.
