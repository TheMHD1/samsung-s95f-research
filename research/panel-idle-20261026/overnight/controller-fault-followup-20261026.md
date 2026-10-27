# Controller fault follow-up: recovery predicates, assets and shared log

Subsequent evidence: [October27 firmware/profile progress](firmware-profile-progress-20261027.md)
supersedes this phase's “no candidate selected” limitation. Existing raw
FW/MD fields uniquely match`F_RSM1_BN9659934B_COMMON.bin`, now copied as an
ordinary file. The complete official main MSD member is also acquired and
CRC/SHA checked on the host; no controller executable or repair is thereby
established. Historical statements below retain their original phase scope.

No physical recovery or permanent prevention is established. The previous
accepted independent ERR_DET sample was1; the separate controller status query
was0x10 (vendor label RT Protect). They were not simultaneous or aligned to an
owner-timed onset. The visible populated-Apps control remains pending. This
follow-up made filesystem reads and one bounded shared-log snapshot; no new
fault-input query, reset, power, latch, protection or factory command was sent.

## Exact host retry predicates

[New bounded predicate map](../tcon-research/qd-monitor-exact-recovery-predicates.md)
closes two previously unnamed operation-two conditions in the copied AVE:

- 0x269ae0: no-current-ERR path and `err_det_reboot_try == 1`.
- 0x269b26: current ERR, `isProductionMode != 1`, and no terminal retry winner.
- Terminal retry thresholds instead select operation zero and the history
  latch. Subsequent entry with `qd_tcon_off==1` skips these branches.

This is static policy, not an onset trace or a remedy. Prior owner-confirmed
Apps visibility already coexisted with a latched-off report, so that history
latch alone does not explain the later sparse-page transition. Resetting the
bookkeeping is not established to recover panel output or clear the fault.

## Newly found existing factory assets

The initial firmware root at `/prd/lib/firmware/tcon` contains just six tree
rows, including two zero-byte dummy files. Its depth-eight bounded enumeration
and hashes are retained in
[firmware-route-metadata-20261026a/client.stdout](firmware-route-metadata-20261026a/client.stdout),
SHA256 `a076292b45588add9e671728f973185f97788d7ab668b426db521f548ea82201`.

The exact updater resolver led to a previously unsearched factory root:
`/factory_peq/tcon_data/QD`. The [actual root metadata](firmware-resolver-roots-metadata-20261026a/client.stdout)
(SHA256 `17628f7c724548d20b9886d75d50ab3b2dbdcdca2ff7bf31dd678341ab727cf2`)
shows nine `F_RSM1_<BN-code>_COMMON.bin` assets. All20 explicit USB TCON
candidate paths were absent or not directories at that sample.

[File sizes/headers](factory-qd-data-metadata-20261026a/client.stdout)
(SHA256 `730b84fb929779223e989b7d01e56619bf5531c00605b3ded83b54e8b8e2e5da`)
show nine regular5MiB files, initial bytes5a5aa5a5 and sampled zeros through
byte63. The first metadata operation deliberately did not hash files above
its4MiB bound; this was not a read failure. A separately intentional
[exact-size hash pass](factory-qd-data-hashes-20261026a/client.stdout)
(SHA256 `4d6a58d152c6cd4dfb31059ba09d336e33bf624299bf26054cea31ccee542897`)
verified allnine are5,242,880 bytes with distinct hashes. None is equal to a
four-byte magic followed by allzero padding. Those are hashes of existing
files, not copies of full assets or proof of active controller contents.

A proposed literal-marker scan found the target `strings` executable absent.
The [retained response](factory-qd-data-string-scan-20261026a/client.stdout)
records `STRINGS_TOOL_ABSENT`; no file was scanned and there is no negative
marker-search result.

[Exact resolver analysis](../tcon-research/qd-firmware-resolver-exact-paths.md)
separates flash-data, OTP-data and MCU executable names. CAD profile selection
uses year tag, chip type and a controller-read ten-character key. The retail
model,77-inch size and F77 startup identifier do not identify which of the
nine assets is active. The original command-nine inference was corrected after tracing the actual
CAD caller: it uses non-SE operation0x20 and exact dynamic name `tcon_ex_proc`.
The separate operation-nine loader cannot supply the CAD layout. No asset has
been applied or labelled the recovered MCU executable. The host-side local checker passed exact function and asset
metadata/hash checks. RT's expansion/producer/threshold remain unknown.

## Shared MICOM log: corrected read semantics

The [exact driver analysis](../tcon-research/tcon-micom-log-cache-producer.md)
supersedes older shorthand describing a fixed kernel text cache under runtime
PM use. The file directly exposes mapped reserved shared memory; its apparent
tryuse/disuse helpers only read an instance state and return, without PM
reference changes. Reading advances only its own file position, and does not
clear/ack the shared header or send a controller command. The exact firmware
writer and reset/wrap semantics remain unrecovered.

