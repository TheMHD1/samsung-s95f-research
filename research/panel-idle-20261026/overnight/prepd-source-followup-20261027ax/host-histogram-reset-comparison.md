# Host DRM histogram comparison across the stock MODE2 lifecycle

## Result

The retained host DRM-DP histogram rows do **not change** across the one stock
MODE2 off/on lifecycle in AV. The closest complete group before the action
starts at uptime `136361.560322`; MODE2 starts at `136363.892943`, and its
PID-tagged I2C replay ends at `136366.222190`; the closest complete group
after that tail starts at `136371.577002`. Every field in `INP(Y/R/G/B)`,
`DE(SAC)`, and `VE(CE_)` is numerically identical between those two groups.

This is a positive statement only about the numeric values present in the
retained kernel rows under those six labels. Their interpretation as reads
from particular host DP-register paths is conditional on the copied
`sdp_drm.ko` matching the live module and on one of the recovered routines
having emitted these rows; neither live binding is retained. It is not proof
of constant video content, a continuously unchanged register, a presented
frame, emitted light, physical panel state, or a PrePD/controller input. No
histogram group was retained inside the MODE2 interval. The copied-source
analysis establishes neither a polling cadence nor a frame association, and
the retained evidence supplies no live dataflow binding these rows to the
controller's ordinary `X` mirrors.

No TV, root, network, USB, controller, native-helper, power, reset, MMIO, or
physical-observation operation was performed for this report.

## Exact evidence reconstruction

The AV evidence manifest is SHA-256
`1c0dbaaa92b6167aa23e2ca2bd04cadbabe90f422535fbe935cbcfb5ddccca75`.
It pins the original `stock-rt-av-20261027.onset/artifacts.txt` at
`a5cb2171a4faf92f7128d15d8adcda5f30449d83daff0aa31fceb4e6b539f95d`,
the raw ftrace at
`ea9f0a57ae34faaae714c11230194d32819cf28c5debcbe8ec1e381706d686ed`,
the decoded trace at
`a6835690ca62fb68ca563ba132171549161876f96c4c964f1a8928ccbd59978b`,
and both saved kernel extracts.

The reproducer parses the original `@@ KERNEL_START` and `@@ KERNEL_END`
sections, joins and strictly base64-decodes their multiline payloads, and
gzip-decompresses them. The reconstructed bytes are exactly equal to:

| section | retained uptime line | reconstructed/saved SHA-256 |
| --- | --- | --- |
| start | `136341.92 508217.79` | `e5eac973ce8ca603e5bfc1e1749eea3897e87eec14f17b4943720da9bbc82e68` |
| end | `136412.87 508427.00` | `c00c2efd6ba743283c38113dc4513d04c9e01488e84c7a27b7536e97d2ece8e8` |

Both sections and the controller snapshots discussed below retain boot ID
`00000000-0000-4000-8000-000000000000`. The decoded trace's recorded source
hash equals the independently hashed raw ftrace. PID `17157` has exactly 346
decoded transfers; the last ends at `136366.222190`. The action start comes
directly from the reconstructed kernel end section's PID-tagged
`QDFTcon_SetQdTconPowerControl ... Reset(2)` row at `136363.892943`.

## Exact histogram bracket

The start snapshot contains 51 complete six-row groups and the end snapshot
contains 50. Forty-three group timestamps overlap because these are rolling
kernel snapshots; there are 58 unique group timestamps, not 101 independent
times. Every retained group in both extracts has the same complete value set.
The closest action bracket is:

| point | first row | last row | relationship |
| --- | ---: | ---: | --- |
| closest pre group | `136361.560322` | `136361.560374` | first row is `2.332621 s` before MODE2 start |
| MODE2 / lower lifecycle | `136363.892943` | `136366.222190` | Reset(2) row through last PID-17157 I2C result |
| closest post group | `136371.577002` | `136371.577049` | first row is `5.354812 s` after the I2C tail |

There is no retained histogram group whose row interval intersects the action
interval. The observed separation between adjacent groups is therefore not a
continuous invariant and is not promoted into a source-proved cadence.

The exact pre and post values are:

