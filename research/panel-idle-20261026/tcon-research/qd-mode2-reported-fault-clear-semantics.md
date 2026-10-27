# What the stock Mode-2 sequence can clear in reported QD state

## Scope

This report correlates the retained Mode-2 transport audit with exact copied
QD/AVE code.  It is analysis of saved bytes only; it performs no TV, root,
network, GPIO, ioctl, controller, or process-memory operation.

Primary retained inputs are:

| input | SHA-256 |
| --- | --- |
| `binaries/qdf_tcon.ko` | `97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63` |
| `binaries/libave.so.0.1` | `a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777` |
| `overnight/sleep-investigation-20261027a/stock-mode2-transport-audit.md` | `70b0d0f2f7a8301d2b598d45a3510a4304bd493c2e7507e0bb1c8f270baf8847` |
| `overnight/sleep-investigation-20261027a/stock-mode2-trial/post-status.json` | `e838bf5eeefbe58831a5577b57dee52288c7e45dc8bf0207acd1071b80f55500` |
| `overnight/sleep-investigation-20261027a/stock-mode2-trial/post-pin.json` | `8bea346b446cbeff5bb483e9301d595ef54ade8436b6455544e6e5b09fc5c20e` |

The rejected 60-second enclosing observer record is not rehabilitated here.
Its I2C/kernel portion can establish the bounded stock transport chronology;
it cannot establish a physical outcome or onset timing.

## Result

The retained Mode-2 sequence gives a coherent explanation for the **reported**
change from pre-action ERR GPIO high/status `0x10` to in-action/post-action
ERR GPIO low/status `0x00`:

1. the stock off/on sequence reached reset and ACDET callbacks;
2. its normal on branch sampled ERR_DET as raw zero, so it did not take QDF's
   early nonzero-ERR return;
3. it ran QDF status checking, frame-mode handling, and cached-setting replay;
4. a later stock status transaction returned raw zero and a separate line
   read returned zero.

That is enough to say the reset/re-enumeration cycle changed what the retained
host getters and controller status transaction reported.  It is **not** enough
to say an RT/controller latch was electrically erased, every controller state
was reset, a panel fault disappeared, or the picture recovered.  The action
was physically unobserved.

The retained AVE monitor log continued to report `QD_TCON_OFF=1` after the
cycle.  That is expected from the separate AVE history-latch design and is
important: Mode 2 did not statically or observationally clear that userspace
bookkeeping latch.  While it remains one, the ordinary monitor body skips new
ERR-GPIO/status/recovery processing on later ticks.  This inhibits **monitor
observation/recovery selection**, not the kernel QDF on-tail that Mode 2 had
already entered.

## The actual Mode-2 normal on path

The retained transport audit places the reset/on sequence at 94420–94422
uptime.  In the static QDF body, `m_set_power_control(1)` calls its normal tail
only when its local ERR_DET sample is zero (or no provider wrote a nonzero
sample):

```text
118e8  call registered ERR_DET reader(&local)
118f0  OR reader return into accumulator
...    nonzero local -> 11994 short cached-power/PVCC return
11900  cached PVCC = 1
1192c  m_check_tcon_status(2)
11930  m_tcon_recovery_frame_mode()
11934  m_register_recovery_noFramerate()
11938  cached m_tcon_power_state = 1
```

The trace has a direct in-action raw-zero GPIO125 sample at 94422.496790–.792,
then complete status/replay traffic.  This fits the normal tail rather than
the short nonzero-ERR branch.  It does not prove the GPIO’s electrical meaning
beyond that stock sample or turn the cached state at `m_tcon_power_state` BSS
`+0x4` into a rail/light measurement.

### The `ABAB` check is a QDF transport acceptance condition

`m_check_tcon_status` at `qdf_tcon .text+0xb250` first optimistically stores
one in QDF `m_tcon_state` at BSS `+0x10` (`0xb280`), then reads packed
`F3:0x0000` through `m_read_cmd` at `0xb310..0xb318`.  It compares the reply
with `0xabababab` at `0xb2e8..0xb2f4`; on the accepted route it again stores
state one at `0xb4b0..0xb4b4`.  The post-reset audit retained the matching
`f38000000000 -> abababab` exchange and `TCON Access Success` log.

This is positive evidence of a completed Linux transfer and QDF's accepted
comparison route.  It is not a general controller-health theorem: it neither
decodes all controller state nor measures OLED emission.  The later `F3:0x08`
reply `00000000` is a different status query; the status ABI still leaves
read-to-clear/controller-latch semantics unresolved.

### Cached replay can restore host-requested settings without proving apply

