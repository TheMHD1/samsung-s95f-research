# Content-dependent blackout investigation

## Scope and current restoration baseline

The native components are restored and are not a current experiment:

| Component | verified restored hash | treatment |
| --- | --- | --- |
| CompHome | `ec4541301a818efd308461c900efde0524f2243226c2db951b1f63674fcff35f` | unchanged |
| CompTerra | `b05655edcc7de8557e306cb980d4098ae2a1f79db69b0b215b2dfafc7b7fe9f1` | unchanged |
| native Apps content | `3775…` (coordinator-verified) | unchanged |

The prior apps-only/row-removal artifacts are not valid inputs for a new
experiment: they were made against a different CompTerra hash and depended on
custom helpers that have been removed.  No UI component is to be patched or
removed while diagnosing the current symptom.

## What is observed

1. The owner reports that a full native Apps screen stays physically visible,
   while sparse/empty For You or Live can black out quickly.  Fullscreen video
   is also reported stable.
2. This is a correlation across content states, not evidence that the UI has
   permission to shut down the panel.
3. Real display-path transitions have been captured: `deviced` can perform an
   off-sensing / DPMS sequence, mute the QD TCON, and resume it.  The kernel
   log around uptime 3863--3865 contains `AVEMonDIM` screen-saver brightness
   `0`, `deviced` off-sensing readiness, panel DPMS off, mute, resume, then
   AVEMonDIM brightness `7`.
4. The `QD_TCON_OFF=1` line is a monitor-history latch, not a live assertion
   that the TCON is currently off.  It has continued while a physically
   visible Apps screen and healthy power/PMIC status were observed.
5. The stable Apps capture still reports APL/Lamp zero.  Therefore **APL=0 is
   not sufficient to explain the symptom**.  Nor does a 1080-versus-480 log
   field alone prove a causal resolution/compositor path.

## Known native UI structure (not a proposed modification)

CompTerra owns `d/tabs`; it conditionally exposes the Home tab layer and uses
its `CompUGTabCache` to populate For You/Live content.  CompHome's
`CompTabLayerCache` independently builds its tab map and writes its cached
representation through `TabListInfo.SetTabList`.  The current normal key is:

```
db/home/tab/list = {
  "d/ug.tab@ForYou":"ForYou",
  "d/ug.tab@Live":"Live",
  "d/apps.tab":"Apps"
}
```

That key is output/cache state, not a reliable persistent preference; simply
overwriting it is not a root-cause test because a component can regenerate it.
`db/home/firstscreen_mode=1` has been observed but its semantic mapping to a
particular tab has not been established.  Do not change either key during the
diagnosis.

## Hypotheses, ranked by evidence

| Hypothesis | Evidence for | Missing proof / discriminating signal |
| --- | --- | --- |
| Off-sensing/DPMS transition is the immediate black-screen mechanism | The sequence exists and can mute/resume the output path. | It is **not yet causal**: captured DPMS offs at 6182/6193/6207 align with owner-style power cycles and later wakes; it was not shown to precede a spontaneous blackout. A blackout-time trace must show it beginning before the observed loss of picture. |
| Static/sparse UI allows screensaver/off-sensing eligibility | Sparse Home is correlated with failure; fullscreen video is stable. | Need screensaver activation/reset and foreground/window state at the same timestamp. Saver brightness 7 was physically visible at uptime 6244, and a later 0→7 transition (6335→6369) was also visible, so brightness 7 is **not sufficient** to explain the black panel. |
| Damaged panel/TCON link faults intermittently; UI state merely exposes it | Physical center-line damage; prior `ERR DET Status:0x10`; actual deviced recovery path. | Need a new blackout trace showing `ERR DET`/HSM/PMIC fault before DPMS, or a stable sparse state with no fault over a comparable interval. |
| Low APL / App rendering directly triggers a panel command | AVEMonDIM reports image metrics. | Disfavoured: full native Apps was physically visible with APL=0 and Lamp=0. No app-to-panel command has been observed. |
| `QD_TCON_OFF` repeats because the panel is being freshly powered off | Repeated monitor log is visually alarming. | Disproved for that field: binary analysis shows it is a latch set by earlier recovery counters. |

## Required read-only A/B capture

The parent collector should capture two labelled, time-synchronised windows
without altering settings:

* **A (control):** full native Apps, physically confirmed visible, 90 seconds.
* **B (event):** For You/Live or the sparse Home state, from navigation until
  30 seconds after the owner says picture is black (or 120 seconds if it does
  not black out).

For each window record the monotonic start/end time, user-visible state and
every line matching these events from `vlogutil -v kerneltime` and `dmesg`:

```
AVEMonDIM|QDDimming|SetQdSsBrightness|screen saver brightness
SCRSAVER|CAPI_SCREENSAVER|glscreensaver|screensaver
off sensing|off_sensing|panel dpms|TCON_MUTE|TCON.*(Resume|Power|ERR DET)
deviced|DISPLAY.*(state|off|on)|ELVDD|HSM Status|PMICINFO
CSFS|com.samsung.tv.csfs|welcome-mode|enlightenment
```

At the beginning and end only, obtain read-only snapshots of:

* deviced `GetScreenState` and `BurnInProtectionInProgress`;
* current foreground process/window list and CSFS/glscreensaver PIDs;
* `db/sysman/off_sensing_time`, `db/home/tab/list`, and
  `db/home/firstscreen_mode`;
* QDF TCON power/HSM/PMIC status already available through existing read-only
  helpers.

The critical ordering test is:

```
screensaver event? → off-sensing eligibility → DPMS off → TCON mute/resume
ERR_DET / HSM failure? → deviced recovery → policy restore
no policy/fault event → compositor/window or panel-output investigation
```

Do not infer an ordering from timestamps in separately collected commands;
one continuously timestamped ring-buffer stream is required.

## Explicit exclusions

No test should kill or patch `deviced`, `tcon-monitor`, AVEMonDIM, fault
handling, thermal monitoring, compensation, ELVDD/PMIC logic, or native image
caches.  No UI binary or database mutation is justified until the A/B trace
identifies a specific process event preceding the blackout.
