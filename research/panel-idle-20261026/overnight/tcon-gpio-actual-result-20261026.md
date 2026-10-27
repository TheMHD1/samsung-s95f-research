# Actual ERR_DET GPIO query: 2026-10-26

After the owner confirmed the panel remained off/black, the parent performed
one ordinary operation0x1d diagnostic. The helper returned output **1**
(`0x00000001`, signed int32 `1`). The stock monitor's separate GPIO predicate
would treat that nonzero word as a fault. This is not operation0x1f's
controller status word0x10 and must not be conflated with RT Protect bit4.

## Retained execution

- [Raw result](managed-tcon-gpio-read/result-20261026a.json), SHA256 `74be6997f2e2ca54e256b2ab2128a27224f5e6f9940cdeedbb93e86fbb79df74`.
- Preflight uptime76166.77, execution end76168.08; same Linux boot
  `00000000-0000-4000-8000-000000000000`.
- Helper PID5317/start19041949; ARM32, little endian, UID/EUID0 and libc/raw
  syscall PID agree. Struct16B, output offset4.
- One open returned fd26/errno0; one ioctl c010749f/op1d returned0/errno0;
  close returned0/errno0. Payload sentinel became1; all other words agree.
- All10 root calls succeeded. Helper stderr empty, postflight source pins
  passed, owned private directory removal confirmed. No retry or further
  GPIO query was performed in this black state.

The provider is an ordinary diagnostic path that can request/free the GPIO
and set input direction; it is not passive memory access. No panel power,
reset, protection, sensing, monitor-latch/counter or firmware change was sent.

## Interpretation limits

A [filtered kernel-log read](managed-tcon-gpio-read/filtered-dmesg-a/client.stdout)
at76174.15..76174.21 found zero retained matching getter/provider rows.
That is not evidence that the getter did not execute. Its accepted output1
proves kernel-written data, but the optional QDF debug override is not
independently excluded. No raw GPIO electrical assertion or connector voltage
is therefore claimed from this result alone. It is not a signed-negative
GPIO read-error word. The exact
[ABI report](../tcon-research/qd-current-fault-gpio-read-abi.md) documents the
cached-power-zero shortcut, provider and debug paths.

The owner had just confirmed the physical panel was black and was instructed
to leave power unchanged. The helper's machine record correctly retains
physical_state=unobserved; there is no calibrated annotation of each read.
This contextual black sample and the earlier raw logged RT Protect word form
a useful pair, not a causal conclusion or recovery.

## Prepared control

After both helpers stopped and their directories were removed, the parent
requested one normal owner standby off/on followed by quickly opening the
populated Apps page. The parent is waiting for the owner's visible/black/
optimization report before collecting any visible-control readings. No
additional status/GPIO query is authorized automatically by this record.


The [independent runtime audit](managed-tcon-gpio-read/runtime-audit.md)
confirms all10 successful calls and exact signed/unsigned output1. It also
validates the bounded inference that this output is inconsistent with the
exact QDF cached-power-zero shortcut, conditional on the copied callback being
the live path. It does not establish raw electrical high or exclude debug.
