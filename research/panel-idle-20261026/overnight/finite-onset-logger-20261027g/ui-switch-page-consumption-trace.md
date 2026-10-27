# `switch_page` consumption trace

## Scope and result

This is an offline comparison of the stock Apps sender, the reviewed managed sender used in V4/V5/V6, and the CSFS receive/consume path. No TV call, UI request, rebuild, or target change was made.

The managed requests match the visible stock payload key and For You page identifier, and CSFS has no visible `Operation` test on the direct `switch_page` branch. There is therefore no proven receiver gate that was definitely unmet by V4/V5/V6. There is, however, one concrete call-parity gap: stock code passes its dictionary through `Tizen.TV.Service.CoBA.Core.Util.AppLauncher.LaunchApp`, whereas the managed helper constructs and sends a bare `AppControl` directly. The retained sources do not contain `AppLauncher.LaunchApp`'s body, so whether it supplies an operation, caller/action metadata, or other launch semantics is unresolved. That gap cannot safely be converted into a guessed fix.

The CSFS trace also shows that `SendLaunchRequest` returning is not consumption proof. The request can be skipped before conversion by NUI lifecycle state, cleared by category-priority handling, or converted and sent as an internal page event without establishing that the page model accepted the requested tile. The unchanged `memory/eden/current_tab=d/apps.tab` in V4–V6 proves lack of the requested state transition, but does not identify which of those boundaries stopped it.

## Evidence pins

- Stock Apps IL: `apps-only-20261026/AppsCommon.dll.il.txt`, SHA-256 `006c10466bc9ffe128a3ef12ea9727017b131840030420930222ce40bd312c94`.
- CSFS IL: `live-cast/csfs.il.txt`, SHA-256 `4f2a9de91fa710593d0f61a9634f70d5cd015a02d2245150c8e661e76052a811`.
- Managed sender source: `overnight/managed-ui-tab-launch/Program.cs`, SHA-256 `43aa6067d1012c318d84b4204a6708da0df8a77bfb8a1f3d45f538090faf32c0`.
- Stock CoBA Core binary whose `AppLauncher` body is not present in the retained text dumps: `live-cast/framework/Tizen.TV.Service.CoBA.Core.dll`, SHA-256 `686716f173c501fae9c87fa9318c7ae7a0ebbcfdeabcdeaed00a1d3b5ad20561`.
- Actual home configuration snapshot `live-cast/home.before.json` records `HomeOperation` and the home/startup/first-screen app IDs as `com.samsung.tv.csfs`.
- V4/V5/V6 managed outcomes are retained under `ui-for-you-onset-v4`, `ui-for-you-onset-v5`, and `ui-for-you-onset-v6`. Their native-outcome SHA-256 values are, respectively, `2796e4a16d82e3d46512521ecf5d8a4d970a390e3bfa54a8d65eb34bb7381eb7`, `99924a6ce0518774966813aa1e76198ad6fe5469b9f97aa2b2ced72ce9491a68`, and `ade0b3c8df7ada7225076ef941b3500c3b526229297e811a5269b0e8b9459b76`.

## Sender comparison

### Stock Apps path

`ATHomeCategoryManager.LaunchSwitchPage(String, Boolean)` at IL line 13803:

1. Creates a `Dictionary<String,String>`.
2. Adds `switch_page` with the supplied page string.
3. If the Boolean is true, additionally adds `__NO_RAISE_WINDOW=enable`; if false, it adds no such entry.
4. Calls `LaunchHome(dictionary)`.

`LaunchHome` then asks `FSConfigAdapter.GetConfigStr` for configuration enum `0x2e`, obtaining the home application ID, and calls `Util.AppLauncher.LaunchApp(homeId, dictionary, false)`. The captured configuration establishes that the current home application ID is `com.samsung.tv.csfs`. The third `LaunchApp` argument is the Boolean constant `false`; its semantic name is unavailable in the IL dump.

The stock method does not construct `Tizen.Applications.AppControl` itself and does not visibly set an `Operation`. Consequently, absence of an explicit operation in this method does **not** prove that the eventual stock `AppControl.Operation` is empty: that construction occurs inside `AppLauncher.LaunchApp`, whose implementation is not present in the retained IL text.

The Boolean passed into `LaunchSwitchPage` by the relevant external caller is also not recovered here. Therefore, managed omission of `__NO_RAISE_WINDOW` is parity with the stock `false` case, but parity with the actual intended For You call is not established.

### Managed V4/V5/V6 path

The reviewed helper directly creates `AppControl`, sets:

- `ApplicationId = com.samsung.tv.csfs`;
- extra key `switch_page`;
- extra value `d/ug.tab@ForYou`;

and calls synchronous `AppControl.SendLaunchRequest`. It intentionally does not set `Operation` and does not add `__NO_RAISE_WINDOW`.

All three retained outcomes report ARM32 ABI accepted, boot matched before and after, request constructed, one send attempted, send returned, handle disposed, and no exception. They explicitly retain `operation_set=false`, `no_raise_window_set=false`, `execution_confirmed=false`, and `physical_picture_observed=false`. Thus they prove successful return from the client API, not receiver execution.

