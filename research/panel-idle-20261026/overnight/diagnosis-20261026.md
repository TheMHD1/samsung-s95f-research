# S95F blackout: low-level investigation, 2026-10-26

Later continuation: [backend-storage-and-onset-preparation.md](backend-storage-and-onset-preparation.md)
records the reviewed 44-byte live diagnosis-backend binding, corrected type-2
NVRAM getter route, and actual vlog/resource measurements. The combined onset
observer remains an unexecuted draft under correction. These findings do not
establish current physical emission or a permanent repair. The owner's latest
damage-size correction is **no larger than a thumb**.

Investigation batch: began at approximately 03:59 UTC; extended with offline hardware/HDMI/FRC analysis after 04:14 UTC, after the owner went to sleep. Device: QN77S95FAFXZC, T-RSMFAKUC-0090-REL-202607141953, Tizen 9, kernel 5.4.261. Boot ID remains `00000000-0000-4000-8000-000000000000`. No owner interaction is required by anything left running: all bounded tracing has stopped and private trace instances are removed. This is diagnosis, not a deployed repair.

## Owner's actual problem

The owner reports pre-existing impact damage: an irregular black spot no larger than the owner’s thumb (latest clarification) and a one-pixel-wide vertical line above it. Movies usually work, but the later account adds occasional one or two brief Ugoos picture losses with an audio pause, followed by recovery; Live TV is worse. Settings overlays on a full page can trigger repeated flicker. An empty-page blackout lasting roughly more than three seconds usually stays black; this is estimated timing, not a measured software threshold. Sparse For You/Live/Apps makes the picture disappear more readily; the original rich Apps catalog can keep it visible, including through a moving screensaver. A blackout can be brief or remain for many minutes while the TV remains on and audio/menu clicks continue. Navigating blindly back to Apps, restoring the populated Home, Settings/Home, compositor redraw and changing composition after black have failed to recover it. A standby/wake cycle followed by rapid navigation to full Apps has recovered it temporarily. The owner explicitly wants the mechanism traced and a repair, not a populated-menu workaround or a repair referral.

Latest explicit physical report: after power-on, For You appeared, then the physical picture went completely black while audio continued. The exact button/blackout time relative to the HWC experiment's 03:57:44 expiry is not recorded, so this is not labeled a proven fallback-prevention failure. The owner then reported going to sleep. Subsequent photo uploads and software captures do not establish the present physical picture state or observer availability.

## What the evidence establishes

**The Home renderer does not simply stop producing images.** In the earlier owner-confirmed black state, screenshots B0/B1 contain rich, changing Apps imagery, with about 380,417 changed pixels; HWC selected surfaces also advance. Screen state remains 1, DPMS is on, panel mute is zero, and the same boot/core processes remain alive. This places that failure after software composition/buffer selection. It does not distinguish DRM/FRC/private output state, TCON internals, and OLED emission electronics.

**A constant module reboot has not been demonstrated in this controlled incident.** Historical ERR_DET/reset events are real, but the captured TCON off/on sequences around these reproductions align with the owner's power-button cycles. The repeating `QD_TCON_OFF=1` message is a latched retry-history marker also seen while the picture was visible; it is not a new power-off command on every log line. Suppressing that message would not be a repair.

**Recovery and prevention remain separate.** A real runtime HWC fallback (`-hwc 0`, `deactive:1`) failed to recover the already-black picture. Normal HWC was restored with `-hwc 1`, verified `deactive:0`. A finite prevention experiment applied fallback before the requested owner wake; it remained active through 03:56:43 and expired/restored at 03:57:44. Owner timing is insufficient to classify the later For You blackout against this window. Fallback does not disable all video/scanout hardware planes.

## New low-level findings

### Kernel tracing is available, with concrete limits

`kernel-observability.json`, `trace-preflight.json`, and `early-trace-format.json` record the actual image. Tracefs is mounted at `/sys/kernel/debug/tracing`; only tracer `nop` is available. Function/function_graph tracing, kprobe_events, uprobe_events, /proc/kallsyms and /proc/config.gz are absent. A function-probe plan would therefore not run on this build.

