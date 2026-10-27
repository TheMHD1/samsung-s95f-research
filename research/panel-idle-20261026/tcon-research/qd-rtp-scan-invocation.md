# QD image-1 RTP scan invocation and immediate sample producer

Recorded 2026-10-27 UTC. This is bounded offline analysis of the already
copied selected QD profile. It made no TV, root, network, server, controller,
USB, UART, flash, EEPROM, process, or capture call. It did not modify the
profile or prepare a controller command.

## Result

The packed-data scan is part of the ordinary packaged application, not an
unreferenced factory-only island. Normal application startup at linked VA
`0x1ba0c` unconditionally calls the registration routine at `0xaee4`. That
routine installs Thumb handler `0x434d` into interrupt/channel descriptor
index `0x1c`; the handler has a positive, unique call chain:

```text
registered handler 0x434c
  -> 0xc250
  -> 0xb644
  -> 0xb7ec
  -> packed scan 0xbd58..0xc040
```

The chain is nevertheless **conditional**, not a proof that ordinary video
always runs the scan or raises event `0x338`. The registered handler first
requires bit 3 in its supplied status word and a nonzero runtime byte at
`context_0x38e8 + 0x48`. The orchestrator then has object, caller-flag,
buffer-ready, mode, and global gates. On the packaged reset image, the
one-time buffer-refresh flag is set while all three immediate scan-request
globals are zero. The first eligible orchestrator call therefore refreshes a
sample slot and returns without scanning; later scanning requires runtime
state changes described below.

There is also a positive immediate producer for the three source slots.
Ordinary startup registers callback `0x18c95`; when that callback's runtime
conditions hold, `0x18ae8` makes two exact `0xb60`-byte copies from computed
addresses in the `0x60000000` MMIO window to the currently selected slot at
`0x20253002 + index*0xb68 + 8`, fills its small header, and advances the
selector byte at `0x20253000` modulo three. The copy source uses an unsigned
byte and a signed halfword from two descriptor records. Their units and the
hardware block behind `0x60000000` are not identified here.

These findings narrow the prior missing invocation edge. They do **not**
prove that the image was installed or executing during a retained incident,
that image-0 AP_RTP storage aliases image-1 RAM, that any particular runtime
gate was true, or that event `0x338` caused RT Protect or a dark panel.

## Inputs and coordinate convention

| item | bytes | SHA-256 |
| --- | ---: | --- |
| `overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin` | 5,242,880 | `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0` |
| `qd-rtp-primary-event-input-provenance.md` | 8,516 | `6ca8f906ed75288816a852a57b196b9667fe2db61a2ab41e659bcbd626225dac` |
| `qd-image1-context-initialization.md` | 12,386 | `e885c17d2d1092fd82d761ed4c7b1cd1627bcfa921bfba8027b515918da39c66` |

All code addresses below are image-1 linked VAs. Image 1 begins at container
file `0x40000`, its vector/link origin is file `0x40200`, and therefore:

```text
container file offset = linked VA + 0x40200
```

RAM and MMIO addresses are literal values and do not receive that bias.

## Normal-startup registration is positive

The reset/scatter path reaches application entry VA `0x1ba0c`, as established
by the pinned image-1 initialization report. The application entry performs
its initializations and then enters the permanent loop at `0x1bad2`:

```text
1ba12  bl  1bcc4       populate application context pointers
...
1ba7a  bl  b378
1ba7e  bl  c220
...
1baba  ldr r0, =40124000
1bac0  bl  aee4       unconditional registration
...
1bad2  bl  17a7c      ordinary permanent loop
1bad6  b   1bad2
```

`0xaee4` initializes several descriptors. The material descriptor is selected
with `r0=0x1c` at `0xb13a`, returned by `0x1b6c8`, configured, and assigned
the literal Thumb pointer `0x0000434d` at `0xb186..0xb188`. Thus `0x434c` is
not inferred from a coincidental raw pointer: the ordinary entrypoint calls
the routine that installs it as the descriptor's `+8` callback.

The same registration routine calls `0x195f8` at `0xaef6`. `0x195f8` stores
Thumb pointer `0x18c95` at `[0x20000468+4]`, saves root `+0x240c` at
`0x20000468`, and clears byte `0x20000460`. There is no direct `BL` to
`0x18c94`; its recovered reachability is through this registered callback.
The consumer of that callback table was not followed beyond this bounded
registration proof, so its cadence remains unknown.

This is evidence for a normal-boot installed path. It is not proof that every
iteration of the main loop invokes either callback. In fact, `0x17a7c` does
not directly call the scan chain.

## Handler and orchestrator gates

### Registered handler `0x434c`

The handler receives a descriptor/status pointer in `r0` and:

1. Requires bit 3 of `**r0` at `0x436a..0x4374`.
2. Uses byte `0x200004e8` as a one-time path: when it is zero, it sets the
   byte, updates/acknowledges the supplied status, and returns at `0x43a2`.
