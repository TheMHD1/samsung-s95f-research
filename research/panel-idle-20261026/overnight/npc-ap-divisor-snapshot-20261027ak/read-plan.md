# NPC_AP divisor snapshot read plan

This directory is reserved for a separately reviewed, one-shot retained
capture. No target call has been made by this implementation task.

The proposed native request is fixed:

```text
target       0x101
bus address  0x4500d730
length       8
header       0101000030d7004508000000
USB bulks    one exact OUT12, then one exact IN8
```

The raw response must be saved as `npc-ap-offset-14-through-1b.bin` before
cleanup. Response offsets `+0/+2/+4/+6` are conditionally labeled object
halfwords `NPC_AP+0x14/+0x16/+0x18/+0x1a`. The first is context only; the
last three are the ordinary consumer's divisor inputs. No returned value,
including stored defaults `1024/1024/1024`, proves live object identity.

Acceptance requires exact header and input counts, terminal
`ReadyForHeader`, release and close, strict authenticated stdout/stderr
framing, a single native invocation, and exact raw hash/length reconstruction.
The native monotonic start/end ticks bracket the USB request pair. They do not
make the sample event-aligned or atomic with another object.

Any short/error/exception is rejected without another vendor header. A
positive short IN prefix of at most eight bytes remains in native output but
is not decoded. No retry, write, reset, alternate address, pointer
dereference, configuration change, or cleanup of an ambiguous stage is
allowed.
