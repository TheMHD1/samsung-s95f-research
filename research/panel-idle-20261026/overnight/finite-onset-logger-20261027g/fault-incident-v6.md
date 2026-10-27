# V6: recorded RTP fault transition on the Samsung S95F

The investigation now has a finite controller capture spanning a normal-to-fault RT transition, followed by the same host status and fault-pin signature seen in earlier owner-confirmed blackouts. The physical panel was unobserved because the owner was asleep. No repair or triggering UI transition is proved.

## Measured event

On Linux boot `00000000-0000-4000-8000-000000000000`, the V6 logger observed uptime115887.39..115907.45 (20.06seconds). The pre-arm64byte RT block had fault halfword0 at offset0x0a. Its restored post-block has0x1001 there. Other changing offsets are0x00 (0→1) and0x0e (1→0); logging gate0x06 returned to0, and mode0x10 remains4. This pattern matches a previously identified packaged RTP setter, but executing-body identity and exact initiating instruction still require the separate code-provenance review.

All16native transfers completed with exact counts; gate0→1→0, release/close, ReadyForHeader, live host READY and exact stage cleanup passed. The fault change does not invalidate restoration: the gate was restored while the fault state changed independently. No error-reset request was sent.

The secondary ring moved from143/143/0 to1899/1899/0. Its net1756byte span contains31printed RTP sample rows and two `rtp_act_736` lines. The exact bytes are in `onset-v6-event-log.bin` and `.txt`, SHA256 `deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba`. Printed sample labels include RGB0, x570/571/620/621/630/631, y2159, c0/4095/464/470/482/492 and diff1065..1864. These are literal firmware labels and values; they are not yet assigned physical units or a physical panel coordinate transform. Missing printed indices do not by themselves prove dropped records.

A later single stock status query returned0x10 with successful cleanup. The retained kernel row independently reports `[116071.646556] [TCON:QDF] QDFTcon_GetErrDetStatus[15976:TconStatusRead.]: ERR DET Status:0x10`. A separate accepted one-shot input request on gpiochip15, line5, returned1 and closed both handles. These sequential measurements corroborate the earlier status0x10/pin1 signature; they do not establish continuous state between samples or observed light emission.

## Trigger and controls

| Capture | Logger observation uptime | ForYou API interval | RT fault before → after | Logger accepted/cleaned |
| --- | --- | --- | --- | --- |
| V4 | 115564.84–115584.91 | 115565.99–115566.01 | 0 → 0x0000 | yes |
| V5 | 115802.04–115822.11 | 115803.51–115803.57 | 0 → 0x0000 | yes |
| V6 | 115887.39–115907.45 | 115888.93–115888.95 | 0 → 0x1001 | yes |

Each ForYou API call returned normally with handle disposal. V4 later still showed Apps and full-screen screensaver windows. V5's in-window view also showed a screensaver and Apps. For V6, one ordinary saved-token Back key was followed immediately by a verified Apps view without screensaver; capture staging and the API request followed without another idle delay. Its in-window view at115889.81 still showed Apps, focused CSFS, and no screensaver. Therefore, the intended ForYou transition is unconfirmed even for V6. The fault occurred during the technical capture while software remained Apps at the sampled view; it cannot be attributed to the returned ForYou request. A brief unobserved intermediate UI state remains possible.

The first attempted Back invocation used system Python and failed at its library import before lock/network acquisition. The existing TV venv then supplied the one actual ordinary key. A later just-in-time Back was explicitly planned for V6. These records remain separate, and no remote API return is treated as an execution acknowledgement or physical observation.

## State left and analysis boundary

No reboot, panel cycle, flash, threshold change, protection suppression or persistent OS change was performed in these captures. V4/V5/V6 logger stages are verified absent. The shared six-file UI stage was explicitly cleaned (`ui-cleanup-onset-v6`, stage_absent true). Older v2/v3 evidence stages are preserved. The latest event is left uncleared for offline analysis; no further UI-trigger attempts are planned from this selector until its consumption gap is understood.

The new priorities are the exact sample formatter/packed-input provenance and the `rtp_act_736` caller-to-setter path. A separate automatic-review-blocked persisted/high-bank/POFLG branch remains excluded and is not retried. Existing static log analysis shows that the NORMAL395/393/365 suffix is a pre-increment halfword, not an assigned fault code or physical unit. No permanent repair or change to the damaged spot/vertical line is established.

## Subsequent ordinary numeric trace and retained context

The completed `rtp-act-736-trace.md` connects the packaged event tail to the
RT1001 setter and host RTProtect10 path. `rtp-736-predicate.md` identifies the
immediate predicate as the low16 selected accumulator exceeding a
mode/alternate-selected halfword limit. Printed individual lane differences
are not that accumulator and do not identify its triggering comparison.

A later accepted fixed reader sampled both allocated windows without
changing settings, gates, thresholds or fault state. Fault1001 persisted;
low-score latches were54(mode6)/44(other), with all candidate limits
200/0/0/200/40. These sequential reads ended about32minutes after V6, and
the live mode/alternate selector was not sampled. Therefore mode4 and the
alternate modes are numerically compatible with the late latches, while
default modes1/6 are not; no one branch is identified as the actual V6
comparison. See [the full findings and raw-artifact links](fault-context-after-v6-findings.md).

The subsequent ordinary input trace establishes that the score uses delayed
history of qualifying-lane counts, not the amplitudes printed as `diff`.
It also found and corrected one fallback-pointer literal-resolution error
in the frozen format report. The [additive erratum](rtp-packed-source-address-erratum.md)
preserves the old report and identifies exactly which semantic claim is
superseded; live bytes, field formats and the event predicate are unaffected.

A second bounded diagnostic captured the ordinary mode/alternate-selector
windows on the same boot. It returned the expected root pointer, aa0/ac2,
alternate mirror1 and candidate byte1 with a matching three-halfword context
fingerprint. The ordinary tail would select mode1 with those flags, and a
nonzero alternate byte selects the earlier measured limit40. That is
consistent with the earlier score44 and the NORMAL row labels. The selector
capture was57.52minutes after V6 and25.41minutes after the score sample, so
these remain a specific test hypothesis rather than the event-time operand
tuple. Its separate control field is0, which is retained rather than assumed
to be continuously Boolean. See [selector findings](selector-context-after-v6-findings.md)
and [the independent runtime audit](selector-context-after-v6-review.md).

The ordinary caller gates future packed scans after the latched fault,
while its configuration mirror can update before that gate. This explains
why late values need their individual update rules: they are not necessarily
all fresh or all from the same scan. The decisive next diagnostic still
needs the loaded mode/limit and score together at the comparison edge.
