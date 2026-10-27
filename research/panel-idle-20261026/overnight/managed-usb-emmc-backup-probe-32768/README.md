# Fixed 32 KiB storage-read boundary probe

This helper is an offline-built, fixed-scope derivative of
`managed-usb-emmc-backup-bounded`. It keeps the reviewed native USB identity,
FD, interface-claim, transfer, deadline, output, and cleanup engine. Its only
active request is one read-only target `0x203` header at address zero for
`0x8000` bytes, followed by exactly four 8192-byte IN calls.

The probe qualifies a boundary that the earlier single-8192-byte read did not
cross. The returned controller code selects a 24576-byte internal response
chunk for operation 3. Four host reads consume three 8192-byte portions of
that first internal chunk and then require the controller's continuation path
to supply the fourth. A successful run therefore tests both splitting the
24576-byte response and crossing into its continuation.

This program does not contain a storage-write request, arbitrary target,
arbitrary address, retry, USB reset, control request, or second header. It
stops on the first short/error transfer and always attempts interface release,
FD close, and output close.

If a partial/error transfer occurs, the controller's request may remain
protocol-inflight. Releasing the interface or closing the host FD does not
constitute a device-protocol abort, and normal next-header rearm occurs only
after the requested remainder reaches zero. An operator must not automatically
retry this probe or issue a new header. Re-enumeration or reboot and fresh
protocol-state qualification are required before another request.

Default execution is dry. `--self-test` performs injected zero-I/O tests.
`--execute` is additionally restricted to the expected ARM32 ABI and writes
`fixeddata.bin` plus `result.json` with create-new semantics beside the
assembly. Exact transport counts and cleanup still do not prove storage-leaf
success, freshness, partition identity, current execution identity, physical
panel recovery, or a repair.

The derivative changes only five logical inputs/assertions in `Program.cs`:
total length/chunk count, the fixed request header and its check, the known
all-`0x5a` success hash, the middle-deadline test timing/count, and the fixed
extent assertion. The assembly/project name deliberately remains
`ManagedUsbEmmcBackupBounded` so a separately reviewed host runner can select
one fixed build profile without changing target-side behavior.
