# EB fixed lane-gate reader

Host-only derivative of frozen DT, qualified by frozen EA read plan SHA256
`35cf50b7794d859629c7dd526c455af2756585d0b7269f5d071fa5f0f5d76878`.
No target execution has occurred at this checkpoint. The coordinator alone
controls any later target action after independent source review. This reader
has no target write, key, UI, reset, MODE2, retry, background loop or arbitrary
address/length option.

EB preserves all14 DT windows and their relative order. Immediately after
Diff, before the two fixed-reference candidates, it inserts exactly:

| Window | Fixed target | Bus address | Bytes |
|---|---|---|---:|
| primary-lane-gate |0x101|0x47010470|136|
| secondary-lane-gate |0x101|0x4700cb94|68|

Full success is **16 headers,32 bulk calls,16 retained windows**. These are
selected image1 SRAM windows corresponding to CPU0x20010470 and0x2000cb94,
not a generic memory scan. Primary covers68 little-endian halfwords, and
secondary covers68 bytes, for lanes568..635 with xBase0. The scope excludes
other possible lanes, including the observed562/563 pair.

Before any of the four added gate/reference headers, completed start-R/M/C
must establish root0x20010000, packed bytes2880, lanes1920, xBase0, C geometry
2160/1920/2880 and **operating mode below6**. The mode is R+0x10, not a
record/predicate category. Operating mode4 is permitted; category1 is a
different field. A mismatch refuses at ReadyForHeader after the original
first10 read pairs, with no gate or fixed-reference header.

The parser retains all68 primary halfwords and secondary bytes and reports
the selected-source local-admission predicate at the sampled values:

```text
SB = ((M.aa == 1 or M.ac == 1) and byte[CPU0x200004cc] != 0)
locallyAdmittedByCapturedTables = ((primary_halfword & 1) == 0) and (secondary_byte == 0 or SB)
```

AA,AC and4cc are retained M offsets10,12 and44. Only the primary low-byte
bit0 is tested by the recovered gate; its other bits are retained. The
samples and context are sequential and non-atomic. Local table admission
also requires the loop to reach that lane: an earlier comparator returning0
can exit the loop at0xbfac. `localEligibilityOnly` is true and
`actualComparatorCallProven` is false. These samples do not establish
historical gate execution, a past comparator call, physical lane mapping,
safe modification, or a root cause. DX's successful code fingerprint did
not cover this later gate body; `gateBodyLiveFingerprinted` remains false.
R/N equality does not prove an unchanged epoch. Five record columns and fixed
reference candidates retain DT's stale/partial-clear/selection caveats.

DT's Controller and NativeBinding are byte-identical. The inherited contract
includes exact boot/bus7/interface2/current device and cached descriptors,
native FD identity, preclaim absence, local claim tracking, kernel GETDRIVER
plus native canonical device/inode comparison, phase/clock checks, matching
IN obligation after an accepted header, and finally release/close. Failed or
short/ambiguous transfers stop without another header. A completed short pair
is not accepted. No managed symlink resolution or new control-transfer path
is introduced. The inherited40s cooperative native deadline and remaining
pair budget do not guarantee cancellation of blocked kernel I/O; outer root45s
and host75s bounds remain unchanged.

`run-once.py` is dry by default. Execution requires the exact manifest SHA and
an accepted current readiness file+SHA with schema
`eb-rtp-lane-gate-readiness-decision-v1`. The coordinator must establish exact
identity, no holders, unbound interface and the closed-world ReadyForHeader
lineage; the wrapper does not promote a metadata census into endpoint queue
proof. It uses DT's pinned root/passive-wrapper dependencies and one private
`/tmp/researcher-eb-<32hex>` stage. Three pinned payload files are staged once,
exclusive-file fake selftests run, metadata is rechecked, then native executes
once. The separate exclusive0600 receipt, not GC-mixed stdout, is parsed.
Accepted completion saves all raw windows, verifies final metadata and exact
stage inventory/hashes, then removes only the known nine files and stage.
Any ambiguity/failure preserves evidence/stage for central reconciliation;
there is no retry or automatic recovery.

Native receipt cap remains24576 bytes, diagnostic stdout16384,stderr2048 and
root response65536. Tests exercise the actual serializer with adversarial
Base64 escaping, long timestamps and a late error. `host-environment/` is
private generated SDK/test state, including developer credentials created by
the SDK; it is excluded from inventories and must not be published.

Build with the retained .NET6 SDK using task-owned HOME/TMPDIR. Host-only
validation uses native`--self-test`, `verify_source.py`, `test-runner.py` and
optimized Python repeats. Tests use fake device operations and cover every
transfer's short/exception path, packing/mode refusal before new reads,
ownership/cleanup failure, clocks, exact headers, gate truth tables, raw
provenance, parser mutations, exclusive receipts and bounded wrapper commands.
These checks qualify source/host behavior; no new runtime observation or
protection-bypass result is claimed.