The read handler has a real count-selection defect: large reads can extend
past the current valid length, while requests smaller than4KiB can receive
more than their requested count. The reviewed bounded method is one `dd`
open with `bs=4096 count=16`. Do not replace it with one8KiB/64KiB request.
Concurrent external writes can still make the result a torn snapshot.

### Actual snapshot and preserved preflight failure

Attempt [a](micom-log-read-20261026a/capture.client.stdout) stopped exit1,
empty stdout/stderr before its private-directory creation marker or log read.
The parent used an incorrect module path under `/kernel/`; the separately
retained [metadata check](micom-log-read-20261026a/preflight-metadata.client.stdout)
confirms that path absent and the attempted private directory absent.
Existing acquisition evidence identifies the actual path under `/kernel/soc/`.
The original rejection flags remain unchanged; no snapshot was obtained in a.

The deliberately corrected [b result](micom-log-read-20261026b/result.json)
contains one actual source open/read sequence, one transfer and one cleanup
RPC, all authenticated/root/exit0/no timeout/empty remote stderr. Source module
hash and Linux release were checked. Captured uptime79281.42..79281.44,
UTC1793057672, boot34f419d2-6256-4e1f-a7a9-8d46b875857d. The decoded
[snapshot](micom-log-read-20261026b/micom-log.bin) is1,477 bytes, SHA256
`bd600476b7a081b58759128cff8bacd8f4fef8d8c45c33327cc575a1c65d7110`.
Its full size/hash matched the target snapshot before guarded removal of the
exact private files/directory. The [independent runtime audit](micom-log-read-20261026b/runtime-audit.md)
replayed allthree responses and accepted this bounded acquisition. No read or capture loop remains active.

The earlier1,405-byte artifact and this snapshot share their first1,404 bytes.
The old trailing `S` is not preserved; the new suffix consists of two additional
complete `Msgbox ISR In Ch : 2`/`Msgbox ISR out` pairs and a final byte0x8b.
Thus the exact former artifact is not a complete prefix of the new one. Do not
interpret the trailing bytes as a fault code or claim an atomic append.
Startup/version/timing text remains the same within the common prefix. There
is no timestamped new fault or proven controller-reboot signature in this
comparison, and absence of such text does not exclude either event.

Physical state at the read is unobserved in the machine record; the latest
owner context remains black/off panel. This does not replace the pending
owner-confirmed visible Apps sample or an aligned visible-to-black transition.


## Named CAD-provider gap: new installed module acquired

A single [installed-module literal scan](tcon-ex-proc-provider-scan-20261026a/client.stdout)
(SHA256 `43d62d1f13fa7b4ece51ae0ddf83c530dd255b0d30ed6a2364a5e257dd11a240`)
searched195 regular module files on the same boot, uptime79537.27..79538.49.
The exact-word string appears only in the known bridge and
`/lib/modules/5.4.261/kernel/soc/sdp_pqe_frc.ko`. A literal match alone does
not prove an export or a live binding.

The new ordinary module file was [copied and independently audited](sdp-pqe-frc-provider-copy-20261026a/runtime-audit.md)
in31 finite32768-byte chunks with size/hash/boot checks before and after every
read. The local file is1,015,070 bytes, SHA256
`1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4`,
Build ID492cc2d117e05b0cc472c2f23ee7a8a0b63b317a. Its symbol table has the
exact `__ksymtab_tcon_ex_proc` export and function `.text+0x58048`, size0x59c.
This closes the named-provider acquisition gap. The subsequent
[bounded provider analysis](../tcon-research/qd-cad-tcon-ex-proc-provider.md)
and [independent review](../tcon-research/qd-cad-provider-independent-review.md)
now trace its actual CAD file parsing and write-capable SSB stream. Live
binding and incident execution are not established. No module was loaded,
restarted or invoked. The earlier319,518-byte/2f23 artifact is a different
module, `sdp_pqe_dp.ko`, and is not substituted for this provider.

The [separate-route analysis](../tcon-research/qd-cad-command9-consumer.md) and
[bounded cross-review](../tcon-research/controller-followup-independent-review.md)
retain why operation-nine and the real CAD operation0x20 must be kept apart.
The incorrect prior resolver report was archived before the current copy was
corrected. Neither this acquisition nor the asset catalog establishes the
RT Protect producer, a physical initiating cause or a panel recovery method.


## Provider parser and comparative field samples now reconstructed

