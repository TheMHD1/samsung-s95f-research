# BX fixed-tab pixel intervention candidate

This directory contains an offline-built .NET 6 candidate and reproducible checks. No TV, root transport, display, controller, firmware, protection, UI database or recovery operation was performed by this task. The user has already authorized TV work; future target steps are centrally coordinated and depend on technical qualification, not another permission request.

**Status:** source/build checks pass; the target EFL/session/timer and physical behavior remain unqualified. `target-package.tar.gz` is a staging artifact, not an instruction to launch it. It contains only `ManagedEflContentOnce.dll`, `.deps.json` and `.runtimeconfig.json`. The managed IL is portable; live entry rejects anything other than little-endian ARM32. Native libraries stay stock and are not packaged.

## Behavior

The exact live modes are `--execute-sham`, `--execute-change`, and `--check-native`. No arguments prints the zero-native-call dry plan. `--self-test` runs pure fixtures, with no native/library initialization or target access. Unknown arguments reject silently with exit 63; incompatible ABI rejects before any native call with exit 64.

Every compatible live mode must first successfully arm a **CLOCK_MONOTONIC POSIX timer delivering SIGKILL to this process after 30 seconds**. SIGKILL cannot be handled or blocked by the helper. The timer is not cancelled before process exit. It bounds a stuck event loop after arming, independently of managed scheduling. Managed runtime startup and native timer creation/arming precede that bound; the existing host/root timeout must still supervise launch accounting. A missing/denied `librt` timer binding stops before EFL initialization. The host test establishes Linux POSIX timer semantics, not the ARM32 target binding.

The helper discovers a unique CSFS process from `/proc` (exact app ID/path or CSFS DLL anchor), retains PID/start ticks/cmdline, parses only the session runtime directory, Wayland display and D-Bus session address from its environment, and checks UID consistency. It does not log unfiltered environment. It requires `/run/user/<discovered uid>` and resolves the Wayland symlink under `/run`; the final socket must have qualified ownership and permissions. It copies those session values into this process only. It rechecks session identity before arming and each pixel epoch. It does not assume UID 5001 or `wayland-0`; those values happen to appear in the parent's filtered retained evidence.

Before display calls, all required EFL symbols are resolved. `--check-native` stops after discovery/export checks; it does not initialize Elementary or create a window. Loading stock libraries can execute their constructors, so this mode is a native qualification action, not advertised as a universally side-effect-free getter.

Each execute mode creates one vendor notification window (upstream type 12, level 40, layer 900), skips focus, sets an empty input rectangle and pass-events, and disables that window's effects. Its 1920×1080 logical canvas has 144 preallocated 120×120 rectangles. No fonts, images, scene parsing, child process, video source switch or new window occurs during an epoch. All rectangles are opaque; RGB code values are at most 48. Gray48 is a candidate baseline, not a proved stabilizer or measured luminance.

The window is initially gray. The helper creates `ready.json` and then waits at most eight seconds for a new regular stage file named `arm`, containing exactly:

```text
BX-ARM-FOR-YOU-V1
```

The terminating LF is required. Publish `arm` atomically from a completely written private temporary file using rename; a partially written assertion is rejected, not retried. The unique private stage must initially contain none of `arm`, `ready.json`, `done.json` or `events.jsonl`. The parent must verify fresh physical visibility, fresh accepted clean RT, selected For You and stable Home/focus/fullscreen state **before** writing this assertion. The helper has no tab getter and labels this a central-controller assertion; it cannot upgrade that assertion into measured tab evidence. If the stage or assertion is stale/invalid, CSFS changes, the wait expires, or fewer than twelve seconds remain in the conservative kernel deadline, it quits without running treatment epochs.

The arming time is t0:

| Time from arm | Sham | Pixel change |
| --- | --- | --- |
| t0 to 2 s | Existing gray48 | Existing gray48 |
| 2 s | Set all 144 tiles to gray48 | Set 132 tiles to gray8; retain a centered 4×3 tile patch at gray48 |
| 8 s | Set all 144 tiles to gray48 | Restore all 144 tiles to gray48 |
| 10 s | Request normal loop exit | Request normal loop exit |

Both modes perform the same object-setter count at the same requested epochs. A recurring 25 ms Ecore callback checks the bounded arm wait and schedule; no repeated repaint/damage request is made between epochs. Callback/setter completion over 250 ms late rejects the trial and ends the loop. The 250 ms tolerance is a design acceptance bound, not a presentation guarantee or a claim that the protection threshold is 250 ms.

