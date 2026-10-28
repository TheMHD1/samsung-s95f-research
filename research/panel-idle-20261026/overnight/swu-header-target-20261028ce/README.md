# CE: private authenticated firmware-header acquisition

This additive candidate reuses BZ's exact fixed metadata TEE command0/1/2
frames, blob/envelope/library pins, selector checks and cleanup. It changes
neither TV firmware nor controller state. Its only new output is a fixed
4032-byte private quarantine file after successful authentication. No live
argument selects an input, output, address, key, command or algorithm.

The installed PUBLIC PEM is pinned to426bytes and SHA256
ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3.
Its CRC is860be2ed, RSA size2048bits, signature extent256bytes. Authentication
is relative to this selected installed key, not a separately established OEM
certificate chain. The exact source-backed whole-plaintext CRC iscbcf1d91.

Core invokes the new synchronous consumer only after all three commands,
validated returned counts totalling exactly4032 and the final selector check.
Native final count now contributes to total. Existing default consumers,
frames, error containment, reverse cleanup and wiping are preserved. The
consumer clones the private span, runs the exact pinned CC authentication
source, writes only on Accepted and wipes its copy in finally. Core's native
private buffer and all shared buffers retain their existing wipe paths.

CC requires exactly one CRC-fitting raw or canonicalPKCS7 representation,
key identifier/signature size, RSA PKCS1 SHA512 over the exact signed remainder,
and bounded OUIT root framing. Nested bodies remain opaque in this subset;
full_schema_validated, metadata_published and firmware applicability remain
false. The retained file is the ORIGINAL raw4032 aggregate, possibly including
PKCS7. Its SelectedBytes/PaddingBytes/Representation must accompany use.

The fixed output path is inside the parent's fresh root0700 stage. Creation
uses WRONLY|CREAT|EXCL|CLOEXEC plus architecture-correct NOFOLLOW/LARGEFILE,
mode0600. Regular mode, uid, nlink1, initial/final sizes, one exact write,
fsync and close are checked. Short/failing output keeps a private unaccepted
partial file and causes no retry. A successful file write occurs before TA
cleanup; later cleanup failure still rejects the overall result.

The runner is dry by default. A reviewed manifest digest is required for one
foreground target invocation. It preserves private transport/native output,
requires exact successful native/authentication rows and consistent aggregate
counts, then fetches the4032-byte file with private framing/hash checks. Its
independent Python cryptography/zlib verifier repeats unique representation,
installed-key binding, SHA512PKCS1 verification and the pinned prior Python
OUIT framing model. Only then is a local0600 raw file promoted inside the
private local output directory. Full schema validation remains false.

Cleanup is gated on all these checks, exact seven-file inventory/modes/input
hashes and private output hash/size. Any ambiguity retains the stage and makes
no new native call, write retry or recovery action. Root timeout45sec and
native default/unblocked SIGALRM25sec are inherited; abrupt termination cannot
promise TA rollback or normal finally execution. Library constructors and
cryptographic-provider initialization may run. Target provider availability
is a measured prerequisite, not established by the x64 host tests.

Host validation: inherited mock/frame/file/binding suite passes;32 extra
integration checks cover callback ordering, exception cleanup, actual4032+0
and short4031+0 counts,4016+16 aggregation, native-failure suppression,
exclusive output/symlink/count refusal. Independent host verifier tests cover
53 signed fixtures and12fake-root orchestration cases in normal and optimized
Python (839checks, maxcommand4721bytes). No root adapter or TV is used by tests.
CC itself has1018checks and separately retained synthetic signer/CRC provenance.

Actual decrypted metadata and its private transport envelopes must remain
outside public exports. Authored code/reports and public acquisition facts can
be published with the project's existing origin/license/privacy workflow.
