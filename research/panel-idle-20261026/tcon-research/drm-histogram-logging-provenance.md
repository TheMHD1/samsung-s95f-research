# DRM histogram logging: provenance and limits

## Result

The checkpoint's `HISTOGRAM INP(Y/R/G/B)`, `DE(SAC)`, and `VE(CE_)` console
rows are produced by the copied **`sdp_drm.ko`**, not by QDF, the OLED panel,
or a generic application histogram.  The recovered path reads display-processor
registers using `dp_reg_readl`, masks each raw register to 23 bits, aggregates
fixed groups, then formats the results through `printk` and `vlog_print`.

This makes the rows useful host-output-pipeline context for a future
overlay/full-screen comparison.  It does **not** make them calibrated
luminance, panel current, post-OLED light, or a QD-protection input.  The
captured labels describe driver regions; neither the retained code nor an
observed row identifies a normalized unit, a source buffer, or a live mapping
from a particular bin to panel pixels.

No TV/root/device/network action occurred for this report.

## Exact input

| file | SHA-256 |
| --- | --- |
| `binaries/sdp_drm.ko` | `d1016cf5b72f86a1623b231d96dc944082263a70d3602d859f993d751bfdf881` |
| checkpoint raw response | `67a23c8d1c00c39aa2c75c2ff52bb40d878b091ec2967b28cacb32bf998566ab` |
| checkpoint decoded trace | `01e43a195109336330d6b609db1eae37d5f7f69d212aa65a953cffd8f2e0a42a` |

All module locations below are ELF `.text` offsets in the copied relocatable
module, not live addresses or an assertion of a current module binding.

## Actual producer paths

The checkpoint contains all six labels—four `INP` channels plus `DE(SAC)` and
`VE(CE_)`.  One source-backed route that emits that exact set is:

```text
__dp_isr_queue_work_thrd                 .text+0x1b008
  -> sdp_dp_input_print_hist_analyze     .text+0x22e40
  -> sdp_dp_post_print_hist_de_ve        .text+0x48f08
  -> printk / vlog_print
```

The direct calls are at `0x1b930` and `0x1b934`.  This is a worker-thread
path, not a per-frame proof: the complete 4,128-byte worker has upstream
state/branch gates outside this bounded attribution, and the checkpoint
doesn't retain a function-entry event.

There is a second, distinct static route for `INP`-label printing:

```text
dp_capture_get_capt_frame_crop            .text+0x2d600
  -> dp_drv_get_mute_status_with_auto_mute_cnt
  -> sdp_dp_post_print_hist                .text+0x48bd0
```

The call is at `0x2d8a4` after the mute-status helper.  Therefore the shared
text labels alone cannot identify which route emitted an arbitrary future
`INP` row.  In this checkpoint, simultaneous `DE(SAC)`/`VE(CE_)` rows provide
positive static compatibility with the worker route, since
`sdp_dp_post_print_hist_de_ve` is directly called there.  This is still a
source-derived attribution, not a live call trace.

## What the driver reads and formats

### `INP(Y/R/G/B)`

`sdp_dp_input_print_hist_analyze` invokes `__get_hist_val` four times with
base addresses:

```text
0xc9002524  Y       0xc90025a4  R
0xc9002624  G       0xc90026a4  B
```

`__get_hist_val` (`0x204d8..0x20540`) initializes eight output words.  For
each output word it reads four consecutive 32-bit DP registers, masks each
with `0x007fffff`, and sums the four masked values.  It advances to the next
four-register group until it has eight aggregates.  The corresponding
formatter prints eight `%06x` fields for each channel.

This proves a raw, fixed-register aggregate.  It does **not** prove that the
aggregate is a pixel-count histogram, is normalized to picture resolution,
is sampled synchronously with a presented frame, or comes before/after every
PQ stage.  `INP` is a driver label, not a licensed semantic definition.

### `DE(SAC)` and `VE(CE_)`

`sdp_dp_post_print_hist_de_ve` reads two more register windows:

* `0x7a00f68..0x7a00ff4` in ten groups; each group is again four reads,
  23-bit masking, and sum before the ten-field `DE(SAC)` output.
* `0x7000a9c..0x7000ac0` is read directly.  The `VE(CE_)` formatter consumes
  eight selected values (`0xa9c`, `0xaa0`, `0xaa4`, `0xaa8`, `0xaac`,
  `0xab4`, `0xab8`, and `0xabc`); the same routine also reads `0xab0` and
  `0xac0` but does not pass those two reads to that eight-field formatter.
  None of these values goes through the input helper's four-read aggregate.

The names establish distinct driver register regions, not known physical
blocks, brightness, duty, current, or panel-side activity.  The raw checkpoint
values therefore must remain hexadecimal driver observations with no inferred
unit.

## Timing and caching limits

The checkpoint retains a single burst at embedded printk time about
`92518.6035..92518.6036`, within a five-second window.  The trace clock is
about 61.5 seconds offset from the embedded printk/uptime domain, so no direct
numeric merge is valid.  There is no retained source-backed polling period or
frame association for the histogram path.  The worker's name and direct
register reads make a software cache less likely than a purely userspace
cached value, but they do not rule out hardware counter latching, delayed
update, or stale register contents.

The separately retained, validated kernel-snapshot extraction
`overnight/sleep-investigation-20261027a/retained-histogram-extract.json`
(SHA-256 `3fa5ea274c9ec61b53d29111ae438a10e12fad70f3015f58343368c4c4cbeabb`)
shows observed `INP(Y)` sums of exactly `8,294,400` and `2,073,600` in records
whose known output resolution changed from 4K to 1080p. This is consistent
with count-like aggregates and useful for comparing content paths, but is not
a unit specification or proof of which pipeline stage owns the values. Those
source records remain unsuitable for a physical-onset claim.

No passive memory field is currently validated as a safer replacement for the
stock logs.  The already-emitted `printk/console` rows are the observable
surface; reading the underlying registers through an unknown interface would
be a new hardware access, not an observation established here.

## Diagnostic use and boundaries

For a future owner-authorized natural transition, preserve the unmodified
histogram console rows alongside the existing I²C/DRM/vblank/QDF evidence.
They could show that host DP-register aggregates differ between overlay and
full-screen content, which would make a content-path distinction concrete.
They cannot answer whether that difference triggered QDF/RT protection or a
physical panel blackout.  A useful record still requires owner-timed physical
annotation and event-loss/clock-domain validation.

Do not enable a hidden capture path, write a DP register, or infer a repair
parameter from the bins.  The `SIG11` console row in the same checkpoint is
separate: a later process snapshot found its ThreadPool PID alive, but that
later observation lacks a pre-event identity and is not crash/reboot or
same-epoch survival proof.

## Offline reproduction

`PYTHONPATH=/tmp/tcon-capstone python3
tcon-research/drm-histogram-logging-provenance-reproduce.py`

The helper hash-pins the copied module and checks the named functions, direct
worker/capture calls, register-base constructions, masks, and format literals.
It reads local files only; landmark verification is not emulation or a live
binding proof.
