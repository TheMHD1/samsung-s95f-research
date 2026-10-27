# AV: stock controller lifecycle followed by a clean RT sample

Recorded 2026-10-27 UTC. This is an executed technical experiment. Physical
panel light was not observed. No permanent repair or blackout prevention is
established.

## Result

After one positively observed stock operation-41/MODE2 off/on sequence, the
unchanged X reader returned a clean internal RT tuple and reported 80 clean
cycles during its approximately 20-second window. Before the lifecycle, the
same reader returned the latched fault tuple. Linux stayed on the same boot.

| Measurement | Before | After | Meaning and limit |
| --- | --- | --- | --- |
| Internal RT tuple: stop / fault / ordinary gate | `1 / 0x1001 / 0` | `0 / 0 / 1` | Fixed raw-window comparison under qualified mappings; delayed post-state, not an immediate transition capture. |
| F380 selector 8 wire reply | `00000010` | `00000000` | Exact complete I2C reads bound to the status helper PIDs. |
| Separate ERR_DET input | `1` | `0` | Input samples; no physical light measurement. |
| F3 selector 0x128 | `256` | `256` | Kernel output and complete traced I2C replies; not calibrated brightness. |
| Linux boot | `00000000-0000-4000-8000-000000000000` | same | No Linux reboot during the experiment. |

This gives a stock operation associated with delayed clearing of the sampled
RT tuple, to test as a physical-recovery candidate with the owner present.
It is not grounds to install an automatic reset loop or to claim that the
physical panel came back on.

## Actual sequence and timing

1. A public/sysfs/procfs preflight observed no reported upgrade or burn-in
   cycle, the expected USB identity/configuration, unbound interfaces and no
   matching userspace usbfs handles. These were bounded samples, not an
   atomic firmware-update lock.
2. The unchanged pre-X reader completed six exact reads/twelve bulks at
   uptime `136101.80`, terminal `ReadyForHeader`, release/close and stage
   removal. Both R samples were `1/0x1001/0`. All six raw windows matched the
   much older original X capture byte for byte.
3. The unchanged 60-second kernel collector was armed. The immediate public
   getters returned upgrade `0`, power `lcdon`, screen `1`, burn-in `0`.
   The stock status sentinel changed. Status, pin and selector samples were
   retained before the action.
4. One fixed MODE2 helper, PID `17157`, reached the actual lower sequence:
   GPIO425 low, `Reset(2)` at `136363.892943`, OCL reset value1, USB device45
   disappearance, normal on, OCL reset value0, same-identity USB device46
   enumeration, GPIO425 high and GPIO125 raw0. The normal on-tail contained
   346 complete I2C transfers, ending `136366.222190`.
5. Post-status, input and selector helpers completed and cleaned up. The
   collector terminated, its raw files were exported and its private
   trace/stage cleanup was verified. Independent offline audit accepted only
   the kernel/I2C lifecycle subchannel.
6. A later post-reset host snapshot confirmed USB device46, same identity,
   configuration1, all interfaces unbound and zero matching userspace
   handles. No intervening vendor OUT was sent in the recorded closed-world
   action lineage. The normal configuration
   callback's source-backed idle/header initialization supported one fixed
   post-X attempt; no retry or reset was available on a transfer ambiguity.
7. Public context at `136897.93..136897.96` reported `lcdon` and screen1.
   Post-X ran from `136902.237744` to `136922.242531`: 80 completed clean
   cycles, 480 reads and 960 exact bulk transfers, `TimeLimit`, terminal
   `ReadyForHeader`, release/close and stage removal. It began **536.016
   seconds after the I2C tail**. Only cycle80 raw bytes were retained;
   79 earlier clean cycles are represented by the validated native summary.

The final retained R windows independently decode to stop0, fault0, gate1.
There was no captured immediate fault-to-clean edge, no proof that MODE2 was
the exclusive cause, and no observation of the intermediate nine minutes.

## Capture integrity and exclusions

The frozen decoder reports 381 complete I2C transactions overall, zero
partial/orphan transfers, zero grammar errors and complete ring accounting.
The action's 346-transfer replay is complete, but is not byte-identical to
the older MODE2 trial: selector0x128 now requests256 instead of207, and its
two handshake replies differ. This experiment did not change those settings.

The enclosing AVOC observer remains **rejected** with
`orphan AVOC ioctl exit in physical window/drain`. No AVOC event-pair,
absence, consumption or recovery claim is made. The decoder's `markers=[]`
does not supply a fabricated custom action marker: raw capture start/end
events, the external dispatch record, exact helper PID and actual kernel
action logs bind the lifecycle. No parser was relaxed.

The updater and stock power operation use distinct locks. The public zeros
and changed sentinel justified a disclosed residual scheduling risk for one
stock action; they did not eliminate that race. No sampled public busy signal
was observed.

All helpers and the private collector have terminated and cleaned up. There
is no new background logger or automatic reset service from this experiment.
No firmware, kernel or protection patch was installed, and no flash was
performed. Root remains host-assisted; untethered persistence is unverified.

## UI and reset-domain qualifications

The ordinary UI read at `137040.96` reports cached `d/apps.tab`, mapped
screensaver windows and compositor `Display State: On`. This is context after
X, not a light measurement or proof of the displayed content during X.
For You/Live was not triggered during this experiment. Therefore this result
does not test prevention under the owner's known failing content.

The [reset-domain audit](reset-domain-provenance.md) finds no receiver edge
proving which core/RAM domain the OCL request resets. Image1's own scatter
does not clear the pointed-to RT object; image0's packaged scatter has a
separate possible clear route, whose execution was not observed. The
selected and recovered older packages have byte-identical 256KiB image1
slots, including the setter defining the three RT offsets. That supports
layout compatibility between those two sources, not proof of active whole
code identity or reset chronology.

## Next owner-observed test

First check whether a physical picture is visible **before** pressing Power
or navigating. An asynchronous question is pending; silence is not a result.
If visible, preserve that state for a clean Apps control, then capture one
known failing transition with the owner's physical onset annotation. If still
black, this clean RT record is a useful counterexample to treating the
recorded fault as equivalent to current darkness; establish the physical
state before any further recovery attempt. Do not automatically repeat MODE2.

## Evidence and independent checks

- [Baseline and lifecycle audit](baseline-and-lifecycle-audit.md): authenticated
  records, raw transaction/PID binding, integrity and narrow-channel verdict.
- [Post-X review](post-x-independent-review.md): exact native output, raw-byte
  checks, counters, timing and guarded cleanup.
- [Orchestration review](orchestration-review.md): one stock request, no action
  retries, fail-closed preflight/deadline gates.
- [Pre-X result](pre-x/result.json) and [post-X result](post-x/result.json).
- [Post-reset USB host snapshot](post-usb-host-preflight.json) and
  [later UI context](ui-after.json).
- [Original enclosing capture verdict](../stock-rt-av-20261027.onset/record.json),
  retained as rejected; original raw trace and sidecars remain alongside it.
