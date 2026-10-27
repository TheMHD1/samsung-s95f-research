# Selected QD profile ordinary-file copy: independent runtime audit

Recorded 2026-10-27 UTC. This review was performed entirely offline from the
retained raw responses and local output bytes. It made no TV, root, network,
controller, SSB, firmware or display call and did not alter the acquisition.

## Outcome

**Accepted as a byte-exact copy of one ordinary existing filesystem file.**
It is not accepted as proof that this file was opened by CAD this boot,
flashed to the controller, equal to all current controller bytes, or causal to
the blackout/RT Protect result.

The reviewed runner is
`external-msd-parser-20261027a/copy-selected-profile-attempt-b.py`, SHA256
`88ec5e6a5a3aef9bd4f29cea996c81c921d1f4df4838830a5ac7b6a338cf5e75`.
It pins root client SHA256
`3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`,
which still matches the local client. Its only target source is:

```text
/factory_peq/tcon_data/QD/F_RSM1_BN9659934B_COMMON.bin
```

## Raw-envelope and source checks

All 15 `chunk-NN.client.stdout` files decode as exact root-client envelopes.
For every response I independently required:

* model `QN77S95FAFXZC`, authenticated `true`, uid/euid 0;
* `root_persistence=host-assisted` and
  `global_system_files_unchanged_at_acquisition=true`;
* exactly one command, status 0, `timed_out=false`, empty embedded remote
  stderr, and empty separately retained client stderr;
* the executed command is byte-identical to its adjacent intent command;
* the same boot ID
  `00000000-0000-4000-8000-000000000000` before and after;
* regular, non-symlink source, exact size 5,242,880, and exact source SHA256
  `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`
  before and after every streamed chunk.

The target command only tests and hashes the regular source, reads boot ID,
and streams `gzip -n -c` through `dd`, a draining `cat >/dev/null`, and
`base64`. It contains no output redirection to a target file, device open,
ioctl, module operation, service action or controller API. The target created
no file. The file is reread once per chunk; that is read amplification, not a
controller operation.

## Exact reconstruction

The first 14 decoded chunks are exactly 32,768 bytes and the last is 4,649
bytes: `14*32768 + 4649 = 463401`. Each decoded chunk hash equals its
corresponding entry in `manifest.json` (SHA256
`39ad1db84bfa64d2bad8928b80da5b9bb1b92b12398a0dc2c6ad756a3905a706`),
and every raw-response hash also equals its manifest entry.

Concatenating the 15 independently decoded chunks produces bytes identical to
`profile.bin.gz`:

```text
bytes   463401
SHA256 ee3f52d5ad2c21191798893240044a415725fbbd07de6335f8c2bb632b12a917
```

Host gzip decompression produces exactly 5,242,880 bytes identical to the
retained `F_RSM1_BN9659934B_COMMON.bin`:

```text
SHA256 bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0
```

This equals the full-file hash previously authenticated during the nine-file
metadata/field acquisition. No gap, duplicate chunk or trailing byte remains.

## Rejected attempt A remains rejected

The prior runner `copy-selected-profile.py` has SHA256
`8fff9fed0198738d0b81d1da65448f099b2bfde2edabb940542f9069d799aa23`.
Only `selected-qd-profile-copy-20261027a/chunk-00.*` exists. Its raw response
(SHA256
`4a5d833b77a7dd3f0e131ffeebac34a138315560fc5073a9d1da4cb660ea30a2`)
is authenticated and source hashes stayed equal, but `DATA_START` to
`DATA_END` is empty and embedded remote stderr is exactly:

```text
gzip: stdout: Broken pipe
```

The pipeline's final status was zero because it lacked a pipe-failure guard;
that status cannot override the nonempty remote stderr and zero payload. The
host script rejected it before producing any manifest or accepted payload.
The exact low-level `dd` cause is unobserved because its stderr was redirected,
so the preserved evidence supports “broken/empty pipeline,” not a more
specific `dd` diagnosis. Attempt A must not be merged with or relabelled as
the accepted copy.

## Limits

The per-chunk records retain boot, path, size, full source hash and repeated
before/after identity, but not per-call UTC/uptime, inode, mount identity or a
single open spanning all chunks. The final reconstructed full-file hash closes
byte completeness for the copied artifact; it does not prove an atomic source
snapshot against an adversarial mutate-and-restore event. There is no evidence
of such an event.

The copy supplies the uniquely tuple-matched packaged profile for offline
analysis. It authorizes no CAD operation `0x20`, SSB transfer, compatibility
override, controller read/write, firmware apply or protection change.
