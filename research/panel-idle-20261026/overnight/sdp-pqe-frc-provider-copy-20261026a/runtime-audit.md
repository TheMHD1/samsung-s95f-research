# Independent runtime audit: `sdp_pqe_frc.ko` provider candidate copy

## Outcome

This is an offline audit of the installed-module literal census and the
31-chunk copy.  I made no TV, root, network, module, symbol, device, or
callback call.

The acquisition is independently accepted as a byte-exact ordinary file
copy:

- the authenticated installed-tree census found the exact word
  `tcon_ex_proc` in two of 195 scanned regular `.ko` files:
  `sdp_pqe_frc.ko` and the already-known `tztv_frc_tcon.ko`;
- every chunk response is authenticated, status zero, not timed out, and has
  empty embedded and host client stderr;
- every chunk command verifies the same boot, regular/non-symlink source,
  exact size, and full remote SHA-256 before and after its read;
- strict base64 decoding, per-chunk length/hash checks, ordered concatenation,
  and comparison with the saved local file all pass; and
- no command loads a module or resolves/invokes `tcon_ex_proc`.

The literal census identifies a high-value provider candidate but is not a
symbol-export or live-binding proof.  Those conclusions require separate
offline ELF/control-flow analysis.

## Provenance

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| provider-scan `client.stdout` | 1,554 | `43d62d1f13fa7b4ece51ae0ddf83c530dd255b0d30ed6a2364a5e257dd11a240` |
| provider-scan `intent.json` | 720 | `76ecafed9b072b5ca81c0620f643a70f303dcbe8672594162621fe516b9f01df` |
| copy `manifest.json` | 9,513 | `54cc98708203cee3778ba329ab8e2219c91fcb4fc82eb9f3076f283fdaad2f4d` |
| reconstructed `sdp_pqe_frc.ko` | 1,015,070 | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |

The reconstructed file is an unstripped AArch64 relocatable ELF with GNU
Build ID `492cc2d117e05b0cc472c2f23ee7a8a0b63b317a`.

## Installed-module census

The scan response authenticates UID/EUID 0 on model `QN77S95FAFXZC`, records
host-assisted persistence and the unchanged-global-system-files invariant,
and contains one status-zero, non-timeout command with empty stderr.  It
walks regular `*.ko` files below `/lib/modules/5.4.261` to depth eight and
uses a binary-safe exact-word grep for `tcon_ex_proc`.

The boot ID is the same at both ends:
`00000000-0000-4000-8000-000000000000`.  Uptime spans
`79537.27..79538.49`.  The exact reported result is:

```text
/lib/modules/5.4.261/kernel/soc/sdp_pqe_frc.ko
  1015070 bytes
  1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4

/lib/modules/5.4.261/kernel/tztv_frc_tcon.ko
  254406 bytes
  aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd

MODULES_SCANNED=195
CANDIDATES=2
```

This proves only literal presence in that finite installed-file scope.
`tztv_frc_tcon.ko` is already known to contain the consumer's requested
name, so inclusion in this result does not make it a provider.  The scan does
not distinguish an export, import, log string, or other data occurrence and
does not establish which module is bound live.

## Chunk replay

The manifest records remote source
`/lib/modules/5.4.261/kernel/soc/sdp_pqe_frc.ko`, the same boot ID, exact size
1,015,070, and the full SHA-256 above.  There are exactly 31 ordered records:

- indices 0 through 29 decode to 32,768 bytes each;
- index 30 decodes to 32,030 bytes; and
- the total is exactly 1,015,070 bytes.

For every index I independently verified:

1. the raw root envelope authenticates UID/EUID 0, the same model,
   host-assisted persistence, and the unchanged-global-system-files
   invariant;
2. the envelope contains exactly one status-zero, non-timeout command with
   empty embedded stderr, while the corresponding host client-stderr file is
   empty;
3. the raw response SHA-256 equals its manifest record;
4. the response command is byte-for-byte its retained intent command;
5. the command checks `test -f`, refuses a symlink, requires the exact source
   size, and checks the full source hash and boot ID both before and after the
   `dd` read;
6. the `skip` value equals the manifest index and the fixed block size is
   32,768;
7. the framed start/end uptimes equal the manifest values; and
8. joining only the wrapped base64 lines and decoding strictly yields the
   recorded byte count and per-chunk SHA-256.

The copied interval spans uptime `79617.95..79622.84`.  Concatenating those
decoded bytes in index order is byte-for-byte identical to the saved local
ELF and reproduces its full hash.  The repeated complete-file hashes bound
the source identity at every chunk transaction; this was a read-only file
copy, not module loading or execution.

## Identity boundary

The older 319,518-byte artifact with SHA-256
`2f23cf9256f2cc2b39a2e0afea7a7fc6007bffd3d5efb536aacd695ee4f3967e`
is `sdp_pqe_dp.ko`, as named by `analysis-input-manifest.json` and confirmed
by the current local file.  It is not this newly acquired
1,015,070-byte `sdp_pqe_frc.ko`.  Their names, sizes, hashes, and roles must
not be substituted in subsequent disassembly or provider analysis.

## Limits

- The census covers the 195 regular module files reached by that exact
  `/lib/modules/5.4.261` traversal; it is not a whole-filesystem string or
  symbol census.
- Literal presence does not prove an export or the bridge's current cached
  function pointer.
- The chunk copy proves installed-file bytes, not that the installed file was
  newly loaded, reloaded, or is the source of every page currently resident
  in the running module.
- No operation-`0x20` envelope, CAD file, update loader, controller command,
  or hardware path was invoked by this acquisition.

