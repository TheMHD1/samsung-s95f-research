# QD monitor runtime-state map

This is an offline address derivation for a future **read-only** AVE memory
sample. It does not prove a physical blackout, live fault, panel emission,
TCON power state, or recovery. No monitor flag, counter, latch, ioctl, GPIO,
power setting or process was changed to produce it.

Input is `binaries/libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
The exact [reproducer](qd-monitor-runtime-map-reproduce.py) verifies the input
hash, symbols, relevant Thumb instructions and the PIC arithmetic below.

## Link-time state block and runtime formula

At Thumb `0x26963a`, the QD monitor loads literal `0x003565de` from
`0x269c48`; the `add r3,pc` at `0x26963e` gives
`0x269642 + 0x003565de = 0x005bfc20`. The immediately following
`ldr r2,[r3,#0x58]` at `0x269640` is therefore the named `qd_tcon_off`
field at link VMA `0x005bfc78`.

For a freshly identity-checked AVE mapping whose offset-zero `r-xp` mapping
starts at runtime load bias `L`, every table address below is `L + link VMA`.
For example, the previously observed AVE bias `0xf6b77000` would map the
block start to `0xf7136c20` and `qd_tcon_off` to `0xf7136c78`. This is an
address formula, not permission to reuse it after AVE or the TV boot changes.
A collector must first check boot ID, avocd PID/executable, matching library
hash, offset-zero map and readable range each time.

| Offset from `0x005bfc20` | Link VMA | Symbol / role |
| ---: | ---: | --- |
| `+0x3c` | `0x005bfc5c` | `err_det_cnt` |
| `+0x40` | `0x005bfc60` | `vdd_det_cnt` |
| `+0x44` | `0x005bfc64` | `elvdd_i2c_error_cnt` |
| `+0x48` | `0x005bfc68` | `err_det_reboot_try` |
| `+0x4c` | `0x005bfc6c` | `vdd_det_reboot_try` |
| `+0x50` | `0x005bfc70` | `elvdd_i2c_reboot_try` |
| `+0x54` | `0x005bfc74` | `si_ok_count` |
| `+0x58` | `0x005bfc78` | `qd_tcon_off` |
| `+0x5c` | `0x005bfc7c` | `onetime_execution` |
| `+0x60` | `0x005bfc80` | `ip_status_count` |
| `+0x68` | `0x005bfc88` | `fault_occurred` |

The named fields come from the full symbol table in the copied matching
library, and the block base is independently recovered from executed Thumb
PIC arithmetic rather than inferred from neighbouring names.

## What the monitor does with the latch and counters

`0x269640` tests `qd_tcon_off`; if it is1, the branch at `0x269644` enters
the log/return route at `0x269b98`. That route does not issue power control,
mute, DPMS or a TCON setter. The terminal branch stores1 at `0x269786`, after
the operation-0 power-control call at `0x26977a`. Thus a later sampled1 is a
monitor-history latch and cannot time or prove a new panel-off action.

The monitor increments `err_det_cnt` at `0x269688..0x26968e`. After its local
three-sample check it increments `err_det_reboot_try` at
`0x269812..0x269820`. The already documented VDD and ELVDD paths similarly
use their own `+0x40/+0x4c` and `+0x44/+0x50` pairs. The latch terminal test
is `err_det_reboot_try > 1`, `vdd_det_reboot_try > 3`, or
`elvdd_i2c_reboot_try > 3` (`0x269738..0x269746` and `0x269ae6..0x269aea`).
Those counters are monitor bookkeeping; a snapshot cannot identify an
electrical root cause or show when a counter changed.

There are clear paths, but none is a supported external rearm interface. The
guarded reset path at `0x269a54..0x269a88` is now resolved exactly: at
`0x269616..0x269636`, it constructs PIC base `0x005a4000`, indexes
`0x3370` to GOT entry `0x005a7370`, then dereferences that entry and compares
the `g_tcon_monitor_restart` global with1. The dynamic relocation at that GOT
entry is `R_ARM_GLOB_DAT g_tcon_monitor_restart`; the same condition is
rechecked at `0x269a48..0x269a50`. When the flag is1, the branch clears the
QD block through `+0x58`, including `qd_tcon_off`, and clears the restart flag
itself at `0x269a7a`. This establishes a monitor-state reset condition, not a
panel recovery result or a supported owner control.

A separate `ip_status_count > 9` path at `0x269994..0x2699a8` clears several
counters but **does not clear `qd_tcon_off`**. The monitor on/off helper can
set `g_tcon_monitor_restart` only when its requested monitor-on value differs
from the remembered previous value; that condition is necessary for this
clear path but does not prove when the QD monitor will run it, or that it will
restore physical output. Therefore ordinary standby/wake and monitor toggles
still cannot be claimed as reliable output rearm operations.

## Monitor enable/restart fields are separate

`ave_tcon_monitor_onoff(int)` at `0x26b17c` uses the GOT slot at link VMA
`0x005a6e18` (the `R_ARM_GLOB_DAT` slot for `g_tcon_monitor_on`) and stores
its argument to that global. It compares it with local static
`pre_monitor_on` at `0x005bfcd0`; only when they differ does it update that
static and write1 through GOT `0x005a7370` to `g_tcon_monitor_restart` at
`0x005bfce8`. The relevant stores are `0x26b190`, `0x26b19a`, and
`0x26b1a0` respectively.

`g_tcon_monitor_on` (`0x005bfcec`), `pre_monitor_on`
(`0x005bfcd0`), and `g_tcon_monitor_restart` (`0x005bfce8`) are useful
context fields for a passive sample. They are not the QD latch, and this
helper neither directly clears `qd_tcon_off` nor signals the monitor condition
variable. Their values cannot establish actual task scheduling or a physical
output state.

## Proposed read-only capture scope

Read a paired 48-byte range starting at `L+0x005bfc5c` and individual words
at `L+0x005bfcd0`, `L+0x005bfce8`, and `L+0x005bfcec`, with maps before and
after. Decode each word little-endian and preserve raw bytes, source hash and
the gap between paired reads. An unobserved baseline is useful for later
comparison when it is labeled as such. Incident inference requires the same
capture around an owner-confirmed physical visible or black state. It must not
write the latch, clear counters, invoke the operation-2 reset, or be used to
treat a logical field as panel-light confirmation.
