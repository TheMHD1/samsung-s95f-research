# `libteec.so` ordinary-file copy: independent runtime audit

Recorded 2026-10-27 UTC. This review used only the retained local acquisition
files. It made no TV, root, network, TEE, device, controller or display call
and did not modify the acquisition.

## Outcome

**Accepted as a byte-exact ordinary-file copy.** The acquisition does not
establish that the library was loaded, invoked, bound to a TEE device, or
relevant to the physical blackout.

The raw response `client.stdout` has SHA256
`28f167a64e23fcbe7d48f2772ca5a404bb8d8b4ad7036028faa88a1a0733a09d`.
It contains one authenticated root envelope with:

* model `QN77S95FAFXZC`, uid/euid 0;
* host-assisted persistence and global-system-files-unchanged flag `true`;
* one command, status 0, no timeout, empty embedded remote stderr and empty
  separately retained client stderr;
* exact byte equality between the executed and intended command;
* boot ID `00000000-0000-4000-8000-000000000000` before and after;
* regular, non-symlink source `/usr/lib/libteec.so`, size 10,892 and source
  SHA256 `926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70`
  before and after.

Strict base64 decoding of the complete retained `DATA_START`/`DATA_END`
section yields 10,892 bytes. Those bytes are identical to local `libteec.so`
and hash to the same source value above. The adjacent `manifest.json` (SHA256
`2e469a86f71b6b67f14d16c1c3430dc0a8202fa0c98995b022d499206ba1802a`)
correctly records the byte count, file hash, boot ID, one root call, and raw
response hash.

The target command consists only of regular-file identity checks, `wc`,
`sha256sum`, boot-ID reads and `base64` of the source. It creates no target
file, loads no library, and opens no TEE or other device. The manifest's
`tv_device_operations=0` is consistent with the exact retained command.

The record does not include per-call UTC/uptime, inode or mount identity. The
same exact content hash before/after and on the reconstructed local file is
sufficient for this bounded copy claim, not for runtime binding or behavioral
claims about the library.
