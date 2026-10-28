# Candidate code-window fingerprints: three exact matches

Recorded2026-10-27 UTC. One root-controlled invocation used independently
reviewed manifest550be573257e5d8e726fbf5b4d223a4eeb82e03376edde5dd8062a0eeb37662c
on the pinned Linux boot00000000-0000-4000-8000-000000000000.
Terminal uptime was122877.73. The record retains20 authenticated root calls,
one native execution and the preceding native50-case self-test.

All six bulk transfers were exact. The parser endedReadyForHeader; release
and close succeeded; strict cleanup returnedSTAGE_ABSENT. No retry, reset,
UI request, firmware/code write, protection change or physical observation
occurred. The source review and separate runtime review are in this directory.

| returned mapped window | bytes | result | SHA256 |
| --- | ---: | --- | --- |
| 46001e60 | 512 | exact selected/current stored match | 8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49 |
| 460038c0 | 64 | exact selected/current stored match | 0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb |
| 4601bb60 | 576 | exact selected/current stored match | 035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8 |

Root separately compared all1152 returned bytes, rather than only trusting
native match booleans, against the selected package with FILE=VA+40200.
The first window contains the entire472-byte predicate; the second contains
the source getter38e8; the third contains the ordinary low-address mapper,
the distinct lookup wrappers and startup pointer stores. These are three
nonadjacent local fingerprints, not a whole-image checksum.

This is the first positive raw code-view evidence for these exact bodies.
Together with the earlier live pointer neighborhood and V6 event text it
substantially strengthens the local source reconstruction. It does not prove
which core's PC was executing those bytes, whole-image identity, event-time
execution, a writable code region or a physical panel outcome. The reader
explicitly reports executing_code_identity_proved=false and
whole_image_identity_inferred=false.

The newest ordinary source-lineage correction remains in sibling
ap-exco-source-read-20261027m/source-lineage-erratum.md. The callback getter's
source is the third AP_EXCO object450158a8, not the two ordinary raw blocks.
A new fixed source diagnostic is being qualified separately. This capture
scheduled no additional target operation or code modification by itself.
