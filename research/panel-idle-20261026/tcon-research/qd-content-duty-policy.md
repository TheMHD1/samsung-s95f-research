# QDMNT content/duty path: a brightness ramp is distinct from panel power

This is an offline audit of the exact copied `libave.so.0.1`, QDF module and
TCON API module, with SHA-256 guards in `qd-content-duty-reproduce.py`.
It does not establish a live object/vtable pointer, a physical blackout cause,
or a recovery. No TV call or display setting was issued for this audit.

## AutoPowerOff is an arithmetic ramp in this implementation

The name `QDDimming::m_AutoPowerOff()` at Thumb code address `0x1740f0`
does not, by itself, identify an instruction to switch the TV or TCON off.
Its inspected body contains arithmetic, state stores and optional logging;
its external calls resolve to logging/shared-memory/file-log helpers. It has
no direct panel-power/mute/sensing call.

`QDDimming::SetAutoDim(int)` at `0x172a34` stores its input into the inner
state field `+0x2a8` when initialized. The ramp reads that same field at
`0x174110` and compares it to 1 at `0x174118`. Its static counter resolves to
link-time address `0x5be420` (PC-relative base `0x5be410`, field `+0x10`).
This counter is distinct from the error-detect recovery count.

For ordinary nonnegative in-range arithmetic, the recovered operation can
be written approximately as:

```text
floor = trunc(inner[0xfc] * 1024 / 100)
desired = inner[0xa8]
if inner[0x2a8] == 1:
    if counter < 300 and desired > floor: counter += 1
    else: counter = 300
else:
    counter = clamp(counter - 1, 0, 300)
inner[0xa8] = floor + trunc((desired - floor) * (300 - counter) / 300)
```

The actual code uses 32-bit shifts/multiplication and signed high-product
division constants `0x51eb851f` and `0x1b4e81b5`; this pseudocode is not an
overflow-equivalent emulator for arbitrary inputs. The first division occurs
at `0x174114..0x17412a`, counter branch at `0x174130..0x17419c`, blend at
`0x17414a..0x17415c`. This is a 300-invocation counter, **not a proved
300-second, five-second or three-second timer**. The call schedule and actual
counter values at the owner's incident remain unknown.

## The QDMNT final-duty route has explicit limits and its own wire command

`QDDimmingMNT::m_SetFinalDuty2D()` (`0x19abe8`) calculates the requested
scalar, stores it to inner `+0xa8` at `0x19ac82`, then calls the ramp through
PLT at `0x19ac86`. Afterward it applies a lower limit of 51 on the ordinary
`inner+0x188 != 1` path (`0x19ac96..0x19aca0`), or 12 when that field is 1
(`0x19adbc..0x19adc2`), then an upper limit of 1023
(`0x19aca4..0x19acb4`). These numbers are host scalar limits, not measured
OLED luminance, voltages, health guarantees or a demonstrated safe threshold.
They do not rule out an internal panel response to content or drive level.

It passes that scalar at request `+8` to backend virtual slot `+0xd8` at
`0x19ad10`. The copied `DimmingBackendRoseMQDMNT` vtable resolves this slot
by an `R_ARM_ABS32` relocation at `0x5a185c` to Thumb symbol
`DimmingBackendRoseMQDMNT::t_Set2DFinalDuty` (`0x1c9e75`, code `0x1c9e74`).
Raw on-disk vtable entries are zero; reading them without relocation would
give a false answer. This proves this class's static dispatch, not the live
backend pointer.

The backend reads request `+8` at `0x1c9e88`, compares its static `siDimLvl`
cache (`0x5acb94`), and on a change:

1. Stores the desired value into that cache **before** the calls
   (`0x1c9ea8`).
2. Calls `ave_frc_write_i2c(0x42b48, value)` at `0x1c9eac`.
3. Calls `ave_tcon_api_send_onecommand(0xf30000000128, &value)` at
   `0x1c9ebc`, OR-ing both return values.

That AVE constructor at `0x2519d8` packages operation18, payload in word1,
the command's high16 in word2 and low32 in word3 into ioctl `0xc010749f`.
The matching API operation18 jump lands at `.text+0xf170`, reconstructs the
48-bit command and calls interface slot `+0x3a0`; QDF's initializer registers
`QDFTcon_SendOneCommand`. Its normal dispatch at `0xd1e4..0xd1f0` calls the
same gated write helper analyzed elsewhere. Debug command/cache configuration
can alter its payload before that dispatch. This is a **dimming-level
request** observed in code, distinct from mute selector0x164, frame0x160,
low-power0x140, screen-saver0xc4 and sensing0x180/0x1a0. Its full write packet
is `F3 00 00 00 01 28`, with a four-byte scalar payload.

