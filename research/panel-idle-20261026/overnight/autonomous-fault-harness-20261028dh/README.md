# DH autonomous menu-fault capture and stock recovery

The owner explicitly requested unattended operation without waiting for panel
verification. This phase acts under that authorization. Every new physical
state is `unobserved`; no screenshot, UI cache, ioctl return or controller
triplet is promoted to emitted light. Earlier owner-visible Apps/recovery
observations remain historical evidence only.

This phase implements automatic normal-key preparation, existing-log capture,
private kernel event tracing, a reviewed controller observer and a separately
bounded stock recovery request. It does not establish a prevention fix or
repair the reported physical panel damage.

## Completed evidence

1. Fresh passive AVE process-memory snapshot `dh-passive-baseline-20261028.json`
   accepted all identity/map/object/paired-field checks. Fault counters were0,
   previous ERR retry2, history latch1 and duty207. Those historical values did
   not independently determine physical light.
2. Existing `vlogutil -v kerneltime -t 2 '*:S' 'AVE:I'` returned a complete
   1,631-byte host capture, including two `QD_TCON_OFF=1` messages from
   AVOC706/thread1019. Its own `not_complete:4` diagnostic is retained: complete
   host transfer is not lossless driver-history proof. No producer flag changed.
3. `autonomous-baseline-01` selected Apps, passed public reject checks and issued
   one stock operation41/mode2. The new deadline/receipt helper exited0 and
   removed its private stage. Kernel evidence independently records USB55
   disconnect173926.154471..173926.165362, USB56 enumeration173927.694924 and
   configuration173927.843562. Kernel return0 alone was not used as an action
   acknowledgement. Linux boot remained unchanged.
4. `menu-onset-01/controller-capture` is an accepted DF eight-window observation:
   40 fixed read requests,80 complete bulks, four clean cycles, then a cycle5
   R-start fault. The software tuple changes0/0/1 to1/0x1001/0. The retained
   clean/fault bracket is174229.552106..174229.804026, **251.920ms**. One normal
   Left down/up was sent after the first full clean cycle. Cached UI afterwards
   was Live. New P16/N36 reply lengths/hashes/counts passed. Temporal ordering
   does not establish key consumption, exact MCU event time or physical light.
5. The paired private kernel trace retained16 events, all IRQ30 messagebox
   entry/exit. No selected GPIO, IRQ84 or suspend event was retained. All CPU
   overrun statistics and raw trace are saved. This observes stock kernel
   operations only; it neither requested pins nor forced a fresh GPIO read.
   No selected event is not proof that an electrical edge did not happen. The
   private instance was removed and global tracing remained off/nop.
6. The30-second AVE history around that observation retained10,728 bytes/61rows,
   including stale QD-off messages, no retained NPC/scene-change message, and
   separate sp-kpi activity after the first controller fault read. The reader
   reported zero overflow/not_complete in that particular dump; enabled producer
   coverage and physical light still are not inferred.
7. The enclosing `menu-onset-01/result.json` remains **rejected**. After the
   accepted observation and successful Right-to-Apps cached transition, the
   coordinator reused its existing `navigate-apps` output path. The ordinary
   navigator correctly refused the existing path; no recovery MODE2 was issued.
   The source was corrected to use a distinct recovery directory. No prior
   capture or rejected outcome was rewritten or relabelled.
8. `onset-01-recovery-continuation` separately passed Apps/public reject checks
   and completed exactly one stock MODE2/cleanup, with zero fault replay. Actual
   USB56 disconnect174287.588129..174287.605446 and USB57 enumeration174289.066923/
   configuration174289.215529 are retained. No physical recovery is inferred.
9. `apps-passive-control-01` then completed **80 clean cycles**,480 read requests/
   960 bulks, terminalTimeLimit, released/closed/ReadyForHeader and STAGE_ABSENT.
   It sent no key and observed no software onset during its bounded20s window.
   This supplies a real Apps control on the same post-recovery instance, not a
   claim that Apps can never fail or that the panel was physically observed.

10. `menu-onset-02` is a fully accepted second autonomous workflow on the same
    USB57 instance as that clean control, with no intervening reset. The fixed
    Left workflow again yielded four clean cycles then cycle5 fault,40reads/
    80bulks, bracket174596.221111..174596.471445 (**250.334ms**). Cached Live was
    followed by recorded Right-to-Apps/public checks and one separate accepted
    stock MODE2/cleanup. Final cached Apps is recorded. Physical light remains
    unobserved. This accepted run does not relabel the rejected first workflow.