3. Runs the recovered setup bodies and a bounded wait around root fields
   `+0x3890/+0x3896`.
4. Loads a context through getter `0x38e8`; only when its byte `+0x48` is
   nonzero does `0x4446` call `0xc250`. Otherwise it calls `0x19730`.

Application startup at `0x1bcc4` positively populates the `0x38e8` getter's
pointer slot `0x200002cc` by calling `0x1bc24`. The identity and eventual
value of context byte `+0x48` remain runtime inputs, rather than reset
constants.

### `0xc250` to `0xb644`

`0xc250` obtains the root through `0x38fc` and the secondary context through
`0x38f4`. It derives two byte arguments passed to `0xb644`:

* byte `0x200004d8` becomes one only when root `+0x2400 == 0` and
  root `+0x240e == 1`; otherwise it becomes zero;
* byte `0x200004d7` is cleared when root `+0x2464 == 0`, and is set when
  `+0x2464 != 0` and `+0x2460 != 1` (the `+0x2460 == 1` branch retains its
  prior value).

Root `+0x2460 == 1` makes `0xb644` skip its scan body. Otherwise:

* byte `0x200004ce != 0` selects a refresh-only route: `0x18ce0(0)` selects
  a slot, the pointer is saved at `0x20000498`, `0x1c12c` may copy it to a
  stable buffer, the flag is cleared, and the function skips the scan;
* after that flag is clear, both caller bytes must be nonzero and byte
  `[context_0x3a88+2]` must be nonzero;
* scan dispatcher `0xb7ec` is called only if byte `0x2000049c != 0`, or
  halfword `0x200004aa == 1`, or halfword `0x200004ac == 1`.

Additional halfwords `0x200004d2`, `0x200004b2`, `0x200004d4`, and
`0x200004b0` gate a setup body at `0xb9f4`. They are kept as numeric state;
no semantic names or units are assigned.

### Dispatcher and packed scan

`0xb7ec` refreshes the two selected pointers using `0x18ce0(1)` and
`0x18ce0(0)`, may call `0x1c12c`, and always chooses one of three direct
calls to `0xbd58` once reached (`0xb84c`, `0xb874`, or `0xb88a`). Its buffer
choice depends on halfword `0x200004c4`, the selected-slot header at `+6`,
and secondary-context fields `+0x6c0/+0x6c7`.

The packed scan at `0xbd58..0xc040` refuses its scan loop when root
`+0x2410 >= 6`. Below that bound it selects thresholds/modes using root
fields and globals including `0x200004aa`, `0x200004ac`,
`0x200004c6..0x200004ca`, and byte `0x200004cc`. The downstream comparison
and event-`0x338` conditions are covered by the pinned primary-event report;
they are not relabelled here.

## Reset values demonstrate that scan is not automatic

The exact reset scatter stream for RAM `0x20000000..0x200004f7` reproduces
to SHA-256
`76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8`,
as independently pinned by the image-1 initialization report. Its relevant
initial values are:

| address | width | reset value | immediate role |
| --- | ---: | ---: | --- |
| `0x2000049c` | byte | 0 | scan-request input |
| `0x200004aa` | u16 LE | 0 | scan-request/mode input |
| `0x200004ac` | u16 LE | 0 | scan-request/mode input |
| `0x200004ce` | byte | 1 | refresh-only route initially selected |
| `0x200004d7` | byte | 1 | caller flag later recomputed/retained |
| `0x200004d8` | byte | 0 | caller flag later recomputed |
| `0x200004e8` | byte | 0 | handler one-time route initially selected |

Therefore normal startup installs the path, but packaged reset state does not
immediately authorize the packed scan. Runtime code must pass the one-time
handler route, establish the context gate, clear the refresh-only flag, and
set at least one scan-request input. External initialization can change these
values before a first observed callback; the table is not a live-state claim.

## Immediate writer of the three `0x20253000` slots

`0x18ce0` uses byte `0x20253000` modulo three and returns:

```text
0x20253002 + index * 0xb68
```

`0x18ae8` is a concrete runtime writer, not merely a selector. For each of
two ten-byte descriptor records rooted at literal `0x2000a60c`, it computes:

```text
source = 0x60000000
       + u8(descriptor + 2) * 0x195 * 0x10000
       + s16(descriptor + 6) * 3 * 0x400
destination = selected_slot + 8
```

It then calls copy body `0x334` with count `0x5b`. That body copies eight
32-bit words per iteration, so the exact requested copy size is:

```text
0x5b * 8 * 4 = 0xb60 bytes
```

