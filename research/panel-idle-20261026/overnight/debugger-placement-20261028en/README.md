# Custom debugger placement and observation boundaries

This checkpoint answers where custom instrumentation exists now and where an execution-time logger would add information. It is a navigation and engineering record, not another claim that the fault has been fixed. Inputs are bound in `input-pins.json`; no target operation is performed by this document.

## Instrumentation actually implemented and exercised

The EH native reader captures an ordered R/M/C/P/N/H/L/R cycle and packs 54 bytes per completed cycle. Its appended fields expose the trainer control, aggregate, reference-selector mirror, reference-refresh event counter, two writer controls and the saved A/B pointers. It reads existing SRAM and stores its own bounded records in the Linux userspace helper. It does not install executable code in the embedded controller.

The original 250 ms schedule captured 60 clean checkpoints in EL, with all sampled selector/counter/writer/score fields zero while the saved pointers rotated through three values. The original alternate limit stayed 40. That capture began before one Left down/up workflow, with Apps and screensaver windows present beforehand. Neither key consumption nor an Apps-to-Live exposure nor panel light was measured. A later cached Apps/screensaver snapshot cannot establish continuous saver residence or that the key failed to wake it.

The preceding EI attempt found an already-latched software fault before its planned key. It therefore sent no Left. The later EB fault capture and separately qualified recovery validation are recorded in EI/findings.md; they must not be merged into an invented onset bracket. The older actual onset records show sampled H reaching 42 with a 40 limit and fault state 0x1001. These data support the software fault path without identifying the final electrical blanking edge.

EM is being built separately to request 25 ms spacing for the same fixed read map and finite record count. A requested poll interval is not the achieved rate or a per-function trace. Its source, review, execution and actual timing must be recorded independently before it becomes evidence.

## Functions that explain each observation

| Firmware point (image1 linked VA) | Question | Existing observation and remaining gap |
| --- | --- | --- |
| 0x3952 selector store, wrapper 0x18c94 | Which upstream context selected this behavior? | EJ traces the AP_EXCO provider and finite timer callback. Current C7 and a later saved mirror do not establish the provider value at the earlier store. |
| 0xc250 and 0x1c12c | Was a reference refresh armed, and which boundary events populated it? | EG traces change detection and the counter seeded at 1. Two qualifying boundary events clear it, without a source guarantee of distinct top/bottom identity. EH samples the counter and mirror but can miss both events. |
| 0xbd58 unpacker entry | Which A/B pointers and selection branch actually reached unpacking? | Saved dispatcher pointers are only sequential samples. A proposed entry hook would record incoming r0/r1 and original LR, distinguishing the fixed-top, fixed-bottom and dynamic caller paths. |
| Per-lane gates before comparator | Did the sampled lane reach the comparison? | EB reads the two fixed eligibility tables. Zero table values describe those read times; they do not prove that the loop reached a lane or exclude an intervening publisher. |
| 0xc5d0 formatter entry | What actual A, B, lane and difference qualified? | Existing records retain B/difference with possible stale epochs and signed-selection ambiguity. A hook restricted to four caller returns would capture actual A in r8 plus original incoming arguments. |
| 0x2024 aggregate decision path | What score and threshold did the branch compare? | H and the publication-bound mirror are sampled separately. The proposed hook records actual r7 and fp/r11 before the original comparison; the mirror must not be promoted to an observed decision-time threshold. |
| 0xc1e0 fault setter entry | Which event and caller entered the common setter? | Current RT state confirms a latched software fault later. A proposed entry event logs r0 and original LR; entry itself would still not prove every subsequent store completed. |

## What remains necessary before an embedded detour

DS defines the exact sites, live registers, original instruction spans and a bounded event schema. DZ identifies stock owners of apparent spare SRAM and shows why a zero region or MODE2 re-enumeration does not establish logger storage or instruction restoration. The live read-only code fingerprint confirms selected bytes only, not writable instruction storage or atomic instruction replacement.

An embedded hook needs an owned storage/code lifetime, a proved install/remove mechanism, instruction visibility and an independent rollback route. These are concrete missing mechanisms, not missing user permission. Until they are established, the executed instrumentation is the bounded custom reader and existing private Linux trace instances. No breakpoint, firmware detour, debug-register write, kernel replacement or persistent logger is installed by this checkpoint.

Next useful evidence is a dense, time-qualified selector/counter transition under a verified normal page transition. If polling still misses the event, a Linux-side flight recorder or a controller hook should be judged by which missing event it can actually capture and by its recovery mechanism, rather than by the volume of addresses read.
