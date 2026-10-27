# Independent fixed-descriptor review and target result

This is the parent-retained record of findings supplied by the read-only final
reviewer in this work block. The reviewer made no target calls and did not edit
implementation/evidence files. Root performed the target runs and saved this
record of the independent review.

The reviewer independently checked the ordinary target0x101 path: validation,
low-byte operation1 normalization, mode0 producer, remap flag0, direct source
RAM0x20261200 and length18. The independent descriptor reconstruction binds that
address to the live USB descriptor callback. IN completion subtracts the actual
count and rearms a12-byte header at zero remainder. Timeout/cancel rearming is
not proved; no retry or reset is implemented.

The original helper's five-file manifest, source, DLL and deployment wrapper
were reconciled. The first actual run passed23 injected cases and failed at
preflight with EndOfStreamException; Opened=false, Claimed=false, no OUT/IN,
private stage removed. Its16 authenticated root responses were independently
validated. The cached sysfs file advertises65553 bytes, but a bounded actual
read returns116; the size-based binary reader was unsuitable.

For revision2, the reviewer checked the isolated bounded-stream delta and four
new stream cases: partial nonseekable inputs0/115/116 and oversize117 rejection.
No Stream.Length/Seek is used; exact116 cached bytes are still required. All
five manifest rows and four host checks reconcile. Final build manifest SHA256:
9a9b6d13afe9daf12c42b7f7197f859b37a67b921bb7b11abbe8476ff21e4655.

The reviewer independently audited revision2's full actual record:

- 16 intact transport envelopes with strict JSON, authenticated root, correct
  model, host-assisted access, zero transport/remote status, no timeouts/stderr
  and exact command echoes.
- Reconstructed all three uploaded payloads from retained base64 command
  chunks; sizes/hashes match the manifest and local deployment files.
- Exactly one --execute invocation; saved stdout equals its response byte for
  byte, SHA256 ded8a32cc98be9bbba2302dfd69793db42471234919a06e8135f45bdadc70081.
- 27 fake cases passed. Expected boot persisted, uptime99909.27–99909.74.
  Actual phases: open25, claim0, OUT12, IN18, release0, close0; Accepted=true.
- Returned18 bytes12010002ef020140e8040120500201020301, SHA256
  f78bbb5a0e0a2fbe4944247d54be966c533da8ad91feac8df848106e9f54825b,
  matching packaged and cached descriptors. Cleanup verified STAGE_ABSENT.

Actual record SHA256:
27aa284dfcb17caca9ff44982ff8d4a72992cab00454a21f7fe0d1921f0632d6.

The narrow live direct-memory route is validated. Whole installed-image
equality, RT-window accessibility, physical panel state and a repair are not
established by this descriptor result. The parent additionally supplied the
reproducible `overnight/rt-telemetry-followup-20261027b/audit-known-descriptor-runs.py`
to reconcile both retained runs.

## Subsequent independent RT-prefix review

The same read-only reviewer separately cleared one explicitly experimental
32-byte RT read after checking the raw-source DMA path and the reset/config
mapping. It distinguished CPU readability from unproved USB DMA reachability
before the test and identified timeout/endpoint or controller reset as the
remaining disruptive failure boundary. No recovered payload/NV write path was
selected. The derivative's source, five-file manifest, wrapper and26 test
records were independently reconciled; the opaque-response acceptance scope
was explicit. The helper has no retry or reset operation.

After root executed that request, the reviewer independently validated all16
raw transport envelopes and reconstructed all three staged payloads. It
confirmed exactly one --execute, expected boot,26 fake cases, phases
open25/claim0/OUT12/IN32/release0/close0 with all errno0, Accepted=true,
returned-prefix.bin/base64/SHA agreement and STAGE_ABSENT.

- Record SHA256:dff0594e5aa2d04c9334f23990e585a3bc83514f081d69fc407cbc7b726163a3.
- Stdout SHA256:bc15f2d3d9bbe50b97ba829d8524cc6623259e49d811120c7723b725b75c2c80.
- Returned-prefix SHA256:0bc6e8374f85b3dc09ad1e3f863d9441f8136e5af36abd5c77c4a66c5e033821.

It independently compared packaged FILE0x183800..0x18381f and found exactly
byte differences+0x08:0->1 and+0x0e:0->1. Returned+0x0a halfword0 and
+0x10 halfword4 were verified. This confirms narrow live USB access to the
image0 RT window on this boot, with nonzero matching parameters corroborating
the region. It does not establish meanings of the changed bytes, physical
panel state, fault cause, image1 alias, whole-image identity or repair.
Root access in all these records remains host-assisted, not permanent.

Two other delegated analysis continuations ended with tool-side security
filter errors. Their incomplete work was not used as evidence. The concrete
review findings above were delivered and independently reconciled by root
before that final agent error; no new action was authorized by an agent error.
