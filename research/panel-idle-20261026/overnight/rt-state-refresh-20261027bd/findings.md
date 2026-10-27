# Fresh passive RT observation after the source-lifecycle analysis

Recorded 2026-10-27 UTC. This pass executed the existing unchanged X passive
observer once. It performed no UI/navigation, power, reset, fault clear,
controller data write, firmware write, bypass or flash. Physical picture was
not observed. No helper or collector remains running after accepted cleanup.

## Observed result

The accepted native observation spans Linux monotonic time
`142036.572541..142056.576396`: approximately 20.004 seconds. It reports 80
completed clean cycles, 480 exact fixed read requests and 960 bulk transfers.
There was no observed RT transition. The terminal reason is `TimeLimit`,
with `ReadyForHeader`, release and close successful and `STAGE_ABSENT`.

The RT triplet remains `stop=0, fault=0, ordinary_gate=1` in the retained
R endpoints. Thresholds are unchanged at `200/0/0/200/40`. The raw final
R SHA-256 is
`9fd238cba5da90bf84f18c6418d22b21ebdab875db903358fd4b7942f6cec90a`.

Only cycle 80's complete `R/M/C/H/L/R` raw windows are retained. The previous
79 completed clean cycles are represented by the observer's validated
summary counters, not separately retained raw bytes. Samples within each
cycle are sequential, not atomic. These are accepted read results under the
existing alias/model qualification, not live CPU-PC/core identification or
proof of callback execution.

## Comparison with the earlier AV clean window

The [decoded comparison](window-comparison.json) checks each saved window's
length and hash against its wrapper result. Comparing the final retained
clean cycles:

| Window | Changed raw bytes | Bounded interpretation |
| --- | ---: | --- |
| R | 2 | offsets `0x20` and `0x98`; clean triplet and known limits unchanged |
| M | 12 | raw changes; decoded selector fields below unchanged |
| C | 0 | byte-identical late snapshot |
| H | 0 | aggregates, q values and history entries remain zero |
| L | 0 | latest subtractor 0, mode6 latch 48, shared non-mode6 latch 0 |

M retains `aa=0, ac=2, alternate_mirror=0, scan_argument=1`, with root anchor
`0x20010000`; C byte7 remains 0. These late states do not reconstruct an
event-time selector or the actual comparison operands. Raw M changes do not
by themselves prove a particular callback or physical content producer ran.

The new observation starts about 85 minutes after AV's prior clean window
ended. That gap was not observed. The two clean captures do not establish
continuous clean state, absence of intervening faults/clears, or an intact
physical picture during the gap. No change is attributed to an unobserved
owner action or particular video/menu content.

## Execution and lineage

The unchanged wrapper and manifest identities are respectively
`a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82`
and `915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1`.
The wrapper verifies its complete local/native inventory before staging.

Fresh [host preflight](host-preflight.json), spanning uptime
`141992.59..142018.41`, confirms the same boot
`00000000-0000-4000-8000-000000000000`, USB device46 at `7-1`, active and
authorized, `04e8:2001` revision0250, configuration1, all three interfaces
unbound, and zero usbfs holders. The closed vendor lineage comes from BB's
strictly accepted complete primary-log read; BC was offline only. Metadata
alone is not the first-header phase proof. See [read-intent.json](read-intent.json).

The wrapper preserves 24 authenticated root calls and complete native output.
Its foreground native invocation occurs exactly once, with no retry. The
whole-command terminal uptime is `142056.76`; it is not a per-field time.
Offline independent audit and artifact hashes are recorded separately.

## Consequence for diagnosis

The latest controller observation is clean. There is no current evidence of
a latched RT fault that an automatic reset would need to clear. This does
not show the physical panel is lit, that all controller callbacks are
dispatching, or that a future sparse-menu transition would remain visible.
It supplies no verified blackout prevention or permanent root.

The existing physical-state question remains unanswered. Before a new power
or navigation action, pair the owner's visible/black confirmation with a
fresh controller observation. A later answer must not be treated as
simultaneous with this saved window. If physically black and contemporaneous
RT is clean, preserve that counterexample and investigate output/lifecycle
state rather than assuming fault1001 is equivalent to darkness. If physically
visible, preserve it as the control and capture one known failing transition.
