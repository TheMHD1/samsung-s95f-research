# Independent consistency review of the final AV findings

Recorded 2026-10-27 UTC. This was a read-only consistency review of the final
AV summaries against the already completed baseline/lifecycle and post-X
audits. It made no TV, network, USB, controller, UI, reset or firmware call and
did not rerun the raw-capture audit.

Reviewed exact files:

- `findings.md`: SHA-256
  `75322162af338a9bad1d071128a30084cda564daaa39621ca8dbfcce9ea97f88`;
- `CURRENT-INVESTIGATION.md`: SHA-256
  `6be666c84c702a6dce43426ed8deadf2a4c851acf5f33816fc27e3a38e600f89`;
- `ordinary-fault-model-20261027.md`: SHA-256
  `694c821323908217e0747863563d2179849275ef3438b8fb4f8d45d154723117`;
  and
- `post-x-independent-review.md`: SHA-256
  `bab8aab040cd0a635e607e70f764b4ba8868c492ffb7db3b8fb6c272f4fa5e64`.

## Result

**Substantive PASS with three narrow wording corrections in `findings.md`.**
The counters and timing are consistent with the accepted post-X result:
80 cycles, six reads per cycle, 480 reads, 960 bulks, `TimeLimit`, and native
uptime `136902.237744..136922.242531`. The reported `536.016`-second delay is
the correctly rounded difference between X start and the final lifecycle I2C
transfer at `136366.222190`. The retained raw evidence is correctly limited to
cycle 80, while the prior 79 clean classifications are explicitly described
as native-summary evidence rather than replayable raw cycles.

All three summaries preserve the important boundaries: the enclosing AVOC
record remains rejected, physical picture/light remains unobserved, cached
Apps/screensaver/compositor state is not treated as emitted light, MODE2 is not
claimed as the exclusive cause, and no permanent repair/prevention or reset
loop is claimed. Local Markdown links in the three reviewed summaries all
resolve.

## Corrections requested

1. `findings.md` says, without a scope qualifier, “No intervening vendor OUT
   was sent.” The reviewed clearance was conditional on the **recorded
   closed-world action lineage**; the retained artifacts do not prove
   continuous global absence of an unrecorded actor. Change this to “No
   intervening vendor OUT appears in the recorded action lineage” (or
   equivalent) and retain the bounded ownership-snapshot limitation.

2. `findings.md` and the ordinary fault model call MODE2 a “candidate stock
   recovery operation.” The present evidence supports a candidate operation
   **associated with delayed clearing of the sampled software RT tuple** for a
   future owner-observed recovery test. It does not yet support the unqualified
   noun “recovery operation,” because no physical picture was observed and the
   reset-domain/causal edge remains missing. Qualify that phrase accordingly.

3. `findings.md` says “No busy signal was observed.” The preflight proves only
   that no **sampled public busy signal** was present at its bounded reads; it
   explicitly does not exclude a scheduling race or prove an atomic private
   maintenance gate. Insert “sampled public” to keep this sentence aligned
   with the immediately preceding limitation.

No counter, timestamp, raw-tuple, cleanup, AVOC-rejection, UI-context, or
physical-state correction is otherwise required. These are documentation
scope fixes only; they do not invalidate the accepted narrow result:
faulted `1/0x1001/0` before the one stock lifecycle and clean `0/0/1` in a
delayed post-lifecycle software sample.