Static tracepoints do work: I²C write/read/reply/result, DRM vblank, vendor `early_trace:early_event`, GPIO, clock, regulator, process exec/exit and raw syscalls. Vendor `early_event` contains a string field. Isolated trace instances avoid changing the global trace instance. This matches the distinction in the [Linux 5.4 ftrace documentation](https://www.kernel.org/doc/html/v5.4/trace/ftrace.html) between compiled tracers and static event tracing.

### Actual driver traffic was captured without issuing panel commands

A two-second isolated trace, `passive-black-i2c.trace`, retained **739/739 events**, SHA-256 `65d7a55533a9b20b99a43bdf59c77f2efda7159a7f35eea1847df3fabfb296f5`:

- AVEMonDIM thread 1013 / avocd TGID 706 issued 360 compat ioctl calls `0xc0086626` on fd 21 over about two seconds, consistent with three requests per 60-Hz interval. These all returned zero. This is activity, not emitted-light proof.
- One ioctl `0xc010749f` on fd 22 brackets the observed QDF exchange. `libave` Thumb symbol `ave_tcon_power_level(int*)` is at `0x25c9ad`, code starts `0x25c9ac`. It builds a 16-byte request with first word `0x21`, performs the ioctl, and returns the second word.
- `qdf_tcon.ko` `QDFTcon_GetPowerLevel` at `0xd088` sends command bytes `F3 00 00 00 01 74` with payload `00 00 00 01`, then reads `F3 80 00 00 00 0D`. The observed reply is `00 00 00 01`, raw power level 1.
- Surrounding `F3 01 00 00 00 00` transactions are command-status handshakes. The observed `00008104` and `00006904` replies are not decoded as fault/emission states.
- This exchange is a stock query, not a reset, mute, LPM change or power-off. A getter can itself involve I²C writes; “query” does not authorize synthesizing that transaction ourselves.

Trace fields print syscall arguments in hexadecimal: `15` means fd21 and `16` means fd22. The offline summary converts these explicitly. All bytes were copied to the host and SHA-verified.

A second five-second trace, `passive-black-output.trace`, retained **349/349 events**, SHA `4dd4266f63102314b86bcb1d17a3dedb8d22162a5cdd9d456527a107f0df3f6d`. It recorded **300 CRTC-1 vblanks**, the same query family, periodic GPIO272 input reads (not demonstrated panel power control), and vendor HDMI/micom watchdog messages. Physical emission during this exact later interval was not reconfirmed by the sleeping owner: this is a pipeline baseline, not fresh incident proof. No clock/regulator enable/disable event was observed in this short window. These tracepoints do not cover every proprietary TCON-internal action and cannot prove the state of OLED rails.

### FRC and cached firmware diagnostics expose another useful boundary

Static review of exact `sdp_frc.ko` read handlers preceded reading `frc/drvstatus`, `frc/drvinfo`, and `frc/inlog`. These expose cached status and logs; drvinfo additionally reads its known status register. No FRC debug command was written.

At uptime 9178.91 (`frc-cached-status.json`): init complete 1, driver ready/status 1, dormant 0, command filters 0, blocked external request 0, seamless freeze 0. Output is `FRC_OUT_UHD_QD_STD`, platform `RheaM_QD_V165T`. Internal log contains the Video60/0x210000 configuration around uptime8606–8613 and later pixel-shift updates. “BLACK PIXELSHIFT” is the literal routine label, not evidence that the whole picture is black. These later logs cannot establish the initiating For You frame or physical emission.

A bounded read of `tcon/tcon_micom_log` was justified by exact `sdp_tcon.ko` handler `0x61b0`: it copies a cached buffer under runtime-PM use, with no QDF/I²C send in that path. `tcon-firmware-log-prefix.txt` contains 1405 bytes, including firmware identifier F77ABU2D20, startup/output information and mailbox messages. It has no usable transition timestamps; no specific blackout fault was extracted from it. “Cold Boot” in that cached startup text is not proof of a new reboot during the blackout.

A narrow filename inventory found only default TCON dummy blobs under the searched firmware directories. The actual external QDF microcontroller firmware/algorithm has **not** been acquired or fully decoded. Host drivers and their commands do not expose every rule implemented inside that controller.

### Dimming, low-power and mute are separate command families

Exact driver analysis identifies separate QDF transport commands:

| Function | Command prefix | Proven interpretation |
| --- | --- | --- |
| Screen-saver brightness | `F3 00 00 00 00 C4` | Separate scalar/policy apply; zero is not calibrated zero light. |
| Factory Low Power Mode Level | `F3 00 00 00 01 40` | Passes payload 0..8; baseline factory value6. Value0 is not proven “disable”. |
| QD panel mute | `F3 00 00 00 01 64` | Real output gate, separate from power/reinit. |
| Power-level query | `…01 74` then read `…00 0D` | Stock query, observed raw result1. |

No mute/LPM/SS/power-off rewrite was observed in the sampled query sequence. That short observation does not exclude a command at the original blackout transition. The LPM command is applied through init/resume/factory paths; no content-selecting LPM change has been shown. Changing factory level0 would be guessing opaque panel policy, not a discovered fix.

QDDimming's `m_SetAPLFilter` (`0x17b191`) packages state into a backend virtual call; it does not calculate motion/staticness or an elapsed-time threshold itself. `m_SetScreenSaver` (`0x17b205`) has initialization/eligibility gates and delegates to a concrete QD backend. The QD screen-saver backend `DimmingBackendRoseMQDMNT::t_SetScreenSaver` (`0x1cb2d9`) uses factory UID0x5019 and caches changed requests. SetTconScreenSaver stores its input at state offset+0x520. No universal 30-second timer has been established; the owner's timing varies.

A deeper AVOC trace found a misleading control candidate: the only recovered PPI screen-saver call is at `avocd:0x7e540`, in a wrapper starting `0x7e4b8`, which always passes zero. A MOVW/MOVT function-pointer construction at `0xc9414` registers it with `KeyCombination_Add_Handler(ID0xbe)`. It is a key-combination callback, not a proven Home policy setter or public D-Bus method. No unknown key combination was sent. The dynamic content/dimming trigger remains unresolved.

## Kernel image recovered for offline machine-code analysis

The actual paired uImage partitions were inspected read-only. The named uImage symlink points to p5, whose first128KiB are zero; p6 contains a valid legacy header and an uncompressed ARM64 Image. The current root is p19, consistent with that pair. `kernel-uImage.bin` is11,786,816 bytes including header; header and payload CRCs both verify. Payload SHA256 is `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`; banner Linux5.4.261, built July1,2026. This matches kernel version, but a running-text hash was not acquired. Nothing was flashed, mounted or patched.

Automatic full-symbol reconstruction using vmlinux-to-elf1.0 failed: no embedded kallsyms token table was found. The export table is still present. PREL32 entries recover built-in Samsung runtime-use functions: tryuse fileoffset0x3fbc58, disuse0x3fbbe8, getdev0x3fbee8. The contiguous9,379-record export index and raw machine-code disassembly are saved as `kernel-export-index.json` and `kernel-runtime-pm.disasm`. These are raw file offsets, not runtime virtual addresses. A host-only `kernel-export-view.elf` adds recovered export labels at artificial base0 without modifying payload bytes; its limitations/hash and reproducer are preserved. It is not a replacement kernel. [The exact built-in implementation is now traced](kernel-runtime-pm-findings.md): it maintains a proprietary per-device busy count, with roughly10-second bounded suspend wait. This is distinct from standard Linux runtime-PM and has not been tied to the blackout. No embedded IKCFG markers were found.

## Extended hardware, HDMI and FRC findings

The detailed [hardware/HDMI evidence map](hardware-hdmi-evidence.md) preserves the actual device-tree GPIO mappings, manufacturer board photographs, exact getter limitations, native-link observations, and a separate plan for the uncaptured Ugoos/JBL AV pause. The S95F-family guide shows TV Main, T-con and a 77-inch DCDC board in the panel, plus OC Main/SMPS in One Connect; it is not an exact-unit schematic or connector pinout. No physical work was done.

The GPIO272 input polls in the trace are unrelated to the mapped TCON controls. Several apparent fault getters request/direction/read/free GPIOs, so no new private fault getter was invoked. Native visible and black samples retain the same One Connect clock/cable status and sampled VX1 lock; this narrows that occurrence without proving panel emission.

The HDMI `crc` debugfs getter was read once before exact disassembly revealed a successful-runtime-use/native-source EINVAL branch lacking paired disuse. It must not be repeated or manually balanced. The recovered kernel proves a proprietary busy-count mechanism, but the live count/global bypass state is unknown and EINVAL also covers failed tryuse; no exact retained count can be inferred. This is a diagnostic limitation/possible driver defect, not an explanation for blackouts that predate the read. Other apparent HDMI blink getters are stubs and cannot provide valid counters. Native source lock0/TX0 is expected, not HDMI fault evidence.

[The FRC output-policy analysis](../tcon-research/overnight-frc-output-policy.md) separates explicit dormant/freeze/low-power controls from frame content. Its later cached ready1/dormant0/freeze0 sample shows none of those state changes; it does not exclude an unobserved initiating transient. No sparse-image timer has been recovered. [The Home mute-chain analysis](../idle-research/overnight-mute-output-chain.md) records the finite RetryMuteAV loop and the remaining managed/native bridge rather than equating three retries with three seconds.

## Concrete AVOC readback gap recovered from machine code

The exact AVOC controller now explains why its zero getters cannot be treated as electrical unmute proof. `GetPanelMute` reads controller global0x179434 byte+0 (force-mute intent); `GetPanelMuteCaseStatus` reads byte+8 (BLACK-case flag). Neither exposes the FREEZE flag at+9.

`avocd_ave_set_panel_mute` wrapper0xac2c8 forwards input bit0 and second argument0 into PPI at0xac2f6→PLT0x1c448. It normalizes a lower failure to-1. However, SetForceMute0xb13b4 stores the controller flags **before** the PPI call and discards its return. Reset0xb152c calls unmute at0xb1550 and clears BLACK at0xb157a regardless of that call’s success. This was independently checked from the matching ARM Thumb code. The controller can therefore report logical zero even if a downstream unmute failed. This is an observability gap and a testable candidate, not proof that it caused this blackout.

The AVE implementation reaches distinct FRC/TCON mute interfaces, so this path is materially different from a compositor redraw. `trace-avocd-panel-mute.py` fingerprints the binary, reconstructs PPI PLT/call sites and regenerates the preserved disassembly windows/index. Windows may contain literal pools; only verified instructions/call paths are interpreted. The lower AVE/QDF gate has now been traced in [the QD mute-gate report](../tcon-research/overnight-panel-mute-gates.md). Public unmute sends TCON ioctl0xc004748c through TCON_SetMute to QDF. Even cached QDF mute0 performs a live read of F3 80…0164, and a nonzero reply re-sends mute-zero. This gives a specific single-zero reassertion candidate; it is not a power reset or protection bypass. [The native controller audit](../idle-research/overnight-avocd-controller.md) recovers four direct ResetBlack callers, including SetNewHome at0xc174a inside callback0xc1524. Its third native argument also flows to the NewHome PPI state setter. The callback table uses `{name,callback}` pairs, proven by the registration loop0x7b79a..7b7c4. A temporarily proposed alternative mapping used pairs shifted four bytes and was rejected before any control test. No mute setter or forced recovery was sent in this batch.

## Historical ERR DET0x10 is now decoded

Exact AVE code identifies QD error-status bit4 as **RT Protect**. It is returned by QDF/TCON transaction F3 80 00 00 00 08, separate from the one-bit fault GPIO. The raw QDF logger precedes optional debug override; the retained historical event has the raw0x10 line, not an injected debug line. The AVE monitor's classification and subsequent power-control(2) path are also recovered. [The detailed decode](historical-errdet-decode.md) preserves all masks, addresses, transport and limits. No RT expansion or failing component is inferred. No fresh RT-Protect event has been aligned to the current menu-black onset, so this historical recovery path must not be assigned as its cause.

## Rejected diagnostic: output CRC would change the display

Static recovery found exact QPI ABI commands in `sdp_drm.ko`, but none was executed:

- GET_POST `0xC2E06498` writes 1 to DP register0x7A02CA4 even for count0 and has no matching standalone disable.
- READY_OUT `0xC0046495` snapshots some registers but also forces scaler filter0 across IDs0..11; the release path does not restore prior filter selections.
- GET_OUT `0xC2E06492` uses a nonblocking ISR-fed queue and can return EPIPE without the missing stock orchestration.

The 736-byte payload has count<=30, three further header words, then six u32[30] CRC lanes at offsets16/136/256/376/496/616. POST lanes map to CRC1_R/G/B then CRC2_R/G/B. The compat ioctl passes through fixed-width fields unchanged. Knowing the ABI does not make these observational. A test-pattern wrapper in libave uses a different invasive ioctl and is not a safe getter lifecycle.

## What was prepared and verified for the next session

`diagnostic-trace.py` defaults to dry-run and accepts an explicit `--run` only for a bounded 5–45-second static-event capture. It uses a unique private instance, exact-build guard, filtered bus5/address118, no raw driver calls, an on-TV setsid expiry, shell trap and host finally cleanup. It saves bytes before analysis, validates SHA and rejects ring overflow rather than silently accepting an incomplete transition. It leaves bounded trace/expiry artifacts under the existing TV tmp directory; these are diagnostic files, not boot services.

The capture body completed a 5-second live validation: `helper-validation.trace`, **324/324 events**, 300 CRTC-1 vblanks, SHA `851cd4c2c9f8367339b49c2902df1e30c1fbf4ce080367fecfdc601a7396ed09`. Cleanup JSON shows global tracing0 and the private instance absent. The final helper revision subsequently tightened expiry timing, overflow validation and exception-preserving cleanup; these were syntax/review checked, and the detached-expiry mechanism was tested separately. The exact final helper revision was not rerun end-to-end on the TV. A separate no-display-action test deliberately timed out its parent shell after1second; the detached setsid expiry still wrote its completion marker after3seconds (`detached-expiry-timeout.json`, `final-state.json`). This demonstrates that cleanup process survival for this transport; it does not guarantee recovery from a TV OS crash or lost power.

Two initial trace attempts failed before enabling tracing because the root transport doubles backslashes used in printf escapes. Echo-to-control-files avoided this; failed attempts and corrected scripts are retained. No panel setting was affected. Existing backslash-dependent helper text must not be assumed to execute byte-for-byte through this transport without checking.

### Next owner-assisted comparison

1. Recover picture by the already observed ordinary standby/wake procedure, then leave full Apps visibly stable. Capture25seconds as the control; do not mix new factory or HWC changes.
2. Start the same25-second capture, make exactly one transition to sparse For You, and immediately record the physical “black now” time. Hold that page. Avoid Live/video for this first comparison because its video plane/source reconfiguration is a confound.
3. Compare I²C command order/payloads, vendor events and timing against the control. A unique mute/LPM/SS/power command at the physical edge would identify a software path to investigate. Absence narrows the boundary but does not prove hardware failure.
4. While already black, launch known moving video once, without standby, and report whether picture recovers. This tests source/FRC reconfiguration as a recovery path separately from preventing entry.
5. Only if still useful, repeat a controlled normal-versus-HWC-fallback crossover with the same sparse page and fixed observation period, checking `deactive` after wake. Do not make a runtime policy permanent based on one success.

Example command (prepare timing with owner before running):

```bash
python3 ${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/diagnostic-trace.py apps-control-next --seconds 25 --run
```

`analysis-input-manifest.json` fingerprints the current matching analysis binaries; matching-driver manifests record original TV paths and verified copies, including the HDMI modules. Exact offsets and detailed evidence are in `../tcon-research/overnight-*.md`, `../idle-research/overnight-ave-hwc-findings.md`, raw trace summaries and this directory's JSON captures.

## Prepared single-zero recovery capture

[The next observed-session protocol](next-observed-session.md) and `unmute-zero-capture.py` make the code-grounded gate test concrete. This separate helper reuses the native trace’s dry-run template, verifies logical baseline0/0, and places exactly one public unmute-zero request inside the same finite root shell. It does not request mute-one, factory changes, power, or a retry. Failed D-Bus reply still preserves the trace. Root serialization is respected; no concurrent second root command is required. Shell syntax/Python compilation and five API-reply classification fixtures passed; the combined probe has not run on the TV. Probe-log and trace transfers both verify size/SHA; cleanup checks transport/exit/timeouts and actual private-instance absence, recording an explicit error artifact on failure. A cleanup failure exits nonzero when there is no earlier exception; an earlier failure is preserved. Independent review of the prepared path completed, with these findings corrected. Public acceptance remains separate from lower I/O or physical recovery. A physical observer is required to determine recovery, and the helper flag does not measure that.

## Final state and unresolved diagnosis

At04:45:57UTC the newer `kernel-running-baseline.json` confirms the same baseline as04:14:10: same OS boot, normal HWC `deactive:0`, AVOC panel mute0/return0, global tracing0, no private trace instance. Physical panel state during these later reads was not confirmed. No factory option, calibration, EEPROM, panel rail, TCON firmware, bootloader, or service restart was changed during this sleeping-owner batch. Root remains host-assisted.

The best-supported diagnosis is **loss of visible output downstream of valid software composition, with the initiating command or internal emission state not yet identified**. A software/FRC/TCON policy interaction and damaged-panel electronics remain live hypotheses. No kernel patch, protection bypass, or permanent repair has been justified or deployed. The next step is an actual transition capture, not repeating black-state recovery setters.

## Further Home-to-output audit, after05:18UTC

The exact callback registration loop confirms the original native mapping: SetNewHome is0xc1524 and reaches ResetBlack at0xc174a when its input is nonzero. A four-byte-misaligned interpretation of the callback table briefly suggested a different identity; the actual loop passes table word0 as name and word1 as callback, proving that interpretation false. This was corrected before any live control. The [UI/native-argument report](../idle-research/newhome-ui-native-arguments.md) preserves the bridge evidence. Matching `Tizen.TV.System.dll`/native-image were copied from `/usr/share/dotnet.tizen/framework/`, with size/SHA checks and a separate manifest; the namespace is Avoc, but there is no separate Avoc-named assembly in the searched paths.

[The exact QD dimming vtable](../tcon-research/newhome-qd-dimming-policy.md) resolves NewHome's previously opaque virtual call to a base no-op query stub. It does not change QD SS/APL/mute/power through that edge. Independently, QDMNT's screen-saver backend can send the known00c0/c4/cc/d0 family from vblank policy; its APL-filter slot is a no-op on that backend. Neither function establishes a sparse-content timer.

[The separate FRC path](../tcon-research/newhome-frc-output-policy.md) is now traced from libave's ioctl0xc00866ff payload `{selector3,enter}` through FRC_Request slot+680 to RosemFrc_SetNewhomeMode. Entering Home can disable low-input-lag policy, select50/60Hz source-rate policy, clear VRR maximum, and request120Hz TCON rate through a distinct backend callback. Input-rate policy must not be mistaken for physical panel rate. Exiting marks a deferred-exit flag. The cached output-rate value is stored even if its backend fails or is absent, so it is not an electrical-health readback. Existing paired snapshots retained no matching NewHome/rate lines; a fresh transition is still needed for causal correlation.

[The historical retry loop](../tcon-research/historical-fault-recovery-timing.md) samples fault GPIO three times with two explicit100ms sleeps before a terminal decision (~200ms plus I/O). It is not a demonstrated three-second timer. Recovery operation2 invokes off then on in the QDF wrapper; repeated QD_TCON_OFF lines only report its latched history. This does not align that old fault with the current menu event. No live display setter, standby/wake, factory control or protection/kernel patch was issued in this further audit.

[The outer monitor task](../tcon-research/monitor-task-cadence.md) has a configured one-second absolute condition timeout. Actual scheduling can wake early or run late. Earlier visible-control logs independently show approximately one-second latched-status reporting; neither establishes fault timing at the current blackout edge. The monitor on/off function changes enable/restart flags, and does not itself clear the fault-history latch.

Independent review of the separate [QD timing backend](../tcon-research/newhome-tcon-vfreq-backend.md) found a material correction: QDFTcon_SetVRRFrameRate converts the raw rate to a frame mode; it does not send that rate as0x15c payload. Its nested frame-mode programming can use the F3:0x164 output gate around F3:0x160 mode writes. This removes the earlier blanket exclusion of output gating from the downstream timing path. Exact error-exit review shows all returning bracketed branches attempt unmute0. However the temporary pair does not update m_mute_state, final unmute failure is discarded by higher wrappers, and requested mode/rate are cached before successful completion. These are concrete ways cached0/success can disagree with the actual gate and identical retry can be suppressed. No aligned failure or causal proof is claimed. No forced timing or new recovery operation was sent.

### Specific new gate-mismatch hypothesis, still untested

The verified chain now is `CSFS global NewHome1 → AVOC ResetBlack/PPI → FRC selector3 → Rosem requested output rate → QDF derived frame mode → temporary mute1 → mode0x160 programming → attempted mute0`. The frame-mode bracket is the **same** F3:0x164 gate as the public mute route. It can leave ordinary cached mute0 untouched throughout. All normal returning paths attempt the final0; no omitted-cleanup branch was found. A final transport/acceptance failure could still be hidden and its retry suppressed by prewritten mode/rate caches. This is a mechanism supported by code, not an observation of the owner’s physical event. It does not yet explain why two Home tabs or content densities differ.

[Independent review and corrections](home-output-independent-review.md) preserves rejected interpretations and verified branch details. New reproductions are offline only (`trace-newhome-frc.py`, `../tcon-research/newhome-tcon-vfreq-reproduce.py`, and the managed metadata probe). Fresh live interaction in this pass was restricted to read-only file discovery/acquisition and a root-access echo. No panel test or new setter ran. The prepared one-zero public unmute capture remains the bounded next recovery discriminator if the owner confirms physical black; its outcome is not inferred from photographs or software flags.

### Further transport audit: final zero can be a successful no-op

The exact [command helper](../tcon-research/qd-command-transport-failure.md) has a narrower failure mode than a missing cleanup branch: for command `0xf30000000164`, payload0 and cached `m_panel_dpms_pvcc_status` at BSS+0x194 equal0, it returns0 **without I2C or mutex acquisition**. The temporary frame-mode final unmute and public setter's zero re-send both use this helper. Thus an attempted cleanup need not be emitted, even without a reported transport error. The [concurrency audit](../tcon-research/qd-mute-concurrency.md) also shows the overall temporary bracket is not atomic: the same mutex protects individual eligible commands and the middle mode region, with gaps between them. Neither finding proves the condition or interleaving occurred during an observed blackout.

The [guard lifecycle report](../tcon-research/qd-unmute-pvcc-guard.md) identifies initialization to1, the explicit flag setter, the API-table wiring, and normal DPMS/power callback routes. Calling that setter with1 can initiate TCON power-on; it was not used as a diagnostic. No live flag value has been established. The [finite mute-writer map](../tcon-research/qd-mute-writer-map.md) distinguishes normal setter, init/resume and temporary mode writers; cache updates can occur after unsuccessful attempts. Its scope is explicit immediate command construction in this copied module, not all firmware/hardware writers.

An [offline decoder](qd-trace-decoder.md) now retains per-thread I2C transfer boundaries, raw bytes/results and capture-integrity failures. Fourteen integrity tests pass. The retained two short post-onset samples each have four complete transfers and no focused mute/frame/VRR command; neither captures the initiating edge. Driver `F3:01` checks do not justify calling the entire raw reply a panel health or MCU success code. No TV action occurred in this offline audit batch.

The two damage close-ups were viewed again and documented in the [photo map](../tcon-research/owner-photo-board-map.md). They show the local lower-edge patch and upward dark line. Thumb-size is the owner's reported scale; exact centimetres and one-pixel width cannot be measured from these photographs. Local visible extent alone does not identify the whole-screen failure mechanism. No permanent repair, panel-damage reversal or untethered root has been verified.

[The transport independent review](qd-transport-independent-review.md) records corrections to handshake byte selection, broader return-zero/no-transport gates, Resume ordering, and fail-closed decoder handling. These corrections were applied before a live control test.

### Gate lifecycles and evidence that limits the hypothesis

The [command-skip lifecycle](../tcon-research/qd-command-skip-lifecycle.md) identifies EL/off-sensing start paths that enable suppression of most driver reads/writes, and completion/stop/Resume paths that clear it. The [suspend/state audit](../tcon-research/qd-suspend-state-lifecycle.md) maps separate suspend and TCON-state gates, including state0 after actual power-off or selected communication failures. These are mechanisms, not evidence that maintenance caused the empty-menu event. Availability1 and elapsed sensing timers are not active-maintenance proof.

[Runtime evidence constraints](qd-gate-evidence-constraints.md) add a useful counterweight: the retained stock0x174/0x0d power-query wire exchange must, on its attributed QDF path, pass suspend/command-skip/state gates at the corresponding checks. That weighs against continuous assertion of those broader gates during that exchange. It does not constrain the special PVCC mute-zero guard, earlier transients, current values, or physical emission. The saved stdout scan finds older state0 skip messages near power/wake transitions, not the initiating visibleApps→black event.

At05:57:28UTC the read-only snapshot shows the same kernel boot, normal HWC and no active private tracing; no current physical report was obtained. Metadata discovery confirms QDF loaded, but kernel memory-read interfaces and module-section addresses are unavailable, so no direct cached-word value was read. No pointer policy, module, memory interface, panel setting or power state was changed.

### Controller-image acquisition and service bridge progress

The official exact-model Samsung support listing identifies USB archive
`T-RSMFAKUC-0090_TB-RSWF4AKUC-0090.zip`, version0090-1301.0, datedSeptember8,2026.
Bounded HTTP range reads retrieved ZIP/ZIP64 directory metadata, CRC-verified
information files and a65494-byte decompressed prefix of the mainMSD container,
without downloading the full2.44GB archive. Its main info identifies version1301.0
and build2026-07-14, matching the running family/date but not proving identical
binaries. The [firmware acquisition map](../tcon-research/qd-firmware-acquisition-map.md)
records the MSDU11/model/Salted__ literals and the exact boundary: no decoded
partition directory, decryption method, full-image signature validation or
F77 controller payload was recovered. No update API was called.

The matching display-panel facade and its two backend files were copied
read-only and verified by remote/local size/SHA. The
[sensing ABI report](../tcon-research/qd-sensing-entry-callers.md) distinguishes
that service dispatch from the separately proved AVE ioctl9/15→QDF callbacks;
no runtime call is inferred from a symbol alone. The decoder now labels the
exact sensing-control commands0x180/0x1a0 in a separate maintenance list, with
fourteen integrity fixtures passing. The retained post-onset samples contain
neither command. No physical recovery or prevention was tested in this batch.

The bounded service bridge is now statically closed: `deviced` imports →
display-panel facade slots2c/30 → matching impl-sec callbacks →
DisplayPanelImplSec sensing methods → imported AVE setters → the previously
proved ioctl/QDF chain. Table population and linked imports are code evidence;
a live table-pointer value and an onset-aligned invocation are still absent.
The two backend files were also acquired by ordinary read-only file copy with
remote/local size and SHA verification.

## Daemon and content-policy audit, completed around07:00UTC

The new [off-sensing policy](../tcon-research/deviced-off-sensing-policy.md)
maps both structured power-suspend routes and an actual GDBus-facing request
handler. The latter can select ordinary user or tester paths. Support and an
encoded product-year option select legacy versusY23 objects. The exact PLT
targets resolve to PPI TCON power and off-sensing setters, and the virtual
tables identify the corresponding software actions. No Home/ForYou/Live IPC
client or incident-aligned maintenance request was identified.

The [EL policy](../tcon-research/deviced-el-sensing-policy.md) separates
persisted user-request bookkeeping from the actual guarded start: it calls
`turnOn` then `startELSensing`, checks the latter's result, then changes local
state and requests a background-standby lock. Stop paths can request EL-disable.
The constant0xdbba0 belongs to that lock call, **not a proved fifteen-minute
maintenance timer**. Neither the owner's60-second prompt nor its claimed
ten-minute cycle is implemented/identified by these recovered bodies.

The [content/duty audit](../tcon-research/qd-content-duty-policy.md) identifies
another distinct host request: QDMNT final duty reaches full packet
`F3 00 00 00 01 28`. The function named `m_AutoPowerOff` performs an
arithmetic brightness ramp with a300-invocation counter; it does not directly
switch panel power off. Its QDMNT caller clamps the desired scalar to12 or51
minimum,1023 maximum. Those numbers are not measured emission/current or a
guaranteed safe operating range for the damaged panel. No content threshold
or timer causing the persistent blackout has been established.

Further requested-versus-applied gaps are now concrete: final-duty, backend
SS-brightness, QDF SS-brightness and daemon TCON-state caches can advance
despite a failed or suppressed lower request. Identical retries can then be
skipped. This extends the prior mute/mode-cache hypothesis; no aligned cache
failure or recovery was observed, and no cache was patched or forced.

The decoder now labels0x128 and exports a separate `dimming_focus` in addition
to mute/frame and maintenance lists. Sixteen fixtures pass. Both retained
post-onset traces still contain four complete query/status transfers, with
all three focus lists empty. The existing visible/black log extract
`paired-content-duty-log-extract.json` preserves APL/Lamp0 in both physical
states and SS0/7 request history without relabeling those as light measurements.

[Independent review](policy-independent-review.md) rejected incorrect symbol,
vtable, timer and absent-caller interpretations before these conclusions were
integrated. Final reproducers fingerprint the copied binaries and exclude
literal pools. Both damage closeups were viewed again; the thumb-size scale
remains owner-reported. This entire pass was offline: no new TV command,
remote key, power/factory/firmware change, patch or panel test ran. Current
physical state is unknown; the prepared single-zero observed recovery test
remains unexecuted. The diagnosis is still unresolved and the goal unfinished.

## October26: checked request/timer contracts and first userspace memory sample

The [power-state contract](../tcon-research/deviced-power-state-contract.md)
now resolves the daemon's exact table:1=`lcdon`,2=`lcdoff`,3=`standby`.
The public `GetPowerState` method record points to the same table-backed
name getter. EL-start's comparison against3 therefore requires standby;
integer `GetScreenState`1 is a separate value. The11:09:57 read-only sample
returned `lcdon`, but has no physical-state confirmation and does not
reconstruct the blackout edge.

The EL lock's0xdbba0 argument reaches GLib unchanged: a nominal900,000ms /
15-minute background-lock expiry. The
[expiry route](../tcon-research/pm-lock-expiry-notifier.md) sends notifier20
then defers PM unlocking; for known legacy/Y23 sensing objects in state2,
the notifier can request EL-disable0. This is a timeout/stop capability,
not identification of the popup's60-second response or ten-minute cycle.
The [IPC client audit](../tcon-research/maintenance-ipc-client.md) separates
request-flag storage from power-off handling and guarded EL-start. Reason
0x4000002a is not unique to a stored user request: a passed-run-cycle path
can produce it too, and power-off type6 excludes consumption on the audited
path. No maintenance control was invoked for this pass.

The [upstream AutoDim audit](../tcon-research/qd-autodim-upstream.md) resolves
the PPI/native forwarding route and provider registration. Client/provider
both use slot+0x98; HomeUI is a distinct QD base stub, not a recovered
Full-Apps-to-AutoDim rule. Independent review rejected draft claims of an
ABI mismatch and an invalid EL interface literal; neither is retained as a
diagnostic hypothesis. Curated excerpts and generated raw output are labelled
separately, and automated-check coverage limits remain recorded in the
[independent review](upstream-contract-independent-review.md).

The first bounded [userspace memory baseline](runtime-dimming-baseline.md)
at11:28:59 directly found active `QDDimming` (not its distinct MNT vtable),
initialized byte1, and stored AutoDim word0. Forty bytes were read from
avocd's process memory. GOT/global/header values matched before and after
over approximately20ms; the two fields were each read once, and the mapping
snapshot was about130seconds earlier. This is a non-atomic, physically
unobserved sample using the previously fingerprinted library's offsets.
It does not establish field history, blackout cause, normal emission or
recovery. The initial `od` reader failed; finite `dd` reads then succeeded,
with both attempts preserved. No tracing, ptrace attachment, process stop,
injection, memory write, setter, remote key or power operation was used.

This adds a practical read-only discriminator for an owner-confirmed paired
transition. The [next-session protocol](next-observed-session.md) now includes
fresh-map/pointer validation and this raw field alongside maintenance/power
state and the existing finite I2C trace. Both thumb-size damage photos were
inspected again; their local patch/line does not time or explain whole-panel
output loss. No permanent blackout repair or untethered root is verified.

## October26: actual RoseMQD backend/cache and daemon-state reads

The [new runtime control report](runtime-control-state.md) closes the previously
unknown backend: the active QDDimming object's nullable output interface is
**DimmingBackendRoseMQD**, not MNT. The combined11:53:06 capture directly reads
its relocated function slot, duty cache and working-duty fields, with fresh
source-file hash/maps and matching paired identity/cache/duty reads. It finds
cache207 and working duty207, rawAutoDim0, and early vsync guards in a pass
configuration. This108-byte non-atomic sample has no physical-state observation
and proves neither callback dispatch nor a failed transport.

The [actual base-path audit](../tcon-research/qd-active-base-duty-path.md)
identifies a concrete retry weakness on this runtime-selected route:
RoseMQD records its candidate before both output calls, has no cache rollback
on errors, and the vsync caller ignores the combined result. An unchanged
candidate can therefore suppress a retry after a reported failure. Equal
cache/working values are also normal steady state; the new sample does not
show that any failure occurred or that a retry was needed. No cache or field
was modified and no forced brightness request was sent.

A separate120-byte daemon sample at11:45:01 resolves legacy EL/off objects,
validates OledDevice/Timer/PowerAdapter child vptrs, and finds local states0
and power index1=`lcdon`. Public getters afterward returnlcdon/BurnIn0.
Fresh maps and bracketed fields match. This is local state-machine evidence,
not electrical emission, timer/request-key state, or an explanation of the
earlier menu blackouts.

The [manual Pixel Refresh UI](../idle-research/menu-screen-optimization.md)
is now traced through an exact hash-guarded five-method IL probe and managed
P/Invoke bridge. Start now passes native mode0; Start after off passes1 and
adds a toast. Its displayed duration text30/60 differs from the owner's
automatic60-second-response/ten-minute popup, whose implementation is still
unidentified. Read-only source acquisition, failed helper-command attempts,
and the remaining SelfDiagnosis resource candidate are preserved in the
discovery JSONs; none is an app installation or UI launch.

[Independent review](runtime-control-independent-review.md) corrected selector
provenance and conditional backend-call descriptions, verified the final IL
output and runtime arithmetic, and retained the physical-state and
non-atomicity limits. The next paired transition can now correlate these
internal fields with actual wire traffic and the owner's physical report.
No kernel/factory/protection patch, persistent-root install or panel recovery
was deployed or verified in this pass. The original repair objective remains
unfinished.


## October26: thumb-size photo clarification and remaining popup lead

The latest photo review preserves the owner's **no larger than a thumb**
clarification, the lower-edge local patch and upward dark line. All10 uploaded
source-photo hashes and byte lengths were rechecked successfully. The visible
patch's size does not establish the extent of an electrical fault or explain
why the whole panel latches black on a sparse Home page.

The [Self Diagnosis follow-up](../idle-research/selfdiagnosis-optimization-candidate.md)
now inspects four additional copied/hash-checked files. Its installed XML and
resource assembly contain Pixel Refresh and Screen optimization labels. A
reproducible bounded string/XML scan does not identify the owner's automatic
60-second/ten-minute popup; it is not a global caller exclusion. The manual
menu's already verified maintenance path remains distinct. No new recovery
control, output forcing, reboot, factory change or firmware patch was deployed
in this follow-up. Physical picture state and a permanent fix remain unverified.


## October26: monitor latch/counters read and clear condition resolved

The [new runtime monitor baseline](runtime-monitor-baseline.md) reads356bytes
across five identity/map/hash-checked stages, with20 matching final pairs.
At12:22:42 UTC (uptime38971.66..38971.83), the active QDDimming/RoseMQD path
still has cache207, working207/207 and AutoDim0. ERR/VDD/ELVDD fault counters
are0/0/0, recovery counters2/0/0, `qd_tcon_off`1, restart/on0/1 and remembered
on1. **Physical picture state was unobserved**; this is neither a visible
control nor a new blackout/recovery result. Fault counters have clear paths,
and latch1 makes a monitor invocation skip its normal hardware checks, so
zero counts cannot exclude a present or earlier electrical fault.

The [exact map/reproducer](../tcon-research/qd-monitor-runtime-map.md) now
resolves the formerly opaque bookkeeping-clear gate as
`g_tcon_monitor_restart == 1`, using its actual GOT relocation. That branch
clears counters/latch and the restart flag; the on/off helper sets restart
when its input differs from remembered previous state. This is a conditional
host-state reset, not proof of panel power-on or recovery. No flag was changed.

A default-dry repeatable reader now refuses fallback root staging, derives
fresh mappings/pointers/types/slot, preserves all raw reads and rejects bad or
changing samples. Independent review decoded every retained block and
confirmed all356bytes/20pairs. Seven reader integrity tests and18 combined
wrapper routing/identity tests pass offline. The [cache lifecycle follow-up](../tcon-research/qd-rosem-cache-lifecycle.md)
keeps cache-after-error retry suppression bounded and finds no known cache
rearm in the examined ctor/dtor/config/init/resume methods; it does not prove
a global writer census or safe standby-based reset. Root remains host-assisted;
no output forcing, recovery loop, binary/kernel/factory patch or permanent
blackout repair has been deployed or verified.


## October26: startup rearm and kernel-observer access boundary

The [monitor lifecycle trace](../tcon-research/qd-monitor-lifecycle-callers.md)
now proves positive GOT stores in normal `ave_tcon_monitor_start`: it writes1
through the exact monitor-on and restart globals. This requests bookkeeping
rearm if the QD routine later runs; it does not itself prove physical power,
recovery, standby/wake reachability, or a safe externally callable repair.
The positive startup stores are separate from any complete caller inventory;
the audit's decoding/coverage limits are preserved in its report. No monitor
control ran.

A [fresh kernel feature read](kernel-observer-features-20261026T123326Z.json)
retains absent/unreadable config/BTF/module-section/policy surfaces and an
explicit missing `/proc/kallsyms` error. Static syscall/scheduler/I2C event
names remain available. The [exact-image audit](kernel-bpf-presence.md)
distinguishes classic socket-filter paths, a normal zero-return BPF call-base
anchor and an unsupported event-output hook. These do not globally prove
eBPF/perf configuration or rule out another output/helper path. Linux5.4
primary-source research constrains the proposed observer but does not reveal
live private QDF suspend/skip/state/PVCC words.

One [native userspace syscall-availability attempt](kernel-abi-probe/README.md)
used invalid, non-creating BPF/perf requests in a reviewed592-byte static
helper. The TV refused to execute the helper with Operation not permitted;
helper exit1,0result bytes and accepted=false are preserved. It supplies no
syscall or private-state result. Its private temporary helper/result directory
was removed and checked absent. A later bounded dmesg tail did not identify
the denial cause. No policy change, alternate execution retry, BPF program/map,
perf event, tracing attachment, kernel patch or panel control was performed.
Physical picture state remains unobserved, and the blackout repair remains
unfinished.

## October26: lifecycle caller coverage and vendor debug-input correction

The finalized [lifecycle caller audit](../tcon-research/qd-monitor-lifecycle-callers.md)
partitions all2,343,452 `.text` bytes using the library's ARM/Thumb/data
mapping symbols, with no undecodable code bytes. This replaces an invalid
early linear-Thumb search that stopped after8,248bytes; no caller-absence
conclusion from that early search is retained. The recovered public Start
chain reaches the direct enable/restart stores. The public Instant On chain
requires a non-null object lookup, then normalizes its input to0/1 and calls
the monitor on/off helper. This is a complete direct-call inventory inside
the matching library, not a global indirect/external caller census, a known
standby/wake route, or physical recovery. Independent review requested and
the author added exact argument-save/convergence assertions before final PASS.

The [QDF cache-print audit](../tcon-research/qd-cache-dump-surface.md) found
the desired suspend/state/PVCC/skip labels in an internal debug callback.
An initial assessment treated its flash/setter dispatcher branches as
reachable. Exact helper disassembly corrects that assessment: both local
numeric-input helpers return constant0x99, the debug exit selector. The
normal matching-code path therefore skips the command table and returns
after its menu/default logging path. Independent review additionally found
that the named cache values are printed only in the dormant selector0x30
branch, not before the input helper. Thus the unchanged normal path cannot
provide these values either. The existence of mutating or cache-print branch
bodies alone is not proof that an ordinary call can reach them. No debug
callback, ioctl, input-helper modification or selector has been invoked for
this investigation. The identified callback is not the missing gate observer.
The ordinary PVCC status at BSS+0x40 remains distinct from the special
panel-DPMS unmute guard at+0x194.

Both latest screen closeups were viewed again. The visible lower-edge patch
is **no larger than the owner's thumb**, per the owner's clarification; the
upward dark line is also visible. The photographs contain no calibrated
scale or independent exact pixel-width measurement. They do not establish
the electrical extent of damage, explain a content-dependent whole-panel
blackout, or confirm the present physical state. No new recovery, reboot,
factory/protection/firmware change or permanent repair is verified.

## October26: automatic warning identified and its expiry action traced

The [exact installed resource match](../idle-research/tv-viewer-optimization-resource-match.md)
now locates the owner's ten-minute Screen Optimization wording in native
`tv-viewer` and its US/GB gettext catalogs. The [native notification trace](../idle-research/tv-viewer-automatic-sensing-notification.md)
and [expiry follow-up](../idle-research/tv-viewer-off-sensing-timeout-flow.md)
recover the forced/reinforced notification ID0x0f. Its ongoing notification
has a local alarm configured with1000/60, a counter increment and remaining
60-counter display. At callback60 it automatically calls the off-sensing
request wrapper. Start Now calls that wrapper separately; close/hide/timeout
events delivered earlier take a cancellation/timer-destruction path. The
intended one-minute mechanism is now code-backed, not inferred solely from
the owner's timing or text. Actual elapsed wall time and which callback ran
in the owner's instance remain unobserved.

The wrapper calls `libdeviced`'s no-argument off-sensing API, which supplies
mode0 to `RequestOffSensing`. The service reply is tested for zero/nonzero;
the local UI wrapper returns void after logging/accounting. This is the
short off-sensing request route, separate from the earlier manual EL/Pixel
Refresh trace. The [producer follow-up](../tcon-research/app-control-off-sensing-producer.md)
maps numeric QD states1/2 to normal/force presentation messages and resolves
a separate reinforce-timer route. Message text, popup expiry and eventual
physical power/sensing success remain distinct facts. No popup was launched,
expired deliberately, clicked or cancelled by this investigation pass.

The source search inspected326 direct main assemblies,666 direct non-DLL
application files and1162 direct system executables with the recorded
patterns; these are bounded glob scopes, not firmware-wide absence proofs.
Nine additional files were acquired with before/after source SHA and exact
copy-length/hash checks. The copier now requires persistent-only access;
there is no fallback staging. Recorded failed locale/CLI discovery attempts
are retained rather than silently classified as missing functionality.

The [QD query contract](../tcon-research/qd-display-state-query-contract.md)
also resolves why `GetQDDisplayState` is unsuitable as a pure baseline read:
its classifier conditionally acknowledges saved results, including an
off-result write through `vconf_set_int`. It was not manually invoked by the
investigation; natural service calls remain possible. Direct stored
key reads instead found reminder fields false/0 at13:29 and raw maintenance
result/time/count values at13:35; those are not a live cycle, light, event or
current object-state measurement. The [factory period audit](../tcon-research/factory-off-sensing-test-period.md)
identifies UID0x506e/item200802 and a value6 disable predicate. Live GetItem
still reports0; its named database key is absent. All-route coverage and
setter/application semantics are not proved, so no factory value was changed.

## October26: power-sequence errors and physical latch chronology

The [hardware power implementation](../tcon-research/qd-power-control-hardware-sequence.md)
traces real GPIO/reset lifecycle phases and a normal on tail that can issue
status/frame/register panel commands. Rail providers can discard lower GPIO
errors; QDF discards recovery-tail returns. A nonzero ERR sample can bypass
that tail while setting cached power/PVCC1, and a GPIO-request error can leave
the initialized sample0 yet still reach the tail/cached-on stores. These are
concrete error/reporting weaknesses, not proof they occurred at the blackout.
Monitor-mode off has two1s waits; no measured owner three-second timer is
inferred from them. The script checks source hashes and instruction landmarks;
the full branch/error flow was independently reviewed manually.

The [paired physical chronology](monitor-latch-physical-timeline.md) confirms
that QD_TCON_OFF1 was already logged around the visible Apps control and
remains1 in the later owner-confirmed black captures in the same boot with
the same sampled P706/T1019. Repeated latch lines therefore cannot establish
a new terminal off action. The168.089s unsampled gap still permits a new
reset/re-set/action; process-start continuity was not captured then. The
[independent review record](power-notification-independent-review.md) retains
the corrections, raw-source checks and automated/manual coverage distinction.
The panel's current physical picture remains unobserved. No setter, reboot,
new native execution attempt, firmware/kernel/protection patch or verified
blackout repair was deployed in this pass. The goal remains unfinished.

The [end-to-end automatic-warning record](automatic-optimization-end-to-end.md)
now consolidates the independently reviewed flow. The reinforce timer defaults
to172800seconds; positive persistent time overrides with×60, while a cancel
event rereads that same key and uses×5 or a14400second fallback. The memory
cancel key is the watcher trigger, not the scaled value. Current0 therefore
does not disable this route. A13:48 passive process snapshot found app-control
PID1519/start2667ticks and tv-viewerPID427/start253ticks, with CLK_TCK250,
plus stored upgrade status0. This dates their process starts, not later
callback execution, timer rearm or a physical recovery. A13:53 bounded vlog
selection using recorded `-t3600` produced no matching warning/request lines;
vlog reported278837 emitted lines. Filtered absence is not a continuous onset
record or a firmware-wide event exclusion. All raw responses are retained.

## October26 follow-up: owner scale, factory correction and ARM32 probe

The latest two screen photographs were viewed again. The visible irregular
patch adjoins the lower edge; one photograph clearly shows a narrow dark
line rising from it. The owner's scale correction is **no larger than a
thumb**. The photographs have no calibrated scale and do not establish the
extent of an electrical fault or the cause of whole-panel blanking. This
correction is preserved in the photo map and the owner-history paragraph.

Independent factory review rejected an intermediate report's selector5/no-op
claim. The serialized node starts at0x6919c; UID0x506e is at+0x40 and the actual
driver selector is16 at+0x44. The index tuple's5 is a different field. The real
branch calls diagnosis and VE PPI functions, then conditionally stores the
value depending on the shared skipSaving status. No factory write occurred.
The subsequent [UID-specific transmit audit](../tcon-research/factory-off-sensing-transmit-target.md)
follows these calls rather than assuming a storage-only setting. A passive
read of eight live GOT bytes identifies the diagnosis PPI provider as
libvideo-misc and confirms the VE provider, with unchanged TIFS process
startticks and matching installed executable hash.

A separate [managed syscall probe](managed-kernel-abi-probe/README.md) used
the existing installed ARM32 CoreCLR6.0.9. It passed architecture/root/
Seccomp/getpid guards and returned errno38/ENOSYS for both deliberately
invalid BPF and perf requests. This is an actual ARM32 interface result,
not inferred kernel configuration or proof about the native ARM64 ABI. The
single run completed at14:22:30 with exit0 and empty stderr; all eight root
responses were retained and its exact private staging directory was removed.
No execution policy, installed file, driver state or display setting changed.

The [notification-server follow-up](../idle-research/stock-notification-cancellation-contract.md)
uses newly acquired installed provider libraries to distinguish database
deletion, event transport and the viewer's local timer destruction. A bare
delete has not been used as a cancellation substitute. These investigations
are consolidated in the [follow-up log](notification-factory-and-compat-abi-followup.md).
No physical recovery or permanent blackout fix is verified; root remains
host-assisted and the physical picture is unobserved.

The completed legacy notification trace links successful matching deletion
with count>0 to delete_single_notify(1,priv_id,uid), the client's detailed
callback event1, and the viewer's local progress-timer destruction. This is a
conditional stock countdown-cancellation route, not a tested intervention or
maintenance-policy disable. Live identity/registration and asynchronous expiry
ordering remain unobserved; an already-issued request is not undone.
