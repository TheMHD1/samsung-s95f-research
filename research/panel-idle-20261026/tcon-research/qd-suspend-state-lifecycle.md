# QD suspend and TCON-state gates

Offline static analysis of the copied `qdf_tcon.ko` only, SHA-256
`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`.
No TV command, power change, trace, or live-memory read was made. Addresses
are module `.text` offsets, not runtime kernel addresses.

## Result

Two cached words suppress normal QD transport before a panel transaction:

| Word | Active condition | Recovered behavior |
| --- | --- | --- |
| `m_suspend_status`, BSS+0 | equals1 | read/send helper returns zero without I2C |
| `m_tcon_state`, BSS+0x10 | not equal1 | send/no-lock-read suppress traffic and return0; locking read normally returns-1, with exact command0 exception described below |

So a public success result, mute cache, or host-side composition does not prove
that a requested command reached the TCON while either gate is active. This
does not show that either gate was active during an owner-observed blackout.

## Suspend state

`QDFTcon_SetSuspendFlag` (`.text+0x148`) is the named writer. It stores its
input at BSS+0 (`0x194`) and returns zero. Input1 clears `m_tcon_power_state`
at+4 (`0x1b4`). Any other input stores one to `m_tcon_power_state`+4 and to
the adjacent BSS+8 (`0x1a0`). It does not write `m_tcon_state`+0x10. The log
literal is `Set Suspend Flag [value:%d]`.

`m_read_cmd_no_lock` checks suspend at `0xb8b8..0xb8c4`; its `0xb98c` branch
returns zero without transport. `m_send_cmd_with_lock` checks it at
`0xbbb8..0xbbcc`; its `0xbf70` path likewise returns zero without I2C. These
are broader than the special PVCC mute-zero skip, so the suspend gate can
suppress other command families as well.

`QDFTcon_InitVariable` clears BSS+0 at `0x1074`. Module initialization exports
the named suspend setter in its operation table. No direct static call to that
setter was found in this module `.text`, so callers may be external table
users. This is a finite local result, not a complete caller inventory across
other modules, firmware, or runtime events. No public getter for the word was
identified here.

## TCON-state transitions

`QDFTcon_InitVariable` initializes BSS+0x10 to one with
`stp wzr,w2,[x19,#12]` at `0xfc0`. That is an initial cached value, not a
measurement of panel light or rail health.

| Direct local writer | Value / condition | Limit |
| --- | --- | --- |
| `m_check_tcon_status` (`0xb250`) | sets state1 at `0xb280`; sets state0 on its bounded bad/terminal route at `0xb40c`; writes state1 on its accepted route at `0xb4b4` | its vendor status word does not decode OLED emission |
| `m_send_cmd_with_lock` | after the specific repeated `-ETIMEDOUT`/`-EREMOTEIO` pre-read route, writes state0 at `0xbde0` and I2C-comm state+0x3c zero at `0xbde4` | proves cached error response, not which physical device failed |
| `m_set_power_control(0)` | clears state0 at `0x11a6c`, together with power/PVCC cache changes | real power lifecycle; never call as a diagnostic |

Local calls to `m_check_tcon_status` occur at `0xb814`, `0xfb24`, Resume's
recovery route `0x11038`, and power-control-on `0x1192c`. These are potential
refresh routes for cached state; they do not prove that they ran at a blackout
or that a state change repairs a fault.

`m_read_cmd_no_lock` tests the state at `0xb8d4..0xb8dc`; the send helper tests
it at `0xbc08..0xbc10`. Their mismatch routes log `tcon state[%d]` and return
zero. The **locking** `m_read_cmd` differs: at `0x9be8..0x9bf8` it permits
exact packed `0xf38000000000` despite bad state; other commands take
`0x9da8`, set return-1 at `0x9db4`, unlock and return. This exception does
not bypass suspend or command-skip. A state0 can make traffic quiet, but its
return must be interpreted using the exact helper.

All three suppressed no-lock read paths leave caller output untouched. So do
locking-read suspend and command-skip return0 paths and its state-failure
return-1 path. Normal output stores occur at `0xb974` (no-lock) or `0x9c90`
(locking). A caller-visible zero or nonzero can therefore come from its
initialization or stale storage, not a new controller reply.

The status checker first sets state1 optimistically at `0xb280` but initializes
its local reply to-1 at `0xb2ac`. Its exact0 read at `0xb318` is exempt only
from locking-read state gating. If suspend or command-skip suppresses that read,
the untouched local remains-1 rather than becoming a successful status word.
Its bounded retry path can end in state0/return-1. The accepted sentinel route
separately stores state1 at `0xb4b4`. The transient optimistic cache alone is
not proof of successful status checking.

`QDFTcon_GetTconStatus` exposes the cache boundary. Given caller storage, it
stores one when `m_tcon_power_state`+4 is zero without consulting state+0x10;
otherwise it copies state+0x10. Its zero return and copied value are not a
panel-health or visible-light measurement.

## Relevance and next evidence

PVCC can specially skip mute-zero; suspend/state gating can suppress broader
traffic. The retained short post-onset traces are not aligned to a visible
transition and do not establish whether these values changed.

For a future observed transition, preserve timestamps for `Set Suspend Flag`,
`SUSPEND`, `qd command skip`, `tcon state`, `i2c master busy is detected 2
times`, power-control messages, and actual I2C bytes. A skip message plus a
missing I2C write supports a software suppression path; a completed transfer
still does not prove MCU acceptance or panel emission. No flag forcing, power
control, protection bypass, firmware patch, or persistent workaround follows
from this static result.

## Reproduction

`python3 tcon-research/qd-suspend-state-reproduce.py` hash-checks the copied
module and prints only the supporting disassembly. It has no network or TV I/O.

## Independent review corrections

The first version overgeneralized the no-lock read's return0 to all readers.
The locking reader's state-failure return-1 and exact0 exception are now explicit.
Suppressed reads leave caller storage untouched, and the status checker uses
a-1 sentinel; no default-zero health success is inferred.
