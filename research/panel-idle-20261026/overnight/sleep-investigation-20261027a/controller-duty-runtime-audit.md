# Controller-duty read and nearby runtime-state audit

## Scope and result

This is an offline audit of three already retained, accepted records on boot
`00000000-0000-4000-8000-000000000000`:

1. a five-second technically complete but physically unobserved smoke capture;
2. one later fixed generic-read request for QDF selector `F3:0128`; and
3. one still-later ordinary status read.

The duty request returned raw value **207** and the later status reader
returned **`0x10`**.  The smoke sample's selected monitor and QDDimming fields
were stable across every retained row, including duty-related cached fields at
207 and the historical QD monitor latch at one.  These facts do not establish
panel light, a controller transaction beyond the kernel callback output,
hardware acceptance, a transition time, or a causal relation between the
fields.

No new TV/root/network action was made for this audit.

## Exact retained inputs

| retained input | SHA-256 |
| --- | --- |
| `sleep-smoke-20261027a.onset/record.json` | `b3e2b0746b211deb939bf834be0f4ee70c511c37bace89b9f0e8cf0a62a4c320` |
| smoke `samples.txt` | `d7ac37df2e96d8356593f287411cbc9af25fd0f4130406677ad81e71d03300ea` |
| smoke `meta.txt` | `45a51a101357416e2bee36d7781d21ea569a3cb0eca4586aea470450d6b008d4` |
| smoke trace | `5d82d12ed6dad98e6a2ea77decf1edf9ee00b6a824512801e2d25b88b5fe05fc` |
| smoke `sample-errors.txt` | `c9672a4bf0e38735c6278f6bf322196ab044af02b5515338235663336093637d` |
| duty result | `4944dd3fe9f47b3d15ca5618b0fc4a203271b0edd5910049d11c6a6d4f8231cc` |
| duty kernel-log extraction | `d43184307091d67d93992a4dd72188ff3331d2a7fd258534c2161c7e1bd5c1c6` |
| later status result | `dbc26105f4a7674ef9b17c4a6e99e4ac9f12bb0dd87b5973a08dc25c16ac203a` |
| later status-log extraction | `d4744f530f75b013cbc9d1c7d8abb417117b68c7e2c1d21f01efcce2aa7258c5` |
| Q-row decoder/source | `3aa5c9480c8a643e14be5c6aeac62202f918d16cd9100a5b0c4ff14a5e2785ca` |

The smoke record is technically accepted and cleanup-verified, but explicitly
marks itself `diagnostic_eligible: false` and physical state
`unobserved-or-incomplete`.

## Sequential timeline

All values below use the target's uptime domain. They are separate sequential
operations, not an atomic combined observation.

| event | target uptime | retained support |
| --- | ---: | --- |
| smoke trace START / END | `93126.809551` / `93131.839148` | smoke record markers |
| five Q branch rows | start `93126.83`; final end `93131.27` | `samples.txt` |
| duty helper execution | `93210.81` | duty result, PID 4231 |
| matching QDF kernel line | `93210.778827` | duty log, same PID 4231 |
| status helper execution | `93259.94` | status result, PID 4792 |
| matching QDF status line | `93259.828033` | status log, same PID 4792 |

Thus the duty read began about 79 seconds after the smoke trace ended, and the
status read began about 49 seconds after the duty helper. The kernel messages
precede their helpers' reported execution times by about 31 ms and 112 ms,
respectively. This corroborates the logging PID/operation association but does
not make the independent reads a single sample or bridge the approximately
80-second unsampled interval.

## Fixed duty-read result

The retained helper used ARM32 generic operation 19 with ioctl
`0xc010749f`, command `0x0000f30000000128`, and request bytes
`f30000000128`. Its output changed from sentinel `0xa55a5aa5` to `207`; it
returned zero and closed successfully. The matching QDF log is:

```text
[93210.778827] [TCON:QDF] QDFTcon_ReadOneCommand[4231:ManagedTconDuty]:
cmd = 0xF30000000128, value =207
```

This establishes only the helper's `kernel_output_written` classification and
matching bounded kernel log. `207` is within the copied profile's low-10-bit
range, not a brightness, light, current, safety, or controller-flash proof.
The retained duty record itself preserves unresolved controller bookkeeping,
profile/live-flash, and physical-state limitations.

## Smoke raw-state rows

The Q decoder is the exact `QD_COUNTS` ordering in the hash-pinned source.
It decoded five Q rows. Each has a sequential span of `0.45..0.46` seconds
(mean `0.458` seconds); monitor rows are independent 38-word reads. Therefore
the values below are row observations, not an atomic snapshot.

All 22 monitor rows and all five Q rows had the same decoded values for every
sampled word. The stable selected fields were:

| sampled field / source offset | all retained rows |
| --- | --- |
| ERR/VDD/ELVDD monitor counters (`state +0x3c/+0x40/+0x44`) | `0 / 0 / 0` |
| ERR/VDD/ELVDD retry bookkeeping (`+0x48/+0x4c/+0x50`) | `2 / 0 / 0` |
| `si_ok_count`, `qd_tcon_off`, one-time, IP-status (`+0x54/+0x58/+0x5c/+0x60`) | `4 / 1 / 1 / 7` |
| unnamed raw word / `fault_occurred` (`+0x64/+0x68`) | `1 / 0` |
| RoseMQD cached duty (`libave +0x5ab958`) | `207` |
| QDDimming inner `+0xa4/+0xa8/+0xac` | `0 / 207 / 207` |
| global gain / target-count pair (`+0x5ad94c`, `+0x5bf6d0..d4`) | `1023 / (1023, 0)` |
| QDDimming inner `+0x2a4/+0x2a8` | `1024 / 0` |
| QDDimming inner `+0x450`; AutoPowerOff counter | `0`; `0` |
| deviced power-index field | `1` |

The monitor `qd_tcon_off=1` is the previously established historical latch,
not evidence of a new panel-off instruction during this smoke. Similarly, the
inner `+0x2a8=0` is a raw sampled field; this audit does not rename it an
emission, AutoDim, brightness, or fault state beyond the sampler's offset map.

The trace ring was complete and retained 8,274 capture-window events, but its
I²C raw count was zero. It therefore supplies no aligned wire result for the
later F3 read and no evidence that 207 was transferred to, applied by, or read
from the controller at the smoke time.

## Later status result

The separately retained status helper changed its sentinel to `0x00000010`,
returned zero, and closed successfully. The matching log is:

```text
[93259.828033] [TCON:QDF] QDFTcon_GetErrDetStatus[4792:TconStatusRead.]:
ERR DET Status:0x10
```

This is an accepted later `kernel_output_written` result with a matching QDF
message, not proof of a controller transaction, read-to-clear behavior,
unmodified QDF debug path, physical panel state, or a recovery outcome. It
does not retrospectively classify the earlier smoke/duty rows.

## Boundaries

There is no owner-timed physical annotation in any of these records. The
completed smoke is explicitly ineligible for a visible-to-black onset claim;
the later controller reads are not a trace. No inference here supports
changing monitor latches, retries, protection state, power, output duty, or
firmware. Any future comparison must use fresh same-epoch state/trace and
human physical annotation.
