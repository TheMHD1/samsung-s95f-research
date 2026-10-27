# Finite secondary-controller onset logger: native core

This directory contains the offline-built native core for one finite 20-second
controller logging window. It derives from the independently qualified
three-second logger core. It has not been run on the TV.

The helper has fixed USB targets, addresses, lengths, payloads, deadlines and
file names. It accepts no caller-selected address, duration, payload or output
path. Before mutation it validates the live callback tuple, captures the full
ring, and requires a fresh complete RT block with both the logging gate at
`+6` and fault halfword at `+0x0a` equal to zero.

After an exact arm write and exact gate-one readback at a known
`ReadyForHeader` boundary, it publishes `logger.ready` through a fresh
`logger.ready.tmp`, durable flush and non-overwriting atomic rename. The ready
record binds the fixed schema, validated stage token, boot, PID, monotonic time,
`/proc/uptime`, gate one and protocol phase. The exact ready JSON and SHA-256 of
the newline-terminated file are repeated in the final native outcome.

The `observe-start` marker is taken immediately before readiness publication;
the 20-second no-USB hold starts after successful publication. Publication has
a two-second admission budget. A publication failure or overrun at the known
ready boundary rejects the run and goes directly to urgent restoration. A
short, failed or ambiguous USB transfer enters a non-ready phase and prohibits
all later controller packets. Release and close do not repair protocol state.

The monotonic deadlines are fail-safe admission bounds, not hard real-time
guarantees. Managed runtime, filesystem and scheduler behavior can delay code.
The external supervisor must remain finite and must never retry the native
execution after an ambiguous outcome.

`build-native.py` performs no target operation. It checks the qualified parent,
builds with zero warnings/errors, runs 85 zero-I/O tests, verifies host ABI
refusal, checks the fixed dry contract, and reproduces all three deployment
artifacts byte-for-byte in a fresh directory.
