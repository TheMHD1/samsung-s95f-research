# OCL reset sender and receiver-candidate map

The accepted platform extraction contains a concrete multipart OCJP firmware candidate. It is not necessary to start with a new firmware download or an arbitrary flash dump. The retained Linux OCL sender, its conditional I²C transports, the loader's filenames/layout/checksum, and the candidate's coherent LEON/SPARC view are source-backed. The incoming mailbox operation1/command`3f` receiver and its reset domain remain unclosed.

This is a host-only source checkpoint. There were no target requests, network calls, OEM executions, firmware builds, binary copies, or writes to existing artifacts. `audit.py` reads retained files in place; it prints hashes, source coordinates, inventory metadata and derived facts, never an extracted firmware image. All instruction coordinates below are section offsets for the Linux ELF or **file offsets** for the candidate image, as labelled.

## What the sender establishes

The retained `sdp_ocl_jp.ko` is 594110 bytes, SHA256 `e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c`. Its accepted PLTF copy is byte-identical. GZ already connects operation41/MODE2 through QDF's off/on callbacks to `sdp_ocl_reset_tcon_power`; HE extends the final sender-to-transport boundary.

| Source | Positive finding | Limit |
|---|---|---|
| `.text2b38..2b88` | Truncates its input to one byte; calls `SDP_OCL_I2C_MBox_Write(1,0x3f,1,0,&byte)` at`2b5c`. | A Linux function name is not receiver semantics. |
| `.text7d60..8248` | Tests configuration bit1. One branch directly uses `ahb_adap/ahb_client`; the other passes the operation to `__i2c_mbox_op` at`8040`. The actual one-byte path is`7f94..7fbc`, which copies the payload and returns to the I²C setup at`7e28`. | The zero-length branch at`7e1c` is not the reset payload path. No current configuration bit was sampled here. |
| `.text7b10..7c5c`, `6758..6894` | Queues the request and waits for completion; worker operation1 loads its exact five arguments at`684c..6854` and calls `__i2c_mbox_write_nolock` at`6858`. | Driver completion/poll acknowledgement does not prove MCU reboot, TCON image download, shared-root initialization, or full power cycling. |
| `.text62d8..6758` | Mailbox form writes a payload message then command metadata. For reset, metadata word is`0x00013f01` (op1/cmd3f/length1/flags0). Client address is read from the registered structure and shifted right1 before `i2c_transfer`; configuration selects mailbox versus AHB framing. | These are kernel-side logical messages, not a retained bus capture or confirmed peripheral address for the current device. |
| `.text.unlikely2c..488` | Gets an I²C adapter using the configuration object's word at`+8`; stores mailbox adapter/client at BSS`30/38` and creates the client from a local board-info object. In the ordinary branch the source board-info address is`0xf8`, yielding transfer address`0x7c`. | Do not hardcode this as the observed current adapter/slave. Configuration bit1 changes transport; adapter numbering has not been live-attested by HE. |

The mailbox write body polls acknowledgement with a bounded source loop. HE does not propose calling it, changing transport flags, enabling logging, or issuing repeated resets. The existing source can return a software result even though the intended larger reset domain is unknown; GZ's earlier optional-callback and discarded-tail qualifications remain applicable.

## Loader and available files

The conditional filename selection is in `.text1f420..1f710`. The named path pair is reached for returned selector4 in this examined function; other branches can leave path pointers zero. The source strings and ADRP relocations prove these two names:

- `/etc/micom-binary/RMFMICOM_OCJP.bin` at `.rodata.str1.8+5488`.
- `/opt/usr/apps/appbinarymanager/default/empOCJPsubmicom.img` at `.rodata.str1.8+5448`.

Neither the RMF basename nor the exact override path was found in HE's filename-only walk of the two accepted, fully extracted PLTF/PRD roots. This is a bounded inventory result, not proof the file is absent from the running device, a writable application area, another package, or attached peripherals.

The accepted PLTF does contain:

| Extracted relative path | Bytes | SHA256 |
|---|---:|---|
| `etc/micom-binary/PMDMICOM_OCJP.bin` | 901120 | `61754d8e0445ed1a73685af83cdcf3fea66971b1a622b04c3f614b8b63286aff` |
| `usr/lib/modules/5.4.261/kernel/soc/PMDMICOM_OCJP.bin` | 901120 | Same exact bytes |
| `etc/micom-binary/PMFMICOM_FRJP.bin` | 901120 | `45f68e72fe62859431ffb9bcb918cd66895296602c7c28c6a6f031e3951dd349` |
| `usr/lib/modules/5.4.261/kernel/soc/PMFMICOM_FRJP.bin` | 901120 | Same exact bytes |

The filename inventory also records 29 MICOM images in each `etc/micom-binary/debug/` and `release/` tree, both OCL kernel modules, `tztv-micom.ko`, and PRD `libmicom.so.0.1`/`micom-tool`/`index_ocl.json`. These labels identify follow-up candidates, not selected-device firmware. Unrelated Wi-Fi MCU and projector/touch-update names are retained as inventory distinctions and are not reset receivers.

