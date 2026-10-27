# Independent runtime audit: bounded TCON MICOM log read

## Outcome

This is an offline audit of the two retained attempts.  I made no TV, root,
network, debugfs, or device call.

- Attempt `a` is correctly rejected.  Its command stopped at the absent,
  incorrectly guessed module path before creating its private directory or
  reaching the debugfs getter.
- Attempt `b` is a complete, authenticated acquisition of one bounded,
  non-consuming MICOM-log snapshot.  The local 1,477-byte file reconstructs
  exactly from the retained transfer response, its hash agrees at capture,
  transfer, and host, and the owned remote namespace was removed.
- The snapshot is physically unobserved and non-atomic with respect to the
  external shared-memory producer.  It adds two complete message-box
  `In/Out` pairs after the 1,404-byte common prefix, but it contains no new
  positive fault text or independently timed reboot/reinitialization marker.

## Audited artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `../micom-log-read-20261026a/result.json` | 2,533 | `54d8cf0f358a8b264c598343a39252100451bf9fba7e94078a837b4d23fb1ffb` |
| `../micom-log-read-20261026a/capture.client.stdout` | 2,390 | `38e6f7cb37c5a82aa7c786bc2e58ca34fd0b6cc382c21d7734d0c003f7b8ddff` |
| `../micom-log-read-20261026a/preflight-metadata.client.stdout` | 1,160 | `fcee2167cac5add071a290febe4011437b4fa97b901ca871389fe3d043ab76d7` |
| `capture-shell.txt` | 1,990 | `d74e3b3414c7027a86495584d045b5920017e3accdf4fe0f4e32b24e505fa4cb` |
| `capture.client.stdout` | 2,953 | `ec23ebf869d3db3232b13e18167c6ecde740c3765006b5e7ac8bc4af0a6f2dee` |
| `chunk0.client.stdout` | 3,220 | `4de69a34f572636340702a081bae084450af9efdc764f894d0347cd42281906b` |
| `cleanup.client.stdout` | 1,414 | `7bad8bf958f470ecfc1e26b36c24016b6862e71c601e3f745f14fccb519761ef` |
| `micom-log.bin` | 1,477 | `bd600476b7a081b58759128cff8bacd8f4fef8d8c45c33327cc575a1c65d7110` |
| `result.json` | 5,149 | `bd07eb27dddce150b2037fc7f1e373682a15fc502225f962707902e0eedd4219` |

All five retained root-client envelopes used in the two attempts authenticate
as UID/EUID 0 on model `QN77S95FAFXZC`, state host-assisted persistence and
the unchanged-global-system-files invariant, contain exactly one command,
and report no transport timeout.  All corresponding host-side client-stderr
files are empty.

## Attempt `a`: pre-getter rejection

The exact command has `set -eu`.  After checking `uname -r`, its first module
operation is:

```text
test -f /lib/modules/5.4.261/kernel/sdp_tcon.ko
```

The command returned status 1 with empty stdout and stderr.  The separately
retained authenticated metadata response records that path as `ABSENT`, the
debugfs node as present, and the exact intended private path as
`PRIVATE_ABSENT`.  The real module is under `kernel/soc/`.  Because the failed
test precedes the debugfs read and `mkdir`, the retained evidence shows no
private creation and no MICOM getter read in attempt `a`.  Its
`cleanup_confirmed:false` is therefore not evidence of residue; no owned
namespace was created.

## Attempt `b`: capture and reconstruction

The exact capture command in `result.json` equals `capture-shell.txt`.  Before
the getter it verifies:

- kernel release `5.4.261`;
- a regular, non-symlinked
  `/lib/modules/5.4.261/kernel/soc/sdp_tcon.ko` with SHA-256
  `9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee`;
- the non-symlink debugfs node; and
- absence of its unique private path.

It creates a root-owned mode-0700 directory and performs one open through:

```text
dd if=/sys/kernel/debug/tcon/tcon_micom_log \
   of=<owned-mode-0600-file> bs=4096 count=16
```

This is the reviewed fixed-request form; it does not use the unsafe single
8 KiB or 64 KiB request.  The command reports `0+1 records in/out`, 1,477
bytes, and capture hash
`bd600476b7a081b58759128cff8bacd8f4fef8d8c45c33327cc575a1c65d7110`.
Its boot ID is unchanged across the read.  The captured interval is uptime
`79281.42..79281.44` and UTC second `1793057672`.

The transfer command rechecks the same boot ID, private-directory ownership
and mode, regular/non-symlink file identity, and full captured-file hash.  I
strictly base64-decoded its retained stdout and obtained byte-for-byte the
local `micom-log.bin`; its length and SHA-256 match the capture metadata.
The result's recorded raw response sizes also equal the actual retained
root-client response sizes.

Cleanup first allows only `log.bin` and `dd.stderr`, verifies each as a
root-owned mode-0600 regular non-symlink, deletes those exact two names,
removes the private directory, verifies its absence, and returns
`PRIVATE_REMOVED` with status 0.  This supports `cleanup_confirmed:true` for
that owned namespace.

## Content comparison and limits

The prior 1,405-byte artifact and the new snapshot agree for exactly 1,404
bytes.  The prior terminal byte is ASCII `S`; at that offset the new snapshot
instead contains:

```text
Msgbox ISR In Ch : 2
Msgbox ISR out
Msgbox ISR In Ch : 2
Msgbox ISR out
```

and then terminates with byte `0x8b`.  Thus the new artifact has four more
newline-terminated lines and two complete additional `In/Out` pairs relative
to the common prefix.  The isolated old `S` and new `0x8b` remain unexplained
producer-boundary bytes; neither should be normalized into text.

The unchanged prefix includes the original startup banner, `Cold Boot!`,
`Main Loop`, and ordinary boot-time protection text.  The new suffix contains
no `ERR`, `Error`, `error`, `Fault`, or `fault` token.  This is only a bounded
content observation.  The getter samples externally updated shared memory
without a lock, sequence counter, epoch, or firmware timestamp, and the owner
state was not contemporaneously annotated.  Therefore the capture does not
prove the absence of a fault, does not time the additional message-box text,
and does not establish or exclude a controller reboot or log reinitialization.

