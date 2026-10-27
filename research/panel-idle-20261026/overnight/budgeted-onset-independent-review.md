# Independent review: budgeted 180-second HDMI onset collector

## Verdict

**CLEAR as an offline-prepared collector derivative only.** It retains the
ancestor's explicit `--run --reviewed` gate and defaults to dry output. This
review does not establish that a 180-second capture will fit, remain loss-free,
or be physically diagnostic. It authorizes no TV/root invocation.

No target, root, network, or device operation was performed during review.

## Exact files reviewed

| file | SHA-256 |
| --- | --- |
| `observed-hdmi-budgeted-onset-capture.py` | `18f2e3db892529218ca13fe5c7a3806348b155379d561db1cc07df7106d4be68` |
| `observed-hdmi-budgeted-onset-capture-tests.py` | `b5cdda519d61d7a4322a4669558cf7d4e683805b831cca86e58e16a950c6e694` |
| pinned long-HDMI ancestor | `65aeae50409ad05532163072e118140d09c7eaf3437aabc5b3843a138ab5c2eb` |

The derivative hashes and verifies its ancestor *before* importing it, then
only exposes 180-second observed mode or an explicitly marked five-second
physically-unobserved smoke mode. The render path and nested long/short path
are both overridden under a context manager and restored afterwards. The
offline nested smoke test reaches the actual lower frozen-run dispatch and
asserts that the staged script contains the budgeted ring and vlog limits.

## Capacity and guard review

The generated shell has one coordinated set of changes in both full and smoke
modes:

| resource | rendered value | enforcement |
| --- | ---: | --- |
| private trace ring | 8,192 KiB per CPU | exact readback plus strict usage below 8 MiB per CPU |
| total private ring | at most 32,768 KiB | metadata must equal per-CPU allocation × online retained CPUs |
| `vlog-after` sidecar | strictly below 134,217,728 bytes | writer, remote sidecar inventory, and host parser agree |
| preflight `MemAvailable` | at least 393,216 KiB | before trace-instance creation/ring allocation |
| preflight `/tmp` available | at least 393,216 KiB | same point |

The shell's existing `ulimit -f 1` sanity check requires `1024` bytes in
`/proc/self/limits`; therefore its `ulimit -f 131072` means 128 MiB on this
target shell contract, not an unqualified block-size assumption.

The resource guard appears before `mkdir "$T"`, the
`buffer_size_kb=8192` write, and tracing enable. The 32 MiB four-CPU ring
allocation therefore is **not** made before the 384 MiB guard. There is minor
earlier setup (private output/stage/watchdog and metadata-process work), so
the guard is a pre-allocation gate rather than a reservation/atomic resource
guarantee.

The retained five-second smoke record has only about 351,804 KiB
`MemAvailable`, below the new 393,216 KiB threshold. A run under the new
collector would therefore refuse before creating the trace ring; that old
record cannot be reclassified as capacity evidence for this collector.

The code correctly retains `capacity_qualified_for_180_seconds: false`. Its
short-capture rate calculation gives a planning indication only; no duration
extrapolation proves future vlog volume, ring occupancy, memory pressure,
event loss, or capture acceptance.

## Offline validation run

```text
python3 -m unittest -v observed-hdmi-budgeted-onset-capture-tests.py  # 11 passed
python3 -m py_compile observed-hdmi-budgeted-onset-capture.py observed-hdmi-budgeted-onset-capture-tests.py
python3 observed-hdmi-budgeted-onset-capture.py fixture-review --emit-shell
/bin/sh -n generated-shell
```

The rendered full shell was checked to contain the guard before trace-instance
creation, ring allocation, and `tracing_on=1`. The tests cover both fixed
durations, source/namespace isolation, the coordinated 128 MiB vlog limits,
metadata projection and rejection of old/oversized ring readback, strict
manifest cap, runtime context restoration, and offline staged nested dispatch.

## Retained boundaries

- A resource preflight is neither a live allocation reservation nor a safety
  guarantee. Any capacity, identity, parser, loss, sidecar, cleanup, or
  physical-annotation failure remains fail-closed.
- The increased ring and vlog files are private collector artifacts only;
  global tracing remains outside this derivative's intended writes.
- Five-second smoke mode is physically unobserved and cannot provide a
  visible-to-black/onset result. The 180-second mode still requires ordered
  owner physical annotations; no software trace, histogram, or output cache
  substitutes for them.
- This review does not change the current plan to use the already reviewed
  shorter bracket for a separately considered stock MODE2 operation.
