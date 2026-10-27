# Fixed controller descriptor-memory read

This is a separate derivative of the reviewed `managed-usb-ssb-read-once` helper.
The earlier helper and its evidence are preserved. This derivative sends only
target `0x101`, address `0x20261200`, length 18: header
`010100000012262012000000`. It accepts a result only when the exact 18-byte
device descriptor matches the reconstructed packaged descriptor and cached USB
descriptor, and interface release and descriptor close both succeed.

No controller-memory write, storage operation, reset, driver unbind, control
request, configuration change or retry is implemented. Sending a USB header
still changes protocol state. Cached descriptor validation and interface claim
precede one OUT and one IN transfer. Each transfer has a two-second timeout.
The opened USB descriptor is verified using ARM32 statx and its cached descriptor.
The original ARM32 ABI, full cached descriptor, boot and interface guards remain.

The default invocation performs no target I/O. `--self-test` exercises 23
injected cases in the same execution engine, including wrong known data and
cleanup errors. Full-count unexpected data is retained but rejected. Host
execution refuses its non-ARM32 ABI. The five-file build manifest binds source,
project and the exact three deployment files, and records four host checks.

`run-once.py` also defaults to zero target operations. Its explicit execution
requires a manifest SHA and a new retained output directory. It uses the pinned
existing root runner, stages three verified files, runs fake-I/O self-tests,
invokes the active helper once and removes only those private staged files.
The complete root responses, helper output and cleanup result are retained.
The deployment script is fingerprinted separately in that runtime record.

Firmware analysis must resolve ordinary parser dispatch before live execution.
The mode-gate follow-up identifies ordinary operation1/2 mode0 producers at
VA `0x2905a..0x2905e`, and operation3/4 mode1 producers at `0x29076..0x2907a`.
All use the same literal for RAM `0x20000571`. These supersede the earlier
mistaken claim that the parser's initial mode2 assignment necessarily prevents
operation dispatch. A successful known-memory result would validate this narrow
live route, not establish complete installed-image equality or physical repair.
