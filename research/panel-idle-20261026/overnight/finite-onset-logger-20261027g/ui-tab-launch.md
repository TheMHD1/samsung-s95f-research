# Fixed normal-UI tab sender

## Purpose

`managed-ui-tab-launch` is a minimal, fixed managed sender for a later bounded
Apps/For You onset capture. It uses the stock Tizen `AppControl` contract and
does not edit the Home database, synthesize a remote key, restart CSFS, or
modify a persistent setting.

The only two requests are:

| CLI | application ID | only extra-data pair |
|---|---|---|
| `--apps` | `com.samsung.tv.csfs` | `switch_page=d/apps.tab` |
| `--for-you` | `com.samsung.tv.csfs` | `switch_page=d/ug.tab@ForYou` |

No `Operation` is set and `__NO_RAISE_WINDOW` is not added. This matches the
retained stock construction pattern: create `AppControl`, assign the
application ID and extra data, then call the one-argument
`AppControl.SendLaunchRequest` overload.

## Target preflight and lifetime

Before constructing `AppControl`, the helper checks all of the following:

- process architecture is ARM, pointer width is four bytes, and byte order is
  little endian;
- `/proc/sys/kernel/random/boot_id` equals the reviewed boot
  `00000000-0000-4000-8000-000000000000`;
- `/proc/uptime` and the boot identifier are captured before the request.

The public `AppControl.SafeAppControlHandle` is retained and explicitly
disposed after the single send attempt. The after-boot and after-uptime values
are then captured. A structured exception records whether failure occurred
during request construction, sending, or handle disposal. There is no retry.

## Staging and timing

The wrapper has three explicit phases:

1. `--prepare` creates a unique root-owned mode-0700 directory and uploads the
   exact managed DLL, deps file, runtimeconfig, and three pinned Tizen framework
   assemblies as root-owned mode-0600 files. It performs no AppControl call.
2. Each `--send` rechecks the boot, `/usr/bin/dotnet`, exact stage inventory,
   ownership, modes, sizes, and hashes, then invokes the managed sender once.
   Separate action directories preserve raw authenticated responses.
3. `--cleanup` is explicit and is intended only after all requested UI actions.
   It deletes the stage only after the same exact-inventory checks pass.

This lets preparation finish before the logger is armed. The For You action
inside the logger window incurs only one root command and one managed process;
there is no upload, self-test, polling loop, retry, or automatic cleanup in
that action.

## Evidence and limits

Retained framework inputs:

- `Tizen.Applications.Common.dll` SHA-256
  `f9d17e5e10632d4001a5381331661104302cc95d12f61567cc61c6cb74ea737c`;
- `Tizen.dll` SHA-256
  `a4f743fd522517584641eb86afe2403ce4134e6e40768da9998242cb095ca93e`.
- `Tizen.Log.dll` SHA-256
  `a2b27f2033177328d0d609f8fab47f3c45bc20a0a30b5f29992b142b02fdf66b`.

The first reviewed five-file deployment is preserved under
`ui-rejected-missing-logbuild`. Its Apps invocation constructed `AppControl`
but failed before `SendLaunchRequest` because `Tizen.Log, Version=4.0.0.0` was
absent from the private CLR probing directory. The structured outcome recorded
`send_attempted=false`, `target_operations=0`, and successful safe-handle
disposal. The associated authenticated runtime-dependency acquisition is
`ui-runtime-dependency-copy.json`; its TV source was
`/usr/share/dotnet.tizen/framework/Tizen.Log.dll`. No UI transition was sent in
that rejected attempt.

`managed-dependency-closure.json` enumerates the ECMA-335 assembly-reference
and native ModuleRef tables for all three staged Tizen assemblies. All
non-framework managed references close within the stage: Common references
`Tizen` and `Tizen.Log`, `Tizen` references `Tizen.Log`, and `Tizen.Log` has no
non-framework managed reference. The remaining `System.*` references are part
of the pinned target .NET 6 runtime. Native ModuleRefs remain target-stock
libraries rather than copied payloads; for the added assembly the only native
reference is `libdlog.so.0`.

The corrected six-file candidate subsequently completed one retained Apps
qualification. `ui-apps-control-v2` reports ARM32 and reviewed-boot preflights,
request construction, one attempted and returned `SendLaunchRequest`, safe
handle disposal, no exception, and `target_operations=1`. Preparation and
cleanup are retained in `ui-prepared-v2` and `ui-cleanup-v2`; cleanup reports
the private stage absent. The independent replay is documented in
`ui-apps-runtime-audit.md`.

That runtime result qualifies only the managed Apps request path. It does not
independently prove that CSFS consumed the request or that the physical panel
displayed the Apps page, so `physical_picture_observed=false` and
`execution_confirmed=false` remain accurate. The For You destination has not
yet been runtime-qualified by this helper.

The CSFS receiver evidence is `live-cast/csfs.il.txt` SHA-256
`4f2a9de91fa710593d0f61a9634f70d5cd015a02d2245150c8e661e76052a811`:
nonempty `switch_page` is consumed by the normal view-event/focus path, and the
two fixed page identifiers occur in the same retained image. The stock sender
construction evidence is `apps-only-20261026/CompAppsTab.before.dll.il.txt`
SHA-256 `4c4a60d8c6ec58c581d43fab4a7a45caa42ddedd285fd7be55362404559a4d90`.

An API return establishes only that `SendLaunchRequest` returned without a
managed exception. It does not prove that CSFS rendered the requested page or
that the physical panel displayed it. Every outcome therefore reports
`physical_picture_observed=false` and `execution_confirmed=false`; external
capture and later audit must establish any UI transition.

The build and independent audit made no TV call. The target run described above
was performed separately and is represented only by its retained authenticated
records.
