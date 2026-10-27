# Runtime maintenance state and actual QD output backend

All samples below were parent-operated, read-only acquisitions on October26.
**Physical picture state is unobserved.** They are not substitutes for the
earlier owner-confirmed Apps/control versus black capture, and do not prove
recovery or a permanent repair. No setter, memory write, ptrace attachment,
injection, process stop, remote key or power command was used.

## Daemon maintenance-state sample

Source identity in `runtime-deviced-maps-20261026T114137Z.json` freshly matches
the copied deviced SHA-256
`2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`.
Its first PT_LOAD has VMA zero; the offset-zero executable mapping gives
PIE bias `L=0x00b7c000`. Boot ID remains
`00000000-0000-4000-8000-000000000000`, PID675, executable `/usr/bin/deviced`.
The [observer map](../tcon-research/deviced-runtime-observer-map.md) derives
the pointer/selector addresses from the actual code rather than adjacent names.

[`runtime-deviced-state-20261026T114500Z.json`](runtime-deviced-state-20261026T114500Z.json)
records remote time11:45:01 and uptime36710.33..36710.37. It reads120 bytes.
Global tuple G1 brackets two copies of the object fields with G2. All paired
fields match. Fresh maps before/after match and bound each read.

| Field | Observed value |
| --- | --- |
| EL selector / pointers | selector0; legacy `0x1182208`; Y23 null |
| Off selector / pointers | selector0; legacy `0x1182f78`; Y23 null |
| EL local state, selected object `+0x30` | `0` |
| Off local state, selected object `+0x24` | `0` |
| EL OledDevice child | `0x1182250`; vptr `L+0x128a28` |
| EL timer child | `0x1182de0`; vptr `L+0x128a90` |
| EL PowerAdapter child | `0x1182a00`; vptr `L+0x128ab0` |
| Power-state index | `1`, the table's `lcdon` |
| Subsequent public getters | `GetPowerState="lcdon"`; `BurnInProtectionInProgress=0` |

The child vptrs match the exact legacy constructors/tables. The state words
are initialized/local state-machine values, not measured maintenance progress
inside the panel. D-Bus getters execute after the memory/maps bracket. The
sample is non-atomic; a change away and back is not excluded. The request
VCONF key and active timer sources were not sampled. This does not prove
maintenance never ran earlier, that no lower request is stuck, or that the
panel emits light.

## Actual base QD backend, then directly read slot/cache

The earlier active object was `QDDimming`, not `QDDimmingMNT`. The
[base-path audit](../tcon-research/qd-active-base-duty-path.md) now follows its
own vsync and final-duty routines. Its `this+0x10` backend is nullable;
the separate vendor call at `this+0x0c` requires inner word zero to equal1.
Those conditions must not be erased when describing the output path.

The11:45:41 pointer capture freshly hashes/maps AVE and reads64 bytes.
The11:46:13 child-vptr capture reads32 bytes with matching identity pairs,
but initially relies on that earlier map/hash approximately32seconds before.
It identifies RoseMQD at runtime, not the MNT backend. Both raw files retain
that cross-sample provenance. The stronger combined capture below removes
that particular map/slot gap for a new sample; it does not retroactively make
the earlier sample atomic.

