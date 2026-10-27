# Managed USB SSB one-shot read

Active, authorized I/O helper; it defaults to dry-run and opens no device unless passed exactly `--execute`.
It hard-codes one request: 12-byte LE header for target `0x203`, address zero, length `0x2000`; endpoint `0x02` exact write then endpoint `0x82` exact 8192-byte read. It claims/releases interface 2 only. No CDC, control request, reset, configuration, detach, unbind, flash, retry, or output file is implemented.

`--execute` requires ARM32 little-endian ABI, pinned boot, an already active/configured/authorized USB `7-1`, the complete retained 116-byte descriptors and unbound vendor interface 2 at alternate setting zero. Exact cached descriptors include only the expected bulk endpoints `0x82/0x02`, each 512 bytes. The bus/device address is constrained and checked again before claiming. The opened FD is checked with `statx` for USB character major/minor identity, then its own cached 18-byte device descriptor is read and compared. ARM EABI `O_NOFOLLOW` is `0x8000`, rather than the generic architecture value.

The shared execution engine records phase returns/errno, exact counts, exceptions, claim/release/close attempts and cleanup outcomes. It accepts only an exact response with successful cleanup. Returned data is a raw candidate, not a verified backup: the device-side firmware ignores the storage-read return before USB transmission. No physical light-output measurement or repair is performed.

`--self-test` uses injected fake I/O through that same execution engine. Its 22 cases exercise nominal completion, failed open/claim, zero/short/overlong/error counts, no IN after failed OUT, changed identity, exceptions throughout the sequence, and cleanup failures. It performs no sysfs/device access. A normal no-argument invocation returns its fixed plan before platform/ABI checks and performs no device access.

The parent replaced the initial implementation before staging. The initial declarative self-test output did not execute failure tests and is not validation evidence. The current real fake-I/O tests pass. Build/test results and file hashes are retained in `build-manifest.json`.

This directory is a prepared experiment. Execution status belongs in the runtime record, rather than being inferred from the existence of `--execute`. Firmware buffer capacity/receive-arm review and independent helper review must be resolved before a live request. These are engineering checks within the owner's authorization, not additional permission requests.
