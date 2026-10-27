# Independent offline review: fixed MODE2 power-cycle helper

## Verdict

**CLEAR for one deliberately parent-operated, separately bracketed request
only.** This is not a finding that the operation is safe for a damaged panel,
that it will run the intended callback, or that it will restore picture. It is
not authorization for an automatic retry, rollback command, firmware work,
or a physical recovery claim.

Review was offline. No TV/root/device/network action was taken.

## Exact bytes reviewed

| item | SHA-256 |
| --- | --- |
| `Program.cs` | `2f4333d381a0a5dbba4b6fcdb87790438f595f981dfadd3e6e6e76b341ae5e9b` |
| managed DLL | `f3b54a30b92d2c749012cc9f070bad4c206090b4f90facf6237e4ce5a9f168ba` |
| build manifest | `67aa102cdd3cdc85ed7fabb68b37d570b721664298317f24f9bd24b8250f9faa` |
| runner | `5c7ec5d3581e349d7f91669977123497147777e573fbdefd8a9b6f96dcf3cb75` |
| runner tests | `f905e2135eb6a86066ed0c05ee34ded35ba50c17791e9e63c6d24d658738474b` |
| independently reviewed power ABI | `6fe142a5d0c2d5e4105ec540a327ad13898afbd20b6486237df649537beaf510` |

## Fixed operation and process boundaries

The ARM32-only helper rejects all command-line arguments, non-ARM or non-32-bit
process ABI, non-root UID/EUID, and a libc/syscall PID mismatch before opening
the device. It constructs exactly one 16-byte little-endian request:

```text
word0 operation 41 (0x29)
word1 mode 2
word2 0
word3 0
ioctl 0xc010749f on /dev/tztv_tcon
```

The source contains one `ioctl(fd, Request, ref value)` call. It checks that
all four words remain exact after the call, always closes the descriptor in a
`finally` block, and rejects a nonzero ioctl or close result. The result parser
requires the exact no-argument/ARM/root/fixed-payload transcript and classifies
the only accepted success as `kernel_return_zero_only` with all three
acknowledgement/recovery/physical flags equal to zero.

The runner pins its build manifest, staged DLL/deps/runtimeconfig payloads,
the inherited lifecycle source, root-client hash, and both ABI reports. It
uses the inherited unique-output/private-directory lifecycle: preflight,
private-directory creation, hash-checked staging, one execution command,
postflight, and cleanup. A parser or helper failure still reaches cleanup in
the tested fixture. It has no automatic retry or compensating command.

The rendered plan has ten bounded root commands; largest was 8,061 bytes
(within the 8,192-byte transport ceiling). The helper deadline is eight
seconds; the stated recovered lower-path explicit waits total at most 2.7
seconds, excluding scheduler/callback time.

## Offline checks run

```text
python3 -m unittest -v test-run-power-cycle-once.py   # 9 passed
python3 -m py_compile run-power-cycle-once.py test-run-power-cycle-once.py
python3 run-power-cycle-once.py                       # dry plan only
```

The dry plan reported fixed words `29,2,0,0`, `retry_permitted=false`, ten
commands all within the ceiling, and no target/device/root/network call.
Tests include exact parser acceptance/rejection, one-ioctl/static-import
checks, lifecycle substitution to the intended DLL, mocked cleanup on success
and parser failure, and refusal of existing or dangling output paths before
transport.

## Material limits retained

- Operation 41/mode 2 is an intentional stock power-control request, not a
  passive read. Static ABI work says it can select an ordinary QDF off/on
  sequence **only if** the intended live callback binding is present.
- A zero result is ambiguous: missing interface/callback paths can return zero;
  lower cache/error propagation does not establish rails, controller action,
  protection state, or recovery.
- The helper does not independently test a live firmware-update/flash state.
  That is an unresolved concurrency/risk boundary, not evidence that flashing
  is occurring or absent.
- The helper may be run while the physical state is unobserved. In that case,
  retained technical output remains unable to claim picture/light restoration.
  Audio, log text, cached fields, or return zero are not substitutes for a
  later owner observation.
- The stock lower route itself has no proven compensating rollback if its off
  or on half fails. A nonzero, timeout, identity drift, cleanup failure, or
  unchanged dark state must stop rather than trigger a helper retry.

The existing recovery plan's passive before/during/after evidence bracket is
therefore a necessary execution precondition, not optional logging decoration.
