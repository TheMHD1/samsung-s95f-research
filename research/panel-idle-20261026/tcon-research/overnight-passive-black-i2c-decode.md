# Passive post-onset I²C capture: exact decoding

Evidence source: `overnight/passive-black-i2c.trace`, 2 seconds, 739 entries,
verified without trace-buffer overflow. There was no fresh simultaneous physical-screen confirmation; the black-state filename reflects the prior owner report. The trace was passive: it observed
the existing `AVEMonDIM` process and did not issue an I²C request.

## Observed stock sequence

At 8988.809 seconds the trace records this Linux-completed transaction sequence on
the QD transport (`i2c-5`, vendor helper address argument `0x76`):

```
F3 01 00 00 00 00  -> 00 00 81 04
F3 00 00 00 01 74  + 00 00 00 01
F3 01 00 00 00 00  -> 00 00 69 04
F3 80 00 00 00 0D  -> 00 00 00 01
```

The intermediate command write is a two-message I²C transfer in the trace:
the first message is the six-byte QD address (`F3 00 00 00 01 74`); the second
is its four-byte payload (`00 00 00 01`).

## Exact module match

This is not an inferred “watchdog” or generic alive operation.  It matches
`QDFTcon_GetPowerLevel` exactly at `qdf_tcon.ko:.text+0xd088`:

```
d098  cbz  x0, error                 // requires caller output pointer
d0b4  mov  x0, #0x174
d0b8  mov  w2, #1
d0bc  movk x0, #0xf300, lsl #32      // F3 00 00 00 01 74
d0c0  mov  w1, w2                    // payload = 1
d0c4  bl   m_send_cmd_with_lock
d0cc  mov  x0, #0xd
d0d0  movk x0, #0xf380, lsl #32      // F3 80 00 00 00 0D
d0d4  bl   m_read_cmd
d0d8  ldr  w1, [sp,#0x2c]
d0dc  str  w1, [x19]                 // return raw level to caller
```

The `F3 01 …00` reads immediately before and after are generated inside
`m_send_cmd_with_lock` (`.text+0xbba0`): they are stock command-status
handshakes, not a separate AVEMonDIM policy command.  The changing replies
`0x00008104` then `0x00006904` are therefore command-status values; this
module does not label either bit pattern as panel brightness, a fault, or a
physical emission state.

`F3 80 …0D` returns `1`.  In context that is the raw value returned by the
stock `QDFTcon_GetPowerLevel` query.  It is strong evidence that the
stock query returned raw power-level value `1` during this post-onset
sample, whose simultaneous physical state was not freshly confirmed.  It is **not** evidence that OLED pixels are emitting:
the getter neither samples pixel light nor validates a rendered frame.

## Userspace ioctl correlation

The trace brackets that I²C sequence with a successful ordinary ARM
`ioctl(22, 0xc010749f, ...)` from AVEMonDIM.  (The raw trace prints syscall
arguments in hexadecimal, so its displayed `16` is decimal file descriptor
22.)  The exact matching wrapper in
the captured `libave.so.0.1` is `ave_tcon_power_level(int *)` at
virtual address `0x25c9ac` (the ELF symbol value is `0x25c9ad`; clear its ARM
Thumb bit before disassembly).  It constructs a 16-byte request whose first two words are
`0x21` and `0x00000000`, calls that ioctl, then copies the returned second
word to the caller's output pointer.  This establishes that the passive
capture is a stock AVE power-level *query*, not a watchdog reset or an
unsolicited control operation.

That wrapper contains no output-control, mute, low-power-mode, or
screen-saver write.  Its syscall returned zero in the trace, while the QDF
response written to the output was `1`.  This is attribution only: directly
calling the private ioctl outside AVEMonDIM's already-initialized AVE context
is not a supported diagnostic or recovery action.

## Consequence

This is a useful negative result.  It ties the retained post-onset QD traffic to an
ordinary stock *power-level query* that succeeds, rather than to an observed
QD power-off (`QDFTcon_SetQdTconPowerControl`), QD mute command (`…0164`), or
LPM rewrite (`…0140`).  Together with the already-observed LVDS-on, mute-zero,
PMIC/HSM-good and advancing composition, it narrows the remaining issue to a
state that is below or outside these host-visible health/power indicators.

The repeated userspace ioctl `0xc0086626` seen around the trace is an
eight-byte FRC-family control ABI call that completes with zero.  This capture
does not expose its userspace buffer, so it is not sufficient by itself to
name that ioctl.  The named QDF operation above is established independently
from exact wire bytes and QDF machine code; no unsupported ioctl needs to be
called to obtain that conclusion.

The later [gate evidence constraints](../overnight/qd-gate-evidence-constraints.md) explain what actual query traffic conditionally establishes about passing the broader driver gates, and what it cannot establish about the PVCC mute-zero guard or physical emission. The pre-read and post-write handshake use different bytes; see the corrected transport audit.
