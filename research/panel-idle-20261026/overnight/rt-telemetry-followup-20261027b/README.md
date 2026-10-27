# Controller diagnostics follow-up, 2026-10-27

This work follows the preserved [260-file work block](../sleep-investigation-20261027a/sleep-evidence-manifest.json). New files here are outside that snapshot. No physical picture recovery or prevention is established.

The owner explicitly permits active commands, protection bypass and flashing if needed, while retaining the requirement to avoid bricking the TV. Authorization is not the missing step. Installed-image identity, a specific intervention, protocol effects and a workable restoration path remain technical questions.

## New live metadata

Three completed authenticated root commands read cached proc/sysfs information. Their raw transport envelopes and extracted stdout are retained alongside the [runtime audit](uart-metadata-runtime-audit.json). Each returned status zero with empty remote and transport stderr, without timeout. Re-decoding the base64 transport responses gives the retained response objects, and extracted stdout matches byte for byte.

- Driver/IRQ inventory: boot `00000000-0000-4000-8000-000000000000`, uptime 97134.81.
- One finite counter interval: uptime 97157.72–97162.73, 5.01 seconds. All retained serial-counter and IRQ lines match between endpoints; the framing newline differs. `ttyS1` at host MMIO `0x00550e00` reports tx/rx zero. This does not establish electrical disconnection, especially with the receiver unopened.
- USB parent identity: uptime 97224.86, same boot. `ttyUSB0` resolves to USB `12-1:1.0`, bound to cp210x, VID/PID `04e8:20e4`, manufacturer Silicon Labs, product **SmartThings Dongle**. It is distinct from the reset-coupled `04e8:2001` Samsung STL1 CDC/Bulk device.

These commands did not open a tty, change termios or mux settings, bind drivers, send USB/control/I²C requests, navigate the UI or reset the panel. No physical picture was observed. The identity result removes one misleading candidate for a controller console; it supplies no firmware fault log.

## New offline results

- [F300 telemetry census](../../tcon-research/qd-f300-read-rt-telemetry-census-20261027.md): all 301 aligned selector positions are accounted for. Three direct getters from the fixed `0x47010000` root map to AP_SBD, AP_ZA and AP_HUT, outside both AP_RTP destinations. Parent re-disassembly confirmed the three load widths and offsets. No direct getter for the identified RT flag/history was recovered in this dispatch.
- [I²C family census](../../tcon-research/qd-i2c-read-command-family-census-20261027.md): the remaining F7 transmit family returns finite bytes from protocol state/response RAM. Parent re-disassembly confirmed its command and index bounds. The generic logical reader remains stored FILE `0x657c`, linked VA `0x637c`; no arbitrary-memory ingress was recovered here. F7 receive commands include active state/MMIO operations, whose purposes require decoding before use.
- [RT accessor callers](../../tcon-research/qd-rt-window-live-producer-census-20261027.md): 91 syntactic direct BL callers resolve to the fixed-root accessor. The only direct caller constructing exact offset `+0x240a` performs a byte load. This does not close computed offsets, indirect copies/DMA, other images or external writers.
- [SmartThings identity boundary](../../tcon-research/ttyusb0-cp210x-identity-boundary-20261027.md) ties the USB result to the retained metadata and distinguishes it from the Samsung bulk interface.

The generic I²C ingress therefore does not currently supply the missing installed-image or RT-history observation. Work now targets the firmware-side bulk handler, the stock backup bootstrap, and whether USB CDC receive bytes reach a useful command consumer. Active I/O is authorized; exact target/storage mappings and byte-count validation must still be recovered to make a backup useful.

## Subsequent positive USB findings

The [scatter/descriptor reconstruction](../../tcon-research/qd-usb-device-descriptor-scatter-match-20261027.md), independently reviewed, expands image0 reset row6 and recovers its complete 18-byte USB device descriptor. Every byte matches the earlier cached live descriptor. Row0 supplies the descriptor callback pointer and the USB initializer passes its table into registration. This closes a concrete descriptor identity gap; it does not prove current executable equality.

The [device-side bulk protocol](../../tcon-research/ssb-device-read-protocol-20261027.md) now binds target `0x203` to an aligned eMMC sector read, separate from the adjacent write operation. This is not a direct SPI-flash dump. The storage routine's result is discarded before the USB response, so full transfer length alone cannot validate fresh storage data. The [independent review](../../tcon-research/ssb-device-read-protocol-independent-review.md) confirms that direction and identifies the receive-arm/response-capacity question for a live request.

