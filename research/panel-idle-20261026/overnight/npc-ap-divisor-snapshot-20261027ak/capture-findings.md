# AK actual divisor snapshot

2026-10-27 UTC. Root executed the separately reviewed fixed reader once.
Its accepted result is in capture-once/result.json, with authenticated call
record, native envelope/stdout/stderr, self-test and exact raw response.
The [independent runtime review](runtime-review.md) passed, including replay
of all19 authenticated call records and the exact native/result contracts.

## Returned bytes

```text
target/address/length: 0x101 / 0x4500d730 / 8
raw:                   64 00 76 00 76 00 76 00
conditional NPC_AP+14: 100
conditional NPC_AP+16: 118
conditional NPC_AP+18: 118
conditional NPC_AP+1a: 118
raw SHA-256: 703e6dd703874a61cf296a379be701c53e5db31d7b51e5e1c868504fb380a86d
```

The three candidate divisor values differ from the stored metadata payload's
1024/1024/1024. This is a real target observation through the qualified
selector-zero RAM mapping. No NPC-specific live pointer gate exists, so
unconditional live object identity is not claimed. Matching context100 is
not an identity acceptance condition.

## Transport and time

The wrapper retained 19 authenticated successful root calls, one native
execution, one fixed read request and two exact bulk transfers. The native
terminal phase was ReadyForHeader; release and close passed. Native exit0,
empty stderr, raw/hash/decoded consistency and strict framing passed before
the private stage was removed with STAGE_ABSENT. There was no retry, reset,
parameter/code write, UI command or physical observation. No helper remains
running from this invocation.

The boot was 00000000-0000-4000-8000-000000000000, terminal Linux uptime
131155.57. Native monotonic ticks bracketed the request pair from
131155397966259 to131155403963173 at frequency1e9, a 5.996914ms host-side
request interval. This is not a controller execution timestamp or physical
onset annotation.

## Arithmetic implication and limits

With the OLD W numerator3*900 and cap6, each new divisor118 would produce
candidate23 and final6 in the reviewed finite-domain calculation, whereas
the stored divisor1024 predicts3. Thus current candidate values can account
numerically for the earlier retained capped indexes without using the
stored defaults as runtime invariants.

This substitution is a cross-time comparison: W's terminal uptime125699.16
preceded AK's by5456.41 seconds (90minutes56.41seconds). AK did not sample
AP_EXCO, controls, source bins, current RT state or emitted light. It does
not prove the divisors had value118 at W, identify the writer/branch that
produced them, reconstruct an actual invocation or fault event, establish
physical units, or identify a safe repair parameter.

## Closer ordinary snapshot

After AK completed in a known Ready phase, root reused the unchanged reviewed
W reader once, with fresh output directory capture-ordinary-after. The
[independent runtime audit](ordinary-runtime-review.md) passed all20
authenticated calls,48zero-I/O self-tests, one native execution, three fixed
reads/six exact bulks, anchors, ReadyForHeader, release/close and cleanup.
No helper remains running. Across both AK acquisitions there were two native
invocations, four read requests and eight bulk transfers.

This acquisition ended at Linux uptime131332.14 on the same boot,176.57seconds
after the divisor-read terminal. The pointer32, ordinary824 and derived1004
raw bytes are all identical to original W, whose terminal was5632.98seconds
earlier. Equality is an observation at two times, not proof of continuous
immutability.

The closer ordinary prefix contains ea=3,f0=900,caps6/6/6,indexes6/6/6 and
recompute116=1. Its e6=1,2fc=0 and derived3d8=1 still match the recovered
selector expression. Substituting the earlier118/118/118 candidate divisors
gives rounded candidates23/23/23, then capped6/6/6, equal to the retained
indexes. The same arithmetic with stored1024s gives3/3/3.

This closes the missing numerical-consistency input under the conditional
NPC alias interpretation, using samples separated by176.57seconds rather
than combining only with original W90.94minutes earlier. It does not prove
a simultaneous invocation, the value's writer/branch or unit, a new RT
transition, displayed content, emitted light, or blackout causality.

`verify-capture-comparison.py` pins both new raw captures and call records,
checks original-W equality and exact decimal terminal separation, and models
the finite positive-divisor quotient with STRH truncation before clamping.
Normal/optimized outputs are identical, SHA-256
`f154615e8300de95a79d0ca9af06575956cba3b9d4227cee70660ec2fe7ab400`.
Independent arithmetic/scope review passed with no findings; see the
[comparison review](comparison-review.md).
