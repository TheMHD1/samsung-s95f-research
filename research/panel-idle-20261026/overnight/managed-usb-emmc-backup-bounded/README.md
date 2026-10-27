# Bounded read-only eMMC backup helper

This is an offline-built derivative of the pinned fixed-sector reader. It has
not been deployed or run on the TV in this directory's build/qualification
step.

The only active mode is `--execute`. It sends exactly one fixed 12-byte header
for target `0x203`, address zero and total length `0x500000`, then accepts
exactly 640 fixed 8192-byte IN transfers. It never sends a write operation,
retry, USB reset, control request, configuration request or second header.
Before the header and every IN transfer it checks a 15-second monotonic start deadline. Every
USB bulk operation has a two-second kernel timeout. A short/error transfer or
deadline stops the sequence and proceeds directly to interface release, FD
close and output close.

The fixed output files are `fixeddata.bin` and `result.json` in the assembly
directory. Both must be absent before execution and are opened with
`FileMode.CreateNew`. The data file retains only preceding exact 8192-byte
chunks after a failure. `result.json` includes every attempted chunk's exact
count, errno, timing, storage status and SHA-256, plus lifecycle cleanup.
Stdout contains only a concise summary, never the 5 MiB payload.

The exact-count and hash checks do not prove storage freshness. Recovered
controller code schedules USB IN even if its eMMC read leaf reports failure.
Any acquisition must therefore be compared for structure and repeatability
before it is treated as a firmware image.

Default invocation is a zero-I/O plan. `--self-test` runs 45 injected tests
with zero target operations. On a non-ARM32 host, `--execute` exits 64 before
creating output files or opening USB.