A fourth authenticated cached-metadata command, [retained here](usb-one-chunk-preflight-metadata.json), completed at uptime 98176.31–98176.36 on the same boot: Samsung `04e8:2001`, configuration1, authorized1, runtime active, all three interface driver links absent, full cached descriptors unchanged, USB character node `/dev/bus/usb/007/045`. It opened no USB device and sent no protocol request. This is timestamped preflight information, not a permanent claim about binding or receive state.

The [one-shot managed reader](../managed-usb-ssb-read-once/README.md) has been rebuilt and independently reviewed after the parent replaced its initial implementation. Its 22 injected failure/cleanup tests exercise the actual shared execution engine. The default dry run performs no sysfs/device access, host execution refuses the ARM32 mismatch, and unknown arguments refuse. The exact six-file [build manifest](../managed-usb-ssb-read-once/build-manifest.json) SHA-256 is `8104f9d4820c29cddfe3233a69fe3a522b2189cc8b870e1eddc19391336bf46f`. No target staging or USB read has occurred at this checkpoint; firmware capacity/receive-arm analysis remains separate from helper correctness.

**Later ARM runtime qualification:** that exact reviewed assembly was then staged in a private temporary directory and invoked only with no arguments and `--self-test`. On the actual TV CLR both completed, reporting a no-device dry run and all22 fake-I/O cases passing. Boot remained unchanged across uptime 98704.39–98704.84. Two separate runtime GC_INFO rows are retained alongside the two intact JSON outputs. [Raw calls](usb-reader-target-dryrun/record.json) and the [runtime audit](usb-reader-target-dryrun/runtime-audit.json) preserve staging hashes, command results and verified removal of the private stage. No USB endpoint was opened and no USB request was sent. This supersedes only the preceding checkpoint's not-yet-staged status; it is not a storage read or physical recovery test.

**Addressed-memory lead and execution gate:** parent disassembly also finds an operation1 route passing a caller address directly into USB IN, and proves that family1 disables the separate address remap for that header. However, the parser writes byte `0x20000571=2`, then an early gate skips the transfer while that byte remains two. This affects the eMMC path as well. The [new lead note](../../tcon-research/ssb-family1-memory-in-route-lead-20261027.md) preserves exact instructions and the unresolved gate. A selected read branch's arguments are not proof that a live header reaches it. No candidate memory-read packet was sent; the managed helper remains unchanged and no active USB execution has occurred.

**Final checkpoint:** the protocol agent's corrected report now incorporates that gate. Its local read direction and one-sector buffer bound remain useful static results, but its earlier one-header feasibility claim is superseded: ordinary packaged parsing sets mode2 and bypasses operation dispatch, with no recovered later mode0/1 producer or alternate re-entry. The prepared 8KiB helper is not an approved live experiment from these findings and was never invoked with `--execute` on the TV. Remaining work is the actual mode producer/alternate path and current executable identity. Authorization is already present. Physical picture recovery after the earlier stock panel cycle remains unobserved.

## Current physical-test boundary

Exactly one stock MODE2 panel cycle preceded this block. It cleared sequential reported RT status/error-input samples; a later pair also read zero. The owner has not yet confirmed whether that restored the physical picture. No additional panel cycle or UI transition was performed in this follow-up. Preserve that observation opportunity before changing the current display state.

No firmware was flashed, no kernel/module was loaded, and no protection or monitor-memory value was changed in this block. These facts describe execution, not a request for additional permission.

## Later correction: ordinary read-mode producers recovered

The preceding final checkpoint is superseded on its specific mode-gate claim.
Parent instruction review found the missing producers in the ordinary parser:
VA0x2905a..0x2905e writes mode0 for operations1/2, and
VA0x29076..0x2907a writes mode1 for operations3/4. All reuse the literal at
VA0x291f0 / FILE0x293f0 for RAM0x20000571. Initial mode2 is a sentinel before
classification. The [new independently reproduced follow-up](../../tcon-research/ssb-mode-gate-followup-20261027.md)
records exact instructions, PC-relative arithmetic and normal completion
rearming the next header. The earlier absence claim missed reused literal
references; it was an analysis error, not evidence of disabled firmware.
No request was sent under that earlier conclusion.

A separate [fixed descriptor reader](../managed-usb-descriptor-read-once/README.md)
now targets only the already reconstructed18 descriptor bytes at RAM0x20261200.
Its default dry run and23 injected cases pass on the host, with an explicit
known-data comparison and all prior cleanup/identity/ARM guards retained.
Independent review is in progress. The existing8KiB storage helper is unchanged
and remains unexecuted. At this checkpoint no active USB packet has been sent.

