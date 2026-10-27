# Derived Failmode request consumer and fixed-register apply path

Recorded 2026-10-27 UTC. This is a bounded offline trace over the retained
selected QD profile. It made no TV, root, network, USB, I2C, controller,
register, UI, power, reset, helper, firmware, patch, bypass, protection, or
storage request.

## Result

The `MULTI/AP_EXCO +0x80` word identified in the preceding ordinary-mute
trace is a staged request word with a positive consumer in the selected image:

| derived word bit | bounded role proved here |
| ---: | --- |
| 2 | pending/apply flag; the consumer returns immediately when zero and clears it after a pre-read match or an unacknowledged write attempt |
| 3 | requested Failmode state; one selects the `F-Set` path and zero selects the delayed `F-Clr` path |

Linked function `0x314c4` consumes those bits and updates the same fixed
field read by host `F3:00` selector `0x164`:

* requested one attempts to make bits 23..22 of word `0x58200060` equal
  **2**;
* requested zero attempts to make the same field equal **1**, after three
  qualifying consumer invocations counted at RAM `0x20000ed8`; and
* the consumer then clears derived bit 2.

There is no post-write readback or acknowledgement before the pending bit is
cleared. This closes a selected-package setter-to-getter dataflow, not proof
that hardware accepted the write. The host getter returns one only for raw
field value two, so the packaged intent is:

```text
request 1 -> attempt raw field 2 -> host readback would be 1
request 0 -> attempt raw field 1 -> host readback would be 0
```

The source also shows associated writes to the separate fixed block at
`0x58300000`. It does not name either block electrically, establish current
package execution, or show emitted light.

## Input and object identity

The selected profile is 5,242,880 bytes with SHA-256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image 0 uses `stored FILE = linked VA + 0x200`.

The starting [ordinary mute receiver report](../mmio-block-attribution-20261027az/ordinary-mute-receiver.md)
has SHA-256 `78ee9e039f6b7f317cf17323e7e01b3bdc2b78f81664a93eb312908537069541`.
It established:

* getter VA `0xe76c` returns derived `MULTI/AP_EXCO` CPU base
  `0x200158a8`, extent `0x3ec`;
* selector `0x164` writer calls `0x3a078(0|1)`;
* `0x3a078` sets pending bit 2 and writes requested state to bit 3; and
* selector `0x164` reader normalizes `0x58200060[23:22] == 2` to one.

Ordinary AP_EXCO at CPU `0x2000ff14` is a different object and is not used as
the staged word in this report.

## Consumer control flow

The complete linked body `0x314c4..0x3155b`, stored FILE
`0x316c4..0x3175b`, is 152 bytes with SHA-256
`88056c17683e9e4d529463155630cdea966464dab7fdb24c4009edb5e03ca8ee`.
It obtains the common object at CPU `0x2000f0e0` and the derived object at
CPU `0x200158a8`, then performs the following finite state machine.

### Pending gate

At `0x314d4..0x314de`, it loads derived word `+0x80`, extracts bit 2, and
returns when that bit is zero. Therefore a late zero word is positively
compatible with no pending apply; it is not a persistent record that no
request occurred earlier.

### Requested one: `F-Set`

When bit 3 is one:

1. read `0x58200060[23:22]`;
2. if it already equals two, skip the fixed-register writes;
3. otherwise call linked `0x20744`;
4. replace `0x58200060[23:22]` with two;
5. emit exact event-log literal `F-Set\n`; and
6. clear derived pending bit 2 without reading the field back.

The complete `0x20744..0x20769` body has SHA-256
`92da54bbc75c2d0df03110b6dc126731a8b14a1dfe7a1327496bba0c9132d000`.
It uses fixed base `0x58300000` and performs:

```text
0x58300000: clear bits 16..19, then clear bit 0
0x58300018: set bit 15
```

These are exact register-like fixed-address operations. No panel, rail,
timing, scan, PWM, or emission label is assigned to them.

### Requested zero: delayed `F-Clr`

`0x3a078(0)` resets RAM counter `0x20000ed8` to zero before the consumer is
later invoked. In the consumer's bit-3-zero path, each qualifying invocation
that reaches this path increments that counter. Counter values one and two
return immediately with pending bit 2 still set. On the third such invocation:

1. read `0x58200060[23:22]`;
2. if it already equals one, skip the fixed-register write;
3. otherwise replace that field with one, store `0xabababab` at common object
   CPU `0x2000f0e0 + 0x158`, and emit exact literal `F-Clr\n`; and
4. clear derived pending bit 2 without reading the field back.

The common-object store is a positive downstream field update but remains
semantically unnamed. `0xabababab` is the exact 32-bit value materialized by
the instruction rendered as `mov.w r0,#-0x54545455`.

Before this delayed path, `0x3a078(0)` has already called the complete linked
body `0x20770..0x20787`, which copies:

```text
*(u32 *)0x58300018 = *(u32 *)0x20000d40
*(u32 *)0x58300000 = *(u32 *)0x20000d4c
```

Thus the `0x58300000` restoration is immediate at request staging, whereas
the `0x58200060` transition attempt to one waits for three later qualifying
consumer invocations. Source ordering does not establish frames, wall-clock
duration, or that every callback reaches this path.

