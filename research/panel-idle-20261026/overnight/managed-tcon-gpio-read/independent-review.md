# Independent review: managed ERR_DET GPIO query

## Outcome

**CLEAR for one deliberate query only**, while the owner's separately retained
physical annotation says the panel is black. This clearance does not cover a
retry, loop, recovery action, setter, power action, sensing action, or a second
query under a different physical state.

No TV, root, network, device, ioctl, GPIO, or control access was made during
this review.

## Exact reviewed bytes

| Artifact | SHA-256 |
| --- | --- |
| `Program.cs` | `568e9f0d257bd98e6a261216d1bcba0c09a15a06083bb1592e97ebdb8ec37c34` |
| `TconGpioRead.csproj` | `a3975a416bddff4af5a760568bbdd3fd74b6d35401c9397412688fa9ea37501c` |
| `run-gpio-read.py` | `18e3ea5591541ecc6f3d3f5988e3c2098e63d23518055a3dc58cd0e96d34da85` |
| `build-manifest.json` | `02a064ed1ef3b975df5b041304f1a48df4664adecfe163fd4716c18909f15883` |
| `TconGpioRead.dll` | `c181208cc4cd090ce9a4f2ac0ffa03569c92b06d4ab899d08b299a69dd5cf447` |

The runner pins the ABI report
`e6b38dd0782fee6aa25bf859b81cd002c61da0fe27934e9e280e5433fcc0428d`
and reproducer
`a65224ccfd2a154f3d5ccdf71b6b2af468c906045db50d9fc6993e453e9153c7`.
It also pins the persistent root client, installed ARM32 CLR/runtime files, and
the three exact installed TCON modules used by the route.

## Query contract

The managed program performs exactly:

1. ABI/architecture, UID and ARM-EABI PID checks before opening the device;
2. one `open("/dev/tztv_tcon", O_RDWR|O_CLOEXEC)`;
3. one ioctl `0xc010749f` with little-endian words
   `[0x1d,0xa55a5aa5,0,0]`;
4. one close in `finally`;
5. no retry.

It requires ARM32, pointer size4, little endian, structure size16 and output
offset4. It records open/ioctl/close returns and errno independently. A usable
result requires ioctl zero, close zero, unchanged operation/opaque words, and
word1 changed from the sentinel.

The result prints word1 as both exact eight-digit unsigned hex and signed
`int32`. The host parser recomputes signed two's-complement from the payload
and requires exact equality. It does not collapse an arbitrary nonzero word
into a boolean assertion.

## Transport and lifecycle

The runner is dry by default and requires both `--run` and `--reviewed`. Live
root calls use `--persistent-only`, a 25-second root-command timeout, and no
fallback transport. The generated plan has ten commands; its largest command
is 8053 bytes, below the enforced 8192-byte limit.

Staging uses a unique private `/tmp/researcher-err-gpio-<32 hex>` directory,
mode0700. Staged and output files are required to be regular, nonsymlink,
root-owned mode0600 files. Staged assembly files are checked by exact length
and SHA-256 before execution and again after execution.

The helper child writes its own PID/start ticks and waits behind a private GO
file. The parent validates PID and generation before creating GO. TERM and
KILL are sent only after a fresh PID/start guard; without a validated
handshake the child never sees GO and self-expires. The execute command has a
bounded wait and TERM-to-KILL escalation. Cleanup deletes only the exact
allowlisted files after directory and per-file ownership/type/mode checks,
then verifies the private directory is absent. A create attempt is recorded
before its root call, so a lost create response still enters cleanup.

Every controller response, client stdout/stderr, echoed command, status and
timeout flag is retained in the result JSON before validation. There is no
automatic retry after any failure.

## Parser and offline evidence

The following offline checks passed against the exact bytes above:

* Python compilation and the default dry plan;
* build-manifest inventory and all local hashes;
* `/bin/sh -n` for all ten generated commands;
* command count10, maximum8053 bytes, every command within8192;
* accepted parser fixtures for output words `0`, `1`, `0xffffffea`,
  `0x80000000`, and `0x7fffffff`;
* rejection fixtures for a mismatched signed value, unchanged sentinel,
  mutated operation word, and duplicate field.

The local host has no `dotnet` executable, so the ARM32 managed assembly was
not executed during this review. The manifest binds the exact source and
staged DLL, and the key managed output strings are present in that exact DLL.
Actual ABI execution remains part of the single target query, guarded by the
program's pre-open checks.

## Evidence limits

Host acceptance means only `kernel_output_written`:

* output zero remains `cached_power_skip_or_raw_low`; it is never a health
  verdict and does not prove the GPIO provider ran;
* output nonzero remains `raw_or_debug_or_read_error`; QDF debug override and
  a signed-negative raw-read result are not excluded by the payload;
* the query itself temporarily requests the GPIO, forces input direction,
  reads it, and frees it on the provider-success path;
* the helper does not prove electrical polarity, controller health, physical
  light emission, cause, or recovery;
* installed file hashes do not independently prove immutable live kernel text.

Any immediate filtered kernel-log read is a separate bounded acquisition. It
may help distinguish the cached-power, raw-nonzero, provider-error, or debug
paths, but absence of a retained log must not be converted into a negative
hardware claim.

