# Rescued owner-power-on capture: bounded offline state analysis

## Capture status

This analysis uses only the rescued retained files under
`owner-power-on-20261026a-rescue/retained/`.  The original record explicitly
marks the 85-second collection `accepted: false`, `technical_capture_complete:
false`, `cleanup_verified: false`, and `physical_state:
unobserved-or-incomplete`; its failure is `ValueError: capture completion
missing`.  The rescue manifest pins the retained trace at 19,310,261 bytes,
SHA-256 `44f68ebd1fb301c74cab501a04e84b73b95223e96c977062ed6db0b92977b575`,
and records separate hashes for `meta.txt`, `samples.txt`, errors, artifacts,
fds, and vlog output.  Rescue preservation does not turn the failed run into
an accepted onset capture.

The retained trace decodes with the exact existing QD decoder: 264 transfers,
zero parse errors, and trace-ring accounting `entries-in-buffer ==
entries-written`.  That establishes syntax/completeness for the retained I2C
trace only.  The absent completion metadata/fd validation and failed cleanup
remain material limits.

## Concrete retained transitions

The decoded QD focus rows contain no off-sensing (`0x180`) or EL-sensing
(`0x1a0`) write.  The following are retained transport-complete writes, not
evidence of MCU acceptance or emitted light:

| uptime | task/PID | selector | value |
| ---: | --- | --- | ---: |
| 73132.587104 | `deviced`/675 | panel mute `0x164` | 1 |
| 73132.801590 | `AVEMonDIM`/1013 | screen-saver brightness `0xc4` | 7 |
| 73136.537901 | `deviced`/675 | screen-saver method `0xc0` | 1 |
| 73136.538960 | `deviced`/675 | screen-saver brightness `0xc4` | 7 |
| 73136.540110 | `deviced`/675 | waiting policy `0xcc` | 2 |
| 73136.541149 | `deviced`/675 | screen-saver slope `0xd0` | 2 |
| 73136.554593 | `deviced`/675 | VRR-DIA `0x150` | 0 |
| 73136.555632 | `deviced`/675 | VRR control `0x15c` | 0 |
| 73136.725190 | `deviced`/675 | panel mute `0x164` | 0 |
| 73136.593759 | retained QDF writer | dimming-level request `0x128` | 207 |
| 73137.318289 | `AVEMonDIM` | screen-saver brightness `0xc4` | 0 |

The later brightness-zero write has a known selector/value but no proved
meaning for emitted light in this report; it must not be conflated with the
earlier value seven or treated as a physical picture label.  The retained observer file has only two chat/instruction notes, neither an
ordered wholly-in-window physical picture transition.  The raw trace does
contain capture markers: `CAPTURE_START` at 73052.233218, `CAPTURE_END` at
73137.840506, and `CAPTURE_DRAIN_END` at 73138.033049.  (The generic QD
decoder does not parse this tracepoint's marker grammar into its `markers`
field.)  Therefore these software timings cannot be aligned
to a confirmed physical blackout or used as fault causality.

## Start-checked sampler deltas

`owner-power-on-qstate-extract.py` and its generated
`owner-power-on-20261026a-qstate.json` decode every retained row using the
exact 26-field `QD_COUNTS` tuple from
`observed-branch-onset-capture.py`.  This is a **start-metadata-only** check:
all rows have the recorded AVOC/deviced PID, start-tick and load-bias tuple;
all preserve the expected QDDimming vptr, inner pointer, backend pointer,
backend vptr/slot and initialized-byte low value of one; and all preserve the
checked deviced/EL pointer-chain words.  The power index is within `0..6` in
every Q row.  It cannot substitute for the missing end metadata, endpoint map
checks or sampler-DD accounting, so the failed capture remains unaccepted and
all rows remain sequential/non-atomic.

There are 370 `M` rows from 73052.32 through 73137.17 and 85 `Q` rows spanning
73052.26 through 73136.66.  The Q read spans are 0.41000000000349246 to
1.1000000000058208 seconds.  The script compares all 38 little-endian words
at `AVE-bias+0x5bfc5c` in every M row.  **There are zero monitor-word deltas.**
Thus the retained interval preserves, among other documented entries:

| monitor field | value in every retained M row |
| --- | ---: |
| ERR/VDD/ELVDD fault counters | 0 / 0 / 0 |
| ERR/VDD/ELVDD recovery counters | 2 / 0 / 0 |
| `si_ok_count` / `qd_tcon_off` / `onetime_execution` / `ip_status_count` | 4 / 1 / 1 / 7 |
| `fault_occurred` | 0 |
| `pre_monitor_on` / `g_tcon_monitor_restart` / `g_tcon_monitor_on` | 1 / 0 / 1 |

The other monitor words are retained by their sampled offsets and were also
unchanged; this report does not invent meanings for those raw words.  An
unchanged latch one is monitor bookkeeping, not a new panel-off operation or a
physical output measurement.

Only three Q subfields changed between adjacent rows (66 raw transitions in
total):

| sampled subfield | raw sequence / interval | bounded interpretation |
| --- | --- | --- |
| `inner+0x45c` | 62 changes, 37 distinct unsigned values, from the first interval 73052.26–73053.23 through 73131.28–73132.28; final sampled value 52 | This offset has no field-role mapping in the retained source map. It is raw changing state, not a timer, brightness, or fault counter. |
| deviced `OP+0x24` raw word | 0→1 during 73131.28–73132.28; 1→0 during 73135.31–73136.23 | The sampler observes this exact raw address, but the available map does not establish a name or meaning. It is deliberately not called a pointer or state. |
| power-state index | 1 (`lcdon`)→3 (`standby`) during 73131.28–73132.28; 3→1 during 73134.24–73135.31 | Names come from the exact deviced seven-entry table. Each is only bounded by the two non-atomic Q row starts; it does not time a physical transition. |

The following sampled values were stable in every Q row: QDDimming initialized
low byte one; `siDimLvl` cache at `AVE+0x5ab958` = 207; `inner+0xa8` = 207;
`inner+0xac` = 207; `inner+0x458` = 1023; `siWeberGain` at `AVE+0x5ad94c` =
1023; `siPreTargetWeberGain` / count at `AVE+0x5bf6d0/+4` = 1023 / 0;
`inner+0x2a4/+0x2a8` = 1024 / 0; and the exact-base-QD AutoPowerOff counter at
`AVE+0x5be420` = 0.  The documented `inner+0x2a8` value is a raw signed
AutoDim argument, not an emitted-light Boolean.  These software values do not
prove lower transport success, panel light, or exclude an unsampled failure.

The narrow next offline action is to trace the writer/policy route for the
retained `screen-saver brightness 0` request at 73137.318289, including its
cache and error gates, rather than inferring that its selector/value changed
the damaged panel.  No additional TV operation follows from this decode.

The only supported conclusion remains narrow: a rescued, syntactically
complete I2C segment records a mute-one then mute-zero bracket with
screen-saver and VRR-policy writes shortly before the latter. It does not
prove why those writes occurred, whether they affected the damaged panel,
whether owner power actions happened, or a recovery/fix.
