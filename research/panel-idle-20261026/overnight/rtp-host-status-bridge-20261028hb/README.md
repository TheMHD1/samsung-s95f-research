# External RTP fault to host RT Protect status: positive source bridge

**The selected controller source returns the exact AP halfword written by the RTP emergency path for the host's F380/register08 request.** This closes a specific source data dependency: root fault lowbit → emergency reason `0x10` → AP+0x10 → four-byte status response → host bit4. It is not an inference from two similarly named bits. It does not prove that a particular historical live `0x10` sample followed this branch, or that clearing the root field reverses the emergency state.

This is a bounded static audit plus pure packet/integer tests. No OEM code is executed, no target/root/network requests occur, and no helper or writer is created. GX/GY/GZ and all prior reports remain unchanged. Original OEM inputs are read in place and not copied here.

## Exact inputs and address domains

|Input|SHA256|Addresses below|
|---|---|---|
|Selected QD package|`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`|image0 file=VA+0x200; image1 file=VA+0x40200|
|Retained qdf_tcon.ko|`97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63`|AArch64 module `.text` offsets|
|Retained libave.so.0.1|`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`|ARM32 Thumb link-time VAs|

The earlier host-side source report is `../../tcon-research/rt-protect-controller-path.md`; its disassembly and the frozen GY audit/inventory are input-pinned by this audit. These are exact retained input identities, not a new live loaded-byte attestation. Hashes, byte counts and bounded instruction-range hashes are in both validation files.

## Positive dependency chain

1. **Fault creation:** image1 common setter c1e0 writes root stop1, ordinary0 and fault`0x1001`; c1fa/c200 are explicitly checked here. GY separately pins the setter and its consumers. The root belongs to the shared RTP context, unlike image1 N counters.
2. **Emergency consumer:** image0 214dc loads root+240a, 214e0 reads its low byte, 214e2 masks bit0, and 214e6 skips the emergency call only if that bit is clear. For fault`0x1001`, the predicate is true. `214f0/214f2` calls b660 with reason`0x10`.
3. **The same stored status:** b660 preserves that reason in r5 and passes it to `2b764` at b6a4/b6a6. `2b768` calls getter e670; its e674 literal is AP CPU`0x2000f0e0`. `2b772` inserts the argument into the low16bits and `2b776` stores a halfword at AP+0x10, CPU`0x2000f0f0`. This is not the root fault field itself; it is a separate emergency-reason halfword.
4. **Incoming request identity:** receiver code `12966..129c8` assembles the first two input bytes by eight-bit shift/OR into command halfword CPU`0x200008c8`, then four register bytes into word CPU`0x200008cc`. Thus six input bytes `F3 80 00 00 00 08` identify command`0xf380`, register8. `1289a..128c0` maps command family F3 to the normal word-read family0.
5. **Command and register dispatch:** ordinary reply code `12aa2..12aaa` loads that register and command and calls `21624`. At21646/2164a command`0xf380` selects call21df8; r5 supplies the register. `21df8` checks register<0x23; TBB at21e0e uses table base21e12. **Entry8 is0x2a**, so the computed target is `21e12+2*0x2a = 21e66`. Entries7/9 select different targets. `21e66` calls the same AP getter e670; **21e6a loads u16 AP+0x10** and returns via21e3a. There is no bit-name substitution or inferred object equivalence.
6. **Four-byte response representation:** `12aae/12ab0` saves the returned, zero-extended u16 into reply word CPU`0x20000900` at byte-index modulo4==0. `12ab2..12ac0` extracts `word >> (24-8*(index&3))` and writes that byte into the controller output register. For reason`0x10`, the four response bytes are `00 00 00 10`. The word is cached for the other three bytes; a subsequent group of four may resample. This path does not itself impose an entire transaction length4; the host requests exactly four bytes. No atomicity across a longer stream or independently sampled RAM window is claimed.
7. **The matching host request and decode:** QDF `.text+a030/a038` builds numeric command`0xf38000000008`; a040 calls m_read_cmd9b88. At9c08..9c20 it constructs the six bytes above. The inspected split transport branch uses6 outbound bytes at9c4c and4 inbound bytes at9c70; the combined branch uses6/4 at9cfc/9cf8. The successful receive path loads the four bytes at9c88 and REV32 at9c8c before writing the numeric result. Therefore `00 00 00 10` becomes host word`0x10`. The function also has configuration/skip/error paths; this is its actual-transfer success path, not an assertion that all calls perform a fresh wire read.
8. **Host interpretation:** libave at268d86 extracts bit4; the retained host report pins the associated `ERR Detect Status RT Protect` literal and the getter/ioctl chain. QDF logs the raw word before its optional m_err_debug overwrite at a078 onward. An enabled debug override can change a later returned status; HB does not attest its live state.

## What the closure changes

There is now a concrete **source-compatible path** from the sampled root fault code to the ordinary host error-status query. The AP reason0x10 is no longer merely a bit-value coincidence with the host RT Protect label. The selected firmware request semantics and the retained host wire construction/response decoding match exactly.

The chain is conditional on the selected firmware handling that wire request and the host taking its actual-transfer success path. It does not independently prove physical bus routing, currently loaded code, a contemporaneous status acquisition, runtime configuration/override values, entry into b660 on the actual trial, or the current image0 PC. Several emergency sources may write the same AP reason field; this audit is not a complete writer/caller census. A host RT Protect bit alone does not prove reason provenance, fault timing or panel light.

GY documents why b660 matters beyond reporting: it disables ordinary RTP, changes shared state, writes hardware-facing registers, performs handshakes, and conditionally enters an emergency-service loop. Its magic-word check permits only an **initial bypass**; the loop backedge does not recheck it. Clearing root240a cannot be claimed to unwind those effects. The proposed HA fixed read-only AP witness can sample AP magic/reason and related objects; neither that later snapshot nor the bit4 host read proves historical branch choice or a physical reset. GZ owns the stock receiver/emergency service continuation.

## Reproduce

Run `PYTHONDONTWRITEBYTECODE=1 python3 audit.py` and the same command with `-O`. Both outputs must match byte-for-byte. The script imports the existing retained Capstone and pyelftools installation at `/tmp/tcon-capstone`, reads known files in place, and emits only metadata and synthetic packet/value cases. It does not import a root/USB client, execute OEM instructions, install tools or make network requests.

Tests cover exact instruction operands and branch/table targets; common AP object identity; command/register/reply globals; matching six-byte construction; fifteen finite halfword response cases with zero-extension/bit4 preservation; neighboring register dispatch; packet width/byte-order cases; and malformed byte types/lengths and invalid halfword values. Synthetic response vectors are not reported as actual captured firmware responses.