| Field/path | Stock visible code | Managed V4–V6 | Parity status |
|---|---|---|---|
| Destination app | Config enum `0x2e`; captured config resolves to `com.samsung.tv.csfs` | `com.samsung.tv.csfs` | Matched for captured configuration |
| Extra key | `switch_page` | `switch_page` | Matched |
| Requested value | Caller-supplied | `d/ug.tab@ForYou` | The receiver accepts an arbitrary nonempty string; stock origin of this exact For You value is not shown in this method |
| No-raise extra | Conditional `__NO_RAISE_WINDOW=enable` | Absent | Matches only the stock `false` case; actual caller Boolean unknown |
| AppControl construction | Hidden in `AppLauncher.LaunchApp` | Direct managed construction | Concrete call-parity gap |
| Operation/action metadata | Not visible before `AppLauncher` call | Operation left unset | Exact parity unresolved |
| Third launch argument | Constant `false` | No corresponding wrapper call | Semantic parity unresolved |

## CSFS receiver path

### Entry and early gates

`NUIApp.OnAppControlReceived` (CSFS IL line 10566) first checks an internal `waitPauseWhenHideByPartialKey` field. When set, it logs a skip and returns without invoking the converter. When not set, it calls the base NUI handler and then `AppControlConverter.OnAppControlReceived`.

If the converter returns an event, NUIApp extracts `entry_point`, applies `PreCheckCategoryPriority`, and can clear the converted control/event when that check rejects it. Only the surviving event is forwarded through the resolved handler and the CSFS show controller. These are concrete receive-state gates, but the V4–V6 records do not capture the corresponding internal field or branch results. V6 showing CSFS focused and no screensaver immediately around the send does not prove either gate's value.

### Extra-data conversion and `switch_page`

`AppControlConverter.OnAppControlReceived` (line 51046) obtains the received caller application ID and copies every received extra-data key/value into its internal control dictionary. This copy is conditioned on nonempty extra data, not on `AppControl.Operation`.

The direct `switch_page` branch at IL offsets `0x0672..0x06ce`:

1. Reads `switch_page` from the copied control.
2. Requires only that the resulting string be nonempty.
3. Temporarily sets `CallByResume=true` on the resolved object when present.
4. Sends internal view event `0x0d` with the requested page string.
5. Restores `CallByResume=false`.
6. Stores the page string in static field `04000177`.

After this event has already been sent, caller IDs `org.tizen.art-app`, `com.samsung.tv.ghdaemon`, and `com.samsung.tv.lightwarp` receive a special informational branch. That caller-ID list does not guard entry to the `switch_page` branch itself.

The converter then calls `CurrentState.PageLoadingCompletedInvoke`. Nothing in the inspected branch validates that the requested ID exists, that the internal event was accepted, or that `memory/eden/current_tab` changed.

No read of `AppControl.Operation` appears in the inspected converter path. Therefore an unset managed `Operation` is a sender-parity uncertainty, but it is not a demonstrated rejection condition at this receiver branch.

### Later focus consumption

`FocusPosition.SetFocusOnShow` eventually tries `SetFocusBySwitchPage` after several higher-priority focus strategies. `SetFocusBySwitchPage` (line 54320) reads the same `switch_page` value, returns false if it is empty, and otherwise logs `Done - Switchpage` and returns true. It does not itself change the page. The actual page-switch attempt is the earlier view event `0x0d`; this later method only claims the focus-selection opportunity after the show lifecycle reaches it.

This ordering matters: a successful nonempty extra is not equivalent to a completed tab transition, and observing CSFS focused does not prove that internal event `0x0d` selected the requested page.

## What V4–V6 establish

- The same fixed For You request returned successfully three times without a client exception.
- V4 and V5 occurred with the screensaver in front, so they cannot isolate normal visible-home consumption.
- V6 verified no screensaver immediately before and after the request and showed the focused CSFS window, yet `memory/eden/current_tab` remained `d/apps.tab`.
- Therefore screensaver occlusion is not a sufficient explanation for the unchanged tab.
- The retained sender outcome does not include receiver logs, caller ID as seen by CSFS, `waitPauseWhenHideByPartialKey`, category-priority result, internal event `0x0d` delivery, page-model lookup, or an acknowledgment from the destination.

## Bounded conclusion

No concrete receiver condition can currently be labeled the proven failing gate. The most specific proven mismatch is architectural: stock routes the dictionary through `AppLauncher.LaunchApp`; the managed helper bypasses that wrapper. Missing operation/action/caller semantics are plausible contents of that gap, but are not established from the retained code and must not be guessed.

The downstream consumption boundary is also unresolved: CSFS can accept the extra and emit view event `0x0d` without the evidence showing whether the page model consumes it. The unchanged current tab is compatible with either non-delivery to the converter, an early NUI/category gate, or a rejected/ineffective internal page event.

Because three finite sends—including one no-screensaver focused-CSFS case—did not produce the requested state, further UI trigger attempts are not justified by this trace. Resolving the boundary would require receiver-side evidence already scoped separately, not another guessed payload or launch variant.
