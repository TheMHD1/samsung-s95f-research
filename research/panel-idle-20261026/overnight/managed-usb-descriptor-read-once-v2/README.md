# Fixed descriptor reader, sysfs streaming revision

This separate revision preserves the first helper and its actual failed run.
The first run passed23 fake-I/O cases, then stopped at preflight with
EndOfStreamException. Opened=false, Claimed=false, no OUT/IN occurred, and
the private stage was removed.

Cached target metadata subsequently reports stat size65553 for the sysfs
descriptor file, while an actual bounded `od -N117` read returns exactly116
known descriptor bytes. A cached file's reported length is therefore not its
content extent. `wc -c` also reports65553 here and cannot be used as the
independent content count; the bounded hexadecimal read supplies that evidence.

This revision replaces only the cached descriptor File.ReadAllBytes call with
a bounded Stream.Read loop. It accepts EOF at up to116 bytes and refuses a
117th byte. The existing exact116-byte content comparison still rejects a
short or different descriptor. It never uses Stream.Length or Seek. Four new
partial, nonseekable-stream cases cover lengths0/115/116 and oversized117,
bringing fake-I/O and stream cases to27. All other source/target restrictions,
ARM ABI checks, known18-byte data validation, cleanup and no-retry behavior are
the same as the previous [reader](../managed-usb-descriptor-read-once/README.md).

The deployment wrapper is unchanged and runs exactly once after fake tests.
Its default performs no target I/O. A timed-out/cancelled USB IN would leave
protocol rearming unproved; it never tries a reset or a second request.
Live execution results are recorded separately in the controller follow-up.
