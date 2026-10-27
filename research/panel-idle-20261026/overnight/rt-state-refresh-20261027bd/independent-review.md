# Independent replay of the unchanged passive-observer run

Recorded 2026-10-27 UTC. Root records the independent read-only review here.
The reviewer used the pinned common response validator and the unchanged
wrapper's envelope/native parsers; no target, network or helper operation
was performed during review.

## Accepted execution

- All 24 root calls have authenticated root UID/EUID, exact command binding,
  successful transport and target exits, no timeout, and empty stderr.
  Stored transport JSON reproduces each parsed response.
- The call layout is one stage creation, 17 chunk uploads, three file
  checks, one injected-I/O self-test, one native execution and one cleanup.
- The self-test reports 75 passed tests and zero target operations.
- Native stdout is 4583 bytes, SHA-256
  `9916e0e9e99c46534eed15f40de6d67cc02e499a1c441542847eb36059d1785f`;
  native stderr is empty. One outcome JSON and four classified GC diagnostic
  lines are retained. Native exit is zero.
- The native outcome is accepted, terminal `TimeLimit`, `ReadyForHeader`,
  opened/claimed/released/closed. Writes and retries are zero.
- Start is `142036572541` microseconds; deadline is `142056572541`;
  end is `142056576396`, 3855 microseconds beyond the fixed deadline.
- There are 80 started/completed-clean cycles, 79 discarded clean cycles,
  480 exact headers, 480 complete inputs and 960 bulk transfers.
- The complete raw `R/M/C/H/L/R` set for cycle 80 is retained. Its 12
  transfers have exact counts, errno zero and monotonic timestamps. Its two
  R brackets are byte-identical and decode clean `0/0/1`.
- The accepted cleanup receipt is exactly `STAGE_ABSENT`.

## Bounded comparison

AV's and BD's retained final clean cycles are about 5134.33 seconds apart on
the same Linux boot. C, H and L are byte-identical. R changes only at `+0x20`
and `+0x98`. M changes at 12 byte offsets: `0`, `0x10`, `0x12..0x15`,
`0x26`, and `0x30..0x34`. No new physical meaning is assigned to those bytes.
Root's [window comparison](window-comparison.json) agrees.

The earlier 79 cycles cannot be independently replayed as raw data; their
clean counts are accepted native summary evidence. Discrete sequential reads
do not supply atomic state or continuous gap coverage. The result establishes
a later clean sampled software state, not an onset, active callback identity,
physical picture, recovery or prevention. No material transport/parser issue
was found in this bounded review.
