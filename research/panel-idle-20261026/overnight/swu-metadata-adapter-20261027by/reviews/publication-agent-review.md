# Independent BY compatibility and orchestration review

Result: no new material defect found in the bounded BX-to-BY revision. The reviewed BY source and deployment inputs are suitable for one centrally coordinated attempt with the existing acceptance/refusal rules. This is source/host evidence, not proof of ARM runtime compatibility, TA acceptance or successful decryption. This reviewer performed no target operation and did not modify implementation, deployment or existing test artifacts.

## Observed failure and actual repair

The BX target attempt stopped at file preflight, before selector/TEE construction. The subsequent file-only diagnostic returned statx success on all six fixed files. The envelope returned mask `0x7ff`; five installed files returned `0x7df`, lacking `STATX_ATIME=0x20`. Both tested native signatures agreed. BY therefore repairs a demonstrated sufficient rejection predicate rather than removing an unexplained check.

`RequiredStatMask=0x3df` requires TYPE, MODE, NLINK, UID, GID, MTIME, CTIME, INO and SIZE. Independently checked against the retained version-pinned Linux UAPI, these cover every optional field consumed by `Identity`, the regular/non-writable mode predicate and the size predicate. Identity retains bytes 16..47 (nlink/uid/gid/mode/inode/size) and 96..143 (ctime/mtime and device numbers). It does not consume atime or blocks. Device numbers have no optional request-mask bit; regular-file rdev values and structure padding are not newly authorized metadata fields. BY still requests `STATX_BASIC_STATS=0x7ff` and rejects any missing required bit. No EOF, exact-size, before/after identity, SHA-256, ELF/Build-ID or replacement check was removed.

The independent ARM `O_NOFOLLOW` defect is also repaired: ARM32 uses `0x8000`, plus `O_CLOEXEC=0x80000` and `O_LARGEFILE=0x20000`, yielding `0xa8000`. X64 uses `0xa0000`. Both constructor and recheck call the shared architecture-selecting function. The retained ARM UAPI octal constants independently support these values. This defect was not established as the earlier refusal cause.

The host suite performs an actual x64 `open` of a final symlink and requires `-1/ELOOP=40`; it also checks both architecture constants. This is a real host guard test, not an ARM syscall test. `PinnedFile` intentionally resolves allowlisted library symlinks before opening the resolved path; `O_NOFOLLOW` protects that final resolved component. It does not claim to reject every symlink in every parent path. Non-library fixed inputs still require canonical-path equality, and resolved libraries remain hash/identity/ELF pinned and descriptor-loaded.

## Bounds, diagnostics and cleanup

`Core.cs` is byte-identical to BX. Operation storage remains 60 bytes including backend offset 56, full-byte parameter-type words are unchanged, and only commands 0/1/2 are reachable. There is no new fallback, arbitrary input, path override, command option or plaintext output. The live main path requires ARM32/little-endian/root/boot identity before the six fixed pinned readers. The envelope path is consistently the BY stage.

Constructor failures zero any allocated data and close the fd only when acquired. Recheck closes its temporary fd in `finally`; ownership of the held descriptor remains with `Dispose`. New file-label, stage and reason diagnostics print fixed enums/labels, not paths, exception text, file bytes, key material or plaintext. Original identity/length/hash checks remain intact.

One bounded diagnostic limitation remains: a `PreflightException` thrown by a selector-triggered `Recheck` *inside* unchanged `Core.Run` is converted by the core's generic catch into `LocalFailure`; it will not retain the outer file/stage enum in the printed result. It still stops the sequence and performs cleanup. The new detailed top-level diagnostics cover initial file construction and checks outside the core; they should not be described as preserving every later internal recheck reason.

The central runner differs from reviewed BX only in the literal stage path. `Program.EnvelopePath` agrees with it. Its manifest binds the current BY source and four payload files; all nine manifest entries were independently rehashed. At most one native dispatch is possible. Upload, framing, native-contract, selector-count or manifest failures do not retry or create success records. Ambiguous/failed stages are retained; removal is bounded to the exact stage after terminal native cleanup acceptance. Output remains explicitly unvalidated metadata with plaintext unsaved.

## Independently executed host checks

The exact BY assembly was executed with `--self-test`: PASS, including 3 golden frames, 8 TEEC failure stages, 3 count overflows, 12 allocation faults, 3 selector-drift cases, SHA-256 known answers, file guards, masks `0x7ff/0x7df/0x3df`, all 9 missing-required-bit refusals, both flag constants, actual x64 no-follow refusal, safe size/hash diagnostics, four ELF pins and seven versioned *mock* exports. Vendor ELF inputs were read/parsed, not loaded as native libraries.

The same assembly's default x64 invocation returned 64 with `REFUSED_ARCH_OR_ARGUMENTS target_calls=0`. Runner tests passed all six mocked cases under normal and optimized Python. To respect ownership, the tests were evaluated in memory with only their initial deployment-manifest rewrite suppressed; the existing frozen manifest was read and independently verified, and all execution target requests remained fake. Temporary test fixtures were cleaned by their tests. No shared implementation/test output file was rewritten.

The existing exact-assembly deadline record reports SIGALRM exit -14 at 25.026 seconds. Its assembly hash matches the reviewed DLL; this reviewer did not repeat the 25-second test. Runtime constructor/callback/daemon behavior and trusted-application acceptance remain for the centrally recorded target attempt, with no automatic retry or broad success claim.

## Reviewed input hashes

| Input | SHA-256 |
| --- | --- |
| Core.cs, unchanged from BX | `6d55fbbac9a7fd0d426f28458809b0d43ddd4f4a8a1fdb937eac2d0d90ddba11` |
| Native.cs | `b226f305431eebc1c56011b2f55f15b2b0ddad700d85a2745e2f95cfb1a6068f` |
| Program.cs | `2ceca356a44f382115d3f4759c562f6d685af5200909cf90937297f79f94dd53` |
| HostTests.cs | `a25acbf74a0bd96815dd4a2fc7c883923e08a10fcab3db712aedaffddebf31f3` |
| run-once.py | `645c9cf391b85dc94f2d74807e30d8eb072353a39ab448c4e3143ae23d1d8563` |
| test-runner.py | `a33505b4f924ae117e14571e953a2f052292134cd2c6250b33b4d4453670780f` |
| SwuMetadataAdapter.dll | `028bcfa1641a1794a27283adf9adf1af9de2e22bb4dc54176fdf2b2fa02f2d60` |
| host_mock.so | `c520f4dbaccc91af3d85de41634c6b0cb5d3bf2054fb1b88eeec666591b5c35d` |
| Header envelope, bytes not reproduced | `6da1e2386f0f97a180984f249febaf831febfee1adb35a8cefa96f89ad069e0d` |
| deployment-manifest.json, all 9 entries verified | `0f7e7ceac5215322c51a699bff608d45284e74c80e20bebe7223140dc310e14e` |
| ABI reference inventory | `44579cf6f97cce296761d04f44bc2a5bc063257b2d106f261afc841ab3e77e93` |
