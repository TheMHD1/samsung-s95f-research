# Fixed-file preflight diagnostic source audit

This standalone project diagnoses the frozen BX adapter's file-preflight refusal. It cannot proceed to selector access, target-library loading, TEEC, SWUCoreTV, updater, or a subprocess. No target operation was performed to build or test it.

`Program.cs` contains the complete implementation. The project has no project/package reference and nine P/Invoke declarations, all to libc: open, close, read, realpath, two syscall signatures, getuid, geteuid and alarm. Main accepts no target arguments, requires ARM32/little endian/root/the fixed boot, and visits exactly the same six fixed input paths with pinned sizes/SHA256 and four ELF Build IDs. The host-only self-test requires x64 and reads only a newly created public fixture; default x64 execution refuses with exit 64.

The original syscall declaration is reproduced without `[Out]`. Each stat observation also calls a second declaration with explicit `[Out]`, reporting rc/errno/mask/mode/size and identity-field agreement. Guard decisions use only the original result. The extra syscall can help distinguish copy-back behavior, but neither successful host behavior nor disagreement alone establishes the target refusal's cause.

Original numeric open flags `0xa0000` are deliberately retained for reproduction. They include O_CLOEXEC and ARM O_LARGEFILE; they do **not** include ARM O_NOFOLLOW. The output explicitly identifies this defect. This diagnostic does not repair or qualify the frozen adapter. A future live revision must use architecture-correct O_NOFOLLOW independently of this diagnosis.

The fixed preflight checks preserve the original canonical-path, regular/non-group-or-other-writable mode, exact size, complete read/EOF, before/after stat identity, SHA256 and ELF identity/Build-ID predicates. Enum-only reasons and fixed stage/file labels are emitted; arbitrary exception text, file data and newly computed content hashes are never printed. Read data is wiped and opened descriptors/buffers are released on all ordinary rejection paths. Exit 65 means at least one file failed; all six files are visited and no subsequent activity exists even on complete success.

The process requests alarm(25), but does not explicitly reset/unblock SIGALRM. The central runner should retain an independent outer deadline; this diagnostic is not a timeout-containment qualification. A blocking filesystem call can prevent completion until a signal/outer control acts. Successful libc calls may leave errno nonzero; rc is authoritative and errno is diagnostic only.

Host verification: Release build passes with zero warnings/errors; fixed public-file preflight passes; wrong-size and wrong-hash fixtures reject with their exact enum reasons; original/explicit-Out stat fields match on host; default host entry rejects before any target-path access. These tests do not qualify ARM CLR marshaling or execute retained target libraries. `build-manifest.json` records exact output hashes, test exit codes and source provenance. The binary is portable net6 IL, not a native ARM cross-built executable.

DLL SHA256: `6d86dc4c214f8ad39abc61aeb006d65ee7b65243ea944cb70cf03d730988e3a6`.