There were three stock MODE2 requests in total: the initial baseline, the
separate first-trial recovery continuation, and the second-trial recovery.
There was no repeated fault/reset loop. No further identical baseline fault
trial is needed before a new discriminating observation or intervention.

## Instrumentation and source changes

`capture-passive.py` and `read-trace-formats.py` established that tracefs offers
only `nop`, no kprobe/uprobe controls, but GPIO, IRQ, raw-syscall and power trace
events. `kernel-trace.py` creates a fresh UUID private trace instance,128KiB per
CPU, monotonic clock, fixed GPIO filters125/121/126/127/425/429/431/148, IRQ30/84,
and suspend events. A90s watchdog disables this instance if the coordinator is
interrupted; the ring bounds memory. No global filter/enable/tracer is changed.
It traces existing gpiolib calls and does not export/request/change pin direction.
Raw GPIO ownership metadata is not a voltage measurement.

`deadline-mode2/Program.cs` preserves the frozen stock request exactly:
`/dev/tztv_tcon`, ioctl0xc010749f, fouru32 `[41,2,0,0]`, one open/ioctl/close.
An exclusive managed `receipt.txt` isolates structured output from native .NET
GC stdout. After ARM32/root/ABI guards it checks default SIGALRM disposition,
explicitly unblocks SIGALRM using the checked128-byte glibc sigset, and arms12s.
The outer root45s/host75s deadline remains. Uninterruptible kernel sleep can
defer termination; cancelling the alarm before receipt I/O means the outer
deadline owns the final file-write bound. No helper retry is permitted.

`run-deadline-mode2.py` pins the build, stock parser/ABI contract, target runtime
and stock modules, uses the qualified Tizen CLR path, and stages only fixed
managed payloads via Base64. It invokes the helper in the foreground, eliminating
the old success-path `/proc/PID/stat` disappearance race. Only zero exit, empty
stderr and the unchanged strict stock receipt permit exact stage cleanup.
Failure/ambiguity retains evidence and does not authorize another request.

Host checks passed the build with zero warnings/errors, x64 refusal before any
device open, exclusive existing-receipt refusal without overwrite, generated
stage shell syntax and malformed receipt rejection. Independent reviews are in
`firmware-evidence-graph-20261028dg/reviews/`. The first native deployment also
completed and cleaned normally. These checks do not prove physical recovery.

## Protocol and automation boundaries

`prepare-onset.py`/`prepare-control.py` read cached USB identity and a bounded
FD census. The phase-decision documents explicitly distinguish the conditional
configuration-callback first-header premise from queue liveness. Accepted
complete OUT/IN pairs supply subsequent modeled ReadyForHeader boundaries.
Agents do host-only analysis; the parent serializes all TV/root/USB/UI requests.

`run-menu-onset.py` and its recorded second-trial variant perform normal Apps/
Up/Up preparation, one reviewed DF observer, separate trace/log capture, cached
Right-to-Apps and one independent recovery if strict software onset completes.
They never infer a physical picture or request owner verification. A recovery
operation is recorded separately from the observation; a workaround is not
labelled a root-cause repair. Unknown USB phase does not authorize a follow-up
header or automatic compensating write.

No firmware flash, EEPROM edit, kernel/module patch, protection toggle, arbitrary
register write or threshold change occurred in this phase. The separately
designed DJ finite volatile comparison experiment is not part of DH's observed
results. Its publication/deployment must use its own final evidence.

## Remaining investigation

The accepted onset again reaches score44 under alternate limit40, with the
AP_EXCO-derived selector active. New P/N data constrain dynamic ring selection
and record publication; P does not identify the final A argument on fixed-A
branches. The positive source path from content-derived distribution/control
state to SLG/C+7 does not identify the physical packed-input producer or repair
the damaged panel. A complete explanation/fix must also account for failing
fullscreen PROGRAM_LABEL/PROGRAM_B, their working behind-Ugoos-Home state,
and working Cars3/PROGRAM_A/PROGRAM_09 controls. A cadence-only claim is weakened
by the known disabled branch and working23.976fps Cars3 case.

Controller-state prevention can be evaluated automatically. Any later claim of
visible picture stability needs a separately identified optical observation;
it does not block continued source work, log collection or bounded testing.
