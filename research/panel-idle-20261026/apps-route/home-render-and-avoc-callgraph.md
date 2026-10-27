# Home render, AVOC, and screen-saver call graph (static audit)

## Boundary: what the restored Home assemblies can do

The restored CompTerra and CompHome assemblies construct CoBA entities,
tabs, rows, and view-models.  Their observed direct outputs are component IDs,
SQLite/UI JSON entities, and a tab-list cache.  They do **not** import the
screensaver C API, `deviced` display-state API, TCON ioctls, panel mute API,
or a direct power/suspend API.

CompTerra's `CompUGTabCache.GetItems` uses a different content source for
For You and Live: it looks up the tab's component IDs dynamically and appends
`s/terra.bottom@…`.  The Apps tab is independently present in the native tab
map (`d/apps.tab`) and its populated rows are backed by the native Apps
content database.  This establishes a content/render-tree difference; it does
not establish a different panel-output or power source.

The exact original `CompTerra` (SHA-256
`b05655ed…7b7fe9f1`) makes that separation sharper.  Its
`CompUGTab.OnSelected` does only logging followed by the base
`Component.OnSelected`; it does not call AVOC, Screen, panel-mute, or window
APIs.  Its `UGComponentManager.UpdateChilds` explicitly skips
`Component.ReloadChild` when the child ID is `d/apps.tab`, while it reloads
the other children.  The For You/Live observer accepts only
`d/ug.tab@ForYou` and `d/ug.tab@Live`; when a server tab list lacks Apps, it
adds a native Apps tab model (`100`, `apps`, `d/apps.tab`).  Thus Apps is
delegated to its native content path while For You/Live go through the
dynamic UG reload path.  That is a real rendering/data-path distinction, but
there is still no AVOC or panel-control call in either path.

The legacy Home preference is relevant to density, not power ownership.
`CompHomeTabCache.GetItems` reads `db/eden/homeRecommendation`; when the
literal is `"false"`, it enumerates `AppListManager.Components` and adds
`d/webapp.row@…` entries.  The historical clean script paired `false` with a
launcher list containing only TV Plus, which can produce a sparse Home tree.
The historical restore script writes `true` and an obsolete 11-entry launcher
list, so it must not be used as a diagnostic restore.

## CSFS compositor-level behavior

CSFS is the NUI/CoBA presentation process.  It has rich window and page
operations, including `WindowHider.Hide`, `SetWindowVisible`, opacity changes,
view-model creation/removal, and focus handling.  These are compositor/window
operations, not proof of panel mute or DPMS.

`WindowHider` uses Wayland window hints including:

```
wm.hwc.window
wm.hwc.dynamic_opaque_window
wm.screensaver.reset.timeout.exception.hint
screensaver_block_reset_timeout
```

The last two mean that an external screensaver-reset helper is especially
unlikely to identify the root issue.  They do not themselves invoke a display
power-off call.

## The material CSFS → AVOC call path

Static IL establishes a genuine AVOC interaction in the restored CSFS DLL:

```
fullscreen-app-id config change / CSFS entry-exit state
  -> FSAVMuteControl.OnChange / AvocSettingForHome
  -> background worker
  -> Tizen.TV.System.Avoc.Avocd.AvocSetNewHome(1 or 0)
  -> AVOC D-Bus method SetNewHome(int value)
  -> avocd import ppi_ve_set_newhome_inout_state
```

`FSAVMuteControl.AvocSettingOffByAppId` obtains
`memory/appfw/current_fullscreen_appid`.  When a non-CSFS/non-TV-viewer
fullscreen app is active, it calls `AvocSetNewHome(0)`.  Entering appropriate
Home/full-home state schedules `AvocSetNewHome(1)`.  It also watches the
fullscreen-app config key and contains resolution-reapply and panel-mute
coordination code.

### Exact caller audit: Apps versus For You/Live

The complete restored-CSFS IL has only these direct/new-home call sites:

| caller | state supplied | trigger class |
| --- | --- | --- |
| `NUIApp.OnTerminate` | `0` | CSFS process termination when foreground app is not TV Viewer |
| `FSAVMuteControl.AvocSettingOffByAppId` | `0` | a **fullscreen app-id change** to an app other than CSFS/TV Viewer |
| `FSAVMuteControl.<AvocSettingForHome>b__0` | argument passed to `AvocSettingForHome` | lifecycle/full-home state worker |

