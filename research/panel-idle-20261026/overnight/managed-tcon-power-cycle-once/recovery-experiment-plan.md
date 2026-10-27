# One-shot stock MODE2 recovery experiment plan

This is an evidence plan, not an execution record. No TV, root, device, GPIO,
controller, power, or network action was performed while preparing it.

## Fixed action

At most one reviewed helper invocation would submit the stock exact-build
envelope `operation=41, mode=2, words2/3=0`. If the intended callback is live,
QDF calls its ordinary off lifecycle once and its ordinary on lifecycle once.
There is no helper retry, loop, protection bypass, EEPROM write, flash update,
or alternate reset command.

## Evidence bracket

Before any future action, establish and retain one shared-boot evidence set.
An awake-owner experiment should include:

1. explicit owner-visible picture state and audio state;
2. accepted ERR_DET status plus its matching raw kernel log when available;
3. independently read ERR_DET GPIO state;
4. the fixed selector-0x128 result, classified only as kernel output;
5. AVOC/QD sampled source and cache fields already covered by the reviewed
   observer; and
6. a passive trace/vlog/kernel capture already armed, with an action marker.

If the owner remains asleep, the existing explicit last-known black report may
anchor a separately labeled **physically unobserved technical experiment**.
That variant still requires the technical status/pin/selector/AVOC evidence
and passive trace bracket, but it cannot claim that MODE2 restored light or
picture until a later owner observation. It does not require waking the owner
or a new permission prompt.

Run the one helper only inside the selected passive bracket. Retain its complete raw
root responses, exact start/end boot and uptime anchors, managed output,
return, deadline, and verified cleanup. Then reacquire the same status, pin,
selector and AVOC/QD fields, plus an explicit owner observation of emitted
picture/light. Do not substitute audio, cached fields, logs, screenshots, or
ioctl return zero for that physical observation.

## Classification

Return zero means only `kernel_return_zero_only`. It can arise from a missing
interface/callback without an action. A nonzero return is an incomplete lower
error aggregate, not a complete hardware verdict. Cache changes can precede
failed rail work, the on path can publish power/PVCC state after ERR_DET, and
several downstream status/recovery returns are discarded.

Recovery requires a temporally bracketed owner-visible picture after the
action, with the technical capture accepted and no identity/loss/cleanup
failure. Even then, the result is a one-shot association, not proof of the
original fault cause or prevention.

## Stop and rollback boundary

Never automatically repeat MODE2. On timeout, identity drift, cleanup failure,
or an unchanged dark state, preserve evidence and stop. Rollback means only
the owner's ordinary stock TV lifecycle under coordination; it does not mean
an EEPROM write, firmware flash, protection suppression, hidden setting, or
invented compensating controller command. The stock MODE2 implementation
itself has no compensating rollback if its off or on half fails.