| field | pre values | post values | changed? |
| --- | --- | --- | --- |
| `INP(Y)` | `0b64d4 057f00 04cf10 039c27 033350 01b6df 0115a4 005522` | same | no |
| `INP(R)` | `0b3d78 0534e4 052a05 038146 039662 01cb13 00cc6e 005876` | same | no |
| `INP(G)` | `0b6966 057ba6 04bd57 03ae85 031cb1 01ba38 0113a2 00688d` | same | no |
| `INP(B)` | `0c6ae4 0671a7 03ba7d 032a1a 029b36 0167a3 015d06 0082ff` | same | no |
| `DE(SAC)` | `0003ff` followed by nine `000000` values | same | no |
| `VE(CE_)` | `7e9000` followed by seven `000000` values | same | no |

The existing copied-module source analysis,
`tcon-research/drm-histogram-logging-provenance.md` at SHA-256
`a0153f56add3290c27e2d0e4d1816409253e6190f53b1ea6a71bee375404b220`,
supports this conditional narrow interpretation if that module/routine
binding holds:

- each `INP` value is a sum of four direct DP-register reads after a 23-bit
  mask, with eight reported aggregates per Y/R/G/B channel;
- `DE(SAC)` similarly reports ten four-register masked sums; and
- `VE(CE_)` reports eight selected direct register values, not the same
  four-register aggregation.

The copied module has two distinct static paths capable of printing the
`INP` labels. The simultaneous `DE(SAC)`/`VE(CE_)` rows are source-compatible
with its worker route but do not prove a live invocation of that route. Thus
even the candidate-function identity is not promoted from static
compatibility to observed execution.

Regardless of that source-attribution condition, the row labels and numbers
do not identify physical units, content buffers, pixel coordinates,
brightness, current, panel-side activity, or PrePD input. Under the
copied-source interpretation, hardware latching, delayed update, and stale
register contents also remain allowed.

## Temporal relationship to the controller input snapshots

The older and later AP_EXCO/controller reads are not samples at the action
boundary:

| evidence | terminal/action uptime | relation to AV | relevant retained result |
| --- | ---: | --- | --- |
| original W AP_EXCO snapshot | `125699.16` | about `10664.733 s` before MODE2 start | ordinary SHA `0f788489...`; `X=8254590/8251261/8250967` |
| AK repeated W snapshot | `131332.14` | `5031.752943 s` before MODE2 start | byte-identical ordinary and derived windows to W; same `X` |
| AV MODE2 lifecycle | `136363.892943..136366.222190` | action bracket | host histogram bracket described above |
| later AW W snapshot | `137706.50` | `1340.277810 s` after the MODE2 I2C tail | ordinary SHA `94839af1...`; `X=31868/21738/35229` |

The original W and AK ordinary/derived windows are byte-identical. The later
AW ordinary window differs and its recovered `X` mirrors are much smaller.
That comparison is delayed and sequential: it does not identify when the
controller fields changed, does not place either old or new values at the
MODE2 action, and does not prove MODE2 exclusively caused the change. The AW
read itself also consists of sequential fixed reads, not an atomic global
snapshot.

Most importantly, the unchanged labeled kernel rows and the changed
controller input window are from different qualified evidence channels and
different times. Existing evidence supplies no live dataflow tying them
together; the DP-register address interpretation itself remains conditional
as described above. Their combination therefore cannot establish that
content was constant during reset, that PrePD was stable, or that one
subsystem reset while another did not.

## Bounded conclusion

Within the retained AV kernel snapshots, the six labeled rows contain
**exactly the same numeric values immediately before and at the first
available group after the stock MODE2 lifecycle**. This rules out a change in
those particular emitted row payloads at those sampled times. Calling them
specific live DP-register values additionally requires the unproved copied
module/routine binding. The result does not rule out a change during the
unsampled interval, prove constant visual content, or identify a
controller/PrePD cause. The old W/AK and later AW controller snapshots only
add broad same-boot ordering; none is an event-time sample.

## Offline reproduction

`host-histogram-reset-reproduce.py` hash-pins the source report, AV manifest,
original artifact/trace, decoded trace, saved extracts, and all three
controller snapshot records/results/raw windows. It reconstructs the kernel
extracts from the original gzip payload, parses only complete ordered
six-row groups, finds the nearest bracket, compares every numeric field, and
emits the temporal limits above.

Focused verification:

```text
python3 host-histogram-reset-reproduce.py
python3 -O host-histogram-reset-reproduce.py
```

Both modes emit byte-identical JSON. No `assert` statement is used for an
evidence or safety check.