The loop executes twice and writes the same selected destination; the second
copy therefore supplies the final payload on this path. It also copies small
descriptor fields to the slot header and increments byte `0x20253000`
modulo three. This establishes a direct MMIO-to-scan-buffer producer. It
does not establish the meaning of the descriptor byte/halfword, the MMIO
block, update cadence, or whether both computed sources are valid in a live
configuration.

Callback `0x18c94` reaches this producer only when secondary-context byte
`+0x6c8 == 3`. It also tests bytes in the structure at literal `0x2000a60a`,
may call initialization body `0x18d1c`, then calls `0x18d84` and `0x18ae8`.
The callback is installed during normal startup as described above, but its
invocation frequency and runtime condition are not proven by packaged bytes.

## Caller census and bounded negatives

A halfword-aligned Thumb direct-call census over the executable image-1
component found:

| callee | direct callers |
| --- | --- |
| `0xc250` | `0x4446` only |
| `0xb644` | `0xc2e6` only |
| `0xb7ec` | `0xb6fa` only |
| `0xbd58` | `0xb84c`, `0xb874`, `0xb88a` only |
| `0x1c12c` | `0xb682`, `0xb828` only |
| `0x18ae8` | `0x18cc4` only |

There is no direct `BL` to `0x434c` or `0x18c94`, consistent with their
positive callback registrations. This census does not exclude computed calls
through other tables, corrupted code, a boot ROM, or later-loaded code.

The `0x20253000` selector literal appears in the producer/selector bodies and
the reset scatter table. The runtime producer above closes the immediate
writer boundary for the selected slot. It does not prove that the produced
bytes correspond to image-0 AP_RTP. Image 0 loads AP_RTP into the numerically
different `0x47010000` window; no alias or cross-core bridge between that
window and image-1 `0x20010000`/`0x20253000` is established here.

## Exact bounded code slices

All slices below use linked-VA bounds translated by file bias `+0x40200`.

| linked VA half-open range | bytes | SHA-256 |
| --- | ---: | --- |
| normal startup `0x1ba0c..0x1bad8` | 204 | `e7806b27e0db5ca8a8f8b25b1ff58cf5fad18865f177c4a8368715b675f1b1b6` |
| registration `0xaee4..0xb338` | 1,108 | `53575dd76b4d9fea26b3ed42fea553064eded6d5f126c2b324aa5f6baf8e6bac` |
| handler `0x434c..0x4480` | 308 | `572c1c7a647033d7661431271df8f557de7d39c227f964af6ffb3240c0e56ffc` |
| `0xc250..0xc2ec` | 156 | `50c6338988042bdf09140937bd552d22e52240b729961970e9f286c6eeaaf32a` |
| orchestrator `0xb644..0xb798` | 340 | `77eaad94857db91496e71c80e7dd23f9509519fa5b0da7b2eac7a0119fba4ffa` |
| dispatcher `0xb7ec..0xb890` | 164 | `933064bf5a35c03a6d48db614f1cc4aec4cbadf9da35a30bdb4777168fb3372a` |
| packed scan `0xbd58..0xc040` | 744 | `dc9c513b47436ecce6297c99bb3083be667a254aa5fa210f170d53bd15c6a291` |
| MMIO producer `0x18ae8..0x18c10` | 296 | `6b428beae0cda70ec9f2b07e6f68560148c2b06b5ee72eb8c8e5e08b9aec6c41` |
| producer callback `0x18c94..0x18cda` | 70 | `2d4c18c7f439b3e2b2000ca704dc00da89c9ac06b06f35cba1048048ed5e7dae` |
| callback registration `0x195f8..0x19616` | 30 | `3df948ab1f327e3ea2297d0b04f4ab547a76c30fefcdb0fd88e4193532ad9b48` |
| selector `0x18ce0..0x18d18` | 56 | `619c8ebc99810e3d9ff88c57d18f5b36fcb76185851938d9b35f9c8fa7bd52ca` |
| stable-buffer copy `0x1c12c..0x1c1a0` | 116 | `3db9bd26b251decf450baa9f21d1d589253cfceaeb921ee4df371ebc0885e756` |

## What remains unproved

* The selected profile packages this code, but no live flash equality or
  image-1 execution measurement exists.
* Callback installation is normal-startup reachability; actual interrupt and
  callback cadence are not recovered.
* The live values of the status bit, context bytes, root fields, scan-request
  globals, thresholds, counters, and buffers are unknown.
* The `0x60000000` MMIO source and descriptor fields are not assigned physical
  units or a named sensor/engine.
* No alias is proved between image-0 `0x4701xxxx`, image-1 `0x2001xxxx`, and
  the producer ring at `0x20253000`.
* Nothing here establishes a panel-light transition, RT Protect cause, fault
  threshold, or recovery policy.

The narrow outcome is therefore: the event path is normally registered and
has a concrete conditional scheduler plus a concrete MMIO sample producer,
but event `0x338` is not an automatic consequence of ordinary video or of
the image-0 AP_RTP payload.