Normal cleanup hides the window, writes bounded status, and exits the process so its Wayland connection closes. It deliberately avoids vendor EO deletion/`elm_shutdown`, following the upstream raw-window double-unref finding. SIGINT/SIGTERM request main-loop exit via Ecore's thread-safe callback. A SIGKILL deadline cannot run `finally`; the compositor must remove the dead client's surface. **Both normal and forced-death target teardown require an observed smoke test.** The helper does not reset or recover the panel and never automatically repeats a trial.

## Timing evidence and boundaries

`events.jsonl` has at most 32 rows/32768 bytes, each at most 2048 bytes. It contains kernel-monotonic timestamps for ready/arm and each scheduled epoch, plus actual before/after times around Evas color setters. `ready.json` records a construction/mapping request, not a displayed frame. `done.json` is written before process exit and explicitly cannot certify that exit or physical cleanup. Runtime/native stdout/stderr must be collected separately by the central bounded launcher; native EFL diagnostic volume is not included in the JSON journal bound.

All records set `presentation_observed=false`. No render-post callback enum was guessed; setter completion is not a commit timestamp, scanout confirmation or light measurement. The target's notification-plane visibility, geometry, focus behavior, full coverage and alpha/composition behavior remain to be measured.

Pair an accepted run with a centrally qualified last-clean/first-fault RT recorder and independent physical observation. Obtain the actual mode, selected limit and aggregate/operands required for G01/E05 through their separately qualified read contract; this helper performs **no USB/vendor read** and does not recreate the rejected BI/AL combined collector. The arm and pixel request intervals must lie inside accepted recorder coverage. A screenshot can validate intended pixels/window coverage, not emitted OLED light. Preserve visible/faulted and black/clean counterexamples.

Keep For You selected through an accepted comparison. Apps-selected stock recovery, if needed, starts only after the terminal observation and recorder closure; it is a separate operational block and changes the page. A later trial requires a fresh identical baseline and an independent arm. Do not interpret restoration to gray as an independent trial or guaranteed recovery after a latched fault.

## Source and ABI qualification still needed

The parent retained a filtered exact-target CSFS environment in `supporting-files-20261027bx/csfs-session-filtered.json`: it has a Wayland session and `wayland_shm` engine. Historical CSFS maps establish EFL 1.25.1 presence. Those observations support feasibility and the dynamic discovery design. They do not qualify every EFL export, current socket metadata or a root-launched window.

`native-binding-requirements.json` lists the exact modules, symbols and ARM32 layouts. Before target UI smoke, centrally qualify the stock EFL library identities/exports, notification/focus API signatures and return semantics, `librt` timer/clock/statx ABI and applicable socket ownership/modes. Current code deliberately rejects group/world-writable socket nodes; if stock target metadata requires a different rule, inspect that evidence and revise/rebuild instead of silently weakening it. No target acquisition or UI action is embedded in the builder.

A centrally staged `--check-native` can then test the bindings/session without Elementary initialization. An observed Apps-only execute smoke should verify notification coverage, focus/input behavior, the normal ten-second sequence, unarmed expiry, exact process exit/window cleanup and a deliberate helper-only termination. Physical/clean For You baseline comes after that. A foreground launch response alone does not establish helper death after a host transport timeout. Keep the launch's PID/start identity and the independent kill deadline evidence; preserve ambiguous stages and do not retry on ambiguity.

The scene being RGB-only at a fixed tab can disfavor a selected-tab-only explanation if the sham/change results differ repeatedly with Home lifecycle matched. It still couples final pixels with composition/pixel processing and possible electrical load. The helper does not claim a pure electrical workload intervention, root cause, damage repair or permanent prevention.

## Offline build and evidence

Run `python3 build-offline.py` in this directory. It pins the existing SDK host and upstream source bytes, clears NuGet sources, builds with zero warnings/errors, checks dry/ABI/CLI behavior and pure schedule/content/session-parser fixtures, verifies the allowed native surface and absence of inherited hardcoded QN90F paths, and compares a second isolated build byte for byte. A host-only C subprocess test proves a monotonic timer terminates its own child with SIGKILL; it neither contacts nor builds for the TV.

The builder emits deterministic `target-package.tar.gz`, `build-manifest.json`, `native-binding-requirements.json` and `source-provenance.json`. Existing research-phase files are read as provenance only and remain unchanged. The provenance lists pinned upstream URLs and SHA-256 values. Host checks and package hashes are evidence of the candidate's bytes and contracts; they are not target execution/physical qualification.
