# Target preflight refusal isolated by a file-only diagnostic

This follows [the first failed adapter attempt](target-trial-01.md). The new
diagnostic's complete entry point only reads the six fixed files and calls
libc metadata/read functions. It contains no library-loader, selector,
TEEC, updater, USB, UI or process-launch path. It ran once centrally and
returned normally with exit 65 after reporting all six files. No retry of
the original adapter or TEE sequence occurred.

The diagnostic assembly SHA-256 is
`6d86dc4c214f8ad39abc61aeb006d65ee7b65243ea944cb70cf03d730988e3a6`;
source SHA-256 is
`d064fcb62c2791fe6c8a9120ff0c616aacfbac61938ca1e8e98d662212678b6d`.
The retained independent entry point, host checks and full native stdout are
in the [diagnostic source directory](../swu-preflight-diagnostic-20261027bx/).
Authenticated transport records remain private in local state.

## Actual target result

| Fixed input | statx return | Original mask | Explicit `[Out]` mask | Compared identity fields equal | Original guard |
| --- | ---: | ---: | ---: | --- | --- |
| Staged envelope | 0 | `0x7ff` | `0x7ff` | Yes, before and after | Passed |
| Installed encrypted master blob | 0 | `0x7df` | `0x7df` | Yes | Rejected `StatxMask` |
| Installed vconf library | 0 | `0x7df` | `0x7df` | Yes | Rejected `StatxMask` |
| Installed common library | 0 | `0x7df` | `0x7df` | Yes | Rejected `StatxMask` |
| Installed backend library | 0 | `0x7df` | `0x7df` | Yes | Rejected `StatxMask` |
| Installed wrapper library | 0 | `0x7df` | `0x7df` | Yes | Rejected `StatxMask` |

Both signatures used ARM compat syscall 397, returned zero with errno zero,
and agreed on the returned masks and identity fields. The missing bit is
`0x20`, `STATX_ATIME`. The diagnostic preserves the original guard for its
decision; the alternative signature is never a fallback. The original
adapter reads the envelope first and the master blob second. Its first
installed-file constructor therefore rejects the observed master-file mask.
This reproduces a concrete sufficient refusal mechanism at that predicate;
it does not retroactively reveal every native value in the earlier attempt.

The Linux UAPI explicitly permits individual `STATX_BASIC_STATS` fields to
be unavailable. Access time is deliberately excluded by the adapter's
identity function. Requiring it served no consumed-field check. See the
[version-pinned statx definition](https://github.com/gregkh/linux/blob/v5.4.261/include/uapi/linux/stat.h).

## Required correction and retained checks

The fields actually consumed require mask `0x3df`: type, mode, link count,
UID, GID, modification time, change time, inode and size. Device identifiers
are unconditional statx fields. Access time (`0x20`) and block count (`0x400`)
are not consumed. A corrected revision can keep requesting basic stats but
require those actual inputs, retaining regular-file, permissions, size,
identity, EOF, hash, ELF and path-replacement checks.

The independent ARM open-flag defect also needs correction: ARM32
`O_NOFOLLOW=0x8000`, while `O_LARGEFILE=0x20000`. These are confirmed by the
[ARM UAPI flags](https://github.com/gregkh/linux/blob/v5.4.261/arch/arm/include/uapi/asm/fcntl.h).
Host tests must cover both architecture constants, missing required statx
fields, the observed missing-atime result and actual host symlink rejection.
These are source/compatibility repairs to our research adapter, not a TV
blackout fix. The original BX build and its failed attempt stay preserved;
the correction belongs to a separately reviewed BY revision.

The diagnostic ended with `files=6 failed=5 target_library_loads=0
selector_calls=0 teec_calls=0 data_bytes_printed=0`. No metadata decryption,
panel reset, firmware write or permanent prevention is established.
