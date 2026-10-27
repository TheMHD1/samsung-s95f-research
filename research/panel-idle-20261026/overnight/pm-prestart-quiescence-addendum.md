# Bounded numeric-54 quiescence retry addendum

Status: implementation contract for a new derivative observer. It does not
modify or reclassify the frozen PM observer, either retained failed smoke, or
their archives. It authorizes no target action.

The independently reviewed design is `pm-prestart-quiescence-review.md`,
SHA-256 `d7c8e0be5cec4867159c20e4864d5c9b7740765829f2ac3ebc78f9b09d657229`.
The derivative pins the frozen PM observer source SHA-256
`c7b07bbcb508005c028824763c84109d18aee1d9df8813a5f59c476093616d06`.

## Remote change

The only acquisition-state change is inside the existing read-only
`/proc/$avoc_pid/task/$tid/syscall` quiescence loop. Literal `running` remains
indeterminate. A parseable numeric syscall 54 is now retained as
`transient_active_54` and retried just like an indeterminate sample. Each TID
still has at most eight attempts with a requested 2 ms delay, and every attempt
is still bounded by the absolute 0.500-second trace prelude. The post-sweep TID
check, FD snapshot, and PREROLL marker must fit the same envelope.

Only a terminal parseable numeric syscall other than 54 qualifies a TID.
Attempt exhaustion, terminal 54, read failure, malformed data, missing or
duplicate TID, clock/order violation, changed TID set, or prelude overrun
rejects before the physical window. No timeout, trace exit, inferred return, or
request-specific timing assumption can substitute for the terminal point
sample.

## Host evidence

The FDS validator retains every raw attempt and classifies it as
`indeterminate`, `transient_active_54`, or terminal `numeric`. Attempts are
strictly contiguous, grouped in exact sorted TID order, finite and monotonic,
and bounded by the unchanged constants. Every row before the terminal must be
one of the first two kinds; the final row must be numeric and not 54.

The report lists intermediate 54 observations under `active_nr54`, preserves
their full raw register text and time, and records terminal point anchors. This
does not pair a sampled call with a trace exit, prove its return, or promote an
outside row into physical-window evidence. Continuous raw-syscall tracing only
closes the race after each terminal point sample: later entries remain subject
to the frozen prelude/pre-roll/window/drain pairing and loss rules.

## Isolation and unchanged limits

The derivative uses new private output, staging, and trace-instance namespaces.
It retains the seven exact PM formats, PID-0 idle qualification, PM pairing,
source/identity/maps/FD/thread/filter/loss/cleanup guards, annotations, and
physical `CAPTURE_START..CAPTURE_END` window from the frozen parent. It is dry
by default and requires both `--run` and `--reviewed`. It adds no keys, getters,
setters, ioctls, device calls, global trace writes, native helpers, automatic
capture reruns, or target actions beyond the bounded read-only sampling already
described.

The mutable ftrace flag/state token remains only a conservative pairing
disambiguator, not authoritative execution-context identity. Framework silence,
quiescence success, and trace silence support no generic absence, physical, or
causal claim. A separately reviewed finite passive smoke is required before any
capacity or longer-duration consideration.

## Namespace correction after the first derivative smoke

The first derivative revision is preserved read-only in
`observed-quiescent-pm-rejected-ee4ee2b/`. Its source, tests, and this addendum
had SHA-256 values `ee4ee2b9568f8618e8f4d16f5402ebb882f4bf380bf84326e072c03079f4b847`,
`f4e185cf7e6aa6b7f0ec496a0a630b09cc8f89abe91ddd5d6b0540f9c7584784`,
and `b72e70e640d9b32420d14d0c9bb76c1ec62ed2f254cb5c181e6d8f06a6b98678`.
One passive smoke completed, but independent review found that the generated
collector and authenticated launch used the derivative namespace while
returned staging metadata and redundant host cleanup named an ancestor PM
namespace. The collector's successful self-cleanup likely removed its actual
private trace instance; that does not make the failure cleanup contract sound.
The smoke also had no intermediate syscall-54 attempt, so it did not live-test
the new retry branch.

The corrected derivative normalizes output, staging, and trace-instance paths
from every ancestor layer at the terminal transport boundary. It wraps inherited
staging metadata so the returned path equals the path actually used by the
translated staging commands. Both normal and failure cleanup commands must name
the derivative output/stage roots and exact private trace prefix, and offline
tests exercise the public nested success and acquisition-failure paths while
capturing every would-be transport command. This changes no event, quiescence,
window, resource, or interpretation rule and authorizes no automatic rerun.
