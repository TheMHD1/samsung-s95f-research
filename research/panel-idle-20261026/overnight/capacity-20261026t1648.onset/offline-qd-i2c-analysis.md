# Offline QD I²C analysis of the 90-second capacity capture

This is an offline decode of the retained `trace`, not a new TV operation.  The
source trace SHA-256 is
`403d6951854ae14e312d894534a02b1fe42bb59e576ef58fe9ef8a44994058e7`.
It was decoded with the existing `overnight/decode-qd-trace.py` at SHA-256
`cc69c38cb78c94b3e044dc546ce1d0d6328b0c2f5aace308499ead0baf375be3`.
The resulting machine-readable derivative is
[`offline-qd-decoded.json`](offline-qd-decoded.json), SHA-256
`17e4671e5472b94c36e3cc34c9367320ecf3d62b59e81df4a019abd5993f11a9`.

## Decode integrity and scope

The trace header reports `107587/107587` retained/written entries, matching
the decoder's 107587 observed event lines.  It has no malformed I²C event,
no orphan result and 44 structurally complete bus-5/address-`0x76`
transactions.  Each has a Linux `i2c_result` return equal to its two messages.
This establishes that those recorded Linux transfers completed; it does not
establish controller acceptance, a state change, rendered frames, or emitted
light.

This is still an *incomplete* onset record: its top-level record reports an
unclosed AVOC ioctl-enter boundary.  Therefore the complete I²C transfer
inventory must not be promoted to a complete AVOC/ioctl attribution inventory.
The physical-state annotation is also explicitly unobserved.

The trace configuration filters the I²C write/read/reply events to bus 5,
address `0x76`; its result event is filtered only to bus 5.  The decoder did
not find an unmatched result, but the capture cannot inventory commands to
other addresses or buses.

## What was actually on the QD transport

There are nine identical AVEMonDIM sequences, at approximately ten-second
intervals from uptime 54773.399 through 54853.614:

```text
F3 01 00 00 00 00  -> command-status reply
F3 00 00 00 01 74  + 00 00 00 01
F3 01 00 00 00 00  -> command-status reply
F3 80 00 00 00 0D  -> 00 00 00 01
```

The status replies vary (`0x00008104`, `0x0000ad04`, or `0x00007c04` before
the write, then `0x00006904`), while every selector-`0x0d` reply is one.  The
existing exact QDF disassembly already identifies this full shape as the stock
`QDFTcon_GetPowerLevel` path: selector `0x174` with payload one is its query
prepare, and selector `0x0d` is its query result.  Thus these are regular
power-level getter polls, not evidence of a mute, frame-mode, dimming, or
screen-optimization setter.  As in the prior two-second decode, raw result one
is only the getter's controller-returned value; it is not a light measurement.

The other complete transfers are reads only:

| Issuer | Observed selector/read reply | Count | Attribution status |
| --- | --- | ---: | --- |
| `tcon-monitor` PID 1019 | `0x0c` -> `00170017` | 4 | selector meaning not statically named here |
| `sp-kpi` PID 7226 | `0x02` -> `472e0000` | 1 | selector meaning not statically named here |
| `sp-kpi` PID 7226 | `0x0c` -> `00170017` | 2 | selector meaning not statically named here |
| `sp-kpi` PID 7226 | `0x09` -> `00000000` | 1 | selector meaning not statically named here |

The four `tcon-monitor` selector-`0x0c` reads occur at 54773.722, 54794.734,
54815.745 and 54836.755: roughly a 21.01-second cadence.  That is a bounded
new static-analysis lead—map `0x0c` and its monitor caller—but it is not yet a
name, a policy transition, or a fault diagnosis.  The command-gate reference
only establishes that exact locking reads of `0xf3800000000c` have a special
command-skip exception; it does not name the selector or make its reply a
panel-health conclusion.

## No recorded candidate setter in this window

The complete address-filtered inventory contains no transaction for the
following named QDF controls:

| Category | Absent observed selector(s) |
| --- | --- |
| panel mute / frame / VRR | `0x164`, `0x160`, `0x150`, `0x15c` |
| off-sensing / EL sensing | `0x180`, `0x1a0` |
| dimming / low-power / screen-saver controls | `0x128`, `0x140`, `0xc0`, `0xc4`, `0xcc`, `0xd0` |

This is limited negative transport evidence for the captured 90-second,
bus-5/address-`0x76` window.  It cannot exclude an omitted bus/address,
commands outside the interval, a suppressed software request that never
reached I²C, internal controller behavior, or a physical-panel fault.  In
particular it does not establish that a black screen did not occur, that the
TV was visible, or that any repair is effective.

## Return-value boundary

All 44 Linux transfer results are complete (`ret == n == 2`).  This rules out
a short Linux transfer for these recorded transactions, but vendor protocol
acceptance and side effects are not exposed by `i2c_result`.  The status
handshake reply values likewise have no physical-brightness meaning established
by the retained QDF code.  No live query, setter, remote key, or power action
was performed for this analysis.
