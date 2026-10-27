# TCON reset analysis — 2026-10-26

## Evidence

The current-boot record at uptime 1826.639–1837.451 is a real display-path power cycle. The process labels in the TV kernel log identify `deviced` (PID 675) as the actor that asserted ELVDD/TCON reset and later called the power-on/recovery sequence. `tcon-monitor` (PID 1019) reported the already-off state once per second; it did not issue the reset in that record.

The sequence is: reset asserted at 1826.639; display reports TCON off at 1827.780; `AVEMonDIM` reports TCON state NG at 1834.698; `deviced` powers it on at 1835.642; access/display/PMIC checks pass; and the TCON resumes by 1837.451. The restart itself lasts about 10.8 seconds from reset assertion to picture-on completion. It is not a TV reboot.

The vendor then restores panel policy values, including `screen saver method:1`, factory screen-saver brightness 7, wait time 2, slope 2, sensitivity 17, and low-power mode 6. After the panel is back, `AVEMonDIM` sets screen-saver brightness 0 at 1837.451; it later sets brightness 7 at 1869.133. This establishes that the menu/saver path can control brightness, but does not establish it initiated the preceding reset.

The earlier Oct 12 capture is separate and more specific: `tcon-monitor` logged error-detect GPIO fault `ERR DET Status:0x10`, then requested reset and recovery. That capture shows a known fault-recovery path. The current capture does include an `off sensing required`/normal-DPMS-off sequence before the reset assertion, but it has no preceding error-detect line. Ordering alone does not establish that off-sensing caused this particular reset.

## Implications

Stopping `tcon-monitor` is not a workaround: it would not have prevented the captured `deviced` reset, and could suppress monitoring/recovery after the documented ERR DET fault. Likewise, repeatedly forcing `Display.State=Normal` affects the high-level display state but cannot cancel a kernel driver power cycle; the log has the display manager active while the TCON is off.

The report that videos remain stable while sparse/static Apps black out is compatible with the panel/saver/off-sensing path being a trigger or stressor, but it does not prove the Apps patch caused a hardware fault. The horizontal/vertical center-line damage and the independent error-detect event make an underlying panel/TCON/internal-link fault plausible.

## Reversible next probe

Collect a new bounded ring-buffer delta immediately after one user-observed blackout, recording both the prior and following 30 seconds. Include error-detect, ELVDD, off-sensing, deviced, TCON and screen-saver messages and the output of read-only vconf enumeration. Compare it with a similarly timed interval of stable full-screen video. This will determine whether every blackout begins with ERR DET, with off-sensing, or with a distinct compositor/idle request.

Only after identifying an exposed `off-sensing` or screen-saver policy key should a reversible setting experiment be considered. The native settings schema exposes pixel shift, logo brightness and manual pixel refresh; it does not expose an automatic TCON-recovery disable. Do not change TCON registers, kill `deviced`, stop `tcon-monitor`, or disable thermal/panel protection: none are a known way to keep an actually faulting panel displaying, and all risk leaving it black rather than recovering.

## Screen-saver research result

Two bounded screen-saver experiments produced no usable mitigation result and were restored. The native-interface path is likely bypassed by the TV's active display path; additionally, exact-build inspection indicates `screensaver_init` is deprecated/no-op. It is therefore not a recommended workaround, and no persistent screen-saver helper is being proposed.

This does not establish that the screen saver caused the resets. The currently running finite display-state-lock test is the separate, reversible policy test described below; its outcome is pending log review. It does not alter TCON registers, ERR_DET handling, panel protection, compensation accounting, or thermal policy.

## Exact display-state lock semantics

Static disassembly of this TV's extracted `libdeviced.so.1.0.3` establishes the on-device D-Bus method signature as `(sssi)`.  The state mappings are `1 -> lcdon`, `2 -> lcddim`, `4 -> lcdoff`, and `8 -> suspend`.  Flag bit `0x2` produces `gotostatenow`; without it the library produces `staycurstate`.  The build has additional vendor flags (`0x4 -> holdkeyblock`, `0x8 -> standbymode`), which are not candidates for this diagnosis.

The public Tizen `display.c` matching the `display_lock_state(state, flag, timeout)` ABI confirms that the final integer is a timeout.  The corresponding display service source treats these state-lock timeouts as milliseconds.  A bounded, reversible policy experiment can therefore use `lockstate("lcdon", "gotostatenow", "NULL", 180000)` for at most three minutes, observing the lock count/state and kernel log, then guarantee an `unlockstate("lcdon", "resettimer")` rollback.  This is a high-level idle/DPMS policy lock, not a TCON override; it must not be represented as a cure for, or used to suppress recovery from, an `ERR DET` fault.
