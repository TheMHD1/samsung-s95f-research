# Stored firmware differs from the selected package

This checkpoint extends the read-only storage investigation. The blackout is
unresolved and the physical picture is unobserved. Owner authorization now
explicitly includes protection changes and flashing if necessary, alongside
the existing requirement to avoid bricking the TV. No protection change,
EEPROM write, flash, reboot or UI navigation was issued in this checkpoint.

## Why this changes the next repair step

The prior sector-zero reply identified build241205A, while the selected 5MiB
package identifies241230A. Six independently addressed sector replies now
show structured, different content; the mismatch extends into image0 code.
Patching absolute addresses from the December30 package therefore requires
current-image acquisition and a fresh mapping first.

All six fixed512-byte reads completed on boot
00000000-0000-4000-8000-000000000000. Each had one exact12-byte OUT header,
one exact512-byte IN, successful interface release and FD close, and an absent
private temporary stage afterward. The host audit reassembles all uploaded
assemblies, checks every manifest row, verifies all authenticated root
envelopes and the entire exact16-command sequence, parses the26 fake tests
and actual helper result, and hashes the extracted bytes.

| Stored address | Role examined | Bytes differing from packaged sector |
| --- | --- | ---: |
|0x000200|Image0 startup/vector data|77|
|0x029000|Image0 protocol code and literals|497|
|0x040200|Image1 startup/vector data|0|
|0x080000|Later image/configuration header|6|
|0x028e00|Image0 header parser and transfer-cap selection|498|
|0x028a00|Image0 IN-completion callback|490|

The six512-byte payload hashes are distinct. Image1's first sector matches
the package exactly; that does not establish that all of image1 matches.
At0x80000, the returned text is2412060 versus packaged2412300. The other
four changed bytes at relative0x60..0x63 are not assigned a meaning here.

## Current returned-code mapping

Image0 stored offsets are linkedVA+0x200. The returned parser region has
recognizable instruction sequences shifted by0x29c from the selected
package in this local area; this is not a global relocation rule.

The returned code at VA0x28d44..0x28da8 selects a transfer cap per header.
Only normalized operation4, together with object halfword+0x1e==0,
selects512. Operation3 follows VA0x28d7c and writes24576 at0x28da8,
after the immediate0x6000 at0x28da2. This corrects an exploratory agent
claim that operation3's cap still depended on the initial configuration
callback. Root verified the exact instruction path, then the agent
independently confirmed the correction in the package.

The returned completion callback at VA0x28918..0x2892a subtracts the
completed amount and advances the address. At zero remainder it stores
operation6 at0x2894c..0x2894e and calls0x29264 at0x28954. Later code
must still be acquired to pin the rearm helper and all continuation blocks.
Do not substitute selected-package coordinates in a patch to this image.

## Limits and next acquisition

These are transport-validated returned bytes. The reconstructed operation3
caller ignores the underlying storage-read return, so exact USB counts do
not independently prove eMMC success, freshness, physical partition identity
or the identity of currently executing code. Distinct address-dependent
structures strengthen the interpretation as meaningful storage content, but
do not remove that limitation.

The fixed8192-byte prefix reader completed successfully: OUT12/IN8192,
release/close0, stage absent, SHA256
74d23e5947b7520dd4735422e206739f53bef92b7d26f9738a457ae1ae8b7061.
Its first512 bytes repeat the previous header sector, and bytes512..1023
repeat the independently acquired vector sector. All sixteen512-byte
subsectors have distinct hashes. The prefix differs from the package in163
bytes. This qualifies the stock8192-byte read size in one request.

Independent review identified a further boundary to test: the proposed
single5MiB request differs from the stock backup's640 separate8192-byte
headers. Its firmware would fill24576-byte device transfers, consumed by
three host8192-byte reads each. The current scheduler body has not yet been
acquired. A fixed32768-byte/four-IN probe therefore precedes the full run
to test the first continuation boundary. Both helpers passed45 injected
tests and independent source/build/host-wrapper review before execution.
The32KiB probe subsequently completed one native request successfully:
four exact8192-byte INs in45ms, complete cleanup, data SHA256
c7488b4e5c01def8bdf0a490d7ae91ad920a476ccbac834e2fc15e08d74a7fcf.
The full acquisition also completed exactly once:640 exact8192-byte INs in
281ms, data SHA256
f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562.
All5,242,880 bytes are now retained locally and hash-verified. No native
request was repeated during either probe or full file recovery.

Retrieval exposed two host-utility compatibility problems after that helper
had already ended. The first attempt rejected double-LF base64 framing. A
normalizing adapter then fetched PID/stat but rejected the first data chunk:
the legacy `tr -d '\n'` pipeline had removed characters from base64 instead
of removing line breaks. Exact counts/hashes prevented accepting corrupted
bytes. Both failed host records and the original adapter are preserved.

The second adapter removes that exact `tr` segment from forwarded ordinary
file reads, preserves the actual raw authenticated command/response, and
normalizes only canonical base64/LF output in host memory. Recovery replays
the original21 calls locally, including the one native execution, then
forwards only file metadata, file retrieval and cleanup. No controller
request is repeated. Source/native-wrapper provenance and wire rewrites are
recorded explicitly. Recovery2 completed and removed the probe stage.

The full helper's stdout exposed one asynchronous GC prefix interleaving:
`[GC_INFO] ` appeared before the self-test JSON, while the following GC_End
line lacked that prefix. The raw log and failed host record remain unchanged.
A third adapter, pinned to that exact completed record and adjacent line pair,
moved only the displaced prefix in the host-facing log. It replayed all19
original calls locally, then forwarded228 ordinary-file reads/metadata/cleanup
calls. No new USB read occurred. The complete full stage is absent.

The raw-replay audit now verifies247 full-record calls, the complete final
record state, all raw authenticated envelopes, each wire rewrite, the exact
reconstructed local files,640 chunk hashes and lifecycle fields. The full
image repeats the32KiB probe and all six separate sector fingerprints.

| Comparison range | Result against selected package |
| --- | --- |
|Header0..0x200|13 changed bytes|
|First slot after header0x200..0x40000|217090 differing byte positions|
|Entire second slot0x40000..0x80000|Exact256KiB match, SHA25656bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf|
|Tail0x80000..0x500000|39 changed bytes|

These are bounded storage-range comparisons, not declarations of executable
function sizes. Overall217142 byte positions differ. Existing image1 analyses
retain byte-level support in the stored second slot; first-image addresses
must be remapped. Runtime callback pointers are the next discriminator for
whether this stored first image is actually executing.

Any partial multi-IN failure can leave the controller request in flight.
Interface release and FD close do not abort the device protocol. Do not
automatically retry or send a new header after such a failure; preserve
the transcript and require re-enumeration/reboot plus state requalification
before a later request. The runner leaves its private stage on failure.

The next diagnostic objective is to map the actual returned image's fault
producer and latch/recovery branches, then decide where reversible logging
or a narrowly targeted patch would provide evidence. No permanent repair
or physical recovery is claimed.
