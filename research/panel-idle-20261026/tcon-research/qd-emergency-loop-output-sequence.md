# QD packaged-image selector-`0x10` emergency-loop sequence

Recorded 2026-10-27 UTC. This is a bounded, offline control-flow review of
already retained bytes. It made no TV, root, network, controller, I2C,
EEPROM, eMMC, GPIO, display, firmware-update, or emulation call and changed
no earlier evidence.

## Result

For the exact selected 5 MiB asset, common error entry `0xb860` has two
materially different outcomes after selector `0x10`:

1. every path which reaches the guard first performs the selector action,
   persistent-history attempts and selector-status store;
2. it then tests two magic halfwords exactly once; and
3. it returns to the ordinary recurring main loop only if the halfwords are
   already `0x1234` and `0xabcd`. A mismatch enters `0xb8dc..0xb8f8`, whose
   back edge has no condition and never rechecks either magic value.

Thus clearing the initiating `+0x240a` bit, changing the stored selector, or
making a guard match *after* the branch cannot return this synchronous
execution path to the normal loop. Once the mismatch arm is taken, an
external control-flow event such as a controller restart/reset or an
asynchronous handler that deliberately transfers control would be required;
no such escape is present in this bounded function.

The emergency loop is not total firmware inactivity. It repeatedly runs six
service calls, five of which also occur in the ordinary main loop. Conversely,
the rest of the ordinary main-loop schedule is no longer reached. The source
therefore proves diversion of normal main-thread upkeep, but it does **not**
identify the omitted routines as physical panel-output maintenance, establish
the meaning of the four touched MMIO blocks, or prove that this path caused the
owner's black picture.

## Inputs and bounded method

```text
overnight/selected-qd-profile-copy-20261027b/
  F_RSM1_BN9659934B_COMMON.bin
size   5242880
SHA256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

The reviewed prior findings are:

```text
qd-live-rt-protection-candidates.md
  b565bccaf3ca47063e6a938b86b54a2c5ae73a9f953b47916882f64e583762de
qd-profile-rt-status-wire.md
  6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e
qd-profile-rt-wire-independent-review.md
  71972c04e8004a59307e08b261aac39774ce167e334aeeb93c254ad91d1eaf1e
