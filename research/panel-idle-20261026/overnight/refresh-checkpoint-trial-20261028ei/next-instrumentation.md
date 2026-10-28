# Follow-up logger questions from the initial-fault refusal

This is a design queue, not an implemented or deployed helper. Preserve the
original EI attempt as an AlreadyFaulted, unqualified key trial; do not relax
its guard to turn it into a successful onset capture.

The first R was faulted before EH armed its Left action. The preceding
healthy EB read and normal Apps/wake/header operations were outside EH's
observation window. Therefore later work must consider faults during the
Live-to-Apps return, screensaver/wake, header preparation or the intervening
idle interval. None is established as the actual onset. Capturing only the
Apps-to-Live direction leaves these transitions unobserved.

One candidate is a separately reviewed fixed Right workflow starting from
Live, using the same read windows and no controller writes. Another is a
finite observer that includes the normal wake/header preparation inside
its logged window. Either requires explicit key/focus prerequisites, source
and parser changes, bounded/reaped children, distinct result schemas and
new successful and refused-path tests. Do not substitute a Right key into
frozen EH or describe a different workflow as the existing one-Left trial.

The54-byte/60-record design fits a tight structured-receipt cap but polls
only every250ms. A future denser flight recorder could allocate a small,
fixed buffer in **its own Linux userspace process before opening USB** and
write an exclusive0600 sidecar in the existing private temporary stage after
capture. A bounded new wrapper would fetch exact-sized/hash-bound chunks
after release/close, then remove only its explicit enlarged stage inventory.
This would avoid enlarging the single structured receipt and could retain
more intermediate M/C/P/score context. It would not own controller SRAM,
instrument every firmware call, provide a B-header alias or prove physical
light. It needs a fresh file contract, independent tests, limits on memory,
duration and read frequency, and exact failure cleanup. No such sidecar or
faster polling is present in the completed EH source.

Keep the executable-hook route separate: source sites are known, but DZ has
not proved owned controller scratch, instruction replacement/cache behavior
or deterministic rollback. A Linux-owned read logger is not an installed
firmware breakpoint. No kernel/boot/flash modification follows from these
questions.
