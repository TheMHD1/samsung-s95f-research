# Independent review: fixed selector-0x128 duty-read runner v2

Recorded 2026-10-27 UTC from local files and offline fixtures only. No TV,
root-controller, network, device, ioctl, staging, or cleanup call was made.

## Verdict

**CLEAR for one deliberately coordinated, finite invocation of this exact
fixed read package.** This is not clearance for retries, arbitrary selectors,
physical-brightness conclusions, protection changes, firmware activity, or
any write/control operation.

Reviewed exact files:

| file | SHA-256 |
| --- | --- |
| `run-duty-read-v2.py` | `5f0796be9ec36f7441ae248a1472cf61001a7417afd896d41057df45e0aad5c6` |
| `test-run-duty-read-v2.py` | `deddbba45e8b3704c8056e8586e594296dec96dc67ea6f23e2d0ca4b011399fc` |
| pinned lifecycle `../managed-tcon-status-read/run-status-read.py` | `7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a` |
| `build-manifest.json` | `2474d06b231e328cb6e85a13163dc5594dce8e2a4114e4206166dff874840a35` |
| staged `ManagedTconDutyRead.dll` | `32e488ff78af4310423bf2c1475f922fec49f1fb5a1cacf10161fe21423f7ee6` |
| generic-read ABI report | `52b1be2e269edc353ffa3f290305067c3c720a3ae000526e08f59d2bbe412172` |
| ABI independent review | `0e0191069116e6d85bdc45dfa178adc2aa83b2bed8f33f1eae6fff17bec79150` |

## Import, payload, and parser boundary

`mod()` hashes the lifecycle source against the literal expected digest
before constructing or executing its import spec. It then checks the
hash-pinned access client. The build contract independently verifies the
immutable build-manifest digest, every listed source/payload digest, and all
five provenance inputs. Only the three named portable-IL runtime files are
staged.

The helper has no selector or command argument. Its sole ioctl envelope is
exactly:

```text
word0 operation = 19 decimal
word1 output    = 0xa55a5aa5 sentinel
word2 high      = 0x0000f300
word3 low       = 0x00000128
ioctl           = 0xc010749f
device          = /dev/tztv_tcon
wire request    = f3 00 00 00 01 28, then four response bytes
```

The C# helper refuses before open unless it observes ARM32, a four-byte
pointer, little endian, the exact 16-byte structure offsets, root UID/EUID,
and matching libc/raw ARM-EABI PIDs. After a successful open it has one ioctl
call and closes in `finally`. It rejects an altered command envelope, nonzero
ioctl return, unchanged sentinel, close failure, or output above 1023. The
Python parser independently requires the exact field inventory, rejects
duplicates and unknown/bare lines, binds the helper PID, repeats every fixed
ABI/request/envelope check, and accepts only a changed value in 0..1023.

An accepted value is only `kernel_output_written` and
`within_packaged_low10_range`. Zero is a valid changed output. Neither zero
nor any other accepted value is physical brightness, emitted light, panel
state, controller-flash identity, or proof that a drive value was applied.

## Lifecycle and failure handling

The runner reuses the exact reviewed status-runner lifecycle rather than
reimplementing staging and process control. It replaces only the three remote
file names, fixed DLL name, exact parser, manifest/ABI record identity, and
result wording. The inherited path provides:

- dry default and `--run --reviewed --output /absolute/unique.json` guards;
- authenticated persistent-root calls with a 25-second controller timeout;
- strict source/module/CLR/device preflight and postflight identities;
- a UUID-private root-owned 0700 directory and root-owned 0600 regular files;
- chunk hash/size checks before execution and after it;
- child PID/start-time handshake, guarded TERM/KILL deadline, wait/reap, and
  output bounds;
- raw response persistence before parsing; and
- exact allowlisted cleanup after success or every staged failure.

The runner emits 11 root commands. Offline rendering measured the longest at
7,965 bytes, leaving 227 bytes below the fixed 8,192-byte command ceiling.
The output file uses exclusive creation before preflight. Independent local
checks confirmed that both an existing regular file and a dangling symlink
are refused with the original object preserved and no mocked transport call.

The supplied fixture exercises success, parser rejection followed by cleanup,
and cleanup failure. A cleanup failure keeps `accepted=false` and
`cleanup_confirmed=false`; a parser/read failure is never rehabilitated by a
successful cleanup. The exact lifecycle source also persists timeout partial
stdout/stderr and cleans after a lost/failed create attempt when a boot anchor
is available.

## Offline verification

The following passed on the exact reviewed bytes:

- `7/7` v2 tests under normal Python;
- `7/7` v2 tests under `python3 -O`;
- `py_compile` for the runner and tests;
- dry-plan construction with no transport, exactly 11 commands, all bounded;
- manifest/source/provenance verification; and
- the additional existing-file and dangling-symlink exclusivity checks above.

## Residual technical limits

The generic operation-19 wrapper does **not** implement the separate status
getter's `tcon_flash_update` gate, and the runner has no source-backed passive
way to observe that private flag. Therefore a concurrent firmware/update
state is not excluded. This is an explicit technical race/coverage limit,
not a claim that such activity is present and not a missing-user-authorization
condition.

The lower path actively writes the six command bytes before its four-byte
read. Its host path invokes no named reset, recovery, power, GPIO, flash, or
setting routine, but controller-side selector semantics remain unknown: a
read-to-clear or other bookkeeping effect has not been excluded. A missing
interface/slot, suspend, command-skip, non-running TCON state, absent
transport, or transfer failure can leave the sentinel unchanged or return an
error; those outcomes are unusable and must not be retried automatically.

This clearance is consequently bounded to one fixed read and its retained
record. It supplies no causal conclusion and no repair/recovery claim.
