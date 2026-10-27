# Independent review retained by root

The read-only reviewer independently verified all fixed sector and prefix
derivatives, the native probe/full helpers, their manifests and host checks,
the host orchestration, each recovery adapter, and final runtime artifacts.
No reviewer contacted the TV or changed source/evidence files.

The six sectors each have exact16-command upload/execution/cleanup sequences,
26 zero-I/O tests and OUT12/IN512. The8192-byte prefix has the same lifecycle,
exact counts, repeated initial sectors and16 distinct subsector hashes.
The current returned parser cap/remainder/call-target checks passed normal
and optimized Python. The reviewer required call-target naming because callee
bodies were not in the initial sector set; root corrected those names.

The reviewer required a32KiB continuation probe before the single-request
5MiB run. Both helpers have45 injected cases and no reset/retry/NV-write
path. Source/build review verified fixed geometry, deadlines, native ABI/
identity guards, per-chunk counts/hashes, first-anomaly stop and cleanup.

Host review added exact stage/file ownership/mode/type/inventory guards,
transcript validation, a known-prefix requirement and full-read gating on
retained successful probe evidence. Root found an empty-file compatibility
issue in `%F`; the implementation uses independent regular-file/type and
mode guards instead. Twelve fake transport cases passed normal/optimized.

Actual probe native success was followed by host-utility incompatibilities.
The reviewer independently cleared recovery adapters only after confirming
byte-for-byte replay of old calls and file-only forwarding. The first
normalizer corrected LF framing but strict length checks rejected corrupted
base64 produced by the legacy tr pipeline. The next adapter removed only
that exact pipeline segment from actual file reads and retained wire rewrite
provenance. Probe recovery replayed21 calls and forwarded8 file operations.
The native probe remained one request. Its full raw/runtime audit passed.

The full native run completed once, then host parsing rejected one GC prefix
interleaving. The final adapter is pinned to the exact failed record and
exact two adjacent affected lines. It moves the displaced prefix without
changing total bytes; every raw envelope/log remains preserved. Independent
offline replay proved that all19 old calls, including the only native
execution, are replayed locally before forwarding any file reads.

Final full audit independently confirmed:

-5,242,880 bytes, SHA256f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562.
-OUT12 and640/640 exact8192-byte INs;281ms total; maximum chunk2ms.
-Every chunk count/order/time/hash, successful release/close/sink-close,
 no reported error, and target/host file hashes and sizes agree.
-247 authenticated record calls, first19 identical to the original failed
 host record; recovery only4 metadata calls,223 file reads and cleanup.
-Full record evolution, actual wire commands and retained files reproduced
 offline by audit-backups.py, normally and with Python-O.
-First32KiB matches the probe and all six sector fingerprints match offsets.
-The complete256KiB second slot matches the selected package; header13,
 first-slot-after-header217090, tail39 byte positions differ.
-Both private stages removed, and no repeated controller request.

The reviewer cleared this checkpoint for preservation with the explicit
limits that underlying storage-read status, freshness, active slot,
currently executing identity, physical panel state and repair remain unproved.
