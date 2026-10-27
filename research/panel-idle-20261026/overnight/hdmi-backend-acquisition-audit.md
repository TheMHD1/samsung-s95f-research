# Independent audit: HDMI backend metadata and copies

Date: 2026-10-26 UTC

## Outcome

**CLEAR for offline static analysis of both retained versioned files.** I
independently decoded every retained chunk, reconstructed both files, and
matched the retained local bytes exactly:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `libhdmi-input-control-impl-sec.so.0.1` | 29,650 | `5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126` |
| `libhdmi-control-impl-sec.so.0.1` | 75,882 | `5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1` |

The successful metadata capture also proves a point-in-time AVOC mapping of
the versioned control implementation. It does not prove that the input
implementation was loaded or called. It also does not close the unversioned
loader-name chain: each unversioned name points to a `.so.0` intermediate,
but that intermediate was not read or resolved to `.so.0.1`.

No TV, root, or network request was made during this independent audit.

## Acquisition code

- `read-hdmi-backend-metadata.py`: `e96fb0d18e75fa0d31e4346d9ab870867e70bd7e535104e478cda052bd3c676d`
- `read-hdmi-backend-versioned-metadata.py`: `02b60b92330f94b497f8122451855495d29eec90dffaab4e3b06c2bc2bd3e660`
- pinned `read-pm-idle-format.py`: `47262917994451714b3dbfb8f53d761c61232587f2e83b3303cd5ce94a1b28e9`
- `pull-hdmi-backends.py`: `1f1e3022a6d64d29002bd4a748d3903739413fae13c6e46434beba8ed6197cc2`
- pinned `pull-serdes-modules.py`: `62fa8107cb3a50b20949d59370fa5a4ed33d48c71153f11643e5b370f680ea11`
- pinned `complete-sdp-sys-provider-copy.py`: `b587e16d4e85a056c248b1adc3f04dccbabed682fe50a8dfdd9987a1543c4582`
- root client in both metadata intents: `3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5`

Both copy choices remain default-dry. Offline invocation without `--run`
printed only the fixed path, byte count, and planned chunk count.

The metadata commands only read boot/time/uptime, `/proc` identity/maps, path
types, symlinks, metadata, and hashes. The copy commands hash a fixed path,
read one bounded range with `dd if=...` and no output file, and base64-encode
it to stdout. They do not load or call a backend, invoke a getter, alter
tracing, or issue a display/hardware control.

## First strict attempt: retained failure

Raw hashes are:

| Artifact | SHA-256 |
| --- | --- |
| `intent.json` | `c64e00f4c64f41c7aae161d64a30614f88c642a09f130e39702c3055e884595c` |
| `client-result.json` | `eaae85e4e6485f4f25ff94b6aa67a7b857a37f40dd74e9c37b2c36024d053925` |
| `client-stdout.json` | `818c2756d4cc6fb3ce58a7dc5cc87dd3ec61a51725c17f9743c9ce0dc41d9a58` |
| `client-stderr.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The response authenticates model `QN77S95FAFXZC`, host `198.51.100.20`,
UID/EUID 0, host-assisted persistent root, and unchanged global system files.
The one retained command matches the intent (SHA-256
`7a44fc83fd0e38cc4d2ab28cf36ed6626f49611f00693614c454cf686982636b`).
Both client and remote return 1 without timeout or stderr.

Stdout starts on boot `00000000-0000-4000-8000-000000000000`, uptime
`70299.40`, records `/usr/bin/avocd` at PID 706/start ticks 603, emits no rows
for the two exact unversioned map names, prints `INPUT_BACKEND_IDENTITY`, and
stops. There is no ending boot/time bracket and no file identity.

The next two silent commands are `test -f` and `test ! -L` under `set -e`.
The failed stdout alone cannot distinguish which predicate returned 1. The
later capture is consistent with failure at `test ! -L` because it observes
the name as a symlink, but it must not retroactively turn the earlier result
into a framed success. No absence, stable-map, or file-identity conclusion
follows from this failure.

The basename-sorted four-file inventory digest over
`<sha256><two spaces><basename>\n` is
`fcfd04735c6d470d5b91415b1366275953995e24e2696d4735de166cc8edb172`.

## Successful version-aware metadata

| Artifact | SHA-256 |
| --- | --- |
| `intent.json` | `494270713ea4d660822f29cb57ea6dfa054f1056d1933dcd21b37264010254d3` |
| `client-result.json` | `f0830177536005c96d52675171ca5a4453cc5bb043aac95e92f6ff08331e434b` |
| `client-stdout.json` | `1452f4e53cf239b2484aa736ab138814692c9452903ed944282f67cd1f81fac3` |
| `client-stderr.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The same root/model/host/access fields validate. Exactly one command matches
the intent and SHA-256
`93f9c4bf7fd4a046df2629a1ada0c4f69d8198f36934d1cdc40ef8c21b47c345`.
Client and remote return 0, with no timeout or stderr. Boot is unchanged;
epoch is `1793048724` at both ends and uptime advances from `70333.51` to
`70333.53`.

