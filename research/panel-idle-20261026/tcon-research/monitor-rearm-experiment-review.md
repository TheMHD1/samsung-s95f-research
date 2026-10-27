# QD monitor-latch rearm: offline safety and reachability review

This is an offline review only. It does not approve, implement, or perform a
process-memory write, monitor call, D-Bus call, power action, network action,
or TV experiment. The exact input is `binaries/libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.

## Current state is insufficient authorization

The latest passive monitor snapshot has the QD bookkeeping tuple
`err/vdd/elvdd retry = 2/0/0`, `qd_tcon_off = 1`, remembered monitor-on `1`,
restart `0`, and monitor-on `1`. This is enough to show a stale history latch
and an ERR retry counter at its terminal threshold; it does not show a current
GPIO assertion, fresh ERR-DET status word, TCON power state, output-gate state,
or physical cause. It is therefore not evidence that clearing any field would
restore the panel.

All fields below are separately aligned 32-bit AVE BSS words, addressed from
the exact library load bias only after a fresh process/hash/map validation:

| link VMA | monitor-state offset | field | observed role |
| ---: | ---: | --- | --- |
| `0x5bfc5c` | `+0x3c` | `err_det_cnt` | asserted-GPIO samples inside a monitor invocation |
| `0x5bfc60` / `64` | `+0x40` / `44` | VDD / ELVDD error count | separate monitor bookkeeping |
| `0x5bfc68` / `6c` / `70` | `+0x48` / `4c` / `50` | ERR / VDD / ELVDD retry count | terminal-recovery bookkeeping |
| `0x5bfc74` | `+0x54` | `si_ok_count` | monitor-local counter |
| `0x5bfc78` | `+0x58` | `qd_tcon_off` | history latch, not a power-state read |
| `0x5bfc7c` | `+0x5c` | `onetime_execution` | adjacent monitor-local word |
| `0x5bfcd0` / `e8` / `ec` | separate | pre-on / restart / monitor-on | lifecycle bookkeeping, not QD-state block |

The storage widths do **not** make the fields a safe API. A direct process
write would race the monitor thread, evade its invariant updates and logging,
and constitute a control modification. Native aligned word stores do not make
this a C/C++ synchronization protocol or prove that the monitor has not read
the old latch just before a write. This review rejects direct latch/counter or
restart writes.

## What a direct latch clear would actually risk

At QD-monitor entry `0x269640..0x269644`, only `qd_tcon_off == 1` takes the
report-and-return route. Clearing only `+0x58` therefore permits the routine to
continue into its ordinary checker; it does not request panel-on, unmute,
frame restore, or a recovery reset.

With the observed ERR retry count already two, if the separate ERR GPIO remains
asserted the next full three-sample confirmation increments `+0x48` again at
`0x269812..0x269820`, and the `>1` terminal test reaches operation zero and
sets `qd_tcon_off` again. Thus a hand-cleared latch could immediately relatch,
possibly after another stock protection/recovery decision. Conversely, if the
GPIO is no longer asserted, the result depends on unobserved normal monitor
branches and is still not a display restore. This is why the retry count is a
protective retry cap/history, not expendable clutter to clear alongside the
latch.

The real in-process reset block is coherent but still not an external control:
when `g_tcon_monitor_restart == 1`, it executes at `0x269a54..0x269a88` and
zeros the QD state words `+0x3c` through `+0x5c` inclusive:

```text
269a76  str     0, [state + 3c]
269a7c  strd    0, 0, [state + 40]  # +40,+44
269a80  strd    0, 0, [state + 48]  # +48,+4c
269a84  strd    0, 0, [state + 50]  # +50,+54
269a88  strd    0, 0, [state + 58]  # +58,+5c
269a7a  str     0, [g_tcon_monitor_restart]
```

It deliberately leaves other words such as `ip_status_count` outside that
range. The monitor then returns to its ordinary entry logic; the clear block
does not call QDF power control, mute, DPMS, FRC duty, or a display restore.
It is bookkeeping reinitialization, not a recovery transaction.

## Existing stock bookkeeping entry points

Two static AVE routes can request the monitor's own coherent clear later:

```text
ave_api_start_monitor
  -> ave_tcon_api_start_monitor
  -> ave_tcon_monitor_start
  -> g_tcon_monitor_on=1; g_tcon_monitor_restart=1

ave_api_set_instant_on(mode)
  -> ave_tcon_api_set_instant_on(mode)
  -> ave_tcon_monitor_onoff(mode ? 1 : 0)
  -> restart=1 only when requested state differs from pre_monitor_on
```

`ave_tcon_monitor_start` stores one directly to both globals; `onoff` changes
monitor-on first and only marks restart on a remembered-state transition. The
normal monitor task later consumes the restart request if it runs. Neither
function signals the condition variable, clears the QD block itself, or issues
any panel output command. The recovered AVE public exports are in-process API
symbols: no supported AVOC D-Bus method or owner-visible control binding has
been proven for either. Calling them by injection, guessed RPC, or process
memory is therefore out of scope and would add a race to a protection-related
state transition.

The named `ave_tcon_monitor_set_system_power` body has no direct call to the
on/off helper; its name must not be treated as a stock rearm route. Nor has a
normal standby/wake transition been proved to reach either monitor-start or
Instant On chain. A Linux/process restart incidentally reinitializes BSS but is
not a safe experiment or evidence of recovery.

## Shortest public output-gate candidate is separate

The shortest already-public, one-shot output-gate request is AVOC
`SetPanelMute(0)`. It is not a monitor-latch rearm: it does not write
`qd_tcon_off`, restart, or retry counters. On its lower QD route it can read
the live `F3:0x164` mute status and conditionally re-send zero, but PVCC/cache
guards can also return success without a wire transfer. A prior single public
zero request has already been retained; it cannot justify an automatic repeat.
Its only future diagnostic role would be one separately reviewed,
owner-observed, finite request while physically black, not a loop or a
substitute for ERR recovery.

## Required evidence before considering any owner action

No action is proposed from the current snapshot. At minimum, a meaningful
review would need fresh, passive evidence that preserves:

1. owner-timed physical black/audio state and explicit absence/unknown status
   of Screen Optimization/countdown;
2. fresh AVOC identity, exact AVE hash/load mapping, paired monitor state
   block and separate pre-on/restart/on words;
3. stock kernel/vlog markers distinguishing a fresh ERR GPIO/status sequence
   from stale `QD_TCON_OFF` reporting, and DPMS/mute/power markers from a
   normal lifecycle; and
4. if a public one-zero is ever reconsidered, exact pre/post public mute
   getters, one request only, finite trace provenance, and physical observation
   after its marker.

Even that evidence could choose between hypotheses; it would not make a direct
monitor-state write, private monitor-start invocation, operation-two reset, or
repeated unmute safe. The current rearm idea is therefore **too risky and not
yet meaningful as a recovery experiment**.