## Format and CPU evidence

The PMD OCJP candidate fits substantially more than a suggestive filename or size:

1. Loader `.text1da60..1dd88` reads a little-endian checksum word at file`0xdbff8`, starts its running checksum at1, and compares its computed value. The arithmetic helper`1aaa0..1ab7c` consumes each loaded little-endian word in byte order bits24,16,8,0, updating two accumulators modulo65521. HE independently implements those instructions and compares with `zlib.adler32` on the corresponding word-reversed view. Both yield`0xce93f188`, matching this candidate's trailer. A one-byte mutation fails. This is format/integrity compatibility, not cryptographic authenticity or selected/live identity.
2. The loader's `g_img_185D_new` table at `.rodata2670` contains11 records of88 bytes. Positive file intervals include `0/f000`, `f000/30000`, `3f000/60000` plus`9f000/a000`, `a9000/6000`, and `db000/1000`. Repeated records describe different destinations; HE leaves those destinations labelled candidates rather than inferring runtime PCs from flash offsets.
3. `.text1e544..1e5ec` reads21 bytes at file`bf08c`; it first copies the new tables, retaining them if all21 bytes are`ff`, otherwise replacing them with old tables. The PMD candidate has all21 bytes`ff`. Its version descriptor at `.rodata25a8` is `(fileBase=f000, offset=850, bytes=8)`.
4. The named LEON version reader`.text1b230..1b3cc` explicitly reorders the bytes of two4-byte groups. Reversing each4-byte group **in memory only** exposes coherent SPARC instruction sequences in the system interval, including `save`, register windows, SPARC delayed calls/branches and a computed dispatch at file`2c904..2c92c`. It also exposes `APP_Mailbox_IPC_System_Read` at file`3b918` and a LEON interrupt message at`34a28`. The original view contains `[HDMI 8051 Menu]` at`aae52`, in the distinct`a9000/6000` component.

These observations support a multipart SPARC/LEON plus separately labelled 8051 candidate. They do not establish that every component has the same byte ordering, that the candidate is the loaded firmware, or that arbitrary file offsets map directly to executable RAM. The inspected views do not require decryption; HE does not claim an exhaustive absence of compression/encryption elsewhere.

## Receiver gap and next bounded source work

The incoming operation1/command`3f` dispatcher has **not** been identified. A useful negative case is file`2bbec`: it compares a byte with`3f`, but the surrounding byte input, `7e`/`68` comparisons, string comparisons and help-style path show a console `?` case. It is not evidence for the reset receiver. File`2c904` dispatches a byte from a structure's`+2`, bounded to12, through a pointer table; this is a candidate mailbox-related sub-dispatch, not a qualified command63 path. The file-to-CPU address/load/relocation relationship and the higher-level command routing must be established before following such indirect pointers as runtime targets.

The smallest next source investigation can use the already retained PMD image in place: reconstruct the system-component header, entry/load/relocation layout and pointer-table mapping, then bind incoming mailbox transport framing to its main dispatcher and operation1/cmd3f case. Follow any reset handler to its actual GPIO/register/mailbox effects and identify which downstream processor or rail it controls. Do not use a raw `3f` scan as the handler proof.

If the PMD image cannot be positively selected, the next acquisition target is the exact **ordinary firmware file or package component** that supplies the module's RMF/default or appbinarymanager override, together with product/platform selection metadata and its version/layout descriptor. That precedes any consideration of an external flash read. A loader filename, a matching checksum, and an embedded firmware-version string cannot substitute for this identity binding. No live acquisition is performed or authorized by this source artifact itself; parent coordinates any later device work.

Until that chain closes, MODE2's USB re-enumeration and local record/N clear must remain distinct from image0 shared RTP-root initialization. GX has a positive image0 startup scatter that initializes the shared root, and real local-N clear paths preserving the fault tuple. HE has not found a reset receiver that invokes the startup scatter, reloads image0, exits its emergency loop, clears the sticky fault, or restores physical light. This map supplies a concrete firmware-analysis target, not a new recovery command.

## Reproduction and limits

Run these host-only commands from this directory:

```sh
python3 -B audit.py > validation.normal.json
python3 -B -O audit.py > validation.optimized.json
cmp validation.normal.json validation.optimized.json
```

The script uses the existing `/tmp/tcon-capstone` import directory without installing or building anything. It verifies exact module and candidate hashes, relocations and instruction operands, source checksum arithmetic and independent library agreement, malformed partial-word rejection, single-byte corruption, duplicate image identity, selected layout fields, SPARC instructions and bounded extracted-root filename facts. `validation.normal.json` contains exact input pins, source-span hashes and candidate metadata; `source-inventory.json` freezes this workstream. It contains no OEM image or disassembly dump.

No conclusion here establishes current peripheral firmware, actual mailbox traffic, runtime PC, a unique reset cause, electrical power behavior, a physical light observation, or a safe new live reset route.
