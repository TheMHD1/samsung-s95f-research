# `mixer_sys_disable_vblank`: controller boundary

## Result

The retained `mixer_sys_disable_vblank` log is a source-backed **host graphics
vblank interrupt-mask transition**, not evidence that the OLED panel stopped
refreshing, that QD/TCON power changed, or that the physical panel became
black.

The exact copied `binaries/sdp_drm.ko` is an AArch64 relocatable ELF,
1,808,606 bytes, SHA-256
`d1016cf5b72f86a1623b231d96dc944082263a70d3602d859f993d751bfdf881`.
All offsets below are ELF `.text` link offsets in that file.  The running
module-to-file binding for this particular log callsite is not established by
this static audit.

## What the retained log does and does not establish

The bounded raw kernel window
`overnight/paired-restart-20261027a/foryou-kernel-window-b.txt` (SHA-256
`21048d338b089df2a860e59e5bf09872dcda32d49f292e06dc93a7454bf67a2b`)
contains:

* `[84442.370919] [S_GFX] ### JJOO ### mixer_sys_disable_vblank`.
* Earlier `GFX V sync is working fine(...)` messages through `84441.707648`.

It therefore identifies a stock host-graphics event in this retained time
window.  It does **not** locate a physical blackout edge: the later owner
black annotation is outside the capture window, and neither printk nor DRM
vblank is a light-emission sensor.

## Static callback chain

The DRM driver registers its CRTC callbacks in `.data`: relocation at
`.data+0x50` binds `sdp_drm_crtc_disable_vblank` (`.text+0x1430`).  The
function maps CRTC argument `w1 == 1` to plane selector `w0 = 5`, otherwise
selector zero, and directly calls `hw_plane_disable_vblank` at `0x1444`.

`hw_plane_disable_vblank` (`0xe238`, 208 bytes) looks up the selected plane
and calls an installed plane callback at either a per-plane function pointer
or the selected operation-table slot (`0xe268..0xe2fc`).  This is an actual
indirect boundary: this audit does not claim that every CRTC disable reaches
the mixer implementation.

The observed log string names the separate mixer implementation:

```
mixer_sys_disable_vblank  .text+0x512f0, 144 bytes
  0x512fc  sdp_gfx_get_comm()
  0x51308  sdp_drm_rpm_dev_tryuse(1)
  0x51310  if comm[+0x0c] == 0: release only
  0x51318  if .bss+0x101f0 != 0: release only
  0x51338  sdp_gfx_set_vblank_interruptmask()
  0x51340  sdp_gfx_update_vblank_status(0)
  0x51344  comm[+0x14] = 0
  0x5135c  printk("...mixer_sys_disable_vblank")
  0x51328  sdp_drm_rpm_dev_disuse(1)
```

The printable string is tied by relocation to `.rodata.str1.8+0x1a0c8` and
the function name is present in the copied module.  This supports a bounded
interpretation of the matching log text, but not live callback-object binding
or a full causal path from Apps/For You content.

## Exact immediate hardware action

`sdp_gfx_set_vblank_interruptmask` (`0x59e08`, 84 bytes) receives zero on the
disable path.  At `0x59e38..0x59e50` it reads register address `0x5d08408`,
clears bit `0x400`, and writes that register back.  The symmetric enable path
sets that bit (`0x59e14..0x59e2c`).  The companion
`sdp_gfx_update_vblank_status(0)` (`0x4f938..0x4f980`) only spinlock-protects
and stores zero to `comm[+0x0c]`.

The direct mixer body contains no I2C/SPI/SSB/TCON/QDF call, no panel power or
backlight callback, no DRM connector disable, no clock/regulator API, and no
self-refresh helper call.  Its only additional external edge is the generic
runtime-PM pair:

* `sdp_drm_rpm_dev_tryuse(1)` at `0xd480` loads a configured RPM node and
  calls `sdp_runtime_pm_tryuse` only if non-null.
* `sdp_drm_rpm_dev_disuse(1)` at `0xd4b0` similarly calls
  `sdp_runtime_pm_disuse` only if non-null.

The retained binary does not resolve the later lower-driver RPM callback, so
this is not a proof that no runtime-PM consequence ever exists.  It is also
not a basis to call the vblank mask itself a panel-power operation.

For comparison, the DP plane callback `dp_plane_disable_vblank` (`0x32c60`)
only calls `sdp_dp_irq_set_vblank_en(0)`; the latter stores a byte-sized
logical enable value into its DP object at `0x1d388..0x1d39c`.  That reinforces
the narrow naming: these paths control vblank/IRQ bookkeeping, not a proven
scanout or OLED rail shutdown.

## Idle and configuration boundaries

No retained copied source or metadata identified a `vblankoffdelay` setting,
an idle/self-refresh policy writer, or a source-backed relationship between
the sparse Home page and this callback.  This is a bounded corpus result, not
a claim that the installed firmware lacks such a policy.  No configuration
was read or changed for this audit.

Prior hardware-composition fallback testing did not restore an already-black
panel; that observation and the existing baseline of continuing software
activity mean this host-vblank line cannot be promoted into a new recovery
candidate.  It is not an exclusion of every composition/display failure.

## Consequence

Do not change a vblank-delay or interrupt setting based on this log.  The
useful future discriminator, if separately authorized, would be a paired
passive capture that retains the same host vblank line together with a
time-bounded owner physical observation and lower display/power tracepoints.
That would still require a separately established live callback binding.
