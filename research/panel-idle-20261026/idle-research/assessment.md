# Idle-path assessment — 2026-10-26

## Separate paths seen in the current boot

| Event | On-device evidence | Meaning |
| --- | --- | --- |
| Low-level TCON recovery | `deviced` began a TCON power reset at uptime 1826.639; display logged `turn off TCON` at 1827.780; `AVEMonDIM` reported `tcon state NG`; `deviced` powered it on at 1835.642, ran register/internal recovery, and display logged `turn on TCON` at 1836.728. | A display-driver/`deviced` recovery, not an ordinary remote timeout or Home tile redraw. |
| Native idle/screensaver state | After recovery, `AVEMonDIM` set screen-saver brightness from 0 to 7 at uptime 1869.133. Recovered settings include method 1, brightness 7, wait time 2, slope 2, sensitivity 17. | A static-image/idle protection transition. It can correlate with a sparse unmoving Home screen but does not prove the cause of the earlier reset. |

The post-recovery TCON read showed temperature 23/23 C, PMIC/LPDDR4/I2C health OK and power on. This proves recovery succeeded once; it does not identify the trigger or prove software can stabilize the damaged panel.

Video being stable while an arrow key does not reliably restore black Apps is not characteristic of a plain screen saver alone. The most supportable inference is that idle/screen-saver entry may expose the existing intermittent panel/TCON fault.

## Documented application control

Samsung documents `webapis.appcommon.setScreenSaver(SCREEN_SAVER_OFF)` for a foreground web application while it actively shows media or slides. It also requires the application to turn the screensaver back on when media stops. This is a per-running-app request; it is not a global replacement for `deviced`, TCON monitoring, thermal monitoring, OLED compensation, or Samsung Home.

Samsung's [Setting Screensaver guide](https://developer.samsung.com/smarttv/develop/guides/fundamentals/setting-screensaver.html) says this control has no effect when **Auto Protection Time** is off. The [AppCommon API](https://developer.samsung.com/smarttv/develop/api-references/samsung-product-api-references/appcommon-api.html) defines `SCREEN_SAVER_OFF = 0` and `SCREEN_SAVER_ON = 1`.

The exact-model e-manual evidence already captured in this project says the S8*F/S9*F normal UI does not offer global Screen Saver off and uses a two-minute still-image trigger. Native Home tiles alone therefore cannot establish a keep-panel-on policy.

## Reversible candidates

1. Restore a populated native Apps layout and test it across the same idle interval. This directly matches the owner's observed difference and can use the existing rollback.
2. After the Samsung signing certificate exists, build a small foreground idle-dashboard app. It can display subtle motion and call the documented foreground `SCREEN_SAVER_OFF`, then restore ON when exited. This is a test/launcher, not a repair and has not been deployed.
3. Inspect, then separately test, the Auto Protection Time state with a recorded original value and exact rollback. This has low firmware-brick risk but increases static-image exposure and cannot be expected to stop `deviced` TCON recovery.

## Do not suppress

Do not patch or kill `deviced`, `tcon-monitor`, `AVEMonDIM`, low-level TCON recovery, PMIC/ELVDD checks, thermal monitoring, or compensation counters. The captured recovery is what returned the TCON to `power(1)` and passing diagnosis; there is no evidence that disabling it would retain a usable image.

## Root read-only probe

```sh
vconftool get -r db/menu/system/auto_protection_time
vconftool get -r menu/system/screen_protection
vconftool get -r memory | grep -i saver
systemctl cat com.samsung.tv.glscreensaver-launcher.service
ps -ef | grep -E 'glscreensaver|AVEMonDIM'
strings /usr/bin/deviced | grep -i -E 'screen.?saver|tcon|off.sensing' | head -100
```

This distinguishes configurable idle policy from the separate hardware-recovery path before any reversible change.

## Exact native-library result

The current TV's `libcapi-screensaver.so` exports an application-facing
Wayland client. ARM disassembly establishes the following usable signatures:

```c
int screensaver_set_appid(const char *appid);
int screensaver_set_timeout(int seconds);
int screensaver_reset_timeout(void);
int screensaver_reset_timeout_with_resid(int resid);
int screensaver_override_reset(unsigned value);
int screensaver_fini(void);
```

`screensaver_always_on(x)` is only a wrapper around
`screensaver_grab_control(x, 1)`. Its first argument is an opaque server-side
control identifier, so it is deliberately excluded from a bounded trial.
`screensaver_set_timeout` accepts a nonnegative seconds value but changes
policy rather than simply resetting an existing countdown. `screensaver_init`
is a deprecated no-op in this build.

The library's messages explicitly distinguish timer resets from the same app
from ones “from other apps” that may be ignored. Therefore an external root
helper is the wrong first experiment. The bounded candidate is a call to
`screensaver_reset_timeout()` from the existing foreground CSFS process,
which owns the Home UI, first once and later only as a hard four-minute
in-memory loop if the single call is accepted and actually prevents the
brightness 0-to-7 transition. A CSFS restart and the existing exact-hash
rollback remove that experiment.

`helper/` contains a built but **not deployed** `S95fScreenSensorProbe.dll`.
It runs only as SDK UID 901 on the exact audited build, reports
`ScreenManagerIsInitialized` and the `ScreenManagerGetSuspendReason` result,
and can make one `ScreenManagerExtendSensorTimer()` call before exiting. It
does not call `ScreenManagerSetAutoPowerControl`, ambient-mode, or power-off
methods. The Screen API is an ambient/lifestyle API: its suspend-reason enum
has `Brightness`, `BLE`, `ProtectionTimer`, `Motion`, and `Tlog`. A successful
timer extension would be evidence about a sensor timer, not evidence that it
controls the ordinary Home screen saver or TCON recovery.

## CSFS managed-DLL trial result — inconclusive

Two bounded CSFS artifacts were briefly deployed by the coordinating agent:
the original one-shot patch (artifact hash prefix `b199`) and the diagnostic
patch (`cde3…`). Each was restored automatically after its short test window
produced no result. The original `csfs.dll`, hash
`a58a755d0761c2f6328ff8efdcd7e5af0a2a0c7a02b2fc3992374506e13ac4d0`, was
then verified restored. `out2/` and `out4/` were never deployed.

A process-map capture made **after** the original DLL had been restored showed
the running CSFS process mapping
`/opt/usr/apps/com.samsung.tv.csfs/bin/.native_image/csfs.ni.dll`, while its
ordinary `csfs.dll` was not mapped. This makes native-image selection a strong
likely explanation for the missing result, but it does not prove which binary
executed during the earlier short deployments. The absent log alone cannot
distinguish a constructor that was never reached, a logging constraint, a
different binary being selected, or a timer callback that never ran.

Accordingly, `out2/` and `out4/` are host-only research artifacts; the earlier
two reverted deployments must not be treated as a completed screensaver test.
No native-image cache change, service disable, monitor disable, or persistent
policy change was made. A separate proposal would need an exact stopped
service procedure, an atomic backup/restore of the native image, a
time-bounded foreground-only test, and an independent recovery path before a
native-image fallback could be considered.
