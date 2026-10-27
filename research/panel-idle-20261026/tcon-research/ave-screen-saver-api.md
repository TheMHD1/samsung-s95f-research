# AVE static-dimming policy path (offline exact-build analysis)

Scope: this document describes only the exported userspace policy path in the
captured `libave.so.0.1` and `libvideoenhance.so.0`.  It is not a recommendation
to access TCON registers, kernel modules, thermal controls, or compensation.

## Exact interfaces

* `libvideoenhance.so.0`: `int ppi_ve_set_tcon_screen_saver(int)` (Thumb export
  `0x46f391bd`).  The wrapper preserves its single integer and calls the loaded
  video-enhancer implementation; it returns `-95` when that implementation or
  its method is unavailable.
* `libave.so.0.1`: `int ave_api_set_tcon_screen_saver(int)` (Thumb export
  `0x0029530d`).  This is the underlying AVE API.  It calls the active
  `VideoEnhancerImpl::set_tcon_screen_saver(int)` virtual method and returns the
  implementation result.
* `libave.so.0.1`: `int ave_tcon_get_screen_saver_status(int *)` (Thumb export
  `0x0025fc51`).  This is a read-only hardware-status query, not a saved-policy
  getter.  It rejects a null pointer, queries TCON command `0xf380` with argument
  `9`, copies raw-status bit 0 to the caller's `int`, and logs raw bit 4 as a
  separate TM status flag.

`/usr/bin/avocd` imports the same `ppi_ve_set_tcon_screen_saver(int)` wrapper.
There is no `SetTconScreenSaver` member in the captured public AVOC D-Bus
interface or in `libavoc.so`; therefore this must be used only through the
loaded AVE/video-enhance process interface, not by inventing an AVOC RPC.

## Meaning of zero and nonzero

In this exact build, `QDDimming::SetTconScreenSaver(int)` stores the argument at
its configuration offset `+0x520`.  On the next `m_SetScreenSaver()` operation,
that field is placed in `BackendQdScreenSaver_t + 0x10`.

`DimmingBackendRoseMQDMNT::t_SetScreenSaver()` tests that field:

* zero selects SS brightness `0`;
* nonzero selects the normal/factory static-screen-saver brightness path.

This agrees with the captured kernel sequence: AVEMonDIM set SS brightness zero
as the image came back, then roughly 30 seconds later requested the factory SS
brightness (`Fac_ss:7, value:1`).  `QDFTcon_SetQdSsBrightness(value=1)` means
"use factory SS brightness"; it is not a raw panel brightness of one.

The API does not range-check arbitrary integers.  Any controlled use must
therefore use only `0` and `1`; it must not set the separate `qd_ss_method`,
brightness, wait-time, or slope APIs, which alter factory tuning.

## Bounded test constraints

The least invasive test candidate is a single session-only policy call with
`0`, followed by a guaranteed `finally` restoration with `1` after a short,
fixed interval.  This changes only the static-screen-saver policy; it does not
intercept fault recovery or power/thermal/compensation safety paths.

The status query should be collected before and after as evidence, but its bit
0 reflects the *currently applied TCON state*.  It must not be treated as the
previous desired policy or used to choose the restore value: an idle screen may
legitimately report zero while normal automatic policy remains enabled.

Current captured UI policy says the hidden Screen Saver setting is On, so `1`
is the appropriate restoration only for this particular TV state.  If that
setting has changed before any trial, do not infer a restore value from the
hardware-status query; re-check the user-visible/supported policy first.

No persistence, recurring renewal, direct TCON command, driver reload,
register write, thermal override, or fault-monitor suppression follows from
this analysis.
