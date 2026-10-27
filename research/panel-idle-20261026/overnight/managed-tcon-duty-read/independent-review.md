# Independent review of the fixed selector-0x128 read helper

Recorded 2026-10-27 UTC by the parent, independently of the implementation
agent. Verdict: **CLEAR for the described offline package and source
contract; target execution remains on hold.** No TV, root, network, capture,
staging, device, or controller operation was performed for this review.

Reviewed build manifest SHA-256:
`2474d06b231e328cb6e85a13163dc5594dce8e2a4114e4206166dff874840a35`.
Reviewed source SHA-256:
`2ac6519a9f22ff029f47395eba97ac28d6151c74086e9c636199433ae874410a`.
Built DLL SHA-256:
`32e488ff78af4310423bf2c1475f922fec49f1fb5a1cacf10161fe21423f7ee6`.

## Request and control-flow review

I read the full source and compared its request with the independently
reviewed copied-driver ABI. The only ioctl call site takes the fixed
16-byte sequential structure, offsets0/4/8/12, and request0xc010749f.
Its words are exactly:

```text
00000013,a55a5aa5,0000f300,00000128
```

The operation is decimal19, not the operation18 write route. This represents
packed command0x0000f30000000128 and the reviewed six-byte command followed
by a four-byte read. The hexadecimal selector is0x128, decimal296. No
command-line input can select another command: nonempty args are rejected.

All device access is after the architecture, pointer width, endianness,
structure size/offset, UID/EUID, and ARM EABI PID checks. There is one open,
one ioctl call site, and a close in finally after a successful open. The
source contains no retry/polling loop, setter path, native-memory write,
power/PM/reset/GPIO/protection operation, or alternate device path.
Opening the device read/write is the copied stock ioctl convention; it does
not change operation19 into a scalar setter.

The result parser in the helper rejects any operation/command-word mutation,
nonzero ioctl return, unchanged sentinel, or failed close before printing the
fresh classification. A changed response larger than1023 is separately
classified incompatible_profile_range with nonzero exit. The range is a
packaged getter property; the helper correctly avoids physical brightness or
panel-state inference. An exception during the ioctl still runs the finally
close; process exit also releases descriptors. No internal retry follows a
failure.

## Executed offline checks

The [parent check record](parent-offline-review-checks.json) verifies all
eight manifest file hashes, all five provenance-input hashes, and the exact
installed SDK executable hash. I independently ran the built DLL locally:

- No arguments on X64: exit64, terminal REFUSED_ARCH_ABI, before UID/PID or
  device/ioctl reporting.
- A supplied argument: exit63, terminal REFUSED_ARGUMENTS, before architecture
  acceptance or any device access.

These are meaningful refusal-path checks, not an ARM32 ABI/device test.
No native-call success/failure, close-error, or returned-value branch was
simulated. Those branches were reviewed from source.

A separate parent build using the existing SDK6.0.428 with --no-restore
succeeded with0warnings/0errors. The rebuilt DLL retains the exact hash
above. The project uses cleared package sources and no external packages.
No new toolchain or dependency was installed.

## Execution boundary

This review does not supply a live runner, managed-loader deadline, private
staging cleanup contract, or current source/module/CLR identity check. The
generic read path also lacks the status getter's flash-update gate. Those
conditions need explicit handling in a future coordinated execution package;
the offline helper must not be treated as deployment-ready on its own.

The selected package's0x128 getter reads the same ten-bit RAM field as the
known setter stages, but package provenance is not proof of current controller
flash equality. A future changed kernel output would establish only a
returned word. It would not prove that a physical drive value applied,
identify the RT producer, clear a latch, recover a panel, or prevent a fault.
The owner was told TV collection is finished for now; this review does not
arm or perform another collection.