The prewritten backend cache introduces another requested-versus-applied gap:
if the downstream write fails or is suppressed, an identical backend request
can skip another attempt. That is a code mechanism, not evidence it happened
at the blackout. No value or cache was forced. No electrical meaning for
zero/12/51/1023 is inferred from the name `siDimLvl` alone.

## Scene policy and screen-saver are additional, separate paths

`DimmingBackendRoseMQDMNT::t_SetQdSeneDetect` (`0x1c9704`) packages source,
mode and policy inputs into FRC request values and conditionally calls
`ave_frc_write_i2c` for addresses `0x42618`, `0x41ec4`, `0x47024`, and
`0x47028`. Its direct external-call inventory contains those FRC writes and
logging/shared-memory helpers, not a direct QD power/mute/sensing setter.
These addresses are arguments to the stock FRC API, not a documented MMIO
pinout or authorization to poke a register. The content algorithm behind
them remains unresolved.

`t_GetMotionThresholdFromBackend` (`0x1c8f78`) selects and returns a scalar
threshold based on supplied flags/source categories. It contains no direct
power/mute call. That does not mean the overall motion/dimming policy has
been reconstructed.

The screen-saver backend at `0x1cb2d8` converts a nonzero cached factory
setting into public brightness request107 (`0x6b` at `0x1cb2fe`), unless
request `+0x10` is zero, which selects0. This **107 is not wire brightness
107**: AVE operation32 forwards the logical scalar, and
`QDFTcon_SetQdSsBrightness` at `0xec00` maps101..107 to1..7. Logical1 selects
the cached factory value; logical0 selects0; other inputs are forwarded to
the low-level 0..7 validation. Thus both request107 and request1 can lead to
wire7 on a factory7 configuration through different selection rules.
The lower helper sends `F3 00 00 00 00 C4` and rejects values outside0..7.
Neither zero nor seven is established as “disable the physical panel.”

Independent review identified two further requested-versus-applied caches
in this brightness route. The backend calls the AVE setter at `0x1cb356`
and stores its desired cache at `0x1cb382` without checking the return.
QDF calls its lower helper at `0xecb4`, retains the return for reporting at
`0xecb8`, then nevertheless stores the mapped desired value at `0xecbc`.
An identical later request can skip retry at either layer after a failed or
suppressed operation. These mechanisms do not prove a failed brightness
write occurred during the owner's blackout.

One older dispatcher description needed correction: `m_SetScreenSaver`
requires inner `+0x450 != 0`, but its source/flag checks compute a boolean
**field inside the request**, rather than suppressing the whole backend call
when false. The QDMNT backend's inspected control flow selects brightness
from request `+0x10`; the computed boolean at `+8` does not gate those
screen-saver setter calls in this body. There is no sparse-page timer here.

## What the retained incident evidence does and does not say

The physically visible Apps capture already contains APL0/Lamp0 telemetry.
The later physically black B0/B1 captures also contain those values, so those
logs are not emitted-light measurements and cannot trigger an automatic fix.
The ring histories show screen-saver brightness0 before the visible capture,
then7 and0 before B0, then7 before B1. They do not record an onset-aligned
0x128 payload or prove any one screen-saver value caused persistent black.
Repeated history lines are not independent new operations.

For the next observed transition, the I2C decoder now labels selector0x128
`dimming-level-request` and retains it together with0x140 and the screen-saver
family in a separate `dimming_focus` list. Its narrow `focus` list still holds
mute/frame/VRR selectors. Inspect all three focus lists and **all transfers**,
rather than concluding “no dimming change” from an empty mute/frame list.
The two retained short post-onset traces contain only the known power-query/
status family, not this initiating-edge evidence. Sixteen decoder fixtures
pass, including retaining raw duty/SS scalars without light/acceptance claims
and refusing an incomplete dimming transfer as semantic evidence.

## Reproduce

```sh
cd ${S95F_EVIDENCE_ROOT}/panel-idle-20261026
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-content-duty-reproduce.py > tcon-research/qd-content-duty.raw.disasm
```

The script verifies the three exact input hashes, resolves class relocations
and PLT imports, honors ARM `$t/$a/$d` mappings so literal pools are not
reported as executable instructions, and prints bounded disassembly. It
requires Capstone5.0.7, pyelftools0.33, `c++filt`, and
`aarch64-linux-gnu-objdump` already available on the controller.
