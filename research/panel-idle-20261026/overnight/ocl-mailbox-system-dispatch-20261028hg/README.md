# Candidate OCL mailbox operation1/command3f receiver

The retained PMD OCJP candidate contains a positive operation1/command`3f` receiver. The chain reaches a secondary STBC-labelled command request with pin argument`0x14` and mode argument`2` or`3`. This is a substantially narrower, source-backed reset-domain description than “MODE2 reinitializes the controller.” The downstream pin's electrical meaning and the actual flashed firmware identity remain unqualified.

This host-only work reads the accepted firmware and retained Linux module in place. It creates no OEM binary copy, target helper, firmware build, network request, live command, register read/write, or reset. HE remains unchanged. HG's decoder and small oracle are source-analysis tools, not a proposed live action.

## Image and address map

The candidate is `etc/micom-binary/PMDMICOM_OCJP.bin`, 901120 bytes, SHA256 `61754d8e0445ed1a73685af83cdcf3fea66971b1a622b04c3f614b8b63286aff` in the accepted extracted PLTF. Its source-derived whole-format checksum was established in HE and is rechecked here. The module's `g_img_185D_new` record at `.rodata2778` gives file`f000`, length`30000` for the component examined here.

Reversing each4-byte group **in memory** reveals a standard64-byte legacy uImage header at file`f000`:

| Field | Value |
|---|---|
| Magic | `0x27051956` |
| Header CRC32 | `0x7afe4346`, independently recomputed with only its CRC field zeroed |
| Payload size | `0x2cbe0` |
| Load / entry | Both `0xa0020000` |
| Data CRC32 | `0x05f82b60`, independently recomputed over exactly file`f040..3bc20` in the transformed view |
| Numeric OS / architecture / image type / compression | `5 / 10 / 1 / 0` |
| Header name | `fw_sys.uimg` |

The coherent SPARC code and valid header/data CRCs establish the transformation and this **linked text correspondence**:

```text
linked text address = 0xa0020000 + file_offset - 0xf040
file offset = 0xf040 + linked_text_address - 0xa0020000
```

Three actual absolute code-pointer tables independently corroborate it: table file`2caec`/11 entries, file`2cfd0`/11 entries, and file`2f6a8`/60 entries. All82 pointers map to aligned positions inside the validated payload. The code constructs these table addresses with SPARC `sethi/or`, indexes them, loads an absolute pointer and jumps to it. These are source link addresses, **not sampled live PCs or qualified executable-RAM addresses**.

The code separately refers to data/string addresses in the`a8000000` range. Six source anchors corroborate a same-payload-offset correspondence, `file=f040+(data_pointer-a8000000)`: Audio and CVBS default-case diagnostics, both Leon-intercommunication diagnostics, the `APP_Mailbox_IPC_System_Read` name, and an STBC timeout diagnostic. This supports analysis of those exact references. HG does not assert a general hardware alias, a live MMU map, loader relocation behavior, or live RAM access through either range.

## Positive incoming path

All coordinates in this table are **original candidate file offsets**, decoded through the word-reversed view. The linked-address map above resolves the absolute tables. The code is source-conditional; no row claims that this path executed on the TV.

| Source | Effect |
|---|---|
| `2cffc`, `2d000..2d004` | The dispatcher accepts a channel selector. Selector1 branches to`2d278`. |
| `2d278..2d28c` | Calls readiness predicate`148d0`; on its positive result, selects register`0xfc311020`. This is constructed by `sethi0x3f0c44` plus`0x20`. |
| `2d030..2d04c` | Reads the register through`11740` (a direct32-bit load), stores the word on its big-endian SPARC stack, and tests bit7 of its low byte. Bit7 clear follows the write path at`2d21c`. |
| `2d21c..2d224` | Passes the register address and header structure to`2cb18`. |
| `2cb18..2cc90` | Uses header byte`+1` as payload length; fetches payload words from register`+4`. The partial-word path masks to the low significant bytes and stores the word in the retained payload buffer at linked data`0xa802f320`, with an offset derived from the existing fragment index. For an ordinary first/only fragment at index0 and length1 this leaves the payload byte in that big-endian word's byte`+3`. |
| `2ccc0..2cce4` | Uses header byte`+3 & 0x7f` as an operation index, bounded to10. Its actual table is linked`0xa003daac` → file`2caec`. |
| Table operation1 | Contains linked`0xa003dd2c` → file`2cd6c`. That case tail-calls`2f798` with the payload-buffer pointer. |
| `2f79c..2f7c4` | Uses header byte`+2` as a command, subtracts4, performs unsigned bound`<=59`, and dispatches through linked`0xa0040668` → file`2f6a8`. |
| Table index59 (`3f-4`) | Contains linked`0xa00407a0` → file`2f7e0`, the positive command`3f` handler. |

