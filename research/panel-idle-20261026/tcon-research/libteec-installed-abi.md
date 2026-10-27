# Installed `libteec.so`: ARM32 ABI and TrustWare backend boundary

## Result

The exact installed `libteec.so` is a **32-bit little-endian ARM EABI5 shared
object**, so the structure sizes used by the existing ARM32-oriented client
are architecturally plausible.  Its exported TEEC functions are not a direct
kernel-driver implementation, however: the library’s load-time initializer
loads `libteec_trustware.so` with `dlopen`, resolves each TEEC symbol with
`dlsym`, saves the results in an internal table, and the public TEEC exports
tail-dispatch through that table.

Consequently, the next specific ordinary file required to evaluate the actual
TEE transport and session side effects is:

```
/usr/lib/libteec_trustware.so
```

No TEEC library was loaded, no TEE device was opened, no trusted application
was opened, and no SWU command or cipher operation was invoked for this work.

## Provenance

| artifact | value |
| --- | --- |
| installed source path | `/usr/lib/libteec.so` (regular file, not symlink) |
| copied local file | `overnight/libteec-copy-20261027a/libteec.so` |
| size | 10,892 bytes |
| SHA-256 | `926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70` |
| ELF machine / class / byte order | ARM / ELF32 / little-endian |
| ARM flags | EABI5, soft-float ABI |
| Build ID | `80169c30fb9cc031d073eb88350ada39a0dfba67` |
| dynamic dependencies | `libdl.so.2`, `libc.so.6` |
| SONAME | `libteec.so` |
| symbol version | `TRUSTWARE3.0` (private extension `TRUSTWAREPrivate3.2`) |

The accepted ordinary-file copy has a before/after source hash and one stable
boot ID in `overnight/libteec-copy-20261027a/client.stdout` and its manifest.
It explicitly records zero TV device operations.  The separate authenticated
metadata sample confirms the installed encrypted-passphrase path exists as a
416-byte regular file with SHA-256
`d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220`.
No passphrase content was copied or read for this analysis.

## Exact public ABI surface

The library exports the functions required by the existing source client:

| export | Thumb entry address | size |
| --- | ---: | ---: |
| `TEEC_InitializeContext` | `0x48380d11` | 16 |
| `TEEC_FinalizeContext` | `0x48380d21` | 16 |
| `TEEC_RegisterSharedMemory` | `0x48380d31` | 16 |
| `TEEC_AllocateSharedMemory` | `0x48380d41` | 16 |
| `TEEC_ReleaseSharedMemory` | `0x48380d51` | 16 |
| `TEEC_OpenSession` | `0x48380d61` | 24 |
| `TEEC_CloseSession` | `0x48380d79` | 16 |
| `TEEC_InvokeCommand` | `0x48380d89` | 24 |
| `TEEC_RequestCancellation` | `0x48380da1` | 16 |

It additionally exports TrustWare callback/file-descriptor extension APIs.
The copied wrapper itself contains no SWU UUID, SWU passphrase pathname, or
command-0/1/2 constant.  Therefore it supplies a generic TEEC ABI boundary;
it does not prove that the SWU trusted application is installed, runnable, or
authorized.

The wrapper exports are short indirect dispatch stubs.  For example,
`TEEC_InitializeContext` at `0x48380d11` computes the table base, loads the
function pointer at table `+4`, then branches to it.  The following exports
advance through adjacent 4-byte slots.  This static forwarding graph confirms
that validating only this wrapper is insufficient to determine the backend’s
kernel device, ioctl ABI, or access checks.

## Load-time behavior and backend selection

`DT_INIT` at `0x4838070c` branches to the initializer at `0x48380bec`; the
two-entry `DT_INIT_ARRAY` contains Thumb entries at `0x48380cb1` and
`0x483807ad`.  The initializer body beginning at `.text+0x38` / virtual
address `0x483807ac` builds a function-name list, calls `dlopen`, then repeats
`dlsym` for every required TEEC API before publishing the internal table.

The literal backend filename is exactly:

```
libteec_trustware.so
```

The wrapper uses `dlopen` and `dlsym` from `libdl.so.2`, not a `DT_NEEDED`
dependency on the backend.  Thus a normal P/Invoke load of `libteec.so` is not
a metadata-only action: it will run these initializers and attempt to load the
TrustWare backend.  The copied wrapper’s dynamic flag `NODELETE` is another
reason not to use “load then unload” as a harmless compatibility probe.

The backend selection is static and exact; whether the loader can locate that
file and whether the backend succeeds at its own initialization are runtime
questions still unobserved.

## ARM32 layout implications

The exact wrapper establishes the target architecture for any future managed
interop: 32-bit ARM, little-endian, EABI5.  It is compatible in principle with
the existing `teec.py` assumptions: 4-byte pointers and 32-bit TEEC fields.
The existing source's asserted layouts (`TEEC_SharedMemory` 36 bytes; modern
`TEEC_Operation` 56 bytes) remain **source-derived expectations**, not layouts
verified against `libteec_trustware.so`.  The wrapper only forwards caller
pointers; it does not validate those structure fields in a recoverable way.

Accordingly, any future ARM32 CLR P/Invoke program would need fixed-layout
structs and an exact backend review.  It should not infer safety merely from
matching the wrapper’s ELF class.

## Access policy and open-side-effect limits

The copied wrapper establishes no SWU-specific access policy.  It knows only
generic TEEC symbols and has no SWU UUID literal.  `TEEC_LOGIN_PUBLIC` comes
from the existing client source, not from a policy decision recovered from the
installed TrustWare backend or SWU TA.

Opening a TEEC session or invoking a command remains potentially stateful:
the source client’s command 0 initializes trusted-world cipher state, while
the TrustWare backend could also open a device or service during library load,
context initialization, or session creation.  None of those operations was
performed here.

## Next file and bounded follow-up

If it becomes necessary after the separate QDF/RHEA identity question is
resolved, acquire only the exact ordinary installed backend file
`/usr/lib/libteec_trustware.so`, with the same before/after hash, size,
boot-identity, and no-load copier discipline used for `libteec.so`. Its
offline inspection can answer:

1. its ELF architecture, dependencies, and constructor behavior;
2. which device path, socket, ioctl, or TrustWare service it opens;
3. how context/session calls map to that transport; and
4. whether it contains static UUID/access-policy clues.

If that backend dynamically loads yet another ordinary library, the next edge
should be determined from its exact relocations/strings rather than guessed.
No library load, session-open, cipher command, passphrase read, or MSD content
access is justified by the current wrapper alone.
