# Y source-trace independent review closure

2026-10-27 UTC. Independent read-only audit and correction recheck passed with no remaining P1/P2 issues. The reviewer independently disassembled the seven pinned consumers, checked the literal inventory, four-lane geometry, two copy ABIs and destinations, and ran normal/optimized local verification. No TV, network or file-write operation was made by the reviewer; root records the returned result here.

Before acceptance, an incorrect named-provenance claim was removed. The `0xef94` getter returns fixed root `0x47010000`; lane-four stores at `0x47013adc..0x47013b18` are outside the AP_RTP registry row at `0x47012400` of length `0x100`. AP_RTP therefore is not a proved named consumer in this trace. Named consumers are AP_AG, AP_EXCO, AP_SPC and NPC_AP only.

The checker now covers ADR16 and positive/negative literal loads of 16/32-bit instruction width. ADR.W is explicitly outside automated coverage; independent complete-body disassembly found none in these seven bodies. The two actual Thumb32 PC-relative loads resolve to the nonprintable source constant. No whole-program source-name absence is claimed.

The 64-byte destination `0x2000b4e0` is a selected-package CPU literal, not a qualified live bus alias or independently established live allocation/content. Source producer, physical units, cadence and relationship to emitted light remain unknown.

Earlier consumer-census source SHA-256 `09c3d64de1137b1c55e271d5fd001821f9c00d36a914cbcc23cea458edcc540a`; report `cda152655ffa7d2f2c86c8658018affaa92a3412e3c5f0b50a722b97a51163d7`. Root's preserved consumer-census normal/optimized outputs are identical SHA-256 `778a3dd08d185cd2566710988b4947dda45b470fba2e030259a590c33c7f8086`. No source table/register read or firmware change was performed.

## Positive Pre-PD association added after the consumer census

Root then inspected the package's type-7 directory rather than only the ordinary RAM registry. The complete source table and companion lie inside the named Pre-PD record's first described range. This supersedes the earlier absence-of-named-block interpretation; the narrow fixed-literal reader census remains valid. The earlier JSON is preserved as consumer-census.normal.json and consumer-census.optimized.json and omits this later association.

Independent metadata review confirmed type7 dispatch to VA5c74 and the adjusted descriptor ABI: source offsets at+2c, destination offsets at+6c added to base+24, lengths at+ac and count+28. Two additional evidence gaps were corrected before final acceptance: the checker now explicitly asserts destination offset+6c=0, and pins the reviewed dispatch/loader instruction slices rather than only metadata. The report distinguishes manual semantic decoding from dynamic execution. No current load, producer, units or individual-field name is inferred from containment.

Final independent recheck PASS, no remaining P1/P2. Current source SHA-256 `2ea74933a733b1065dafb1dc230c569122b1e18be2f69b3ac99895bf83b516b6`; report `52774f5a67d1f927a05c71dd7788da2b4601091472ac9e3230b53692c89aacdb`. Accepted current verifier.normal/optimized.json outputs are identical SHA-256 `94dbe930770b381fc9a6a8be324a89e26eb932b111daa11a1aae02a99f0e6b3b`.