The audited callers of `AvocSettingForHome` are likewise application-state
paths: `NUIApp.OnResume`, `NUIApp.OnPause`, `NUIApp.SetWindowVisible`,
`NUIApp.OnPowerChange`, and `FullView.ShowModeStateChange`.  `FullView` is a
whole-home show-mode controller: leaving its `ShowModeState==1` calls
`ExitFullHome`; entering full mode registers AVOC handling, tries panel mute
on resume, and controls auto-hide/PIP.  It is not a tab-selection handler.

There is no direct `AvocSetNewHome`, `AvocSettingForHome`, `ExitFullHome`, or
`ExitStandbyFullHome` call from a CSFS tab-selection handler, nor a branch on
`d/apps.tab`, `d/ug.tab@ForYou`, or `d/ug.tab@Live` in those AVOC call paths.
Therefore **selecting Apps rather than For You/Live does not, in the restored
CSFS binary, directly toggle NewHome**.  It could only correlate indirectly
if that navigation also changes the fullscreen app ID, window focus/visibility
or global `FullView` show mode. Those are precisely the state transitions to
capture.

### Testable state and log evidence

`AvocSetNewHome` is asynchronous from the CSFS lifecycle worker. The
following are its non-mutating observations:

* `memory/appfw/current_fullscreen_appid` before/after a tab switch;
* CSFS logs: `AvocSettingForHome`, `AvocSettingOffByAppId`,
  `call AvocSetNewHome(1)`, `AvocSetNewHome(0)`, `SetWindowVisible`, and
  `ShowModeStateChange`;
* AVOC logs: `New Home (%d)` and the existing source/HDR/multiview/VRR line
  ending in `new home(%d)`;
* passive AVOC `GetPanelMute` / `GetPanelMuteCaseStatus` values and deviced
  screen state at window boundaries.

No public getter for the NewHome flag was found in the captured AVOC D-Bus
introspection. A matching `New Home (0|1)` AVOC log is therefore the precise
confirmation of applied state, while the CSFS log is only evidence of a
request.

This is the only audited Home-adjacent route into AVOC.  It is a **state hint
to video enhancement**, not a demonstrated `SetPanelMute`, `deviced` DPMS, or
TCON power request.  `avocd` imports `ppi_ve_set_newhome_inout_state`; the
captured AVOC D-Bus interface separately exposes `SetNewHome`, `GetPanelMute`,
`GetPanelMuteCaseStatus`, and `SetPanelMute`.  No static call path from a Home
tab ID to `SetPanelMute` was established.

### AVE-side resolution of the NewHome call

The matching AVE binary resolves the AVOC import as:

```
ppi_ve_set_newhome_inout_state(bool)
  -> impl_set_newhome_inout_state                 (0x2a53f9)
  -> VideoEnhancerImpl::set_newhome_inout_state   (0x29f25d)
  -> ave_api_set_newhome_inout_state(int)         (0x28c039)
  -> ave_frc_api_set_newhome_inout_state(int)     (0x246849)
```

That code records `m_iNewHomeMode`, invokes one unnamed virtual method on the
initialized dimming instance, and submits a vendor FRC operation through
ioctl `0xc00866ff`; model/low-power-art and vfreq gates are also present.
The AVE audit found no direct call edge from this path to QD TCON power
control, QD screen-saver brightness, or the AVE panel-mute APIs.  The unnamed
virtual dimming dispatch means the evidence cannot prove *no* dimming effect.
It does prove that Apps/For You is not a direct NewHome switch and that a
NewHome log transition alone is not evidence of a panel-off, panel-mute, or
screen-saver command.

Consequently, comparing `SetNewHome` state, fullscreen-app ID, AVOC panel mute
state, and screen/display state across A/B states is the highest-value
non-mutating observation.  Do not call `SetNewHome` or `SetPanelMute` during
the comparison: both are actions rather than observations.

## Passive capture targets

Capture these in the same monotonic-time window as the kernel/vlog stream:

1. AVOC logs containing `New Home`, `AvocSetNewHome`, `PanelMute`,
   `ppi_ve_set_newhome_inout_state`, and resolution events.
2. Read-only D-Bus getters `GetPanelMute` and `GetPanelMuteCaseStatus`, plus
   deviced `GetScreenState` and `BurnInProtectionInProgress`, once before and
   after each A/B window.
3. The values of `memory/appfw/current_fullscreen_appid`,
   `memory/eden/display_current_source`, `db/eden/homeRecommendation`, and
   `db/eden/launcher/list` (read only).