## First verified live controller-memory read

The first fixed-descriptor helper reached the TV and passed23 injected cases,
then failed before USB open/claim with EndOfStreamException. Its full
[record](usb-known-descriptor-read-once/record.json) is preserved. New cached
metadata identifies the cause: sysfs advertises65553 descriptor bytes, while a
bounded `od -N117` produces116 actual bytes. Size-based File.ReadAllBytes was
therefore replaced in a separate revision by bounded streaming, without
changing the first source/build/evidence. No protocol command was sent in the
failed attempt.

The streaming revision passed27 cases on the TV and then completed exactly
one live target0x101 read of18 bytes from controllerRAM0x20261200. The
[actual output](usb-known-descriptor-read-once-v2/stdout.txt) records
open25, claim0, OUT12, IN18, release0, close0 and Accepted=true. Returned bytes
`12010002ef020140e8040120500201020301` match the reconstructed and cached
descriptor; SHA256 `f78bbb5a0e0a2fbe4944247d54be966c533da8ad91feac8df848106e9f54825b`.
The authenticated run stayed on the expected boot, uptime99909.27–99909.74,
and cleanup verified STAGE_ABSENT. The [reproducible runtime audit](audit-known-descriptor-runs.py)
reconciles both runs' raw transport envelopes, five-file manifests, helper
outputs, data and cleanup. Independent review also reconstructed uploaded
payloads and verified all16 calls per run.

This is the first positively validated live direct-memory diagnostic route
in this follow-up. It does not prove whole installed-image equality, USB DMA
access to the separate0x4701 RT window, the physical picture, a protection
change or a repair. Normal completion rearms the next command in the packaged
code; timeout/cancel rearming is unproved, so no retry/reset is implemented.
The temporary helper was removed. No flash or protection write occurred.

## Subsequent positive RT-window read

The next separately built/reviewed helper performed one experimental32-byte
read at image0 RT address0x47012400. It passed26 cases on the TV and completed
OUT12/IN32 with successful claim/release/close, Accepted=true and private-stage
removal. Its [actual reply](usb-rt-prefix-read-once/stdout.txt),
[reproducible audit](audit-rt-prefix-run.py) and
[result](rt-prefix-runtime-audit.json) preserve all details. Returned data
matches30 of32 packaged initializer bytes; offsets08/0e changed0->1, the
RT flag halfword at0a is0 and mode at10 is4. A later accepted stock status
query returned0, corroborated by the raw QDF row for its PID10844 at
uptime100242.204712. The memory window100190.44–100190.96 precedes that
query by roughly51seconds; no simultaneity/continuity is claimed.

Independent review verified the final derivative, all16 root responses,
reconstructed uploaded bytes, known initializer deltas, exact transfers and
cleanup. This supersedes the earlier RT-DMA-accessibility gap for only this
32-byte window on this boot. Whole-image identity, image1 alias, physical
panel state and fault causality remain unproved. No reset/UI transition,
protection/payload-memory write, flash or continuous logger was run here.
See the [complete progress and next-capture design](controller-memory-access-progress.md).

## Preserved controller-access checkpoint

The [90-file evidence snapshot](controller-access-evidence-manifest.json)
contains6,549,528 bytes and has SHA256
`c543b3d24a8cd7b807990e46e25ee4ede3420724d47c43fc752af472800a2c38`.
It includes the exact helper builds/sources, failed and successful runtime
records, reproducible audits, corrected static analyses and the selected
profile. Mutable navigation/README files and future additions are excluded.
Normal and optimized runtime audits passed; optimized snapshot verification
and an independent row-by-row scan both reconciled every byte/hash. A second
publication was refused without changing the manifest. The preceding260-file
snapshot also reverified unchanged at SHA956d690aae4dad5309db6af6324c329d4e67bf29f8bd9e7601f8c26ae4157296.
No new control/test remains running; all new private helper stages were removed.

## Later continuation

The [next work block](../rt-onset-memory-20261027c/progress.md) qualified a
full256-byte RT snapshot and20-sample short recorder, then obtained a
structurally valid but different target203 sector-zero reply (241205A versus
selected241230A). It preserves the read-status/freshness caveat and requires
new backup/fingerprint evidence before absolute-offset patching. Its new
41-file snapshot is separate; this earlier90-file snapshot is unchanged.
