# Apps request while screensaver remains foreground

After BI owner-confirmed recovery, one normal AppControl request for switch_page=d/apps.tab returned. The owner still saw the screensaver and did not press a button. A later cached UI read still named d/ug.tab@ForYou beneath mapped screensaver windows. Therefore the request is not an Apps-transition acknowledgement; no failed physical transition should be claimed either.

The independent firmware_backup_helper offline review identified the following retained IL edges, using the source files pinned in source-pins.json:

- live-cast/csfs.il.txt:51046–51164 enumerates ExtraData without an Operation requirement. Lines51582–51618 convert nonempty switch_page to view event0x0d and cache its string without completion/state validation.
- Lines3830–3872 explicitly take Keep State when __NO_RAISE_WINDOW=enable. The existing sender correctly leaves it unset; adding it is not a focus fix.
- Lines10596–10628 may skip receiving while waitPauseWhenHideByPartialKey; lines10693–10714 may clear converted control after priority preprocessing. Lines61006–61040 defer focus work when CurrentState.Shown=false even on focus-gained. These are candidate boundaries, not observations that a particular one ran.
- Lines61231–61269 route generic switch_page focus through type0 without add_type=App. The explicit entry_point=apps_key branch at61204–61229 routes type1 with MEDIA_APPS_TILE_ID. CheckShowStatus recognizes apps_key at4036–4058; SetFocusByAppKey sends the Apps-tile event at54529–54590.
- apps-only-20261026/AppsCommon.dll.il.txt:13803–13842 shows stock LaunchSwitchPage also sends switch_page alone, plus optional no-raise. Thus omission of add_type=App does not explain nonconsumption of the direct event0x0d path by itself.

No retained CSFS code proves switch_page dismisses the separate GL screensaver or raises above it. The source cannot distinguish this request being skipped, ignored while hidden, or deferred. A fixed ordinary AppControl Apps-key request is a bounded navigation candidate, not a diagnosed panel repair. A separately built helper may submit only switch_page=d/apps.tab plus entry_point=apps_key, once, with no power/controller operation; physical and cached results must be recorded separately. No automatic saver dismissal, Home key, reset or retry is included. If it also leaves the screensaver foreground, stop rather than treating API success as visible navigation.

The separately reviewed Apps-key trial is now complete at [BM](../apps-key-trial-20261027bm/findings.md). One fixed request returned and cleaned up; cached current_tab remained For You and the owner confirmed screensaver was still physically visible without a click. This is a no-confirmed-navigation result, not proof of which hidden/focus branch ran. No automatic saver dismissal or repeat follows.
