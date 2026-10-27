# Overnight AVE/HWC findings (offline, no TV actions)

## Boundary and new evidence

The rich-Apps B0/B1 compositor captures advanced while the owner saw a black
physical panel.  At the later HWC fallback capture (`hwc-prevention/check-0356`)
the output still reported `DPMS_ON`; the DRM DP log reported `sync: on`,
`[main] mute: off`, and `set_layer_mute ... blank = 0`.  Thus neither the
Enlightenment HWC fallback request nor this sample reports a normal DRM
software mute/blank command.  This strengthens the existing post-composition
boundary; it does not exclude a panel/TCON/output failure after DP.

## Exact HWC fallback state

The stock server's live HWC report provides a concrete runtime difference,
not merely a policy label:

| state | HWC global | visible relevant surfaces |
| --- | --- | --- |
| normal pre-trial (`before.json`) | `mode=1 wait_commit=1 deactive=0` | several 1920x1080 AR24 surfaces in `DV`/`CL`, with DP target surfaces/queues |
| requested fallback (`check-0356.json`) | `mode=1 wait_commit=0 deactive=1` | a `CL` 1920x1080 AR24 surface, one `VD` XR24 surface reported as `4096x121297` with source position `848x480`, plus compositor `DV` targets |

`-hwc 0` causes `deactive=1` / fallback; `-hwc 1` restores
`deactive=0` / normal HWC.  This is live compositor state only, not a TV
setting.  The fallback did **not** recover one owner-confirmed black
occurrence. That is a negative recovery result, not a prevention result: it
lowers the priority of a simple HWC/direct-scanout explanation but does not
rule it out for a later transition or panel-path interaction.

The `wait_commit` change and the unusual `VD` geometry are useful capture
markers, but not a proven content detector: no static or live evidence yet
links Apps versus For You/Live to a different `-hwc` command, DP mute, or
TCON command.

## QDDimming machine-code gates (exact build)

`QDDimming::m_SetAPLFilter` at `0x17b191` has no sparse/rich content,
motion-score, or hysteresis branch of its own.  Each invocation copies the
following QDDimming state into a stack backend request and calls the backend
virtual slot `+0x210` when the backend pointer is non-null:

```
+0x160 (u32), +0x15a (u8), +0x159 (u8), +0x44c (u8),
+0x294 (u32), +0x00c (u32), +0x124 (u32)
```

Those are opaque policy/state fields in the stripped binary.  In particular,
this routine itself does not compute APL from compositor pixels.  The actual
APL algorithm, its thresholds, and its counters are behind the selected
backend's virtual `+0x210` method; they are not recoverable from the dispatcher
alone.

`QDDimming::m_SetScreenSaver` at `0x17b205` has a concrete eligibility gate:

1. QDDimming field `+0x450` must be nonzero.
2. It computes a boolean request field from **any** of: `+0x15a != 0`, `+0x159 != 0`,
   `+0x160 == 1`, or source/context field `+0x00c` equals `0x00050010` or
   `0x00070007`.
3. It submits a backend virtual `+0x200` request containing fields `+0x284`,
   `+0x2b8`, that computed boolean, `+0x124`, and the screen-saver policy field
   `+0x520`.

This is a strict improvement over the earlier generic description: a static
scene is **not** an eligibility condition in this dispatch body.  The only
identified input capable of selecting the factory/zero SS path there is the
pre-existing `+0x520` policy field.  Field names and the semantic meaning of
the five eligibility values remain unknown; no setter should be inferred from
their offsets.

`QDDimming::t_vSyncCallBack` at `0x17b35d` is a large bitmask dispatcher.  It
first requires nonzero fields `+0x39` and `+0x5c` and requires `+0x1b4 != 1`.
It then consumes pending-operation bits at `+0x18c`, invokes multiple feature
handlers, and selects output handling based on `+0x6c` values 0–5.  It is not
a simple per-vsync static-image detector. The callback's calls are conditional
on pending-operation bits. No fixed delay constant occurs in these small
dispatch bodies; timing is not established, because sparse For You has also
blacked immediately after wake while other observations were delayed/varied.

## Concrete backend and upstream writers

The active QD screen-saver virtual resolves to
`DimmingBackendRoseMQDMNT::t_SetScreenSaver` at `0x1cb2d9`.  Its first
operation loads the Factory UID `0x5019` data.  Its cached static values are
the already-known factory screen-saver brightness/method/wait/slope values;
it compares request field `+0x10` (the QDDimming `+0x520` policy value) and
emits the selected backend configuration only when the cached state changes.
This connects the QDDimming policy field to the QD factory baseline, but not
to a panel-power command.

The direct upstream writer is equally narrow:

```
QDDimming::SetTconScreenSaver(int) @ 0x1735fd
  -> if initialized (`this+0x18 != 0`), store the input verbatim at +0x520
```

It does not range-check, schedule a timer, call AVOC, or call the backend
itself. Its caller/state writer is therefore the missing control point; it
must not be described as a fixed 30-second timer.

Later exact recheck: the checks in step2 do not suppress the backend call
when false; they select request field `+8`. Only the initial `+0x450` gate
suppresses this route. The QDMNT backend selects SS brightness using request
`+0x10`, without using the computed boolean to gate its setter calls. See
[the content/duty audit](../tcon-research/qd-content-duty-policy.md).