`m_register_recovery_noFramerate` (`0xf6d8`) follows the status/frame calls.
It performs named cached restores, then replays every generic command whose
valid word is one.  The retained cycle contains 113 complete setting writes,
including the cached `F3:0x128` value `207`, and all 226 generic entries were
considered (`226 reg -> 89 count` log).  The replay loop ignores individual
lower returns and returns zero itself.  It thus demonstrates re-issuance of
remembered host requests—not hardware application, fault clearing, or a
source of a visible picture.

## Why the ELVDD “tcon off” message is not the AVE latch

The retained kernel line `Stop checking due to tcon off` is emitted by QDF
`m_check_elvdd_check_error` at `0xb0f8`, not AVE’s `qd_tcon_off` variable.
At `0xb158..0xb160`, it loads **QDF** BSS `m_tcon_power_state` at `+0x4`:

```text
b158  ldr w1,[qdf_bss,#4]
b160  cbz w1,b210
b210  m_hsm_elvdd_state = 1; print "Stop checking due to tcon off"; return 0
```

If nonzero, the helper sleeps and eventually reads a separate command; if
zero, it stops immediately.  Therefore that line establishes only that this
function observed the QDF cached power word as zero at that load.  It does not
mean AVE ordered a TCON off, identify a rail, or show the panel went dark.

The Mode-2 on routine stores QDF power state one only after the
status/frame/replay tail at `0x11938`.  The retained asynchronous kernel logs
and I2C events do not provide an atomic cross-thread ordering between the
ELVDD helper's `b158` load and that final store.  The line is therefore
compatible with an in-progress lifecycle/cache race and must not be used to
negate the later successful QDF transport route.

## AVE’s historical latch remains a separate blocker

`ave_tcon_monitor_ddr_pmic_check_qd_oled` starts at Thumb VA `0x2695fc`.
Its state block holds `qd_tcon_off` at `0x5bfc78` (`+0x58`).  On entry:

```text
269640  ldr r2,[state,#0x58]
269644  cbnz r2, 269b98       ; log/return path
```

That path skips the monitor's fresh ERR getter, status decoder, operation-zero
terminal action, and both operation-two sites.  The retained Mode-2 audit
records continued `QD_TCON_OFF=1` logs after the QDF tail.  This is consistent
with static ownership: QDF power control does not write AVE process BSS, while
the monitor’s own restart-consume block (`0x269a54..0x269a88`) is the recovered
path that clears the latch and adjacent counters together.

Consequences that are actually supported:

* Mode 2 can run QDF's normal kernel on-tail despite a pre-existing AVE latch;
  the layers are separate.
* A later ordinary AVE monitor tick with that latch still set cannot perform a
  new stock ERR sample or choose recovery, so it cannot report a fresh monitor
  classification.

Unsupported conclusions include that the latch caused the original blackout,
that clearing it would restore monitoring safely, or that the post-Mode-2
zero readings make a future black state harmless.

## Exact fields and stock markers for a future safe logger

There is no validated function probe facility on this build.  A kernel patch,
module replacement, or AVE memory hook is not a safe logger.  The available
reversible diagnostic tier is a finite private static-event capture plus
non-clearing start/end kernel log snapshots, as bounded in
`qd-function-logging-plan-20261027.md`.

For a naturally occurring transition, the useful *observational* tuple is:

| layer | exact field / marker | discriminator |
| --- | --- | --- |
| AVE monitor | retry words `+0x48/+0x4c/+0x50`, `qd_tcon_off +0x58`, restart global | stale-history return versus an actual monitor-state change |
| QDF normal tail | `Tcon Power Off/On`, reset/ACDET logs; `m_check_tcon_status` (`0xb250`) result logs; `m_tcon_recovery_frame_mode` and replay markers | early ERR return versus normal check/replay path |
| QDF cache caveat | `m_tcon_power_state +0x4`, `m_tcon_state +0x10`, `m_pvcc_status +0x40` only if an already reviewed identity-guarded sampler exists | lifecycle-cache transitions; never panel-light truth |
| wire/kernel | complete adapter-5/address-`0x76` transfer bytes/results; GPIO/clock/regulator rows; `F3:0x00`, `F3:0x08`, `F3:0x160`, replay traffic | separates observed stock traffic families without injecting a query |
| physical state | owner-timed visible/black/audio/overlay annotation | the only evidence for emitted picture state |

The needed logger should preserve these stock rows; it must not poll status,
read the GPIO repeatedly, write monitor state, call operation two, or suppress
protection.  The current static event surfaces cannot directly expose an
in-process AVE branch argument or prove callback return/application.

## Boundary

The strongest grounded statement is limited to **reported state and stock
transport**: the one Mode-2 lifecycle reset/re-enumerated the controller-facing
path, saw ERR_DET low in its own on branch, accepted its QDF ABAB status route,
replayed cached settings, and was followed by raw status/pin zeros at retained
sample times.  It did not clear the separate AVE history latch.  None of that
establishes physical restoration, fault cause, or a reason to weaken any
protection or retry behavior.
