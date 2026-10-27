# Target file acquisition during source comparison

2026-10-27 UTC. After the first offline source reviews identified missing
installed components, the parent copied ordinary files from the accessible
TV. Researchers continued static analysis on the copied bytes. No SWU or TEE
library function, updater executable, capture API, GPIO operation, controller
request, firmware-write operation or UI key was invoked by these acquisitions.

## Scope and provenance

All remote commands used the existing hash-pinned authenticated root adapter,
its existing model/build validation, and Linux boot guard
`00000000-0000-4000-8000-000000000000`. This was the same Linux boot as the
working BW recovery. Commands read directory metadata, ordinary file sizes,
hashes and file bytes. The adapter's full raw records are retained in private
acquisition directories; only selected metadata was printed.

| File | Size | SHA-256 | Local acquisition |
| --- | ---: | --- | --- |
| `/usr/lib/libteec.so` | 10,892 | `926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70` | `target-file-acquisition-02/` |
| `/usr/lib/libteec_trustware.so` | 30,352 | `0574261e6291fb3f28bf8a254c0610c9177e132a6afd0bc7418826173555db81` | `target-file-acquisition-02/` |
| `/usr/lib/libSWUProductionConfig.so` | 6,440 | `c6af8346f4643f2cf50e996682611ece7ad6ff8999274570023561d1a97879f0` | `target-file-acquisition-03/` |
| `/usr/bin/SWUCoreTV` | 4,980,824 | `b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697` | `target-file-acquisition-03/` |
| `/usr/lib/libteec_trustware_common.so` | 244,580 | `353104729c40d6f1eff4f07b96f8a14466dd98efddb21a9cb7d14752351dd139` | `target-file-acquisition-04/` |

`libSWUProductionConfigRelease.so` is a symlink to the copied configuration
library. Metadata also identified SWUService, SWUVerifierTV, SWUStandalone and
SWUAutoUpgrade; those executables were not run. SWUCoreTV was selected for
static analysis because it contains the actual client call path, rather than
guessing a library filename from another firmware.

The [bounded copier](tools/acquire-swu-files.py) is dry by default. Its fixed
groups contain only the identified regular files, known sizes and hashes.
It reads chunks of at most 24,576 bytes, validates every chunk length, checks
the whole remote hash before/after and the reconstructed host hash, and
promotes a partial file only after those checks. It has no retry, target-file
write, arbitrary-path option or target-library invocation. The exact source
revision used for each multi-chunk run is retained alongside its records.

## Stored key selector

The `target-swu-selector-05/` configuration sample at uptime
163635.32–163635.40 recorded stored
`db/menu/support/softwareupdate/isSubmodelKeyType` was False. Both encrypted
items files were 416 bytes. The master file SHA-256 was
`d8af420d63b9cb2643783c56ce7396a5fd4d809e48df0bd321781cfd025e8220`;
the submodel file SHA-256 was
`bb1ab330400743923bd06c3e8479da13ae61e699e2c39fe21227b176ac096e2f`.
The normal client path therefore selected the master at that sampled time.
Only stored configuration and encrypted-file metadata were read; the encrypted
blob bytes and any plaintext key were not copied by that sample.

## Failure retained and corrected

The first wrapper-library transfer completed, but the host parser rejected its
format because the shell marker newlines were overescaped. The raw response
was preserved. The correction normalized only the three known marker
delimiters on the host, then verified base64, exact length and matching
before/after/local hashes against that original response. The wrapper was not
read again. Subsequent transfers used hash lines and base64 without those
markers. See `target-file-acquisition-02/host-parser-correction.json`.

This was a host parsing failure, not a failed TEE operation; no such operation
had been attempted. Future analysis must preserve that distinction.

## What acquisition proves

It proves the identities of the copied installed ordinary files on the
recorded boot and enables architecture/ABI/dataflow analysis. It does not
prove that a trusted application accepted a call, that the secure daemon's
policy allows this root context, that an encrypted section decrypts, or that
an updated image can be installed or restored. The metadata-decryption design
must follow the actual client frames and buffer/length semantics rather than
deploy the unrelated parts of an upstream Probe.