4. CSFS/window logs containing `SetWindowVisible`, `WindowHider`, `Visible`,
   `WindowFocused`, `opacity`, `ApplicationWindowAppeared`, and `OnPowerChange`.
5. Screensaver and display-path messages as specified in
   `content-dependent-blackout-investigation.md`.

An observed `AvocSetNewHome(0/1)` transition without panel mute/DPMS would
show a normal rendering-mode transition, not a cause of the blackout.  A
panel-mute or DPMS transition immediately following it would identify a
specific path for further audit.

## `vd-nui-objectdump`: exact static behavior

The copied matching binary is a small **request tool**, not a compositor tree
printer or a framebuffer/screenshot tool. Its ARM code reads
`memory/uifw/nui_objectdump_state`, obtains the AUL window stack and focused
window/PID, accepts an optional `--pid <decimal-pid>` override (and an optional
third decimal state selector), writes the selected PID string to
`memory/uifw/nui_objectdump`, then writes state `3` to
`memory/uifw/nui_objectdump_state`.

That asks the selected NUI process to emit an object dump through its own
diagnostic path. It changes diagnostic VCONF state, so it is not part of the
initial read-only A/B collector and is not a screenshot endpoint.

## Decisive compositor-versus-panel capture

The matching `enlightenment_info` binary supplies the useful capture boundary.
Its embedded help establishes these passive compositor queries:

```
enlightenment_info -topwins
enlightenment_info -topvwins
enlightenment_info -compobjs simple
```

They report all windows, top visible windows, and a simplified composition
object view respectively. The first two include window/client identity and
visibility/composition fields; they are the lowest-risk window-tree capture.

It also documents an image dump command:

```
enlightenment_info -dump_screen -p <existing-empty-output-directory> -n <label>.png
```

`-dump_screen` writes a PNG of the current Enlightenment composited screen;
it does not alter panel settings. It is the decisive early A/B metric when
used with an explicit fresh capture directory and distinct filenames.

Interpretation:

| Physical panel | compositor PNG | strongest next implication |
| --- | --- | --- |
| visible | visible Home/App pixels | capture/control path is sane |
| black | still-visible Home/App pixels | compositor has a frame; investigate output/panel/AVOC/DPMS after the compositor |
| black | black/empty frame | investigate CSFS/Enlightenment visibility, a screensaver overlay, or a composition path before the panel |
| black | capture fails | compare window tree and service/log state; failure is not evidence that the compositor frame is black |

Capture `-topwins`, `-topvwins`, `-compobjs simple`, and `-dump_screen` in
the stable full-Apps control, then immediately after the owner reports the
sparse-Home physical blackout. Preserve command timestamps and hashes of the
PNGs. Do not use `-frender`, `-scrsaver enable/disable/timeout`, `-prop` with
a value, `-hwc`, `-dump` buffer toggles, `-kill`, or any other action command
in this comparison.

## Tools not yet invoked: safe discovery sequence

The TV has `/usr/bin/screend`, `/usr/bin/vd-nui-objectdump`, and DRM debug
directories. `screend`'s options have not been assumed. Before any collector
uses it, record only its usage text/version behavior:

```
/usr/bin/screend --help
/usr/bin/screend -h
```

Run one command at a time, preserve stdout/stderr and exit status, and stop
after the first recognized usage output. Do not invoke an unrecognised mode.
If a documented read-only listing/dump mode is revealed, capture it in both A
and B states; use it to compare surface visibility, opacity, z-order, buffer
attachment, and current focus. Treat `vd-nui-objectdump` separately as an
opt-in diagnostic request after its destination/log behavior is identified.

For DRM, first enumerate only:

```
find /sys/kernel/debug/dri/{0,1,2} -maxdepth 1 -type f -printf '%f\\n'
```

Then read only files whose names clearly indicate state/clients/planes/CRTCs;
skip every writeable or trigger-like node.  A useful frame/output diagnosis
needs a difference in plane/CRTC enablement or framebuffer attachment between
the full-Apps and sparse-Home windows.  An empty graphics-class directory is
not a negative result for DRM state.

## No causal claim yet

Full Apps remaining visible while APL/Lamp are zero and the `QD_TCON_OFF`
latch is set rules out neither AVOC state transitions nor intermittent panel
faults.  It does rule out treating those metrics/latch alone as a control
signal.  The next conclusion requires a time-aligned event sequence.
