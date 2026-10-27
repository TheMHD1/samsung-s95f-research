# Fixed ordinary selector-window capture plan

This is a new bounded acquisition, separate from the completed retained-score
read. The owner authorizes unattended diagnostics. It does not change any
flag, threshold, protection, configuration, UI, power state or firmware.

## Fixed geometry and purpose

| Order | Target | Bus start | Bytes | Header |
| --- | --- | --- | ---: | --- |
| 1 | `0x101` | `0x470004a0` | 68 | `01010000a004004744000000` |
| 2 | `0x101` | `0x47000bc0` | 16 | `01010000c00b004710000000` |

There are exactly four synchronous bulk transfers. The second header is
forbidden after any incomplete or uncertain first transaction. There is no
retry, memory write, reset, signal, gate operation or caller-selected address.
Only a complete, exact, known `ReadyForHeader` result permits private-file
cleanup after retaining raw evidence. An ambiguous result preserves the
stage and stops further vendor traffic.

The first window contains the proposed mode halfwords at offsets `0x0a`
and `0x0c`, and the complete root pointer at offset `0x40`. Interpretation
as image-1 CPU mode fields requires that same-response root to equal
`0x20010000`. A mismatch does not make a completed USB transaction uncertain;
it rejects the CPU-field interpretation while preserving the raw bytes.

The second is expressly a **candidate bus window**. Its byte `+7` is the
mapper-predicted counterpart of the alternate-threshold CPU flag, but no
local live anchor or live secondary core tag has been measured there. Return
its bytes even if zero or unexpected, with CPU interpretation still
candidate-only. A nonzero byte matching a packaged default is corroboration,
not a new proof of the alias or an event-time value.

## Address and identity evidence

The selected image-1 scatter allocates CPU `0x20000000..0x200004f7` by
decompression and `0x200004f8..0x2000e19b` by zero fill. Both proposed
CPU-side spans lie within those allocations. The exact copied mapper has a
non-A branch adding `0x27000000`; the previous returned bus window at
`0x470004c0/64` contained root `0x20010000` at `0x470004e0`. These are the
specific support for the candidates. The separate AP_RTP `0x4701...`
configuration does not cover them and must not be widened to justify them.
See `rtp-mode-ram-read-qualification.md` for the independent boundaries.

The newly traced ordinary AP_EXCO callback copies `source_context+0x3d8`
to CPU `0x20000bc7`. The selected packaged source byte is `0x14`, which would
select the alternate limit if copied and retained at runtime. Neither its
live value nor that callback's event-time execution is established. The
capture therefore keeps the bus/CPU distinction even if byte `+7` is 20.

## Current protocol boundary and implementation

The last vendor session was the accepted retained-context read, with exact
OUT12/IN64/OUT12/IN256, release/close, final `ReadyForHeader`, and private
stage verified absent. It preserved the latched `0x1001` fault. No vendor
request, reboot, panel cycle or UI action followed it while this plan was
prepared. The new helper must enforce the same boot, descriptor/device/FD
identity and one-shot finite engine, pin its local source/build manifest,
pass fake short/error cases, and receive independent review before use.

Both samples will be late and sequential. They cannot reconstruct V6's
instantaneous selector values, establish the current physical picture,
identify a named Samsung setting, or demonstrate a repair. Their purpose is
to qualify an ordinary state reader and narrow the selector hypotheses for
the next coordinated event capture.
