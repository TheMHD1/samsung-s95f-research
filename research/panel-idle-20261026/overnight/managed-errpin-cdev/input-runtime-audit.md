# Independent runtime audit — one-shot ERR_DET GPIO input

Audit date: 2026-10-26 UTC

## Outcome

**ACCEPTED for the exact one-shot input contract.**

The immutable input record is `input-result-20261026a.json`, 143,316 bytes,
SHA-256
`59116acf54ebd8e492f6f94d792a1b40e33e78cc6acdbb72b4161d656f46ae5f`.
It records `accepted=true`, `read_usable=true`, `cleanup_confirmed=true`, one
shot, and no retry.

The accepted sample value was **1**.  Under the reviewed zero active-low
flags, this is a raw high logic level for gpio15 offset 5 at the sample.  It is
consistent with the vendor monitor's nonzero ERR_DET predicate, but it does
not establish connector polarity, physical panel emission, or fault cause.

## Independent raw replay

I decoded every one of the 11 retained base64 controller responses, parsed
the transport bytes as strict UTF-8 JSON, and confirmed exact equality with
the corresponding stored response object.  For every call, the retained
command echo and byte count matched; transport exit was zero; neither host nor
remote timeout occurred; client and remote stderr were empty; and the
response authenticated the expected model, root UID/EUID zero, host-assisted
persistence, and the system-file invariant.

I reran the frozen input runner's preflight and execution parsers directly on
the retained raw responses.  Both reproduced the stored objects exactly.  The
actual execute command contained exactly one `--input-once` selector.

The retained command sequence was preflight, private creation, six staging
chunks, one managed execution, postflight identity validation, and cleanup.
The last two results were exactly `POSTFLIGHT_IDENTITY_MATCH` and
`PRIVATE_REMOVED`.

## Actual result

- Boot ID remained `00000000-0000-4000-8000-000000000000`.
- Uptime advanced from 78292.71 to 78294.22 seconds.
- Helper PID/start identity was 8654/19573487; it exited zero without hitting
  its deadline.
- Managed runtime reported ARM32, four-byte pointers, little endian, and
  root UID/EUID.
- Chip open returned fd 26; CHIPINFO returned
  `gpiochip15`/`gpio15`/8 lines.
- Pre-request LINEINFO returned offset 5, flags `0x00000000`, and empty name
  and consumer.
- The one handle request returned fd 27, flags `0x00000001`, and lines 1.
- The single GET returned zero/errno zero, value 1, and all remaining 63
  bytes zero.
- Handle close and chip close both returned zero with errno zero.
- Managed stderr was empty.

The exact source and DLL were the same bytes independently reviewed before
execution.  No SET-values output was emitted, and the exact program contains
no SET-values call.  This record therefore supports one input request and one
GET only, not a control write or recovery attempt.

## Limits

- The record labels physical state `unobserved`; the owner's separate black-
  screen report was not synchronized to the read by a calibrated annotation.
- Value 1 is a point sample after the request's direction-input configuration,
  not a continuous history and not a proof that the value caused the screen
  state.
- The request had known ownership, descriptor-flag, and direction-input MMIO
  side effects.  Successful close proves release of the handle ownership, not
  restoration of prior direction or the transitory flag.
- No retry, repeated monitor, recovery action, protection bypass, or output
  operation is supported by this audit.