## Positive invocation paths

A finite halfword-aligned direct-`BL` census finds exactly two direct calls to
the consumer in selected image 0:

| callsite | source-backed context |
| ---: | --- |
| `0x39b58` | startup executes `movs r0,#1; bl 0x3a078; bl 0x314c4`, staging requested one and immediately attempting it once |
| `0x13306` | body `0x132c0` calls the consumer only on the branch where bit 3 of the word reached through its caller-supplied descriptor pointer is one |

The startup pair is linked `0x39b50..0x39b5b`, SHA-256
`a4d978d090d3080cc32641b94d3fa01af968268448cc30ef9455cf9c9fd19020`.
It occurs before the ordinary recurring loop at `0x39bda..0x39c4c`.

The second call is inside linked body `0x132c0..0x13345`, SHA-256
`2e472ef163d2a285a67628abaef6195cdc824f781654e471f4e9659eb51e7a25`.
At `0x132ca..0x132d4`, that body loads a word through its input descriptor,
extracts bit 3, and skips the larger branch—including the consumer—when the
bit is zero. This is a positive invocation gate; the descriptor's semantic
name, schedule, and live invocation are not established here.

The direct-call census is not an indirect-call absence proof. It is sufficient
to establish one startup attempt and one gated ordinary body. In particular,
the selector writer itself stages the word but does not call the consumer
synchronously.

### Registration and a matching fault-teardown resource

Root independently followed the registration rather than inferring a runtime
IRQ from the callback address. At linked0x1e702, input8 is passed to0x13aa8.
On success, that helper marks descriptor8 claimed and returns8; its failure
path returns0xff. The next lookup uses table base0x20000948 and20-byte stride,
saves the descriptor pointer at0x20000884, and stores Thumb callback0x132c1
at descriptor+8 at0x1e79c. The binding is conditional on successful claiming;
the code shown does not establish its live result.

The already traced fault-teardown body0x96d8 directly looks up descriptor8
at0x9724..0x9726, loads its signed IRQ field at+4, and passes it to0x1b0e8.
That complete helper performs the indexed bit write through base0xe000e180.
For a valid nonnegative device IRQ, this is the standard NVIC clear-enable
operation: Arm defines NVIC base0xe000e100, ICER offset0x80 and the same
indexed bit write in its [CMSIS core header](https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Include/core_cm4.h).
Unlike the reference CMSIS helper, this selected body has no nonnegative
argument guard; the actual descriptor IRQ value was not sampled here.

This is a positive selected-code connection: the fault path visits the
resource used by the ordinary mute-apply callback, conditional on successful
registration and a valid live IRQ. It supplies a mechanism by which a later
request could be staged while its ordinary apply route is interrupted. It
does not prove that this occurred on the TV, that the callback was the only
possible invocation route, or that no later path re-enables the interrupt.
Neither changing that resource nor bypassing fault teardown is proposed.

The independently checked additional source slices are claim0x13aa8..0x13ad5,
registration0x1e702..0x1e79d, teardown0x96d8..0x9745, lookup0x38c24..0x38c37
and disable helper0x1b0e8..0x1b0ff. Their complete hashes and positive literal/
call checks are preserved in the reproducer. No storage or return-guard
branch was followed to obtain this connection.

## Pending versus consumed evidence

Within this selected code, the strongest software distinction is:

| observation | bounded interpretation |
| --- | --- |
| derived `+0x80` bit 2 = 1 | request remains pending, including the first two qualifying zero-request invocations |
| derived `+0x80` bit 2 = 0 | no request is pending at that sample; it may never have existed or may already have been consumed/cleared after an attempt |
| raw `0x58200060[23:22] = 2` | selected getter returns one; compatible with requested-one state |
| raw field = 1 | selected getter returns zero; compatible with requested-zero state |
| raw field = 0 or 3 | selected getter also returns zero; host readback alone cannot distinguish these from raw one |

The retained W, AK, and AW derived-object snapshots all contained zero at
`+0x80`, so they show no pending request at those late sequential samples.
They did not capture the raw two-bit register field, were not event aligned,
and had no physical-picture observation. Consequently they cannot prove
which apply path last ran, whether a fixed-address write was accepted, or
whether the panel was lit.

## Limits

This report proves a selected-package request/consumer/getter mechanism. It
does not prove:

* running controller equality with the selected package;
* execution of either ordinary invocation path during a blackout;
* acknowledgement, readback, or physical acceptance of either attempted
  `0x58200060` write;
* that fixed addresses `0x58200060` or `0x58300000` directly control OLED
  emission rather than another output state;
* the wall-clock delay represented by three qualifying consumer invocations;
  or
* a repair, patch, bypass, or safe forced value.

No new access or modification recipe follows from this source result.

## Reproduction

Run locally only:

```text
python3 staged-consumer-reproduce.py
python3 -O staged-consumer-reproduce.py
```

The standard-library checker pins the package and AZ input identities,
complete positive function slices, roots/literals/log strings, startup order,
consumer/callee edges, and the finite direct-call contexts. It constructs no
transport request and performs zero target operations.
