# Independent audit of the bounded-quiescence PM smoke

Status: offline independent review of the already completed passive capture
`qpm-smoke-20261026t204819.onset`. This review made no TV, root, network,
display, device, or control call. The retained capture bytes were not changed.

## Outcome

The retained trace, metadata, samples, and logs form a technically complete
five-second, physically unobserved capture. Re-running the exact host parsers
over the raw sidecars reproduced the record's process/FD report, metadata and
trace accounting byte-for-byte; sample and vlog summaries also reproduced
(JSON changes integer dictionary keys to strings in `sample_stderr`).

Two host-side namespace defects prevent treating the executed `ee4ee2b...`
derivative revision as safe for another run without correction:

1. `staging.json` line 2, and consequently `record.json`'s `staging.path`,
   names the parent path
   `/tmp/researcher-observed-pm-onset-stage-20261026/.../capture.sh`. The
   authenticated launch command actually verifies and executes the derivative
   path
   `/tmp/researcher-observed-quiescent-pm-onset-stage-20261026/.../capture.sh`.
   Bytes, hash, chunk count, and the launch-time check are correct, but the
   recorded path is not.
2. `cleanup.json` line 11 targets trace instance
   `researcher-pm-onset-qpm-smoke-20261026t204819`, whereas `remote.sh` line 6
   created and used
   `researcher-quiescent-pm-onset-qpm-smoke-20261026t204819`. Thus the host cleanup
   did not independently verify or remove the actual derivative trace
   namespace. For this successful run, `remote.sh` line 77 disables the exact
   derivative instance and requires `rmdir "$T"` under `set -e` before line 84
   emits `CAPTURE_COMPLETE`; `collector.stdout` line 8 proves that path
   completed. This is run-specific evidence that the actual instance was
   removed, but it does not repair the cleanup failure path or make the stale
   host check a valid redundant cleanup check.

The new retry branch was not exercised live. `fds.txt` lines 123-145 show all
23 AVOC TIDs qualifying on their first numeric non-54 sample; the parsed
`active_nr54` list is empty. The retained earlier failure and offline fixtures
test the numeric-54 case, but this run validates only the no-retry runtime path.

Accordingly, the captured data can remain recorded as technically complete,
but the executed revision's runtime contract is not accepted. A later offline
revision, source SHA-256
`8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`,
corrects both namespace leaks and covers them through the nested public-run
tests; it has not been validated by this live smoke. This audit does not
promote the run to a physical observation or diagnostic capture.

## Exact identities

Reviewed host inputs:

| item | bytes | SHA-256 |
|---|---:|---|
| `observed-quiescent-pm-onset-capture.py` | 14,713 | `ee4ee2b9568f8618e8f4d16f5402ebb882f4bf380bf84326e072c03079f4b847` |
| `observed-quiescent-pm-onset-capture-tests.py` | 14,799 | `f4e185cf7e6aa6b7f0ec496a0a630b09cc8f89abe91ddd5d6b0540f9c7584784` |
| `pm-prestart-quiescence-addendum.md` | 3,246 | `b72e70e640d9b32420d14d0c9bb76c1ec62ed2f254cb5c181e6d8f06a6b98678` |
| retained `remote.sh` | 35,490 | `20d7e911fa74f4612e6d218c9f2c22b8901f2b81cce6ada3da7a7fd4106a700c` |
| `record.json` | 9,612,916 | `82771270a4aed3b08f8afa9c9bc6bac6fd175d77ea4abdf38bc8d4a9e846553e` |

Regenerating the five-second shell from the reviewed source and exact label
produced all 35,490 retained bytes and the same SHA-256. Metadata lines 6-8 and
5026-5028 bind that same staged file at both endpoints. The Q sampler is 3,572
bytes with SHA-256
`ff7e35825dfcfc047af80825cf09b6d3b8d1c22091dace53d899a065ac5405fe`
at both endpoints.

The authenticated launch response is SHA-256
`26e949bd91ef8944aa30a618e1df0ee723907e31c8f03e4c58a361ac985ab367`.
It reports model `QN77S95FAFXZC`, UID/EUID 0, host-assisted persistent root,
unchanged global-system-file status, command exit 0, no timeout, empty stderr,
and collector PID/process group 17006 with start ticks 17327987. The command
checks the actual derivative script path, size, and SHA before execution.

Metadata validates one boot ID at both endpoints, AVOC PID/start 706/603 and
deviced PID/start 675/560, unchanged executable/source hashes, exact maps,
unchanged typed QDDimming/RoseMQD pointer chains, and distinct owned monitor
and Q sampler identities. The synchronization envelope is uptime
69313.08..69333.51; the trace window is 69323.81..69328.88 with drain end
69328.98.