```

This review decoded the complete `0xb860` and selector-`0x10` action bodies,
the six direct emergency-loop callees, their directly selected helper bodies,
the ordinary recurring loop, and the low-level I2C event body. Direct-call
censuses and fixed literals were checked against the complete retained file.
This is not a whole-program CFG: computed callbacks, exception entry,
dynamically populated IRQ numbers, and code in the separately linked second
image remain bounded gaps.

Relevant exact ranges hash as follows:

```text
0xb860..0xb8f9    40e434612828833aa7b433798a352a99c766cbb47351d2cb42ba364a868d2c6a
0x14b10..0x14bbb  5fcc7bea9301c9aa6b815a92fff05ac97769daf64e9eccbe1bac23f5667e3d18
0x25d24..0x25d5f  94f4a4f1407e57b0e80f80fa4b16b353b6c41dd7f98d566203b916f1f1387b48
0x39dda..0x39e4d  e2d3cc629921b0cdccdd3151a4b545dbb594c5b214ff87faf9e7c81c03bd8936
0x12ac4..0x12dbd  5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85
0x12e60..0x12ebf  33a8f28329f000ab1ce39302dcae0ad872485fd99f987ebfbea669309ad66b03
```

## Exact pre-guard sequence

`0xb860` retains the input selector in `r5` and the message pointer in `r4`.
For selector `0x10`, its ordering is:

1. `0xe878` returns second-object address `0x2000ff14`, which is saved across
   the operation.
2. `0x300d4` stores a global `1`, calls `0x217bc`, and sets bit `0x1000` in a
   third object's word `+0x7c`.
3. `0x26458(0x10)` returns without taking its selector-`0x40` special case.
4. `0x98d8` performs interrupt/peripheral teardown described below.
5. The inlined priority operation writes byte `0x20` to architectural Cortex-M
   NVIC priority address `0xe000e400 + 0x1b`. This changes IRQ 27's priority;
   it does not enable that IRQ.
6. `0x14b10(0x10)` executes the selector-specific action.
7. `0x2b964(0x10)` overwrites common-object halfword `+0x10` with `0x0010`.
8. Two logs run, followed by `0x206f8`, which stores zero at RAM
   `0x20000850` and one at RAM `0x20000878`.
9. Only then are the two return guards tested.

This ordering matters. The emergency loop is selected after the MMIO,
EEPROM/eMMC and visible-status changes, not instead of them.

### Interrupt teardown before the selector action

`0x98d8` first calls `0xda34(8, 0)`, requesting teardown of logical resource
8. If that resource's runtime state is active, the zero arm performs an
architectural NVIC clear-enable bit write and lower teardown; otherwise it
returns a failure which `0x98d8` does not inspect. `0x98d8` then looks up
20-byte RAM table entries for indices
`0x1c`, `0x1e`, `0x1b`, `7`, `8`, and `0x10`, loads the signed IRQ byte at
each entry's `+4`, and passes it to `0x1b2e8`. For a valid nonnegative IRQ
number, that helper writes the corresponding bit to NVIC `ICER` base
`0xe000e180`.

The actual signed IRQ bytes reside in runtime RAM and are not fixed in this
asset. The source therefore proves execution of an ICER disable sequence
derived from those six records, but not the concrete IRQ set, whether every
runtime value is valid, or whether the TCON host-I2C event line is among it.
The subsequent priority-byte write for IRQ 27 is not an enable operation and
does not close that gap.

## Selector-`0x10` action and persistent attempts

The selected arm `0x14b70..0x14b88` executes in this order:

1. clear second-object halfword `+8`;
2. call `0x25d24(1)`;
3. store 32-bit `0x10` at `0x4013400c`;
4. call EEPROM counter/update function `0x9b68`; and
5. call eMMC-region path `0xa230`.

`0x25d24(1)` itself first calls `0x3ffc`, conditionally calls `0x4014` when
common halfword `+0x36` is zero or one, calls `0x10fe0` with common halfword
`+0x92`, and then performs the two final 32-bit stores:

```text
0x40132010 <- 0x00000080
0x40131010 <- 0x00000004
```

The earlier direct helper `0x3ffc` stores `8` at `0x40130010`.
Conditionally, `0x4014` stores `0x200` at `0x40132010` before the final
`0x80` store to that same address. `0x10fe0` makes three lower internal calls
around a four-byte argument; no hardware name was recovered for it.

`0x9b68` increments the retained RT-history byte, attempts an EEPROM-labelled
four-byte write/readback at address `0xe0`, and returns after a match or ten
failed comparisons. It uses `cpsid i` only around each write/read call and
executes `cpsie i` immediately afterward; it does not leave interrupts
globally masked when it returns. `0xa230` requests the already documented
`0x1400`-byte eMMC-region write path. Neither return value is tested by
`0x14b10`.

The addresses and store values are exact. No recovered register description
supports naming any of `0x40130010`, `0x40131010`, `0x40132010`, or
`0x4013400c` as a panel rail, panel reset, backlight, scan, timing, or output
register. Their physical effects remain unknown.

## One-shot guards and non-returning arm

After the common selector store and logs, `0xb860` obtains common-object
address `0x2000f0e0` through `0xe870` and compares its first halfword with
`0x1234`. Only if that matches does it compare the first halfword of the saved
second object at `0x2000ff14` with `0xabcd`.

```text
if *(u16 *)0x2000f0e0 == 0x1234 and
   *(u16 *)0x2000ff14 == 0xabcd:
       return
else:
       branch to 0xb8f8
       repeat 0xb8dc..0xb8f8 forever
