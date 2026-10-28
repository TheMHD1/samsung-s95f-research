# EP: five fixed lane-gate/source fingerprints

This additive reader is host-built and fake-tested only. It is not executed on the TV by its author. It proposes exactly five read-only target0x101 pairs, in the fixed order below, with324input bytes,5headers and10bulks. It has no data-write, mask, key, UI, reset, retry, alternate bank, storage, POFLG, hook or scratch operation. Its purpose is sampled source correspondence before any separately reviewed lane diagnostic, not authorization for a later write.

| Role | Bus address | Bytes | Selected image1 VA |
| --- | --- | ---: | --- |
| Root getter, padding and root-pointer literal |460038fc|12|38fc|
| Caller root save |4600bd6c|8|bd6c|
| Operating mode and SB construction |4600be0c|44|be0c|
| Four local lane gates including570 |4600beb4|228|beb4|
| Required AA/AC/4cc/secondary literal adjunct |4600c030|32|c030|

`ek-source-pins.json` records the exact expected SHA256, source offsets and little-endian12-byte read headers for all five regions. They are copied from frozen EK inventory`caca76ba6a9dfe3bee8df33d198e38c836710abff7e65470393840ab063ef0f8` and selected package`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Every complete interval is word-aligned and within the selected source-qualified image1 code/resource alias. The fourth region contains the actual local primary-bit0 test; the fifth binds otherwise unmeasured PC-relative literals. The expected root value is still mutable data elsewhere: this reader does not claim current root/table admission from a code literal match.

The fixed reader derives from reviewed DX. `NativeBinding.cs` is byte-identical to both DX and EB, using the qualified native GETDRIVER/native directory device+inode identity contract. It does not reintroduce the managed sysfs alias resolution bug. `Controller` and the resource acquisition/release/close sequence are byte-identical to DX. Source verification checks these relationships against frozen hashes. Metadata and FD identity checks, local claim provenance, three binding snapshots and input/OUT allowlists remain. `--device N` binds the fresh bus7/interface2 node; it cannot select an address or operation. ARM32/little-endian/16-byte ioctl-struct/root/boot/descriptors checks still precede production I/O.

The cooperative native transaction budget is40seconds, per-bulk timeout2seconds, root45seconds and host75seconds. There is no native hard40second alarm. Before starting a pair, the controller reserves4seconds; after an exact accepted header it owes the matching IN even if the clock errors. A short/overlong/throwing header or IN sets Unknown, stops every later header and is never retried. Root timeout/host cleanup are not proof that uninterruptible kernel I/O terminated.

After each complete pair, the native code retains that window and checks its exact expected hash. A mismatch stops immediately with a retained completed-prefix window, ReadyForHeader if the pair was exact, false acceptance and successful resource cleanup where possible. Partial-IN storage is not represented as a complete window or hashed as a successful sample. The receipt retains the count/error/phase and any previously completed windows; an uncompleted buffer is not promoted into evidence of source correspondence. No mismatch causes a fallback, second invocation or a projection through the success parser.

The strict offline parser accepts only the full5/10 successful contract: exact fields/types, binding snapshots, ordered steps/phases/counts, monotonic brackets and fixed window identities, including independent hashes of decoded canonical Base64. It rejects incomplete/mismatching/failing receipts. The wrapper saves the exact root envelope, native receipt and terminal exit before requiring success. A nonzero native exit therefore remains a refused original wrapper outcome, with the stage retained for separately reviewed reconciliation. Success stores the five private raw files and interpretation, verifies the exact9-file remote inventory/hashes, and removes only those names plus the directory. Diagnostic GC stdout is separately bounded and never parsed as semantic JSON.

Structured JSON is written to an exclusive0600 receipt in a fresh0700 nonce stage `/tmp/researcher-ep-<32lowercasehex>`, opened before production I/O. Target raw code bytes are held in memory and in that private receipt only; they are never printed to diagnostic stdout. The native fixture/selftest entrypoints use FakeOps, never device I/O. The324bytes of bounded selected-package excerpts in HostTests are test data and never executed. They are not a redistributed firmware image. Raw target captures/identity-bearing fixtures, host environments and binaries require the existing private/public publication boundary.

Only error rendering was bounded outside the inherited Controller/lifecycle: each error retains a prefix limited to128serialized JSON bytes. This cannot turn failure into acceptance. The fixed flow has at most six clock/outer-catch/cleanup messages; the adversarial proof uses eight, all10maximum-width steps, all5maximum-escaped Base64 windows, three malformed maximum-width binding records with255-character names, and19-digit timestamps. The worst serialized envelope is19951bytes including newline, below24576by4625bytes. Success and late failures are tested. The wrapper keeps stdout16384/stderr2048 and root response65536 caps separately.

`run-once.py` defaults to a zero-operation dry run. Execute requires the reviewed manifest SHA, fresh private output, and an exact `ep-lane-code-fingerprint-readiness-decision-v1` whose digest binds the current identity, interface-unbound/no-holders observations and explicit centrally justified first-header lineage. Readiness is not an endpoint queue probe. The separate dry-by-default prepare-readiness.py requires exact wrapper/manifest hashes, validates all supplied identity/premise fields before loading a root adapter, and adds one fresh cached metadata/census observation without any vendor transfer. Its evidence references are rehashed after observation. The wrapper performs fresh cached metadata/census before staging and again before its single production invocation; immediate metadata is checked in the same invocation command. A prior receipt or empty census alone is not a fresh phase proof. No helper, author test or manifest generator invokes the root adapter or TV.

Reproduce host work with the retained .NET6 SDK and cleared NuGet sources:

```sh
sh build-host.sh
python3 -B verify_source.py
python3 -O -B verify_source.py
python3 -B finalize_host.py
TMPDIR="$PWD/host-environment/tmp" python3 -B test-runner.py
TMPDIR="$PWD/host-environment/tmp" python3 -O -B test-runner.py
python3 -B run-once.py
```

The build uses only task-owned DOTNET_CLI_HOME, TMPDIR and NuGet cache; it does not repurpose HOME/CODEX_HOME or copy the SDK. Final manifest and source inventory are frozen after the reported checks. Parent/independent reviewers must approve those exact pins before the coordinator performs any target operation.

Even five exact matches establish only these324sampled bytes at the alias and capture times. They do not prove active instruction fetch, whole-image identity, every writer/caller, physical lane identity, code writability, hook safety, runtime mask restore, electrical safety or a fault fix. No mask experiment is included.

Final host qualification: build0warnings/0errors;1571native fake checks;63source-lineage checks,1531wrapper/parser checks and87readiness checks in each of normal/optimized Python. Wrapper tests syntax-check305commands with maximum7828bytes; readiness mocks check6commands with maximum4194bytes. Actual late-clock plus both-cleanup-failure coverage records six bounded errors after one completed pair, with no next header. No production target invocation was performed.