## Raw sidecars and independent parser replay

`collector.stdout` lines 1-7 authenticate all fetched sidecars and line 8 is
the sole completion marker:

| sidecar | bytes | SHA-256 |
|---|---:|---|
| `trace` | 1,198,275 | `64bd189afff5c01a08556cac05f3407489ba74a9bcf2c6d0140a88051bc9f9a5` |
| `meta.txt` | 494,864 | `7d6a74c59eddc39cbc7ece8480ea1d9ad1d59a13fbe56ac6b5bcd7b9ff0241c3` |
| `samples.txt` | 6,962 | `7261cfb0e6ab066d6020be208a45f2714e220cce6a291057f4a25f3a924cea7c` |
| `sample-errors.txt` | 14,754 | `5eb7645b3f08a53d3966a9772d949aba11fd8ca67d799ea2ec98b102a3e4d8b4` |
| `vlog-after.txt` | 4,898,382 | `0b9e673c776e53bf3e0907bfbb8c176ca968039eb62173c8200ab44c5b6db267` |
| `artifacts.txt` | 4,433 | `4aad0fc8cfaefd2945c2879874b90e629b0b1b8f30c5a7e02fbc3f0f5b988bf4` |
| `fds.txt` | 5,710 | `139c6413db42a1f4caf10d602fb8ac856db57e794a1a29589a19b98b7085bd47` |

The independent replay established:

- all START/PRE/ARM/post-sweep/END TID sets are the same 23 sorted TIDs;
  start/pre-roll/end FD maps are identical;
- the sweep spans 0.150 seconds within the fixed 0.500-second prelude and all
  rows have contiguous attempt indices and terminal numeric non-54 samples;
- five exact owned markers occur in order at trace lines 29, 732, 1949,
  10675, and 10796; the physical window remains START..END;
- trace retained/written/decoded counts are all 10,777, with zero reported
  per-CPU overrun, commit overrun, or dropped events on CPUs 0-3;
- 2,729 syscall-54 pairs are complete: 107 outside/prelude, 436 pre-roll, 2,137
  window-complete, and 49 drain-only. There are no start-boundary or
  window-tail pairs, unmatched rows, pending calls, lifecycle ambiguity, FD
  changes, or post-drain syscall rows;
- the seven PM formats and their private enable readbacks match at both ends;
  PM accounting has 238 selected rows, 119 complete runtime-PM pairs, seven
  window-overlapping pairs, no malformed or unmatched selected PM rows, and
  no positive exact `sdp-hdmi` callback correlation;
- 22 monitor and five Q rows pass identity, map, endpoint, ordering, and span
  checks; all 191 expected `dd` operations have only complete success
  summaries;
- vlog contains 32,550 ordered records covering the required endpoints, with
  a maximum observed timestamp gap of about 0.010 seconds and natural exit 0.

These are capture-completeness properties only. In particular, selected PM
returns, ioctl returns, source-backed pointers, compositor output, and log
rows do not establish physical panel light or hardware acceptance.

## Cleanup and bounded conclusion

The host cleanup response is SHA-256
`90a08195c6339449fed64311b91c0eb3ef253d1c71bd74d684cf9b9a86c7f069`.
It is authenticated UID/EUID 0, exit 0, no timeout, empty stderr, and stdout
`0\nCLEAN\n`. It verifies the derivative output/staging directories and owned
process files, and global tracing remained off. Its trace-instance check is
nevertheless the stale-parent-path defect described above.

A later, separate fixed read-only residue check closes the status of this
particular completed run without repairing that source defect. Its authenticated
raw response is
`quiescent-smoke-residue-20261026/client-stdout.json`, 2,214 bytes, SHA-256
`4480e7e25a9db002acee96df495f2f3a88d0ec10d5a14c410b285fb27e8a7355`.
On the same boot ID, uptime 69670.76..69670.77, it reports both the derivative
and parent trace instances, both derivative output/staging paths, and both
parent output/staging paths absent. Global tracing is `0` with tracer `nop` at
both endpoints. The persistent-root response is authenticated UID/EUID 0,
exit 0, no timeout, and empty stderr. This proves those six exact paths were
absent at the later check; it is not a general filesystem/process absence
claim and does not make the defective cleanup command correct.

The record's `accepted=true` is supportable for the retained sidecar and
parser-completeness result, with the successful collector's mandatory exact
trace-instance removal and later six-path residue check providing run-specific
cleanup evidence. The executed revision's runtime contract itself is not
independently accepted for reuse; the corrected offline successor is distinct
from this run. The result
must not be
used to claim that the derivative's host cleanup contract is correct, that
numeric-54 retry succeeded live, that a blackout occurred, that any framework
or proprietary PM path caused the symptom, or that the physical fault has
been repaired.
