# Independent HC source/protocol review

**PASS_HOST_ONLY_SCOPED. No blocking finding in the frozen fixed snapshot/archive CLI.** This approves the reviewed host contract for the parent's separately bound root adapter; it is not a target execution, live utility compatibility attestation, kernel instrumentation enable, MODE2 approval or physical recovery result.

Reviewed author inventory: `26c311d11a845dad76a02370259bb4ed997312406269da1df669c7f91d718621` (10 files). CLI `stock_log.py`: `f6730ccd8c9dd8bc928a60eb602e03f6aa9592f12d5a474f1d304fabf495ccf4`; README `609f0f2b5e6d69db4fc4da4949f611a02b6c74476455cbb056f697d9f6fe832b`; checkpoint `39bf2ffb2aa046c0a8884cc4ca99571e3935aa6a8f1b35a3ade7c877c3efee0d`. All inventoried bytes and16 retained source/evidence pins remain exact. No author files were modified. All review writes and temporary files are under `reviews/`; no generated command was executed and no target/root/network calls were made.

The fixed capture command is backslash-free, validates the exact syntactic nonce/boot, UID0 and boot before capture, creates an exclusive private stage, and executes plain `dmesg` once under a file-size limit. It does not request clear/read-clear, use alternate dmesg flags, enable tracing, select GPIOs, issue USB requests, invoke a recovery helper or remove remote files. It rechecks boot after dmesg and requires the two expected ordinary private files before its terminal metadata frame. Files already created remain remotely retained on refusal/ambiguity. The implementation-dependent shell file-limit unit is correctly distinguished from the independent accepted byte caps.

The snapshot frame has exact ordered fields, canonical LF framing and bound sizes. Fetch commands are restricted to two fixed files and exact chunk extents; they check stage ownership/mode, regular/no-symlink files, inventory, sizes and whole hashes, and recheck both hashes and boot before terminal completion. The maximum is64 raw chunks plus1 stderr chunk,66 commands including capture;16KiB chunks fit the24k chunk-frame cap and65,536 decoded-response cap. The command maximum is1,390B in reproduced author qualification, below8,192B. Remote45s/host75s authenticated-envelope enforcement remains the central adapter's responsibility. There is no transport or automatic retry in HC.

Host archival checks exact private chunk inventory, chunk identities and canonical decoded base64, assembled file lengths and whole hashes before creating an exclusive output directory. Independent interception confirms both original files and their directory are fsynced before classification. Binary stdout, including NUL/invalid UTF-8/CRLF bytes, is preserved exactly. A deliberately failed classifier leaves the already durable raw/stdout and stderr files, creates no successful analysis, and cannot overwrite the partial output on another archive attempt. Forensic archival of a bounded stderr refusal retains `captureAccepted=false` and its original reason. Remote stage cleanup is never generated.

The retained ELF/source audit reproduces exactly. QDF's critical ERR-skip branch, normal-tail calls and mode2 off/on aggregation are checked against real instructions; its format relocations and marker fragments are pinned. The classifier retains line byte coordinates/hashes, printed timestamps and PIDs instead of inventing a per-invocation success verdict. Historical normal-tail messages, retained event interfaces and partial capability discovery remain historical/scoped evidence. Missing messages do not prove absent execution; log text does not prove current provider, instruction reload, shared fault clear, GPIO voltage, a complete kernel ring or optical recovery. `kernel.raw` is correctly described as the utility's output bytes.

Two nonblocking parser qualifications should remain explicit:

- Chunk framing intentionally accepts base64 line wrapping and, through `splitlines`, CRLF framing. Independent tests verify actual76-column wrapping and CRLF preserve the exact canonical decoded payload, which is subsequently checked against its whole-file hash. This is not a claim that every accepted chunk frame has one canonical newline representation.
- Receipt revalidation compares Python values using equality, so Boolean-equivalent JSON numeric flags can compare equal to generated Boolean flags. This does not let a refused capture become accepted:0 cannot equal true and1 cannot equal false. The coordinator should use the freshly generated private receipt bound to its actual frame and authenticated envelope. Strict field-type hardening could be a later version; no author change is required for this fixed provenance-bound workflow.

The root-agent quoting assumption is directly addressed by excluding all backslashes. Shell syntax is qualified with `/bin/sh -n` only. Utility availability/format compatibility, authenticated UID/euid/model/boot binding and exact enclosing root response/exit/deadline checks must be supplied by the current parent adapter. A real first snapshot can still refuse safely; host qualification does not guarantee it will run on the target. No generic model guard was bypassed or target module imported.

## Reproduction and scope

The author host suite was rerun with `HC_TEST_TMPDIR` set to the existing private `reviews/private` directory. Both modes reproduce345 host checks,66 syntax checks and maximum1,390B exactly. Source audit reruns reproduce13,330 checks and16 input pins byte-for-byte in both modes. The independent69-check suite covers the frozen seal, source pins, real base64 wrapping, malformed binding/framing/type/extents/caps, raw-before-classification fsync ordering, forced classification failure, immutable partial output and refusal-preserving archival. Its normal/optimized outputs are identical.

From HC's directory:

```sh
HC_TEST_TMPDIR="$PWD/reviews/private" python3 -B test_host.py > reviews/host.normal.json
HC_TEST_TMPDIR="$PWD/reviews/private" python3 -B -O test_host.py > reviews/host.optimized.json
python3 -B audit.py > reviews/source.normal.json
python3 -B -O audit.py > reviews/source.optimized.json
python3 -B reviews/independent_check.py > reviews/independent-validation.normal.json
python3 -B -O reviews/independent_check.py > reviews/independent-validation.optimized.json
```

This independent review does not qualify a composed HF coordinator or any actual capture. Those require their own source binding and retained actual evidence. The author's frozen10-file seal remains unchanged.