[`runtime-qd-duty-cache-20261026T115305Z.json`](runtime-qd-duty-cache-20261026T115305Z.json)
records remote time11:53:06, uptime37195.51..37195.56. It reads108 bytes,
freshly matches disk AVE SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`,
and captures matching maps before/after. This is source-file identity,
not a hash of live executable memory.

| Meaning | Address / value |
| --- | --- |
| AVE bias | `0xf6b77000` |
| Active object | `0xf7203698`; QDDimming vptr `bias+0x59f2e8` |
| Inner shared object | `0xf63895d8` in `/dev/shm/shm_ave` |
| Backend object | `0xf7203630`; vptr `0xf711852c = bias+0x5a152c` |
| Backend class | `DimmingBackendRoseMQD` |
| Actual vptr `+0xd8` slot | `0xf7118604` contains Thumb pointer `0xf6d3d275 = bias+0x1c6275` |
| Backend `siDimLvl` cache | `0xf7122958 = bias+0x5ab958`; value207 |
| Inner `+0xa8` / `+0xac` | 207 / 207 |
| Inner AutoDim `+0x2a8` | raw0 |
| Outer initialized byte `+0x18` | 1 |
| Vsync gates `+0x39`, `+0x5c`, `+0x1b4` | 1,1,0 |
| Control word `+0x18c` | `0xffffffff`, including final-duty bit11 |
| Separate vendor gate, inner `+0` | 89, so the exact `==1` condition is false |

Global/header/interface/vptr/slot/cache/duty pairs all match. The control and
gate fields were read once; they can change during this non-atomic50ms
interval. The three early vsync guards are in their pass configuration at
their reads, but no function invocation or transport is observed by reading
memory. Earlier callbacks can reload/change control before final-duty dispatch.
No scalar above is calibrated luminance, voltage, current or measured emission.

## Concrete retry weakness, with an explicit incident boundary

The resolved RoseMQD function at0x1c6274 compares its candidate with
`siDimLvl` and skips both transports when equal. The latest sample contains
cache207 and working duty207. If it is invoked with that candidate while the
values stay unchanged, the equal-value branch skips the F3:0128 request and
following FRC I2C operation. This is normal steady-state suppression as well
as a mechanism that can retain a failed request.

The static weakness is precise: on inequality, instruction0x1c62ac records
the candidate **before** either output call. Neither reported error rolls it
back. The two statuses are ORed, but the vsync caller does not inspect the
final-duty return. A reported transport failure can therefore leave the cache
suppressing an identical retry. The FRC call uses the local word reloaded
after the TCON API; that mutable buffer need not still hold the original
candidate.

This is not evidence that a request failed here, that a retry was needed,
that the callback ran during the sample, or that the screen was black.
An unchanged cache value alone cannot select a repair. No cache was cleared
or invalidated and no duty request was forced. The useful next evidence is
the same fields plus transport results around an owner-confirmed transition.

## UI caller progress and remaining automatic prompt

The newly copied/hash-checked `org.tizen.menu.dll` contains a manual
Pixel Refresh page. The [UI report](../idle-research/menu-screen-optimization.md)
and bounded five-method IL probe close its buttons through the managed
privilege check to the native mode split: Start now passes0; Start after off
passes1. Displayed duration text is30 or60, and the latter button adds a
3000-unit toast argument. This does not identify the owner's automatic
60-second-response / claimed ten-minute Screen Optimization popup.

The initial candidate notification assemblies and welcome-mode binary had no
matching terms in the local searches; that does not exclude dynamic requests.
The first remote `strings` attempt failed because that command is absent;
a later `timeout`-wrapped search likewise failed because `timeout` is absent.
Those errors are retained in the discovery JSONs and were followed by a
successful bounded API-reference search. A missing English locale directory
also caused an inventory command's exit2 after its size/hash results; the
subsequent source transfers passed independent size/hash checks. None of these
tool errors is treated as negative evidence about the installed feature.

The follow-up ASCII/UTF16-shaped off-sensing/resource-key scan completed with
no stderr and found the menu, the already copied System framework pair, and
`/opt/usr/apps/com.samsung.SelfDiagnosis/bin/SelfDiagnosisTextResources.dll`.
That last file is an additional resource candidate; its contents have not yet
been inspected or connected to the automatic popup. The scan scope is the
recorded app-bin/framework DLL globs, not every installed file or dynamic path.

Independent reviewer findings and limits are preserved in
[runtime-control-independent-review.md](runtime-control-independent-review.md).
The whole-panel blackout diagnosis, reliable recovery/prevention, and untethered
root remain unfinished.