```

The two values are magic guards only; their lifecycle and semantic names were
not recovered. The mismatch branch jumps to the loop tail first, then the
tail unconditionally branches to its head. The top-level loop control never
rechecks either guard or the initiating `+0x240a` bit and never targets the
function epilogue. Some retained state-machine callees inspect bits of common
selector `+0x10`, but no recovered callee edge can redirect this enclosing
loop to its epilogue.

## What continues and what stops on the synchronous main path

The ordinary recurring block `0x39dda..0x39e4c` schedules, in order:

```text
39604, 30550, 171c0, 216d4 [live RT poll], 272ec, 139f8, 2efc,
278ec, 1d968, 7408, 5858, 20710, 20db4, 2e6ec, 5180, 1f5e4,
24e5c, cc94, optional 9db8/9d9c, then back to 39dda
```

If `0x216d4` calls `0xb860(0x10)` and either magic guard mismatches, control
never reaches `0x272ec` or any later ordinary-loop call. It instead repeats:

```text
3ad34(1), 171c0, 39604(0), 278ec, 20710, 1f5e4
```

The retained calls have bounded observable roles:

* `0x3ad34(1)` sets byte `0x20000e30`; getter `0x38cf0` reads that same byte,
  and both `0x278ec` and `0x20710` gate their work on it.
* `0x171c0` services bounded byte queues/states and calls lower helpers for
  selected state bytes.
* `0x39604(0)` drains two bounded ring-like byte buffers through lower byte
  sinks.
* `0x278ec` performs a timestamp-gated call to `0x27924(0)`.
* `0x20710` advances time/counter and persistent-write state when enabled.
* `0x1f5e4` calls eight common-object state machines (`0x20358`, `0x1f190`,
  `0x1f390`, `0x1f50c`, `0x1fc10`, `0x2002c`, `0x1ff38`, `0x20274`). This
  exact dispatcher is also part of the ordinary loop.

These are active status/queue/timer/persistence state machines, not a sleep
loop. At the same time, thirteen ordinary-loop calls plus the post-loop state
dispatch are omitted. No symbol or register binding in the bounded evidence
establishes which omitted or retained call directly sustains pixels. The
strong supported statement is that normal main-loop scheduling stops and a
smaller emergency schedule replaces it, not that all output logic or all
firmware execution stops.

## Host-I2C/status servicing remains conditional

The `F3 80 ... 08` parser/serializer already traced at `0x12ac4` is called by
`0x12e60`. That body processes a hardware-event object, calls `0x12ac4` or an
alternate parser according to common halfword `+0xc0`, performs peripheral
acknowledgement work, then writes an IRQ bit to architectural NVIC clear-
pending base `0xe000e280`. Its shape is an interrupt-style event callback.

There is no direct synchronous call from the emergency loop to `0x12e60` or
`0x12ac4`. Within the directly decoded selector path, no permanent global
interrupt mask was recovered; the explicit `cpsid/cpsie` pairs in `0x9b68`
are balanced before the emergency loop. Accordingly, interrupt-driven host
servicing can in principle coexist with a spinning main thread.

That is not a proof it does so here. The exact callback/vector registration
for `0x12e60` was not recovered from the flat asset, and the runtime IRQ bytes
disabled by `0x98d8` are unknown. A responsive host status command therefore
would not by itself disprove emergency-loop entry, but the source also cannot
guarantee host-I2C remains enabled after this path.

## Bounded interpretation for persistent black

This sequence supplies a source-backed mechanism for persistence at the
controller-software level: after the live RT bit is observed, the selected
action runs and a magic-guard mismatch permanently diverts the ordinary main
thread. Reverting a menu, clearing a later status value, or waiting does not
provide an in-function exit. That is compatible with a picture which remains
black while some status/queue or interrupt-driven functions continue.

It is not a causal diagnosis of this TV. The selected asset has not been
read back from the live controller, the two guard values were not sampled,
the MMIO meanings are unknown, and no retained routine is positively bound
to pixel generation or a physical panel power state. The code supports only
this recovery boundary: if the live controller took the mismatch arm of this
exact function, returning the ordinary main thread requires control-flow
restart/intervention outside the loop. It does not identify which safe stock
operation, if any, performs that recovery, and it is not a patch or bypass
recipe.