The Linux module's metadata word`0x00013f01` becomes stack bytes`00 01 3f 01` after the candidate's32-bit read/store: payload length1, command`3f`, write operation1. The direct-AHB sender's command register address and this candidate's channel1 input register are both`0xfc311020`. This is a positive structural source bridge, not a retained physical bus transaction or proof the currently running MCU matches this candidate.

The parser contains multi-fragment state and assembly logic. HG proves the dispatch entries and the handler for the assembled buffer; it does not prove a current fragment index, mailbox readiness predicate, bus byte-lane behavior, or an uncontended/valid incoming transaction. The first/only-fragment interpretation above is a stated protocol premise, not a sampled state. It must not be used to invent positive endpoint queue proof.

The earlier literal`3f` at file`2bbec` remains the separate console `?` path. HG uses neither that literal nor a string-name match as its receiver proof.

## Handler and secondary command boundary

The actual handler is only a few instructions:

| File offset | Source behavior |
|---|---|
| `2f7e0` | Loads the payload buffer's byte`+3`. |
| `2f7e4..2f7f0` | Compares with0. The `bne` delay slot **always** assigns argument2; only the zero path subsequently assigns3. Thus nonzero→2, zero→3. |
| `2f7f4..2f7f8` | Calls`177a4`, with pin argument`0x14` assigned in the call delay slot. |
| `2f7fc` | Annulled unconditional branch to epilogue`30278`. It performs no test of the callee's returned result. |

HG's small actual-instruction oracle decodes the pinned handler, honors both branch and call delay slots, and verifies all256 possible payload bytes. It is a host source oracle, not full SPARC emulation or firmware execution. All nonzero bytes reach`177a4(0x14,2)`; zero reaches`177a4(0x14,3)`.

`177a4..177d8` masks its two inputs to bytes and calls`17088` with `(0,0x40,pin,argument,0,0x40,reply-flag-pointer,reply-word-pointer)`. Its downstream path is:

```text
17088 -> 1705c packs bytes(command, pin, argument, trailing0)
      -> 16e50 stores the word to MMIO0xfc040000
      -> 16e60 waits on the secondary reply queue
      -> 17088 examines the reply kind and command fields
```

The two outgoing words are `0x40140200` for nonzero input and `0x40140300` for zero. The source labels this reply subsystem STBC through timeout/NACK diagnostics. The reply path compares kind`0xf1` and command`0x40`; these comparisons do not establish a physical reset acknowledgement. In particular, the outer command`3f` handler does not check the return value or forward a qualified downstream reset result.

No direct RTP shared-root zeroing, image0 startup scatter, emergency-loop exit, firmware download, or CPU restart appears in this bounded handler path. There is an actual second command boundary: the receiver of the STBC command word at`0xfc040000`, its command`40` handling, the semantics of pin20/modes2/3, and the board connection still need source closure. Calling pin20 a TCON rail/reset line merely from the exported Linux function name would skip that boundary.

## Identity evidence and remaining target

Parent's already completed ordinary file-metadata query is pinned as input only: `menu-recovery-branch-trial-20261028hf/ocl-file-identity/response.txt`, SHA256 `768cd19fbd0cc2ce4d45b276bede099ad1a4d33a16778ca24fd6ec15ae4cc7d3`. It records both PMD OCJP copies at901120 bytes and the expected hash; the installed JP kernel module matches SHA256`e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c`. The RMF default and appbinarymanager override are reported `NOT_REGULAR_OR_ABSENT` at those exact paths. HG makes no new target call and does not reproduce the identity-bearing raw metadata.

This strengthens available-file/module identity. It does **not** establish the active flashed MCU version, live execution of the candidate, or equivalence of the PMD filename and the loader's conditional RMF path.

The next bounded source target is the secondary STBC command`40` receiver and its pin-mode mapping. HE's module layout already includes a first file interval`0..f000`, and the candidate contains separate 8051-labelled material. Determine which component implements that receiver before assigning a CPU or board net. Match the actual incoming four-byte command path; avoid interpreting overlapping raw opcode/literal patterns as a reachable handler. A separate identity corroboration can use retained boot-version logs or already qualified ordinary metadata; HG proposes no firmware API invocation or flash read.

## Reproduction

```sh
python3 -B audit.py > validation.normal.json
python3 -B -O audit.py > validation.optimized.json
cmp validation.normal.json validation.optimized.json
```

The existing host Capstone/pyelftools directory is imported without a build or installation. The audit pins HE, candidate, module and parent metadata; validates legacy header/data CRCs and source-format checksum; checks actual instructions, all82 absolute table entries, six data correspondences,256 unsigned command-bound cases and256 delayed-handler cases; and rejects wrong transforms, truncated/corrupt headers/payloads and unqualified code addresses. Original image bytes are never written to an output file. The output contains source hashes, coordinates and derived results only.

This checkpoint closes the candidate receiver and immediate secondary command, not a live full-reset guarantee. No actual GPIO request, electrical meaning, image0 reinitialization, runtime PC, physical light result, safe new reset route, or causal fix is claimed.
