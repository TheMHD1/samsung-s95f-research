# Independent review closure

Reviewed read-only on 2026-10-27 UTC. No TV, network, USB, root-agent,
firmware, UI, or instrumentation operation was made by this review.

## Final reviewed pins

- `historical-zero.md`: SHA-256
  `2b951e1a221d0272f16ed5efafe5dadd120820f624a43af4bb4f7f3b36a234e0`
- `verify-historical-zero.py`: SHA-256
  `01e2ae4944ad09f1c36fefdef2409ff78199586df1a228aa29fec6e847f696bc`
- normal and optimized verifier output: identical, SHA-256
  `9c3e6acdd44db8d4ec2671bf3ce4807dab31fcc08fda8090a7c81f8242fb566c`

## Result

PASS, within the report's final conditional scope.

The verifier independently reconstructs all 16 authenticated root-call
envelopes and all three staged runtime files, binds the one native invocation
to exact `OUT 12` / `IN 64`, checks release and close, binds the returned
64-byte payload and native `DataBase64` to SHA-256
`309cd7686044d75384b26fd389eef73add04f6a4651339151a0535fce3c4d3aa`,
and checks terminal `STAGE_ABSENT`. The raw halfword at bus-window offset
`0x30` is zero. Normal and `-O` verifier runs reproduced byte-identical
output.

The selected-image mapper disassembly positively maps selector zero and CPU
range `[0x20000000,0x20020000)` by adding `0x25000000`. The acquired current
mapper uses that branch only for core tag `0xa`. Because the historical read
did not sample the live selector/core tag, identifying bus `0x4500f0f0` as
CPU common-status `0x2000f0f0` correctly remains conditional. The same Linux
boot also does not prove uninterrupted controller/MCU lifetime.

The later host status is correctly retained only as
`kernel_output_written` with `controller_transaction_proved=false`. It is not
a second raw controller sample. Therefore the corpus proves the successful
raw-zero lower premise, not a raw-zero-to-raw-`0x10` transition. A later
write/copy/reinitialization follows only if a future or otherwise independent
proof establishes that a later `0x10` reflects the same controller field.

## Review correction retained

The initial report incorrectly said that, under only mapper and
same-controller assumptions, the retained later `0x10` could not be stale.
That omitted the necessary premise that the later value itself came from the
same controller field through a proved transaction. The final report fixes
this explicitly and now agrees with its structured result
(`partial_temporal_premise=true`) and the retained host-query limitation.

No physical picture state, V6 causality, unique writer, live executing-image
identity, or event-time status transition follows from this evidence.