The exact provider's operation0x20 starts a worker with a48-byte envelope.
Its command0x30..0x33 branch accepts declared sizes5..6MiB and obtains version/
profile components at file offsets0x8000a/0x80100 or0xb000a/0xb0100, plus the
tail0x4ffe00. Request+32 contains a pointer to comparison metadata; those
strings are at separate pointee offsets0/9/20, not inline bytes beyond the
48-byte envelope. The parser then has write-capable SSB transfer mechanics;
none was invoked. It is distinct from the separate command-nine loader.

The worker's `_read_data_file` requests the whole declared file size into a
pre-zeroed rounded buffer but accepts any nonzero low32 return from
`kernel_read`, without a sign or exact-count check. That static defect does
not prove any actual asset read failed, and it has not been patched or used
as a blackout explanation.

A [single actual filesystem acquisition](factory-qd-data-fields-20261026a/client.stdout)
(SHA256 `ad0090732901edfadd0c202e855a7bacd660af5acd1e94967710b360a849cdd0`)
read64 bytes at each of the five source-derived offsets from allnine regular
files. Every file's exact size and full SHA were checked before and after its
ranges. Same boot, uptime80110.13..80111.04; status0/no timeout/empty stderr.
[Decoded catalog](factory-qd-data-fields-20261026a/fields.json) retains all45
byte-exact slices and their individual hashes. Independent review reproduced
all45 local slices from the authenticated raw response.

The catalog contains different fixed-width identifiers, including
`F77ABU0D2` and `F77ABUAE2`; another candidate uses `F32AHUME2` at the alternate
offset. The controller's separate startup identifier `F77ABU2D20` is not a
source-backed mapping to one of them. Shared prefixes and distinct-width
fields do not establish active selection, incompatibility or corrupted
firmware. The real RT Protect producer/threshold/clear semantics are still
outside the recovered host parser, and no asset has been applied.

This turn's meaningful progress is actual missing-provider acquisition,
source-bound data-field recovery and correct log capture. The next physical
fault discriminator remains a confirmed visible Apps control and then an
aligned transition; no permanent prevention or recovery is verified.

## SSB acquisition boundary and current registration metadata

The [transport binding](../tcon-research/ssb-transport-driver-binding.md)
and [readback boundary](../tcon-research/qd-ssb-readback-acquisition-boundary.md)
trace the actual embedded USB driver and both readback-shaped paths in the
copied module. The internal firmware reader's callers follow update writes;
the separate backup entry requests a fixed5MiB through USB request headers
and writes an output file. It is not an ordinary passive firmware-file read.
Independent review additionally resolved the SSB open/release callbacks to
USB runtime-PM get/put operations. Opening the transport can resume its USB
interface; the repeated chunk opens are therefore another active side effect,
even without an explicit vendor panel-power/reset helper in the backup body.
Neither path identifies the actual producer of RT Protect or maps this
USB address space to the startup log's2MiB F77 SPI image.

The initial [four-path metadata sample](ssb-device-metadata-20261026a/client.stdout)
found both `/dev/ssb1` and `/dev/ssbs1`, and their named class entries, absent.
A separate [registration/USB metadata sample](ssb-registration-metadata-20261026a/client.stdout),
SHA256 `2807922e63b27c2aef8d9b3ad9c9b5eb3b20a49f5d6e2808928784b6bff48351`,
was authenticated uid/euid0, modelQN77S95FAFXZC, exit0, no timeout and empty
remote/client stderr. Boot ID stayed34f419d2-6256-4e1f-a7a9-8d46b875857d,
uptime80586.50..80586.66. It found `sdp_pqe_frc` loaded, stateLive/refcnt0,
with module driver links to the two platform drivers `sdp_ld` and
`sdp_pqe_frc`. Its bounded globs matched no `/dev/ssb*`,
`/sys/class/usbmisc/ssb*` or `/sys/bus/usb/drivers/*ssb*` entry.

The same cached USB metadata positively contains device7-1, VID:PID04e8:2001,
product`STL1 CDC and Bulk`, manufacturerSamsung. Those IDs match the
copied driver's static VID/PID criterion. This is stronger than saying no
matching USB device exists, but is not a successful SSB-interface binding,
proof of the device's physical function or permission to infer a TCON MCU
storage layout. The sample read ordinary kernel metadata; it did not register
the driver, create/open a character node, issue an ioctl, send a USB request
or change panel state. Its physical picture state is unobserved in the
machine record; the latest owner report remains panel off.

No SSB readback or updater was invoked. The actionable missing comparison
is still a fresh owner-confirmed visible Apps state versus black with the
same bounded controller-status and independent fault-input observations.

The final [independent SSB review](../tcon-research/ssb-acquisition-independent-review.md)
checked the corrected runtime-PM behavior, transfer-count limitations and
device/interface distinction. Both source-verification helpers passed normal
and optimized runs. This accepts the bounded offline conclusions only;
no controller transaction or physical recovery was tested.