Two adjacent public setters write separate QDDimming fields:

```
SetAutoDim(int)                   @ 0x172a35 -> +0x2a8
SetScreenProtectAppLaunched(int)  @ 0x172acd -> +0x2b4
```

Neither is `+0x520`, and neither appears in the `m_SetScreenSaver` eligibility
branch decoded above.  They must not be assumed to disable the screen-saver
policy.

The available APL backend override is
`DimmingBackendRoseMWOLED::t_SetAPLFilter` at `0x1bf93d`.  It gates on request
bytes `+4/+5`, normalizes source/context `+0x0c` against two constants
(`0x00020000`, `0x000a0000`), caches changed values in backend globals, and
submits command ID `0x827` through the backend transport.  It contains no
elapsed-time counter or generic “static content” test.  This identifies an
actual APL wire-command family, but does not prove this S95F is using this
backend for the currently observed Home state; the QD screen-saver backend is
the MQDMNT implementation above.

## AVE static-dimming dispatch: confirmed interfaces, not a content rule

The exact captured `libave.so.0.1` exposes separate DimmingInterface calls for
`SetHomeUI`, `SetScreenProtectAppLaunched`, `SetAutoDim`, `SetLogoDetection`,
`SetAutoBriReduction`, `SetLowPowerAmbientMode`, `SetPanelMute`,
`SetVideoSignalActivity`, and `SetTconScreenSaver`.  This proves that Home
context, static-image protection, and panel mute are *independent inputs* to
the dimming implementation.  It does not show that a sparse Home tab invokes
any particular one; the restored CSFS/CompTerra audit found no direct tab-ID
call to AVOC/panel power.

The only fully resolved static-image scalar remains `SetTconScreenSaver`:
QDDimming stores the requested value at `+0x520`; backend screen-saver apply
uses zero for SS brightness zero and nonzero for factory SS brightness.  It
does not accept a documented “disable” value.  Existing visible-panel evidence
at both zero and factory-7 means that scalar is not sufficient to cause or
avoid this fault.

## Read-only discriminators for a later collected trace

1. Timestamp AVE/AVEMonDIM messages containing `SetHomeUI`, `AutoDim`,
   `Logo`, `AutoBriReduction`, `ScreenProtect`, `LowPowerAmbient`,
   `SetPanelMute`, and `SetTconScreenSaver` across a single Apps versus
   For-You/Live transition.
2. In the same window capture HWC global line plus `-hwc_wins`, DRM-DP
   `mute|blank|sync|outpath` logs, AVOC panel-mute getters, and an
   Enlightenment PNG.  This distinguishes policy request, composition mode,
   and downstream output state without sending a setter.
3. Treat `mode`, `wait_commit`, `DV/CL/VD`, APL, lamp, and `QD_TCON_OFF` only
   as correlated markers.  None is currently a valid trigger for automatic
   recovery or a proof of panel power state.

No direct AVE route from APLFilter/AVEMonDIM to Apps-vs-UG content selection
was resolved in this pass. AVEMonDIM runs in `avocd` and uses this copied AVE
library. The virtual backends are now identified; the remaining upstream
boundary is the external caller of `ppi_ve_set_tcon_screen_saver` / AVE's
virtual `SetTconScreenSaver` path, which has no direct branch reference due to
virtual/PPI dispatch.

## AVOC/PPI boundary

`avocd` does import `ppi_ve_set_tcon_screen_saver`; its matching internal
wrapper string is `avocd_ave_api_set_tcon_screen_saver`. The captured public
`org.tizen.tv.avoc.AvOutputControl` D-Bus interface contains no
`SetTconScreenSaver`/screen-saver method.  Consequently this policy is not a
public Home or D-Bus setter: the call is internal to AVOC/AVE and can be made
by AVOC's monitor thread (the observed `AVEMonDIM` thread belongs to avocd).

The actual imported PLT call site is now recovered: relocation index 137 maps
to ARM PLT `0x1ba58`; exactly one Thumb `BLX` call occurs at `0x7e540`, inside
a wrapper starting `0x7e4b8`. That wrapper explicitly loads zero into `r5` at
`0x7e4f4`, moves it to argument `r0`, and invokes the PPI. Thus this recovered
wrapper always requests **zero**, not a caller-provided boolean. Its nearby
logging identifies the internal AVOC screen-saver API wrapper.

This is evidence for an AVOC-side reset/zero request, but not yet evidence of
the condition that schedules it or of a nonzero counterpart. That caller is
now resolved: avocd code at `0xc9414` constructs callback address `0x7e4b9`
(Thumb form of wrapper `0x7e4b8`), passes key-combination ID `0xbe`, and calls
`KeyCombination_Add_Handler` through PLT `0x1b5e4` (relocation index 42).

Therefore the recovered zero request is a **key-combination handler**, not a
periodic AVEMonDIM timer, public D-Bus method, or direct Apps/For You tab
policy setter. It must not be used as a Home workaround and no unknown key
combination should be sent to exercise it. This only rules out this particular
zero-PPI wrapper as the direct normal Home-policy source; it does not rule out
other AVOC/AVE state writers. Do not invent a D-Bus call to this private PPI.
