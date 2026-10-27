# Independent review record: factory, notification and ARM32 probe

This records findings returned by read-only reviewer `runtime_reader_review`
and parent instruction-level checks during the post14:00 follow-up. It is
written by the parent; the reviewer did not edit evidence or call the TV.
No factory write or notification action occurred.

## Rejected factory conclusions

The first transmit report confused the separate factory index tuple's5 with
the serialized node's driver field. Correct node base0x6919c has UID0x506e
at+0x40 and selector16 at+0x44. The copied factory-interface constructor
copies0x164 bytes and preserves+0x44, while separately assigning the loop
index at+0. Therefore selector5's unsupported arm cannot justify the result
for this item. Selector16 reaches the diagnosis and VE PPI calls.

The reviewer also rejected an intermediate claim that diagnosis return-95
prevents storage. The actual call at TIFS0xc5f3e is followed by a logging setup
that overwrites r0 at0xc5f44. The comparison at0xc5f72 follows the **VE** call
at0xc5f6a and tests VE's result, not the earlier diagnosis result. A terminal
callee error must not be propagated across this caller without tracing it.

For the copied UID0x506e path, the diagnosis default method does not preserve
or dereference the incoming status pointer. AVE's recovered FRC/TCON paths
return zero without a lower setter for this UID. Setter0x107822/24 initializes
the skip byte0; transmit0xc5e96 loads it and0xc5ee8 initializes its local
status. The VE-success route0xc6174→0xc6160→0xc6172→0xc6018 normalizes/copies
status0 at0xc6028, returns0 at0xc5fec, and allows the setter predicate at
0x107840–0x10784e to select storage0x107890. This is a recovered binary path,
not a performed write or a proven daemon reload/physical result.

Several checker defects were caught before accepting the audit: a malformed
factory-interface hash, too-short disassembly slices, a cmp/branch address
mix-up, and an incomplete VE backend/table chain. These illustrate the limit
of a passing landmark checker: matching isolated calls/constants cannot prove
the whole control flow or an error's effect. The final report must distinguish
automated exact-site checks from manual path review.

The live GOT observations bind the TIFS imports to libvideo-misc and
libvideoenhance. Merely finding a downstream implementation in process maps
does not independently read every backend pointer; the downstream table and
method chain is also reconstructed statically from the matching acquired
implementation. No live factory receiver call was used to validate behavior.

Final scoped review cleared report SHA
`4f25430cc4f7de89dbcb24f832fcff195e5042123b6111e0a0633b75fe3f4561`
and checker SHA
`d3e8a5da6d5c1cbd7878a619afa3b6416f29040e3a87b20b9b79fba0f69de1a4`.
The reviewer reran the checker successfully. Its final output explicitly says
`PASS: hash-gated landmarks; manual paired-path review required`. No remaining
blocker was found in the requested provenance/coverage/conditional-route scope.

## Notification separation

The legacy notification RPC and C++ notification_ex protocol must be traced
separately. A type2 EventInfo in the latter does not establish the legacy
callback integer. The reviewer traced legacy del_noti_single0x15d2c to
0x143c0: only successful database deletion with changed-count>0 builds the
legacy `(iii)` payload `(1, priv_id, uid)` and emits delete_single_notify to
UID-registered monitors. The client conversion/registration and resulting
viewer callback were then resolved by the notification researcher: client
0x46c5cf7a matches delete_single_notify, parses `(iii)`, and supplies literal
event1 to dispatcher0x46c5ec8c. A live kind-2 detailed callback registration
receives that event, which reaches the previously reviewed viewer timer
destruction branch. This is a linked conditional static route, not observed
runtime delivery. Server signal emission alone would not establish it; the
separate client mapping is necessary. Authentication, actual deleted count,
live registration and an already-dispatched expiry remain test boundaries.

The parent independently decoded the provider count predicate, event1 and
send call, the client's literal event1/dispatcher call, and fourth-argument
detailed-callback callsites. The resulting offline landmark reproducer passed
with all four source hashes gated. This supplements the manually traced
legacy route; it does not turn it into a live delivery test or an automated
complete CFG proof. The final cancellation report was reconciled to remove
earlier missing-server/callback assertions and separate notification_ex type2.

## Managed ARM32 probe review

Source and runner were independently reviewed before execution. Cdecl native
word arguments match ARM EABI libc syscall; the program verifies ARM/4-byte,
root, Seccomp0 and libc/raw getpid equality before invalid BPF/perf requests.
Architecture refusal was exercised on the host before P/Invoke. Stock
runtime hashes/boot are pinned; staged data is SHA-checked; commands are
bounded; watchdog and exact private cleanup were reviewed. A transport outage
can strand the recorded private path, a documented artifact limitation.

The reviewer independently inspected the completed result: all eight root
calls succeeded with clean transport and remote status, actual ARM32
PID19071 matched, both libc returns were-1/errno38, runtime exit0/stderr empty,
and exact private directory removal was confirmed. This establishes ENOSYS
for the ARM32 compatibility interface exercised by the stock CoreCLR on this
boot. It does not establish native ARM64 availability or global CONFIG
absence. The prior native ARM64 helper was not retried, and no execution
policy was changed. See [the probe record](managed-kernel-abi-probe/README.md).
