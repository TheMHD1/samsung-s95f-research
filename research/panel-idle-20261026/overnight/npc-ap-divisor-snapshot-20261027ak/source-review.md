# AK source/build review before target execution

2026-10-27 UTC. Two independent read-only audits passed for one bounded
invocation: native/ARM32 ABI and source/wrapper/build contracts. Root also
reproduced 26 native zero-I/O fixtures, 34 wrapper checks under normal and
optimized Python, and the exact zero-operation dry geometry.

Reviewed manifest SHA-256
`333461c953490ca11c0c788018cc2f0ca4f3d44fc1161e4183558da8eb817211`;
Program `45f1dc7f908fbb0b2fd621ad89b54de86e1fb4478274f9d05bddddf8a01a6245`;
wrapper `11bc47c92c1e46cea5c3d8e6f419a5f607c1377a5359a3a939c8c54368ccfadc`;
DLL `72377393d057d70bb2894e362210136b1b1621296d17133c47901eea8a0675bb`.

The only vendor operation is fixed target1014500d730/8: OUT12 then IN8,
with two-second transfer timeouts. No write/reset/retry/dynamic address is
available. Phase is unknown before each ioctl; uncertainty stops subsequent
headers. Positive short prefixes are retained without decoding. Release and
close are required for acceptance. The wrapper retains the authenticated
envelope and native bytes before semantic acceptance and removes its private
stage only after a complete exact Ready result.

The source/address qualification is AJ. Interpretation is conditional on
selector-zero NPC_AP lineage, with no NPC-specific live pointer/default gate.
The result does not establish physical light, an event tuple or atomic state
with another object.

Nonblocking review observations: host tests do not fake-drive every staging
and cleanup main() step, although the inherited lifecycle was manually
audited; exact successful IN8 also truthfully populates fields named PartialData.
No source blocker remains. Root authorizes the one passive invocation within
the owner's existing unattended-testing instruction. This review is not a
runtime success record.
