# Actual unchanged-40 score baseline: independent offline replay

The accepted `DK/score-baseline-01` ends with **postfault A0 = 42**, after **last-clean A0 = 38**. It has five full clean checkpoint cycles and a sixth cycle whose first R read is already faulted. No compact checkpoint sampled a clean score above 40. This does not exclude a crossing between polls. The captured software transition is qualified after the successful Left workflow; it does not prove key causation, UI receipt, or physical light loss.

This analysis makes no TV calls. It leaves the frozen DP sources, manifests, DK captures and DM sources unchanged. `input-pins.json` pins every consumed receipt, raw binary, saved interpretation/result and source reference. `analyze.py` verifies all pins before loading the frozen strict DP/DM parsers, compares every exported raw file and saved interpretation, and independently unpacks the 34-byte checkpoints and retained H/N/R/M/C fields. `decoded.json` retains all exact read brackets and field values.

| Full clean cycle | A0 | q0 | history0, oldest first | N ordinal0 | C+7 | R+c4 start/end | M+2a publication mirror | H full-pair bracket, µs |
|---|---:|---:|---|---:|---:|---|---:|---|
| 1 | 0 | 0 | 0,0,0,0 | 0 | 0 | 40/40 | 200 | 178074749184–178074749265 |
| 2 | 0 | 0 | 0,0,0,0 | 0 | 0 | 40/40 | 200 | 178074992025–178074992104 |
| 3 | 0 | 0 | 0,0,0,0 | 0 | 1 | 40/40 | 200 | 178075242181–178075242262 |
| 4 | 0 | 0 | 0,0,0,0 | 0 | 1 | 40/40 | 40 | 178075494688–178075494831 |
| 5 | 38 | 0 | 0,4,0,4 | 41 | 1 | 40/40 | 40 | 178075743954–178075744242 |

All compact start/end RT classifications are Clean. These are sequential window reads, nominally 250 ms apart, rather than instrumentation at each comparator execution. In cycle 3 the earlier M mirror is 200 while the later C selector is 1. The data establish that this sequential cycle contains those values. They do not establish simultaneous state, a particular lag mechanism, or the comparator's actual FP register.

The last-clean retained full capture has source counts `[4,0,0,0,0,0]`, six ordinals `[41,0,0,0,0,0]`, A `[38,0,0,0,0,0]`, all q zero, and history0 `[0,4,0,4]`. Its two R windows agree: stop/fault/gate `0/0/1`, normal threshold 200, alternate threshold 40, action bucket 3 and mode-1 record latch 41. The first transition R has `1/0x1001/0`, action bucket 7 and latch 41. The postfault H bracket is **178075995427–178075995507 µs**; it has A `[42,0,0,0,0,0]`, all q zero, history0 `[4,0,4,0]`, and all other histories zero. The earlier postfault N has the same ordinal41 and **all six current source counts zero**. These current counts reset each dispatch; they are not cumulative event counts.

The selected source's delayed four-history accumulation is compatible with increasing 38 to 42 while the retained current source count is zero. In particular, a history shift can add an earlier qualifying count. These two sequential snapshots do not recover the exact intervening dispatch sequence. This run's actual score42 agrees with the earlier reported DH02 value; score44 from other runs must not be substituted here.

The last retained clean R pair is **178075744603–178075744874 µs**. The first fault R pair is **178075994002–178075994144 µs**. The conservative possible software-transition bracket spans the clean pair's OUT-header start through the fault pair's IN-data completion: **178075744603–178075994144 µs**, width **249541 µs**. It is conditional on the protocol reply freshness premise; neither the IN start nor its end is an exact controller sampling timestamp. Left-down dispatch/reply is **178074756271–178074886745 µs** and Left-up is **178075037604–178075063356 µs**. The whole transition bracket is strictly after both key calls returned. Native observation start/end are **178074740329/178075997983 µs**. The 20-second deadline was not reached.

Retained M has aa=0/ac=2, which selects mode1 in the selected image1 VA `0x1e68..0x203e`. Its source branch selects alternate R+c4 when C+7 is nonzero, otherwise normal R+0x30. Last-clean and postfault C+7=1, alternate40, mirror40 are mutually compatible with that selection. The H A0 low16 value42 exceeds40, and the action bucket changes3→7. This supports the sampled mode1 threshold path under the selected-code/layout premise; **the actual decision-time FP register is not captured**. It does not prove every other predicate, one unique event caller, the physical source of the packed data, or electrical damage safety. Raising the alternate limit to200 would change this conditional comparison for42, but this unchanged-40 run does not test or validate that intervention.

The later independently parsed `DK/record-fault-01` has 12 complete pairs, matching start/end R and N, mode1 context, C+7=1, mirror40, fault4097, ordinal/latch41 and six current source counts zero. All 48 candidate tuples and exact brackets are retained in `decoded.json`. Source-compatible indices0..40 have y2159/channel0, x in570/571/622/623/624/625/632/633, with the tail41..47 showing cleared coordinates/differences and some nonzero B values. These arrays can mix epochs/types and contain stale tails; no valid-prefix or epoch guarantee follows just from ordinal41. The mode1 inclusive publication bound40 permits indices0..40 then ordinal41; it does not cap qualifying source counting at41. **The actual selected A buffer/branch is not proven**: current metadata and descriptor D are not a direct decision-time B-ring header. B plus unsigned difference alone generally lacks the sign; any restricted-domain reconstruction remains conditional.

The original global counts remain **48 headers, 48 completed inputs and 96 bulk calls**, with five clean cycles, four discarded under the original clean retention policy, and six cycles started. The count is 5×8 full-clean pairs + 1 transition-R pair + 7 postfault pairs = 48. Saved trigger-baseline + last-clean + transition + postfault contain **24 raw windows**; the baseline is not an added cycle or additional transfer. The five checkpoints are 170 packed bytes. Native reports ReadyForHeader, released/closed, zero writes/retries and one completed Left attempt. The wrapper records one native invocation, accepted trial qualification, and stage absence after cleanup. No threshold write occurred in this run.

Reproduce with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 analyze.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -O analyze.py --check
```

Checks use explicit exceptions and remain active under `-O`. Both modes perform 207 decode/pin/semantic checks plus one exact decoded-artifact comparison. Frozen parser checks run additionally. `validation.json` records the results. `source-inventory.json` pins the new analysis artifacts; it excludes itself. No raw OEM firmware or new device data are exported by this analysis.
