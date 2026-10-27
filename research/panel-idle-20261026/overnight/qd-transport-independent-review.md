# Independent review of transport, mute writers and offline decoder

Review was read-only against copied code and local evidence; no TV control or
new trace was executed. The review corroborated the PVCC-zero skip before the
mutex/I2C, the non-atomic temporary mute bracket, the cache/transport distinction,
and the central lifecycle callback wiring. It also caught the following errors,
which were corrected before a live control test.

| Finding | Correction |
| --- | --- |
| Focusing only on PVCC skip could imply other payloads always emit | Transport report now includes suspend, command-skip and TCON-state no-transport/return-zero gates and their distinct log literals |
| Pre-read and post-write handshake were incorrectly said to inspect the same byte | Pre-read uses raw final byte; post-write uses raw third byte and compares with its local checksum; full words remain undecoded |
| Resume recovery and direct zero were described as exclusive branches | Returning recovery path branches back to the direct zero/cache-clear; ordering is preserved in writer map |
| Generic ftrace event counting could hide malformed known I2C bodies | Decoder records line/event/body parse errors; capture-wide semantic completeness fails and no command labels/focus are emitted |
| Contradictory opcode/payload directions and read-reply flags were accepted | Decoder requires recovered two-message operation/direction/length shape and matching request/reply flags; raw evidence retained |

Thirteen offline integrity fixtures pass, including four new regressions for
malformed known event bodies, opposite read/write shape in both directions,
and reply-flag mismatch. These validate evidence processing, not hardware.
Both retained samples were regenerated: each still has four complete transfers
and no focused mute/frame/VRR operation. They remain short post-onset samples.

The PVCC report and bounded reproducer explicitly use the ELF symbol section:
DPMS-on is `tztv_frc_tcon.ko:.text.unlikely+0x1114`. Reading `.text+0x1114`
would attribute unrelated code to that function. No runtime guard value,
physical recovery, permanent repair, or exhaustive external MCU behavior is
claimed by this review.

Final re-review confirmed the corrected static findings and thirteen fixtures. A residual CLI display issue was corrected: stdout now includes semantic-capture completeness and parse-error count alongside ring accounting. A temporary malformed 1/1-event capture verified stdout reports ring accounting true, semantic completeness false, and one parse error. No TV access was involved.

A second lifecycle review corrected the locking-read state failure to-1 with
its exact0 command exception, added no-lock command-skip behavior without the
locking reader's0x0c exemption, and documented that suppressed reads leave
caller output untouched. The status checker's local-1 sentinel prevents
calling a skipped read a successful health reply. It also independently
confirmed the conditional gate constraints from the retained stock power query.

The final corrected-document read found no residual substantive defect in the two lifecycle reports or runtime evidence constraints. In particular, it confirmed that the stock-query inference is conditional and does not establish current flag values or physical light.

Independent raw review also corroborated the neutral sensing-control selectors:
0x180 off-sensing and0x1a0 EL-sensing, payload1/0 control forms. Both input1
routes request frame-mode0 and wait500ms before the sensing send; skip1 is
stored later. A new decoder fixture covers both without an active/success
claim; fourteen fixtures pass and retained samples have empty maintenance lists.

The service/PPI/impl-sec/static AVE chain was independently corroborated. The
previously underspecified publicAVE→TCON edge is direct, via exact PLT/GOT
relocations. Review also found reproduction coverage and prerequisite gaps;
the helper now prints the missing callback-table/relocation/public-AVE ranges
and documents the available Capstone/pyelftools environment explicitly. Its
expanded hash-checked offline run succeeded. No runtime callback-pointer value
or triggering service method has been observed.
