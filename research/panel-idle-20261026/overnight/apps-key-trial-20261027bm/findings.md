# One ordinary Apps-key request with no confirmed foreground transition

The independently reviewed fixed normal AppControl sender was prepared once, invoked once, and cleaned up. It sent only com.samsung.tv.csfs with switch_page=d/apps.tab and entry_point=apps_key; no Operation or no-raise flag was added. There was no Home key, controller request, vendor USB operation, power change, settings change or firmware/code patch on the TV.

The initial offline build had a wrapper/manifest schema mismatch. Independent review caught it before any staging or target request; review-hold.json preserves that result. The corrected build added a real production manifest-loader check, was rebuilt/repinned, and passed independent re-review. The executed manifest is16dde8936e80b3366600a07f5633f23eaa9d321015a93b644f40b863ed5ecd6e; review-pass.json supersedes the older pin in intent.json. No failed old build was deployed.

Preparation, one send and explicit cleanup all exited zero. The one managed result reports send_attempted=true, send_returned=true, target_operations=1 and no exception. All retained root calls have authenticated uid/euid0, successful non-timeout command results and empty stderr. Cleanup proves the exact private stage absent.

Before and after, cached current_tab is still d/ug.tab@ForYou; GL screensaver windows remain mapped. Thus the Apps-key route did not establish a foreground Apps transition, just as the earlier switch-page-only request did not. A returned SendLaunchRequest is submission, not consumption or focus acknowledgement. The owner then confirms the physical screensaver is still visible and asks whether to click. No click is requested: cached current_tab remains For You. Physical confirmation is retained separately in owner-observation.json; native software physical flags remain false. No further request, forced saver dismissal or retry follows this no-change result.

See ../ui-focus-analysis-20261027bk/findings.md for source constraints and possible hidden/focus handling. This does not diagnose or repair the panel fault. The latest controller action remains BI MODE2; BI's failed recording does not qualify any post-X/vendor read.