The process sample again identifies `/usr/bin/avocd`, PID 706/start ticks 603.
Four map rows name only
`/prd/usr/lib/libhdmi-control-impl-sec.so.0.1`, device/inode `b3:1b`/`348`:

- `f503c000-f504b000 r-xp 00000000`
- `f504b000-f505a000 ---p 0000f000`
- `f505a000-f505b000 r--p 0000e000`
- `f505b000-f505c000 rw-p 0000f000`

The path records are exact:

- unversioned input: symlink to `libhdmi-input-control-impl-sec.so.0`;
- input `.so.0.1`: regular, mode 0755, UID 0, 29,650 bytes, expected hash;
- unversioned control: symlink to `libhdmi-control-impl-sec.so.0`;
- control `.so.0.1`: regular, mode 0755, UID 0, 75,882 bytes, expected hash.

Neither `.so.0` intermediate is inspected, and `readlink -f` is not applied
to the unversioned names. Thus the unversioned path-to-copied-file chain is
not established. The control map positively observes its `.so.0.1`; the
absence of an input map row is not proof it was never loaded or used.

PID identity/maps are sampled once, not at both ends. They are point
observations rather than PID-reuse- or map-change-excluding snapshots. This
does not weaken the separately pre/post-hashed file copies. The successful
metadata four-file inventory digest is
`8181c82ac947f6275bd7896cede91671448883af4e4536dd652ec2a2a05999f7`.

## Chunk authentication and reconstruction

For all four chunk commands I independently required authenticated
root/model/host/access provenance; one command identical to its intent and
the expected fixed index; correct command hash; client/remote return 0; no
timeout or stderr; exact framing; stable boot; ordered bounded clocks;
matching expected path and whole-file hash both before and after the read;
strict base64 decoding; exact length; and full agreement with the manifest.
`set -euo pipefail` prevents `base64` from masking a failed `dd`.

The input copy is one 29,650-byte chunk from uptime `70348.24` to `70348.25`;
its chunk hash equals the whole-file hash. Manifest SHA-256 is
`8bddd01c1dae5e3c09e5182ac569ec5fe319a59be9e94e785ba6066bde534ee5`.
Its six-file directory inventory digest is
`b7647780813d9d45531737afd57f3abcd8fa4a5eeab55dad206a5de7e8cb55a8`.

The control chunks are:

| Index | Bytes | SHA-256 | Uptime |
| ---: | ---: | --- | --- |
| 0 | 32768 | `cfa75fc324e6edd65ca4dca08125c7a8d902c65a534586f3443b846efeff6edd` | `70354.21`–`70354.22` |
| 1 | 32768 | `f5c664f9174bb1db0d17df04a82684b130a7ebe6a60b47e0007eccfc5e12e57c` | `70354.50`–`70354.51` |
| 2 | 10346 | `85dd2c6fe304e3d2fd4062d4bffa5b9351895df3e5079a177135c6cf04193c52` | `70354.70`–`70354.71` |

Their concatenation is exactly 75,882 bytes at the expected hash. Manifest
SHA-256 is
`198f28081d1289828519c92edaf5ec906a01e77af632f8e905ff5eb7bd52d39f`;
the 14-file inventory digest is
`c632605ed8de0fa0af3e501a85fcba8dd8996347a5a9da7db27f728eacb87b47`.

Both manifests correctly retain `sequential_nonatomic=true`,
`loaded_or_called_by_capture=false`, and `physical_picture="unobserved"`.
The retained files are ELF32 little-endian ARM EABI5 shared objects. Input
build ID is `08ec0fc1d8bf51d6aab81b6e60a31a509d8c9daa`; control build ID is
`1300a5998bcc494192189a6479fa4b316e108111`.

## Claim boundary

This evidence authenticates two exact versioned files for offline reverse
engineering and one contemporaneous control-implementation map. It does not
prove the missing `.so.0` hops, bind the input file to the unversioned loader
literal, recover a live callback table, show either implementation executing,
or establish any display, power, recovery, or black-panel effect.
