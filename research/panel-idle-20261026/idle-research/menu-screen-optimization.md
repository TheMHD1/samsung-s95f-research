# Menu Pixel Refresh / Screen Optimization UI

Later follow-up: the owner's automatic ten-minute warning is now text-matched
and traced separately in native `tv-viewer`; its forced/reinforced countdown
requests mode0 off-sensing at its60th callback. This manual EL/Pixel Refresh
menu audit remains a distinct path. See the
[automatic expiry flow](tv-viewer-off-sensing-timeout-flow.md), rather than
inferring the automatic popup from the manual menu's duration or buttons.

Offline IL audit of `binaries/org.tizen.menu.dll`, SHA-256
`f2a5c1daaa515330503800d39d6025267615dff20f6bf78d8ef67d0e4c0c1921`.
The bounded preceding ASCII reference scan found this as the sole candidate in
the scanned app DLLs/tvappapi set; that is not proof of an exhaustive caller
list. The analysis ran a host-side metadata probe; no target assembly code,
TV control, or network operation was executed by that probe. The binaries
were acquired separately through read-only source-file transfers.

## Concrete UI and request ordering

`PixelRefreshView::CreateViews` token `0x06000baa` selects displayed duration
string `"30"`; it reads `system_info::GetInt(1163)` and changes it to `"60"`
only when that value equals `37` (IL `004e..0058`). It inserts that text in the
translation whose identifier says power is turned off for about minutes. This
is UI text selection, not an actual 30/60-minute timer.

`PixelRefreshView::SetButtonsInfo` token `0x06000bab` creates two choices:
`COM_TV_SID_START_NOW` and product SID suffix `_SID_SMNT_CCJUL_START_AFTER_OFF`.
Their actual callback methods are:

| Choice | token / IL | request |
| --- | --- | --- |
| Start now | `0x06001211`, `IL_0066..006c` | `ldc.i4.0`; `DDDisplay::QDDisplayRequestELSensing(QDDisplayELSensingMode)` |
| Start after off | `0x06001212`, `IL_0066..006c` | `ldc.i4.1`; same managed request |

The latter then shows a translated toast at `IL_007c..0096`, with literal
`3000` passed to `GetMenuCommonToastPopupAttributes`; that establishes a
3,000-unit UI toast argument, not panel-maintenance duration. It does not issue
the mode-0 request after mode-1 in this callback. The native client audit
separately establishes mode 0 as a power-off request and mode 1 as the
persisted D-Bus EL request, so the enum semantic names must not be guessed from
the managed literals alone.

The matching managed bridge is also recovered, not assumed from the API name.
Copied `Tizen.TV.System.dll` SHA-256
`72056f70facd6433bd696de41ba857c387c22abfdeaa6032d39f0a640acc9065`,
method token `0x060000b2`, checks `DDDisplay::PlatformPrivilege` and throws
if access is denied. On the allowed path, `IL_001e` loads its input argument
unchanged and `IL_001f` calls `Interop/Deviced::qd_display_request_el_sensing`.
That P/Invoke method is token `0x0600066d`, module `/usr/lib/libdeviced.so.1`,
entry point `qd_display_request_el_sensing`. This closes the static
button→managed wrapper→native mode split. It does not prove a button was used
or that a particular privilege check passed during the owner's popup.

## What this assembly does not establish

This traced PixelRefresh page contains no demonstrated 60-second countdown,
ten-minute timer, auto-start flag, cancel/timeout transition, or a second
request after either button callback. The observed popup may be implemented by
another assembly/process or dynamic UI path. Therefore this assembly proves a
manual two-choice Pixel Refresh UI and managed request values, not the
ordering/cause of the observed automatic prompt.

## Reproduction

`menu-optimization-probe/Program.cs` is now a bounded, hash-guarded
Mono.Cecil probe. It verifies both exact input hashes, prints complete IL for
the five named tokens, records the P/Invoke identity, and checks the
duration-selection branch, button bindings, literal mode arguments, toast
argument, and unchanged managed/native argument forwarding. The earlier broad
keyword scan has been replaced; it was not a precise reproducer.

Run with the local SDK host and both copied files:

```sh
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet run --project ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/idle-research/menu-optimization-probe/MenuOptimizationProbe.csproj -- ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/binaries/org.tizen.menu.dll ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/binaries/Tizen.TV.System.dll
```

[`generated-il.txt`](menu-optimization-probe/generated-il.txt) is the actual
174-line stdout from the passing probe, SHA-256
`c23bceb6b91dfe77ad4c410ed2e2783493e67f1b6d3395f0f4951d85be3456c7`.
`raw.txt` is a separate **curated highlights** file, not verbatim probe output.
No target assembly is loaded for execution and no TV call is made.
