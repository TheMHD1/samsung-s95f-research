# Retained numeric context after the V6 RTP fault

The bounded two-window read completed on the same Linux boot with the RT
fault still latched at `0x1001`. It obtained 64 bytes from bus `0x47010f00`
and 256 bytes from `0x47012400`. Four exact bulk transfers, interface
release/close, terminal `ReadyForHeader`, and exact private-stage removal
all passed. Nineteen authenticated root calls include staging, the zero-I/O
self-test, the single native invocation, and cleanup. No memory setting,
logging gate, threshold, protection, firmware, UI, or reset was changed.

The terminal uptime is `117834.25`, about 1,926.80 seconds after the V6
observation ended. The windows were read in sequence. These are late retained
values, not an atomic reconstruction of the event instant. The image-1 CPU
alias remains conditional on the unsampled live core tag; the primary claim
is the actual bus-window content.

## Bytes and ordinary numeric interpretation

| Bus address | Unsigned LE halfword | Conditional packaged-code interpretation |
| --- | ---: | --- |
| `0x47010f04` | 0 | latest subtractor latch `T` |
| `0x47010f06` | 54 | latest mode-6 low accumulator latch |
| `0x47010f08` | 44 | latest shared non-mode-6 low accumulator latch |
| `0x4701240a` | `0x1001` | latched RT fault |
| `0x47012430` | 200 | mode-1 default `fp` |
| `0x47012432` | 0 | mode-2 `fp` |
| `0x47012440` | 0 | mode-4 `fp` |
| `0x470124c0` | 200 | mode-6 default `fp` |
| `0x470124c4` | 40 | alternate mode-1/mode-6 `fp` |
| `0x4701249e` | 1 | predicate enable gate |
| `0x470124a0` | 160 | source-count comparison field |
| `0x470124a2` | 0 | conditional BPFLG latch |
| `0x470124d2` | 1 | subtractor-helper selector |
| `0x470124d6` | 10 | retained parameter, no new units assigned |

Logging gate `0x47012406` remains 0. The first 64 RT bytes exactly equal the
V6 restored post-block. Root field `+0x2410` remains 4, but it is not the
ordinary caller's CPU-global mode selector. It cannot establish the event
mode. A zero subtractor latch is preserved as measured; it does not establish
the event-time subtractor or a defect in the helper.

The immediate packaged predicate is `r7 > fp`, with `r7` the low 16 bits of
the selected 32-bit accumulator. Using the late latches only yields the
following hypothetical comparisons:

| Hypothetical mode/selection | Late score and limit | Numeric result |
| --- | --- | --- |
| 1, default | 44 > 200 | false |
| 1, alternate | 44 > 40 | true |
| 4 | 44 > 0 | true |
| 6, default | 54 > 200 | false |
| 6, alternate | 54 > 40 | true |
| 2, implemented branch without a recovered direct caller | 44 > 0 | true |

This table deliberately retains incompatible and compatible cases. The
shared non-mode-6 latch does not identify which mode last stored it, and the
alternate selector was not read. Neither a small limit nor a zero limit is
evidence of bad configuration. Selecting the 0 or 40 case as the cause
would outrun the measurements. Event-time mode, selected limit, and the
accumulator immediately before the compare remain the important missing
observations.

All five candidate limits and the five additional gate/parameter fields in
the comparison also exactly match the AP_RTP initializer in both the selected
package and the saved controller backup. Their complete 256-byte initializer
payloads are identical, SHA256
`3a16ea440b59a8e778c01ddfc429b110fbdd03e55c953954ce99337ebf5b3937`.
The AP_RTP directory records are also byte-identical; the separately verified
loader resolves source `0x80000+0x103800` to this payload. The configuration
headers themselves differ in version text, so this equality is confined to
the verified directory record and payload, not the whole firmware. The
measured zeros are thus present in both retained baseline artifacts. This
does not prove which values were used at the event instant, that the current
whole executable matches, or that its mode selectors are correct.

## Provenance and reproduction

The read used the independently cleared helper manifest
`c64d77d8356fde3867490155095e1ef240151634f1c72a529a43970055f5aa7e`.
Raw execution, native stdout/stderr, self-test and cleanup records are in
`fault-context-after-v6/`. Context SHA256 is
`0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439`;
RT SHA256 is
`91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9`.

`decode-fault-context-after-v6.py` reproduces every halfword, all six
comparisons, prefix equality and timing from pinned raw artifacts. It has
zero target operations. The complete result is
`fault-context-after-v6-decoded.json`. See the separate reader source review,
numeric predicate review and runtime review. Existing frozen captures and
manifests were not rewritten.

The investigation has moved from a host fault name to a captured controller
event, its exact ordinary numeric predicate, and a retained parameter
snapshot. It has not demonstrated recovery, prevention, current whole-body
firmware equality, or a repair to the physically damaged panel. No flash or
permanent-root change was performed.
