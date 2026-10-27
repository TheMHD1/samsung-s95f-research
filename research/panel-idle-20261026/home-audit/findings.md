# Apps-only Home renderer audit

## Evidence

The current Apps-only implementation preserves Samsung's native downloaded-app renderer. It seeds `PreviewManager` with one category, one layer, and five actual tile records, then limits the three native child-list providers to those records. `CompATCategoryTile.Run` is still Samsung code: it creates its element, registers a content-status listener, reads `PreviewManager.Data`, and hides itself when that data is absent. The current five records are present, which accounts for the owner now seeing tiles after the earlier custom-tile failure.

The helper contains no panel-power, TCON, display, screensaver, timer, animation, native-interop, or GPIO calls. Its only background work is none. The original Apps-tab data manager does own a timer, but its timer tick only sets `IsOverTwoHours`; it is not a keep-awake or rendering mechanism.

The visual shell is controlled by existing top-level `d/media.category` and `d/tabs` records. Their extensions already include Samsung's `lighting_url`, `bg_colorchip`, `sidebar_fold_bg`, loading resource and preloading values. CSFS consumes those fields to initialize its sidebar/full-view rendering. The current Apps tab itself supplies a static `home_i_bg_tab_selected.webp` background.

The five-tile row uses an original downloaded-app category record: `CategoryLayer`, `layer_type=applist`, `layer_height=28`, `content_height=14`, `expected_width=14`, and stock focus scaling. Those numeric fields are schema data, but no source evidence establishes that changing them makes five tiles scale to fill the screen. They were copied from Samsung's own downloaded-app group and should remain so absent a controlled cosmetic-only test.

`focused_bg_icon` and `unfocused_bg_icon` are recognized category/tab fields. They represent static assets. The existing shell `lighting_url` resolves to an SVG resource; no audit evidence shows it is an animated surface. There is no demonstrated native provider interface for a safe periodic background update.

The current kernel capture is a normal `deviced` off-sensing/DPMS sequence, not proof of a hardware fault. Its order is explicit: `deviced` logs `off sensing required before power off`, saves result `0`, requests panel DPMS off, mutes the TCON, and powers it off. Only after that does `tcon-monitor` and `AVEMonDIM` report TCON state `0`/non-OK. That state is expected after a power-off and cannot be used as the cause of it. `deviced` subsequently powers the TCON on, gets a successful self-diagnosis, and restores its state. No `ERR DET` or `Fault Occurred` log precedes this current sequence.

The older capture that contains `ERR DET Status:0x10` is separate evidence. It must not be conflated with the normal off-sensing sequence or used to prove the cause of the current idle transition.

## Welcome Mode and `0x40000027`

The copied, exact ARM32 `org.tizen.welcome-mode` executable is a normal power-animation frontend, not an identified Screen Optimization controller. Its embedded source paths name `WelcomeModeApp.cpp`, `MainView.cpp`, `WelcomeModeWnd.cpp`, and rollable/projector audio and animation handlers. It subscribes to power-state changes and has the normal sequence `m_OnOutroAnimationFinishMLED` → `power_off_reason is %d` → `device_power_request_poweroff`, with a fallback `device_power_set_state to standby` path.

The binary contains neither a Screen Optimization/pixel refresh/OLED maintenance string nor a corresponding vconf key, prompt, countdown, cancel action, or 10-minute timer. Its discovered keys and timers concern the welcome power animation, boot sound, retail delay, rollable screen, AirPlay/screen mirroring, ambient support, and accessibility. This rules out using Welcome Mode itself as evidence for a reversible Screen Optimization setting, and rules out disabling it as a safe remedy.

`libdeviced`'s `is_valid_poweroff_reason` accepts `0x40000027`. The ARM code removes the `0x40000000` / `0x20000000` flag bits, then permits base values `1..52`; consequently this value is a flagged valid base reason `39`, not an arbitrary error code. The bundled `libpower-defs` maps *wake* reasons and has no entry for power-off base reason 39, so it does **not** name or decode this power-off value. Neither the Welcome Mode executable nor the copied power-definition library contains the literal `0x40000027`.

Therefore the repeated history record `<off: 1/40000027/.../welcome-mode>` establishes the immediate requester and a valid flagged reason, but does not establish that the request was Screen Optimization, automatic maintenance, or a fault recovery. The observed user prompt is consistent with a separate OLED/ELSensing flow, which `deviced` exposes through `RequestELSensing`, `RequestOffSensing`, and `BurnInProtectionInProgress`; no cancellation/configuration path has yet been demonstrated.

## Decision

Do not add a timer which repeatedly changes `PreviewManager` data or attempts to drive CSFS directly. Such a helper would create cross-thread/lifecycle and UI-update behavior without an audited ownership model. A JSON-only background change would be cosmetic and cannot prevent the normal `deviced` idle/off-sensing path or force a damaged panel/TCON to remain powered.

The safe current state is the native five-app layout. A new complete custom full-screen launcher would need a distinct native component or a signed foreground application, neither of which follows from safe schema-only changes. Samsung's documented application-level screensaver API is suitable only for a foreground application and cannot override global Home or the `deviced` off-sensing policy.

The next technical priority is attribution of the `.NET ThreadPool` SIG11 lines: process map, Home/CSFS service result, coredump list, and kernel context during the next blackout. The source itself does not support assigning those signals to this helper.

For the displayed Screen Optimization prompt, the safe next acquisition is a timestamped read-only correlation: capture the deviced/ELSensing logs, current `BurnInProtectionInProgress`, and the power-history record before accepting, cancelling, or timing out the prompt. That can establish whether a prompt transition writes an identifiable request reason, without modifying the panel, disabling safety paths, or guessing at an undocumented setting.
