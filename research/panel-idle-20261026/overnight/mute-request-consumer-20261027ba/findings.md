# BA: staged mute application and a fault-teardown connection

Recorded 2026-10-27 UTC. This pass was offline except for checking Arm's
public architectural reference. No TV command, controller read/write, new
target logger, UI/power action, patch, bypass or flash was performed.

## New positive source result

The [consumer trace](staged-consumer.md) closes the selected-image dataflow
between the ordinary mute setter and the normalized getter. The setter
stages derived MULTI/AP_EXCO+0x80 bits2/3. Consumer0x314c4 checks pending
bit2; requested bit3 selects an attempt to write raw2 or raw1 into the same
two-bit field that the getter reads at0x58200060.

Requested zero waits for three qualifying pending/zero-state invocations
after the setter resets its counter. This is an invocation count, not a
measured time or frame count. Pending clears after either a pre-read match
or an attempted write, with no post-write acknowledgement. Thus pending0
does not prove electrical acceptance or emitted light.

Root independently disassembled the complete consumer, its ordinary callback,
and the small fixed-register side-effect routines. The reproduced register
operations and logs agree with the source trace. The helper's earlier phrase
"third consumer invocation" was corrected to the narrower qualifying-call
condition before final validation.

## Connection to retained darkness

The consumer is directly called during startup and from body0x132c0. Root
then followed successful registration of0x132c0 to descriptor8, including
the claim success/failure distinction, the saved descriptor pointer and the
callback store. The existing fault-teardown body directly visits descriptor8
and passes its signed IRQ field to the interrupt clear-enable helper. The
architectural identification is supported by [Arm's CMSIS definitions](https://github.com/ARM-software/CMSIS_6/blob/main/CMSIS/Core/Include/core_cm4.h);
the source report records the exact bytes and the missing live IRQ value.

This supplies a selected-code mechanism by which a later ordinary request
could be staged while its usual apply callback is interrupted. It helps
explain why receiving a command need not recover output after a controller
fault. It is not proof that this mechanism caused the owner's failure:

- successful live registration and the actual descriptor IRQ are unobserved;
- the image/branch executed during a physical blackout is not established;
- indirect invocation or a later interrupt re-enable is not excluded;
- the physical purpose of the0x58200000/0x58300000 blocks is not identified;
  and
- the old W/AK/AW zero words show no pending request at those late samples,
  rather than demonstrating a request stuck pending.

No interrupt re-enable, callback alteration or fault-path bypass follows from
this analysis.

## What a useful next test must distinguish

Keep four events separate: a host request actually reaching the transport,
the setter staging it, the consumer taking its pre-read/write path, and the
physical panel returning. The existing `Failmode` entry and `F-Set`/`F-Clr`
log sites can support positive source execution evidence if captured; an
absent line in a wrapped ring is not a proof of no execution. An `F-Clr`
line would establish a write-path attempt, not post-write acceptance.

The existing unchanged W reader already includes the staged word, so no new
memory window or combined recorder is needed merely to inspect that word.
Its result remains a sequential snapshot. A late pending0 cannot prove which
consumer ran, and a sampled pending1 alone cannot measure callback cadence.
The actual next live experiment still requires the owner's current physical
picture state, with a fresh RT measurement, before any new action changes it.
The previous physical-state question remains unanswered; an old clean RT
sample cannot substitute for this pairing.

## Validation and scope

The final standard-library reproducer pins the package and prior AZ report,
consumer/setter/callback bodies, added claim/registration/teardown bodies,
table and literals, and positive call edges. Normal and optimized runs both
exit0 and emit identical output, SHA-256
`55b2ac585b5760e24e8fec77ab48a807e8239d1e8ebc6878f4d9465ebf3da82b`.
The emitted target-operation count is0. No new runtime claim is inferred from
those passing source checks. The blackout fix and permanent root remain
unverified.
