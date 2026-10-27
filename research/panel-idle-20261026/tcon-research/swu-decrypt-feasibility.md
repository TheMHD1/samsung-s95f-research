# SWU/TEE firmware-decrypt feasibility: cipher-only boundary

## Decision

**Not ready to invoke.**  An ARM32 CLR program could in principle reproduce
the local Python client's three-command cipher flow without calling a firmware
installer or flash writer, but the current evidence is source-level and
cross-model.  The exact installed `libteec.so`, its kernel transport, the SWU
trusted application, its access policy, and the current TV's ABI/profile have
not been pinned by a read-only runtime inventory.  There are no copied
`libteec`, SWU client, or TEE-driver binaries in the panel-idle evidence
directory to statically validate that boundary.

The next safe decision point is a **read-only compatibility inventory**, not a
test session and not a decrypt attempt.  It must establish the items in the
gate table below on this exact boot.

## What the existing local client actually does

The local source files are:

| local source | SHA-256 |
| --- | --- |
| `${S95F_EVIDENCE_ROOT}/root-access/source/swu/swu_firmware_decrypt.py` | `5eb5dd7ff2ac651de1c074a293aa1fc22b31868376eee809380946ede0ae2e5e` |
| `${S95F_EVIDENCE_ROOT}/root-access/source/swu/teec.py` | `668ef67bc8a7a1187ac74b230999fab5397f95b3a0b02472454842e4f3717359` |

`swu_firmware_decrypt.py` is deliberately a decryption client, not an update
client.  It:

1. opens a public TEEC session to UUID `22222221-0000-0000-0000-000000000001`;
2. allocates three 64 KiB shared-memory buffers;
3. invokes command 0 once with the encrypted production-passphrase blob and an
   8-byte section salt, selecting SHA-256/AES-256/decrypt values;
4. invokes command 1 for AES-block-aligned ciphertext chunks; and
5. invokes command 2 to finalize CBC, then verifies PKCS#7 padding and an
   optional caller-supplied CRC32 before atomically publishing a local
   plaintext output file.

The source contains no firmware-install RPC, reboot, partition writer, flash
device path, or call to Samsung's updater executable.  Its host-visible writes
are its newly-created local output file and temporary output file.  That does
**not** mean the TEEC calls are side-effect-free: command 0 necessarily
initializes mutable secure-world cipher/session state, commands 1/2 process
that state, and the exact trusted application implementation has not been
copied or audited here.

The source itself prevents a second `initialize` in the same client object and
uses a `finally` block that clears its local initialized flag on finalize.
Cleanup of session and shared buffers runs through the context manager even on
client-side errors.  These are useful host-side safeguards, not proof of
trusted-application rollback, transactionality, or harmlessness.

## Independent author documentation

The original author’s current model-specific research note documents the same
normal SWU request sequence for a **different** `QE77S95FATXXH` Tizen 9,
firmware 1296.8 system.  It describes AES-256-CBC MSD sections, command 0
initialization, command 1 streaming, command 2 finalization, padding removal,
and CRC validation.  It also explicitly says that no firmware was flashed,
modified, or written back in that research.

That supports the architecture of the local client, but does not establish
compatibility with `QN77S95FAFXZC`, its installed SWU TA, a different regional
build, the current Tizen revision, or the official archive parent is acquiring.
The author’s document is an original reverse-engineering source, not Samsung
support documentation and not a substitute for per-device ABI verification.

Source: [hTobi02, *QE77S95F 1296.8 firmware decoding*](https://github.com/hTobi02/TizenWLED/blob/master/docs/FIRMWARE_DECODE_QE77S95F_1296.md), retrieved 2026-10-27.  The author’s short protocol description is within the source’s own stated QE77S95F/Tizen-9 scope.

## Why ARM32 CLR P/Invoke is technically plausible but unproven

`teec.py` explicitly models a 32-bit little-endian ABI:

- pointer, TEEC context, and session-handle sizes: 4 bytes;
- `TEEC_SharedMemory`: 36 bytes;
- modern `TEEC_Operation`: 56 bytes;
- registered-memory reference parameters and four type bytes packed into the
  operation word.

Those structures can be represented with fixed-layout CLR structs and
`DllImport`/PInvoke calls on an ARM32 CLR runtime.  The needed exported API
surface is finite: `TEEC_InitializeContext`, `TEEC_FinalizeContext`,
`TEEC_AllocateSharedMemory`, `TEEC_ReleaseSharedMemory`, `TEEC_OpenSession`,
`TEEC_CloseSession`, and `TEEC_InvokeCommand`.

However, a managed program must not treat matching field sizes as sufficient.
Native structure packing, `libteec.so` architecture, exported symbol ABI,
kernel/TEE transport, session authorization, and TA command behavior all need
current-device evidence.  No CLR implementation is created or proposed by
this review.

## Required read-only gates before any further feasibility decision

| gate | exact evidence required | why it matters |
| --- | --- | --- |
| OS/profile | `/etc/os-release` proves the expected Tizen major; current ABI accepts `modern` only for 9 | the source refuses unverified releases |
| native library | installed `/usr/lib/libteec.so` path, ELF class/machine, full hash, export list, DT dependencies | P/Invoke target and ARM32 ABI must be exact |
| kernel transport | read-only device/module/sysfs/map evidence naming the library’s actual TEE backend | source code does not prove which driver is active |
| SWU TA availability | session/TA registration metadata, if available without opening a session; otherwise this remains an invocation-only unknown | UUID alone is not availability or permission proof |
| access policy | documented/static evidence for `TEEC_LOGIN_PUBLIC` on this build | root access does not imply TA authorization |
| encrypted input | existence, size and hash of the passphrase blob **without disclosing its bytes** | command 0 needs the installed blob; it is sensitive material |
| source/ciphertext | host-only official MSD archive hash, section offsets/lengths/salt/expected CRC, exact region block alignment | prevents using guessed data or a wrong section |
| output containment | a newly allocated, mode-restricted destination outside TV system paths and an exclusive publication policy | decryption emits sensitive plaintext on the host filesystem |

The current evidence establishes none of the runtime library/transport/TA
gates above.  It therefore does not justify creating a managed P/Invoke tool,
opening a TEEC session, invoking command 0, or reading the encrypted
passphrase blob.

## Side-effect and verification boundaries

| operation | source-level behavior | unproven/important limitation |
| --- | --- | --- |
| command 0 | supplies encrypted passphrase plus salt and initializes cipher state | may change TA session state; access/policy unknown |
| command 1 | sends ciphertext and receives output through shared memory | implementation could enforce quotas, logging, or other policy; TA body absent |
| command 2 | finalizes cipher state and returns final bytes | source cleanup does not prove secure-world rollback after failures |
| CRC check | local client can reject mismatched plaintext before final local rename | only meaningful if the official MSD table/CRC is independently pinned |
| firmware installation | absent from the reviewed Python flow | absence from this wrapper does not prove all SWU services are non-writing |

No secret, passphrase byte, key, decrypted firmware data, or update container
was extracted during this review.

## Conclusion

There is a bounded, source-supported **cipher-only API shape**, and an ARM32
CLR P/Invoke implementation is technically representable.  It is not yet an
approved safe operation on this TV.  The necessary next step, if it becomes
useful after the official MSD archive is verified, is a dedicated no-session,
read-only inventory that pins library, ABI, transport, TA availability
evidence, and input/output containment.  It cannot diagnose or repair the
current RT-protection/black-picture issue by itself.
