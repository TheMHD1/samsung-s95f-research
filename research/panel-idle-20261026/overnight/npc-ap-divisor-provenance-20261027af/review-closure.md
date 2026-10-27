# AF independent review closure

2026-10-27 UTC. Independent source/math review initially identified four
issues. Root corrected them, and the independent recheck passed with no
remaining P1/P2 findings in those areas.

- Model the low-halfword STRH truncation before the cap comparison. The new
  65535-squared/divisor1/cap6 regression yields zero. W's small-value
  predictions are unchanged.
- Require positive count for the array writer's final-row description.
  Count zero instead forms rows[-1]; the dispatcher has no positive minimum.
- Qualify both outgoing copy edges: NPC_AP+19a==1 and +19c==0 selects zero
  writes to the roots, rather than copying the three low fields.
- Distinguish the metadata-declared 0x53e-byte payload from the 0x540-byte
  allocation. Pin type4, logical base140000, destination offset0, copylen53e
  and the exact declared payload hash. No loader execution or live object
  initialization is proved by that metadata.

Accepted verifier SHA-256
`c7109a19a443788513d84289e1c707175cc2c3cfe54530b9820874133b5faffa`;
report `a1adb0c07a03a65f7801a1fd2893cad5ddf4ee2d4e3ff60481d26b3b4fc274b9`.
Normal/optimized outputs match SHA-256
`36d9fda014e4536ad4b77bf83994dfa947428b2f96e90f39c60d29c5666666ab`.
The superseded pre-review outputs remain as verifier.pre-review.* with hash
`3b558a0b1576a79d659583f68d8c722438a151b4d3af22f86533f18eaa2acb79`.
They are historical results, not accepted exact-formula evidence.

The read-only reviewer checked source/load/call-census boundaries and the W
arithmetic as well. Root records the returned review here. No target,
network, USB, code or parameter action occurred in this audit.
