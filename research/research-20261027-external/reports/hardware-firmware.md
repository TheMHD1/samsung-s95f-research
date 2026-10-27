# S95F hardware and firmware: external evidence against the actual gaps

Research date: 2026-10-27 UTC. Scope: internet sources and already retained local artifacts only. **No TV connection, target read/write, USB/I2C transaction, power action, helper deployment, or firmware application occurred.** Source copies, repository commits, hashes, and licenses are recorded in `../sources/hardware-firmware/source-inventory.json` and `download-manifest.json`.

## Result

The useful new finding is an independently reproduced **clear MSDU11 directory interpretation of the target's already retained official firmware prefix**. It exposes nine contiguous payload intervals and a complete encrypted metadata block; its final interval ends at exactly the ZIP member's previously recorded uncompressed length. This materially improves the acquisition map without claiming decryption, signed-image verification, target flash identity, or TCON firmware recovery.

A first-party S95F 77-inch research repository supplies a concrete modern SWU TrustZone decryption implementation. Its documented successful extraction is **another researcher's report for EU QE77S95FATXXH, T-RSMFDEUC 1296.8**, not an independently reproduced result on this Canadian TV. Source inspection confirms the transport and command sequence exist; it also exposes important reproducibility gaps and side effects omitted by a casual reading of the headline. There is still **no located public model-matched schematic, connector pinout, S6TUT14 register map, RT-protection definition, or QDF USB vendor-protocol specification**.

The target's own strongest result remains content dependent recovery: populated Apps plus one stock operation-41 MODE2 restart recovers visible Apps, whereas the restart with sparse For You selected did not. Audio/Linux continuity and the bottom-edge thumb-sized impact patch plus vertical line are preserved observations. Neither external documents nor the photos prove an electrically failing component, that the physical damage caused RT protection, or that firmware corruption caused the blackouts.

## Existing evidence retained, with applicability boundaries

| Evidence already known locally | Consequence for external research |
|---|---|
| Panel label `CY-AF077FLLV2H`; host model `QN77S95FAFXZC`; photographed main-board model marking `QN77S95FAFXZA` | Region/model strings alone do not identify a PCB revision, controller IC/package, or connector pin assignment. |
| `BN96-60461A` panel links, `BN96-60922A` PANEL link, `BN96-56961A` DCDC **cable** | Cable numbers are useful for matching documentation; the last number is not an established green-board part number. Tentative `BN95-55394B`/`BN44-01322A` remain unconfirmed. |
| External QDF FW/MD `FA024C300` / `F77ABUAE20312300`; bus-5/address-0x76 status route | Prioritize the external QDF implementation and matching composite asset for RT. |
| Internal-TCON/RHEA log `F77ABU2D20`, 2 MiB SPI capacity | This comes from a different host route. It is not established as the producer of external QDF `F3:08`/RT status. |
| Selected 5 MiB `F_RSM1_BN9659934B_COMMON.bin` has two coherent Cortex-M/Thumb images plus tables | It is already an acquisition success, not an opaque calibration-only file. It is not a raw 2 MiB RHEA flash dump. |
| Three selector-1 code-view reads match selected/current stored image-1 slices; stored image-1 slots agree | This does not classify mapped backing as writable RAM, identify a running PC, prove whole-image execution, or establish restore semantics. |
| Producer gap at `[0x584109a4,0x58410aa4)`; source trace reaches scheduling but no runtime table writer | Publicly identifying the peripheral/core or a DMA descriptor would be valuable. No reviewed manufacturer document closes that edge. |

Local anchors: [owner board map](../../panel-idle-20261026/tcon-research/owner-photo-board-map.md), [external/internal identity separation](../../panel-idle-20261026/tcon-research/qd-rt-controller-identity-boundary.md), [selected composite asset](../../panel-idle-20261026/tcon-research/qd-selected-profile-content.md), [write-readiness boundary](../../panel-idle-20261026/overnight/code-write-readiness-20261027r/code-write-readiness.md), [unresolved producer](../../panel-idle-20261026/overnight/rt-input-producer-gap-20261027bq/source-review.md), and [current investigation](../../CURRENT-INVESTIGATION.md). Existing reports can contain older open edges subsequently closed elsewhere; their historical wording is not a claim that the investigation has regressed.

