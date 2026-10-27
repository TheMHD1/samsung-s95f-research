# Independent root review of packed-buffer origin

Recorded 2026-10-27 UTC. Reviewed the final report 77ea5a70ebfcdfa18daf010147b357de04565e4d0a58854e40120378a511ca1d
and verifier abab487ebbedfcaee5934a96530103318c9da6f6864152bca1961297a4351706.
This reviewer did not author those two files. No target or network operation
was made. This review is outside frozen D7 evidence.

The verifier completed successfully. Separately, direct Thumb disassembly of
the original package confirmed the source-address construction, signed load,
CPU copy call, ring selector load, per-iteration index advancement and loop
boundary. In particular, VA18be4..18bf6 increments the stored selector modulo
three before VA18bf8 increments the descriptor index and VA18bfc loops. Thus
the two iterations use consecutive slots, not the same selected destination.

Selector18ce0(1) uses current selector modulo3; selector18ce0(0) uses
(selector+1)mod3. After the two iterations, these correspond to initial(s+2)
and initial(s), respectively. The copy body334 loads eight words and stores
eight words per iteration for count5b, establishing b60 bytes and a CPU copy.

Root initially flagged a header-table issue at VA18b46: boolean header+1
comes from descriptor+0, while header+2/source arithmetic use descriptor+2.
The author independently confirmed the distinction and the final report
explicitly contains it. Prior/current snapshot language is limited to fields
+2..+9, not the whole ten-byte record. That issue is closed in the reviewed
hashes.

A separate direct read of metadata FILE83c00 confirmed EXCO_PAR2_S0 and its
address word58601400; the callback root58601408 is that base plus8.
This is an association with a configuration parameter record, not a physical
stream identification or proof of current-boot loading. No DMA, framebuffer,
sensor, loopback, physical coordinate or electrical unit is established.

No blocking issue remains in these bounded claims. The additive report
supersedes the older same-slot sentence while preserving the original file.
