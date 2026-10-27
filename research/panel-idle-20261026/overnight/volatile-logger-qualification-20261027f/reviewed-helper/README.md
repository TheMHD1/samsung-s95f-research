# Fixed secondary logger smoke qualification

This helper implements the reviewed arm-verified finite experiment as one
native state machine. It is offline-built and performs no target operation by
default. It accepts only `--self-test` or one `--execute`; no address, length,
payload, hold duration, deadline, retry, or reset is caller-selectable.

The fixed sequence reads and validates the packaged callback tuple, captures
the complete secondary ring, and takes the last fresh 64-byte RT read. It
will not write unless the complete halfword at RT offset `+6` is exactly zero.
It then sends fixed target-`0x102` header/payload `01 00`, reads back exact one,
holds for three seconds without USB traffic, sends fixed payload `00 00`,
reads back exact zero, and finally captures the complete ring again.

Every transaction models `ReadyForHeader`, `ExpectingWritePayload`,
`ExpectingReadIn`, and `Unknown`. Any short count, overcount, exception, or
timeout after a transaction begins enters `Unknown`; that state forbids all
later USB traffic, including blind restoration. At a positively known ready
boundary after arm, restoration is mandatory even after logic or hold errors.

This is a diagnostic logger qualification, not a panel repair. It does not
touch thresholds, protection settings, persisted storage, flash, EEPROM,
ring cursors, or availability flags. No TV execution has been performed.