## 1. Target firmware: directory structure independently recovered offline

Samsung's exact [Canadian model support page](https://www.samsung.com/ca/support/model/QN77S95FAFXZC/) still lists `T-RSMFAKUC-0090_TB-RSWF4AKUC-0090.zip`, `0090-1301.0`, dated 2026-09-08. This confirms the existing package source rather than identifying a new release. The page and official repair/update PDFs were downloaded locally and hashed. The full 2.44 GB archive was **not** downloaded in this task.

Two primary upstream parsers agree on the important byte layout: 6-byte magic, three 32-bit words/one 32-bit plus one 64-bit field, section count, then packed `(u32 id,u64 offset,u64 size)` records and named encrypted-header descriptors. They differ in naming unknown fields, so those field names are not treated as authoritative. Sources: [bugficks structure/parser](https://github.com/bugficks/msddecrypt/blob/c5e6d661640521ab292f7cedc329b092d805906b/src/samygo/msd.py), [Synacktiv schema](https://github.com/synacktiv/samsung-q60t-exploit/blob/db3697456be6f95599ea09ad1570bb80dd8797e1/firmware/decrypt.py), and the modern [S95F inspector](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/tools/firmware/inspect_msd.py).

A new standard-library verifier implements only that bounded structure against the previously retained target prefix, SHA-256 `01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d`. It checks descriptor bounds, ASCII label, marker placement, adjacency, payload contiguity, and the previously established full member length. It does not execute downloaded code. [Verifier](../sources/hardware-firmware/verify-retained-msd-header.py); [retained result](../sources/hardware-firmware/retained-msd-header.json).

| ID | Target offset | Encrypted interval length | EU 1296.8 manifest name, **candidate only for target** |
|---:|---:|---:|---|
| 1001 | `0x10c2` | 1,455,423,504 | `platform.img` |
| 1002 | `0x56c010d2` | 11,892,544 | `uImage` |
| 1003 | `0x57758812` | 9,306,128 | `factory_peq.img` |
| 1004 | `0x58038822` | 8,380,432 | `secos.bin` |
| 1005 | `0x58836832` | 3,661,840 | `seret.bin` |
| 1006 | `0x58bb4842` | 3,137,552 | `secos_drv.bin` |
| 1007 | `0x58eb2852` | 1,564,688 | `dtb.bin` |
| 1008 | `0x59030862` | 166,416 | `ddr.init` |
| 1009 | `0x59059272` | 1,040 | `sign.bin` |

The clear descriptor ends at byte234. It labels `T-RSMFAKUC-0090`, places its encrypted header at234 with length4056, and ends at4290 (`0x10c2`), exactly the first payload start. `Salted__` is at242, eight bytes after the descriptor's offset. **The full encrypted metadata block is already present within the saved65,494-byte prefix.** Payload1009 ends at1,493,538,434, exactly the previously recorded whole MSD member length. This agreement is strong structural validation; it is not signature/CRC validation of the package.

Eight payload lengths match the [EU1296.8 manifest](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/tools/firmware/manifests/T-RSMFDEUC-0090-1296.8.json). EU payload1 is larger by `0x1600000` (23,068,672 bytes), shifting later offsets. Matching lengths do not prove matching contents or item names. **Do not copy the EU offsets, salts, expected CRCs, GPT boundaries, or filenames into a target manifest.** The target's name/salt/CRC mapping remains encrypted. The word at byte6 is retained as `0x1f54c22c`, unverified; the u64 at10 is216, with semantics unassigned.

Verification ran normally and under `python3 -O`; both pass. Five malformed variants are rejected: truncated descriptors, wrong magic, excessive section count, an interval gap, and wrong encrypted-header marker. These checks validate the bounded parser and explicit invariants, not cryptographic authenticity.

## 2. Modern same-size S95F extraction lead: code exists, claimed success remains external

The pinned [TizenWLED extraction report](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/docs/FIRMWARE_DECODE_QE77S95F_1296.md) reports decrypting EU77-inch S95F1296.8 main and companion containers, all nine section CRCs, an ARM64 Linux5.4.261 kernel, and GPT-contained platform/product VDFS4 filesystems. This is closer than Q60T-era examples but remains different region/version. The repository does not include the decrypted artifacts, so those successes, kernel identity, GPT values, and file counts were **not independently reproduced here**.

Actual code audit narrows what is supported:

* [Host streamer](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/tools/firmware/decrypt_via_tv.py) sends section salt to `/stream-begin`, ciphertext chunks to `/stream-update`, and invokes `/stream-finish`; it uses `.partial` output and promotes only after a manifest CRC match. It is **TV-assisted decryption**, followed by offline extraction. It is not an available offline RoseM production key.
* [Native streaming code](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/Probe/probe_native.c) reads the encrypted passphrase file, opens the SWU TA, and implements commands0/1/2 with partial shared-memory references. Init packs derivation and mode/key-size values; update/final use reported output lengths and capacity checks. The audited streaming functions contain no flash/storage-write call. That is a static call-site finding, not proof of the target TA's internals or crash behavior.
* [Managed Probe](https://github.com/hTobi02/TizenWLED/blob/e6b4acea23bd4fd53a779ac23f371db70a55eda1/Probe/Program.cs) is broader than that subset: startup automatically runs `BuildReport`, which calls `ProbeSwu` and tries command3 unwrap modes0..3. Its listener binds all interfaces on45679 and exposes additional file/capture routes. Deploying the whole Probe unchanged would perform extra work unrelated to bounded header decryption.
* Host `strip_pkcs7` returns input unchanged for invalid padding rather than rejecting it. CRC comparison is the final host gate; it is not a PKCS#7 validity proof or signature check. The host trusts supplied section offsets/sizes and CRCs, so target metadata must be independently derived first.

This is enough to justify **reviewing the installed target SWU client's ABI/configuration against this concrete modern flow**, not to claim its successful execution on the target. A bounded encrypted-header decode is the smallest useful acquisition milestone: it can reveal item names/salts/CRCs before moving gigabytes, and can prioritize the candidate factory payload over the full platform. Parent coordination owns any future target work.

The VDFS extraction stage is not fully reproducible from this repository alone. Its report says the required authenticated-file extractor patch remains outside Git. Pinned [gtors `decompress.rs`](https://github.com/gtors/vdfs-unpack/blob/0bc1e65b74016fbd59d5d68f09ab7920044be1f9/src/decompress.rs) still uses a special `h`-prefix single-stream branch, whereas the report's correction calls for per-extent inflation after accounting for authentication data. The public [VDFS4 layout](https://github.com/vdfs-team/vdfs4/blob/dfb2450427477c7b1eefb0a8580e92c24feba3b4/vdfs4_layout.h) supplies compression/authentication structures, but this task did not reconstruct or test the missing patch against a target filesystem. Require representative authenticated multi-extent samples and full output-length/digest checks before asserting a complete extraction.

## 3. Historical decryptors and firmware-mod-kit: concrete limits

[bugficks/msddecrypt](https://github.com/bugficks/msddecrypt/tree/c5e6d661640521ab292f7cedc329b092d805906b) provides useful packed MSDU10/11 structures and older SWU/TEEC code. Its example targets2016-era K-series, not RoseM2025. [Synacktiv's Q60T decryptor](https://github.com/synacktiv/samsung-q60t-exploit/blob/db3697456be6f95599ea09ad1570bb80dd8797e1/firmware/decrypt.py) has an embedded historical passphrase and an MSD schema; it is not evidence that those credentials decrypt T-RSMFAKUC1301. No guessed key or cross-model decrypt test was run.

[SamyGO's historical image guide](https://wiki.samygo.tv/index.php?title=Playing_with_Firmware_Images) concerns older `.enc`/`.sec`, XOR/AES and CI+ signing, not this target's validated decryption procedure. It was read via browser retrieval; direct Python capture failed certificate verification and was not retried with verification disabled. [firmware-mod-kit README](https://github.com/rampageX/firmware-mod-kit/blob/c72f45d7a062156125ae00cb867d8a614b50b963/README.md) documents conventional embedded-filesystem extraction/rebuilding. Its reviewed scope supplies neither a validated RoseM decryptor nor a VDFS4 authenticated-file repair nor Samsung signing/rollback semantics. Treating generic binwalk/FMK extraction success as proof that a modified image can be applied would be unsupported.

## 4. CPU/ISA mapping and the code-write gap

The retained vectors, Thumb handlers, scatter startup, and compiler banner already support Cortex-M-family code for the composite asset. Host ARM64 kernel modules and ARM32 user libraries are separate execution layers. Public source cannot identify a physical MCU/ASIC solely from `S6TUT14FW`, `Q100A_MCU`, or a readable alias.

Arm's [Cortex-M4 TRM, DDI0439B](https://documentation-service.arm.com/static/5f19da2a20b7cf4bc524d99a), section7.3, identifies `0xe000ed88` as CPACR and bits20..23 as floating-point coprocessor access. This offers a narrow architectural interpretation for the raw address in the first-reset-callee report. It does **not** configure arbitrary external code-backing write permission, name the routine `SystemInit`, uniquely identify Cortex-M4 versus another compatible M-profile core, or classify `0x4600....` as RAM. The same CPACR offset in [Arm CMSIS core_cm4.h](https://github.com/ARM-software/CMSIS_6/blob/99072a3bf70578394bea9dba511922d2961007f5/CMSIS/Core/Include/core_cm4.h) corroborates that architectural location; it is not a Samsung chip address map.

No authoritative source found maps `0x584109a4` to histogram/pixel/sensor data, `0x40122000` to a named Samsung peripheral, or selector code aliases to mutable backing. The producer and write-readiness gaps therefore remain. No cross-model MMIO address, GPIO, timer label, code-write probe, or pin assignment is imported.

## 5. Repair/power/USB/RT sources: where documentation stops

The [official CA repair guide](https://org.downloadcenter.samsung.com/downloadfile/ContentsFile.aspx?CDSite=UNI_CA&OriginYN=N&ModelType=N&ModelName=QN77S95FAF&CttFileID=11121872&CDCttType=EU&VPath=EU%2F202511%2F20251120162206263%2F77.Repair_Guide_S95FH_QNxxS95FDFXxx_Ver1.0.pdf) is genuine Samsung family-level disassembly/replacement material. The newly downloaded PDF is byte-identical to the previously saved guide, SHA-256 `3032488019c873e8aafd071ad8c1b8392196da06e9015425a14f700c8e5d3567`; it is corroboration, not new electrical documentation. Its TV Main/T-con/77-inch-only DCDC distinction agrees with the retained photos. Its troubleshooting section is mostly user checks and post-main-board configuration; screenshots are examples, including other firmware/panel strings. It **does not supply a target circuit schematic, connector signal map, rail timing specification, controller datasheet, or RT-fault dictionary**. A small number of servicing voltage/discharge checks are not a panel sequencing specification. Confirm exact target board/chip/revision before using any other-model service schematic.

The existing [QDF power-sequence trace](../../panel-idle-20261026/tcon-research/qd-power-control-hardware-sequence.md) is more specific than the public repair guide: real lower callbacks, waits and incomplete error propagation are already known. Its logical DVDD/ELVDD/ACDET callbacks are **not a physical connector pinout**. No public document found establishes the target mapping, rail limits, or an electrically safe substitute sequence.

The [USB-IF CDC specification page](https://www.usb.org/document-library/class-definitions-communication-devices-12) identifies the generic class documentation. It cannot define QDF proprietary bulk commands or demonstrate that opening/configuring the interface is passive. Local [corrected line-coding analysis](../../panel-idle-20261026/tcon-research/qd-usb-linecoding-callback-corrected.md) already finds endpoint/bookkeeping effects. No manufacturer source found documents the target0x101/0x102 memory semantics, transactional phase rules, or a dump/restore command. USB re-enumeration does not prove a particular MCU/RAM reset domain.

Exact/identifier searches for QDF/TCON, `S6TUT14`, `S6TUT14FW`, `CY-AF077FLLV2H`, `F77ABU2D20`, `RT Protect` and the known cable/board strings produced no usable manufacturer schematic or protocol definition. The Samsung open-source portal browser fetch timed out; no assertion of a complete portal/source-release search is made. Public Screen Optimization guidance remains distinct from RT/ERR_DET; the [existing primary-source review](../../panel-idle-20261026/tcon-research/rt-protection-external-evidence.md) already documents that limitation. Missing documentation is a bounded search result, not proof that service documentation does not exist.

## 6. Backup, signatures, rollback and prioritized next evidence

The [official USB update guide](https://org.downloadcenter.samsung.com/downloadfile/ContentsFile.aspx?CDSite=UNI_CA&OriginYN=N&ModelType=N&ModelName=QN77S95FAF&CttFileID=11227395&CDCttType=FM&VPath=FM%2F202601%2F20260102174449889%2FTV_USB_Update_Guide.pdf) describes model-matched higher-version updates and automatic restart. It provides no raw-flash backup command, forced downgrade, TCON rollback, or signed recovery image for this panel. Source-readable decryption and CRC equality do not establish image authenticity, signing ability, secure downgrade eligibility, or safe application. No verified target A/B/boot-selection scheme is recovered here.

The retained ordinary-filesystem composite asset, recovered storage artifact, and installed components are valuable backups **of the captured bytes**. They are not a demonstrated full controller flash/EEPROM/calibration backup and do not prove restoration after interruption. Existing update paths are consumers/writers, not established readback interfaces. There is no qualified firmware patch/apply/rollback action in this report.

| Priority / gap | Concrete next evidence | What it would resolve; what it would not |
|---|---|---|
| P1: Target metadata still encrypted | Independently match the target's retained SWU client/configuration to the reviewed modern0/1/2 flow; first decode only the already complete encrypted header with strict bounds and semantic validation | Produces target item identities/salts/CRCs. Does not identify panel flash contents or authorize applying an image. Avoid deploying the broad Probe unchanged. |
| P1: Actual table producer/physical onset | Continue static producer/DMA/peripheral-owner tracing using the exact selected/current-image distinction; correlate existing approved observation methods with owner-visible Apps→For You onset | Addresses the causal gap directly. A new generic public OLED theory or late threshold recomputation does not. |
| P2: Missing external controller package/variant | Once target names/CRCs are recovered, prioritize the actual factory payload; hash/parse and compare recovered QDF assets against the retained composite before searching the entire platform | Can reveal source variants and packaged executables. Does not prove current execution or that RHEA is the RT producer. |
| P2: Required VDFS extraction correction | Recover/reimplement the authenticated multi-extent layout from appropriate driver sources and validate actual target samples | Makes extraction reproducible; external zero-failure claims alone do not. |
| P2: Pinout/rail/controller identity | Model/revision-matched manufacturer schematic or readable IC identity plus vendor documentation | Needed before assigning physical pins/MMIO/rail behavior. Logical GPIO numbering and reseller fit lists are insufficient. |
| P3: Any persistent firmware change | Positive backing/write semantics, complete relevant storage/calibration inventory, verified boot/signature/downgrade rules, and independently demonstrated restoration path | Closes recoverability prerequisites. Matching three readable code windows and holding a stock package do not. |

No exact electrical failure or permanent repair is established. The new acquisition structure and the audited modern SWU implementation are actionable research leads; the owner-confirmed content dependence and controller restart behavior remain the strongest target-specific facts.
